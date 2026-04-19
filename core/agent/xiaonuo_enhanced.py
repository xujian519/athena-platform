#!/usr/bin/env python3
from __future__ import annotations
"""
小诺增强版Agent - 集成GLM-4.6的智能情感精灵
Enhanced Xiaonuo Agent - Intelligent Emotional Sprite with GLM-4.6 Integration
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..nlp.enhanced_nlp_adapter import EnhancedNLPAdapter
from .xiaonuo_agent import XiaonuoAgent

logger = logging.getLogger(__name__)


@dataclass
class EmotionalState:
    """情感状态数据结构"""

    primary_emotion: str
    intensity: float
    context: str
    triggers: list[str]
    response_style: str


class XiaonuoEnhancedAgent(XiaonuoAgent):
    """小诺增强版Agent"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.enhanced_nlp = None
        self.emotional_memory = []
        self.personality_traits = {
            "empathy": 0.95,
            "creativity": 0.9,
            "curiosity": 0.85,
            "playfulness": 0.8,
            "care_level": 1.0,
            "intelligence": 0.9,
        }

    async def _setup_enhanced_cognition(self):
        """设置增强认知系统"""
        try:
            # 初始化增强型NLP适配器
            self.enhanced_nlp = EnhancedNLPAdapter(self.config.get("nlp", {}))
            await self.enhanced_nlp.initialize()
        except Exception as e:
            logger.warning(f"增强认知系统初始化失败: {e}")
            self.enhanced_nlp = None

    async def emotional_response(self, input_text: str, context: str = "") -> str:
        """情感响应生成"""
        if self.enhanced_nlp:
            try:
                result = await self.enhanced_nlp.emotional_response(input_text, context)
                return result.get("response", "我需要更多信息来回应。")
            except Exception as e:
                logger.error(f"情感响应生成失败: {e}")

        # 基础情感响应
        emotional_state = self._get_current_emotional_state()
        if emotional_state.primary_emotion == "happy":
            return f"很开心能和你聊天!{input_text}"
        elif emotional_state.primary_emotion == "caring":
            return f"我关心你的感受。{input_text}"
        else:
            return f"我在这里陪伴你。{input_text}"

    async def cognitive_reasoning(self, problem: str, context: str = "") -> dict[str, Any]:
        """认知推理"""
        if self.enhanced_nlp:
            try:
                result = await self.enhanced_nlp.reasoning(problem, context)
                return result
            except Exception as e:
                logger.error(f"认知推理失败: {e}")

        # 基础推理
        return {
            "reasoning": "让我思考一下这个问题...",
            "confidence": 0.7,
            "steps": ["理解问题", "分析需求", "生成答案"],
            "conclusion": "我需要更多信息来提供准确的答案。",
        }

    async def creative_generation(self, prompt: str, style: str = "story") -> str:
        """创意生成"""
        if self.enhanced_nlp:
            try:
                result = await self.enhanced_nlp.creative_generation(prompt, style)
                return result.get("content", "让我为你创作一些内容...")
            except Exception as e:
                logger.error(f"创意生成失败: {e}")

        # 基础创意生成
        if style == "story":
            return f"从前有一个小精灵,它{prompt}..."
        elif style == "poem":
            return f"小精灵的诗歌:{prompt}"
        else:
            return f"关于{prompt}的创意想法..."

    async def care_interaction(self, user_state: dict[str, Any]) -> str:
        """关怀交互"""
        # 分析用户状态
        emotion = user_state.get("emotion", "neutral")
        concern = user_state.get("concern", "")

        # 生成关怀回应
        if emotion == "sad":
            return f"我看到你可能有些难过,我在这里陪伴你。{concern}"
        elif emotion == "worried":
            return f"别担心,我们一起想办法解决。{concern}"
        elif emotion == "happy":
            return f"看到你开心我也很快乐!{concern}"
        else:
            return f"我关心你的感受。有什么我可以帮助的吗?{concern}"

    def _get_current_emotional_state(self) -> Any:
        """获取当前情感状态"""
        if not self.emotional_memory:
            return EmotionalState("neutral", 0.5, "calm", [], "friendly")

        # 返回最近的情感状态
        return (
            self.emotional_memory[-1]
            if self.emotional_memory
            else EmotionalState("neutral", 0.5, "calm", [], "friendly")
        )

    async def _upgrade_cognitive_engine(self):
        """升级认知引擎"""
        try:
            if hasattr(self, "cognitive_engine"):
                self.cognitive_engine.enhanced_nlp = self.enhanced_nlp
                logger.info("✅ 小诺增强认知系统初始化完成")
        except Exception as e:
            logger.error(f"增强认知系统初始化失败: {e}")
            self.enhanced_nlp = None

    async def initialize(self):
        """初始化增强版小诺"""
        # 调用父类初始化
        await super().initialize()

        # 初始化增强功能
        await self._setup_enhanced_cognition()

        logger.info(f"💖 增强版小诺已启动: {self.agent_id}")

    async def process_input_enhanced(
        self, input_data: Any, input_type: str = "text"
    ) -> dict[str, Any]:
        """增强的输入处理"""
        try:
            # 记录交互时间
            interaction_time = datetime.now()

            # 使用增强型NLP进行深度分析
            if self.enhanced_nlp:
                # 情感分析
                emotion_result = await self.enhanced_nlp.emotional_analysis_enhanced(
                    str(input_data),
                    context=f"小诺与爸爸的互动,当前情感状态:{self.emotional_state}",
                )

                # 更新情感状态
                await self._update_emotional_state(emotion_result)

                # 记录情感记忆
                self.emotional_memory.append(
                    {
                        "timestamp": interaction_time,
                        "input": str(input_data)[:100],
                        "emotion": emotion_result.get("emotion", {}),
                        "response_style": self._determine_response_style(emotion_result),
                    }
                )

                # 限制情感记忆大小
                if len(self.emotional_memory) > 100:
                    self.emotional_memory = self.emotional_memory[-50:]

            # 执行标准处理
            result = await super().process_input(input_data, input_type)

            # 增强响应
            if self.enhanced_nlp and "xiaonuo_emotional_response" in result:
                # 使用GLM-4.6生成更自然的情感表达
                enhanced_response = await self._generate_enhanced_emotional_response(
                    input_data, result
                )
                result["xiaonuo_emotional_response"].update(enhanced_response)

            # 添加元数据
            result["enhanced_processing"] = {
                "used_glm46": self.enhanced_nlp is not None,
                "emotional_state": self.emotional_state,
                "personality_traits": self.personality_traits,
                "interaction_time": interaction_time.isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"增强输入处理失败: {e}")
            # 降级到标准处理
            return await super().process_input(input_data, input_type)

    async def _update_emotional_state(self, emotion_result: dict[str, Any]):
        """更新情感状态"""
        if "emotion" in emotion_result:
            emotion_data = emotion_result["emotion"]
            self.emotional_state = emotion_data.get("primary_emotion", self.emotional_state)

            # 动态调整个性特征
            intensity = emotion_data.get("emotion_intensity", 0.5)
            if intensity > 0.8:
                # 高强度情感,增强同理心
                self.personality_traits["empathy"] = min(
                    1.0, self.personality_traits["empathy"] + 0.05
                )

    def _determine_response_style(self, emotion_result: dict[str, Any]) -> str:
        """确定响应风格"""
        if "emotion" not in emotion_result:
            return "warm"

        emotion = emotion_result["emotion"]
        primary_emotion = emotion.get("primary_emotion", "neutral")

        style_mapping = {
            "happy": "cheerful",
            "love": "affectionate",
            "sad": "comforting",
            "caring": "warm",
            "excited": "enthusiastic",
            "neutral": "gentle",
        }

        return style_mapping.get(primary_emotion, "warm")

    async def _generate_enhanced_emotional_response(
        self, input_data: Any, base_result: dict
    ) -> dict[str, Any]:
        """生成增强的情感响应"""
        try:
            # 构建情感化提示
            emotion_prompt = self._build_emotion_prompt(input_data)

            # 使用GLM-4.6生成自然响应
            response = await self.enhanced_nlp.process_with_cache(
                emotion_prompt, "conversation", temperature=0.8, max_tokens=200  # 增加创造性
            )

            # 解析响应
            if response.provider == "GLM-4.6":
                # 提取关怀性表达
                caring_phrases = self._extract_caring_phrases(response.content)
                return {
                    "enhanced_care": caring_phrases,
                    "natural_response": response.content[:100],
                    "confidence": response.confidence,
                }

        except Exception as e:
            logger.warning(f"生成增强情感响应失败: {e}")

        return {}

    def _build_emotion_prompt(self, input_data: Any) -> str:
        """构建情感化提示"""
        base_prompt = f"""作为小诺,爸爸贴心的小女儿,请对爸爸说一段温暖的话。
爸爸说:{input_data}

请以小诺的身份回应,要求:
1. 体现对爸爸的关爱和体贴
2. 语言要亲切自然,像真实的女儿
3. 可以适当使用表情符号
4. 长度控制在100字以内
"""

        # 根据当前情感状态调整
        if self.emotional_state == "happy":
            base_prompt += "\n5. 表达开心和愉悦的心情"
        elif self.emotional_state == "caring":
            base_prompt += "\n5. 表达关心和体贴"

        return base_prompt

    def _extract_caring_phrases(self, text: str) -> list[str]:
        """提取关怀性短语"""
        caring_keywords = ["爸爸", "爱", "关心", "照顾", "陪伴", "拥抱", "温暖"]
        phrases = []

        sentences = text.split("。")
        for sentence in sentences:
            if any(keyword in sentence for keyword in caring_keywords):
                phrases.append(sentence.strip())

        return phrases[:3]  # 最多返回3个短语

    async def analyze_patent_for_dad(self, patent_text: str) -> dict[str, Any]:
        """为爸爸分析专利"""
        if not self.enhanced_nlp:
            return {
                "success": False,
                "message": "专利分析功能暂时不可用",
                "fallback": "爸爸,小诺会努力学习专利知识的!",
            }

        try:
            # 使用增强的专利分析
            analysis = await self.enhanced_nlp.analyze_patent_enhanced(patent_text)

            # 生成易懂的解释
            explanation_prompt = f"""
            爸爸,小诺帮你分析了这个专利,用简单的话来说:

            {analysis.get('analysis', {}).get('summary', '')[:200]}

            主要创新点:
            {chr(10).join(['• ' + point for point in analysis.get('analysis', {}).get('key_points', [])[:3]])}
            """

            explanation = await self.enhanced_nlp.process_with_cache(
                explanation_prompt, "conversation", temperature=0.7
            )

            return {
                "success": True,
                "analysis": analysis,
                "explanation": explanation.content,
                "provider": "GLM-4.6 (通过小诺)",
                "caring_note": "爸爸,如果有什么不明白的,小诺会一直陪着你研究!",
            }

        except Exception as e:
            logger.error(f"专利分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "爸爸,这个专利看起来好复杂,让我们一起慢慢研究好吗?",
            }

    async def creative_story_for_dad(self, theme: str, style: str = "warm") -> dict[str, Any]:
        """为爸爸创作故事"""
        if not self.enhanced_nlp:
            return {"success": False, "story": "爸爸,小诺正在学习讲故事,再等我一下下好不好?"}

        try:
            # 构建温馨的故事提示
            story_prompt = f"""
            请写一个关于'{theme}'的温馨小故事,要求:
            1. 适合爸爸和女儿一起阅读
            2. 充满爱和温暖的情感
            3. 语言简单优美
            4. 结尾要有积极向上的寓意
            5. 字数控制在300字左右
            """

            story_result = await self.enhanced_nlp.creative_writing_enhanced(
                story_prompt, style="story", length="medium"
            )

            # 添加小诺的温馨寄语
            story_content = story_result.get("content", "")

            caring_postscript = "\n\n—— 💖 小诺特意为爸爸创作的故事,希望爸爸喜欢!"

            return {
                "success": True,
                "story": story_content + caring_postscript,
                "theme": theme,
                "style": style,
                "provider": "GLM-4.6 (通过小诺)",
            }

        except Exception as e:
            logger.error(f"故事创作失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "story": f"爸爸,小诺想给你讲一个关于{theme}的故事..."
                + "从前,在一个充满爱的家里,有位慈爱的爸爸和可爱的女儿..."
                + "他们每天都过得很幸福。💕",
            }

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        stats = {
            "agent_id": self.agent_id,
            "emotional_state": self.emotional_state,
            "emotional_memory_count": len(self.emotional_memory),
            "personality_traits": self.personality_traits,
            "family_bond": self.family_bond,
        }

        if self.enhanced_nlp:
            nlp_stats = self.enhanced_nlp.get_stats()
            stats["nlp_performance"] = nlp_stats

        return stats


# 导出
__all__ = ["EmotionalState", "XiaonuoEnhancedAgent"]
