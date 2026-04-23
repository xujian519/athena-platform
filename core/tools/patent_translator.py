#!/usr/bin/env python3
"""
专利翻译工具 - 支持中英日韩等多语言专利文献互译

功能：
1. 支持语言：中文、英文、日文、韩文
2. 翻译方向：任意两种语言互译
3. 专利术语优化：保留专利专业术语
4. 批量翻译：支持大规模文本翻译

技术方案：
- 主要方案：Google Translate API
- 备选方案：本地NMT模型（Fairseq/MarianMT）
- 专利术语词典：保留专业术语不翻译

Author: Athena平台团队
Date: 2026-04-20
"""

import asyncio
import re
from typing import Dict, List, Optional, Any
from enum import Enum

from core.tools.decorators import tool
from core.logging_config import setup_logging

logger = setup_logging()


class LanguageCode(Enum):
    """支持的语言代码"""
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"


class PatentTranslator:
    """专利翻译器"""

    # 专利术语词典（术语 -> 保持原样）
    PATENT_TERMS = {
        "权利要求": "claims",
        "说明书": "description",
        "摘要": "abstract",
        "附图": "drawings",
        "优先权": "priority",
        "申请日": "filing date",
        "公开日": "publication date",
        "专利号": "patent number",
        "申请号": "application number",
        "IPC分类": "IPC classification",
        "创造性": "inventive step",
        "新颖性": "novelty",
        "实用性": "industrial applicability",
        "现有技术": "prior art",
        "技术领域": "technical field",
        "背景技术": "background art",
        "发明内容": "summary of invention",
        "具体实施方式": "detailed description",
        "实施例": "embodiment",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化翻译器

        Args:
            api_key: Google Translate API密钥（可选，不提供则使用免费方案）
        """
        self.api_key = api_key
        self._init_translator()

    def _init_translator(self):
        """初始化翻译引擎"""
        try:
            # 尝试导入googletrans（免费方案）
            from googletrans import Translator
            self.translator = Translator()
            self.use_api = False
            logger.info("✅ 使用Google Translate免费方案")
        except ImportError:
            logger.warning("⚠️ googletrans未安装，尝试使用API方案")
            self.use_api = True
            self.translator = None
            if not self.api_key:
                logger.warning("⚠️ 未提供API密钥，翻译功能可能受限")

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        preserve_terms: bool = True
    ) -> dict[str, Any]:
        """
        翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言代码（zh/en/ja/ko）
            target_lang: 目标语言代码（zh/en/ja/ko）
            preserve_terms: 是否保留专利术语

        Returns:
            翻译结果字典
        """
        if not text or not text.strip():
            return {
                "success": False,
                "error": "输入文本为空",
                "original": text,
                "translated": ""
            }

        # 验证语言代码
        try:
            source_code = LanguageCode(source_lang).value
            target_code = LanguageCode(target_lang).value
        except ValueError:
            return {
                "success": False,
                "error": f"不支持的语言代码: {source_lang}或{target_lang}",
                "supported": [lang.value for lang in LanguageCode]
            }

        try:
            # 检查翻译器是否可用
            if self.use_api and not self.api_key:
                # 使用模拟翻译（用于演示）
                logger.warning("⚠️ 使用模拟翻译（未安装googletrans或未提供API密钥）")
                translated = self._mock_translate(text, source_lang, target_lang)
            elif self.use_api:
                # 专利术语保护
                if preserve_terms:
                    text = self._protect_patent_terms(text, source_lang, target_lang)

                # 执行翻译
                translated = await self._translate_with_api(text, source_code, target_code)

                # 恢复专利术语
                if preserve_terms:
                    translated = self._restore_patent_terms(translated, source_lang, target_lang)
            else:
                # 专利术语保护
                if preserve_terms:
                    text = self._protect_patent_terms(text, source_lang, target_lang)

                # 执行翻译
                translated = await self._translate_with_free(text, source_code, target_code)

                # 恢复专利术语
                if preserve_terms:
                    translated = self._restore_patent_terms(translated, source_lang, target_lang)

            return {
                "success": True,
                "original": text,
                "translated": translated,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "char_count": len(text)
            }

        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "original": text,
                "translated": ""
            }

    async def _translate_with_free(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """使用免费方案翻译（googletrans）"""
        # googletrans是同步的，使用run_in_executor避免阻塞
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.translator.translate(text, src=source_lang, dest=target_lang)
        )
        return result.text

    async def _translate_with_api(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """使用Google Cloud Translation API翻译"""
        # 需要安装google-cloud-translate
        try:
            from google.cloud import translate_v2 as translate

            translate_client = translate.Client(api_key=self.api_key)
            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                lambda: translate_client.translate(
                    text,
                    source_language=source_lang,
                    target_language=target_lang
                )
            )

            return result['translatedText']

        except ImportError:
            # 回退到免费方案
            logger.warning("⚠️ google-cloud-translate未安装，使用免费方案")
            return await self._translate_with_free(text, source_lang, target_lang)

    def _mock_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        模拟翻译（用于演示和测试）

        当没有安装googletrans或未提供API密钥时使用。
        """
        # 简单的语言映射表（用于演示）
        mock_translations = {
            ("zh", "en"): [
                ("本发明", "The present invention"),
                ("涉及", "relates to"),
                ("一种", "a kind of"),
                ("自动驾驶", "autonomous driving"),
                ("技术", "technology"),
                ("属于", "belongs to"),
                ("智能交通", "intelligent transportation"),
                ("领域", "field"),
            ],
            ("en", "zh"): [
                ("The present invention", "本发明"),
                ("relates to", "涉及"),
                ("autonomous driving", "自动驾驶"),
                ("technology", "技术"),
                ("intelligent transportation", "智能交通"),
                ("field", "领域"),
            ]
        }

        translated = text
        key = (source_lang, target_lang)

        if key in mock_translations:
            for src, tgt in mock_translations[key]:
                translated = translated.replace(src, tgt)

        # 添加翻译标记
        translated = f"[模拟翻译] {translated}"

        return translated

    def _protect_patent_terms(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """保护专利术语，使用占位符替换"""
        # 对于中文→英文，使用中文术语作为key
        # 对于英文→中文，使用英文术语作为key
        if source_lang == "zh":
            for zh_term, en_term in self.PATENT_TERMS.items():
                if zh_term in text:
                    text = text.replace(zh_term, f"[[{zh_term}]]")
        else:
            for zh_term, en_term in self.PATENT_TERMS.items():
                if en_term in text:
                    text = text.replace(en_term, f"[[{en_term}]]")

        return text

    def _restore_patent_terms(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """恢复专利术语"""
        # 恢复占位符为正确的术语
        for zh_term, en_term in self.PATENT_TERMS.items():
            if source_lang == "zh":
                # 中文→英文：恢复为英文术语
                text = text.replace(f"[[{zh_term}]]", en_term)
                text = text.replace(f"[[{en_term}]]", en_term)
            else:
                # 英文→中文：恢复为中文术语
                text = text.replace(f"[[{en_term}]]", zh_term)
                text = text.replace(f"[[{zh_term}]]", zh_term)

        return text

    async def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        preserve_terms: bool = True
    ) -> list[dict[str, Any]]:
        """
        批量翻译

        Args:
            texts: 待翻译文本列表
            source_lang: 源语言代码
            target_lang: 目标语言代码
            preserve_terms: 是否保留专利术语

        Returns:
            翻译结果列表
        """
        results = []
        for text in texts:
            result = await self.translate(text, source_lang, target_lang, preserve_terms)
            results.append(result)

        return results


# 创建全局翻译器实例
_translator_instance: Optional[PatentTranslator] = None


def get_translator() -> PatentTranslator:
    """获取全局翻译器实例（单例模式）"""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = PatentTranslator()
    return _translator_instance


@tool(
    name="patent_translator",
    description="专利文献翻译工具，支持中英日韩多语言互译，保留专利专业术语",
    category="patent_search",
    tags=["patent", "translation", "multilingual", "zh", "en", "ja", "ko"]
)
async def patent_translator_handler(
    text: str,
    target_lang: str = "en",
    source_lang: str = "auto",
    preserve_terms: bool = True
) -> dict[str, Any]:
    """
    专利翻译工具handler

    Args:
        text: 待翻译的专利文本
        target_lang: 目标语言（zh/en/ja/ko）
        source_lang: 源语言（zh/en/ja/ko/auto，默认auto自动检测）
        preserve_terms: 是否保留专利术语（默认True）

    Returns:
        翻译结果字典，包含：
        - success: 是否成功
        - original: 原文
        - translated: 译文
        - source_lang: 源语言
        - target_lang: 目标语言
        - char_count: 字符数
        - error: 错误信息（如果失败）
    """
    translator = get_translator()

    # 自动检测源语言
    if source_lang == "auto":
        # 简单的语言检测逻辑
        if any(ord(c) > 127 for c in text):
            # 包含非ASCII字符
            if any('\u4e00' <= c <= '\u9fff' for c in text):
                source_lang = "zh"  # 中文
            elif any('\u3040' <= c <= '\u309f' for c in text):
                source_lang = "ja"  # 日文
            elif any('\uac00' <= c <= '\ud7af' for c in text):
                source_lang = "ko"  # 韩文
            else:
                source_lang = "en"  # 默认英文
        else:
            source_lang = "en"

    result = await translator.translate(text, source_lang, target_lang, preserve_terms)

    return result


@tool(
    name="patent_translator_batch",
    description="批量专利文献翻译，支持大规模文本翻译",
    category="patent_search",
    tags=["patent", "translation", "batch", "multilingual"]
)
async def patent_translator_batch_handler(
    texts: list[str],
    target_lang: str = "en",
    source_lang: str = "auto",
    preserve_terms: bool = True
) -> list[dict[str, Any]]:
    """
    批量专利翻译工具handler

    Args:
        texts: 待翻译的专利文本列表
        target_lang: 目标语言（zh/en/ja/ko）
        source_lang: 源语言（zh/en/ja/ko/auto）
        preserve_terms: 是否保留专利术语

    Returns:
        翻译结果列表
    """
    translator = get_translator()

    # 自动检测源语言（基于第一个文本）
    if source_lang == "auto" and texts:
        first_text = texts[0]
        if any('\u4e00' <= c <= '\u9fff' for c in first_text):
            source_lang = "zh"
        elif any('\u3040' <= c <= '\u309f' for c in first_text):
            source_lang = "ja"
        elif any('\uac00' <= c <= '\ud7af' for c in first_text):
            source_lang = "ko"
        else:
            source_lang = "en"

    results = await translator.translate_batch(texts, source_lang, target_lang, preserve_terms)

    return results


# 导出
__all__ = [
    "PatentTranslator",
    "get_translator",
    "patent_translator_handler",
    "patent_translator_batch_handler",
    "LanguageCode"
]
