#!/usr/bin/env python3
"""
爸爸的菜谱查询系统
Recipe Query System
"""

from pathlib import Path

from security_manager import PersonalSecurityManager


class RecipeQuerySystem:
    """菜谱查询系统"""

    def __init__(self):
        self.security_manager = PersonalSecurityManager()
        self.recipe_keywords = {
            "虾滑紫菜汤": ["虾滑", "紫菜", "汤"],
            "番茄鱼片": ["番茄", "鱼片", "巴沙鱼"],
            "山药碎汤": ["山药", "碎汤", "汤"]
        }

    def query_recipe(self, query) -> None:
        """查询菜谱"""
        # 先在标题中搜索
        results = self.security_manager.get_secure_info(search_term=query)

        recipes = []
        for result in results:
            if "content" in result and any(keyword in result["title"] for keyword in ["虾滑", "番茄", "山药", "菜谱"]):
                recipes.append({
                    "title": result["title"],
                    "content": result.get("content", "内容未找到"),
                    "created_at": result.get("created_at", "未知")
                })

        return recipes

    def get_recipe_by_name(self, recipe_name) -> None:
        """根据菜名获取完整菜谱"""
        # 直接搜索完整菜名
        results = self.security_manager.get_secure_info(search_term=recipe_name)

        for result in results:
            if recipe_name in result["title"]:
                # 从备份文件读取完整内容
                backup_file = self.find_backup_file(result["title"])
                if backup_file and backup_file.exists():
                    try:
                        with open(backup_file, encoding='utf-8') as f:
                            return f.read()
                    except Exception as e:
                        return f"读取文件失败: {e}"

        return None

    def find_backup_file(self, title) -> None:
        """查找备份文件"""
        backup_dir = Path("/Users/xujian/Athena工作平台/personal_secure_storage/file_backups/05个人/05-2菜谱")

        for file in backup_dir.rglob("*"):
            if file.is_file() and title.replace(" ", "") in file.name:
                return file

        return None

    def format_recipe_response(self, recipe_content, recipe_name) -> None:
        """格式化菜谱回复"""
        if not recipe_content:
            return f"抱歉，没有找到《{recipe_name}》的菜谱。"

        # 提取关键信息
        lines = recipe_content.split('\n')
        ingredients = []
        steps = []
        current_section = None

        for line in lines:
            line = line.strip()
            if "原材料" in line or "一、" in line:
                current_section = "ingredients"
            elif "步骤" in line or "二、" in line:
                current_section = "steps"
            elif line and current_section == "ingredients":
                if any(char in line for char in ["、", "，", "."]):
                    ingredients.append(line)
            elif line and current_section == "steps":
                if line.startswith("-") or line.startswith("2.") or (line and not line.startswith("#")):
                    steps.append(line)

        response = f"🍜 《{recipe_name}》\n\n"
        response += "🥘 所需材料：\n"
        for ing in ingredients:
            response += f"  {ing}\n"

        response += "\n👨‍🍳 制作步骤：\n"
        for i, step in enumerate(steps, 1):
            response += f"  {i}. {step.lstrip('- 0123456789.')}\n"

        return response

def main() -> None:
    """测试函数"""
    rqs = RecipeQuerySystem()

    # 测试查询
    test_recipes = ["虾滑紫菜汤", "番茄鱼片", "山药碎汤"]

    for recipe in test_recipes:
        print(f"\n{'='*50}")
        print(f"查询: {recipe}")
        print('='*50)

        content = rqs.get_recipe_by_name(recipe)
        response = rqs.format_recipe_response(content, recipe)
        print(response)

if __name__ == "__main__":
    main()
