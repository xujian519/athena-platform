#!/usr/bin/env python3
"""
技术交底书解析器

解析技术交底书文档，提取结构化信息。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from core.tools.enhanced_document_parser import EnhancedDocumentParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DisclosureDocument:
    """技术交底书文档"""
    raw_text: str  # 原始文本
    sections: dict[str, str] = field(default_factory=dict)  # 各章节内容
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据
    confidence: float = 0.0  # 解析置信度

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "raw_text": self.raw_text,
            "sections": self.sections,
            "metadata": self.metadata,
            "confidence": self.confidence
        }


class DisclosureDocumentParser:
    """技术交底书解析器"""

    def __init__(self):
        """初始化解析器"""
        self.document_parser = EnhancedDocumentParser()
        logger.info("✅ 技术交底书解析器初始化成功")

    async def parse_disclosure(
        self,
        file_path: str,
        use_ocr: bool = True
    ) -> DisclosureDocument:
        """
        解析技术交底书文档

        Args:
            file_path: 文档文件路径
            use_ocr: 是否使用OCR

        Returns:
            DisclosureDocument对象
        """
        logger.info(f"📄 开始解析技术交底书: {file_path}")

        try:
            # 1. 使用EnhancedDocumentParser解析文档
            parse_result = await self.document_parser.parse(
                file_path=file_path,
                use_ocr=use_ocr
            )

            if not parse_result.get("success", False):
                error_msg = parse_result.get("error", "未知错误")
                logger.error(f"❌ 文档解析失败: {error_msg}")
                return DisclosureDocument(
                    raw_text="",
                    confidence=0.0
                )

            # 2. 提取原始文本和元数据
            raw_text = parse_result.get("content", "")
            metadata = parse_result.get("metadata", {})

            # 3. 提取各章节内容
            sections = self._extract_sections(raw_text)

            # 4. 计算置信度
            confidence = self._calculate_confidence(sections, raw_text)

            logger.info(f"✅ 技术交底书解析完成，置信度: {confidence:.2f}")

            return DisclosureDocument(
                raw_text=raw_text,
                sections=sections,
                metadata=metadata,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"❌ 解析技术交底书失败: {e}")
            import traceback
            traceback.print_exc()
            return DisclosureDocument(
                raw_text="",
                confidence=0.0
            )

    def _extract_sections(self, text: str) -> dict[str, str]:
        """
        提取各章节内容

        Args:
            text: 原始文本

        Returns:
            章节字典
        """
        sections = {}

        # 定义章节标题模式
        section_patterns = {
            "发明名称": r"(?:发明名称|名称)[：:]\s*(.+?)(?:\n|$)",
            "技术领域": r"(?:技术领域)[：:]\s*(.+?)(?=\n(?:背景技术|发明内容|现有技术)|$)",
            "背景技术": r"(?:背景技术|现有技术)[：:]\s*(.+?)(?=\n(?:发明内容|技术问题|技术方案)|$)",
            "发明内容": r"(?:发明内容)[：:]\s*(.+?)(?=\n(?:具体实施方式|附图说明|具体实施方式)|$)",
            "技术问题": r"(?:技术问题|所要解决的技术问题)[：:]\s*(.+?)(?=\n|$)",
            "技术方案": r"(?:技术方案|技术解决方案)[：:]\s*(.+?)(?=\n|$)",
            "技术效果": r"(?:技术效果|有益效果)[：:]\s*(.+?)(?=\n|$)",
            "具体实施方式": r"(?:具体实施方式|实施例)[：:]\s*(.+)$",
            "附图说明": r"(?:附图说明)[：:]\s*(.+?)(?=\n(?:具体实施方式|发明内容)|$)",
        }

        import re

        # 提取各章节
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                content = match.group(1).strip()
                # 清理内容（去除多余的空白行）
                content = re.sub(r'\n{3,}', '\n\n', content)
                sections[section_name] = content
            else:
                # 如果没有匹配到，尝试模糊匹配
                sections[section_name] = ""

        # 如果某些关键章节为空，尝试从全文中提取
        if not sections.get("技术领域"):
            sections["技术领域"] = self._extract_field(text)

        if not sections.get("技术问题"):
            sections["技术问题"] = self._extract_problem(text)

        if not sections.get("技术方案"):
            sections["技术方案"] = self._extract_solution(text)

        if not sections.get("技术效果"):
            sections["技术效果"] = self._extract_effects(text)

        return sections

    def _extract_field(self, text: str) -> str:
        """提取技术领域"""
        import re

        # 查找包含"技术领域"、"所属技术领域"等的段落
        patterns = [
            r'(?:所属)?技术领域[：:][^\n]*?(?=[，。；\n]|$)',
            r'本发明涉及[^\n]*?(?=[，。；\n]|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return " ".join(matches[:3])  # 取前3个匹配

        return ""

    def _extract_problem(self, text: str) -> str:
        """提取技术问题"""
        import re

        # 查找包含"技术问题"、"缺陷"、"不足"等的段落
        patterns = [
            r'(?:所要解决)?技术问题[：:][^\n]*?(?=[，。；\n]|$)',
            r'(?:现有技术中存在)?(?:缺陷|不足|问题)[：:][^\n]*?(?=[，。；\n]|$)',
            r'为了解决[^\n]*?(?=[，。；\n]|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return " ".join(matches[:5])  # 取前5个匹配

        return ""

    def _extract_solution(self, text: str) -> str:
        """提取技术方案"""
        import re

        # 查找包含"技术方案"、"采用"、"包括"等的段落
        patterns = [
            r'技术方案[：:][^\n]*?(?=[，。；\n]|$)',
            r'采用[^\n]*?(?=[，。；\n]|$)',
            r'包括[：:][^\n]*?(?=[，。；\n]|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return " ".join(matches[:10])  # 取前10个匹配

        return ""

    def _extract_effects(self, text: str) -> str:
        """提取技术效果"""
        import re

        # 查找包含"技术效果"、"有益效果"、"优点"等的段落
        patterns = [
            r'(?:有益)?技术效果[：:][^\n]*?(?=[，。；\n]|$)',
            r'优点[：:][^\n]*?(?=[，。；\n]|$)',
            r'优势[：:][^\n]*?(?=[，。；\n]|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return " ".join(matches[:5])  # 取前5个匹配

        return ""

    def _calculate_confidence(
        self,
        sections: dict[str, str],
        raw_text: str
    ) -> float:
        """
        计算解析置信度

        Args:
            sections: 章节字典
            raw_text: 原始文本

        Returns:
            置信度分数 (0-1)
        """
        # 关键章节权重
        key_sections = {
            "技术领域": 0.1,
            "背景技术": 0.1,
            "技术问题": 0.2,
            "技术方案": 0.3,
            "技术效果": 0.2,
            "具体实施方式": 0.1,
        }

        confidence = 0.0

        # 计算关键章节覆盖率
        for section_name, weight in key_sections.items():
            if sections.get(section_name):
                confidence += weight

        # 如果文本长度合理，加分
        if 100 < len(raw_text) < 50000:
            confidence += 0.1

        return min(confidence, 1.0)


async def test_disclosure_parser():
    """测试技术交底书解析器"""
    parser = DisclosureDocumentParser()

    print("\n" + "="*80)
    print("📄 技术交底书解析器测试")
    print("="*80)

    # 测试文本解析（模拟技术交底书）
    test_text = """
