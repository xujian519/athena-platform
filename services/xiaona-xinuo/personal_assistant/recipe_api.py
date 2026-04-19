#!/usr/bin/env python3
"""
菜谱查询API接口
Recipe Query API for Xiaona System
"""


from simple_recipe_query import query_recipe_direct


def get_recipe(recipe_name) -> None:
    """
    获取菜谱的API函数

    Args:
        recipe_name (str): 菜谱名称，如"虾滑紫菜汤"

    Returns:
        str: 格式化的菜谱内容
    """
    return query_recipe_direct(recipe_name)

# 示例用法
if __name__ == "__main__":
    # 测试API
    import sys

    if len(sys.argv) > 1:
        recipe_name = sys.argv[1]
        print(get_recipe(recipe_name))
    else:
        # 默认测试
        print("=== 菜谱查询API测试 ===")
        print(get_recipe("虾滑紫菜汤"))
