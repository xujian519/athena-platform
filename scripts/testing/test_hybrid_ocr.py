#!/usr/bin/env python3
"""
混合OCR测试脚本 - Docling + GLM-OCR
测试专利PDF的文本提取能力

Author: Athena平台团队
Date: 2026-04-22
"""

import asyncio
import base64
import json
import logging
import sys
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridOCREngine:
    """混合OCR引擎：Docling + GLM-OCR"""

    def __init__(self, llm_base_url: str = "http://localhost:8009"):
        """
        初始化混合OCR引擎

        Args:
            llm_base_url: LLM服务地址
        """
        self.llm_base_url = llm_base_url.rstrip("/")
        self.converter = None  # Docling转换器
        self.llm_adapter = None  # LLM适配器

    async def initialize(self):
        """初始化所有组件"""
        try:
            # 导入Docling（延迟导入，确保安装后才导入）
            try:
                from docling.document_converter import DocumentConverter

                self.converter = DocumentConverter()
                logger.info("✅ Docling初始化成功")
            except ImportError as e:
                logger.error(f"❌ Docling未安装: {e}")
                logger.info("请运行: pip install docling")
                return False

            # 初始化LLM适配器
            try:
                from core.ai.llm.adapters.local_8009_adapter import Local8009Adapter

                self.llm_adapter = Local8009Adapter(
                    base_url=self.llm_base_url,
                    model="gemma-4-e2b-it-4bit",
                    timeout=180
                )

                success = await self.llm_adapter.initialize()
                if not success:
                    logger.error(f"❌ LLM服务不可用: {self.llm_base_url}")
                    return False

                logger.info("✅ LLM适配器初始化成功")

            except ImportError as e:
                logger.error(f"❌ LLM适配器导入失败: {e}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}", exc_info=True)
            return False

    async def analyze_with_docling(self, pdf_path: str) -> dict[str, Any]:
        """
        使用Docling分析PDF结构

        Args:
            pdf_path: PDF文件路径

        Returns:
            Docling分析结果
        """
        logger.info("🔍 阶段1：Docling分析PDF结构...")

        try:
            # Docling转换
            doc = self.converter.convert(pdf_path)

            # 提取基本信息
            result = {
                "total_pages": len(doc.pages) if hasattr(doc, 'pages') else 0,
                "has_text": False,
                "is_scanned": False,
                "pages": []
            }

            # 分析每一页
            for page_idx, page in enumerate(doc.pages):
                page_info = {
                    "page_number": page_idx + 1,
                    "has_text_content": False,
                    "items_count": 0,
                    "item_types": set()
                }

                # 统计页面内容
                if hasattr(page, 'items'):
                    page_info["items_count"] = len(page.items)

                    for item in page.items:
                        item_type = item.type if hasattr(item, 'type') else 'unknown'
                        page_info["item_types"].add(item_type)

                        # 检查是否有文本
                        if hasattr(item, 'text') and item.text:
                            page_info["has_text_content"] = True
                            result["has_text"] = True

                result["pages"].append(page_info)

            # 判断是否为扫描件
            if not result["has_text"]:
                result["is_scanned"] = True
                logger.warning("⚠️ PDF似乎是扫描件（无文本层）")
            else:
                logger.info("✅ PDF包含文本层")

            return result

        except Exception as e:
            logger.error(f"❌ Docling分析失败: {e}", exc_info=True)
            return {"error": str(e)}

    async def recognize_with_vlm(
        self,
        pdf_path: str,
        max_pages: int = 3
    ) -> dict[str, Any]:
        """
        使用GLM-OCR（VLM）识别PDF内容

        Args:
            pdf_path: PDF文件路径
            max_pages: 最大处理页数（默认前3页）

        Returns:
            VLM识别结果
        """
        logger.info(f"🧠 阶段2：GLM-OCR识别PDF内容（前{max_pages}页）...")

        try:
            # PDF转图像
            from pdf2image import convert_from_path

            logger.info("  📄 PDF转图像中...")
            images = convert_from_path(pdf_path, dpi=200)

            if not images:
                return {"error": "PDF转图像失败"}

            logger.info(f"  ✅ 成功转换 {len(images)} 页")

            # 限制处理页数
            images = images[:max_pages]

            # 识别每一页
            results = []

            for img_idx, image in enumerate(images):
                logger.info(f"  🔍 识别第 {img_idx + 1}/{len(images)} 页...")

                # 保存临时图像
                temp_img_path = f"/tmp/ocr_page_{img_idx}.png"
                image.save(temp_img_path, "PNG")

                # 读取并编码图像
                with open(temp_img_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()

                # VLM识别提示词
                system_prompt = """你是一个专业的专利文档OCR助手。
请准确识别图像中的中文文字，保留原有布局结构。

输出要求：
1. 使用Markdown格式
2. 保留标题层级（#, ##, ###）
3. 表格使用Markdown表格格式
4. 如果有附图，说明附图内容
5. 保持段落结构"""

                user_prompt = """请识别这页专利文档的内容。

特别注意：
- 专利号、申请日、授权公告日等关键信息
- 权利要求书、说明书、附图说明等章节标题
- 技术术语和编号

输出格式：Markdown"""

                # 调用LLM进行VLM识别
                try:
                    content = await self.llm_adapter.generate(
                        prompt=f"[IMAGE]data:image/png;base64,{image_data}[/IMAGE]\n\n{user_prompt}",
                        system_prompt=system_prompt,
                        temperature=0.1,  # 低温度保证准确性
                        max_tokens=4096
                    )

                    results.append({
                        "page": img_idx + 1,
                        "content": content,
                        "success": True
                    })

                    logger.info(f"    ✅ 第 {img_idx + 1} 页识别完成，长度: {len(content)} 字符")

                except Exception as e:
                    logger.error(f"    ❌ 第 {img_idx + 1} 页识别失败: {e}")
                    results.append({
                        "page": img_idx + 1,
                        "error": str(e),
                        "success": False
                    })

            return {
                "total_pages": len(images),
                "processed_pages": len(results),
                "successful_pages": sum(1 for r in results if r["success"]),
                "pages": results
            }

        except ImportError:
            logger.error("❌ pdf2image未安装: pip install pdf2image")
            return {"error": "pdf2image未安装"}
        except Exception as e:
            logger.error(f"❌ VLM识别失败: {e}", exc_info=True)
            return {"error": str(e)}

    async def test_single_pdf(
        self,
        pdf_path: str,
        output_markdown: str = None
    ) -> dict[str, Any]:
        """
        测试单个PDF文件

        Args:
            pdf_path: PDF文件路径
            output_markdown: 输出Markdown文件路径（可选）

        Returns:
            完整测试结果
        """
        logger.info(f"🚀 开始测试PDF: {pdf_path}")
        logger.info("=" * 80)

        # 检查文件存在
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            logger.error(f"❌ PDF文件不存在: {pdf_path}")
            return {"error": "PDF文件不存在"}

        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
        logger.info(f"📁 文件大小: {file_size_mb:.2f} MB")

        # 阶段1：Docling分析
        docling_result = await self.analyze_with_docling(pdf_path)

        if "error" in docling_result:
            logger.error(f"❌ Docling分析失败: {docling_result['error']}")
            return docling_result

        logger.info("✅ Docling分析完成:")
        logger.info(f"   - 总页数: {docling_result['total_pages']}")
        logger.info(f"   - 是否扫描件: {docling_result['is_scanned']}")
        logger.info(f"   - 包含文本: {docling_result['has_text']}")

        # 阶段2：VLM识别
        vlm_result = await self.recognize_with_vlm(pdf_path, max_pages=3)

        if "error" in vlm_result:
            logger.error(f"❌ VLM识别失败: {vlm_result['error']}")
            return vlm_result

        logger.info("✅ VLM识别完成:")
        logger.info(f"   - 处理页数: {vlm_result['processed_pages']}")
        logger.info(f"   - 成功页数: {vlm_result['successful_pages']}")

        # 组装结果
        final_result = {
            "pdf_path": pdf_path,
            "file_size_mb": file_size_mb,
            "docling_analysis": docling_result,
            "vlm_recognition": vlm_result,
            "summary": {
                "is_scanned": docling_result.get("is_scanned", False),
                "total_pages": docling_result.get("total_pages", 0),
                "successful_pages": vlm_result.get("successful_pages", 0),
                "method_used": "Docling + GLM-OCR (Hybrid)"
            }
        }

        # 生成Markdown报告
        if output_markdown:
            self._generate_markdown_report(final_result, output_markdown)
            logger.info(f"📝 Markdown报告已生成: {output_markdown}")

        logger.info("=" * 80)
        logger.info("✅ 测试完成！")

        return final_result

    def _generate_markdown_report(
        self,
        result: dict[str, Any],
        output_path: str
    ):
        """生成Markdown格式报告"""

        pdf_name = Path(result["pdf_path"]).stem

        md_content = f"""# {pdf_name} 混合OCR测试报告

**测试时间**: {asyncio.get_event_loop().time()}
**测试方法**: Docling + GLM-OCR 混合架构
**PDF路径**: `{result["pdf_path"]}`
**文件大小**: {result["file_size_mb"]:.2f} MB

---

## 📊 Docling结构分析

| 项目 | 结果 |
|------|------|
| **总页数** | {result["docling_analysis"]["total_pages"]} |
| **是否扫描件** | {"✅ 是" if result["docling_analysis"]["is_scanned"] else "❌ 否"} |
| **包含文本层** | {"✅ 是" if result["docling_analysis"]["has_text"] else "❌ 否"} |

### 页面详情

"""

        # 页面详情
        for page_info in result["docling_analysis"]["pages"]:
            md_content += f"""
#### 第 {page_info['page_number']} 页
- 内容项数量: {page_info['items_count']}
- 内容类型: {', '.join(page_info['item_types']) if page_info['item_types'] else '无'}
- 包含文本: {'✅ 是' if page_info['has_text_content'] else '❌ 否'}

"""

        # VLM识别结果
        md_content += "\n---\n\n## 🧠 GLM-OCR 识别结果\n\n"

        for page_result in result["vlm_recognition"]["pages"]:
            # 判断成功或失败
            if page_result.get('success'):
                page_content = f"#### 识别内容：\n\n{page_result['content']}"
            else:
                page_content = f"**❌ 识别失败**: {page_result.get('error', '未知错误')}"

            md_content += f"""
### 第 {page_result['page']} 页

{page_content}

---

"""

        # 总结
        md_content += f"""
## 📋 测试总结

| 项目 | 结果 |
|------|------|
| **测试方法** | {result["summary"]["method_used"]} |
| **PDF类型** | {"扫描件" if result["summary"]["is_scanned"] else "数字PDF"} |
| **总页数** | {result["summary"]["total_pages"]} |
| **成功识别页数** | {result["summary"]["successful_pages"]} |
| **识别成功率** | {result["summary"]["successful_pages"] / max(result["summary"]["total_pages"], 1) * 100:.1f}% |

---

**报告生成**: Athena混合OCR引擎 🚀
"""

        # 保存Markdown
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(md_content, encoding="utf-8")

        logger.info(f"📄 Markdown报告已保存: {output_path}")


async def main():
    """主函数"""

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python test_hybrid_ocr.py <PDF文件路径> [输出Markdown路径]")
        print("示例: python test_hybrid_ocr.py CN207834740U.pdf output.md")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 创建混合OCR引擎
    engine = HybridOCREngine()

    # 初始化
    logger.info("🔧 初始化混合OCR引擎...")
    if not await engine.initialize():
        logger.error("❌ 初始化失败，请检查：")
        logger.error("  1. Docling是否安装: pip install docling")
        logger.error("  2. 8009端口LLM服务是否运行")
        sys.exit(1)

    # 测试PDF
    result = await engine.test_single_pdf(pdf_path, output_path)

    # 输出JSON结果
    print("\n" + "=" * 80)
    print("📊 测试结果（JSON）:")
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
