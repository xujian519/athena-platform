#!/usr/bin/env python3
"""
小诺生活助理系统
Xuenuo Life Assistant System - 负责爸爸的生活管理
"""

from pathlib import Path

from security_manager import PersonalSecurityManager
from xuenuo_recipe_assistant import answer_recipe_question


class XuenuoLifeAssistant:
    """小诺 - 爸爸的生活助理"""

    def __init__(self):
        self.security_manager = PersonalSecurityManager()
        self.storage_dir = Path("/Users/xujian/Athena工作平台/personal_secure_storage")

        # 生活助理功能模块
        self.functions = {
            "菜谱查询": self.query_recipe,
            "个人信息": self.query_personal_info,
            "备忘录": self.query_notes,
            "日程提醒": self.query_schedule
        }

    def query_recipe(self, question) -> None:
        """菜谱查询功能"""
        return answer_recipe_question(question)

    def query_personal_info(self, question) -> None:
        """查询个人信息（需要密码）"""
        return "🔒 个人信息查询需要密码验证，请使用 security_manager.py 访问"

    def query_notes(self, question) -> None:
        """查询备忘录"""
        # 从存储中搜索笔记
        results = self.search_in_storage(question, category="general")
        if results:
            return self.format_notes_results(results)
        return "没有找到相关的备忘录"

    def query_schedule(self, question) -> None:
        """查询日程提醒"""
        return "日程提醒功能正在开发中..."

    def search_in_storage(self, keyword, category=None) -> None:
        """在安全存储中搜索"""
        try:
            results = self.security_manager.get_secure_info(category=category, search_term=keyword)
            return results
        except Exception:
            return None

    def format_notes_results(self, results) -> None:
        """格式化搜索结果"""
        response = "📝 找到的备忘录：\n\n"
        for result in results[:5]:  # 只显示前5条
            if 'title' in result:
                response += f"📄 {result['title']}\n"
            if 'content' in result:
                response += f"   {result['content'][:100]}...\n"
            response += "\n"
        return response

    def process_request(self, request) -> None:
        """
        处理用户请求

        Args:
            request (str): 用户请求，如"虾滑紫菜汤怎么做？"

        Returns:
            str: 回复内容
        """
        # 首先尝试菜谱查询
        if any(keyword in request for keyword in ["怎么做", "怎么煮", "怎么做菜", "食谱", "菜谱"]):
            return self.query_recipe(request)

        # 然后尝试其他功能
        for _func_name, func in self.functions.items():
            result = func(request)
            if result and "没有找到" not in result and "需要密码" not in result:
                return result

        # 默认回复
        return """🤖 小诺（生活助理）为您服务！

我能帮您：
1. 🍜 菜谱查询 - 说"XX怎么做？"查看菜谱
2. 🔒 个人信息管理 - 需要通过 security_manager.py 访问
3. 📝 备忘录搜索 - 说"查找关于XX的笔记"
4. ⏰ 日程提醒 - 功能开发中...

现有菜谱：虾滑紫菜汤、番茄鱼片、山药碎汤
"""

# 全局小诺实例
xuenuo = XuenuoLifeAssistant()

def xuenuo_help(request) -> None:
    """
    小诺帮助函数

    Args:
        request (str): 用户请求

    Returns:
        str: 小诺的回复
    """
    return xuenuo.process_request(request)

# 测试
if __name__ == "__main__":
    # 测试各种请求
    test_requests = [
        "小诺，虾滑紫菜汤怎么做？",
        "帮我找一下我的简介",
        "今天该吃什么菜？",
        "小诺你能做什么？"
    ]

    print("=" * 60)
    print("🤖 小诺生活助理系统测试")
    print("=" * 60)

    for req in test_requests:
        print(f"\n用户: {req}")
        print(f"小诺: {xuenuo_help(req)}")
        print("-" * 50)
