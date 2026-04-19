#!/usr/bin/env python3
"""
法律条款知识图谱导入系统（NebulaGraph）
作者: 小诺·双鱼公主 v4.0.0
日期: 2025-12-28

功能:
1. 将已解析的法律条款导入NebulaGraph
2. 创建patent_rules图空间
3. 建立条款之间的关系
4. 支持图查询和图遍历
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from nebula3.Config import Config
    from nebula3.gclient.net import ConnectionPool
    NEBULA_AVAILABLE = True
except ImportError:
    NEBULA_AVAILABLE = False
    logging.warning("⚠️ nebula3未安装，将使用REST API方式")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NebulaGraphImporter:
    """NebulaGraph知识图谱导入器"""

    def __init__(self, host: str = "127.0.0.1", port: int = 9669,
                 username: str = "root", password: str = "nebula"):
        """
        初始化NebulaGraph连接

        Args:
            host: NebulaGraph服务器地址
            port: 端口（默认9669）
            username: 用户名
            password: 密码
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.space_name = "patent_rules"

        # 尝试使用Python SDK
        if NEBULA_AVAILABLE:
            try:
                config = Config()
                config.max_connection_pool_size = 10
                self.connection_pool = ConnectionPool()
                self.session = self.connection_pool.connect(
                    [(host, port)],
                    username,
                    password,
                    space_name=self.space_name
                )
                self.use_sdk = True
                logger.info("✅ NebulaGraph SDK连接成功")
            except Exception as e:
                logger.warning(f"⚠️ SDK连接失败: {e}，将使用REST API")
                self.use_sdk = False
        else:
            self.use_sdk = False

    def create_space(self) -> Any:
        """创建图空间"""
        logger.info(f"🌟 创建图空间: {self.space_name}")

        if self.use_sdk:
            # 使用SDK创建
            n_gql = f"CREATE SPACE IF NOT EXISTS {self.space_name} " \
                   f"(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(256));"
            try:
                result = self.session.execute(n_gql)
                if not result.is_succeeded():
                    logger.warning(f"⚠️ 创建空间失败: {result.error_msg()}")
                else:
                    logger.info("✅ 图空间创建成功")
            except Exception as e:
                logger.error(f"❌ 创建空间错误: {e}")
        else:
            # 生成nGQL脚本供手动执行
            self._generate_space_creation_script()

    def create_schema(self) -> Any:
        """创建图Schema（点和边类型）"""
        logger.info("📐 创建图Schema")

        schema_definitions = [
            # 点类型
            "CREATE TAG IF NOT EXISTS legal_article(content string, level string, effective_date string);",
            "CREATE TAG IF NOT EXISTS law_law(name string, level string);",

            # 边类型
            "CREATE EDGE IF NOT EXISTS next_article(weight double);",
            "CREATE EDGE IF NOT EXISTS same_chapter(weight double);",
            "CREATE EDGE IF NOT EXISTS refers_to(weight double);",
        ]

        for n_gql in schema_definitions:
            logger.debug(f"执行: {n_gql}")
            if self.use_sdk:
                try:
                    result = self.session.execute(n_gql)
                    if not result.is_succeeded():
                        logger.warning(f"⚠️ Schema创建失败: {result.error_msg()}")
                except Exception as e:
                    logger.warning(f"⚠️ 执行失败: {e}")

        logger.info("✅ Schema定义完成")

    def import_articles(self, articles: list[dict]) -> Any:
        """
        导入法律条款到知识图谱

        Args:
            articles: 法律条款列表
        """
        logger.info(f"📥 开始导入 {len(articles)} 个条款到知识图谱")

        if self.use_sdk:
            self._import_via_sdk(articles)
        else:
            self._import_via_rest(articles)

        logger.info("✅ 知识图谱导入完成")

    def _import_via_sdk(self, articles: list[dict]) -> Any:
        """使用Python SDK导入"""
        # 先插入点
        for i, article in enumerate(articles):
            law_id = article['law_id'].replace(' ', '_').replace('/', '_')

            # 插入顶点
            n_gql = f'INSERT VERTEX legal_article(content, level, effective_date) ' \
                   f'VALUES "{law_id}": ' \
                   f'"{article.get("content", "")[:100]}", ' \
                   f'"{article.get("level", "")}", ' \
                   f'"{article.get("effective_date", "")}";'

            try:
                result = self.session.execute(n_gql)
                if i % 50 == 0:
                    logger.info(f"📝 已插入 {i}/{len(articles)} 个顶点")
            except Exception as e:
                logger.warning(f"⚠️ 插入顶点失败 {law_id}: {e}")

        # 再插入边
        edge_count = 0
        for i, article in enumerate(articles):
            if i == 0:
                continue

            current_id = article['law_id'].replace(' ', '_').replace('/', '_')
            prev_id = articles[i-1]['law_id'].replace(' ', '_').replace('/', '_')

            # 同一法律文件内的相邻关系
            if (article['law_name'] == articles[i-1]['law_name']):
                n_gql = f'INSERT EDGE next_article(weight) VALUES ' \
                       f'"{prev_id}" -> "{current_id}": (1.0);'
                try:
                    result = self.session.execute(n_gql)
                    edge_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ 插入边失败: {e}")

        logger.info(f"✅ 插入 {edge_count} 条边")

    def _import_via_rest(self, articles: list[dict]) -> Any:
        """生成REST API导入脚本"""
        logger.info("📝 生成导入脚本")

        script_dir = Path("/Users/xujian/Athena工作平台/production/data/legal_articles")
        script_file = script_dir / "nebula_import.ngql"

        with open(script_file, 'w', encoding='utf-8') as f:
            # 写入头部
            f.write("-- NebulaGraph导入脚本\n")
            f.write(f"-- 生成时间: {datetime.now().isoformat()}\n")
            f.write(f"-- 条款数量: {len(articles)}\n\n")

            # USE space
            f.write(f"USE {self.space_name};\n\n")

            # 插入点
            f.write("-- 插入顶点\n")
            for i, article in enumerate(articles):
                law_id = article['law_id'].replace(' ', '_').replace('/', '_')
                content = article.get('content', '').replace('"', '\\"')[:100]

                f.write('INSERT VERTEX legal_article(content, level, effective_date) ')
                f.write(f'VALUES "{law_id}": ')
                f.write(f'"{content}", "{article.get("level", "")}", "{article.get("effective_date", "")}";\n')

                if (i + 1) % 50 == 0:
                    f.write(f"\n-- 批次 {i//50 + 1}\n")

            f.write("\n-- 插入边\n")
            for i, article in enumerate(articles):
                if i == 0:
                    continue

                current_id = article['law_id'].replace(' ', '_').replace('/', '_')
                prev_id = articles[i-1]['law_id'].replace(' ', '_').replace('/', '_')

                if article['law_name'] == articles[i-1]['law_name']:
                    f.write('INSERT EDGE next_article(weight) VALUES ')
                    f.write(f'"{prev_id}" -> "{current_id}": (1.0);\n')

        logger.info(f"✅ 导入脚本已保存: {script_file}")
        logger.info(f"💡 在NebulaGraph控制台中执行: source {script_file}")

    def _generate_space_creation_script(self) -> Any:
        """生成图空间创建脚本"""
        script_dir = Path("/Users/xujian/Athena工作平台/production/data/legal_articles")
        script_file = script_dir / "nebula_setup.ngql"

        with open(script_file, 'w', encoding='utf-8') as f:
            f.write("-- NebulaGraph图空间创建脚本\n")
            f.write(f"-- 生成时间: {datetime.now().isoformat()}\n\n")

            f.write("-- 创建图空间\n")
            f.write(f"CREATE SPACE IF NOT EXISTS {self.space_name} " \
                   f"(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(256));\n\n")

            f.write("-- 使用图空间\n")
            f.write(f"USE {self.space_name};\n\n")

            f.write("-- 创建点类型\n")
            f.write("CREATE TAG IF NOT EXISTS legal_article(content string, level string, effective_date string);\n")
            f.write("CREATE TAG IF NOT EXISTS law_law(name string, level string);\n\n")

            f.write("-- 创建边类型\n")
            f.write("CREATE EDGE IF NOT EXISTS next_article(weight double);\n")
            f.write("CREATE EDGE IF NOT EXISTS same_chapter(weight double);\n")
            f.write("CREATE EDGE IF NOT EXISTS refers_to(weight double);\n")

        logger.info(f"✅ 图空间创建脚本已保存: {script_file}")
        logger.info("💡 在NebulaGraph控制台中执行此脚本创建图空间")

    def verify_import(self) -> bool:
        """验证导入结果"""
        logger.info("🔍 验证知识图谱导入")

        if self.use_sdk:
            # 查询顶点数
            n_gql = f"USE {self.space_name}; " \
                   f"MATCH (v) RETURN count(v) AS vertex_count;"

            try:
                result = self.session.execute(n_gql)
                if result.is_succeeded():
                    logger.info(f"✅ 顶点数: {result}")
            except Exception as e:
                logger.warning(f"⚠️ 查询失败: {e}")
        else:
            logger.info("💡 使用以下nGQL查询验证:")
            logger.info(f"  USE {self.space_name};")
            logger.info("  MATCH (v) RETURN count(v);")
            logger.info("  MATCH ()-[e]->() RETURN count(e);")


