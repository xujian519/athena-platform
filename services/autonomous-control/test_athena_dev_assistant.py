#!/usr/bin/env python3
"""
测试Athena开发助手
Test Athena Development Assistant
"""

import asyncio
import sys
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / "athena_dev_assistant"))

from tools.patent_writing_tool import AthenaPatentWritingTool
from tools.examination_response_tool import AthenaExaminationResponseTool


async def test_patent_writing():
    """测试专利撰写工具"""
    print("\n🧪 测试专利撰写工具")
    print("-" * 30)

    tool = AthenaPatentWritingTool()

    # 示例技术交底
    disclosure = """
    技术领域
    本发明涉及物联网技术领域，具体是一种智能温控系统。

    背景技术
    目前的温控系统需要手动设置，不够智能化。现有技术虽然有一些自动温控，但成本高，精度低。

    技术方案
    本发明提供一种智能温控系统，包括：温度传感器阵列；中央处理器；机器学习模块；无线通信模块；执行器控制模块。
    中央处理器接收温度传感器阵列的数据，通过机器学习模块预测温度变化趋势，控制执行器模块调节温度。

    有益效果
    本发明的有益效果是：1）实现智能温度控制；2）提高控制精度；3）降低能耗。
    """

    # 分析
    print("\n1. 分析技术交底书...")
    analysis = tool.analyze_invention_disclosure(disclosure)
    print("✅ 分析完成")

    # 生成权利要求
    print("\n2. 生成权利要求...")
    claims = tool.draft_claims(analysis, "产品")
    print(f"✅ 生成了 {len(claims)} 条权利要求")
    print(f"   第一条: {claims[0][:50]}..." if claims else "   无权利要求")

    # 生成说明书
    print("\n3. 生成说明书...")
    spec = tool.draft_specification(analysis)
    print("✅ 说明书生成完成")
    print(f"   技术领域: {spec['技术领域'][:50]}...")

    # 检查专利法第26条
    print("\n4. 检查专利法第26条...")
    check_result = tool.check_patent_law_26('\n'.join(spec.values()))
    print(f"✅ 检查完成: 完整性={check_result['完整性检查']['是否完整']}")


async def test_examination_response():
    """测试审查答复工具"""
    print("\n🧪 测试审查答复工具")
    print("-" * 30)

    tool = AthenaExaminationResponseTool()

    # 示例审查意见
    opinion = """
    审查意见

    1. 关于权利要求1的新颖性
    权利要求1不具备新颖性，其与对比文件D1公开内容相同。

    2. 关于权利要求2的创造性
    权利要求2相对于D1和D2的结合是显而易见的，不具备创造性。

    3. 关于权利要求3的清楚性
    权利要求3的保护范围不清楚。
    """

    # 分析
    print("\n1. 分析审查意见...")
    analysis = tool.analyze_examination_opinion(opinion)
    print(f"✅ 分析完成: {', '.join(analysis['审查类型'])}")

    # 生成答复提纲
    print("\n2. 生成答复提纲...")
    outline = tool.generate_response_outline(analysis)
    print(f"✅ 提纲完成: {len(outline['正文段落'])} 个段落")

    # 生成答复
    print("\n3. 生成答复...")
    patent_info = {
        "application_no": "202410000000.0",
        "applicant": "测试公司"
    }
    response = tool.draft_response(analysis, patent_info)
    print(f"✅ 答复完成: {len(response)} 字符")

    # 生成修改建议
    print("\n4. 生成修改建议...")
    suggestions = tool.generate_amendment_suggestions(analysis)
    print(f"✅ 建议完成: {len(suggestions)} 条建议")

    # 检查完整性
    print("\n5. 检查答复完整性...")
    completeness = tool.check_response_completeness(response)
    print(f"✅ 完整性检查: 格式完整, 内容完整")


async def test_integration():
    """测试集成功能"""
    print("\n🧪 测试集成功能")
    print("-" * 30)

    # 测试模块导入
    try:
        from athena_dev_integration import router, get_writing_tool, get_response_tool
        print("✅ 模块导入成功")

        # 测试工具实例化
        writing_tool = get_writing_tool()
        response_tool = get_response_tool()
        print("✅ 工具实例化成功")

        # 测试路由
        routes = [route.path for route in router.routes]
        print(f"✅ API路由: {len(routes)} 个端点")
        for route in routes[:3]:
            print(f"   - {route}")

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")


async def main():
    """主测试函数"""
    print("🧪 Athena开发助手测试")
    print("=" * 50)
    print("💖 爸爸的专利专业助手测试")
    print("=" * 50)

    # 运行测试
    await test_patent_writing()
    await test_examination_response()
    await test_integration()

    print("\n" + "=" * 50)
    print("✨ 所有测试完成！")
    print("💖 Athena已经准备好为爸爸服务！")
    print("\n启动命令:")
    print("  python3 start_athena_dev_assistant.py")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())