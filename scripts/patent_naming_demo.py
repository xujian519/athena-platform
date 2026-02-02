#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小娜专利命名系统演示
Xiaona Patent Naming System Demo

演示小娜专利命名系统的使用方法
处理异丁烷脱氢制MTBE组合工艺等专利命名项目

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.cognition.xiaona_patent_naming_system import (
    XiaonaPatentNamingSystem,
    PatentNamingRequest,
    PatentType,
    NamingStyle
)

async def demo_naming_system():
    """演示专利命名系统"""
    print("="*80)
    print("⚖️" + " "*25 + "小娜专利命名系统演示" + " "*25 + "⚖️")
    print("="*80)
    print(f"🕐 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👩‍⚖️ 操作者: 小娜·天秤女神 (专利法律专家)")
    print(f"🎯 演示目标: 展示专利命名系统功能")
    print("="*80)

    # 初始化命名系统
    print("\n🚀 正在初始化小娜专利命名系统...")
    naming_system = XiaonaPatentNamingSystem()

    # 显示系统统计
    stats = naming_system.get_naming_statistics()
    print(f"✅ 系统初始化完成")
    print(f"📊 支持专利类型: {', '.join(stats['supported_types'])}")
    print(f"📚 技术词汇库: {stats['technical_vocabulary_count']} 个领域")
    print(f"📝 命名模板: {stats['naming_templates_count']} 个")
    print(f"🏆 成功案例: {stats['success_cases_count']} 个")

    # 演示案例1: 异丁烷脱氢制MTBE组合工艺
    print("\n" + "="*60)
    print("📋 案例一: 异丁烷脱氢制MTBE组合工艺")
    print("="*60)

    request1 = PatentNamingRequest(
        patent_type=PatentType.INVENTION,
        technical_field="化学工程",
        invention_description="本发明涉及一种异丁烷脱氢制MTBE的组合工艺，通过优化反应条件和分离工艺，提高MTBE产率和纯度。该工艺采用多级反应器和先进的分离技术，实现了高效、节能的MTBE生产。",
        key_features=["异丁烷脱氢", "MTBE合成", "组合工艺", "反应器优化", "分离技术"],
        application_scenarios=["石油化工", "汽油添加剂生产", "化工原料制备"],
        innovation_points=["多级反应器设计", "工艺参数优化", "分离纯化技术", "能效提升"],
        naming_style=NamingStyle.TECHNICAL,
        special_requirements=["突出技术优势", "体现工艺创新"],
        client_info={
            "company": "某化工企业",
            "industry": "石油化工"
        }
    )

    result1 = await naming_system.generate_patent_name(request1)

    print(f"🎯 主要专利名称: {result1.patent_name}")
    print(f"📋 备选名称: {', '.join(result1.alternative_names)}")
    print(f"⭐ 命名置信度: {result1.naming_confidence:.2f}")
    print(f"💡 专业见解: {len(result1.professional_insights)} 条专业建议")

    # 演示案例2: 智能手机曲面屏设计
    print("\n" + "="*60)
    print("📋 案例二: 智能手机曲面屏外观设计")
    print("="*60)

    request2 = PatentNamingRequest(
        patent_type=PatentType.DESIGN,
        technical_field="产品设计",
        invention_description="本设计涉及一种智能手机的曲面屏外观，采用创新的曲面设计语言，结合现代美学和人体工学，提供更好的视觉体验和手感。",
        key_features=["曲面屏", "智能手机", "创新设计", "美学设计", "人体工学"],
        application_scenarios=["消费电子", "移动设备", "智能终端"],
        innovation_points=["曲面设计", "视觉效果", "用户体验", "制造工艺"],
        naming_style=NamingStyle.APPLICATION,
        special_requirements=["体现设计美感", "突出创新特色"],
        client_info={
            "company": "手机设计公司",
            "industry": "消费电子"
        }
    )

    result2 = await naming_system.generate_patent_name(request2)

    print(f"🎯 主要专利名称: {result2.patent_name}")
    print(f"📋 备选名称: {', '.join(result2.alternative_names)}")
    print(f"⭐ 命名置信度: {result2.naming_confidence:.2f}")

    # 演示案例3: 高效节能LED驱动电路结构
    print("\n" + "="*60)
    print("📋 案例三: 高效节能LED驱动电路结构")
    print("="*60)

    request3 = PatentNamingRequest(
        patent_type=PatentType.UTILITY_MODEL,
        technical_field="电子工程",
        invention_description="本实用新型涉及一种高效节能的LED驱动电路结构，通过优化电路设计和控制策略，显著提高LED驱动效率和节能效果。",
        key_features=["LED驱动", "节能电路", "电路结构", "控制策略", "高效设计"],
        application_scenarios=["照明设备", "显示屏", "指示灯", "装饰照明"],
        innovation_points=["电路优化", "节能控制", "稳定性提升", "成本降低"],
        naming_style=NamingStyle.FUNCTIONAL,
        special_requirements=["突出功能特点", "体现节能效果"],
        client_info={
            "company": "LED制造企业",
            "industry": "电子制造"
        }
    )

    result3 = await naming_system.generate_patent_name(request3)

    print(f"🎯 主要专利名称: {result3.patent_name}")
    print(f"📋 备选名称: {', '.join(result3.alternative_names)}")
    print(f"⭐ 命名置信度: {result3.naming_confidence:.2f}")

    # 批量命名演示
    print("\n" + "="*60)
    print("🔄 批量命名演示")
    print("="*60)

    batch_requests = [request1, request2, request3]
    batch_results = await naming_system.generate_batch_naming(batch_requests)

    print(f"✅ 批量命名完成: {len(batch_results)} 个专利")
    for i, result in enumerate(batch_results, 1):
        print(f"  {i}. {result.patent_name} ({result.naming_confidence:.2f})")

    # 案例分析演示
    print("\n" + "="*60)
    print("🔍 案例分析演示")
    print("="*60)

    test_name = "异丁烷脱氢制MTBE组合工艺系统及方法"
    analysis = await naming_system.analyze_naming_case(test_name, "invention")

    print(f"📝 分析名称: {analysis['patent_name']}")
    print(f"📊 相似度分数: {analysis['similarity_score']:.2f}")
    print(f"✅ 优势: {', '.join(analysis['strengths'])}")
    print(f"⚠️ 不足: {', '.join(analysis['weaknesses'])}")
    print(f"💡 建议: {', '.join(analysis['suggestions'])}")

    # 保存结果
    print("\n" + "="*60)
    print("💾 保存演示结果")
    print("="*60)

    demo_results = {
        "demo_time": datetime.now().isoformat(),
        "case_1": {
            "name": result1.patent_name,
            "type": "发明专利",
            "confidence": result1.naming_confidence,
            "alternatives": result1.alternative_names
        },
        "case_2": {
            "name": result2.patent_name,
            "type": "外观设计专利",
            "confidence": result2.naming_confidence,
            "alternatives": result2.alternative_names
        },
        "case_3": {
            "name": result3.patent_name,
            "type": "实用新型专利",
            "confidence": result3.naming_confidence,
            "alternatives": result3.alternative_names
        }
    }

    result_file = Path("/tmp/xiaona_patent_naming_demo.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(demo_results, f, ensure_ascii=False, indent=2)

    print(f"✅ 演示结果已保存到: {result_file}")

    # 实际项目检查
    print("\n" + "="*60)
    print("📋 实际项目检查")
    print("="*60)

    # 检查是否有实际的专利起名任务
    print("🔍 检查实际专利起名项目...")

    # 这里可以集成实际的客户需求
    pending_projects = [
        {
            "project": "异丁烷脱氢制MTBE组合工艺",
            "client": "化工企业",
            "status": "待处理",
            "priority": "高",
            "deadline": "待确认"
        }
    ]

    if pending_projects:
        print(f"⏳ 发现 {len(pending_projects)} 个待处理项目:")
        for project in pending_projects:
            print(f"  📁 {project['project']} ({project['client']}) - {project['status']}")

        print("\n💡 建议:")
        print("  1. 使用小娜专利命名系统生成专业名称")
        print("  2. 结合客户具体要求调整命名风格")
        print("  3. 确保命名符合专利法规要求")
        print("  4. 提供多个备选方案供客户选择")
    else:
        print("✅ 当前无待处理的专利起名项目")

    print("\n" + "="*80)
    print("🎉 小娜专利命名系统演示完成")
    print("="*80)
    print("💖 小娜已准备好为您提供专业的专利命名服务")
    print("📞 如需服务，请联系小娜进行专业咨询")
    print("🔧 系统支持发明专利、实用新型专利、外观设计专利命名")
    print("✨ 具备技术分析、创新点提炼、合规检查等完整功能")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(demo_naming_system())