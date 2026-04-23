#!/usr/bin/env python3
"""
平台管理器
Platform Manager
管理各个自媒体平台的发布和运营
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Any

from utils.logger import logger


class PlatformManager:
    """平台管理器 - 多平台发布管理"""

    def __init__(self):
        self.name = "平台管理器"
        self.version = "1.0.0"

        # 平台配置
        self.platforms = {
            "小红书": {
                "api_endpoint": "https://api.xiaohongshu.com",
                "content_types": ["image", "video", "article"],
                "max_text_length": 1000,
                "image_limit": 9,
                "video_limit": 1,
                "hashtag_limit": 5,
                "status": "configured"
            },
            "知乎": {
                "api_endpoint": "https://api.zhihu.com",
                "content_types": ["article", "video", "answer"],
                "max_text_length": 10000,
                "image_limit": 20,
                "video_limit": 1,
                "hashtag_limit": 3,
                "status": "configured"
            },
            "抖音": {
                "api_endpoint": "https://open.douyin.com",
                "content_types": ["video", "image"],
                "max_text_length": 500,
                "image_limit": 9,
                "video_limit": 1,
                "hashtag_limit": 4,
                "status": "configured"
            },
            "B站": {
                "api_endpoint": "https://api.bilibili.com",
                "content_types": ["video", "article"],
                "max_text_length": 2000,
                "image_limit": 20,
                "video_limit": 1,
                "hashtag_limit": 4,
                "status": "configured"
            },
            "公众号": {
                "api_endpoint": "https://api.weixin.qq.com",
                "content_types": ["article"],
                "max_text_length": 50000,
                "image_limit": 50,
                "video_limit": 10,
                "hashtag_limit": 2,
                "status": "configured"
            },
            "微博": {
                "api_endpoint": "https://api.weibo.com",
                "content_types": ["text", "image", "video"],
                "max_text_length": 140,
                "image_limit": 9,
                "video_limit": 1,
                "hashtag_limit": 3,
                "status": "configured"
            }
        }

        # 发布记录
        self.publish_history = []

        # 平台认证状态
        self.auth_status = dict.fromkeys(self.platforms, False)

    async def initialize(self):
        """初始化平台管理器"""
        logger.info("📱 平台管理器初始化中...")

        # 检查平台连接
        await self._check_platform_connections()

        # 加载发布历史
        await self._load_publish_history()

        logger.info("✅ 平台管理器初始化完成！")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查所有平台连接状态
            connected_platforms = sum(1 for status in self.auth_status.values() if status)
            len(self.auth_status)

            # 至少需要一个平台连接正常
            return connected_platforms > 0
        except Exception as e:
            logger.error(f"平台管理器健康检查失败: {str(e)}")
            return False

    async def _check_platform_connections(self):
        """检查平台连接"""
        logger.info("🔍 检查各平台连接状态...")

        for platform in self.platforms:
            # 模拟连接检查（实际应该调用真实API）
            try:
                # 这里应该是真实的平台API检查
                # await self._check_real_platform_connection(platform)

                # 暂时设置为已连接（演示用）
                self.auth_status[platform] = True
                logger.info(f"✅ {platform}连接正常")

            except Exception as e:
                logger.warning(f"⚠️ {platform}连接失败: {str(e)}")
                self.auth_status[platform] = False

    async def _load_publish_history(self):
        """加载发布历史"""
        # 这里应该从数据库加载
        # 暂时使用空列表
        self.publish_history = []

    async def publish_to_platforms(self, content: dict, platforms: list[str], schedule_time: str | None = None) -> dict[str, Any]:
        """
        发布内容到指定平台

        Args:
            content: 要发布的内容
            platforms: 目标平台列表
            schedule_time: 定时发布时间（可选）

        Returns:
            发布结果
        """
        results = {}

        for platform in platforms:
            try:
                result = await self._publish_to_single_platform(platform, content, schedule_time)
                results[platform] = result

                # 记录发布历史
                self._record_publish(platform, content, result)

            except Exception as e:
                logger.error(f"发布到{platform}失败: {str(e)}")
                results[platform] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        return results

    async def _publish_to_single_platform(self, platform: str, content: dict, schedule_time: str | None = None) -> dict[str, Any]:
        """发布到单个平台"""
        if platform not in self.platforms:
            raise ValueError(f"不支持的平台: {platform}")

        if not self.auth_status[platform]:
            raise ConnectionError(f"{platform}未连接或未授权")

        # 适配平台格式
        await self._adapt_content_for_platform(content, platform)

        # 模拟发布（实际应该调用真实API）
        logger.info(f"📤 正在发布到{platform}...")

        # 模拟发布延迟
        await asyncio.sleep(0.5)

        # 模拟发布结果
        publish_result = {
            "success": True,
            "platform": platform,
            "content_id": f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "url": f"https://example.com/{platform}/posts/{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "publish_time": schedule_time or datetime.now().isoformat(),
            "stats": {
                "views": 0,
                "likes": 0,
                "shares": 0,
                "comments": 0
            },
            "message": f"成功发布到{platform}"
        }

        logger.info(f"✅ {platform}发布成功")
        return publish_result

    async def _adapt_content_for_platform(self, content: dict, platform: str) -> dict[str, Any]:
        """适配内容到指定平台"""
        platform_config = self.platforms[platform]
        adapted = content.copy()

        # 调整文本长度
        if "body" in adapted and len(adapted["body"]) > platform_config["max_text_length"]:
            adapted["body"] = adapted["body"][:platform_config["max_text_length"] + "..."

        # 调整标签数量
        if "tags" in adapted and len(adapted["tags"]) > platform_config["hashtag_limit"]:
            adapted["tags"] = adapted["tags"][:platform_config["hashtag_limit"]

        # 平台特定适配
        if platform == "小红书":
            adapted = await self._adapt_for_xiaohongshu(adapted)
        elif platform == "知乎":
            adapted = await self._adapt_for_zhihu(adapted)
        elif platform == "抖音":
            adapted = await self._adapt_for_douyin(adapted)
        elif platform == "B站":
            adapted = await self._adapt_for_bilibili(adapted)
        elif platform == "公众号":
            adapted = await self._adapt_for_wechat(adapted)
        elif platform == "微博":
            adapted = await self._adapt_for_weibo(adapted)

        return adapted

    async def _adapt_for_xiaohongshu(self, content: dict) -> dict[str, Any]:
        """适配小红书"""
        adapted = content.copy()

        # 添加emoji
        if "title" in adapted:
            adapted["title"] = self._add_emoji_to_text(adapted["title"])

        # 添加话题标签
        if "tags" in adapted:
            adapted["tags"] = [f"#{tag}" for tag in adapted["tags"]

        # 添加引导语
        adapted["body"] = "大家好，我是小宸～\n\n" + adapted.get("body", "")

        return adapted

    async def _adapt_for_zhihu(self, content: dict) -> dict[str, Any]:
        """适配知乎"""
        adapted = content.copy()

        # 添加专业声明
        adapted["body"] = "（本文为小宸原创，转载请注明出处）\n\n" + adapted.get("body", "")

        # 添加参考链接
        adapted["body"] += "\n\n# 相关资源\n\n- [小宸的其他回答]\n- [知识产权学习资料]"

        return adapted

    async def _adapt_for_douyin(self, content: dict) -> dict[str, Any]:
        """适配抖音"""
        adapted = content.copy()

        # 简化标题
        if "title" in adapted:
            adapted["title"] = adapted["title"][:30] + "..." if len(adapted["title"]) > 30 else adapted["title"]

        # 添加音乐建议
        adapted["background_music"] = "轻松愉快的背景音乐"

        return adapted

    async def _adapt_for_bilibili(self, content: dict) -> dict[str, Any]:
        """适配B站"""
        adapted = content.copy()

        # 添加分区信息
        adapted["category"] = "知识"
        adapted["subcategory"] = "科普"

        # 添加互动提示
        adapted["body"] += "\n\n喜欢这个视频记得三连支持一下！关注小宸，获取更多知识产权知识！"

        return adapted

    async def _adapt_for_wechat(self, content: dict) -> dict[str, Any]:
        """适配公众号"""
        adapted = content.copy()

        # 添加封面图建议
        adapted["cover_image"] = "建议使用专业、清晰的封面图"

        # 添加摘要
        adapted["summary"] = "小宸为您讲解知识产权相关知识，用山东人的实在话，说专业的法律事。"

        return adapted

    async def _adapt_for_weibo(self, content: dict) -> dict[str, Any]:
        """适配微博"""
        adapted = content.copy()

        # 限制字数
        if "body" in adapted and len(adapted["body"]) > 140:
            adapted["body"] = adapted["body"][:130] + "...（详见长图）"

        # 添加话题
        if "tags" in adapted:
            adapted["tags"] = [f"#{tag}#" for tag in adapted["tags"]

        return adapted

    def _add_emoji_to_text(self, text: str) -> str:
        """添加emoji到文本"""
        emojis = ["✨", "🎯", "💡", "🔥", "📚", "💪", "👍", "🎉"]
        # 简单地在开头添加一个emoji
        return random.choice(emojis) + " " + text

    def _record_publish(self, platform: str, content: dict, result: dict) -> Any:
        """记录发布历史"""
        record = {
            "platform": platform,
            "content_id": result.get("content_id"),
            "publish_time": result.get("publish_time"),
            "success": result.get("success", False),
            "error": result.get("error"),
            "stats": result.get("stats", {})
        }

        self.publish_history.append(record)

        # 限制历史记录数量
        if len(self.publish_history) > 1000:
            self.publish_history = self.publish_history[-1000:]

    async def get_publish_stats(self, platform: str | None = None) -> dict[str, Any]:
        """获取发布统计"""
        # 过滤平台
        history = self.publish_history
        if platform:
            history = [record for record in history if record["platform"] == platform]

        # 计算统计数据
        total_published = len(history)
        successful_published = len([r for r in history if r["success"])

        # 统计各平台发布数量
        platform_stats = {}
        for record in history:
            platform = record["platform"]
            if platform not in platform_stats:
                platform_stats[platform] = {"total": 0, "success": 0}
            platform_stats[platform]["total"] += 1
            if record["success"]:
                platform_stats[platform]["success"] += 1

        return {
            "total_published": total_published,
            "successful_published": successful_published,
            "success_rate": successful_published / total_published if total_published > 0 else 0,
            "platform_stats": platform_stats,
            "recent_publishes": history[-10:]  # 最近10条
        }

    async def get_platform_status(self) -> dict[str, Any]:
        """获取平台状态"""
        return {
            "platforms": self.platforms,
            "auth_status": self.auth_status,
            "connected_count": sum(self.auth_status.values()),
            "total_count": len(self.platforms)
        }

    async def cleanup(self):
        """清理资源"""
        logger.info("🌙 平台管理器正在休息...")

        # 保存发布历史
        # await self._save_publish_history()

        pass


if __name__ == "__main__":
    # 测试代码
    async def test():
        manager = PlatformManager()
        await manager.initialize()

        # 测试发布
        content = {
            "title": "小宸测试内容",
            "body": "这是一条测试内容，测试多平台发布功能。",
            "tags": ["测试", "小宸", "自媒体"]
        }

        platforms = ["小红书", "知乎", "微博"]
        results = await manager.publish_to_platforms(content, platforms)

        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(test())
