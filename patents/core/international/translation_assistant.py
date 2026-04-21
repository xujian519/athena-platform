#!/usr/bin/env python3
"""
翻译辅助工具

提供多语言翻译支持，帮助国际专利申请。
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranslationAssistant:
    """翻译辅助器"""

    def __init__(self):
        """初始化翻译器"""
        self.translation_glossary = self._load_translation_glossary()
        self.language_codes = {
            "中文": "zh",
            "英语": "en",
            "日语": "ja",
            "韩语": "ko",
            "德语": "de",
            "法语": "fr",
            "西班牙语": "es",
            "俄语": "ru"
        }
        logger.info("✅ 翻译辅助器初始化成功")

    def _load_translation_glossary(self) -> Dict[str, Dict[str, str]]:
        """加载翻译术语表"""
        return {
            "权利要求": {
                "en": "claims",
                "ja": "請求項",
                "ko": "청구항",
                "de": "Ansprüche",
                "fr": "revendications"
            },
            "说明书": {
                "en": "description",
                "ja": "明細書",
                "ko": "명세서",
                "de": "Beschreibung",
                "fr": "description"
            },
            "摘要": {
                "en": "abstract",
                "ja": "要約",
                "ko": "요약",
                "de": "Zusammenfassung",
                "fr": "résumé"
            },
            "发明": {
                "en": "invention",
                "ja": "発明",
                "ko": "발명",
                "de": "Erfindung",
                "fr": "invention"
            },
            "申请人": {
                "en": "applicant",
                "ja": "出願人",
                "ko": "출원인",
                "de": "Anmelder",
                "fr": "demandeur"
            },
            "优先权": {
                "en": "priority",
                "ja": "優先権",
                "ko": "우선권",
                "de": "Priorität",
                "fr": "priorité"
            }
        }

    def translate_term(self, term: str, target_language: str) -> str:
        """
        翻译专利术语

        Args:
            term: 中文术语
            target_language: 目标语言代码

        Returns:
            翻译结果
        """
        lang_code = self.language_codes.get(target_language, target_language)

        if term in self.translation_glossary:
            translations = self.translation_glossary[term]
            return translations.get(lang_code, term)

        # 如果没有找到，返回原词
        return term

    def translate_claims(self, claims: List[str], target_language: str) -> List[str]:
        """翻译权利要求"""
        translated = []
        for claim in claims:
            # 简化翻译：替换关键词
            translated_claim = claim
            for cn_term, translations in self.translation_glossary.items():
                en_term = translations.get("en", cn_term)
                if cn_term in translated_claim:
                    translated_claim = translated_claim.replace(cn_term, en_term)
            translated.append(translated_claim)
        return translated

    def get_translation_glossary(self, terms: List[str], target_languages: List[str]) -> Dict[str, Dict[str, str]]:
        """获取多语言术语对照表"""
        glossary = {}
        for term in terms:
            if term in self.translation_glossary:
                translations = self.translation_glossary[term]
                term_translations = {}
                for lang in target_languages:
                    lang_code = self.language_codes.get(lang, lang)
                    term_translations[lang] = translations.get(lang_code, term)
                glossary[term] = term_translations
        return glossary

    def generate_multilingual_abstract(self, abstract: str, target_languages: List[str]) -> Dict[str, str]:
        """生成多语言摘要"""
        multilingual = {"中文": abstract}

        # 简化处理：实际应用中需要调用翻译API
        for lang in target_languages:
            if lang == "英语":
                multilingual[lang] = f"[EN] {abstract}"
            elif lang == "日语":
                multilingual[lang] = f"[JA] {abstract}"
            # 其他语言...

        return multilingual


if __name__ == "__main__":
    assistant = TranslationAssistant()

    # 测试术语翻译
    print("\n" + "="*80)
    print("🌐 翻译辅助器测试")
    print("="*80)

    terms = ["权利要求", "说明书", "摘要", "发明", "申请人", "优先权"]
    languages = ["英语", "日语", "德语"]

    glossary = assistant.get_translation_glossary(terms, languages)

    print(f"\n📖 术语对照表:")
    for term, translations in glossary.items():
        print(f"\n   {term}:")
        for lang, trans in translations.items():
            print(f"      {lang}: {trans}")

    # 测试权利要求翻译
    claims = ["1. 一种智能控制方法，其特征在于..."]
    translated = assistant.translate_claims(claims, "英语")

    print(f"\n✅ 权利要求翻译:")
    print(f"   原文: {claims[0]}")
    print(f"   译文: {translated[0]}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
