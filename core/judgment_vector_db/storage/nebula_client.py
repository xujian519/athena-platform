#!/usr/bin/env python3
"""
⚠️  DEPRECATED - NebulaGraph版本已废弃
DEPRECATED - NebulaGraph version deprecated

废弃日期: 2026-01-26
废弃原因: TD-001 - 系统已迁移到Neo4j
影响范围: 整个文件
建议操作: 使用 core/judgment_vector_db/storage/neo4j_client.py

原功能说明:
NebulaGraph知识图谱客户端
NebulaGraph Knowledge Graph Client for Patent Judgments

功能:
- 管理专利判决知识图谱
- 存储/查询 法律条文→裁判规则→典型案例 关系
- 图谱遍历和推理
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from core.config.secure_config import get_config
from core.logging_config import setup_logging

config = get_config()


logger = setup_logging()


class NebulaGraphClient:
    """NebulaGraph知识图谱客户端"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化NebulaGraph客户端

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.session = None
        self.is_connected = False

        # 从配置获取连接信息
        self.host = self.config.get("host", "127.0.0.1")
        self.port = self.config.get("port", 9669)
        space_name = self.config.get("space_name", "patent_judgments")

        # 验证space_name(只允许字母、数字和下划线,防止nGQL注入)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", space_name):
            raise ValueError(
                f"Invalid space_name: {space_name}. Only letters, numbers and underscores are allowed."
            )

        self.space_name = space_name
        self.user = self.config.get("user", "root")
        self.password = self.config.get("password", config.get("NEBULA_PASSWORD", required=True))

    def connect(self) -> bool:
        """
        连接到NebulaGraph

        Returns:
            是否连接成功
        """
        try:
            from nebula3.gclient.net import ConnectionPool

            logger.info(f"🔄 连接到NebulaGraph: {self.host}:{self.port}")

            # 创建连接池
            self.pool = ConnectionPool()

            # 初始化连接
            self.pool.init([(self.host, self.port), self.user, self.password])

            # 获取session
            self.session = self.pool.session(self.space_name)
            self.is_connected = True

            logger.info("✅ NebulaGraph连接成功")
            return True

        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e!s}")
            self.is_connected = False
            return False

    def initialize_space(self) -> bool:
        """
        初始化图空间

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到NebulaGraph")
            return False

        try:
            # 创建空间
            # 安全说明:space_name已在__init__中通过正则验证,只包含字母、数字和下划线
            self.session.execute(f"""
                CREATE SPACE IF NOT EXISTS {self.space_name}
                (partition_num=10, replica_factor=1, vid_type=FIXED_STRING(256))
            """)

            logger.info(f"✅ 图空间创建成功: {self.space_name}")

            # 使用空间 - space_name已验证安全
            self.session.execute(f"USE {self.space_name}")

            # 创建标签(点类型)
            self._create_tags()

            # 创建边类型
            self._create_edges()

            return True

        except Exception as e:
            logger.error(f"❌ 初始化空间失败: {e!s}")
            return False

    def _create_tags(self) -> Any:
        """创建点类型(标签)"""
        tags = [
            # 法律条文
            """
            CREATE TAG IF NOT EXISTS legal_article(
                name string,
                content string,
                article_type string
            )
            """,
            # 裁判规则
            """
            CREATE TAG IF NOT EXISTS judgment_rule(
                name string,
                description string,
                applicability float,
                core_elements string,
                logic_pattern string
            )
            """,
            # 典型案例
            """
            CREATE TAG IF NOT EXISTS typical_case(
                case_id string,
                court string,
                year int,
                case_type string,
                judgment_result string,
                importance float
            )
            """,
            # 法律概念
            """
            CREATE TAG IF NOT EXISTS legal_concept(
                name string,
                definition string,
                category string
            )
            """,
            # 争议焦点
            """
            CREATE TAG IF NOT EXISTS dispute_focus(
                description string,
                category string
            )
            """,
        ]

        for tag in tags:
            try:
                self.session.execute(tag)
                logger.info("✅ 创建标签成功")
            except Exception as e:
                logger.warning(f"⚠️ 创建标签失败: {e!s}")

    def _create_edges(self) -> Any:
        """创建边类型"""
        edges = [
            # 适用于
            """
            CREATE EDGE IF NOT EXISTS applies_to(
                applicability_count int DEFAULT 0
            )
            """,
            # 来源于
            """
            CREATE EDGE IF NOT EXISTS derived_from(
                reasoning string
            )
            """,
            # 关联
            """
            CREATE EDGE IF NOT EXISTS relates_to(
                relationship_type string
            )
            """,
            # 解决
            """
            CREATE EDGE IF NOT EXISTS addresses(
                focus_level int
            )
            """,
            # 引用
            """
            CREATE EDGE IF NOT EXISTS cites(
                citation_count int DEFAULT 0
            )
            """,
        ]

        for edge in edges:
            try:
                self.session.execute(edge)
                logger.info("✅ 创建边成功")
            except Exception as e:
                logger.warning(f"⚠️ 创建边失败: {e!s}")

    def insert_legal_article(
        self, name: str, content: str = "", article_type: str = "statute"
    ) -> bool:
        """
        插入法律条文

        Args:
            name: 条文名称(如:专利法第22条第3款)
            content: 条文内容
            article_type: 类型

        Returns:
            是否成功
        """
        try:
            # 生成VID
            vid = f"legal_article_{name}"

            # 插入点
            self.session.execute(f"""
                INSERT VERTEX legal_article(
                    "{vid}",
                    name, "{content}", "{article_type}"
                )
            """)

            logger.debug(f"✅ 插入法律条文: {name}")
            return True

        except Exception as e:
            logger.error(f"❌ 插入法律条文失败: {e!s}")
            return False

    def insert_judgment_rule(
        self,
        name: str,
        description: str,
        applicability: float,
        core_elements: list[str],
        logic_pattern: str = "",
    ) -> bool:
        """
        插入裁判规则

        Args:
            name: 规则名称
            description: 描述
            applicability: 适用率
            core_elements: 核心要素列表
            logic_pattern: 逻辑模式

        Returns:
            是否成功
        """
        try:
            vid = f"judgment_rule_{name}"

            self.session.execute(f"""
                INSERT VERTEX judgment_rule(
                    "{vid}",
                    name, "{description}",
                    {applicability},
                    "{','.join(core_elements)}",
                    "{logic_pattern}"
                )
            """)

            logger.debug(f"✅ 插入裁判规则: {name}")
            return True

        except Exception as e:
            logger.error(f"❌ 插入裁判规则失败: {e!s}")
            return False

    def insert_typical_case(
        self,
        case_id: str,
        court: str,
        year: int,
        case_type: str,
        judgment_result: str,
        importance: float = 1.0,
    ) -> bool:
        """
        插入典型案例

        Args:
            case_id: 案号
            court: 法院
            year: 年份
            case_type: 案由
            judgment_result: 判决结果
            importance: 重要性

        Returns:
            是否成功
        """
        try:
            vid = f"typical_case_{case_id}"

            self.session.execute(f"""
                INSERT VERTEX typical_case(
                    "{vid}",
                    case_id, court, {year},
                    "{case_type}", "{judgment_result}", {importance}
                )
            """)

            logger.debug(f"✅ 插入典型案例: {case_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 插入典型案例失败: {e!s}")
            return False

    def create_relation(self, edge_type: str, src_vid: str, dst_vid: str, **properties) -> bool:
        """
        创建关系(边)

        Args:
            edge_type: 边类型
            src_vid: 源点VID
            dst_vid: 目标点VID
            **properties: 边属性

        Returns:
            是否成功
        """
        try:
            # 构建属性字符串
            props_str = ", ".join([f"{k}={v!r}" for k, v in properties.items()])

            self.session.execute(f"""
                INSERT EDGE {edge_type}
                ON "{src_vid}" -> "{dst_vid}"
                @{props_str}
            """)

            logger.debug(f"✅ 创建关系: {src_vid} -> {dst_vid}")
            return True

        except Exception as e:
            logger.error(f"❌ 创建关系失败: {e!s}")
            return False

    def query_by_legal_article(self, article_name: str) -> list[dict[str, Any]]:
        """
        根据法律条文查询相关裁判规则和案例

        Args:
            article_name: 法律条文名称

        Returns:
            查询结果列表
        """
        try:
            result = self.session.execute(f"""
                GO FROM "legal_article_{article_name}"
                OVER applies_to YIELD applies_to
                OVER derived_from YIELD derived_from
                | YIELD $$.article.name AS article, $$.rule.name AS rule, $$.case.case_id AS case
            """)

            data = result.data()
            return data

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return []

    def query_shortest_path(self, src_type: str, dst_type: str) -> list[dict[str, Any]]:
        """
        查询最短路径

        Args:
            src_type: 源点类型
            dst_type: 目标点类型

        Returns:
            路径列表
        """
        try:
            result = self.session.execute(f"""
                FIND SHORTEST PATH FROM "{src_type}"
                TO "{dst_type}"
                OVER *
                YIELD path AS p
            """)

            data = result.data()
            return data

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return []

    def print_status(self) -> Any:
        """打印图谱状态"""
        if not self.is_connected:
            print("❌ 未连接到NebulaGraph")
            return

        try:
            print("\n" + "=" * 60)
            print("📊 NebulaGraph知识图谱状态")
            print("=" * 60)
            print(f"连接: {self.host}:{self.port}")
            print(f"空间: {self.space_name}")

            # 统计各种类型的点数量
            tag_counts = {}
            for tag in [
                "legal_article",
                "judgment_rule",
                "typical_case",
                "legal_concept",
                "dispute_focus",
            ]:
                try:
                    result = self.session.execute(f"""
                        MATCH (n:{tag})
                        RETURN count(n) AS count
                    """)
                    count = result.data()[0][0] if result.data() else 0
                    tag_counts[tag] = count
                except Exception as e:
                    logger.warning(f"⚠️ 查询{tag}节点失败: {e}")
                    tag_counts[tag] = 0

            print("\n节点统计:")
            for tag, count in tag_counts.items():
                print(f"  {tag}: {count}")

            print("=" * 60 + "\n")

        except Exception as e:
            logger.error(f"❌ 获取状态失败: {e!s}")


# 便捷函数
def get_nebula_client(config: Optional[dict[str, Any]] = None) -> NebulaGraphClient | None:
    """
    获取NebulaGraph客户端单例

    Args:
        config: 配置字典

    Returns:
        NebulaGraph客户端实例
    """
    client = NebulaGraphClient(config)
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
    client = get_nebula_client(config["nebula_graph"])

    if client:
        # 初始化空间
        client.initialize_space()

        # 打印状态
        client.print_status()
