#!/usr/bin/env python3
"""
启动完整的专利全文处理Pipeline
Start Full Patent Full-Text Pipeline

包括：
1. PDF监控服务 - 自动处理新下载的PDF
2. Qdrant向量存储 - 保存向量化结果
3. NebulaGraph知识图谱 - 构建专利知识图谱
"""

from __future__ import annotations
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config() -> Any | None:
        return {
            'host': '127.0.0.1',
            'port': 9669,
            'user': 'root',
            'password': 'nebula',
            'space': 'patent_full_text_v2'
        }

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullPipelineOrchestrator:
    """
    完整Pipeline编排器

    协调PDF监控、向量化、知识图谱构建
    """

    def __init__(
        self,
        patent_directory: str = "/Users/xujian/apps/patents",
        enable_qdrant: bool = True,
        enable_nebula: bool = True,
        enable_pdf_monitor: bool = True
    ):
        """
        初始化编排器

        Args:
            patent_directory: 专利文件目录
            enable_qdrant: 是否启用Qdrant向量存储
            enable_nebula: 是否启用NebulaGraph知识图谱
            enable_pdf_monitor: 是否启用PDF监控服务
        """
        self.patent_directory = patent_directory
        self.enable_qdrant = enable_qdrant
        self.enable_nebula = enable_nebula
        self.enable_pdf_monitor = enable_pdf_monitor

        # 组件
        self.pdf_monitor = None
        self.pipeline = None
        self.db_integration = None

        # 控制标志
        self.running = False

        # 统计
        self.stats = {
            "start_time": None,
            "processed_patents": 0,
            "total_vectors": 0,
            "total_triples": 0,
            "total_vertices": 0,
            "total_edges": 0
        }

    def initialize_databases(self) -> Any:
        """初始化数据库连接"""
        print("\n" + "=" * 70)
        print("📊 初始化数据库连接")
        print("=" * 70)

        # 导入数据库集成模块
        from db_integration import DatabaseIntegration, DBIntegrationConfig

        # 创建配置 - 从环境变量读取Nebula密码
        nebula_config = get_nebula_config()
        config = DBIntegrationConfig(
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_collection="patent_full_text_v2"
        )
        # Nebula配置通过property从环境变量读取,无需手动设置

        # 创建数据库集成层
        self.db_integration = DatabaseIntegration(config)

        # 连接数据库
        print("\n🔗 连接数据库...")
        connection_results = self.db_integration.connect_all()

        for db_name, success in connection_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {db_name.upper()}")

        # 初始化数据库（创建集合/空间）
        print("\n🏗️  初始化数据库...")
        self.db_integration.initialize_databases()
        print("  ✅ 数据库初始化完成")

        # 健康检查
        print("\n🏥 健康检查...")
        health_results = self.db_integration.health_check_all()

        for result in health_results:
            status = "✅" if result.is_healthy else "❌"
            response_time = result.response_time * 1000
            print(f"  {status} {result.db_type.value}: {response_time:.2f}ms")

        return True

    def initialize_pipeline(self) -> Any:
        """初始化处理Pipeline"""
        print("\n" + "=" * 70)
        print("🏗️  初始化Pipeline")
        print("=" * 70)

        # 导入Pipeline
        from pipeline_v2 import PatentFullTextPipelineV2

        # 创建在线BGE模型加载器（使用HuggingFace）
        print("\n🔧 创建BGE向量化模型...")

        class OnlineBGEModel:
            """使用sentence_transformers直接加载在线BGE模型"""
            def __init__(self):
                self.model = None
                self._load()

            def _load(self) -> Any:
                from sentence_transformers import SentenceTransformer
                print("  📥 从HuggingFace加载BGE-base-zh-v1.5模型...")
                # 使用在线模型（会自动缓存到本地）
                self.model = SentenceTransformer(
                    'BAAI/bge-m3',
                    device='cpu'
                )
                print(f"  ✅ 模型加载成功，向量维度: {self.model.get_sentence_embedding_dimension()}")

            def encode(self, text) -> None:
                return self.model.encode(text)

        class SimpleModelLoader:
            """简化的模型加载器"""
            def __init__(self):
                self.bge_model = OnlineBGEModel()

            def load_model(self, name) -> None:
                if name == "BAAI/bge-m3":
                    return self.bge_model
                raise ValueError(f"未知模型: {name}")

        model_loader = SimpleModelLoader()

        # 创建Pipeline
        print("📦 创建Pipeline...")
        self.pipeline = PatentFullTextPipelineV2(
            model_loader=model_loader,
            enable_vectorization=True,
            enable_triple_extraction=True,
            enable_kg_build=self.enable_nebula,
            save_qdrant=self.enable_qdrant,
            save_nebula=self.enable_nebula,
            qdrant_client=self.db_integration.qdrant.client if self.enable_qdrant else None,
            nebula_client=self.db_integration.nebula.pool if self.enable_nebula else None
        )

        print("  ✅ Pipeline已创建")

        return True

    def process_patent_file(self, pdf_path: str, patent_number: str) -> Any | None:
        """
        处理专利文件

        Args:
            pdf_path: PDF文件路径
            patent_number: 专利号

        Returns:
            处理结果
        """
        logger.info(f"🔄 开始处理专利: {patent_number}")

        try:
            # 检查是否有对应的TXT文件
            pdf_path_obj = Path(pdf_path)
            txt_path = pdf_path_obj.parent / f"{patent_number}.txt"

            if txt_path.exists():
                # 读取TXT文件内容
                content = txt_path.read_text(encoding='utf-8', errors='ignore')

                # 解析专利数据
                patent_data = self._parse_patent_txt(content, patent_number)

            else:
                # 使用默认数据（实际应该解析PDF）
                patent_data = {
                    'patent_number': patent_number,
                    'title': f'专利 {patent_number}',
                    'abstract': '',
                    'ipc_classification': '',
                    'claims': '',
                    'invention_content': ''
                }

            # 创建Pipeline输入
            from pipeline_v2 import PipelineInput
            input_data = PipelineInput(
                patent_number=patent_data['patent_number'],
                title=patent_data.get('title', ''),
                abstract=patent_data.get('abstract', ''),
                ipc_classification=patent_data.get('ipc_classification', ''),
                claims=patent_data.get('claims', ''),
                invention_content=patent_data.get('invention_content', ''),
                publication_date=patent_data.get('publication_date', ''),
                application_date=patent_data.get('application_date', ''),
                ipc_main_class=patent_data.get('ipc_main_class', ''),
                ipc_subclass=patent_data.get('ipc_subclass', ''),
                ipc_full_path=patent_data.get('ipc_full_path', ''),
                patent_type=patent_data.get('patent_type', 'invention')
            )

            # 处理
            result = self.pipeline.process(input_data)

            # 更新统计
            self.stats["processed_patents"] += 1
            self.stats["total_vectors"] += result.total_vectors
            self.stats["total_triples"] += result.total_triples
            self.stats["total_vertices"] += result.total_vertices
            self.stats["total_edges"] += result.total_edges

            if result.success:
                logger.info(f"✅ 处理成功: {patent_number}")
                logger.info(f"   向量: {result.total_vectors}个")
                logger.info(f"   三元组: {result.total_triples}个")

                # 保存向量到Qdrant
                if self.enable_qdrant and result.vectorization_result:
                    self._save_vectors_to_qdrant(result)

                return {"success": True, "result": result}
            else:
                logger.error(f"❌ 处理失败: {result.error_message}")
                return {"success": False, "error": result.error_message}

        except Exception as e:
            logger.error(f"❌ 处理异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _parse_patent_txt(self, content: str, patent_number: str) -> dict:
        """解析专利TXT文件"""
        import re

        patent_data = {
            'patent_number': patent_number,
            'title': '',
            'abstract': '',
            'ipc_classification': '',
            'claims': '',
            'invention_content': '',
            'publication_date': '',
            'application_date': '',
            'patent_type': 'invention'
        }

        # 提取发明名称
        title_match = re.search(r'\(54\)\s*发明名称\s*\n(.+?)\n', content)
        if title_match:
            patent_data['title'] = title_match.group(1).strip()

        # 提取IPC分类
        ipc_match = re.search(r'\(51\)Int\.Cl\.\s*\n((?:[A-Z]\d+[A-Z]\s*\d+/\d+.*\n)+)', content)
        if ipc_match:
            patent_data['ipc_classification'] = ipc_match.group(1).strip()

        # 提取摘要
        abstract_match = re.search(r'\(57\)\s*摘要\s*\n((?:.+\n)+?)(?=\n权利要求书|CN\s)', content)
        if abstract_match:
            patent_data['abstract'] = abstract_match.group(1).strip()

        # 提取权利要求书
        claims_match = re.search(r'权利要求书.*?\n((?:.+\n)+?)(?=说明书|CN\s)', content, re.DOTALL)
        if claims_match:
            patent_data['claims'] = claims_match.group(1).strip()

        # 提取申请日
        date_match = re.search(r'\(22\)\s*申请日\s*([\d.]+)', content)
        if date_match:
            patent_data['application_date'] = date_match.group(1).replace('.', '-')

        # 提取发明内容
        invention_match = re.search(r'发明内容.*?\n((?:.+\n)+)', content, re.DOTALL)
        if invention_match:
            patent_data['invention_content'] = invention_match.group(1).strip()[:2000]

        return patent_data

    def _save_vectors_to_qdrant(self, result) -> None:
        """保存向量到Qdrant"""
        try:
            vectors = []

            for _vector_info in result.vectorization_result.all_vectors:
                # 这里需要实际的向量数据，暂时跳过
                pass

            if vectors:
                # 批量插入
                self.db_integration.qdrant.insert_vectors(vectors)
                logger.info(f"💾 已保存{len(vectors)}个向量到Qdrant")

        except Exception as e:
            logger.error(f"❌ 保存向量失败: {e}")

    def start_pdf_monitor(self) -> Any:
        """启动PDF监控服务"""
        if not self.enable_pdf_monitor:
            logger.info("⚠️  PDF监控服务未启用")
            return

        print("\n" + "=" * 70)
        print("📁 启动PDF监控服务")
        print("=" * 70)

        from pdf_monitor_service import PDFMonitorService

        # 创建监控服务
        self.pdf_monitor = PDFMonitorService(
            watch_directory=self.patent_directory,
            recursive=True,
            check_interval=10.0
        )

        # 设置处理回调
        self.pdf_monitor.set_processing_callback(self.process_patent_file)

        # 启动服务
        self.pdf_monitor.start()

        print("  ✅ PDF监控服务已启动")
        print(f"  📁 监控目录: {self.patent_directory}")
        print("  ⏱️  检查间隔: 10秒")

    def start(self) -> None:
        """启动完整Pipeline"""
        print("\n" + "=" * 70)
        print("🚀 启动完整专利全文处理Pipeline")
        print("=" * 70)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.running = True
        self.stats["start_time"] = time.time()

        try:
            # 1. 初始化数据库
            if not self.initialize_databases():
                logger.error("❌ 数据库初始化失败")
                return False

            # 2. 初始化Pipeline
            if not self.initialize_pipeline():
                logger.error("❌ Pipeline初始化失败")
                return False

            # 3. 启动PDF监控
            self.start_pdf_monitor()

            print("\n" + "=" * 70)
            print("✅ 完整Pipeline启动成功!")
            print("=" * 70)
            print("\n配置:")
            print(f"  📁 专利目录: {self.patent_directory}")
            print(f"  💾 Qdrant向量存储: {'✅ 启用' if self.enable_qdrant else '❌ 禁用'}")
            print(f"  🕸️  NebulaGraph知识图谱: {'✅ 启用' if self.enable_nebula else '❌ 禁用'}")
            print(f"  📄 PDF监控服务: {'✅ 启用' if self.enable_pdf_monitor else '❌ 禁用'}")

            print("\n📊 实时统计:")
            self._print_stats()

            return True

        except Exception as e:
            logger.error(f"❌ 启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop(self) -> None:
        """停止Pipeline"""
        if not self.running:
            return

        print("\n" + "=" * 70)
        print("🛑 停止Pipeline")
        print("=" * 70)

        self.running = False

        # 停止PDF监控
        if self.pdf_monitor:
            self.pdf_monitor.stop()

        # 断开数据库连接
        if self.db_integration:
            self.db_integration.disconnect_all()

        # 打印最终统计
        self._print_final_stats()

        print("\n✅ Pipeline已停止")

    def _print_stats(self) -> Any:
        """打印统计信息"""
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0

        print(f"  运行时间: {uptime:.0f}秒")
        print(f"  处理专利: {self.stats['processed_patents']}个")
        print(f"  总向量数: {self.stats['total_vectors']}")
        print(f"  总三元组: {self.stats['total_triples']}")

        if self.pdf_monitor:
            status = self.pdf_monitor.get_status()
            print(f"  已知文件: {status['known_files_count']}")

    def _print_final_stats(self) -> Any:
        """打印最终统计"""
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0

        print("\n" + "=" * 70)
        print("📊 最终统计")
        print("=" * 70)
        print(f"  总运行时间: {uptime:.0f}秒 ({uptime/60:.1f}分钟)")
        print(f"  处理专利: {self.stats['processed_patents']}个")
        print(f"  总向量数: {self.stats['total_vectors']}")
        print(f"  总三元组: {self.stats['total_triples']}")
        print(f"  总顶点数: {self.stats['total_vertices']}")
        print(f"  总边数: {self.stats['total_edges']}")

    def run_forever(self) -> Any:
        """持续运行"""
        if not self.running:
            if not self.start():
                return

        print("\n✅ Pipeline正在运行，按Ctrl+C停止...")
        print("=" * 70)

        # 注册信号处理
        def signal_handler(signum, frame) -> None:
            print("\n\n收到停止信号...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 定期打印统计
        try:
            while self.running:
                time.sleep(60)  # 每分钟打印一次统计
                if self.running:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📊 实时统计:")
                    self._print_stats()

                    if self.pdf_monitor:
                        recent = self.pdf_monitor.get_recent_tasks(5)
                        if recent:
                            print("  最近任务:")
                            for task in recent:
                                status_emoji = "✅" if task['status'] == 'success' else "❌"
                                print(f"    {status_emoji} {task['patent_number']}")

        except KeyboardInterrupt:
            print("\n\n收到停止信号...")
            self.stop()


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="启动完整专利全文处理Pipeline")
    parser.add_argument("--patent-dir", default="/Users/xujian/apps/patents",
                       help="专利文件目录")
    parser.add_argument("--no-qdrant", action="store_true",
                       help="禁用Qdrant向量存储")
    parser.add_argument("--no-nebula", action="store_true",
                       help="禁用NebulaGraph知识图谱")
    parser.add_argument("--no-monitor", action="store_true",
                       help="禁用PDF监控服务")

    args = parser.parse_args()

    # 创建编排器
    orchestrator = FullPipelineOrchestrator(
        patent_directory=args.patent_dir,
        enable_qdrant=not args.no_qdrant,
        enable_nebula=not args.no_nebula,
        enable_pdf_monitor=not args.no_monitor
    )

    # 运行
    orchestrator.run_forever()


if __name__ == "__main__":
    main()
