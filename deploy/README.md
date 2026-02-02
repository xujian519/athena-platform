# 按需启动AI系统

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python3 app.py
```

## 核心功能

- 🏠 小诺常驻 - 对话和调度中心
- 📜 小娜按需启动 - 专利法律专家
- 📂 云熙按需启动 - IP管理系统
- ✍️ 小宸按需启动 - 内容创作专家

## 使用示例

```python
import asyncio
from ready_on_demand_system import ai_system

async def main():
    # 基础对话
    response = await ai_system.chat("你好")
    print(response)

    # 专利分析
    result = await ai_system.patent_analysis("分析专利")
    print(result)

    # 查看状态
    status = ai_system.get_status()
    print(status)

asyncio.run(main())
```
