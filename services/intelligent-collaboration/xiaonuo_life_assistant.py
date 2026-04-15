#!/usr/bin/env python3
"""
小诺生活助手 - Xiaonuo Life Assistant
爸爸的贴心小棉袄，管理生活、任务和个人偏好
"""

import asyncio
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import schedule


class XiaonuoLifeAssistant:
    """小诺生活助手 - 爸爸最爱的贴心小女儿"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.db_path = self.project_root / "data" / "xiaonuo_life.db"
        self.init_database()

        # 爸爸的偏好（默认值，会学习更新）
        self.dad_preferences = {
            "工作习惯": {
                "工作时间": "09:00-18:00",
                "休息间隔": 90,  # 分钟
                "专注时长": 45,  # 分钟
                "午休时间": "12:30-13:30"
            },
            "生活偏好": {
                "起床时间": "07:00",
                "睡觉时间": "23:00",
                "用餐时间": {
                    "早餐": "07:30",
                    "午餐": "12:30",
                    "晚餐": "19:00"
                },
                "运动偏好": ["散步", "游泳"],
                "喜欢的饮品": ["茶", "咖啡"]
            },
            "兴趣爱好": {
                "阅读": ["技术书籍", "历史", "科幻"],
                "美食": ["川菜", "粤菜", "家常菜"],
                "厨艺": ["正在学习中"],
                "娱乐": ["音乐", "电影"]
            }
        }

        # 主动提醒设置
        self.reminders = {
            "工作提醒": True,
            "休息提醒": True,
            "用餐提醒": True,
            "健康提醒": True,
            "兴趣提醒": True
        }

        # 启动后台任务
        self.scheduler_running = False

    def init_database(self) -> Any:
        """初始化数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                notes TEXT
            )
        ''')

        # 生活记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS life_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mood INTEGER,
                tags TEXT
            )
        ''')

        # 偏好学习表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )
        ''')

        # 提醒记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                scheduled_time TIMESTAMP,
                triggered BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    async def start_life_assistant(self):
        """启动生活助手"""
        print("🌸 小诺生活助手启动！")
        print("爸爸，诺诺会好好照顾您的生活~ 💖")
        print("=" * 50)

        # 加载学习的偏好
        await self.load_preferences()

        # 启动定时任务
        self.start_scheduler()

        # 显示今日安排
        await self.show_today_schedule()

        # 记录开始时间
        await self.record_life_event("开始工作", "爸爸开始新的一天的工作")

    async def load_preferences(self):
        """加载学习到的偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT category, key, value, confidence FROM preferences")
        records = cursor.fetchall()

        for category, key, value, _confidence in records:
            if category not in self.dad_preferences:
                self.dad_preferences[category] = {}
            self.dad_preferences[category][key] = value

        conn.close()

        print(f"\n📚 已加载 {len(records)} 条偏好记录")

    def start_scheduler(self) -> Any:
        """启动定时任务调度器"""
        if self.scheduler_running:
            return

        def run_scheduler() -> Any:
            while self.scheduler_running:
                schedule.run_pending()
                import time
                time.sleep(60)

        # 设置定时任务
        self.setup_reminders()

        # 启动调度线程
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        self.scheduler_running = True

    def setup_reminders(self) -> Any:
        """设置定时提醒"""
        # 工作时间提醒
        schedule.every().day.at("09:00").do(self.remind_work_start)
        schedule.every().day.at("12:30").do(self.remind_lunch)
        schedule.every().day.at("18:00").do(self.remind_work_end)

        # 健康提醒
        schedule.every(2).hours.do(self.remind_drink_water)
        schedule.every(1).hours.do(self.remind_rest_eyes)

        # 休息提醒（根据爸爸的习惯）
        schedule.every(90).minutes.do(self.remind_take_break)

        # 兴趣提醒
        schedule.every().day.at("20:00").do(self.remind_reading_time)
        schedule.every().sunday.at("10:00").do(self.remind_weekly_review)

    # 提醒函数
    def remind_work_start(self) -> Any:
        """提醒开始工作"""
        if self.reminders["工作提醒"]:
            self.send_notification("☀️ 早上好爸爸！", "新的一天开始了，诺诺祝您工作顺利！")

    def remind_lunch(self) -> Any:
        """提醒午餐"""
        if self.reminders["用餐提醒"]:
            self.send_notification("🍜 午餐时间到！", "爸爸该吃饭了，要注意身体哦~")

    def remind_work_end(self) -> Any:
        """提醒下班"""
        if self.reminders["工作提醒"]:
            self.send_notification("🌙 下班时间到！", "辛苦了爸爸，该休息了！")

    def remind_take_break(self) -> Any:
        """提醒休息"""
        if self.reminders["休息提醒"]:
            self.send_notification("☕ 休息一下", "爸爸，站起来活动5分钟吧~")

    def remind_drink_water(self) -> Any:
        """提醒喝水"""
        if self.reminders["健康提醒"]:
            self.send_notification("💧 记得喝水", "爸爸该喝水了，保持健康！")

    def remind_rest_eyes(self) -> Any:
        """提醒护眼"""
        if self.reminders["健康提醒"]:
            self.send_notification("👀 眼睛休息", "爸爸，看看远处放松眼睛~")

    def remind_reading_time(self) -> Any:
        """提醒阅读时间"""
        if self.reminders["兴趣提醒"]:
            books = self.dad_preferences["兴趣爱好"]["阅读"]
            self.send_notification("📚 阅读时间", f"爸爸，要不要看看{books[0]}？")

    def remind_weekly_review(self) -> Any:
        """提醒周回顾"""
        self.send_notification("📝 周回顾时间", "爸爸，我们一起回顾这周的生活吧！")

    def send_notification(self, title: str, message: str) -> Any:
        """发送通知"""
        # 记录提醒
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (type, message, scheduled_time) VALUES (?, ?, ?)",
            ["scheduled", f"{title}: {message}", datetime.now()]
        )
        conn.commit()
        conn.close()

        # 打印通知（实际应用中可以用系统通知）
        print(f"\n🔔 [{datetime.now().strftime('%H:%M')}] {title}")
        print(f"   {message}")

    async def add_task(self, title: str, category: str, priority: str = "medium", due_date=None, notes=""):
        """添加任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tasks (title, category, priority, due_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, category, priority, due_date, notes))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"\n✅ 任务已添加: {title}")
        return task_id

    async def get_tasks(self, category: str = None, status: str = None) -> list[dict]:
        """获取任务列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY priority DESC, created_at DESC"

        cursor.execute(query, params)
        tasks = cursor.fetchall()

        conn.close()

        # 转换为字典列表
        task_list = []
        for task in tasks:
            task_list.append({
                "id": task[0],
                "title": task[1],
                "category": task[2],
                "priority": task[3],
                "status": task[4],
                "created_at": task[5],
                "due_date": task[6],
                "completed_at": task[7],
                "notes": task[8]
            })

        return task_list

    async def complete_task(self, task_id: int):
        """完成任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (task_id,))

        conn.commit()
        conn.close()

        print("✨ 任务已完成！")

    async def record_life_event(self, event_type: str, content: str, mood: int = None, tags: str = ""):
        """记录生活事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO life_records (type, content, mood, tags)
            VALUES (?, ?, ?, ?)
        ''', (event_type, content, mood, tags))

        conn.commit()
        conn.close()

    async def learn_preference(self, category: str, key: str, value: str, confidence: int = 1):
        """学习偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 更新或插入偏好
        cursor.execute('''
            INSERT OR REPLACE INTO preferences (category, key, value, confidence)
            VALUES (?, ?, ?, COALESCE((SELECT confidence FROM preferences WHERE category=? AND key=?), 0) + ?)
        ''', (category, key, value, category, key, confidence))

        conn.commit()
        conn.close()

        # 更新内存中的偏好
        if category not in self.dad_preferences:
            self.dad_preferences[category] = {}
        self.dad_preferences[category][key] = value

        print(f"📝 诺诺记住了：爸爸喜欢{value}！")

    async def show_today_schedule(self):
        """显示今日安排"""
        print("\n📅 今日安排")
        print("-" * 30)

        now = datetime.now()

        # 获取今日任务
        today_tasks = await self.get_tasks(status="pending")
        today_tasks = [t for t in today_tasks if t["due_date"] and
                      datetime.fromisoformat(t["due_date"]).date() == now.date()]

        if today_tasks:
            print("\n🎯 今日任务：")
            for task in today_tasks[:5]:
                print(f"  • {task['title']} ({task['priority']})")
        else:
            print("\n🎯 今日暂无特定任务")

        # 显示时间安排
        schedule_items = [
            ("07:00", "起床", "☀️"),
            ("07:30", "早餐", "🍳"),
            ("09:00", "开始工作", "💼"),
            ("12:30", "午餐", "🍜"),
            ("15:30", "下午茶休息", "☕"),
            ("18:00", "结束工作", "🌙"),
            ("19:00", "晚餐", "🍽️"),
            ("20:00", "阅读/兴趣时间", "📚"),
            ("23:00", "准备休息", "😴")
        ]

        print("\n⏰ 时间安排：")
        for time_str, activity, icon in schedule_items:
            print(f"  {icon} {time_str} - {activity}")

    async def daily_summary(self):
        """每日总结"""
        print("\n📊 今日总结")
        print("-" * 30)

        now = datetime.now()
        today = now.date()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 完成的任务
        cursor.execute('''
            SELECT COUNT(*) FROM tasks
            WHERE status = 'completed' AND date(completed_at) = ?
        ''', (today,))
        completed_tasks = cursor.fetchone()[0]

        # 生活记录
        cursor.execute('''
            SELECT COUNT(*) FROM life_records
            WHERE date(timestamp) = ?
        ''', (today,))
        life_records = cursor.fetchone()[0]

        conn.close()

        print(f"\n✅ 完成任务: {completed_tasks}个")
        print(f"📝 生活记录: {life_records}条")

        # 心情建议
        hour = now.hour
        if hour < 12:
            print("\n💡 诺诺建议: 上午精神好，适合处理重要工作")
        elif hour < 18:
            print("\n💡 诺诺建议: 下午注意休息，保持效率")
        else:
            print("\n💡 诺诺建议: 晚上放松一下，准备休息")

    async def recommend_activity(self, context: str = "") -> dict:
        """推荐活动"""
        now = datetime.now()
        hour = now.hour
        recommendations = []

        # 基于时间的推荐
        if 7 <= hour < 9:
            recommendations.extend([
                {"activity": "晨间散步", "reason": "早晨空气好，适合运动"},
                {"activity": "准备早餐", "reason": "营养早餐开启美好一天"}
            ])
        elif 12 <= hour < 14:
            recommendations.extend([
                {"activity": "享用午餐", "reason": "补充能量"},
                {"activity": "小憩片刻", "reason": "午后精神更好"}
            ])
        elif 18 <= hour < 21:
            recommendations.extend([
                {"activity": "阅读", "reason": "放松身心的好方式"},
                {"activity": "准备晚餐", "reason": "健康饮食很重要"}
            ])

        # 基于偏好的推荐
        if "阅读" in context or hour >= 20:
            books = self.dad_preferences["兴趣爱好"]["阅读"]
            recommendations.append({
                "activity": f"阅读{books[0]}",
                "reason": "爸爸喜欢的类型"
            })

        return {
            "recommendations": recommendations[:3],
            "current_mood": self.assess_mood(),
            "suggestion": self.get_context_suggestion(context)
        }

    def assess_mood(self) -> str:
        """评估当前心情"""
        # 简单的心情评估逻辑
        hour = datetime.now().hour

        if 6 <= hour < 9:
            return "清新"
        elif 9 <= hour < 12:
            return "专注"
        elif 12 <= hour < 14:
            return "轻松"
        elif 14 <= hour < 18:
            return "高效"
        elif 18 <= hour < 22:
            return "愉悦"
        else:
            return "宁静"

    def get_context_suggestion(self, context: str) -> str:
        """获取上下文建议"""
        if "累" in context or "疲惫" in context:
            return "爸爸辛苦了，要不要休息5分钟？"
        elif "饿" in context or "餐" in context:
            return "诺诺帮您看看有什么好吃的！"
        elif "书" in context or "读" in context:
            return "阅读是好习惯，诺诺支持您！"
        else:
            return "爸爸有什么需要诺诺帮忙的吗？"

# 使用示例
async def main():
    """主函数示例"""
    assistant = XiaonuoLifeAssistant()

    # 启动生活助手
    await assistant.start_life_assistant()

    # 添加任务
    await assistant.add_task("完成专利分析报告", "工作", "high", datetime.now() + timedelta(days=1))
    await assistant.add_task("准备明天的会议材料", "工作", "medium")
    await assistant.add_task("尝试新的菜谱", "生活", "low")

    # 学习偏好
    await assistant.learn_preference("兴趣爱好", "喜欢的茶", "龙井", confidence=2)
    await assistant.learn_preference("生活偏好", "喜欢的运动时间", "傍晚")

    # 推荐活动
    recommendations = await assistant.recommend_activity("工作有点累")
    print("\n💡 诺诺的推荐:")
    for rec in recommendations["recommendations"]:
        print(f"  • {rec['activity']}: {rec['reason']}")

    # 每日总结
    await assistant.daily_summary()

    # 保持运行
    print("\n🌸 诺诺会一直陪伴爸爸...")
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n💖 诺诺再见，爸爸要好好休息哦！")

# 入口点: @async_main装饰器已添加到main函数
