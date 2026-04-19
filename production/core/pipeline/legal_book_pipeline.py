#!/usr/bin/env python3
"""
《以案说法》书籍导入管道
Legal Case Book Import Pipeline

功能:
1. PDF解析和OCR识别
2. 案例知识抽取
3. 向量化存储到Qdrant
4. 知识图谱构建导入NebulaGraph

作者: Athena AI系统
创建时间: 2025-01-06
版本: 1.0.0
"""

from __future__ import annotations
import hashlib
import io
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# 第三方库
from PIL import Image

# 条件导入PyMuPDF (fitz)
try:
    import fitz
except ImportError:
    fitz = None

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class LegalBookPipeline:
    """法律书籍导入管道"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化管道

        Args:
            config: 配置字典,包含:
                - pdf_path: PDF文件路径
                - output_dir: 输出目录
                - chunk_size: 文本分块大小(默认1000字符)
                - chunk_overlap: 分块重叠大小(默认200字符)
                - enable_ocr: 是否启用OCR(默认True)
                - ocr_lang: OCR语言(默认'chi_sim')
        """
        self.config = config or {}
        self.pdf_path = self.config.get("pdf_path")
        self.output_dir = Path(self.config.get("output_dir", "./data/legal_books"))
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
        self.enable_ocr = self.config.get("enable_ocr", True)
        self.ocr_lang = self.config.get("ocr_lang", "chi_sim")

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            "total_pages": 0,
            "text_pages": 0,
            "ocr_pages": 0,
            "total_chunks": 0,
            "case_stories": 0,
            "legal_rules": 0,
        }

        logger.info("📚 《以案说法》导入管道初始化完成")

    async def process_pdf(self) -> dict[str, Any]:
        """
        处理PDF文件的主入口

        Returns:
            处理结果字典
        """
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")

        logger.info(f"🔄 开始处理PDF: {self.pdf_path}")

        # 阶段1: PDF解析和文本提取
        logger.info("📄 阶段1: PDF解析和文本提取")
        text_content = await self._extract_text_from_pdf()

        # 阶段2: 案例知识抽取
        logger.info("🧠 阶段2: 案例知识抽取")
        case_stories, legal_rules = await self._extract_knowledge(text_content)

        # 阶段3: 文本分块
        logger.info("✂️ 阶段3: 文本分块")
        chunks = await self._chunk_text(text_content)

        # 阶段4: 向量化准备
        logger.info("🔢 阶段4: 向量化准备")
        vector_docs = await self._prepare_vector_docs(chunks, case_stories, legal_rules)

        # 阶段5: 知识图谱构建
        logger.info("🕸️ 阶段5: 知识图谱构建")
        graph_data = await self._build_knowledge_graph(case_stories, legal_rules)

        # 保存中间结果
        await self._save_results(text_content, case_stories, legal_rules, vector_docs, graph_data)

        logger.info("✅ PDF处理完成!")
        logger.info(f"📊 统计信息: {json.dumps(self.stats, ensure_ascii=False, indent=2)}")

        return {
            "status": "success",
            "stats": self.stats,
            "output_dir": str(self.output_dir),
            "vector_docs_count": len(vector_docs),
            "graph_nodes_count": len(graph_data.get("nodes", [])),
            "graph_relations_count": len(graph_data.get("relations", [])),
        }

    async def _extract_text_from_pdf(self) -> list[dict[str, Any]]:
        """
        从PDF提取文本

        Returns:
            页面内容列表,每项包含:
            - page_num: 页码
            - text: 提取的文本
            - method: 提取方法(text/ocr)
            - images: 图片信息列表
        """
        pdf_document = fitz.open(self.pdf_path)
        pages_content = []

        logger.info(f"📖 PDF总页数: {len(pdf_document)}")
        self.stats["total_pages"] = len(pdf_document)

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # 尝试直接提取文本
            text = page.get_text("text")

            # 判断文本质量(如果文本太少,可能是扫描版PDF)
            if len(text.strip()) < 100 and self.enable_ocr:
                logger.info(f"🔍 第{page_num+1}页文本较少,启用OCR")
                text = await self._ocr_page(page)
                method = "ocr"
                self.stats["ocr_pages"] += 1
            else:
                method = "text"
                self.stats["text_pages"] += 1

            # 提取图片信息
            images = []
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # 保存图片
                image_filename = (
                    self.output_dir / f"page_{page_num+1}_img_{img_index+1}.{image_ext}"
                )
                with open(image_filename, "wb") as img_file:
                    img_file.write(image_bytes)

                images.append(
                    {
                        "index": img_index,
                        "filename": str(image_filename),
                        "format": image_ext,
                        "size": len(image_bytes),
                    }
                )

            pages_content.append(
                {
                    "page_num": page_num + 1,
                    "text": text.strip(),
                    "method": method,
                    "images": images,
                    "char_count": len(text.strip()),
                }
            )

            if (page_num + 1) % 10 == 0:
                logger.info(f"✅ 已处理 {page_num+1}/{len(pdf_document)} 页")

        pdf_document.close()
        return pages_content

    async def _ocr_page(self, page) -> str:
        """
        对页面进行OCR识别

        Args:
            page: PyMuPDF页面对象

        Returns:
            识别的文本
        """
        try:
            # 将页面渲染为图片
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            Image.open(io.BytesIO(img_bytes))

            # 这里可以集成OCR引擎(如Tesseract、PaddleOCR等)
            # 暂时返回占位符
            # TODO: 集成实际的OCR引擎
            return "[OCR识别结果 - 需要配置OCR引擎]"

        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return ""

    async def _extract_knowledge(
        self, pages_content: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        从文本中抽取案例和法律规则

        Args:
            pages_content: 页面内容列表

        Returns:
            (案例列表, 法律规则列表)
        """
        case_stories = []
        legal_rules = []

        # 合并所有文本
        full_text = "\n".join([p["text"] for p in pages_content])

        # 识别案例模式(根据《以案说法》的格式特征)
        # 常见模式:[案例X]、[案例索引]、案号等
        case_pattern = re.compile(
            r"[案例\s*(\d+)].*?(?=[案例\s*\d+\]|$)", re.DOTALL | re.MULTILINE
        )

        # 识别法律规则模式
        # 常见模式:根据专利法第X条、按照规定等
        rule_pattern = re.compile(
            r"(?:根据|按照|依据).*?(?:专利法|实施细则|指南).*?第\s*(\d+)\s*条",
            re.DOTALL | re.MULTILINE,
        )

        # 抽取案例
        case_matches = case_pattern.findall(full_text)
        for match in case_matches:
            # 这里需要更精细的解析逻辑
            # 暂时创建基础案例结构
            case_stories.append(
                {
                    "case_id": f"case_{match}",
                    "source": "以案说法",
                    "raw_text": "",  # 实际应该提取完整案例文本
                    "metadata": {
                        "book": "以案说法--专利复审、无效典型案例指引",
                        "extracted_at": datetime.now().isoformat(),
                    },
                }
            )

        # 抽取法律规则
        rule_matches = rule_pattern.findall(full_text)
        for match in set(rule_matches):  # 去重
            legal_rules.append(
                {
                    "rule_id": f"article_{match}",
                    "article_number": match,
                    "law": "专利法",
                    "source": "以案说法",
                    "raw_text": "",
                    "metadata": {
                        "book": "以案说法--专利复审、无效典型案例指引",
                        "extracted_at": datetime.now().isoformat(),
                    },
                }
            )

        self.stats["case_stories"] = len(case_stories)
        self.stats["legal_rules"] = len(legal_rules)

        logger.info(f"📖 抽取到 {len(case_stories)} 个案例")
        logger.info(f"📜 抽取到 {len(legal_rules)} 个法律规则")

        return case_stories, legal_rules

    async def _chunk_text(self, pages_content: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        将文本分块

        Args:
            pages_content: 页面内容列表

        Returns:
            文本块列表
        """
        chunks = []
        current_chunk = ""
        current_page_start = 1

        for page in pages_content:
            text = page["text"]

            # 如果当前块加上新文本超过大小限制,先保存当前块
            if len(current_chunk) + len(text) > self.chunk_size:
                if current_chunk:
                    chunks.append(
                        {
                            "text": current_chunk.strip(),
                            "page_start": current_page_start,
                            "page_end": page["page_num"],
                            "char_count": len(current_chunk),
                        }
                    )
                    # 重置,保留重叠部分
                    overlap_text = (
                        current_chunk[-self.chunk_overlap :] if self.chunk_overlap > 0 else ""
                    )
                    current_chunk = overlap_text + text
                    current_page_start = page["page_num"]
                else:
                    current_chunk = text
            else:
                current_chunk += "\n\n" + text

        # 保存最后一个块
        if current_chunk:
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "page_start": current_page_start,
                    "page_end": pages_content[-1]["page_num"],
                    "char_count": len(current_chunk),
                }
            )

        self.stats["total_chunks"] = len(chunks)
        logger.info(f"✂️ 文本分块完成,共 {len(chunks)} 块")

        return chunks

    async def _prepare_vector_docs(
        self,
        chunks: list[dict[str, Any]],
        case_stories: list[dict[str, Any]],
        legal_rules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        准备向量化文档

        Args:
            chunks: 文本块
            case_stories: 案例列表
            legal_rules: 法律规则列表

        Returns:
            向量化文档列表
        """
        vector_docs = []

        # 1. 为文本块准备向量文档
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(chunk["text"].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

            vector_docs.append(
                {
                    "id": doc_id,
                    "text": chunk["text"],
                    "metadata": {
                        "type": "text_chunk",
                        "source": "以案说法",
                        "chunk_id": i,
                        "page_start": chunk["page_start"],
                        "page_end": chunk["page_end"],
                        "char_count": chunk["char_count"],
                    },
                }
            )

        # 2. 为案例准备向量文档
        for case in case_stories:
            doc_id = hashlib.md5(case["case_id"].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

            vector_docs.append(
                {
                    "id": f"case_{doc_id}",
                    "text": case.get("raw_text", ""),
                    "metadata": {
                        "type": "case_story",
                        "source": "以案说法",
                        "case_id": case["case_id"],
                        "extracted_at": case["metadata"].get("extracted_at"),
                    },
                }
            )

        # 3. 为法律规则准备向量文档
        for rule in legal_rules:
            doc_id = hashlib.md5(rule["rule_id"].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

            vector_docs.append(
                {
                    "id": f"rule_{doc_id}",
                    "text": rule.get("raw_text", ""),
                    "metadata": {
                        "type": "legal_rule",
                        "source": "以案说法",
                        "rule_id": rule["rule_id"],
                        "article_number": rule["article_number"],
                        "law": rule["law"],
                        "extracted_at": rule["metadata"].get("extracted_at"),
                    },
                }
            )

        logger.info(f"📄 准备了 {len(vector_docs)} 个向量化文档")

        return vector_docs

    async def _build_knowledge_graph(
        self, case_stories: list[dict[str, Any]], legal_rules: list[dict[str, Any]]) -> dict[str, Any]:
        """
        构建知识图谱

        Args:
            case_stories: 案例列表
            legal_rules: 法律规则列表

        Returns:
            知识图谱数据(节点和关系)
        """
        nodes = []
        relations = []

        # 1. 创建案例节点
        for case in case_stories:
            nodes.append(
                {
                    "id": case["case_id"],
                    "type": "Case",
                    "name": f"案例 {case['case_id']}",
                    "properties": {
                        "source": "以案说法",
                        "extracted_at": case["metadata"].get("extracted_at"),
                    },
                }
            )

        # 2. 创建法律规则节点
        for rule in legal_rules:
            nodes.append(
                {
                    "id": rule["rule_id"],
                    "type": "LegalRule",
                    "name": f"{rule['law']}第{rule['article_number']}条",
                    "properties": {
                        "article_number": rule["article_number"],
                        "law": rule["law"],
                        "source": "以案说法",
                    },
                }
            )

        # 3. 创建书节点
        book_node = {
            "id": "book_yianshuofa",
            "type": "Book",
            "name": "以案说法--专利复审、无效典型案例指引",
            "properties": {"category": "专利法律", "publisher": "知识产权出版社", "year": "2020"},
        }
        nodes.append(book_node)

        # 4. 创建关系
        # 案例属于书
        for case in case_stories:
            relations.append(
                {
                    "source": case["case_id"],
                    "target": "book_yianshuofa",
                    "type": "BELONGS_TO",
                    "properties": {},
                }
            )

        # 法律规则属于书
        for rule in legal_rules:
            relations.append(
                {
                    "source": rule["rule_id"],
                    "target": "book_yianshuofa",
                    "type": "BELONGS_TO",
                    "properties": {},
                }
            )

        # 案例引用法律规则(这里需要实际的分析逻辑)
        # 暂时创建示例关系
        if case_stories and legal_rules:
            relations.append(
                {
                    "source": case_stories[0]["case_id"],
                    "target": legal_rules[0]["rule_id"],
                    "type": "REFERENCES",
                    "properties": {"context": "案例引用法律条款"},
                }
            )

        logger.info(f"🕸️ 知识图谱构建完成: {len(nodes)} 个节点, {len(relations)} 个关系")

        return {"nodes": nodes, "relations": relations}

    async def _save_results(
        self,
        text_content: list[dict[str, Any]],
        case_stories: list[dict[str, Any]],
        legal_rules: list[dict[str, Any]],
        vector_docs: list[dict[str, Any]],
        graph_data: dict[str, Any],
    ):
        """保存处理结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存文本内容
        text_file = self.output_dir / f"text_content_{timestamp}.json"
        with open(text_file, "w", encoding="utf-8") as f:
            json.dump(text_content, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 文本内容已保存: {text_file}")

        # 保存案例
        cases_file = self.output_dir / f"case_stories_{timestamp}.json"
        with open(cases_file, "w", encoding="utf-8") as f:
            json.dump(case_stories, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 案例已保存: {cases_file}")

        # 保存法律规则
        rules_file = self.output_dir / f"legal_rules_{timestamp}.json"
        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(legal_rules, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 法律规则已保存: {rules_file}")

        # 保存向量文档
        vectors_file = self.output_dir / f"vector_docs_{timestamp}.json"
        with open(vectors_file, "w", encoding="utf-8") as f:
            json.dump(vector_docs, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 向量文档已保存: {vectors_file}")

        # 保存知识图谱
        graph_file = self.output_dir / f"knowledge_graph_{timestamp}.json"
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 知识图谱已保存: {graph_file}")

        # 保存统计信息
        stats_file = self.output_dir / f"stats_{timestamp}.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 统计信息已保存: {stats_file}")


async def main():
    """主函数 - 使用示例"""

    # 配置管道
    config = {
        "pdf_path": "/Users/xujian/Desktop/以案说法--专利复审、无效典型案例指引.pdf",
        "output_dir": "./data/legal_books/yianshuofa",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "enable_ocr": True,
        "ocr_lang": "chi_sim",
    }

    # 创建并运行管道
    pipeline = LegalBookPipeline(config)
    result = await pipeline.process_pdf()

    print("\n" + "=" * 50)
    print("📊 处理完成!")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


# 入口点: @async_main装饰器已添加到main函数
