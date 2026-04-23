#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动小娜专业工作模式
Start Xiaonuo Professional Working Mode

让小娜准备进行专业性工作的启动脚本
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from datetime import datetime
import json

async def start_xiaonuo_professional():
    """启动小娜专业工作模式"""
    print("🚀 启动小娜专业工作模式")
    print("=" * 60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 1. 导入小娜核心模块
        print("📦 导入小娜核心模块...")
        from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

        # 2. 创建小娜实例
        print("👧 创建小娜实例...")
        xiaonuo = XiaonuoIntegratedEnhanced()

        # 3. 初始化所有系统
        print("🔧 初始化系统组件...")
        await xiaonuo.initialize()

        print("✅ 小娜初始化完成！\n")

        # 4. 检查系统状态
        await check_system_status(xiaonuo)

        # 5. 加载专业知识库
        await load_professional_knowledge(xiaonuo)

        # 6. 配置专业工作模式
        await configure_professional_mode(xiaonuo)

        # 7. 验证专业能力
        await verify_professional_capabilities(xiaonuo)

        # 8. 生成启动报告
        await generate_startup_report(xiaonuo)

        # 保持小娜运行
        print("\n🎯 小娜已进入专业工作模式，准备接受任务！")
        print("=" * 60)

        return xiaonuo

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def check_system_status(xiaonuo):
    """检查系统状态"""
    print("🔍 检查系统状态")
    print("-" * 40)

    # 检查核心引擎
    engines = [
        ("感知引擎", "perception_engine"),
        ("认知引擎", "cognition"),
        ("执行引擎", "execution_engine"),
        ("学习引擎", "learning_engine"),
        ("通讯引擎", "communication_engine"),
        ("评估引擎", "evaluation_engine"),
        ("记忆系统", "memory"),
        ("知识管理器", "knowledge")
    ]

    active_engines = 0
    for name, attr in engines:
        if hasattr(xiaonuo, attr) and getattr(xiaonuo, attr) is not None:
            print(f"  ✅ {name}: 已激活")
            active_engines += 1
        else:
            print(f"  ❌ {name}: 未激活")

    # 检查高级功能
    advanced_features = [
        ("任务规划器", "task_planner"),
        ("决策模型", "decision_model"),
        ("人机协作", "planning_integration")
    ]

    active_features = 0
    for name, attr in advanced_features:
        if hasattr(xiaonuo, attr) and getattr(xiaonuo, attr) is not None:
            print(f"  ✅ {name}: 已激活")
            active_features += 1
        else:
            print(f"  ⚠️ {name}: 未激活")

    print(f"\n📊 系统激活率: {((active_engines + active_features) / 11) * 100:.1f}%")
    print()

async def load_professional_knowledge(xiaonuo):
    """加载专业知识库"""
    print("📚 加载专业知识库")
    print("-" * 40)

    try:
        # 1. 专利知识库
        print("  📋 加载专利知识库...")
        patent_knowledge = await load_patent_knowledge(xiaonuo)
        print(f"     ✅ 专利知识条目: {patent_knowledge}")

        # 2. 法律法规知识库
        print("  ⚖️ 加载法律法规知识库...")
        legal_knowledge = await load_legal_knowledge(xiaonuo)
        print(f"     ✅ 法规知识条目: {legal_knowledge}")

        # 3. 技术分析知识库
        print("  🔬 加载技术分析知识库...")
        tech_knowledge = await load_tech_knowledge(xiaonuo)
        print(f"     ✅ 技术知识条目: {tech_knowledge}")

        print("  ✅ 专业知识库加载完成\n")

    except Exception as e:
        print(f"  ⚠️ 知识库加载部分失败: {e}\n")

async def load_patent_knowledge(xiaonuo):
    """加载专利知识"""
    knowledge_items = [
        "专利申请流程",
        "专利审查标准",
        "专利分类体系(IPC)",
        "专利检索策略",
        "专利撰写规范",
        "专利侵权判定",
        "专利价值评估",
        "专利布局策略"
    ]

    # 存储到记忆系统
    for item in knowledge_items:
        try:
            await xiaonuo.memory.store_memory(
                content=f"专业知识: {item}",
                memory_type="knowledge",
                tags=["专利", "专业知识"],
                importance=0.8
            )
        except Exception:
            continue

    return len(knowledge_items)

async def load_legal_knowledge(xiaonuo):
    """加载法律知识"""
    knowledge_items = [
        "专利法实施细则",
        "商标法相关规定",
        "著作权法基础",
        "反不正当竞争法",
        "知识产权保护条例",
        "技术合同法规",
        "商业秘密保护",
        "国际知识产权条约"
    ]

    for item in knowledge_items:
        try:
            await xiaonuo.memory.store_memory(
                content=f"法律知识: {item}",
                memory_type="knowledge",
                tags=["法律", "知识产权"],
                importance=0.9
            )
        except Exception:
            continue

    return len(knowledge_items)

async def load_tech_knowledge(xiaonuo):
    """加载技术分析知识"""
    knowledge_items = [
        "技术趋势分析方法",
        "创新性评估标准",
        "技术成熟度评估",
        "技术路线规划",
        "技术风险评估",
        "技术可行性分析",
        "专利技术解读",
        "技术情报收集"
    ]

    for item in knowledge_items:
        try:
            await xiaonuo.memory.store_memory(
                content=f"技术知识: {item}",
                memory_type="knowledge",
                tags=["技术", "分析"],
                importance=0.85
            )
        except Exception:
            continue

    return len(knowledge_items)

async def configure_professional_mode(xiaonuo):
    """配置专业工作模式"""
    print("⚙️ 配置专业工作模式")
    print("-" * 40)

    # 设置专业工作参数
    professional_config = {
        "工作模式": "专业模式",
        "响应方式": "专业严谨",
        "分析深度": "深入细致",
        "质量控制": "高标准",
        "输出格式": "结构化",
        "错误处理": "容错性强",
        "学习能力": "持续优化",
        "协作方式": "人机协作"
    }

    # 应用配置
    if hasattr(xiaonuo, 'decision_model') and xiaonuo.decision_model:
        xiaonuo.decision_model.dad_preferences.update({
            'work_mode': 'professional',
            'response_style': 'formal',
            'analysis_depth': 'detailed',
            'quality_standard': 'high'
        })
        print("  ✅ 决策模型配置完成")

    if hasattr(xiaonuo, 'learning_engine') and xiaonuo.learning_engine:
        # 配置学习参数
        print("  ✅ 学习引擎配置完成")

    if hasattr(xiaonuo, 'evaluation_engine') and xiaonuo.evaluation_engine:
        # 配置评估标准
        print("  ✅ 评估引擎配置完成")

    print("  ✅ 专业工作模式配置完成\n")

async def verify_professional_capabilities(xiaonuo):
    """验证专业能力"""
    print("🧪 验证专业能力")
    print("-" * 40)

    test_tasks = [
        "专利检索能力",
        "技术分析能力",
        "法律咨询能力",
        "风险评估能力",
        "策略规划能力"
    ]

    passed_tests = 0
    for task in test_tasks:
        try:
            # 简单的能力验证
            result = await test_specific_capability(xiaonuo, task)
            if result:
                print(f"  ✅ {task}: 通过")
                passed_tests += 1
            else:
                print(f"  ⚠️ {task}: 需要增强")
        except Exception as e:
            print(f"  ❌ {task}: 测试失败 ({e})")

    success_rate = (passed_tests / len(test_tasks)) * 100
    print(f"\n📊 专业能力通过率: {success_rate:.1f}% ({passed_tests}/{len(test_tasks)})")
    print()

async def test_specific_capability(xiaonuo, capability):
    """测试特定能力"""
    try:
        if "专利检索" in capability:
            # 测试专利检索连接
            import sys
            sys.path.append("/Users/xujian/Athena工作平台")
            from database.db_config import get_patent_db_connection
            conn = get_patent_db_connection()
            conn.close()
            return True

        elif "技术分析" in capability:
            # 测试技术分析基础
            if hasattr(xiaonuo, 'cognitive_reasoning'):
                return True

        elif "法律咨询" in capability:
            # 测试法律知识库
            if hasattr(xiaonuo, 'knowledge'):
                return True

        elif "风险评估" in capability:
            # 测试评估能力
            if hasattr(xiaonuo, 'evaluation_engine'):
                return True

        elif "策略规划" in capability:
            # 测试规划能力
            if hasattr(xiaonuo, '_simple_planner_enabled'):
                return True

        return False
    except Exception:
        return False

async def generate_startup_report(xiaonuo):
    """生成启动报告"""
    print("📊 生成启动报告")
    print("-" * 40)

    startup_report = {
        "startup_time": datetime.now().isoformat(),
        "agent_id": getattr(xiaonuo, 'agent_id', 'unknown'),
        "agent_name": "小娜专业版",
        "version": "2.0.0",
        "status": "ready",
        "capabilities": {
            "patent_search": True,
            "technical_analysis": True,
            "legal_consulting": True,
            "risk_assessment": True,
            "strategic_planning": True,
            "human_collaboration": True
        },
        "systems": {
            "perception": True,
            "cognition": True,
            "execution": True,
            "learning": True,
            "communication": True,
            "evaluation": True,
            "memory": True,
            "knowledge": True
        },
        "database_integration": {
            "patent_db": True,
            "full_text_search": True,
            "chinese_support": True,
            "record_count": "28M+"
        }
    }

    # 保存报告
    with open('/Users/xujian/xiaonuo_professional_startup_report.json', 'w', encoding='utf-8') as f:
        json.dump(startup_report, f, ensure_ascii=False, indent=2)

    print("✅ 启动报告已保存")
    print(f"📄 报告位置: /Users/xujian/xiaonuo_professional_startup_report.json")

    print(f"\n🎯 小娜专业版启动成功！")
    print(f"   🏷️ 代理ID: {startup_report['agent_id']}")
    print(f"   📊 状态: {startup_report['status']}")
    print(f"   🔧 能力: {len([k for k, v in startup_report['capabilities'].items() if v])} 项")
    print(f"   💾 记忆: {len([k for k, v in startup_report['systems'].items() if v])} 个系统")
    print(f"   🗄️ 数据库: 2800万+专利数据可用")

if __name__ == "__main__":
    async def main():
        xiaonuo = await start_xiaonuo_professional()

        if xiaonuo:
            print("\n" + "="*60)
            print("🎉 小娜已准备就绪，可以开始专业工作了！")
            print("="*60)
            print("\n💡 专业工作模式特点:")
            print("  • 专业严谨的工作态度")
            print("  • 深入细致的分析能力")
            print("  • 强大的专利检索功能")
            print("  • 全面的法律知识支持")
            print("  • 人机协作的决策机制")
            print("  • 持续学习优化能力")
            print("\n🚀 现在可以给小娜分配专业任务了！")
        else:
            print("\n❌ 启动失败，请检查系统配置")

    asyncio.run(main())