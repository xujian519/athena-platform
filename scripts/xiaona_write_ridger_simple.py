#!/usr/bin/env python3
"""
小娜·天秤女神 - 农业种植用起垄器专利说明书撰写（简化版）
直接使用Ollama API
"""

import asyncio
from pathlib import Path

import aiohttp


async def write_patent_with_ollama():
    """使用Ollama API撰写专利说明书"""

    print("=" * 70)
    print("⚖️ 小娜·天秤女神 - 专利说明书撰写系统")
    print("=" * 70)
    print()

    # 读取技术交底书
    tech_disclosure_path = Path("/Users/xujian/Athena工作平台/data/reports/农业种植用起垄器_技术交底书.md")
    with open(tech_disclosure_path, encoding='utf-8') as f:
        tech_disclosure = f.read()

    # 构建提示词
    patent_prompt = f"""你是一位资深的专利代理人，拥有20年的专利申请撰写经验。请根据以下技术交底书，撰写"农业种植用起垄器"的完整实用新型专利申请文件。

# 发明人信息
- 发明人：李艳
- 身份证号：372325197904023645
- 联系地址：山东省沾化县黄升乡中心路4号6排16号
- 申请日期：2026年3月6日

# 技术交底书
{tech_disclosure}

# 撰写要求
请按照以下结构撰写完整的专利申请文件：

1. 发明名称
2. 技术领域
3. 背景技术（包含现有技术对比表格）
4. 发明内容
   - 要解决的技术问题
   - 技术方案（详细描述各部件结构）
   - 有益效果（与现有技术对比）
5. 附图说明（描述7张附图）
6. 具体实施方式（提供3个实施例）
7. 权利要求书（1项独立权利要求+从属权利要求）
8. 与现有技术的区别特征

语言风格：专业、严谨、准确，符合专利申请要求。"""

    print("📝 正在通过Ollama API生成专利说明书...")
    print("-" * 70)

    try:
        # 使用Ollama API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8765/v1/chat/completions",
                json={
                    "model": "glm-4.7-flash:latest",
                    "messages": [{"role": "user", "content": patent_prompt}],
                    "stream": False,
                    "temperature": 0.3,
                    "max_tokens": 8000,
                },
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status != 200:
                    print(f"❌ Ollama API返回错误: {response.status}")
                    return False

                result = await response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        print()
        print("=" * 70)
        print("✅ 专利说明书撰写完成")
        print("=" * 70)
        print()

        # 保存结果
        output_dir = Path("/Users/xujian/Athena工作平台/data/reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存专利说明书
        spec_file = output_dir / "农业种植用起垄器_专利说明书_小娜版.md"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 专利说明书已保存: {spec_file}")

        print()
        print("📊 撰写统计:")
        print(f"  - 总字数: {len(content)} 字")
        paragraph_delimiter = '\n\n'
        print(f"  - 段落数: {len([p for p in content.split(paragraph_delimiter) if p.strip()])} 段")

        print()
        print("✅ 专利说明书撰写任务完成")
        return True

    except Exception as e:
        print(f"❌ 任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(write_patent_with_ollama())
    sys.exit(0 if success else 1)
