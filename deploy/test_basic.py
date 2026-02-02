import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

try:
    from ready_on_demand_system import ai_system
    print("✅ 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

async def test():
    print("🚀 开始测试...")

    # 测试基础对话
    try:
        response = await ai_system.chat("你好")
        print(f"✅ 基础对话测试通过 ({len(response)}字符)")
    except Exception as e:
        print(f"❌ 基础对话测试失败: {e}")
        return False

    # 测试专利分析
    try:
        response = await ai_system.patent_analysis("测试专利")
        print(f"✅ 专利分析测试通过 ({len(response)}字符)")
    except Exception as e:
        print(f"❌ 专利分析测试失败: {e}")
        return False

    # 测试状态查询
    try:
        status = ai_system.get_status()
        print(f"✅ 状态查询测试通过 ({status['running_agents']}/{status['total_agents']})")
    except Exception as e:
        print(f"❌ 状态查询测试失败: {e}")
        return False

    print("🎉 所有测试通过!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
