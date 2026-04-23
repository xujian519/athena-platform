#!/usr/bin/env python3
"""
混合OCR测试脚本 V2 - GLM-OCR纯VLM方案
完全使用gemma-4-e2b-it-4bit进行VLM识别，无需Docling下载模型

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

import PIL.Image

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridOCREngineV2:
    """混合OCR引擎 V2 - 纯VLM方案"""

    def __init__(self, llm_base_url: str = "http://localhost:8009"):
        """
        初始化混合OCR引擎 V2

        Args:
            llm_base_url: LLM服务地址
        """
        self.llm_base_url = llm_base_url.rstrip("/")
        self.llm_adapter = None  # LLM适配器

    async def initialize(self):
        """初始化所有组件"""
        try:
            # 初始化LLM适配器
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
            return True

        except ImportError as e:
            logger.error(f"❌ LLM适配器导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}", exc_info=True)
            return False

    async def analyze_pdf_structure(self, pdf_path: str) -> dict[str, Any]:
        """
        分析PDF基本信息（无需Docling）

        Args:
            pdf_path: PDF文件路径

        Returns:
            PDF基本信息
        """
        logger.info("🔍 阶段1：分析PDF基本信息...")

        try:
            pdf_file = Path(pdf_path)

            # 基本文件信息
            result = {
                "file_name": pdf_file.name,
                "file_size_mb": pdf_file.stat().st_size / (1024 * 1024),
                "exists": True
            }

            # 尝试使用pypdfium2获取页数（如果可用）
            try:
                import pypdfium2
                pdf_doc = pypdfium2.PdfDocument(pdf_path)
                result["total_pages"] = len(pdf_doc)

                # 检查是否有文本层
                has_text = False
                for page in pdf_doc:
                    text = page.get_textpage().get_text_range()
                    if text.strip():
                        has_text = True
                        break

                result["has_text_layer"] = has_text
                result["is_scanned"] = not has_text

                if has_text:
                    logger.info(f"✅ PDF包含文本层（{result['total_pages']}页）")
                else:
                    logger.warning(f"⚠️ PDF似乎是扫描件（{result['total_pages']}页）")

            except ImportError:
                # pypdfium2不可用，使用pdf2image
                logger.warning("⚠️ pypdfium2不可用，使用pdf2image")
                from pdf2image import convert_from_path

                # 转换第一页来检查
                convert_from_path(pdf_path, first_page=1, last_page=1)
                result["total_pages"] = "未知"
                result["has_text_layer"] = False
                result["is_scanned"] = True
                logger.warning("⚠️ 无法检测文本层，假设为扫描件")

            return result

        except Exception as e:
            logger.error(f"❌ PDF分析失败: {e}", exc_info=True)
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

                # 压缩图像以减少token数量
                # 降低分辨率并使用JPEG压缩
                import io

                # 计算新的尺寸（宽度最大1500px）
                max_width = 1500
                original_width, original_height = image.size

                if original_width > max_width:
                    scale = max_width / original_width
                    new_width = max_width
                    new_height = int(original_height * scale)
                    image = image.resize((new_width, new_height), PIL.Image.Resampling.LANCZOS)
                    logger.info(f"    📐 图像已缩放: {original_width}x{original_height} → {new_width}x{new_height}")

                # 保存为JPEG（质量85）以减小文件大小
                temp_img_path = f"/tmp/ocr_page_{img_idx}.jpg"
                image.save(temp_img_path, "JPEG", quality=85, optimize=True)

                # 检查文件大小
                file_size_kb = Path(temp_img_path).stat().st_size / 1024
                logger.info(f"    📁 压缩后图像大小: {file_size_kb:.1f} KB")

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
                        "success": True,
                        "char_count": len(content)
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

        # 阶段1：PDF基本信息分析
        structure_info = await self.analyze_pdf_structure(pdf_path)

        if "error" in structure_info:
            logger.error(f"❌ PDF分析失败: {structure_info['error']}")
            return structure_info

        logger.info("✅ PDF分析完成:")
        logger.info(f"   - 文件大小: {structure_info.get('file_size_mb', 0):.2f} MB")
        logger.info(f"   - 总页数: {structure_info.get('total_pages', '未知')}")
        logger.info(f"   - 是否扫描件: {structure_info.get('is_scanned', '未知')}")

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
            "structure_analysis": structure_info,
            "vlm_recognition": vlm_result,
            "summary": {
                "is_scanned": structure_info.get("is_scanned", False),
                "total_pages": structure_info.get("total_pages", 0),
                "successful_pages": vlm_result.get("successful_pages", 0),
                "method_used": "GLM-OCR (Pure VLM)"
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

        md_content = f"""# {pdf_name} GLM-OCR 测试报告

**测试时间**: 2026-04-22
**测试方法**: GLM-OCR (gemma-4-e2b-it-4bit VLM)
**PDF路径**: `{result["pdf_path"]}`

---

## 📊 PDF基本信息

| 项目 | 结果 |
|------|------|
| **文件名** | {result["structure_analysis"].get("file_name", "未知")} |
| **文件大小** | {result["structure_analysis"].get("file_size_mb", 0):.2f} MB |
| **总页数** | {result["structure_analysis"].get("total_pages", "未知")} |
| **是否扫描件** | {"✅ 是" if result["structure_analysis"].get("is_scanned") else "❌ 否"} |
| **包含文本层** | {"✅ 是" if result["structure_analysis"].get("has_text_layer") else "❌ 否"} |

---

## 🧠 GLM-OCR 识别结果

"""

        # VLM识别结果
        for page_result in result["vlm_recognition"]["pages"]:
            # 判断成功或失败
            if page_result.get('success'):
                page_content = f"""#### 识别内容：

{page_result['content']}

**字符数**: {page_result.get('char_count', 0)}"""
            else:
                page_content = f"**❌ 识别失败**: {page_result.get('error', '未知错误')}"

            md_content += f"""
### 第 {page_result['page']} 页

{page_content}

---

"""

        # 总结
        successful_rate = 0
        if result["summary"]["total_pages"]:
            successful_rate = result["summary"]["successful_pages"] / max(result["summary"]["total_pages"], 1) * 100

        md_content += f"""
## 📋 测试总结

| 项目 | 结果 |
|------|------|
| **测试方法** | {result["summary"]["method_used"]} |
| **PDF类型** | {"扫描件" if result["summary"]["is_scanned"] else "数字PDF"} |
| **总页数** | {result["summary"]["total_pages"]} |
| **成功识别页数** | {result["summary"]["successful_pages"]} |
| **识别成功率** | {successful_rate:.1f}% |

### 方法说明

本测试使用纯VLM方案：
- **模型**: gemma-4-e2b-it-4bit（8009端口本地部署）
- **优势**: 语义理解能力强，适合专利文档
- **特点**: 无需预先下载OCR模型，完全本地运行

---

**报告生成**: Athena混合OCR引擎 V2 🚀
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
        print("使用方法: python test_hybrid_ocr_v2.py <PDF文件路径> [输出Markdown路径]")
        print("示例: python test_hybrid_ocr_v2.py CN207834740U.pdf output.md")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 创建混合OCR引擎 V2
    engine = HybridOCREngineV2()

    # 初始化
    logger.info("🔧 初始化混合OCR引擎 V2...")
    if not await engine.initialize():
        logger.error("❌ 初始化失败，请检查：")
        logger.error("  1. 8009端口LLM服务是否运行")
        logger.error("  2. pdf2image是否安装: pip install pdf2image")
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
