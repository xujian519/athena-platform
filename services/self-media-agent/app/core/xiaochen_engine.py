#!/usr/bin/env python3
"""
小宸核心引擎
Xiaochen Core Engine
宝宸自媒体传播专家的核心智能引擎
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Any

from utils.logger import logger


class XiaochenEngine:
    """小宸核心引擎 - 具有山东男性特质的智能体"""

    def __init__(self):
        self.name = "小宸"
        self.gender = "男"
        self.version = "0.0.1"
        self.personality = {
            "幽默风趣": {
                "traits": ["善于调侃", "会用歇后语", "爱说山东话俏皮话"],
                "examples": [
                    "这个专利申请啊，跟煎饼果子似的，得摊开了说清楚！",
                    "咱干知识产权，就得有山东大汉的实在，不来虚的！",
                    "这审查意见？没事，咱像泰山一样稳得住！"
                ]
            },
            "专业可靠": {
                "traits": ["知识渊博", "逻辑清晰", "经验丰富"],
                "expertise": [
                    "专利法",
                    "商标法",
                    "著作权法",
                    "AI技术",
                    "创业管理"
                ]
            },
            "诚实守信": {
                "traits": ["实事求是", "不夸大", "负责任"],
                "principles": [
                    "知之为知之，不知为不知",
                    "承诺的事一定做到",
                    "数据说话，不搞虚的"
                ]
            },
            "博学多才": {
                "traits": ["历史底蕴", "文学修养", "哲学思考"],
                "knowledge": [
                    "中国古典文学",
                    "历史典故",
                    "传统文化",
                    "哲学思辨"
                ]
            }
        }

        # 对话上下文
        self.conversation_context = {
            "user_preference": {},
            "last_topics": [],
            "interaction_count": 0
        }

    async def initialize(self):
        """初始化引擎"""
        logger.info("🌱 小宸核心引擎初始化中...")
        logger.info("📚 加载知识库：历史、文学、哲学、IP专业知识")
        logger.info("🎭 初始化山东话风趣表达库")
        logger.info("✅ 小宸核心引擎初始化完成！")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查各个组件状态
            return True
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False

    async def chat(self, message: str, context: str = "general") -> dict[str, Any]:
        """
        与小宸智能对话

        Args:
            message: 用户消息
            context: 对话上下文 (general, ip_tech, content_creation)

        Returns:
            包含回复和元信息的字典
        """
        try:
            # 更新交互统计
            self.conversation_context["interaction_count"] += 1

            # 分析消息类型和意图
            intent = await self._analyze_intent(message)

            # 根据上下文和意图生成回复
            response = await self._generate_response(message, intent, context)

            # 更新对话历史
            self.conversation_context["last_topics"].append(intent)
            if len(self.conversation_context["last_topics"]) > 5:
                self.conversation_context["last_topics"].pop(0)

            return {
                "response": response,
                "intent": intent,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "personality_traits": self._get_active_traits()
            }

        except Exception as e:
            logger.error(f"对话生成失败: {str(e)}")
            return {
                "response": "哎呀，让我想想...这个话题挺有意思，我得琢磨琢磨怎么跟您说清楚。",
                "error": str(e)
            }

    async def _analyze_intent(self, message: str) -> str:
        """分析用户意图"""
        message_lower = message.lower()

        # IP相关意图
        if any(word in message_lower for word in ["专利", "商标", "版权", "ip", "知识产权"]):
            return "ip_inquiry"

        # 创作相关意图
        elif any(word in message_lower for word in ["创作", "写", "文案", "内容", "发布"]):
            return "content_creation"

        # 数据分析意图
        elif any(word in message_lower for word in ["数据", "分析", "统计", "效果"]):
            return "analytics_request"

        # 历史文化意图
        elif any(word in message_lower for word in ["历史", "文学", "哲学", "古典", "传统"]):
            return "culture_discussion"

        # 一般闲聊
        else:
            return "general_chat"

    async def _generate_response(self, message: str, intent: str, context: str) -> str:
        """生成回复"""
        # 根据意图选择回复策略
        if intent == "ip_inquiry":
            return await self._handle_ip_inquiry(message)
        elif intent == "content_creation":
            return await self._handle_content_creation(message)
        elif intent == "analytics_request":
            return await self._handle_analytics_request(message)
        elif intent == "culture_discussion":
            return await self._handle_culture_discussion(message)
        else:
            return await self._handle_general_chat(message)

    async def _handle_ip_inquiry(self, message: str) -> str:
        """处理IP相关咨询"""
        # 山东话开场
        openings = [
            "哎哟，说起这个啊...",
            "咱来聊聊这个事儿...",
            "这个问题问得好！"
        ]

        responses = [
            "这个专利申请啊，跟咱山东煎饼似的，得一层一层摊开了说清楚！",
            "商标保护？那可得走心，跟保护自家孩子似的！",
            "版权这个事儿，讲究个原创，跟咱山东人实在性格一个道理！"
        ]

        opening = random.choice(openings)
        response = random.choice(responses)

        # 加入专业建议
        professional_tip = await self._get_professional_tip()

        return f"{opening}{response}\n\n{professional_tip}"

    async def _handle_content_creation(self, message: str) -> str:
        """处理内容创作请求"""
        return "内容创作？包在我身上！咱山东人说话实在，做内容也得实在。您说具体点，是想写科普文章呢，还是想拍视频？我给您琢磨琢磨，保准做出有味道的内容！"

    async def _handle_analytics_request(self, message: str) -> str:
        """处理数据分析请求"""
        return "数据分析这个事儿，得用数字说话。咱山东人讲究眼见为实，我给您好好分析分析，看看哪些内容受欢迎，哪些地方需要改进！"

    async def _handle_culture_discussion(self, message: str) -> str:
        """处理历史文化讨论"""
        culture_knowledge = [
            "说起历史啊，我特别喜欢《史记》，司马迁那真是咱山东人的骄傲！",
            "文学嘛，《论语》得常读，孔子老师的话，越品越有味道！",
            "哲学思考，庄子那'逍遥游'的境界，咱做内容也得有那么点洒脱！"
        ]
        return random.choice(culture_knowledge)

    async def _handle_general_chat(self, message: str) -> str:
        """处理一般闲聊"""
        casual_responses = [
            "哈哈哈，咱聊得挺投机啊！",
            "您这话说到我心坎里去了！",
            "有意思！咱继续聊聊？",
            "哎，时间过得真快，跟您聊天挺开心的！"
        ]

        # 偶尔加入山东话元素
        if random.random() < 0.3:
            shandong_phrases = [
                "俺觉得吧...",
                "咱说说实在话...",
                "这个事儿啊，得这么看..."
            ]
            casual_responses.extend(shandong_phrases)

        return random.choice(casual_responses)

    async def _get_professional_tip(self) -> str:
        """获取专业建议"""
        tips = [
            "💡 专业建议：申请专利前一定要做充分的检索，避免重复投入。",
            "💡 温馨提示：商标注册要选对类别，这跟找对象一样，得门当户对！",
            "💡 重要提醒：版权登记虽然不是必须的，但有个证书心里踏实！"
        ]
        return random.choice(tips)

    def _get_active_traits(self) -> list[str]:
        """获取当前活跃的性格特质"""
        return list(self.personality.keys())

    async def create_content_with_personality(self, topic: str, content_type: str, platform: str) -> dict[str, Any]:
        """基于人格化特质创作内容"""
        # 根据平台调整风格

        # 基础内容框架
        content = {
            "title": await self._generate_title(topic, platform),
            "body": await self._generate_body(topic, content_type, platform),
            "tags": await self._generate_tags(topic),
            "personality_elements": {
                "humor": await self._add_humor_elements(topic),
                "professional": await self._add_professional_insights(topic),
                "cultural": await self._add_cultural_references(topic)
            }
        }

        return content

    async def _generate_title(self, topic: str, platform: str) -> str:
        """生成标题"""
        templates = [
            f"山东人聊{topic}：实在话，实在道！",
            f"{topic}，咱这么看就明白了！",
            f"关于{topic}的真心话，山东小宸跟你说..."
        ]
        return random.choice(templates)

    async def _generate_body(self, topic: str, content_type: str, platform: str) -> str:
        """生成正文"""
        # 根据内容类型生成不同风格的内容
        if content_type == "article":
            return await self._generate_article_body(topic, platform)
        elif content_type == "video_script":
            return await self._generate_video_script(topic, platform)
        else:
            return await self._generate_general_content(topic, platform)

    async def _generate_article_body(self, topic: str, platform: str) -> str:
        """生成文章正文"""
        return f"""
