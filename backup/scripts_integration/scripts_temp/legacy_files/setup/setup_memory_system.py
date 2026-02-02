#!/usr/bin/env python3
"""
设置云熙记忆系统
Setup YunPat Memory System
"""

import subprocess
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemorySystemSetup:
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": "athena123"  # 根据实际配置修改
        }

    def create_database(self):
        """创建记忆系统数据库"""
        logger.info("🗄️ 创建yunpat_memory数据库...")

        try:
            # 连接到postgres默认数据库
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True  # 自动提交

            with conn.cursor() as cursor:
                # 检查数据库是否已存在
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'yunpat_memory'")
                if cursor.fetchone():
                    logger.info("✅ yunpat_memory数据库已存在")
                    conn.close()
                    return True

                # 创建数据库
                cursor.execute("CREATE DATABASE yunpat_memory")
                logger.info("✅ yunpat_memory数据库创建成功")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            return False

    def setup_memory_tables(self):
        """设置记忆系统表结构"""
        logger.info("📋 设置记忆系统表...")

        config = {
            "host": self.db_config["host"],
            "port": self.db_config["port"],
            "database": "yunpat_memory",
            "user": self.db_config["user"],
            "password": self.db_config["password"]
        }

        try:
            conn = psycopg2.connect(**config)
            conn.autocommit = True

            with conn.cursor() as cursor:
                # 创建memory_items表
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS memory_items (
                    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    memory_type VARCHAR(20) NOT NULL CHECK (memory_type IN ('short', 'long', 'work', 'emotional')),
                    user_id VARCHAR(100) NOT NULL DEFAULT 'default',
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
                    tags TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    vector_id UUID,
                    expires_at TIMESTAMP,
                    is_archived BOOLEAN DEFAULT FALSE
                );

                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_memory_user_type ON memory_items(user_id, memory_type);
                CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_items(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_items(importance DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_items USING GIN(tags);
                CREATE INDEX IF NOT EXISTS idx_memory_expires ON memory_items(expires_at) WHERE expires_at IS NOT NULL;
                """

                cursor.execute(create_table_sql)
                logger.info("✅ memory_items表创建成功")

                # 创建测试数据
                self._create_sample_data(cursor)

            conn.close()
            logger.info("✅ 记忆系统表设置完成")
            return True

        except Exception as e:
            logger.error(f"❌ 设置表失败: {e}")
            return False

    def _create_sample_data(self, cursor):
        """创建示例数据"""
        logger.info("📝 创建示例记忆数据...")

        sample_memories = [
            {
                "content": "主人今天询问了专利无效性分析的方法",
                "memory_type": "long",
                "metadata": {
                    "source": "conversation",
                    "topic": "专利分析",
                    "timestamp": "2025-12-14T10:00:00"
                },
                "tags": ["专利", "无效性", "学习"],
                "importance": 0.8
            },
            {
                "content": "主人对云熙的服务很满意，这让云熙很开心~ 💖",
                "memory_type": "emotional",
                "metadata": {
                    "emotion": "happy",
                    "source": "feedback"
                },
                "tags": ["开心", "满意", "感谢"],
                "importance": 0.9
            },
            {
                "content": "专利申请的基本流程包括提交、审查、公示和授权",
                "memory_type": "work",
                "metadata": {
                    "knowledge_type": "专利流程",
                    "importance": "high"
                },
                "tags": ["专利", "申请", "流程"],
                "importance": 0.7
            },
            {
                "content": "测试短期记忆功能",
                "memory_type": "short",
                "metadata": {
                    "test": True
                },
                "tags": ["测试", "验证"],
                "importance": 0.3
            }
        ]

        for memory in sample_memories:
            sql = """
            INSERT INTO memory_items (content, memory_type, metadata, tags, importance)
            VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (
                memory["content"],
                memory["memory_type"],
                json.dumps(memory["metadata"]),
                memory["tags"],
                memory["importance"]
            ))

        logger.info(f"✅ 创建了 {len(sample_memories)} 条示例记忆")

    def install_dependencies(self):
        """安装必要的依赖"""
        logger.info("📦 安装依赖...")

        dependencies = [
            "psycopg2-binary",
            "sentence-transformers",
            "numpy",
            "scipy"
        ]

        for dep in dependencies:
            try:
                result = subprocess.run(
                    ["pip3", "install", dep],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ {dep} 安装成功")
                else:
                    logger.warning(f"⚠️ {dep} 可能已安装: {result.stderr}")
            except Exception as e:
                logger.warning(f"⚠️ 安装{dep}时出错: {e}")

    def test_connection(self):
        """测试数据库连接"""
        logger.info("🔍 测试数据库连接...")

        try:
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database="yunpat_memory",
                user=self.db_config["user"],
                password=self.db_config["password"]
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM memory_items")
                count = cursor.fetchone()[0]

            conn.close()
            logger.info(f"✅ 数据库连接成功，当前记忆数量: {count}")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def run_setup(self):
        """运行完整设置"""
        print("="*60)
        print("🧠️ 云熙记忆系统设置向导")
        print("="*60)
        print()

        # 安装依赖
        print("步骤 1/4: 安装Python依赖")
        self.install_dependencies()
        print()

        # 创建数据库
        print("步骤 2/4: 创建数据库")
        if not self.create_database():
            print("❌ 数据库创建失败")
            return
        print()

        # 设置表结构
        print("步骤 3/4: 设置表结构")
        if not self.setup_memory_tables():
            print("❌ 表结构设置失败")
            return
        print()

        # 测试连接
        print("步骤 4/4: 测试系统连接")
        if not self.test_connection():
            print("❌ 系统连接测试失败")
            return
        print()

        print("="*60)
        print("✅ 云熙记忆系统设置完成！")
        print()
        print("📌 系统信息:")
        print("  - 数据库: yunpat_memory")
        print("  - 端口: 5432")
        print("  - 记忆类型: 短期、长期、工作、情感")
        print()
        print("🚀 使用方法:")
        print("1. 重启YunPat服务: ./scripts/db_manager.sh restart")
        print("2. 测试API: curl http://localhost:8087/api/v1/memory/types")
        print("3. 查看API文档: http://localhost:8087/docs")
        print()
        print("💡 记忆功能:")
        print("- 自动保存重要对话")
        print("- 智能分类记忆类型")
        print("- 语义相似度搜索")
        print("- 个性化推荐")
        print("="*60)


def main():
    """主函数"""
    setup = MemorySystemSetup()
    setup.run_setup()


if __name__ == "__main__":
    main()