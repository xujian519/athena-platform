#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利数据批量导入脚本
Patent Data Batch Import Script

优化导入5700万条专利数据，避免重复并提高性能
"""

import hashlib
import json
import logging
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/patent_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentDataImporter:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.batch_size = 10000  # 批量插入大小
        self.total_processed = 0
        self.total_inserted = 0
        self.total_skipped = 0
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

    def create_temp_table(self):
        """创建临时表用于导入"""
        logger.info('📝 创建临时导入表...')

        create_temp_sql = """
        CREATE TEMP TABLE IF NOT EXISTS temp_patents (
            LIKE patents INCLUDING DEFAULTS
        ) ON COMMIT PRESERVE ROWS;

        -- 删除索引以加快导入速度
        DROP INDEX IF EXISTS idx_temp_patents_app_number;
        DROP INDEX IF EXISTS idx_temp_patents_pub_number;

        -- 创建必要的约束
        ALTER TABLE temp_patents DROP CONSTRAINT IF EXISTS temp_patents_pkey;
        """

        try:
            self.cursor.execute(create_temp_sql)
            self.conn.commit()
            logger.info('✅ 临时表创建成功')
        except Exception as e:
            logger.error(f"❌ 创建临时表失败: {e}")
            raise

    def clean_existing_data(self):
        """清理现有无效数据"""
        logger.info('🧹 清理现有无效数据...')

        try:
            # 删除公开号为空的记录（可能是导入失败的记录）
            delete_sql = """
            DELETE FROM patents
            WHERE publication_number = '' OR publication_number IS NULL
            OR LENGTH(TRIM(publication_number)) = 0;
            """

            self.cursor.execute(delete_sql)
            deleted_count = self.cursor.rowcount
            self.conn.commit()

            logger.info(f"✅ 清理了 {deleted_count:,} 条无效记录")

        except Exception as e:
            logger.error(f"❌ 清理数据失败: {e}")
            self.conn.rollback()

    def generate_file_hash(self, row_data):
        """生成文件哈希值用于去重"""
        # 使用关键字段生成哈希
        key_fields = [
            str(row_data.get('application_number', '')),
            str(row_data.get('publication_number', '')),
            str(row_data.get('authorization_number', ''))
        ]

        hash_input = '|'.join(key_fields).encode('utf-8')
        return hashlib.md5(hash_input, usedforsecurity=False).hexdigest()

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
                    return datetime.strptime(str(date_str), '%Y-%m-%d').date()
                except:
                    return None

            # 生成文件哈希
            file_hash = self.generate_file_hash(row)

            # 构建插入数据
            insert_data = {
                'id': patent_id,
                'patent_name': str(row.get('patent_name', '')).strip(),
                'patent_type': str(row.get('patent_type', '')).strip(),
                'application_number': str(row.get('application_number', '')).strip(),
                'application_date': parse_date(row.get('application_date')),
                'publication_number': str(row.get('publication_number', '')).strip(),
                'publication_date': parse_date(row.get('publication_date')),
                'authorization_number': str(row.get('authorization_number', '')).strip(),
                'authorization_date': parse_date(row.get('authorization_date')),
                'applicant': str(row.get('applicant', '')).strip(),
                'applicant_type': str(row.get('applicant_type', '')).strip(),
                'applicant_address': str(row.get('applicant_address', '')).strip(),
                'applicant_region': str(row.get('applicant_region', '')).strip(),
                'applicant_city': str(row.get('applicant_city', '')).strip(),
                'applicant_district': str(row.get('applicant_district', '')).strip(),
                'current_assignee': str(row.get('current_assignee', '')).strip(),
                'current_assignee_address': str(row.get('current_assignee_address', '')).strip(),
                'assignee_type': str(row.get('assignee_type', '')).strip(),
                'credit_code': str(row.get('credit_code', '')).strip(),
                'inventor': str(row.get('inventor', '')).strip(),
                'ipc_code': str(row.get('ipc_code', '')).strip(),
                'ipc_main_class': str(row.get('ipc_main_class', '')).strip(),
                'ipc_classification': str(row.get('ipc_classification', '')).strip(),
                'abstract': str(row.get('abstract', '')).strip(),
                'claims_content': str(row.get('claims_content', '')).strip(),
                'claims': str(row.get('claims', '')).strip(),
                'citation_count': int(row.get('citation_count', 0) or 0),
                'cited_count': int(row.get('cited_count', 0) or 0),
                'self_citation_count': int(row.get('self_citation_count', 0) or 0),
                'other_citation_count': int(row.get('other_citation_count', 0) or 0),
                'cited_by_self_count': int(row.get('cited_by_self_count', 0) or 0),
                'cited_by_others_count': int(row.get('cited_by_others_count', 0) or 0),
                'family_citation_count': int(row.get('family_citation_count', 0) or 0),
                'family_cited_count': int(row.get('family_cited_count', 0) or 0),
                'source_year': int(row.get('source_year', 2024) or 2024),
                'source_file': str(row.get('source_file', 'batch_import')).strip(),
                'file_hash': file_hash,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            return insert_data

        except Exception as e:
            logger.error(f"❌ 转换行数据失败: {e}, 行数据: {row}")
            return None

    def check_duplicate(self, row_data):
        """检查是否重复"""
        check_sql = """
        SELECT COUNT(*) FROM patents
        WHERE (application_number = %s AND application_number IS NOT NULL AND application_number != '')
           OR (publication_number = %s AND publication_number IS NOT NULL AND publication_number != '')
           OR (authorization_number = %s AND authorization_number IS NOT NULL AND authorization_number != '')
        LIMIT 1;
        """

        self.cursor.execute(check_sql, (
            row_data['application_number'],
            row_data['publication_number'],
            row_data['authorization_number']
        ))

        return self.cursor.fetchone()[0] > 0

    def batch_insert(self, batch_data):
        """批量插入数据"""
        if not batch_data:
            return 0, 0

        # 过滤重复数据
        unique_data = []
        skipped_count = 0

        for row_data in batch_data:
            if not self.check_duplicate(row_data):
                unique_data.append(row_data)
            else:
                skipped_count += 1

        if not unique_data:
            return 0, skipped_count

        # 构建插入SQL
        columns = list(unique_data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"""
        INSERT INTO patents ({', '.join(columns)})
        VALUES ({placeholders})
        """

        # 准备数据
        values = []
        for row in unique_data:
            values.append([row.get(col) for col in columns])

        try:
            # 执行批量插入
            self.cursor.executemany(sql, values)
            self.conn.commit()

            inserted_count = len(unique_data)
            return inserted_count, skipped_count

        except Exception as e:
            logger.error(f"❌ 批量插入失败: {e}")
            self.conn.rollback()
            return 0, skipped_count

    def process_csv_file(self, file_path):
        """处理单个CSV文件"""
        logger.info(f"📂 处理文件: {file_path}")

        try:
            # 读取CSV文件
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                low_memory=False,
                dtype=str  # 所有字段作为字符串读取，避免类型推断问题
            )

            logger.info(f"📊 文件 {os.path.basename(file_path)} 包含 {len(df):,} 条记录")

            # 分批处理
            batch = []
            file_inserted = 0
            file_skipped = 0

            for index, row in df.iterrows():
                # 转换数据
                transformed = self.transform_row(row.to_dict())

                if transformed:
                    batch.append(transformed)

                    # 批量插入
                    if len(batch) >= self.batch_size:
                        inserted, skipped = self.batch_insert(batch)
                        file_inserted += inserted
                        file_skipped += skipped

                        self.total_processed += len(batch)
                        self.total_inserted += inserted
                        self.total_skipped += skipped

                        logger.info(f"  进度: {self.total_processed:,} | 插入: {self.total_inserted:,} | 跳过: {self.total_skipped:,}")

                        batch = []

            # 处理剩余数据
            if batch:
                inserted, skipped = self.batch_insert(batch)
                file_inserted += inserted
                file_skipped += skipped

                self.total_processed += len(batch)
                self.total_inserted += inserted
                self.total_skipped += skipped

            logger.info(f"✅ 文件 {os.path.basename(file_path)} 完成: 插入 {file_inserted:,}, 跳过 {file_skipped:,}")

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

            # 每处理10个文件显示一次进度
            if i % 10 == 0:
                elapsed = datetime.now() - start_time
                rate = self.total_processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                logger.info(f"\n📊 阶段进度报告 [{i}/{len(csv_files)}]:")
                logger.info(f"  总处理: {self.total_processed:,} 条")
                logger.info(f"  总插入: {self.total_inserted:,} 条")
                logger.info(f"  总跳过: {self.total_skipped:,} 条")
                logger.info(f"  处理速度: {rate:.0f} 条/秒")
                logger.info(f"  已用时间: {elapsed}")

        # 最终统计
        total_time = datetime.now() - start_time
        logger.info(f"\n🎉 导入完成！")
        logger.info(f"  总文件数: {len(csv_files)}")
        logger.info(f"  总处理: {self.total_processed:,} 条")
        logger.info(f"  总插入: {self.total_inserted:,} 条")
        logger.info(f"  总跳过: {self.total_skipped:,} 条")
        logger.info(f"  错误数: {self.error_count}")
        logger.info(f"  总用时: {total_time}")
        logger.info(f"  平均速度: {self.total_processed/total_time.total_seconds():.0f} 条/秒")

    def update_indexes(self):
        """更新索引"""
        logger.info('🔧 更新索引...')

        try:
            # 更新表统计信息
            self.cursor.execute('ANALYZE patents;')

            # 重建全文搜索索引
            self.cursor.execute("""
                UPDATE patents
                SET search_vector = to_tsvector('chinese',
                    COALESCE(patent_name, '') || ' ' ||
                    COALESCE(abstract, '') || ' ' ||
                    COALESCE(claims, '')
                )
                WHERE search_vector IS NULL OR (
                    patent_name IS NOT NULL OR
                    abstract IS NOT NULL OR
                    claims IS NOT NULL
                );
            """)

            self.conn.commit()
            logger.info('✅ 索引更新完成')

        except Exception as e:
            logger.error(f"❌ 更新索引失败: {e}")

    def cleanup(self):
        """清理资源"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info('🧹 资源清理完成')


def main():
    """主函数"""
    logger.info('🚀 开始专利数据批量导入')

    # 获取数据目录
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
    else:
        data_directory = input('请输入CSV数据目录路径: ').strip()

    if not os.path.exists(data_directory):
        logger.error(f"❌ 目录不存在: {data_directory}")
        return

    # 创建导入器
    importer = PatentDataImporter()

    try:
        # 连接数据库
        importer.connect_db()

        # 清理现有无效数据
        importer.clean_existing_data()

        # 处理数据
        importer.process_directory(data_directory)

        # 更新索引
        importer.update_indexes()

    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断导入")
    except Exception as e:
        logger.error(f"❌ 导入过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        importer.cleanup()


if __name__ == '__main__':
    main()