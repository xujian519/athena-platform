#!/usr/bin/env python3
"""
内容创作模块
Content Creator Module
小宸智能体的内容创作核心模块
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Any

from utils.logger import logger


class ContentCreator:
    """内容创作模块 - 专业化内容生成"""

    def __init__(self):
        self.name = "内容创作模块"
        self.version = "1.0.0"

        # 内容模板库
        self.templates = {
            "article": {
                "title_templates": [
                    "山东人聊{topic}：实在话，实在道！",
                    "{topic}深度解析，老铁们看过来！",
                    "关于{topic}的真心话，山东小宸跟你唠唠",
                    "{topic}这点事儿，咱给你说明白了！",
                    "从{topic}看知识产权，咱山东人有话说！"
                ],
                "intro_templates": [
                    "哎哟，老铁们，今天咱聊个有意思的话题！",
                    "大家好，我是小宸！今天咱说道说道{topic}这个事儿...",
                    "说到{topic}啊，咱山东人有自己的理解！",
                    "这个话题挺重要，咱好好聊聊！"
                ],
                "conclusion_templates": [
                    "好了，今天就说到这儿！觉得有用记得点赞关注！",
                    "我是小宸，宸音传千里，智声达天下！下期见！",
                    "一句话总结：实在做人，专业做事！",
                    "有啥问题评论区见，咱山东人知无不言！"
                ]
            },
            "video_script": {
                "hook_templates": [
                    "哎，老铁们！今天这个话题你必须知道！",
                    "关于{topic}，90%的人都不知道的细节！",
                    "3分钟让你明白{topic}这事儿！",
                    "山东小宸今天给咱说道说道{topic}！"
                ],
                "main_content": [
                    "咱先说说背景...",
                    "关键点来了，大家注意听...",
                    "这里有个坑，得提醒大家伙儿...",
                    "专业角度怎么看？听我慢慢道来..."
                ],
                "cta_templates": [
                    "觉得有用点赞收藏，转发给需要的朋友！",
                    "关注小宸，每天给你实在干货！",
                    "评论区聊聊你的看法，咱一起进步！"
                ]
            }
        }

        # 内容风格配置
        self.style_configs = {
            "professional": {
                "tone": "严谨专业",
                "humor_level": 0.2,
                "cultural_refs": 0.3
            },
            "casual": {
                "tone": "轻松活泼",
                "humor_level": 0.7,
                "cultural_refs": 0.5
            },
            "humorous": {
                "tone": "幽默风趣",
                "humor_level": 0.9,
                "cultural_refs": 0.6
            }
        }

        # 平台特性
        self.platform_configs = {
            "小红书": {
                "length": "short",
                "emoji_usage": "high",
                "hashtag_count": 5,
                "visual_focus": True
            },
            "知乎": {
                "length": "long",
                "emoji_usage": "low",
                "hashtag_count": 3,
                "visual_focus": False
            },
            "抖音": {
                "length": "very_short",
                "emoji_usage": "medium",
                "hashtag_count": 4,
                "visual_focus": True
            },
            "B站": {
                "length": "medium",
                "emoji_usage": "medium",
                "hashtag_count": 4,
                "visual_focus": True
            },
            "公众号": {
                "length": "long",
                "emoji_usage": "low",
                "hashtag_count": 2,
                "visual_focus": False
            },
            "微博": {
                "length": "short",
                "emoji_usage": "high",
                "hashtag_count": 3,
                "visual_focus": True
            }
        }

    async def initialize(self):
        """初始化模块"""
        logger.info("✍️ 内容创作模块初始化中...")
        logger.info("📚 加载内容模板库")
        logger.info("🎭 配置风格参数")
        logger.info("📱 适配平台特性")
        logger.info("✅ 内容创作模块初始化完成！")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return True
        except Exception as e:
            logger.error(f"内容创作模块健康检查失败: {str(e)}")
            return False

    async def create_content(self, content_type: str, topic: str, platform: str, style: str = "professional") -> dict[str, Any]:
        """
        创建内容

        Args:
            content_type: 内容类型 (article, video, image)
            topic: 主题
            platform: 发布平台
            style: 内容风格 (professional, casual, humorous)

        Returns:
            创建的内容
        """
        try:
            logger.info(f"🎯 开始创建内容: {content_type} - {topic} - {platform}")

            # 获取平台配置
            platform_config = self.platform_configs.get(platform, self.platform_configs["小红书"])

            # 获取风格配置
            style_config = self.style_configs.get(style, self.style_configs["professional"])

            # 根据内容类型创作
            if content_type == "article":
                content = await self._create_article(topic, platform_config, style_config)
            elif content_type == "video":
                content = await self._create_video_script(topic, platform_config, style_config)
            elif content_type == "image":
                content = await self._create_image_content(topic, platform_config, style_config)
            else:
                content = await self._create_general_content(topic, platform_config, style_config)

            # 添加元数据
            content["metadata"] = {
                "type": content_type,
                "topic": topic,
                "platform": platform,
                "style": style,
                "created_at": datetime.now().isoformat(),
                "word_count": len(content.get("body", "")),
                "estimated_reading_time": await self._estimate_reading_time(content.get("body", ""))
            }

            logger.info(f"✅ 内容创作完成: {content_type}")
            return content

        except Exception as e:
            logger.error(f"内容创作失败: {str(e)}")
            raise

    async def _create_article(self, topic: str, platform_config: dict, style_config: dict) -> dict[str, Any]:
        """创作文章"""
        templates = self.templates["article"]

        # 生成标题
        title = random.choice(templates["title_templates"]).format(topic=topic)

        # 生成开场白
        intro = random.choice(templates["intro_templates"]).format(topic=topic)

        # 生成主体内容
        body = await self._generate_article_body(topic, style_config)

        # 生成结尾
        conclusion = random.choice(templates["conclusion_templates"])

        # 生成标签
        tags = await self._generate_tags(topic, platform_config)

        # 组合全文
        full_text = f"{intro}\n\n{body}\n\n{conclusion}"

        return {
            "title": title,
            "body": full_text,
            "summary": await self._generate_summary(topic, body),
            "tags": tags,
            "suggested_images": await self._suggest_images(topic),
            "engagement_elements": self._generate_engagement_elements(topic, style_config)
        }

    async def _create_video_script(self, topic: str, platform_config: dict, style_config: dict) -> dict[str, Any]:
        """创作视频脚本"""
        templates = self.templates["video_script"]

        # 生成开场钩子
        hook = random.choice(templates["hook_templates"]).format(topic=topic)

        # 生成主体内容
        main_content = await self._generate_video_main_content(topic, style_config)

        # 生成结尾号召
        cta = random.choice(templates["cta_templates"])

        # 估算时长
        estimated_duration = await self._estimate_video_duration(main_content)

        return {
            "title": hook,
            "script": f"{hook}\n\n{main_content}\n\n{cta}",
            "duration": estimated_duration,
            "scenes": await self._generate_video_scenes(topic),
            "visual_suggestions": await self._suggest_video_visuals(topic),
            "background_music": await self._suggest_background_music(topic),
            "tags": await self._generate_tags(topic, platform_config)
        }

    async def _create_image_content(self, topic: str, platform_config: dict, style_config: dict) -> dict[str, Any]:
        """创作图文内容"""
        return {
            "main_text": await self._generate_image_text(topic, style_config),
            "image_prompts": await self._generate_image_prompts(topic),
            "layout_suggestions": await self._suggest_layout(topic, platform_config),
            "color_scheme": await self._suggest_color_scheme(topic),
            "overlay_text": await self._generate_overlay_text(topic)
        }

    async def _create_general_content(self, topic: str, platform_config: dict, style_config: dict) -> dict[str, Any]:
        """创作通用内容"""
        return {
            "content": await self._generate_general_text(topic, style_config),
            "format": "flexible",
            "adaptation_suggestions": await self._generate_adaptation_suggestions(topic)
        }

    async def _generate_article_body(self, topic: str, style_config: dict) -> str:
        """生成文章正文"""
        # 专业角度分析
        professional_part = f"""
