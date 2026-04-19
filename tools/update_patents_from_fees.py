#!/usr/bin/env python3
"""
基于官费缴费记录更新专利状态
将已缴费的专利标记为有效专利
"""

import json
import logging
import sys
import uuid
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentFeeUpdater:
    """基于官费记录更新专利状态"""

    def __init__(self):
        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "athena_business",
            "user": "postgres",
            "password": "xj781102"
        }

    def update_existing_patents(self) -> dict:
        """更新现有专利状态"""
        logger.info("🔄 更新现有专利状态...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 获取所有缴费记录中的专利号
            cursor.execute('SELECT metadata::text FROM financial_records WHERE metadata IS NOT NULL')
            records = cursor.fetchall()

            # 统计信息
            patent_numbers = set()
            for r in records:
                if r[0]:
                    try:
                        metadata = json.loads(r[0])
                        patent_num = metadata.get('patent_number', '')
                        if patent_num:
                            patent_numbers.add(patent_num)
                    except Exception:
                        continue

            logger.info(f"  从缴费记录中提取到 {len(patent_numbers)} 个唯一专利号")

            matched_count = 0
            updated_count = 0

            # 为每个专利号尝试匹配和更新
            for pnum in patent_numbers:
                # 尝试多种匹配方式
                cursor.execute('''
                    SELECT patent_id, application_number, title, status, legal_status
                    FROM patents
                    WHERE application_number = %s
                       OR application_number = %s
                       OR application_number = %s
                       OR application_number LIKE %s
                ''', (pnum, pnum + '.X', pnum + '.x', f'%{pnum}%'))

                results = cursor.fetchall()

                if results:
                    matched_count += 1
                    for r in results:
                        patent_id = r[0]
                        current_status = r[3]
                        current_legal = r[4]

                        # 更新专利状态
                        new_status = 'active'
                        new_legal_status = '有效专利（已缴费）'

                        if current_status != new_status or current_legal != new_legal_status:
                            cursor.execute('''
                                UPDATE patents
                                SET status = %s, legal_status = %s, updated_at = CURRENT_TIMESTAMP
                                WHERE patent_id = %s
                            ''', (new_status, new_legal_status, patent_id))
                            updated_count += 1

            conn.commit()

            logger.info(f"  匹配到现有专利: {matched_count} 个")
            logger.info(f"  更新专利状态: {updated_count} 个")

            return {
                "total_fee_patents": len(patent_numbers),
                "matched_patents": matched_count,
                "updated_patents": updated_count
            }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"更新现有专利失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def create_missing_patents(self) -> dict:
        """为未匹配的专利创建新记录"""
        logger.info("🆕 创建缺失的专利记录...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 获取所有缴费记录中的专利号
            cursor.execute('SELECT metadata::text FROM financial_records WHERE metadata IS NOT NULL')
            records = cursor.fetchall()

            # 收集所有专利号
            patent_numbers = set()
            for r in records:
                if r[0]:
                    try:
                        metadata = json.loads(r[0])
                        patent_num = metadata.get('patent_number', '')
                        if patent_num:
                            patent_numbers.add(patent_num)
                    except Exception:
                        continue

            logger.info(f"  从缴费记录中提取到 {len(patent_numbers)} 个唯一专利号")

            # 找出未匹配的专利号
            unmatched_patents = []
            for pnum in patent_numbers:
                cursor.execute('''
                    SELECT COUNT(*) FROM patents
                    WHERE application_number = %s
                       OR application_number = %s
                       OR application_number = %s
                       OR application_number LIKE %s
                ''', (pnum, pnum + '.X', pnum + '.x', f'%{pnum}%'))

                count = cursor.fetchone()[0]
                if count == 0:
                    unmatched_patents.append(pnum)

            logger.info(f"  未匹配的专利号: {len(unmatched_patents)} 个")

            # 为未匹配的专利创建新记录
            created_count = 0
            patents_to_insert = []

            for pnum in unmatched_patents:
                # 获取对应的缴费记录信息
                cursor.execute('''
                    SELECT metadata::text, record_type, amount, record_date, description
                    FROM financial_records
                    WHERE metadata::text LIKE %s
                    LIMIT 1
                ''', (f'%{pnum}%',))

                fee_record = cursor.fetchone()

                if fee_record and fee_record[0]:
                    try:
                        metadata = json.loads(fee_record[0])
                        business_type = metadata.get('business_type', '')
                        client_name = metadata.get('client_name', '')

                        # 构建专利记录
                        patent_record = {
                            'patent_id': str(uuid.uuid4()),
                            'title': f'专利-{pnum}',
                            'abstract': f'基于官费缴费记录创建的专利，申请号：{pnum}，业务类型：{business_type}',
                            'application_number': pnum,
                            'inventor': client_name,
                            'applicant': client_name,
                            'status': 'active',
                            'legal_status': '有效专利（已缴费）',
                            'metadata': json.dumps({
                                'source': 'fee_payment_record',
                                'created_from_fee': True,
                                'business_type': business_type,
                                'client_name': client_name,
                                'fee_amount': float(fee_record[2]),
                                'fee_date': fee_record[3].isoformat() if fee_record[3] else None
                            }, ensure_ascii=False),
                            'created_at': datetime.now(),
                            'updated_at': datetime.now(),
                            'created_by': 'fee_updater'
                        }

                        patents_to_insert.append(patent_record)
                    except Exception as e:
                        logger.warning(f"处理专利号 {pnum} 时出错: {str(e)}")
                        continue

            # 批量插入新专利
            if patents_to_insert:
                columns = patents_to_insert[0].keys()
                values = [[record[col] for col in columns] for record in patents_to_insert]

                insert_query = f"""
                    INSERT INTO patents ({', '.join(columns)})
                    VALUES %s
                """

                execute_values(cursor, insert_query, values)
                created_count = len(patents_to_insert)

                conn.commit()
                logger.info(f"  创建新专利记录: {created_count} 个")

                # 更新财务记录中的专利ID
                self.update_financial_records_patent_id(conn, patents_to_insert)

            return {
                "unmatched_patents": len(unmatched_patents),
                "created_patents": created_count
            }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"创建缺失专利失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def update_financial_records_patent_id(self, conn, patents_to_insert: list[dict]):
        """更新财务记录中的专利ID"""
        logger.info("🔗 更新财务记录中的专利ID...")

        cursor = conn.cursor()
        updated_count = 0

        for patent in patents_to_insert:
            patent_number = patent['application_number']
            patent_id = patent['patent_id']

            # 更新对应的财务记录
            cursor.execute('''
                UPDATE financial_records
                SET patent_id = %s
                WHERE metadata::text LIKE %s
            ''', (patent_id, f'%{patent_number}%'))

            rows_affected = cursor.rowcount
            if rows_affected > 0:
                updated_count += 1

        conn.commit()
        logger.info(f"  更新了 {updated_count} 个专利对应的财务记录")

    def get_final_statistics(self) -> dict:
        """获取最终统计信息"""
        logger.info("📊 获取最终统计信息...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 统计专利总数
            cursor.execute('SELECT COUNT(*) FROM patents')
            total_patents = cursor.fetchone()[0]

            # 统计有效专利数
            cursor.execute('SELECT COUNT(*) FROM patents WHERE status = \'active\' AND legal_status LIKE \'%有效专利%\'')
            active_patents = cursor.fetchone()[0]

            # 统计待审核专利数
            cursor.execute('SELECT COUNT(*) FROM patents WHERE status = \'pending\'')
            pending_patents = cursor.fetchone()[0]

            # 统计财务记录数
            cursor.execute('SELECT COUNT(*) FROM financial_records')
            total_financial_records = cursor.fetchone()[0]

            # 统计有专利ID的财务记录数
            cursor.execute('SELECT COUNT(*) FROM financial_records WHERE patent_id IS NOT NULL')
            linked_financial_records = cursor.fetchone()[0]

            return {
                "total_patents": total_patents,
                "active_patents": active_patents,
                "pending_patents": pending_patents,
                "total_financial_records": total_financial_records,
                "linked_financial_records": linked_financial_records,
                "linkage_rate": (linked_financial_records / total_financial_records * 100) if total_financial_records > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()


def main():
    """主函数"""
    print("🚀 基于官费缴费记录更新专利状态")
    print("=" * 60)

    updater = PatentFeeUpdater()

    try:
        # 1. 更新现有专利状态
        update_result = updater.update_existing_patents()

        # 2. 创建缺失的专利记录
        create_result = updater.create_missing_patents()

        # 3. 获取最终统计
        stats = updater.get_final_statistics()

        print("\n✨ 更新完成！")
        print("📈 更新现有专利:")
        print(f"  总缴费专利数: {update_result['total_fee_patents']}")
        print(f"  匹配到现有专利: {update_result['matched_patents']}")
        print(f"  更新专利状态: {update_result['updated_patents']}")

        print("\n🆕 创建新专利记录:")
        print(f"  未匹配专利数: {create_result['unmatched_patents']}")
        print(f"  创建新专利数: {create_result['created_patents']}")

        print("\n📊 最终统计:")
        print(f"  专利总数: {stats.get('total_patents', 0)}")
        print(f"  有效专利数: {stats.get('active_patents', 0)}")
        print(f"  待审核专利数: {stats.get('pending_patents', 0)}")
        print(f"  财务记录总数: {stats.get('total_financial_records', 0)}")
        print(f"  已关联专利的财务记录: {stats.get('linked_financial_records', 0)}")
        print(f"  关联率: {stats.get('linkage_rate', 0):.1f}%")

        return True

    except Exception as e:
        logger.error(f"❌ 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
