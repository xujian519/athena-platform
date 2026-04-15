#!/usr/bin/env python3
"""
更新知识图谱API服务以支持审查指南
"""

import os
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

def update_main_app() -> None:
    """更新主应用文件"""
    main_app_path = Path("/Users/xujian/Athena工作平台/services/knowledge-graph-service/api/main.py")

    # 读取原文件
    if not main_app_path.exists():
        logger.error(f"主应用文件不存在: {main_app_path}")
        return False

    with open(main_app_path, encoding='utf-8') as f:
        content = f.read()

    # 检查是否已导入
    if "guideline_integration" in content:
        logger.info("审查指南模块已集成")
        return True

    # 添加导入语句
    import_section = """
# 导入审查指南集成模块
from api.guideline_integration import GuidelineIntegration, add_guideline_routes

# 创建审查指南集成实例
guideline_integration = GuidelineIntegration()
"""

    # 在适当位置插入导入
    lines = content.split('\n')
    import_pos = -1
    for i, line in enumerate(lines):
        if line.startswith("from fastapi import"):
            import_pos = i + 1
            break

    if import_pos > 0:
        lines.insert(import_pos, import_section)

    # 添加路由注册
    route_section = """
# 注册审查指南路由
add_guideline_routes(app)
"""

    # 在app创建后添加路由注册
    for i, line in enumerate(lines):
        if "app = FastAPI(" in line:
            # 找到app创建后的位置
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('@'):
                j += 1
            lines.insert(j, route_section)
            break

    # 写回文件
    updated_content = '\n'.join(lines)
    with open(main_app_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    logger.info("✅ 主应用文件更新成功")
    return True

def create_health_check() -> Any:
    """创建健康检查端点"""
    health_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查审查指南集成状态
"""

import requests
import json

def check_qdrant():
    """检查Qdrant服务"""
    try:
        response = requests.get("http://localhost:6333/collections/patent_guideline")
        if response.status_code == 200:
            data = response.json()
            points = data.get("result", {}).get("points_count", 0)
            print(f"✅ Qdrant: patent_guideline集合, {points}个向量")
            return True
    except (json.JSONDecodeError, TypeError, ValueError):
        print("❌ Qdrant服务不可用")
    return False

def check_graph_data():
    """检查知识图谱数据"""
    try:
        with open("/Users/xujian/Athena工作平台/data/guideline_graph/patent_guideline_graph.json", "r") as f:
            data = json.load(f)
            nodes = len(data.get("nodes", []))
            rels = len(data.get("relationships", []))
            print(f"✅ 知识图谱: {nodes}个节点, {rels}条关系")
            return True
    except (json.JSONDecodeError, TypeError, ValueError):
        print("❌ 知识图谱数据文件不存在")
    return False

def check_api():
    """检查API服务"""
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code == 200:
            print("✅ API服务运行正常")
            return True
    except (ConnectionError, OSError, TimeoutError):
        print("❌ API服务不可用")
    return False

def main():
    print("检查审查指南集成状态...\n")

    all_ok = True

    if not check_qdrant():
        all_ok = False

    if not check_graph_data():
        all_ok = False

    if not check_api():
        all_ok = False

    print("\n" + "="*50)
    if all_ok:
        print("✅ 所有组件运行正常")
        print("\n可用的API端点:")
        print("- GET  /api/v2/guidelines/search?query=<text>")
        print("- GET  /api/v2/guidelines/structure")
        print("- POST /api/v2/guidelines/prompt")
        print("- GET  /api/v2/guidelines/extract-rules?topic=<text>")
    else:
        print("⚠️ 部分组件存在问题")
    print("="*50)

if __name__ == "__main__":
    main()
'''

    health_path = Path("/Users/xujian/Athena工作平台/services/knowledge-graph-service/check_guideline_status.py")
    with open(health_path, 'w', encoding='utf-8') as f:
        f.write(health_content)

    # 设置执行权限
    os.chmod(health_path, 0o755)

    logger.info("✅ 健康检查脚本创建成功")

def create_usage_example() -> Any:
    """创建使用示例"""
    example_content = '''# 专利审查指南API使用示例

## 1. 搜索审查指南
```bash
curl -X GET "http://localhost:8080/api/v2/guidelines/search?query=发明专利&limit=5"
```

## 2. 获取指南结构
```bash
curl -X GET "http://localhost:8080/api/v2/guidelines/structure"
```

## 3. 生成动态提示词
```bash
curl -X POST "http://localhost:8080/api/v2/guidelines/prompt" \\
  -H "Content-Type: application/json" \\
  -d '{"context": "申请文件格式审查", "max_rules": 5}'
```

## 4. 提取主题规则
```bash
curl -X GET "http://localhost:8080/api/v2/guidelines/extract-rules?topic=新颖性&limit=10"
```

## Python SDK使用示例

```python
import requests

# 搜索审查指南
response = requests.get(
    "http://localhost:8080/api/v2/guidelines/search",
    params={"query": "发明专利", "limit": 5}
)
results = response.json()["results"]

# 生成提示词
response = requests.post(
    "http://localhost:8080/api/v2/guidelines/prompt",
    json={"context": "申请文件格式审查"}
)
prompt = response.json()["prompt"]

print(prompt)
```
'''

    example_path = Path("/Users/xujian/Athena工作平台/services/knowledge-graph-service/GUIDELINE_API_USAGE.md")
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_content)

    logger.info("✅ 使用示例文档创建成功")

def main() -> None:
    """主函数"""
    print("🚀 更新知识图谱API服务以支持审查指南...")
    print("\n" + "="*60)

    # 1. 更新主应用
    if update_main_app():
        print("\n1. ✅ API服务集成完成")
    else:
        print("\n1. ❌ API服务集成失败")
        return False

    # 2. 创建健康检查
    create_health_check()
    print("\n2. ✅ 健康检查脚本创建完成")

    # 3. 创建使用示例
    create_usage_example()
    print("\n3. ✅ 使用示例文档创建完成")

    print("\n" + "="*60)
    print("✅ 审查指南集成完成！")
    print("\n📝 后续步骤:")
    print("1. 重启API服务: docker-compose restart")
    print("2. 检查集成状态: python3 check_guideline_status.py")
    print("3. 查看使用示例: cat GUIDELINE_API_USAGE.md")
    print("\n🔗 可用的API端点:")
    print("- GET  /api/v2/guidelines/search")
    print("- GET  /api/v2/guidelines/structure")
    print("- POST /api/v2/guidelines/prompt")
    print("- GET  /api/v2/guidelines/extract-rules")
    print("="*60)

if __name__ == "__main__":
    main()