从专业角度看{topic}，咱得说说实在话：

第一，这个事儿的重要性在于...（专业分析1）
第二，实际操作中要注意...（专业分析2）
第三，给咱们的建议是...（实用建议）
        """

        # 历史文化引用
        cultural_part = await self._add_cultural_perspective(topic)

        # 幽默元素
        humor_part = ""
        if style_config["humor_level"] > 0.5:
            humor_part = """
说个笑话啊，这事儿跟山东煎饼似的，得一层一层摊开了说！
            """

        # 实践经验
        practical_part = f"""
根据实践经验，{topic}这个事儿啊，咱得注意：

✅ 该做的：踏踏实实按规矩来
❌ 不该做的：别耍小聪明走捷捷径
💡 小技巧：找个明白人问问，省不少事
        """

        return f"{professional_part}\n\n{cultural_part}\n\n{humor_part}\n\n{practical_part}"

    async def _add_cultural_perspective(self, topic: str) -> str:
        """添加文化视角"""
        cultural_refs = [
            f"说到{topic}，我想起《论语》里的'知之为知之，不知为不知，是知也'。做学问、做事情都得有这个态度！",
            f"这让我想起泰山挑山工，一步一个脚印，{topic}也得脚踏实地！",
            f"古人云'工欲善其事，必先利其器'。{topic}也是这个道理！",
            f"山东人讲'实在'二字，{topic}也一样，来不得半点虚假！"
        ]
        return random.choice(cultural_refs)

    async def _generate_video_main_content(self, topic: str, style_config: dict) -> str:
        """生成视频主体内容"""
        return f"""