class SimplifiedGraphBuilder:
    """简化的图谱构建器（使用JSON）"""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.graph = {
            'nodes': [],
            'links': []
        }

    def build_from_articles(self, articles: list[dict]) -> Any:
        """从法律条款构建图谱"""
        logger.info("🕸️  构建JSON格式知识图谱")

        # 添加节点
        for article in articles:
            node = {
                'id': article['law_id'],
                'name': article['article_number'],
                'type': 'legal_article',
                'law_name': article['law_name'],
                'level': article['level'],
                'properties': {
                    'content': article['content'][:200],
                    'chapter': article.get('chapter', ''),
                    'effective_date': article['effective_date']
                }
            }
            self.graph['nodes'].append(node)

        # 添加边
        for i in range(1, len(articles)):
            if articles[i]['law_name'] == articles[i-1]['law_name']:
                link = {
                    'source': articles[i-1]['law_id'],
                    'target': articles[i]['law_id'],
                    'type': 'next_article',
                    'weight': 1.0
                }
                self.graph['links'].append(link)

        logger.info(f"✅ 图谱构建完成: {len(self.graph['nodes'])} 节点, {len(self.graph['links'])} 边")

    def save(self) -> Any:
        """保存图谱"""
        logger.info(f"💾 保存图谱: {self.output_file}")

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.graph, f, ensure_ascii=False, indent=2)

        logger.info("✅ 图谱保存完成")