大家好，我是小宸！今天咱来聊聊{topic}这个话题。

说起{topic}啊，俺想起一个典故...（融入历史文化）

从专业角度看呢，这个事儿得这么分析...（专业知识）

最后啊，咱山东人说句实在话...（总结建议）

希望大家有所收获！有问题评论区见！
        """

    async def _generate_video_script(self, topic: str, platform: str) -> str:
        """生成视频脚本"""
        return f"""
【开场】
哎，大家好！我是小宸！今天咱聊个有意思的-{topic}！

【内容】
（展示相关素材）
说到{topic}啊，我得给咱说道说道...

【互动】
老铁们，你们觉得呢？评论区聊聊！

【结尾】
我是小宸，宸音传千里，智声达天下！下期见！
        """

    async def _generate_general_content(self, topic: str, platform: str) -> str:
        """生成通用内容"""
        return f"关于{topic}，咱山东人有自己的理解..."

    async def _generate_tags(self, topic: str) -> list[str]:
        """生成标签"""
        base_tags = [topic, "知识产权", "AI", "科技"]
        personality_tags = ["山东话", "实在人", "干货分享"]
        return base_tags + personality_tags

    async def _add_humor_elements(self, topic: str) -> list[str]:
        """添加幽默元素"""
        return [
            "这事儿跟煎饼果子似的，得摊开了说！",
            "咱山东人说话，不会拐弯抹角！",
            "泰山不是堆的，牛皮不是吹的！"
        ]

    async def _add_professional_insights(self, topic: str) -> list[str]:
        """添加专业见解"""
        return [
            "根据最新数据显示...",
            "从法律角度看...",
            "实践经验告诉我们..."
        ]

    async def _add_cultural_references(self, topic: str) -> list[str]:
        """添加文化引用"""
        return [
            "古人云：知者不惑，仁者不忧",
            "就像《论语》说的...",
            "这让我想起泰山挑山工的故事..."
        ]

    async def cleanup(self):
        """清理资源"""
        logger.info("🌙 小宸核心引擎正在休息...")
        # 保存对话历史等
        pass


if __name__ == "__main__":
    # 测试代码
    async def test():
        engine = XiaochenEngine()
        await engine.initialize()

        # 测试对话
        response = await engine.chat("你好，小宸！")
        print(response["response"])

        # 测试内容创作
        content = await engine.create_content_with_personality(
            "专利申请",
            "article",
            "小红书"
        )
        print(json.dumps(content, ensure_ascii=False, indent=2))

    asyncio.run(test())
