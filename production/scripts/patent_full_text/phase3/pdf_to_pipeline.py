#!/usr/bin/env python3
"""
PDF到Pipeline集成处理
PDF to Pipeline Integration

将PDF文件监控与专利全文处理Pipeline集成

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF处理器

    集成PDF文件监控和专利处理Pipeline
    """

    def __init__(
        self,
        model_loader=None,
        db_integration=None,
        save_to_db: bool = True,
        output_dir: str = "/Users/xujian/apps/apps/patents/processed"
    ):
        """
        初始化PDF处理器

        Args:
            model_loader: 模型加载器
            db_integration: 数据库集成
            save_to_db: 是否保存到数据库
            output_dir: 输出目录
        """
        self.model_loader = model_loader
        self.db_integration = db_integration
        self.save_to_db = save_to_db
        self.output_dir = Path(output_dir)

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: str) -> str | None:
        """
        从PDF提取文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            提取的文本
        """
        try:
            # 尝试使用PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                pass

            # 尝试使用pdfplumber
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text
            except ImportError:
                pass

            # 尝试使用pymupdf
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except ImportError:
                pass

            logger.error("❌ 未安装PDF解析库（PyPDF2/pdfplumber/PyMuPDF）")
            return None

        except Exception as e:
            logger.error(f"❌ PDF文本提取失败: {e}")
            return None

    def parse_patent_text(self, text: str) -> dict[str, Any]:
        """
        解析专利文本，提取结构化信息

        Args:
            text: 专利全文文本

        Returns:
            结构化专利信息
        """
        # 简单解析（实际应该使用更复杂的解析逻辑）
        lines = text.split('\n')

        info = {
            "title": "",
            "abstract": "",
            "ipc_classification": "",
            "claims": "",
            "invention_content": "",
            "background": ""
        }

        current_section = None
        current_lines = []

        for line in lines:
            line = line.strip()

            # 检测章节标题
            if any(keyword in line for keyword in ["发明名称", "技术领域", "背景技术"]):
                if "发明名称" in line:
                    current_section = "title"
                elif "背景技术" in line:
                    current_section = "background"
                current_lines = []
            elif any(keyword in line for keyword in ["摘要", "技术方案"]):
                if "摘要" in line and "技术方案" not in line:
                    current_section = "abstract"
                elif "技术方案" in line or "发明内容" in line:
                    current_section = "invention_content"
                current_lines = []
            elif any(keyword in line for keyword in ["权利要求", "Claims"]):
                current_section = "claims"
                current_lines = []
            elif "IPC" in line or "国际分类" in line:
                current_section = "ipc"
                # 尝试提取IPC分类号
                parts = line.split()
                for part in parts:
                    if len(part) > 3 and any(c.isupper() for c in part):
                        info["ipc_classification"] = part
                        break

            elif current_section:
                if current_section == "title":
                    info["title"] += line + " "
                elif current_section == "abstract":
                    info["abstract"] += line + " "
                elif current_section == "background":
                    info["background"] += line + "\n"
                elif current_section == "invention_content":
                    info["invention_content"] += line + "\n"
                elif current_section == "claims":
                    info["claims"] += line + "\n"

        # 清理
        for key in info:
            if isinstance(info[key], str):
                info[key] = info[key].strip()

        return info

    def process_pdf(self, pdf_path: str, patent_number: str) -> dict[str, Any]:
        """
        处理PDF文件

        Args:
            pdf_path: PDF文件路径
            patent_number: 专利号

        Returns:
            处理结果
        """
        logger.info(f"📄 开始处理PDF: {patent_number}")

        # 1. 提取文本
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {
                "success": False,
                "error": "文本提取失败"
            }

        logger.info(f"✅ 文本提取成功: {len(text)}字符")

        # 2. 解析结构
        patent_info = self.parse_patent_text(text)
        patent_info["patent_number"] = patent_number

        logger.info("📋 解析结果:")
        logger.info(f"  标题: {patent_info['title'][:50]}...")
        logger.info(f"  IPC: {patent_info['ipc_classification']}")

        # 3. 保存提取的文本
        output_file = self.output_dir / f"{patent_number}.txt"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(patent_info, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 已保存: {output_file}")
        except Exception as e:
            logger.warning(f"⚠️  保存文件失败: {e}")

        # 4. 如果有模型加载器，执行Pipeline处理
        if self.model_loader:
            try:
                # 延迟导入Pipeline
                import sys
                sys.path.insert(0, str(Path(__file__).parent))

                from pipeline_v2 import create_pipeline_input, process_patent

                # 创建Pipeline输入
                pipeline_input = create_pipeline_input(
                    patent_number=patent_number,
                    title=patent_info.get("title", ""),
                    abstract=patent_info.get("abstract", ""),
                    ipc_classification=patent_info.get("ipc_classification", ""),
                    claims=patent_info.get("claims") or None,
                    invention_content=patent_info.get("invention_content") or None,
                    background=patent_info.get("background") or None
                )

                # 执行Pipeline
                result = process_patent(
                    pipeline_input,
                    self.model_loader,
                    save_qdrant=self.save_to_db and self.db_integration is not None,
                    save_nebula=self.save_to_db and self.db_integration is not None
                )

                logger.info("✅ Pipeline处理完成:")
                logger.info(f"  向量数: {result.total_vectors}")
                logger.info(f"  三元组: {result.total_triples}")
                logger.info(f"  顶点数: {result.total_vertices}")
                logger.info(f"  边数: {result.total_edges}")

                return {
                    "success": True,
                    "patent_info": patent_info,
                    "pipeline_result": {
                        "vectors": result.total_vectors,
                        "triples": result.total_triples,
                        "vertices": result.total_vertices,
                        "edges": result.total_edges
                    }
                }

            except Exception as e:
                logger.error(f"❌ Pipeline处理失败: {e}")
                return {
                    "success": False,
                    "error": f"Pipeline处理失败: {e}",
                    "patent_info": patent_info
                }

        return {
            "success": True,
            "patent_info": patent_info
        }


def create_pdf_processor(**kwargs) -> PDFProcessor:
    """创建PDF处理器"""
    return PDFProcessor(**kwargs)


# ========== 集成启动函数 ==========

def start_pdf_monitor_with_pipeline(
    watch_directory: str = "/Users/xujian/apps/patents",
    model_loader=None,
    db_integration=None,
    save_to_db: bool = True,
    **kwargs
):
    """
    启动PDF监控并集成Pipeline处理

    Args:
        watch_directory: 监控目录
        model_loader: 模型加载器
        db_integration: 数据库集成
        save_to_db: 是否保存到数据库
        **kwargs: 传递给PDFMonitorService的参数
    """
    from pdf_monitor_service import create_pdf_monitor

    # 创建PDF处理器
    pdf_processor = create_pdf_processor(
        model_loader=model_loader,
        db_integration=db_integration,
        save_to_db=save_to_db
    )

    # 创建监控服务
    monitor = create_pdf_monitor(
        watch_directory=watch_directory,
        **kwargs
    )

    # 设置处理回调
    def process_callback(file_path: str, patent_number: str) -> Any:
        return pdf_processor.process_pdf(file_path, patent_number)

    monitor.set_processing_callback(process_callback)

    # 启动服务
    monitor.start()

    return monitor


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("PDF监控 + Pipeline处理 示例")
    print("=" * 70)

    # 创建模型加载器（可选）
    model_loader = None  # 使用实际的模型加载器

    # 启动监控服务
    monitor = start_pdf_monitor_with_pipeline(
        watch_directory="/Users/xujian/apps/patents",
        model_loader=model_loader,
        save_to_db=False,  # 示例中不保存到数据库
        check_interval=5.0
    )

    print("\n✅ 监控服务已启动，按Ctrl+C停止...")

    try:
        import time
        while True:
            time.sleep(30)
            status = monitor.get_status()
            print("\n📊 服务状态:")
            print(f"  运行时间: {status['uptime_seconds']:.0f}秒")
            print(f"  已知文件: {status['known_files_count']}")
            print(f"  检测到: {status['stats']['total_detected']}")
            print(f"  已处理: {status['stats']['total_processed']}")
            print(f"  成功: {status['stats']['total_success']}")
            print(f"  失败: {status['stats']['total_failed']}")

    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号...")
        monitor.stop()


if __name__ == "__main__":
    main()
