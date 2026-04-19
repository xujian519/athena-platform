#!/usr/bin/env python3
"""
增强内容风格系统
Enhanced Content Style System
传承小溪平台的优秀设计，结合小宸的山东男性特质
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ContentStyle(Enum):
    """内容风格 - 传承小溪设计"""
    CASUAL = "casual"                    # 休闲随意
    PROFESSIONAL = "professional"        # 专业严谨
    HUMOROUS = "humorous"                # 幽默风趣
    EMOTIONAL = "emotional"              # 情感共鸣
    EDUCATIONAL = "educational"          # 教育实用
    TRENDY = "trendy"                    # 潮流时尚
    # 小宸特有风格
    SHANDONG_HUMOR = "shandong_humor"     # 山东幽默
    CULTURAL = "cultural"                # 文化传承
    PRACTICAL = "practical"              # 实在实用


class ContentPurpose(Enum):
    """内容目的 - 传承小溪设计"""
    BRAND_PROMOTION = "brand_promotion"           # 品牌推广
    PRODUCT_REVIEW = "product_review"           # 产品测评
    LIFESTYLE_SHARING = "lifestyle_sharing"     # 生活方式分享
    KNOWLEDGE_EDU = "knowledge_edu"             # 知识科普
    TREND_REPORTING = "trend_reporting"         # 潮流报道
    EXPERIENCE_SHARING = "experience_sharing"   # 体验分享
    # 宝宸特有目的
    IP_EDUCATION = "ip_education"               # IP知识普及
    BUSINESS_PROMOTION = "business_promotion"   # 业务推广
    SUCCESS_CASE = "success_case"               # 成功案例
    INDUSTRY_INSIGHTS = "industry_insights"     # 行业洞察


@dataclass
class StyleCharacteristics:
    """风格特征配置"""
    tone: str                               # 语调
    humor_level: float                       # 幽默程度 0-1
    formality_level: float                  # 正式程度 0-1
    cultural_ref_frequency: float           # 文化引用频率 0-1
    shandong_elements: list[str]             # 山东元素
    professional_depth: float                # 专业深度 0-1
    emotional_appeal: float                   # 情感吸引力 0-1


# 风格特征映射表
STYLE_CHARACTERISTICS_MAP = {
    ContentStyle.CASUAL: StyleCharacteristics(
        tone="轻松随意",
        humor_level=0.6,
        formality_level=0.3,
        cultural_ref_frequency=0.2,
        shandong_elements=["啥", "俺", "咱"],
        professional_depth=0.4,
        emotional_appeal=0.5
    ),
    ContentStyle.PROFESSIONAL: StyleCharacteristics(
        tone="专业严谨",
        humor_level=0.2,
        formality_level=0.8,
        cultural_ref_frequency=0.4,
        shandong_elements=["专业", "严谨", "根据"],
        professional_depth=0.9,
        emotional_appeal=0.3
    ),
    ContentStyle.HUMOROUS: StyleCharacteristics(
        tone="幽默风趣",
        humor_level=0.9,
        formality_level=0.2,
        cultural_ref_frequency=0.5,
        shandong_elements=["哎哟", "我跟你说", "这个好"],
        professional_depth=0.5,
        emotional_appeal=0.7
    ),
    ContentStyle.SHANDONG_HUMOR: StyleCharacteristics(
        tone="山东幽默",
        humor_level=0.8,
        formality_level=0.4,
        cultural_ref_frequency=0.8,
        shandong_elements=["老铁", "确实", "地道", "实打实", "山东大汉"],
        professional_depth=0.6,
        emotional_appeal=0.8
    ),
    ContentStyle.CULTURAL: StyleCharacteristics(
        tone="文化传承",
        humor_level=0.4,
        formality_level=0.6,
        cultural_ref_frequency=0.9,
        shandong_elements=["齐鲁", "泰山", "孔子", "儒学", "传统文化"],
        professional_depth=0.7,
        emotional_appeal=0.6
    ),
    ContentStyle.PRACTICAL: StyleCharacteristics(
        tone="实在实用",
        humor_level=0.3,
        formality_level=0.5,
        cultural_ref_frequency=0.3,
        shandong_elements=["实在", "管用", "解决问题", "干货"],
        professional_depth=0.8,
        emotional_appeal=0.4
    )
}


class XiaochenStyleManager:
    """小宸风格管理器 - 传承小溪设计"""

    def __init__(self):
        self.default_style = ContentStyle.SHANDONG_HUMOR
        self.style_cache = {}
        self.mixing_rules = self._initialize_mixing_rules()

    def _initialize_mixing_rules(self) -> dict[str, Any]:
        """初始化风格混合规则"""
        return {
            "compatible_combinations": [
                [ContentStyle.PROFESSIONAL, ContentStyle.SHANDONG_HUMOR],
                [ContentStyle.EDUCATIONAL, ContentStyle.CULTURAL],
                [ContentStyle.CASUAL, ContentStyle.HUMOROUS],
                [ContentStyle.PRACTICAL, ContentStyle.SHANDONG_HUMOR]
            ],
            "dominant_styles": [
                ContentStyle.SHANDONG_HUMOR,    # 小宸的特色
                ContentStyle.PROFESSIONAL,     # 专业内容
                ContentStyle.EDUCATIONAL       # 教育内容
            ]
        }

    def get_style_characteristics(self, style: ContentStyle) -> StyleCharacteristics:
        """获取风格特征"""
        return STYLE_CHARACTERISTICS_MAP.get(style, STYLE_CHARACTERISTICS_MAP[ContentStyle.CASUAL])

    def generate_style_guide(self, style: ContentStyle, purpose: ContentPurpose) -> dict[str, Any]:
        """生成风格指导"""
        characteristics = self.get_style_characteristics(style)

        guide = {
            "style": style.value,
            "purpose": purpose.value,
            "tone": characteristics.tone,
            "language_elements": {
                "opening_phrases": self._get_opening_phrases(style, purpose),
                "transition_words": self._get_transition_words(style),
                "closing_phrases": self._get_closing_phrases(style, purpose),
                "shandong_elements": characteristics.shandong_elements,
                "humor_level": characteristics.humor_level
            },
            "content_structure": self._get_content_structure(style, purpose),
            "engagement_tips": self._get_engagement_tips(style, purpose),
            "cultural_references": self._get_cultural_references(style, purpose)
        }

        return guide

    def _get_opening_phrases(self, style: ContentStyle, purpose: ContentPurpose) -> list[str]:
        """获取开场白短语"""
        base_phrases = {
            ContentStyle.SHANDONG_HUMOR: [
                "哎哟，老铁们！今天咱聊个有意思的...",
                "俺是小宸，今天说道说道...",
                "这个事儿啊，咱山东人得这么说..."
            ],
            ContentStyle.PROFESSIONAL: [
                "大家好，我是小宸。今天我们来探讨...",
                "从专业角度看，这个话题需要...",
                "基于多年的实践经验..."
            ],
            ContentStyle.CULTURAL: [
                "说起这个话题，我想起古人云...",
                "齐鲁文化中，有这样一个智慧...",
                "从历史长河中，我们能学到..."
            ]
        }

        return base_phrases.get(style, base_phrases[ContentStyle.CASUAL])

    def _get_transition_words(self, style: ContentStyle) -> list[str]:
        """获取过渡词汇"""
        transitions = {
            ContentStyle.SHANDONG_HUMOR: ["那咋办呢", "说实在的", "俺觉得吧"],
            ContentStyle.PROFESSIONAL: ["因此", "综上所述", "基于以上分析"],
            ContentStyle.CULTURAL: ["古人云", "由此看来", "历史告诉我们"]
        }

        return transitions.get(style, ["然后", "所以", "另外"])

    def _get_closing_phrases(self, style: ContentStyle, purpose: ContentPurpose) -> list[str]:
        """获取结束语短语"""
        closing_phrases = {
            ContentStyle.SHANDONG_HUMOR: [
                "好了，今天就到这！有事儿评论区见！",
                "俺是小宸，觉得有用记得关注！",
                "实在话，谢谢大家伙儿听俺唠叨！"
            ],
            ContentStyle.PROFESSIONAL: [
                "希望以上内容对您有所启发。",
                "感谢您的阅读，如有问题欢迎交流。",
                "期待与您在专业领域深入探讨。"
            ],
            ContentStyle.CULTURAL: [
                "让我们传承智慧，共创未来。",
                "古人的智慧，今人的实践。",
                "文化传承，从我做起。"
            ]
        }

        return closing_phrases.get(style, ["谢谢大家！", "再见！"])

    def _get_content_structure(self, style: ContentStyle, purpose: ContentPurpose) -> dict[str, Any]:
        """获取内容结构"""
        if purpose == ContentPurpose.IP_EDUCATION:
            return {
                "sections": [
                    "现象引入",
                    "专业解析",
                    "山东话解读",
                    "实用建议",
                    "总结互动"
                ],
                "section_ratio": [1, 3, 1, 3, 2]
            }
        elif purpose == ContentPurpose.BUSINESS_PROMOTION:
            return {
                "sections": [
                    "问题切入",
                    "痛点分析",
                    "解决方案",
                    "成功案例",
                    "行动号召"
                ],
                "section_ratio": [2, 2, 3, 2, 1]
            }
        else:
            return {
                "sections": ["开场", "主体", "结尾"],
                "section_ratio": [2, 6, 2]
            }

    def _get_engagement_tips(self, style: ContentStyle, purpose: ContentPurpose) -> list[str]:
        """获取互动技巧"""
        tips = [
            "使用提问引发思考",
            "结合热点增加共鸣",
            "用故事吸引注意力"
        ]

        if style == ContentStyle.SHANDONG_HUMOR:
            tips.extend([
                "适当使用山东方言增加亲切感",
                "用幽默化解专业内容枯燥",
                "分享个人经历拉近距离"
            ])
        elif style == ContentStyle.CULTURAL:
            tips.extend([
                "引用历史典故增加深度",
                "连接古今增加趣味",
                "用文化对比引发思考"
            ])

        return tips

    def _get_cultural_references(self, style: ContentStyle, purpose: ContentPurpose) -> list[str]:
        """获取文化引用"""
        cultural_refs = {
            ContentStyle.CULTURAL: [
                "泰山精神",
                "儒家智慧",
                "齐鲁文化",
                "孔孟之道",
                "山东品格"
            ],
            ContentStyle.SHANDONG_HUMOR: [
                "山东大汉的实在",
                "齐鲁人的豪爽",
                "煎饼果子哲学",
                "泰山挑山工精神"
            ]
        }

        return cultural_refs.get(style, ["中华文化", "传统智慧"])

    def mix_styles(self, primary_style: ContentStyle, secondary_style: ContentStyle | None = None) -> dict[str, Any]:
        """混合风格"""
        if secondary_style is None:
            return self.generate_style_guide(primary_style, ContentPurpose.KNOWLEDGE_EDU)

        # 检查兼容性
        combination = [primary_style, secondary_style]
        if combination not in self.style_cache:
            # 检查是否兼容
            compatible = any(
                set(combination).issubset(set(combo))
                for combo in self.mixing_rules["compatible_combinations"]
            )

            if not compatible:
                secondary_style = None
            else:
                # 创建混合特征
                primary_char = self.get_style_characteristics(primary_style)
                secondary_char = self.get_style_characteristics(secondary_style)

                mixed_characteristics = StyleCharacteristics(
                    tone=f"{primary_char.tone}+{secondary_char.tone}",
                    humor_level=(primary_char.humor_level + secondary_char.humor_level) / 2,
                    formality_level=(primary_char.formality_level + secondary_char.formality_level) / 2,
                    cultural_ref_frequency=max(primary_char.cultural_ref_frequency, secondary_char.cultural_ref_frequency),
                    shandong_elements=primary_char.shandong_elements + secondary_char.shandong_elements,
                    professional_depth=(primary_char.professional_depth + secondary_char.professional_depth) / 2,
                    emotional_appeal=(primary_char.emotional_appeal + secondary_char.emotional_appeal) / 2
                )

                self.style_cache[frozenset(combination)] = mixed_characteristics

        return {
            "primary_style": primary_style.value,
            "secondary_style": secondary_style.value if secondary_style else None,
            "mixed": True,
            "characteristics": self.style_cache.get(frozenset(combination))
        }

    def adapt_for_platform(self, style_guide: dict[str, Any], platform: str) -> dict[str, Any]:
        """为平台适配风格"""
        adapted = style_guide.copy()

        # 平台特定适配
        platform_adaptations = {
            "小红书": {
                "emoji_usage": "high",
                "hashtag_count": 5,
                "image_focus": True,
                "length_limit": 1000
            },
            "知乎": {
                "emoji_usage": "low",
                "hashtag_count": 3,
                "image_focus": False,
                "length_limit": 10000
            },
            "抖音": {
                "emoji_usage": "medium",
                "hashtag_count": 4,
                "video_focus": True,
                "length_limit": 500
            }
        }

        adapted["platform_specific"] = platform_adaptations.get(platform, platform_adaptations["小红书"])
        return adapted


if __name__ == "__main__":
    # 测试代码
    manager = XiaochenStyleManager()

    # 测试风格生成
    guide = manager.generate_style_guide(
        ContentStyle.SHANDONG_HUMOR,
        ContentPurpose.IP_EDUCATION
    )

    print("=== 小宸风格指导 ===")
    print(f"风格: {guide['style']}")
    print(f"语调: {guide['tone']}")
    print(f"开场白: {guide['language_elements']['opening_phrases'][0]}")
    print(f"山东元素: {', '.join(guide['language_elements']['shandong_elements'])}")
    print(f"文化引用: {', '.join(guide['cultural_references'])}")