def main() -> None:
    """主函数"""

    # 配置
    json_file = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_articles_20251228_173733.json"
    graph_output = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_graph_final.json"

    # 加载数据
    logger.info(f"📂 加载数据: {json_file}")
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    logger.info(f"✅ 加载 {len(articles)} 个条款")

    # 1. 尝试导入NebulaGraph
    try:
        nebula = NebulaGraphImporter()
        nebula.create_space()
        nebula.create_schema()
        nebula.import_articles(articles)
        nebula.verify_import()
    except Exception as e:
        logger.warning(f"⚠️ NebulaGraph导入失败: {e}")
        logger.info("💡 将使用JSON格式保存图谱")

    # 2. 构建JSON格式图谱（备用方案）
    graph_builder = SimplifiedGraphBuilder(graph_output)
    graph_builder.build_from_articles(articles)
    graph_builder.save()

    logger.info(f"\n{'='*60}")
    logger.info("✅ 全部完成!")
    logger.info(f"{'='*60}")
    logger.info("📊 处理统计:")
    logger.info(f"  - 条款数量: {len(articles)}")
    logger.info(f"  - 图谱节点: {len(graph_builder.graph['nodes'])}")
    logger.info(f"  - 图谱边: {len(graph_builder.graph['links'])}")
    logger.info("💾 输出文件:")
    logger.info(f"  - JSON图谱: {graph_output}")
    logger.info("  - NebulaGraph脚本: production/data/legal_articles/nebula_*.ngql")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
