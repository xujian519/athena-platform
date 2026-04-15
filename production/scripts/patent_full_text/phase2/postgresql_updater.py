#!/usr/bin/env python3
"""
PostgreSQL自动更新模块
将PDF处理结果更新到PostgreSQL patents表

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from core.config.secure_config import get_config

config = get_config()

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# 导入安全配置
try:
    from production.config import get_postgres_config
except ImportError:
    def get_postgres_config() -> Any | None:
        return {
            'host': 'localhost',
            'port': 5432,
            'user': 'athena',
            "password": config.get("POSTGRES_PASSWORD", required=True),
            'database': 'patent_db'
        }

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("⚠️ psycopg2未安装")


@dataclass
class UpdateResult:
    """更新结果"""
    patent_number: str
    success: bool
    postgres_id: str | None = None
    error_message: str | None = None
    updated_fields: list[str] = None

    def __post_init__(self):
        if self.updated_fields is None:
            self.updated_fields = []


class PostgreSQLUpdater:
    """PostgreSQL更新器"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None
    ):
        """
        初始化更新器

        Args:
            host: 数据库主机 (如果为None,从配置读取)
            port: 端口 (如果为None,从配置读取)
            database: 数据库名 (如果为None,从配置读取)
            user: 用户名 (如果为None,从配置读取)
            password: 密码 (如果为None,从配置读取)
        """
        # 从配置获取默认值
        config = get_postgres_config()
        self.host = host or config.get('host', 'localhost')
        self.port = port or config.get('port', 5432)
        self.database = database or config.get('database', 'patent_db')
        self.user = user or config.get('user', 'athena')
        self.password = password or config.get("password", config.get("POSTGRES_PASSWORD", required=True))

        self.conn = None

        if PSYCOPG2_AVAILABLE:
            self._connect()

    def _connect(self) -> Any:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"✅ 连接PostgreSQL成功: {self.database}")

        except Exception as e:
            logger.error(f"❌ 连接PostgreSQL失败: {e}")
            self.conn = None

    def update_pdf_info(
        self,
        patent_number: str,
        pdf_path: str,
        pdf_source: str = "patent_search",
        file_size: int | None = None
    ) -> UpdateResult:
        """
        更新PDF信息

        Args:
            patent_number: 专利号
            pdf_path: PDF文件路径
            pdf_source: PDF来源
            file_size: 文件大小

        Returns:
            UpdateResult: 更新结果
        """
        if not self.conn:
            return UpdateResult(
                patent_number=patent_number,
                success=False,
                error_message="数据库未连接"
            )

        try:
            with self.conn.cursor() as cursor:
                # 查找专利记录
                cursor.execute(
                    """
                    SELECT id FROM patents
                    WHERE publication_number = %s OR application_number = %s
                    LIMIT 1
                    """,
                    (patent_number, patent_number)
                )

                result = cursor.fetchone()
                if not result:
                    return UpdateResult(
                        patent_number=patent_number,
                        success=False,
                        error_message="未找到专利记录"
                    )

                postgres_id = result[0]

                # 更新PDF信息
                update_fields = ["pdf_path", "pdf_source", "pdf_downloaded_at"]
                values = [pdf_path, pdf_source, datetime.now()]
                params = []

                if file_size is not None:
                    update_fields.append("pdf_filesize")
                    values.append(file_size)

                # 构建SQL
                set_clause = ", ".join([f"{field} = %s" for field in update_fields])
                sql = f"""
                UPDATE patents
                SET {set_clause}
                WHERE id = %s
                """

                values.append(postgres_id)
                cursor.execute(sql, values)
                self.conn.commit()

                logger.info(f"✅ 更新PDF信息成功: {patent_number}")

                return UpdateResult(
                    patent_number=patent_number,
                    success=True,
                    postgres_id=str(postgres_id),
                    updated_fields=update_fields
                )

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 更新PDF信息失败: {e}")
            return UpdateResult(
                patent_number=patent_number,
                success=False,
                error_message=str(e)
            )

    def update_vector_info(
        self,
        patent_number: str,
        vector_ids: dict[str, str]
    ) -> UpdateResult:
        """
        更新向量ID

        Args:
            patent_number: 专利号
            vector_ids: 向量ID字典 {"title": "xxx", "abstract": "xxx", ...}

        Returns:
            UpdateResult: 更新结果
        """
        if not self.conn:
            return UpdateResult(
                patent_number=patent_number,
                success=False,
                error_message="数据库未连接"
            )

        try:
            with self.conn.cursor() as cursor:
                # 查找专利记录
                cursor.execute(
                    """
                    SELECT id FROM patents
                    WHERE publication_number = %s OR application_number = %s
                    LIMIT 1
                    """,
                    (patent_number, patent_number)
                )

                result = cursor.fetchone()
                if not result:
                    return UpdateResult(
                        patent_number=patent_number,
                        success=False,
                        error_message="未找到专利记录"
                    )

                postgres_id = result[0]

                # 更新主向量ID（使用full text的向量）
                main_vector_id = vector_ids.get("full", vector_ids.get("abstract", ""))

                # 构建更新数据
                vector_data = {}
                for section, vector_id in vector_ids.items():
                    vector_data[f"vector_{section}"] = vector_id

                # 更新主向量ID
                if main_vector_id:
                    sql = """
                    UPDATE patents
                    SET vector_id = %s,
                        vectorized_at = %s,
                        full_text_processed = TRUE
                    WHERE id = %s
                    """

                    cursor.execute(sql, (main_vector_id, datetime.now(), postgres_id))

                self.conn.commit()

                logger.info(f"✅ 更新向量ID成功: {patent_number}")

                return UpdateResult(
                    patent_number=patent_number,
                    success=True,
                    postgres_id=str(postgres_id),
                    updated_fields=["vector_id", "vectorized_at", "full_text_processed"]
                )

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 更新向量ID失败: {e}")
            return UpdateResult(
                patent_number=patent_number,
                success=False,
                error_message=str(e)
            )

    def update_kg_info(
        self,
        patent_number: str,
        kg_vertex_id: str
    ) -> UpdateResult:
        """
        更新知识图谱顶点ID

        Args:
            patent_number: 专利号
            kg_vertex_id: NebulaGraph顶点ID

        Returns:
            UpdateResult: 更新结果
        """
        if not self.conn:
            return UpdateResult(
                patent_number=patent_number,
                success=False,
                error_message="数据库未连接"
            )

        try:
            with self.conn.cursor() as cursor:
                # 查找专利记录
                cursor.execute(
                    """
                    SELECT id FROM patents
                    WHERE publication_number = %s OR application_number = %s
                    LIMIT 1
                    """,
                    (patent_number, patent_number)
                )

                result = cursor.fetchone()
                if not result:
                    return UpdateResult(
                        patent_number=patent_number,
                        success=False,
                        error_message="未找到专利记录"
                    )

                postgres_id = result[0]

                # 更新知识图谱ID
                sql = """
                UPDATE patents
                SET kg_vertex_id = %s,
                    kg_processed_at = %s,
                    full_text_processed = TRUE
                WHERE id = %s
                """

                cursor.execute(sql, (kg_vertex_id, datetime.now(), postgres_id))
                self.conn.commit()

                logger.info(f"✅ 更新知识图谱ID成功: {patent_number}")

                return UpdateResult(
                    patent_number=patent_number,
                    success=True,
                    postgres_id=str(postgres_id),
                    updated_fields=["kg_vertex_id", "kg_processed_at", "full_text_processed"]
                )

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 更新知识图谱ID失败: {e}")
            return UpdateResult(
                patent_number=patent_number,
                success=False,
                error_message=str(e)
            )

    def update_all(
        self,
        patent_number: str,
        pdf_path: str | None = None,
        vector_ids: dict[str, str] | None = None,
        kg_vertex_id: str | None = None
    ) -> dict[str, UpdateResult]:
        """
        更新所有信息

        Args:
            patent_number: 专利号
            pdf_path: PDF路径
            vector_ids: 向量ID字典
            kg_vertex_id: 知识图谱顶点ID

        Returns:
            Dict[str, UpdateResult]: 各项更新结果
        """
        results = {}

        # 更新PDF信息
        if pdf_path:
            results["pdf"] = self.update_pdf_info(patent_number, pdf_path)

        # 更新向量ID
        if vector_ids:
            results["vector"] = self.update_vector_info(patent_number, vector_ids)

        # 更新知识图谱ID
        if kg_vertex_id:
            results["kg"] = self.update_kg_info(patent_number, kg_vertex_id)

        return results

    def get_patent_by_publication_number(self, publication_number: str) -> dict[str, Any | None]:
        """
        根据公开号获取专利信息

        Args:
            publication_number: 公开号

        Returns:
            Dict[str, Any]: 专利信息
        """
        if not self.conn:
            return None

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM patents
                    WHERE publication_number = %s
                    LIMIT 1
                    """,
                    (publication_number,)
                )

                return cursor.fetchone()

        except Exception as e:
            logger.error(f"❌ 查询专利失败: {e}")
            return None

    def close(self) -> Any:
        """关闭连接"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 PostgreSQL连接已关闭")


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    updater = PostgreSQLUpdater()

    if not updater.conn:
        logger.error("❌ 无法连接PostgreSQL，跳过示例")
        return

    print("=" * 70)
    print("PostgreSQL更新示例")
    print("=" * 70)

    # 示例1: 更新PDF信息
    print("\n📋 示例1: 更新PDF信息")
    result = updater.update_pdf_info(
        patent_number="CN112233445A",
        pdf_path="/Users/xujian/apps/apps/patents/PDF/CN/CN112233445A.pdf",
        pdf_source="patent_search",
        file_size=382439
    )

    print(f"   成功: {result.success}")
    print(f"   PostgreSQL ID: {result.postgres_id}")
    print(f"   更新字段: {result.updated_fields}")

    # 示例2: 更新向量ID
    print("\n📋 示例2: 更新向量ID")
    result = updater.update_vector_info(
        patent_number="CN112233445A",
        vector_ids={
            "title": "patent_CN112233445A_title",
            "abstract": "patent_CN112233445A_abstract",
            "full": "patent_CN112233445A_full"
        }
    )

    print(f"   成功: {result.success}")
    print(f"   更新字段: {result.updated_fields}")

    # 示例3: 更新知识图谱ID
    print("\n📋 示例3: 更新知识图谱ID")
    result = updater.update_kg_info(
        patent_number="CN112233445A",
        kg_vertex_id="abc123def456"
    )

    print(f"   成功: {result.success}")
    print(f"   更新字段: {result.updated_fields}")

    # 示例4: 批量更新
    print("\n📋 示例4: 批量更新所有信息")
    results = updater.update_all(
        patent_number="CN112233445A",
        pdf_path="/Users/xujian/apps/apps/patents/PDF/CN/CN112233445A.pdf",
        vector_ids={
            "title": "patent_CN112233445A_title",
            "full": "patent_CN112233445A_full"
        },
        kg_vertex_id="abc123def456"
    )

    for key, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"{status} {key}: {result.updated_fields}")

    updater.close()


if __name__ == "__main__":
    main()
