#!/usr/bin/env python3
from typing import Any

"""
小诺菜谱助手
Xuenuo Recipe Assistant - 小诺是您的生活助理
"""

class XuenuoRecipeAssistant:
    """小诺（生活助理）的菜谱助手"""

    def __init__(self):
        # 菜谱关键词映射
        self.recipe_keywords = {
            "虾滑紫菜汤": ["虾滑", "紫菜", "汤"],
            "番茄鱼片": ["番茄", "鱼片", "巴沙鱼", "鱼汤"],
            "山药碎汤": ["山药", "碎汤", "汤"]
        }

        # 可用菜谱列表
        self.available_recipes = ["虾滑紫菜汤", "番茄鱼片", "山药碎汤"]

    def query_recipe(self, question) -> None:
        """
        根据问题查询菜谱

        Args:
            question (str): 用户的问题，如"虾滑紫菜汤怎么做？"

        Returns:
            str: 菜谱回答
        """
        # 识别菜名
        recipe_name = self.extract_recipe_name(question)

        if recipe_name:
            # 使用API查询菜谱
            from recipe_api import get_recipe
            return get_recipe(recipe_name)
        else:
            # 提供可用菜谱列表
            return self.list_available_recipes()

    def extract_recipe_name(self, question) -> None:
        """从问题中提取菜名"""
        # 优先完整匹配菜名
        for recipe in self.available_recipes:
            if recipe in question:
                return recipe

        # 然后关键词匹配
        for recipe in self.available_recipes:
            for keyword in self.recipe_keywords.get(recipe, []):
                if keyword in question:
                    return recipe
        return None

    def list_available_recipes(self) -> Any:
        """列出可用菜谱"""
        response = "📚 爸爸的菜谱本里有以下菜谱：\n\n"
        for i, recipe in enumerate(self.available_recipes, 1):
            response += f"{i}. {recipe}\n"
        response += "\n💡 您可以说：'XX怎么做？' 来查看具体菜谱"
        return response

# 全局实例
recipe_assistant = XuenuoRecipeAssistant()

def answer_recipe_question(question) -> None:
    """
    回答菜谱问题的便捷函数

    Args:
        question (str): 用户问题

    Returns:
        str: 菜谱回答
    """
    return recipe_assistant.query_recipe(question)

# 测试
if __name__ == "__main__":
    # 测试各种问题
    test_questions = [
        "虾滑紫菜汤怎么做呀？",
        "番茄鱼片的制作方法？",
        "山药汤怎么煮？",
        "今天吃什么？"
    ]

    for q in test_questions:
        print(f"\n问: {q}")
        print(f"答: {answer_recipe_question(q)}")
        print("-" * 50)
