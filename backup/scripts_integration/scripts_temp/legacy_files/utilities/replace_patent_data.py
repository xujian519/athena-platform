#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利数据替换脚本
Patent Data Replacement Script

用5700万条原始数据完全替换现有的2800万条数据
"""

import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime

import pandas as pd
import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/patent_replace.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentDataReplacer:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.batch_size = 10000
        self.total_processed = 0
        self.total_inserted = 0
        self.error_count = 0

    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='',
                database='patent_db'
            )
            self.cursor = self.conn.cursor()
            logger.info('✅ 数据库连接成功')

            # 设置事务隔离级别
            self.conn.set_session(isolation_level='READ_COMMITTED')

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise

    def backup_existing_data(self):
        """备份现有数据（可选）"""
        backup_choice = input('是否备份现有2800万条数据？(y/N): ').strip().lower()

        if backup_choice == 'y':
            logger.info('💾 开始备份现有数据...')

            backup_sql = """
            CREATE TABLE patents_backup_{} AS
            SELECT * FROM patents;
            """.format(datetime.now().strftime('%Y%m%d_%H%M%S'))

            try:
                self.cursor.execute(backup_sql)
                self.conn.commit()
                logger.info('✅ 数据备份完成')
            except Exception as e:
                logger.error(f"❌ 备份失败: {e}")
                raise

    def truncate_table(self):
        """清空现有数据表"""
        logger.warning('🗑️  准备清空patents表...')

        confirm = input("确认要清空现有的2800万条记录吗？这将删除所有数据！(输入 'DELETE ALL' 确认): ").strip()

        if confirm == 'DELETE ALL':
            try:
                # 记录清空前的统计信息
                self.cursor.execute('SELECT COUNT(*) FROM patents')
                count_before = self.cursor.fetchone()[0]
                self.cursor.execute("SELECT pg_size_pretty(pg_total_relation_size('public.patents'))")
                size_before = self.cursor.fetchone()[0]

                logger.info(f"当前记录数: {count_before:,}")
                logger.info(f"当前大小: {size_before}")

                # 清空表
                self.cursor.execute('TRUNCATE TABLE patents RESTART IDENTITY CASCADE;')
                self.conn.commit()

                logger.info('✅ patents表已清空')

                # 重置序列
                self.cursor.execute('ALTER SEQUENCE IF EXISTS patents_id_seq RESTART WITH 1;')
                self.conn.commit()

            except Exception as e:
                logger.error(f"❌ 清空表失败: {e}")
                self.conn.rollback()
                raise
        else:
            logger.info('❌ 操作已取消')
            sys.exit(0)

    def reset_table_auto_increment(self):
        """重置表自增ID"""
        logger.info('🔄 重置表自增ID...')

        # patents表使用UUID，不需要重置序列
        logger.info('✅ ID重置完成（使用UUID）')

    def transform_row(self, row):
        """转换数据行格式"""
        try:
            # 生成UUID
            patent_id = str(uuid.uuid4())

            # 处理日期字段
            def parse_date(date_str):
                if pd.isna(date_str) or date_str == '' or date_str is None:
                    return None
                try:
                    # 尝试多种日期格式
                    date_str = str(date_str).strip()
                    if len(date_str) == 10:  # YYYY-MM-DD
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    elif len(date_str) == 8:   # YYYYMMDD
                        return datetime.strptime(date_str, '%Y%m%d').date()
                    else:
                        return None
                except:
                    return None

            # 处理数字字段
            def parse_int(value, default=0):
                try:
                    if pd.isna(value) or value == '' or value is None:
                        return default
                    return int(float(str(value)))
                except:
                    return default

            # 处理字符串字段
            def parse_str(value, default=''):
                if pd.isna(value) or value is None:
                    return default
                return str(value).strip()

            # 生成文件哈希
            key_fields = [
                parse_str(row.get('application_number')),
                parse_str(row.get('publication_number')),
                parse_str(row.get('authorization_number'))
            ]
            hash_input = '|'.join(key_fields).encode('utf-8')
            file_hash = hashlib.md5(hash_input, usedforsecurity=False).hexdigest()

            # 构建插入数据
            insert_data = {
                'id': patent_id,
                'patent_name': parse_str(row.get('patent_name')),
                'patent_type': parse_str(row.get('patent_type')),
                'application_number': parse_str(row.get('application_number')),
                'application_date': parse_date(row.get('application_date')),
                'publication_number': parse_str(row.get('publication_number')),
                'publication_date': parse_date(row.get('publication_date')),
                'authorization_number': parse_str(row.get('authorization_number')),
                'authorization_date': parse_date(row.get('authorization_date')),
                'applicant': parse_str(row.get('applicant')),
                'applicant_type': parse_str(row.get('applicant_type')),
                'applicant_address': parse_str(row.get('applicant_address')),
                'applicant_region': parse_str(row.get('applicant_region')),
                'applicant_city': parse_str(row.get('applicant_city')),
                'applicant_district': parse_str(row.get('applicant_district')),
                'current_assignee': parse_str(row.get('current_assignee')),
                'current_assignee_address': parse_str(row.get('current_assignee_address')),
                'assignee_type': parse_str(row.get('assignee_type')),
                'credit_code': parse_str(row.get('credit_code')),
                'inventor': parse_str(row.get('inventor')),
                'ipc_code': parse_str(row.get('ipc_code')),
                'ipc_main_class': parse_str(row.get('ipc_main_class')),
                'ipc_classification': parse_str(row.get('ipc_classification')),
                'abstract': parse_str(row.get('abstract')),
                'claims_content': parse_str(row.get('claims_content')),
                'claims': parse_str(row.get('claims')),
                'citation_count': parse_int(row.get('citation_count')),
                'cited_count': parse_int(row.get('cited_count')),
                'self_citation_count': parse_int(row.get('self_citation_count')),
                'other_citation_count': parse_int(row.get('other_citation_count')),
                'cited_by_self_count': parse_int(row.get('cited_by_self_count')),
                'cited_by_others_count': parse_int(row.get('cited_by_others_count')),
                'family_citation_count': parse_int(row.get('family_citation_count')),
                'family_cited_count': parse_int(row.get('family_cited_count')),
                'source_year': parse_int(row.get('source_year'), 2024),
                'source_file': parse_str(row.get('source_file', 'batch_import')),
                'file_hash': file_hash,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            return insert_data

        except Exception as e:
            logger.error(f"❌ 转换行数据失败: {e}")
            return None

    def batch_insert(self, batch_data):
        """批量插入数据"""
        if not batch_data:
            return 0

        # 构建插入SQL（不包含向量字段，这些可以后续生成）
        columns = list(batch_data[0].keys())
        # 排除向量相关字段，后续统一处理
        exclude_fields = ['embedding_title', 'embedding_abstract', 'embedding_claims',
                         'embedding_combined', 'search_vector', 'vectorized_at']
        columns = [col for col in columns if col not in exclude_fields]

        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"""
        INSERT INTO patents ({', '.join(columns)})
        VALUES ({placeholders})
        """

        # 准备数据
        values = []
        for row in batch_data:
            values.append([row.get(col) for col in columns])

        try:
            # 执行批量插入
            self.cursor.executemany(sql, values)
            self.conn.commit()

            inserted_count = len(batch_data)
            return inserted_count

        except Exception as e:
            logger.error(f"❌ 批量插入失败: {e}")
            self.conn.rollback()
            return 0

    def process_csv_file(self, file_path):
        """处理单个CSV文件"""
        logger.info(f"📂 处理文件: {file_path}")

        try:
            # 读取CSV文件
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                low_memory=False,
                dtype=str  # 所有字段作为字符串读取
            )

            logger.info(f"📊 文件 {os.path.basename(file_path)} 包含 {len(df):,} 条记录")

            # 分批处理
            batch = []
            file_inserted = 0

            for index, row in df.iterrows():
                # 转换数据
                transformed = self.transform_row(row.to_dict())

                if transformed:
                    batch.append(transformed)

                    # 批量插入
                    if len(batch) >= self.batch_size:
                        inserted = self.batch_insert(batch)
                        file_inserted += inserted
                        self.total_processed += len(batch)
                        self.total_inserted += inserted

                        # 显示进度
                        progress = (self.total_processed / 57000000) * 100
                        logger.info(f"  进度: {progress:.2f}% | {self.total_processed:,} | 插入: {self.total_inserted:,}")

                        batch = []

            # 处理剩余数据
            if batch:
                inserted = self.batch_insert(batch)
                file_inserted += inserted
                self.total_processed += len(batch)
                self.total_inserted += inserted

            logger.info(f"✅ 文件 {os.path.basename(file_path)} 完成: 插入 {file_inserted:,}")

        except Exception as e:
            logger.error(f"❌ 处理文件 {file_path} 失败: {e}")
            self.error_count += 1

    def process_directory(self, directory_path):
        """处理目录下的所有CSV文件"""
        logger.info(f"📁 开始处理目录: {directory_path}")

        csv_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))

        logger.info(f"📝 找到 {len(csv_files)} 个CSV文件")

        # 按文件大小排序，先处理小文件
        csv_files.sort(key=lambda x: os.path.getsize(x))

        start_time = datetime.now()

        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"\n📄 [{i}/{len(csv_files)}] 处理文件: {os.path.basename(csv_file)}")
            self.process_csv_file(csv_file)

            # 每处理5个文件显示一次详细进度
            if i % 5 == 0:
                elapsed = datetime.now() - start_time
                rate = self.total_processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                logger.info(f"\n📊 阶段进度报告 [{i}/{len(csv_files)}]:")
                logger.info(f"  总处理: {self.total_processed:,} 条 ({self.total_processed/57000000*100:.2f}%)")
                logger.info(f"  总插入: {self.total_inserted:,} 条")
                logger.info(f"  处理速度: {rate:.0f} 条/秒")
                logger.info(f"  已用时间: {elapsed}")
                estimated_total = 57000000 / rate if rate > 0 else 0
                remaining_time = estimated_total - elapsed.total_seconds()
                logger.info(f"  预计剩余: {remaining_time/3600:.1f} 小时")

        # 最终统计
        total_time = datetime.now() - start_time
        logger.info(f"\n🎉 数据替换完成！")
        logger.info(f"  总文件数: {len(csv_files)}")
        logger.info(f"  总处理: {self.total_processed:,} 条")
        logger.info(f"  总插入: {self.total_inserted:,} 条")
        logger.info(f"  错误数: {self.error_count}")
        logger.info(f"  总用时: {total_time}")
        logger.info(f"  平均速度: {self.total_processed/total_time.total_seconds():.0f} 条/秒")

    def update_indexes_and_stats(self):
        """更新索引和统计信息"""
        logger.info('🔧 更新索引和统计信息...')

        try:
            # 更新表统计信息
            self.cursor.execute('ANALYZE patents;')

            # 创建全文搜索索引
            logger.info('创建全文搜索索引...')
            self.cursor.execute("""
                UPDATE patents
                SET search_vector = to_tsvector('chinese',
                    COALESCE(patent_name, '') || ' ' ||
                    COALESCE(abstract, '') || ' ' ||
                    COALESCE(claims, '')
                )
                WHERE search_vector IS NULL;
            """)

            # 创建GIN索引
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patents_search_vector
                ON patents USING GIN(search_vector);
            """)

            # 创建常用字段索引
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_patents_app_number ON patents(application_number);',
                'CREATE INDEX IF NOT EXISTS idx_patents_pub_number ON patents(publication_number);',
                'CREATE INDEX IF NOT EXISTS idx_patents_auth_number ON patents(authorization_number);',
                'CREATE INDEX IF NOT EXISTS idx_patents_applicant ON patents(applicant);',
                'CREATE INDEX IF NOT EXISTS idx_patents_ipc_code ON patents(ipc_code);',
                'CREATE INDEX IF NOT EXISTS idx_patents_app_date ON patents(application_date);',
                'CREATE INDEX IF NOT EXISTS idx_patents_pub_date ON patents(publication_date);'
            ]

            for index_sql in indexes:
                try:
                    self.cursor.execute(index_sql)
                    logger.info(f"✅ 创建索引成功")
                except Exception as e:
                    logger.warning(f"⚠️  创建索引失败: {e}")

            self.conn.commit()
            logger.info('✅ 索引和统计信息更新完成')

        except Exception as e:
            logger.error(f"❌ 更新索引失败: {e}")

    def show_final_stats(self):
        """显示最终统计信息"""
        logger.info("\n📊 最终统计信息:")

        try:
            # 记录数
            self.cursor.execute('SELECT COUNT(*) FROM patents')
            count = self.cursor.fetchone()[0]
            logger.info(f"  总记录数: {count:,}")

            # 数据库大小
            self.cursor.execute("SELECT pg_size_pretty(pg_database_size('patent_db'))")
            db_size = self.cursor.fetchone()[0]
            logger.info(f"  数据库大小: {db_size}")

            # 表大小
            self.cursor.execute("SELECT pg_size_pretty(pg_total_relation_size('public.patents'))")
            table_size = self.cursor.fetchone()[0]
            logger.info(f"  patents表大小: {table_size}")

            # 有效记录统计
            self.cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN publication_number IS NOT NULL AND publication_number != '' THEN 1 END) as has_pub_num,
                    COUNT(CASE WHEN application_number IS NOT NULL AND application_number != '' THEN 1 END) as has_app_num
                FROM patents
            """)
            stats = self.cursor.fetchone()
            logger.info(f"  有效公开号: {stats[1]:,}")
            logger.info(f"  有效申请号: {stats[2]:,}")

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")

    def cleanup(self):
        """清理资源"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info('🧹 资源清理完成')


def main():
    """主函数"""
    logger.info('🚀 开始专利数据替换')

    # 获取数据目录
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
    else:
        data_directory = input('请输入CSV数据目录路径: ').strip()

    if not os.path.exists(data_directory):
        logger.error(f"❌ 目录不存在: {data_directory}")
        return

    # 创建替换器
    replacer = PatentDataReplacer()

    try:
        # 连接数据库
        replacer.connect_db()

        # 备份现有数据（可选）
        replacer.backup_existing_data()

        # 清空现有数据
        replacer.truncate_table()

        # 重置自增ID
        replacer.reset_table_auto_increment()

        # 导入新数据
        logger.info("\n📥 开始导入新数据...")
        replacer.process_directory(data_directory)

        # 更新索引
        replacer.update_indexes_and_stats()

        # 显示最终统计
        replacer.show_final_stats()

    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断操作")
    except Exception as e:
        logger.error(f"❌ 替换过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        replacer.cleanup()


if __name__ == '__main__':
    main()