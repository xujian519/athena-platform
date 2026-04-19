#!/usr/bin/env python3
"""
PostgreSQL元数据存储客户端
PostgreSQL Metadata Storage for Patent Judgments

功能:
- 存储判决书元数据
- 存储论点元数据
- 存储法律条文引用关系
- 支持全文检索
"""

from __future__ import annotations
import json
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


class PostgreSQLClient:
    """PostgreSQL元数据存储客户端"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化PostgreSQL客户端

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.conn = None
        self.is_connected = False

        # 从配置获取连接信息
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 5432)
        self.database = self.config.get("database", "athena_platform")
        self.user = self.config.get("user", "athena_user")
        self.password = self.config.get("password", "")

    def connect(self) -> bool:
        """
        连接到PostgreSQL

        Returns:
            是否连接成功
        """
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            logger.info(f"🔄 连接到PostgreSQL: {self.host}:{self.port}/{self.database}")

            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                cursor_factory=RealDictCursor,
            )

            self.is_connected = True
            logger.info("✅ PostgreSQL连接成功")

            return True

        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e!s}")
            self.is_connected = False
            return False

    def _is_valid_date(self, date_value) -> None:
        """验证日期值是否有效"""
        if not date_value:
            return False
        if date_value == "" or date_value is None:
            return False
        return not (isinstance(date_value, str) and date_value.strip() == "")

    def initialize_tables(self) -> bool:
        """
        初始化数据库表

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到PostgreSQL")
            return False

        try:
            with self.conn.cursor() as cursor:
                # 创建判决书表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS patent_judgments (
                        case_id VARCHAR(255) PRIMARY KEY,
                        court VARCHAR(255),
                        level VARCHAR(100),
                        case_type VARCHAR(255),
                        judgment_date DATE,
                        plaintiff VARCHAR(500),
                        defendant VARCHAR(500),
                        third_party VARCHAR(500),
                        full_text TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建论点表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS judgment_arguments (
                        argument_id VARCHAR(255) PRIMARY KEY,
                        case_id VARCHAR(255) REFERENCES patent_judgments(case_id),
                        dispute_focus TEXT,
                        argument_logic JSONB,
                        confidence FLOAT,
                        layer_name VARCHAR(10),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_layer CHECK (layer_name IN ('L1', 'L2', 'L3'))
                    )
                """)

                # 创建法律条文引用表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS legal_article_references (
                        id SERIAL PRIMARY KEY,
                        argument_id VARCHAR(255) REFERENCES judgment_arguments(argument_id),
                        article_name VARCHAR(255),
                        article_content TEXT,
                        is_direct_quote BOOLEAN,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建全文检索索引(使用默认配置)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_judgments_fulltext
                    ON patent_judgments USING gin(to_tsvector('simple', full_text))
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_arguments_fulltext
                    ON judgment_arguments USING gin(to_tsvector('simple', dispute_focus))
                """)

                # 创建向量ID索引(用于Qdrant同步)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_arguments_vector_id
                    ON judgment_arguments(argument_id)
                """)

                # 创建更新时间触发器
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql'
                """)

                cursor.execute("""
                    DROP TRIGGER IF EXISTS update_patent_judgments_updated_at ON patent_judgments
                """)
                cursor.execute("""
                    CREATE TRIGGER update_patent_judgments_updated_at
                    BEFORE UPDATE ON patent_judgments
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
                """)

                self.conn.commit()
                logger.info("✅ 数据库表初始化成功")
                return True

        except Exception as e:
            logger.error(f"❌ 初始化表失败: {e!s}")
            self.conn.rollback()
            return False

    def insert_judgment(self, judgment_data: dict[str, Any]) -> bool:
        """
        插入判决书元数据

        Args:
            judgment_data: 判决书数据

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到PostgreSQL")
            return False

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO patent_judgments (
                        case_id, court, level, case_type, judgment_date,
                        plaintiff, defendant, third_party, full_text, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (case_id) DO UPDATE SET
                        court = EXCLUDED.court,
                        level = EXCLUDED.level,
                        case_type = EXCLUDED.case_type,
                        judgment_date = CASE WHEN EXCLUDED.judgment_date IS NULL THEN patent_judgments.judgment_date ELSE EXCLUDED.judgment_date END,
                        plaintiff = EXCLUDED.plaintiff,
                        defendant = EXCLUDED.defendant,
                        third_party = EXCLUDED.third_party,
                        full_text = EXCLUDED.full_text,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        judgment_data["case_id"],
                        judgment_data.get("court", ""),
                        judgment_data.get("level", ""),
                        judgment_data.get("case_type", ""),
                        (
                            judgment_data.get("date")
                            if self._is_valid_date(judgment_data.get("date"))
                            else None
                        ),
                        judgment_data.get("plaintiff", ""),
                        judgment_data.get("defendant", ""),
                        judgment_data.get("third_party", ""),
                        judgment_data.get("full_text", ""),
                        json.dumps(judgment_data.get("metadata", {}), ensure_ascii=False),
                    ),
                )

            self.conn.commit()
            logger.debug(f"✅ 插入判决书: {judgment_data['case_id']}")
            return True

        except Exception as e:
            logger.error(f"❌ 插入判决书失败: {e!s}")
            self.conn.rollback()
            return False

    def insert_argument(self, argument_data: dict[str, Any]) -> bool:
        """
        插入论点元数据

        Args:
            argument_data: 论点数据

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到PostgreSQL")
            return False

        try:
            with self.conn.cursor() as cursor:
                # 插入论点
                cursor.execute(
                    """
                    INSERT INTO judgment_arguments (
                        argument_id, case_id, dispute_focus,
                        argument_logic, confidence, layer_name
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (argument_id) DO UPDATE SET
                        dispute_focus = EXCLUDED.dispute_focus,
                        argument_logic = EXCLUDED.argument_logic,
                        confidence = EXCLUDED.confidence
                """,
                    (
                        argument_data["argument_id"],
                        argument_data["case_id"],
                        argument_data.get("dispute_focus", ""),
                        json.dumps(argument_data.get("argument_logic", {}), ensure_ascii=False),
                        argument_data.get("confidence", 0.8),
                        argument_data.get("layer", "L3"),
                    ),
                )

                # 插入法律条文引用
                for article_ref in argument_data.get("legal_articles", []):
                    cursor.execute(
                        """
                        INSERT INTO legal_article_references (
                            argument_id, article_name, article_content, is_direct_quote
                        ) VALUES (
                            %s, %s, %s, %s
                        )
                    """,
                        (
                            argument_data["argument_id"],
                            article_ref.get("article_name", ""),
                            article_ref.get("article_content", ""),
                            article_ref.get("is_direct_quote", False),
                        ),
                    )

                self.conn.commit()
                logger.debug(f"✅ 插入论点: {argument_data['argument_id']}")
                return True

        except Exception as e:
            logger.error(f"❌ 插入论点失败: {e!s}")
            self.conn.rollback()
            return False

    def fulltext_search(
        self, query: str, table: str = "patent_judgments", limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        全文检索

        Args:
            query: 查询文本
            table: 表名
            limit: 返回数量

        Returns:
            搜索结果列表
        """
        if not self.is_connected:
            return []

        try:
            with self.conn.cursor() as cursor:
                if table == "patent_judgments":
                    cursor.execute(
                        """
                        SELECT
                            case_id,
                            court,
                            case_type,
                            ts_rank(to_tsvector('simple', full_text), plainto_tsquery('simple', %s)) AS rank
                        FROM patent_judgments
                        WHERE to_tsvector('simple', full_text) @@ plainto_tsquery('simple', %s)
                        ORDER BY rank DESC
                        LIMIT %s
                    """,
                        (query, query, limit),
                    )

                elif table == "judgment_arguments":
                    cursor.execute(
                        """
                        SELECT
                            argument_id,
                            case_id,
                            dispute_focus,
                            ts_rank(to_tsvector('simple', dispute_focus), plainto_tsquery('simple', %s)) AS rank
                        FROM judgment_arguments
                        WHERE to_tsvector('simple', dispute_focus) @@ plainto_tsquery('simple', %s)
                        ORDER BY rank DESC
                        LIMIT %s
                    """,
                        (query, query, limit),
                    )

                results = cursor.fetchall()

                logger.info(f"🔍 全文检索完成: {len(results)}个结果")
                return results

        except Exception as e:
            logger.error(f"❌ 全文检索失败: {e!s}")
            return []

    def get_judgment_by_id(self, case_id: str) -> dict[str, Any] | None:
        """
        根据案号获取判决书

        Args:
            case_id: 案号

        Returns:
            判决书数据
        """
        if not self.is_connected:
            return None

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM patent_judgments
                    WHERE case_id = %s
                """,
                    (case_id,),
                )

                result = cursor.fetchone()
                return result

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return None

    def get_arguments_by_case(self, case_id: str) -> list[dict[str, Any]]:
        """
        获取某判决书的全部论点

        Args:
            case_id: 案号

        Returns:
            论点列表
        """
        if not self.is_connected:
            return []

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM judgment_arguments
                    WHERE case_id = %s
                    ORDER BY argument_id
                """,
                    (case_id,),
                )

                results = cursor.fetchall()
                return results

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return []

    def print_status(self) -> Any:
        """打印数据库状态"""
        if not self.is_connected:
            print("❌ 未连接到PostgreSQL")
            return

        try:
            with self.conn.cursor() as cursor:
                # 统计判决书数量
                cursor.execute("SELECT COUNT(*) as count FROM patent_judgments")
                judgment_count = cursor.fetchone()["count"]

                # 统计论点数量
                cursor.execute("SELECT COUNT(*) as count FROM judgment_arguments")
                argument_count = cursor.fetchone()["count"]

                # 统计法律条文引用数量
                cursor.execute("SELECT COUNT(*) as count FROM legal_article_references")
                ref_count = cursor.fetchone()["count"]

                print("\n" + "=" * 60)
                print("📊 PostgreSQL元数据存储状态")
                print("=" * 60)
                print(f"连接: {self.host}:{self.port}/{self.database}")
                print("\n数据统计:")
                print(f"  判决书: {judgment_count}份")
                print(f"  论点: {argument_count}个")
                print(f"  法条引用: {ref_count}条")
                print("=" * 60 + "\n")

        except Exception as e:
            logger.error(f"❌ 获取状态失败: {e!s}")

    def close(self) -> Any:
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.is_connected = False
            logger.info("✅ PostgreSQL连接已关闭")


# 便捷函数
def get_postgres_client(config: dict[str, Any] | None = None) -> PostgreSQLClient | None:
    """
    获取PostgreSQL客户端单例

    Args:
        config: 配置字典

    Returns:
        PostgreSQL客户端实例
    """
    client = PostgreSQLClient(config)
    if client.connect():
        return client
    return None


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    # 加载配置
    import yaml

    with open("/Users/xujian/Athena工作平台/config/judgment_vector_db_config.yaml") as f:
        config = yaml.safe_load(f)

    # 创建客户端
    client = get_postgres_client(config["postgresql"])

    if client:
        # 初始化表
        client.initialize_tables()

        # 打印状态
        client.print_status()

        # 关闭连接
        client.close()
