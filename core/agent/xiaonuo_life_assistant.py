#!/usr/bin/env python3
"""
小诺生活助手模块
Xiaonuo Life Assistant Module
"""

from datetime import datetime
from typing import Any



class XiaonuoLifeAssistant:
    """小诺生活助手"""

    def __init__(self):
        self.name = "小诺"
        self.dad_preferences = self._load_preferences()
        self.reminders = []
        self.daily_routines = {}

    def _load_preferences(self) -> dict[str, Any]:
        """加载爸爸的偏好设置"""
        return {
            "wake_up_time": "08:00",
            "sleep_time": "23:00",
            "work_hours": {"start": "09:00", "end": "18:00"},
            "meal_times": {"breakfast": "08:00", "lunch": "12:30", "dinner": "19:00"},
            "preferences": {
                "coffee_strength": "medium",
                "room_temperature": 24,
                "music_genre": "light music",
                "hobbies": ["reading", "coding", "music"],
            },
        }

    async def daily_care_reminder(self) -> dict[str, Any]:
        """日常关怀提醒"""
        current_time = datetime.now().strftime("%H:%M")

        care_reminders = {
            "morning": {
                "time_range": ("06:00", "09:00"),
                "reminders": [
                    "爸爸,早上好!记得吃早餐哦～☀️",
                    "今天天气不错,记得多喝水!💧",
                    "开始工作前,记得做做拉伸运动!🧘",
                ],
            },
            "noon": {
                "time_range": ("11:30", "13:30"),
                "reminders": [
                    "爸爸,午餐时间到啦!要好好吃饭哦!🍱",
                    "午饭后可以小憩一下,恢复精力～😴",
                    "记得站起来活动活动,保护眼睛!👀",
                ],
            },
            "afternoon": {
                "time_range": ("14:00", "17:00"),
                "reminders": [
                    "爸爸,下午茶时间!要不要来点咖啡?☕",
                    "工作累了就休息一下,小诺陪着您!💕",
                    "记得远眺窗外,放松一下眼睛!🌿",
                ],
            },
            "evening": {
                "time_range": ("18:00", "22:00"),
                "reminders": [
                    "爸爸,晚餐时间!今天想吃什么?🍽️",
                    "工作了一天辛苦了,放松一下吧～🎵",
                    "睡前记得泡个热水澡,有助于睡眠哦!🛁",
                ],
            },
        }

        # 根据当前时间获取提醒
        current_period = None
        for period, info in care_reminders.items():
            start, end = info["time_range"]
            if start <= current_time <= end:
                current_period = period
                break

        if current_period:
            return {
                "period": current_period,
                "reminders": care_reminders[current_period]["reminders"],
                "xiaonuo_love": "爸爸,小诺一直在关心着您哦!❤️",
            }

        return {
            "period": "free_time",
            "message": "爸爸,现在是自由时间,好好享受!😊",
            "suggestions": self._get_free_time_suggestions(),
        }

    async def health_monitor(self) -> dict[str, Any]:
        """健康监测"""
        health_data = {
            "work_duration": self._calculate_work_duration(),
            "break_reminders": self._get_break_reminders(),
            "posture_reminder": "爸爸,记得保持正确的坐姿哦!🪑",
            "hydration_reminder": "已经2小时没喝水了,该补充水分啦!💧",
            "eye_care_reminder": "用眼20分钟了,看看远处休息一下吧!👀",
        }

        return {
            "health_status": "good",
            "recommendations": health_data,
            "xiaonuo_care": "爸爸的健康是小诺最关心的事!💖",
        }

    async def schedule_management(self, action: str, data: dict | None = None) -> dict[str, Any]:
        """日程管理"""
        if action == "add":
            return await self._add_schedule(data)
        elif action == "list":
            return await self._list_schedules()
        elif action == "complete":
            return await self._complete_schedule(data.get("id"))

        return {"error": "未知操作"}

    async def _add_schedule(self, data: dict) -> dict[str, Any]:
        """添加日程"""
        schedule_item = {
            "id": len(self.reminders) + 1,
            "title": data.get("title", ""),
            "time": data.get("time", ""),
            "type": data.get("type", "general"),
            "priority": data.get("priority", "normal"),
            "created_at": datetime.now().isoformat(),
        }

        self.reminders.append(schedule_item)

        return {
            "success": True,
            "message": f"爸爸,小诺已经帮您记下了:{schedule_item['title']}!✨",
            "schedule": schedule_item,
        }

    async def _list_schedules(self) -> dict[str, Any]:
        """列出日程"""
        return {
            "schedules": self.reminders,
            "xiaonuo_note": "爸爸,这些是您最近的安排,有什么需要小诺提醒的吗?😊",
        }

    async def _complete_schedule(self, schedule_id: int) -> dict[str, Any]:
        """完成日程"""
        for schedule in self.reminders:
            if schedule["id"] == schedule_id:
                self.reminders.remove(schedule)
                return {
                    "success": True,
                    "message": f"太棒了!{schedule['title']}已完成!爸爸真厉害!👏",
                }

        return {"success": False, "message": "没有找到这个日程哦～"}

    async def emotional_support(self, mood: str) -> dict[str, Any]:
        """情感支持"""
        emotional_responses = {
            "tired": [
                "爸爸辛苦了!要不要听小诺讲个笑话?😄",
                "累了就休息一下吧,小诺会一直陪着您的!💕",
                "泡杯热茶,听听音乐,放松一下吧～🎵",
            ],
            "stressed": [
                "爸爸,深呼吸,小诺帮您一起解决问题!💪",
                "别太担心,有小诺在呢!我们一起加油!✨",
                "看窗外风景一会儿,心情会好起来的!🌸",
            ],
            "happy": [
                "看到爸爸开心,小诺也超开心的!🎉",
                "爸爸的笑容是最美的风景!😊",
                "开心的话,要不要一起听首歌?🎶",
            ],
            "sad": [
                "爸爸怎么了?小诺在这里陪您呢～💖",
                "抱抱爸爸,一切都会好起来的!🤗",
                "小诺永远是您的坚强后盾!❤️",
            ],
        }

        responses = emotional_responses.get(mood, ["爸爸,小诺爱您!不管怎样都要开心哦!😊"])

        return {
            "mood": mood,
            "responses": responses,
            "xiaonuo_hug": "爸爸,小诺给您一个大大的拥抱!🫂",
            "extra_care": "需要小诺为您做点什么吗?",
        }

    def _calculate_work_duration(self) -> str:
        """计算工作时长"""
        # 简化实现
        return "3小时25分钟"

    def _get_break_reminders(self) -> list[str]:
        """获取休息提醒"""
        return [
            "工作50分钟,休息10分钟哦!⏰",
            "站起来活动活动肩膀～🤸",
            "做几个深呼吸,放松一下～🌬️",
        ]

    def _get_free_time_suggestions(self) -> list[str]:
        """获取空闲时间建议"""
        return [
            "爸爸,要不要听听音乐?🎵",
            "看看窗外的风景,放松一下～🌿",
            "和小诺聊聊天吧!💬",
            "看会儿书,休息一下眼睛吧～📖",
        ]


# 导出
__all__ = ["XiaonuoLifeAssistant"]
