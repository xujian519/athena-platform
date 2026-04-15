#!/usr/bin/env python3
"""
复审决定书知识图谱导入模块
将已处理的复审决定书数据导入NebulaGraph知识图谱

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import json
import logging

# 添加项目路径
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from nebula3.Config import Config

# NebulaGraph客户端 (同步API)
from nebula3.gclient.net import ConnectionPool

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/nebula_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class DecisionNebulaImporter:
    """复审决定书NebulaGraph导入器 - 使用同步API"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.checkpoint_file = self.base_dir / "production/data/patent_decisions/checkpoints/nebula_import.json"
        self.chunks_dir = self.base_dir / "production/data/patent_decisions/processed"

        # NebulaGraph连接 (同步)
        self.pool = None
        self.session = None
        self.lock = threading.Lock()  # 线程安全

        # 导入统计
        self.stats = {
            'decisions_imported': 0,
            'chunks_imported': 0,
            'legal_refs_imported': 0,
            'relations_created': 0,
            'errors': 0
        }

        # 加载检查点
        self.checkpoint = self._load_checkpoint()

        logger.info("复审决定书NebulaGraph导入器初始化完成")

    def _load_checkpoint(self) -> dict[str, Any]:
        """加载检查点"""
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"检查点加载失败: {e}")

        return {
            'imported_decisions': [],
            'imported_chunks': [],
            'last_batch': 0,
            'stats': self.stats
        }

    def _save_checkpoint(self) -> Any:
        """保存检查点"""
        with self.lock:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    **self.checkpoint,
                    'stats': self.stats,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

    def connect_nebula(self) -> Any:
        """连接NebulaGraph (同步)"""
        logger.info("连接NebulaGraph...")

        config = Config()
        config.max_connection_pool_size = 10

        # 连接地址列表 - 需要使用(host, port)元组格式
        addresses = [('127.0.0.1', 9669)]

        try:
            self.pool = ConnectionPool()
            self.pool.init(addresses, config)

            # 获取会话 - 使用用户名和密码
            self.session = self.pool.get_session('root', 'nebula')

            # 测试连接
            result = self.session.execute('SHOW SPACES;')
            logger.info("✅ NebulaGraph已连接")

            # 切换到patent_rules空间
            use_result = self.session.execute('USE patent_rules;')
            logger.info("✅ 使用patent_rules空间")

            # 检查并创建schema
            self._ensure_schema()

        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            raise

    def _ensure_schema(self) -> Any:
        """确保schema存在"""
        logger.info("检查schema...")

        try:
            # 检查现有标签
            result = self.session.execute('SHOW TAGS;')

            # 使用rows()方法获取数据
            tag_names = []
            if result.is_succeeded():
                for row in result.rows():
                    tag_names.append(row[0].as_string())

            logger.info(f"现有标签: {tag_names}")

            if 'patent_decision' not in tag_names:
                logger.info("创建patent_decision标签...")
                self._create_decision_schema()
            else:
                logger.info("patent_decision标签已存在")

            # 检查边类型
            edge_result = self.session.execute('SHOW EDGES;')
            edge_names = []
            if edge_result.is_succeeded():
                for row in edge_result.rows():
                    edge_names.append(row[0].as_string())

            if 'cites' not in edge_names:
                logger.info("创建cites边类型...")
                self._create_decision_schema()

        except Exception as e:
            logger.warning(f"Schema检查失败，尝试创建: {e}")
            self._create_decision_schema()

    def _create_decision_schema(self) -> Any:
        """创建复审决定书schema"""
        statements = [
            # 创建patent_decision标签
            "CREATE TAG IF NOT EXISTS patent_decision("
            "  doc_id string, "
            "  decision_number string, "
            "  decision_date string, "
            "  block_type string, "
            "  section string, "
            "  text string, "
            "  filename string, "
            "  char_count int, "
            "  source string DEFAULT 'patent_decision'"
            ");",

            # 创建法律引用标签
            "CREATE TAG IF NOT EXISTS legal_ref("
            "  ref_text string, "
            "  law_name string, "
            "  article string, "
            "  confidence double DEFAULT 1.0"
            ");",

            # 创建引用关系边
            "CREATE EDGE IF NOT EXISTS cites("
            "  ref_context string, "
            "  confidence double DEFAULT 1.0"
            ");"
        ]

        for stmt in statements:
            try:
                result = self.session.execute(stmt)
                if not result.is_succeeded():
                    logger.warning(f"Schema创建警告: {result.error_msg()}")
                else:
                    logger.info(f"✅ 执行成功: {stmt[:50]}...")
            except Exception as e:
                logger.warning(f"Schema创建警告: {e}")

    def import_from_checkpoint(self) -> Any:
        """从检查点导入数据"""
        logger.info("=" * 60)
        logger.info("🚀 开始导入复审决定书到NebulaGraph")
        logger.info("=" * 60)

        # 获取已处理的批次文件
        batch_files = list(self.chunks_dir.glob("*_chunks_*.json"))

        if not batch_files:
            logger.warning("没有找到已处理的批次文件")
            # 尝试从检查点目录查找
            checkpoint_dir = self.base_dir / "production/data/patent_decisions/checkpoints"
            progress_file = checkpoint_dir / "progress.json"

            if progress_file.exists():
                logger.info("找到进度文件，检查数据源...")
                with open(progress_file) as f:
                    progress = json.load(f)
                    logger.info(f"已处理文件数: {len(progress.get('processed_files', []))}")
                    logger.info(f"总块数: {progress.get('total_chunks', 0)}")
            return

        logger.info(f"找到 {len(batch_files)} 个批次文件")

        # 排序并处理
        batch_files.sort()

        for batch_file in batch_files[-3:]:  # 处理最新的3个批次
            try:
                self._import_batch(batch_file)
            except Exception as e:
                logger.error(f"批次导入失败 {batch_file.name}: {e}")
                continue

        # 生成最终报告
        self._print_report()

    def _import_batch(self, batch_file: Path) -> Any:
        """导入一个批次"""
        logger.info(f"处理批次: {batch_file.name}")

        with open(batch_file, encoding='utf-8') as f:
            batch_data = json.load(f)

        chunks = batch_data.get('chunks', [])

        if not chunks:
            logger.warning("批次中没有数据块")
            return

        # 过滤已导入的
        imported_set = set(self.checkpoint.get('imported_chunks', []))
        chunks_to_import = [c for c in chunks if c['chunk_id'] not in imported_set]

        if not chunks_to_import:
            logger.info("所有数据块已导入，跳过")
            return

        logger.info(f"待导入数据块: {len(chunks_to_import)}")

        # 批量插入
        batch_size = 100
        for i in range(0, len(chunks_to_import), batch_size):
            batch = chunks_to_import[i:i + batch_size]
            self._insert_chunks(batch)

            # 每批次保存一次检查点
            logger.info(f"  进度: {min(i + batch_size, len(chunks_to_import))}/{len(chunks_to_import)}")

        # 更新检查点
        for chunk in chunks_to_import:
            self.checkpoint['imported_chunks'].append(chunk['chunk_id'])

        self.stats['decisions_imported'] += len(chunks_to_import)
        self.stats['chunks_imported'] += len(chunks_to_import)
        self._save_checkpoint()

        logger.info(f"✅ 批次完成: {len(chunks_to_import)} 数据块")

    def _insert_chunks(self, chunks: list[dict[str, Any]]) -> Any:
        """插入数据块"""
        for chunk in chunks:
            try:
                chunk_id = chunk['chunk_id']
                doc_id = chunk.get('doc_id', '')

                # 清理文本，移除特殊字符
                text = chunk.get('text', '')[:500]  # 限制长度
                # 保留单引号，只转义双引号
                text = text.replace('"', '\\"')
                text = text.replace('\n', '\\n').replace('\r', '\\r')

                # 准备属性值
                decision_num = str(chunk.get('metadata', {}).get('decision_number', '')).replace('"', '\\"')
                decision_date_val = str(chunk.get('metadata', {}).get('decision_date', '')).replace('"', '\\"')
                block_type_val = str(chunk.get('block_type', '')).replace('"', '\\"')
                section_val = str(chunk.get('section', '')).replace('"', '\\"')
                filename_val = str(chunk.get('metadata', {}).get('filename', '')).replace('"', '\\"')
                char_count_val = chunk.get('metadata', {}).get('char_count', 0)

                # 使用正确的NebulaGraph语法: INSERT VERTEX tag_name VALUES "vid":(val1, val2, ...);
                # 注意: 属性列表在tag_name后，用括号包裹值
                stmt = f'''INSERT VERTEX patent_decision VALUES "{chunk_id}":("{doc_id}", "{decision_num}", "{decision_date_val}", "{block_type_val}", "{section_val}", "{text}", "{filename_val}", {char_count_val}, "patent_decision");'''

                result = self.session.execute(stmt)

                if result.is_succeeded():
                    self.stats['relations_created'] += 1
                else:
                    logger.debug(f"插入失败 [{chunk_id}]: {result.error_msg()}")
                    self.stats['errors'] += 1

                # 创建法律引用顶点和关系
                law_refs = chunk.get('metadata', {}).get('law_references', [])

                for ref in law_refs:
                    try:
                        ref_id = short_hash(f"{chunk_id}_{ref}".encode())[:8]
                        ref_clean = ref.replace('"', '\\"')[:100]

                        # 创建法律引用顶点
                        # legal_ref有4个属性: ref_text, law_name, article, confidence
                        ref_stmt = f'''INSERT VERTEX legal_ref VALUES "{ref_id}":("{ref_clean}", "专利法/实施细则", "", 1.0);'''

                        ref_result = self.session.execute(ref_stmt)

                        # 创建引用关系边
                        # cites有2个属性: ref_context, confidence
                        edge_stmt = f'''INSERT EDGE cites VALUES "{chunk_id}"->"{ref_id}":("{ref_clean[:50]}", 1.0);'''

                        edge_result = self.session.execute(edge_stmt)

                        if edge_result.is_succeeded():
                            self.stats['legal_refs_imported'] += 1

                    except Exception as e:
                        logger.debug(f"法律引用插入失败: {e}")

            except Exception as e:
                logger.debug(f"数据块插入失败: {e}")
                self.stats['errors'] += 1

    def _print_report(self) -> Any:
        """打印导入报告"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 NebulaGraph导入报告")
        logger.info("=" * 60)
        logger.info(f"导入决定书数据块: {self.stats['chunks_imported']}")
        logger.info(f"创建法律引用: {self.stats['legal_refs_imported']}")
        logger.info(f"创建关系: {self.stats['relations_created']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("=" * 60)

    def verify_data(self) -> bool:
        """验证导入的数据"""
        logger.info("验证导入数据...")

        try:
            # 查询顶点数量
            count_result = self.session.execute('''
                MATCH (v:patent_decision)
                RETURN count(v) AS total;
            ''')

            if count_result.is_succeeded():
                rows = count_result.rows()
                if rows:
                    count = rows[0][0].as_int()
                    logger.info(f"patent_decision顶点数: {count}")

            # 查询关系数量
            edge_result = self.session.execute('''
                MATCH ()-[e:cites]->()
                RETURN count(e) AS total;
            ''')

            if edge_result.is_succeeded():
                rows = edge_result.rows()
                if rows:
                    count = rows[0][0].as_int()
                    logger.info(f"cites关系数: {count}")

        except Exception as e:
            logger.warning(f"验证查询失败: {e}")

    def close(self) -> Any:
        """关闭连接"""
        if self.session:
            self.session.release()
        if self.pool:
            self.pool.close()
        logger.info("NebulaGraph连接已关闭")


def main() -> None:
    """主函数"""
    importer = DecisionNebulaImporter()

    try:
        # 连接NebulaGraph
        importer.connect_nebula()

        # 导入数据
        importer.import_from_checkpoint()

        # 验证数据
        importer.verify_data()

    finally:
        importer.close()


if __name__ == "__main__":
    main()
