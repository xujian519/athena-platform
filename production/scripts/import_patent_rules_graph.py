#!/usr/bin/env python3
"""
patent_rules图空间导入脚本
作者: 小诺·双鱼公主 v4.0.0
日期: 2025-12-28
"""

from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from typing import Any

from nebula3.gclient.net import ConnectionPool


def get_env_password(key: str, default: str = "") -> str:
    """从环境变量获取密码"""
    return os.environ.get(key, default)

# 修复Config导入
try:
    from nebula3.Config import Config
except ImportError:
    # 尝试直接从Config类导入
    Config = __import__('nebula3.Config').Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentRulesGraphImporter:
    """专利规则知识图谱导入器"""

    def __init__(self, host="127.0.0.1", port=9669, user="root", password=get_env_password('NEBULA_PASSWORD')):
        """初始化导入器"""
        self.config = Config()
        self.config.max_connection_pool_size = 10
        self.connection_pool = ConnectionPool()

        # 连接NebulaGraph
        try:
            if not self.connection_pool.init([(host, port)], user, password):
                logger.error("❌ 连接NebulaGraph失败!")
                raise Exception("连接失败")
            logger.info(f"✅ 成功连接到NebulaGraph: {host}:{port}")
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            raise

        self.space_name = "patent_rules"
        self.data_dir = "/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph"

    def execute_query(self, query, description="") -> None:
        """执行查询"""
        logger.info(f"🔧 执行: {description or query}")

        session = self.connection_pool.get_session('root', 'nebula')
        try:
            result = session.execute(query)
            if not result.is_succeeded():
                logger.error(f"❌ 查询失败: {result.error_msg()}")
                return False
            logger.info("✅ 查询成功")
            return True
        except Exception as e:
            logger.error(f"❌ 查询异常: {e}")
            return False
        finally:
            session.release()

    def create_space(self) -> Any:
        """创建图空间"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 步骤1: 创建图空间 {self.space_name}")
        logger.info(f"{'='*60}\n")

        query = f"""
        CREATE SPACE IF NOT EXISTS {self.space_name} (
            partition_num = 10,
            replica_factor = 1,
            vid_type = FIXED_STRING(256)
        );
        """

        if self.execute_query(query, f"创建图空间 {self.space_name}"):
            logger.info("⏳ 等待10秒让图空间初始化...")
            import time
            time.sleep(10)
            return True
        return False

    def use_space(self) -> Any:
        """使用图空间"""
        query = f"USE {self.space_name};"
        return self.execute_query(query, f"使用图空间 {self.space_name}")

    def create_tags(self) -> Any:
        """创建标签"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 步骤2: 创建标签(Tags)")
        logger.info(f"{'='*60}\n")

        # 创建legal_term标签
        query = """
        CREATE TAG IF NOT EXISTS legal_term(
            name string,
            definition string,
            category string,
            source string,
            confidence double,
            created_at string
        );
        """
        self.execute_query(query, "创建legal_term标签")

        # 创建document标签
        query = """
        CREATE TAG IF NOT EXISTS document(
            title string,
            doc_type string,
            publish_date string,
            source string,
            confidence double,
            created_at string
        );
        """
        self.execute_query(query, "创建document标签")

        # 创建tech_field标签
        query = """
        CREATE TAG IF NOT EXISTS tech_field(
            name string,
            description string,
            level string,
            keywords string,
            confidence double,
            created_at string
        );
        """
        self.execute_query(query, "创建tech_field标签")

        return True

    def create_edges(self) -> Any:
        """创建边类型"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 步骤3: 创建边类型(Edges)")
        logger.info(f"{'='*60}\n")

        # 创建related_to边
        query = """
        CREATE EDGE IF NOT EXISTS related_to(
            relation_type string,
            strength double,
            confidence double,
            created_at string
        );
        """
        self.execute_query(query, "创建related_to边")

        # 创建refers_to边
        query = """
        CREATE EDGE IF NOT EXISTS refers_to(
            relationship_type string,
            confidence double,
            created_at string
        );
        """
        self.execute_query(query, "创建refers_to边")

        # 创建applies_to边
        query = """
        CREATE EDGE IF NOT EXISTS applies_to(
            context string,
            relevance double,
            confidence double,
            created_at string
        );
        """
        self.execute_query(query, "创建applies_to边")

        return True

    def import_legal_terms(self) -> Any:
        """导入法律术语实体"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 步骤4: 导入法律术语实体")
        logger.info(f"{'='*60}\n")

        # 读取legal_term数据
        legal_term_file = os.path.join(self.data_dir, "entities_LEGAL_TERM.json")

        if not os.path.exists(legal_term_file):
            logger.warning(f"⚠️ 文件不存在: {legal_term_file}")
            return False

        with open(legal_term_file, encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"📄 读取到 {len(data)} 个法律术语")

        # 导入数据
        session = self.connection_pool.get_session('root', 'nebula')
        try:
            for item in data:
                vid = item.get('id', item.get('name', ''))
                query = f"""
                INSERT VERTEX legal_term(name, definition, category, source, confidence, created_at)
                VALUES "{vid}": "{item.get('name', '')}", "{item.get('definition', '')}",
                          "{item.get('category', '')}", "{item.get('source', '')}",
                          {item.get('confidence', 0.0)}, "{datetime.now().isoformat()}";
                """
                result = session.execute(query)
                if not result.is_succeeded():
                    logger.warning(f"⚠️ 插入失败: {vid}")

            logger.info("✅ 法律术语导入完成")
            return True
        except Exception as e:
            logger.error(f"❌ 导入异常: {e}")
            return False
        finally:
            session.release()

    def import_documents(self) -> Any:
        """导入文档实体"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 步骤5: 导入文档实体")
        logger.info(f"{'='*60}\n")

        # 查找guideline相关文件
        guideline_file = os.path.join(self.data_dir, "guideline_entities_20251223_054048.json")

        if not os.path.exists(guideline_file):
            logger.warning(f"⚠️ 文件不存在: {guideline_file}")
            return False

        with open(guideline_file, encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"📄 读取到 {len(data)} 个文档实体")

        # 导入数据
        session = self.connection_pool.get_session('root', 'nebula')
        try:
            for item in data[:100]:  # 先导入100个测试
                vid = item.get('id', item.get('title', ''))
                query = f"""
                INSERT VERTEX document(title, doc_type, publish_date, source, confidence, created_at)
                VALUES "{vid}": "{item.get('title', '')}", "{item.get('doc_type', 'document')}",
                          "{item.get('publish_date', '')}", "{item.get('source', 'guideline')}",
                          {item.get('confidence', 0.9)}, "{datetime.now().isoformat()}";
                """
                result = session.execute(query)
                if not result.is_succeeded():
                    logger.warning(f"⚠️ 插入失败: {vid}")

            logger.info("✅ 文档实体导入完成(前100个)")
            return True
        except Exception as e:
            logger.error(f"❌ 导入异常: {e}")
            return False
        finally:
            session.release()

    def import_relations(self) -> Any:
        """导入关系数据"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 步骤6: 导入关系数据")
        logger.info(f"{'='*60}\n")

        # 读取关系数据
        relation_file = os.path.join(self.data_dir, "relations_related_to.json")

        if not os.path.exists(relation_file):
            logger.warning(f"⚠️ 文件不存在: {relation_file}")
            return False

        with open(relation_file, encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"📄 读取到 {len(data)} 条关系")

        # 导入数据
        session = self.connection_pool.get_session('root', 'nebula')
        try:
            for item in data[:50]:  # 先导入50条测试
                src = item.get('from', '')
                dst = item.get('to', '')
                query = f"""
                INSERT EDGE related_to(relation_type, strength, confidence, created_at)
                VALUES "{src}"->"{dst}": "{item.get('relation', 'related')}",
                           {item.get('strength', 0.5)}, {item.get('confidence', 0.8)},
                           "{datetime.now().isoformat()}";
                """
                result = session.execute(query)
                if not result.is_succeeded():
                    logger.warning(f"⚠️ 插入失败: {src} -> {dst}")

            logger.info("✅ 关系数据导入完成(前50条)")
            return True
        except Exception as e:
            logger.error(f"❌ 导入异常: {e}")
            return False
        finally:
            session.release()

    def verify_import(self) -> bool:
        """验证导入结果"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 步骤7: 验证导入结果")
        logger.info(f"{'='*60}\n")

        session = self.connection_pool.get_session('root', 'nebula')
        try:
            # 统计节点数
            query = f"USE {self.space_name}; MATCH (v) RETURN count(v) AS node_count;"
            result = session.execute(query)
            if result.is_succeeded():
                node_count = result.row_values(0)[0] if result.row_size() > 0 else 0
                logger.info(f"✅ 节点总数: {node_count}")

            # 统计边数
            query = f"USE {self.space_name}; MATCH ()-[e]->() RETURN count(e) AS edge_count;"
            result = session.execute(query)
            if result.is_succeeded():
                edge_count = result.row_values(0)[0] if result.row_size() > 0 else 0
                logger.info(f"✅ 边总数: {edge_count}")

            # 查询样例
            query = f"USE {self.space_name}; MATCH (v:legal_term) RETURN v LIMIT 5;"
            result = session.execute(query)
            if result.is_succeeded():
                logger.info("✅ 法律术语样例:")
                for row in result:
                    logger.info(f"   - {row}")

            return True
        except Exception as e:
            logger.error(f"❌ 验证异常: {e}")
            return False
        finally:
            session.release()

    def run(self) -> None:
        """执行完整导入流程"""
        logger.info(f"\n{'='*60}")
        logger.info("🚀 开始patent_rules图空间导入流程")
        logger.info(f"时间: {datetime.now().isoformat()}")
        logger.info(f"{'='*60}\n")

        try:
            # 1. 创建图空间
            if not self.create_space():
                logger.error("❌ 创建图空间失败")
                return False

            # 2. 使用图空间
            if not self.use_space():
                logger.error("❌ 使用图空间失败")
                return False

            # 3. 创建标签
            if not self.create_tags():
                logger.error("❌ 创建标签失败")
                return False

            # 4. 创建边类型
            if not self.create_edges():
                logger.error("❌ 创建边类型失败")
                return False

            # 5. 导入数据
            self.import_legal_terms()
            self.import_documents()
            self.import_relations()

            # 6. 验证结果
            self.verify_import()

            logger.info(f"\n{'='*60}")
            logger.info("✅ patent_rules图空间导入完成!")
            logger.info(f"{'='*60}\n")
            return True

        except Exception as e:
            logger.error(f"❌ 导入流程异常: {e}")
            return False
        finally:
            self.connection_pool.close()
            logger.info("🔌 连接已关闭")

def main() -> None:
    """主函数"""
    importer = PatentRulesGraphImporter()
    importer.run()

if __name__ == "__main__":
    main()
