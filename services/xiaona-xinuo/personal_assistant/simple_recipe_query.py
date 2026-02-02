#!/usr/bin/env python3
"""
简单菜谱查询系统
Simple Recipe Query System - 直接从备份文件查询
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable, Union

class SimpleRecipeQuery:
    """简单菜谱查询系统"""

    def __init__(self):
        self.backup_dir = Path("/Users/xujian/Nutstore Files/13-Markdown/05个人/05-2菜谱")

    def query_recipe(self, recipe_name) -> None:
        """查询菜谱"""
        # 查找匹配的文件
        for file in self.backup_dir.glob("*.md"):
            if recipe_name in file.name:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return self.format_recipe(content, recipe_name)
                except Exception as e:
                    return f"读取菜谱失败: {e}"

        # 如果没找到，尝试搜索内容
        results = self.search_in_content(recipe_name)
        if results:
            return results

        return f"抱歉，没有找到《{recipe_name}》的菜谱。现有的菜谱有：\n1. 虾滑紫菜汤\n2. 番茄鱼片\n3. 山药碎汤"

    def search_in_content(self, keyword) -> None:
        """在文件内容中搜索关键词"""
        for file in self.backup_dir.glob("*.md"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if keyword in content:
                        recipe_name = file.stem
                        return self.format_recipe(content, recipe_name)
            except (FileNotFoundError, PermissionError, OSError):
                continue
        return None

    def format_recipe(self, content, recipe_name) -> None:
        """格式化菜谱回复"""
        if not content:
            return f"没有找到《{recipe_name}》的详细内容。"

        # 解析内容
        lines = content.split('\n')
        ingredients = []
        steps = []
        current_section = None

        for line in lines:
            line = line.strip()
            # 识别原材料部分
            if "原材料" in line or "一、" in line:
                current_section = "ingredients"
                continue
            # 识别步骤部分
            elif "步骤" in line or "二、" in line:
                current_section = "steps"
                continue
            # 收集原材料
            elif line and current_section == "ingredients":
                if line and not line.startswith("#"):
                    # 清理格式
                    clean_line = line.lstrip("- 0123456789.，；。").strip()
                    if clean_line:
                        ingredients.append(clean_line)
            # 收集步骤
            elif line and current_section == "steps":
                if line and not line.startswith("#"):
                    # 清理格式
                    clean_line = line.lstrip("- 0123456789.，；。").strip()
                    if clean_line:
                        steps.append(clean_line)

        # 格式化回复
        response = f"🍜 《{recipe_name}》\n\n"

        if ingredients:
            response += "🥘 所需材料：\n"
            for ing in ingredients:
                # 过滤掉空行和非材料行
                if ing and any(char in ing for char in ["；", "。", "、", "，", "鸡蛋", "虾滑", "番茄", "山药", "紫菜", "芫荽", "葱姜蒜", "盐", "味精"]):
                    response += f"  • {ing}\n"

        if steps:
            response += "\n👨‍🍳 制作步骤：\n"
            for i, step in enumerate(steps, 1):
                # 过滤掉空行
                if step and len(step) > 5:
                    response += f"  {i}. {step}\n"

        return response

def query_recipe_direct(recipe_name) -> None:
    """直接查询函数，供外部调用"""
    srq = SimpleRecipeQuery()
    return srq.query_recipe(recipe_name)

# 测试函数
if __name__ == "__main__":
    # 测试几个菜谱
    test_recipes = ["虾滑紫菜汤", "番茄鱼片", "山药碎汤"]

    for recipe in test_recipes:
        print(f"\n{'='*60}")
        print(f"查询: {recipe}")
        print('='*60)
        result = query_recipe_direct(recipe)
        print(result)