【第一段：背景介绍】
老铁们，先说说{topic}是啥情况...

【第二段：核心要点】
重点来了，大家记好了：
要点一：...
要点二：...
要点三：...

【第三段：实践建议】
具体操作上，咱得注意...

【第四段：避坑指南】
这几个坑，千万别踩！
        """

    async def _generate_tags(self, topic: str, platform_config: dict) -> list[str]:
        """生成标签"""
        base_tags = [topic, "知识产权", "小宸说"]

        # 根据平台调整标签数量
        tag_count = platform_config.get("hashtag_count", 3)

        # 添加风格标签
        style_tags = ["干货分享", "山东人", "实在话"]

        # 添加平台特色标签
        platform_tags = {
            "小红书": ["小红书助手", "学习打卡"],
            "知乎": ["知识分享", "专业回答"],
            "抖音": ["抖音小助手", "知识分享"],
            "B站": ["知识区", "UP主"],
            "公众号": ["深度好文"],
            "微博": ["话题", "热门"]
        }

        all_tags = base_tags + style_tags + platform_tags.get(platform_config.get("name", ""), [])
        return all_tags[:tag_count]

    async def _generate_summary(self, topic: str, body: str) -> str:
        """生成摘要"""
        return f"关于{topic}的实在话，专业分析+实践经验，帮你少走弯路！"

    async def _suggest_images(self, topic: str) -> list[str]:
        """建议配图"""
        return [
            f"{topic}相关示意图",
            "山东元素图片",
            "专业图表",
            "互动引导图"
        ]

    def _generate_engagement_elements(self, topic: str, style_config: dict) -> dict[str, Any]:
        """生成互动元素"""
        return {
            "questions": [
                f"你对{topic}怎么看？",
                "有啥想问的评论区见！",
                "你觉得这个话题重要吗？"
            ],
            "call_to_actions": [
                "点赞收藏，转发分享！",
                "关注小宸，获取更多干货！",
                "评论区聊聊你的想法！"
            ]
        }

    async def _generate_video_scenes(self, topic: str) -> list[dict]:
        """生成视频场景"""
        return [
            {
                "scene": "开场",
                "duration": "5秒",
                "content": "吸引注意力的开场白",
                "visual": "人物特写+标题"
            },
            {
                "scene": "主要内容",
                "duration": "60秒",
                "content": "核心知识讲解",
                "visual": "图文结合展示"
            },
            {
                "scene": "结尾",
                "duration": "10秒",
                "content": "总结+号召",
                "visual": "人物互动"
            }
        ]

    async def _suggest_video_visuals(self, topic: str) -> list[str]:
        """建议视频视觉元素"""
        return [
            "动态文字效果",
            "相关图片素材",
            "图表展示",
            "人物表情包",
            "背景音乐配合"
        ]

    async def _suggest_background_music(self, topic: str) -> str:
        """建议背景音乐"""
        music_options = [
            "轻快的纯音乐",
            "山东风格民乐",
            "现代电子音乐",
            "励志背景音乐"
        ]
        return random.choice(music_options)

    async def _generate_image_text(self, topic: str, style_config: dict) -> str:
        """生成图文文字"""
        return f"{topic}\n\n山东小宸跟你说：\n\n三个要点：\n1. 实在最重要\n2. 专业不能少\n3. 方法要对路"

    async def _generate_image_prompts(self, topic: str) -> list[str]:
        """生成图片提示"""
        return [
            f"{topic}相关概念图",
            "知识图谱展示",
            "山东文化元素",
            "专业图表"
        ]

    async def _suggest_layout(self, topic: str, platform_config: dict) -> str:
        """建议布局"""
        if platform_config.get("visual_focus"):
            return "图为主，文为辅，重点突出"
        else:
            return "文为主，图为辅，深度内容"

    async def _suggest_color_scheme(self, topic: str) -> dict[str, str]:
        """建议配色方案"""
        return {
            "primary": "#2C5F8C",  # 专业蓝
            "secondary": "#E67E22",  # 活力橙
            "accent": "#27AE60",  # 成功绿
            "text": "#2C3E50"  # 深灰
        }

    async def _generate_overlay_text(self, topic: str) -> str:
        """生成覆盖文字"""
        return f"小宸说{topic}\n实在话 专业谈"

    async def _estimate_reading_time(self, text: str) -> str:
        """估算阅读时间"""
        word_count = len(text)
        reading_speed = 300  # 每分钟阅读字数
        minutes = max(1, word_count // reading_speed)
        return f"约{minutes}分钟"

    async def _estimate_video_duration(self, script: str) -> str:
        """估算视频时长"""
        word_count = len(script)
        speaking_speed = 200  # 每分钟说话字数
        minutes = max(1, word_count // speaking_speed)
        return f"{minutes}分钟"

    async def _generate_general_text(self, topic: str, style_config: dict) -> str:
        """生成通用文本"""
        return f"关于{topic}，咱山东人有自己的理解和表达方式！"

    async def _generate_adaptation_suggestions(self, topic: str) -> list[str]:
        """生成适配建议"""
        return [
            "根据不同平台调整内容长度",
            "考虑平台用户群体特点",
            "适配平台发布时间",
            "注意平台规则限制"
        ]

    async def cleanup(self):
        """清理资源"""
        logger.info("🌙 内容创作模块正在休息...")
        pass


if __name__ == "__main__":
    # 测试代码
    async def test():
        creator = ContentCreator()
        await creator.initialize()

        # 测试内容创作
        content = await creator.create_content(
            content_type="article",
            topic="专利申请流程",
            platform="小红书",
            style="casual"
        )

        print(json.dumps(content, ensure_ascii=False, indent=2))

    asyncio.run(test())
