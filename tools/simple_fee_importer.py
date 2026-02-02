#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的官费缴费记录导入工具
专门处理2025年专利官费缴费记录的特殊格式
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
import sys
import logging
import uuid
import re
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleFeeImporter:
    """简化的官费缴费记录导入器"""

    def __init__(self):
        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "athena_business",
            "user": "postgres",
            "password": "xj781102"
        }

        # 缓存现有数据
        self.existing_patents = set()
        self.client_map = {}
        self.patent_map = {}

    def load_existing_data(self):
        """加载现有专利和客户数据"""
        logger.info("🔗 加载现有数据...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 加载现有专利申请号
            cursor.execute("""
                SELECT patent_id, application_number, title
                FROM patents
                WHERE application_number IS NOT NULL
            """)
            for row in cursor.fetchall():
                if row[1]:
                    clean_app_num = self._clean_patent_number(row[1])
                    self.existing_patents.add(clean_app_num)
                    self.patent_map[clean_app_num] = row[0]

            # 加载现有客户
            cursor.execute("""
                SELECT id, name
                FROM clients
                WHERE name IS NOT NULL
            """)
            for row in cursor.fetchall():
                name = row[1].strip()
                self.client_map[name] = row[0]

            logger.info(f"  现有专利申请号: {len(self.existing_patents)}")
            logger.info(f"  现有客户: {len(self.client_map)}")

        except Exception as e:
            logger.error(f"加载现有数据失败: {str(e)}")
        finally:
            if conn:
                conn.close()

    def _clean_patent_number(self, patent_num: str) -> str:
        """清理专利申请号"""
        if not patent_num:
            return ""

        patent_num = str(patent_num).strip()

        # 移除常见的格式问题
        patent_num = re.sub(r'[^\d.]', '', patent_num)

        # 标准化格式：移除多余的点
        while '..' in patent_num:
            patent_num = patent_num.replace('..', '.')

        # 确保只有一个点
        if patent_num.count('.') > 1:
            parts = patent_num.split('.')
            patent_num = parts[0] + '.' + parts[1]

        return patent_num

    def process_fee_file(self, excel_path: str) -> List[Dict]:
        """处理官费缴费记录文件"""
        logger.info("📝 处理官费缴费记录文件...")

        try:
            # 使用openpyxl直接读取
            df = pd.read_excel(excel_path, engine='openpyxl')

            print(f"原始文件行数: {len(df)}")
            print(f"列名: {list(df.columns)}")

            # 跳过第一行汇总，从第2行开始处理
            payment_records = []

            for idx in range(1, len(df)):
                row = df.iloc[idx]

                try:
                    # 申请号/专利号
                    patent_num = None
                    if pd.notna(row['申请号/专利号']):
                        patent_num = self._clean_patent_number(str(row['申请号/专利号']))

                    if not patent_num:
                        continue

                    # 缴费日期
                    payment_date = None
                    if pd.notna(row['缴费日期']):
                        date_val = row['缴费日期']
                        if isinstance(date_val, (int, float)):
                            # 处理Excel的数字日期格式
                            payment_date = pd.to_datetime(date_val, errors='coerce')

                    # 费用金额
                    payment_amount = 0.0
                    if pd.notna(row['费用金额（人民币）']):
                        try:
                            payment_amount = float(row['费用金额（人民币）'])
                        except Exception as e:

                            # 记录异常但不中断流程

                            logger.debug(f"[simple_fee_importer] Exception: {e}")
                    # 费用种类
                    payment_type = "未知"
                    if pd.notna(row['费用种类']):
                        payment_type = str(row['费用种类']).strip()

                    # 票据抬头（作为客户名称）
                    client_name = ""
                    if pd.notna(row['票据抬头']):
                        client_name = str(row['票据抬头']).strip()

                    # 业务类型
                    business_type = ""
                    if pd.notna(row['业务类型']):
                        business_type = str(row['业务类型']).strip()

                    # 构建记录
                    record = {
                        "patent_number": patent_num,
                        "client_name": client_name,
                        "payment_amount": payment_amount,
                        "payment_date": payment_date,
                        "payment_type": payment_type,
                        "business_type": business_type,
                        "source_file": Path(excel_path).name,
                        "import_time": datetime.now(),
                        "row_index": idx + 1  # +1 因为跳过了第0行汇总
                    }

                    payment_records.append(record)

                except Exception as e:
                    logger.warning(f"处理第{idx+1}行出错: {str(e)}")
                    continue

            logger.info(f"  提取到 {len(payment_records)} 条缴费记录")
            return payment_records

        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            return []

    def save_to_database(self, payment_records: List[Dict]):
        """保存到数据库"""
        logger.info("💾 保存数据到数据库...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 检查是否存在财务记录表
            table_exists = False
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'financial_records'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                logger.info("  创建财务记录表...")
                cursor.execute("""
                    CREATE TABLE financial_records (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        patent_id VARCHAR(50) REFERENCES patents(patent_id),
                        client_id UUID REFERENCES clients(id),
                        record_type VARCHAR(50) NOT NULL,
                        amount DECIMAL(12,2) NOT NULL,
                        record_date DATE,
                        description TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        source VARCHAR(100),
                        row_number INTEGER
                    );
                """)

                # 创建索引
                cursor.execute("CREATE INDEX idx_financial_patent ON financial_records(patent_id);")
                cursor.execute("CREATE INDEX idx_financial_date ON financial_records(record_date);")
                logger.info("  ✅ 财务记录表创建成功")

            # 准备数据
            records_to_insert = []
            matched_patents = 0
            matched_clients = 0
            unmatched_patents = 0

            for record in payment_records:
                patent_id = self.patent_map.get(record['patent_number'])
                client_id = None

                # 如果有客户名称，尝试匹配
                if record['client_name']:
                    # 尝试精确匹配
                    if record['client_name'] in self.client_map:
                        client_id = self.client_map[record['client_name']]
                    else:
                        # 尝试模糊匹配
                        for name, cid in self.client_map.items():
                            if record['client_name'] in name or name in record['client_name']:
                                client_id = cid
                                break

                if patent_id:
                    matched_patents += 1
                else:
                    unmatched_patents += 1

                if client_id:
                    matched_clients += 1

                financial_record = {
                    'patent_id': patent_id,
                    'client_id': client_id,
                    'record_type': record['payment_type'],
                    'amount': record['payment_amount'],
                    'record_date': record['payment_date'],
                    'description': f"缴费记录 - {record['payment_type']} ({record.get('business_type', '')})",
                    'metadata': json.dumps({
                        'source_file': record['source_file'],
                        'import_time': record['import_time'].isoformat(),
                        'patent_number': record['patent_number'],
                        'business_type': record.get('business_type', ''),
                        'row_index': record['row_index']
                    }, ensure_ascii=False),
                    'source': 'fee_importer',
                    'row_number': record['row_index']
                }

                records_to_insert.append(financial_record)

            # 插入数据
            if records_to_insert:
                columns = records_to_insert[0].keys()
                values = [[record[col] for col in columns] for record in records_to_insert]

                insert_query = f"""
                    INSERT INTO financial_records ({', '.join(columns)})
                    VALUES %s
                """

                execute_values(cursor, insert_query, values)

                conn.commit()
                logger.info(f"✅ 成功保存 {len(records_to_insert)} 条财务记录")
                logger.info(f"  匹配到专利: {matched_patents} 条")
                logger.info(f"  匹配到客户: {matched_clients} 条")
                logger.info(f"  未匹配专利: {unmatched_patents} 条")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def analyze_payment_data(self, payment_records: List[Dict]) -> Dict:
        """分析缴费数据"""
        logger.info("📈 分析缴费数据...")

        total_amount = sum(r['payment_amount'] for r in payment_records)
        unique_patents = len(set(r['patent_number'] for r in payment_records))
        payment_types = {}

        for record in payment_records:
            ptype = record['payment_type']
            payment_types[ptype] = payment_types.get(ptype, 0) + 1

        analysis = {
            "total_records": len(payment_records),
            "total_amount": total_amount,
            "unique_patents": unique_patents,
            "payment_types": payment_types,
            "average_amount": total_amount / len(payment_records) if payment_records else 0
        }

        logger.info(f"  总记录数: {analysis['total_records']}")
        logger.info(f"  总金额: ¥{analysis['total_amount']:,.2f}")
        logger.info(f"  涉及专利: {analysis['unique_patents']} 项")
        logger.info(f"  平均金额: ¥{analysis['average_amount']:,.2f}")

        return analysis


def main():
    """主函数"""
    excel_path = "/Users/xujian/工作/10_归档文件/2025年专利官费缴费记录(1).xlsx"

    print("🚀 简化版2025年专利官费缴费记录导入工具")
    print("=" * 60)

    # 检查文件
    if not Path(excel_path).exists():
        logger.error(f"❌ 文件不存在: {excel_path}")
        return False

    # 创建导入器
    importer = SimpleFeeImporter()

    try:
        # 1. 加载现有数据
        importer.load_existing_data()

        # 2. 处理缴费记录
        payment_records = importer.process_fee_file(excel_path)

        if not payment_records:
            logger.error("❌ 没有提取到缴费记录")
            return False

        # 3. 分析数据
        analysis = importer.analyze_payment_data(payment_records)

        # 4. 保存到数据库
        importer.save_to_database(payment_records)

        print("\n✨ 导入完成！")
        print(f"  处理记录: {len(payment_records)} 条")
        print(f"  总金额: ¥{analysis['total_amount']:,.2f}")
        print(f"  涉及专利: {analysis['unique_patents']} 项")

        return True

    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        import traceback

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)