发明名称：一种基于深度学习的图像识别方法

技术领域：
本发明涉及计算机视觉和人工智能技术领域，具体涉及一种基于深度卷积神经网络的图像识别方法。

背景技术：
现有的图像识别方法主要基于传统机器学习算法，如SVM、随机森林等。这些方法需要手工设计特征，对于复杂的图像识别任务效果有限。

技术问题：
本发明要解决的技术问题是：如何提高图像识别的准确率和鲁棒性，减少对手工特征工程的依赖。

技术方案：
本发明提供一种基于深度学习的图像识别方法，包括：输入层，用于接收待识别图像；卷积层，用于提取图像特征；池化层，用于降维和特征选择；全连接层，用于分类识别；输出层，输出识别结果。

技术效果：
本发明能够自动提取图像特征，提高识别准确率，具有良好的泛化能力。

具体实施方式：
如图1所示，本发明的图像识别方法采用深度卷积神经网络结构...
"""

    # 保存测试文本到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_text)
        temp_file = f.name

    try:
        # 解析文档
        result = await parser.parse_disclosure(temp_file, use_ocr=False)

        print(f"\n✅ 解析置信度: {result.confidence:.2f}")
        print("\n📋 提取的章节:")
        for section_name, content in result.sections.items():
            if content:
                print(f"\n【{section_name}】")
                print(f"  {content[:100]}..." if len(content) > 100 else f"  {content}")

        print("\n" + "="*80)
        print("✅ 测试完成")
        print("="*80)

    finally:
        # 清理临时文件
        import os
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    asyncio.run(test_disclosure_parser())
