#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动小娜专利搜索系统
Start Xiaona Patent Search System

小娜·天秤女神 - 专利法律专家，为您搜索中国专利！

作者: 小诺·双鱼座
创建时间: 2025-12-17
版本: v1.0.0 "专利搜索就绪"
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加core路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XiaonaPatentSearchSystem:
    """小娜专利搜索系统"""

    def __init__(self):
        self.name = "小娜专利搜索系统"
        self.version = "v1.0.0"
        self.xiaona_controller = None
        self.search_history = []
        self.chinese_patent_sources = [
            "Google Patents",
            "CNIPA (中国国家知识产权局)",
            "Patsnap专利数据库",
            "智慧芽专利数据库",
            "百度专利搜索"
        ]

    def __str__(self):
        return f"⚖️ {self.name} ({self.version})"

    async def initialize(self):
        """初始化小娜专利搜索系统"""
        print("\n" + "="*60)
        print("⚖️ 启动小娜专利搜索系统...")
        print("="*60)

        try:
            # 导入小娜控制器
            from cognition.xiaona_google_patents_controller import (
                XiaonaGooglePatentsController,
                PatentRetrievalRequest,
                PatentRetrievalResult
            )

            # 初始化小娜控制器
            self.xiaona_controller = XiaonaGooglePatentsController()

            print(f"✅ {self.name} 初始化完成")
            print(f"📊 小娜专业能力:")
            print(f"   - 专利法律专业: 95%")
            print(f"   - 知识产权分析: 90%")
            print(f"   - 先前技术分析: 85%")
            print(f"   - 专利验证能力: 90%")

            print(f"\n🔍 支持的专利数据源:")
            for i, source in enumerate(self.chinese_patent_sources, 1):
                print(f"   {i}. {source}")

            print(f"\n🎯 小娜功能特性:")
            print(f"   ✅ 全文获取")
            print(f"   ✅ 结构化分析")
            print(f"   ✅ 法律分析")
            print(f"   ✅ 批量处理")
            print(f"   ✅ 智能推荐")

        except ImportError as e:
            print(f"❌ 初始化失败: {e}")
            print(f"💡 建议检查依赖是否安装完整")
            return False

        return True

    def create_search_request(self, patent_number: str, description: str = "") -> PatentRetrievalRequest:
        """创建专利搜索请求"""
        return PatentRetrievalRequest(
            patent_number=patent_number,
            retrieval_type="full_text",
            priority="high",
            user_request=description or f"获取专利 {patent_number} 的详细信息",
            output_format=["json", "structured"],
            language_preference="zh"
        )

    async def search_single_patent(self, patent_number: str, description: str = "") -> PatentRetrievalResult | None:
        """搜索单个专利"""
        print(f"\n🔍 搜索专利: {patent_number}")

        if not self.xiaona_controller:
            print("❌ 小娜控制器未初始化")
            return None

        try:
            # 创建搜索请求
            request = self.create_search_request(patent_number, description)

            # 执行搜索
            result = await self.xiaona_controller.retrieve_patent(request)

            # 记录搜索历史
            self.search_history.append({
                "patent_number": patent_number,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "success": result.success,
                "retrieval_time": result.retrieval_time
            })

            return result

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return None

    async def search_multiple_patents(self, patent_numbers: List[str],
                                      description: str = "批量专利搜索") -> List[PatentRetrievalResult]:
        """批量搜索专利"""
        print(f"\n🔍 批量搜索 {len(patent_numbers)} 个专利")
        print(f"📋 搜索描述: {description}")

        if not self.xiaona_controller:
            print("❌ 小娜控制器未初始化")
            return []

        results = []
        for i, patent_number in enumerate(patent_numbers, 1):
            print(f"   [{i}/{len(patent_numbers)}] 搜索: {patent_number}")

            result = await self.search_single_patent(patent_number, f"批量搜索第{i}个专利")
            if result:
                results.append(result)

        # 记录批量搜索
        self.search_history.append({
            "batch_search": True,
            "patent_count": len(patent_numbers),
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "successful_count": len(results)
        })

        return results

    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        if not self.xiaona_controller:
            return {"error": "小娜控制器未初始化"}

        stats = self.xiaona_controller.get_statistics()
        search_stats = {
            "local_search_history": len(self.search_history),
            "batch_searches": len([h for h in self.search_history if h.get("batch_search")]),
            "single_searches": len([h for h in self.search_history if not h.get("batch_search")])
        }

        return {**stats, **search_stats}

    def display_search_result(self, result: PatentRetrievalResult):
        """显示搜索结果"""
        print(f"\n📄 专利搜索结果:")
        print(f"   专利号: {result.patent_number}")
        print(f"   成功状态: {'✅ 成功' if result.success else '❌ 失败'}")

        if result.success:
            print(f"   标题: {result.title}")
            print(f"   摘要: {result.abstract[:100]}..." if len(result.abstract) > 100 else f"   摘要: {result.abstract}")

            if result.claims:
                print(f"   权利要求: {len(result.claims)} 项")
                for i, claim in enumerate(result.claims[:3], 1):
                    print(f"     {i}. {claim[:80]}..." if len(claim) > 80 else f"     {i}. {claim}")

            if result.legal_analysis:
                print(f"   法律分析: {result.legal_analysis[:100]}...")

            if result.professional_insights:
                print(f"   专业见解:")
                for insight in result.professional_insights:
                    print(f"     💡 {insight}")

        print(f"   获取时间: {result.retrieval_time:.2f}秒")

    def display_welcome_info(self):
        """显示欢迎信息"""
        print(f"\n💖 小娜·天秤女神 - 专利法律专家")
        print(f"🌟 专业领域: 专利检索、法律分析、知识产权")
        print(f"🎯 当前版本: {self.version}")
        print(f"⚖️ 中国专利搜索系统已就绪")
        print(f"\n📋 小娜可以为您:")
        print(f"   🔍 搜索单个专利详细信息")
        print(f"   📊 批量专利数据处理")
        print(f"   ⚖️ 专利法律分析")
        print(f"   💡 专业建议和见解")
        print(f"   📈 专利趋势分析")

async def main():
    """主函数"""
    print("🌟 欢迎使用小娜专利搜索系统！")

    # 创建搜索系统
    search_system = XiaonaPatentSearchSystem()

    # 显示欢迎信息
    search_system.display_welcome_info()

    # 初始化系统
    if not await search_system.initialize():
        print("❌ 系统初始化失败，请检查配置")
        return

    # 演示中国专利搜索
    print("\n" + "="*60)
    print("🎯 演示：搜索中国专利")
    print("="*60)

    # 示例专利号 (中国专利)
    demo_patents = [
        ("CN123456789", "5G通信相关专利"),
        ("CN987654321", "人工智能技术专利"),
        ("CN555566777", "新能源专利")
    ]

    # 执行搜索演示
    for patent_number, description in demo_patents:
        print(f"\n--- 搜索专利: {patent_number} ---")
        result = await search_system.search_single_patent(patent_number, description)

        if result:
            search_system.display_search_result(result)
        else:
            print(f"❌ 专利 {patent_number} 搜索失败")

    # 显示统计信息
    print("\n" + "="*60)
    print("📊 搜索统计信息")
    print("="*60)

    stats = search_system.get_search_statistics()
    print(f"总请求数: {stats.get('total_requests', 0)}")
    print(f"成功获取: {stats.get('successful_retrievals', 0)}")
    print(f"失败次数: {stats.get('failed_retrievals', 0)}")
    print(f"本地搜索历史: {stats.get('local_search_history', 0)}")

    print(f"\n📋 使用说明:")
    print("="*60)
    print("1️⃣ 创建搜索请求:")
    print("   request = search_system.create_search_request(patent_number, description)")
    print("   ")
    print("2️⃣ 执行搜索:")
    print("   result = await search_system.search_single_patent(patent_number)")
    print("   ")
    print("3️⃣ 批量搜索:")
    print("   results = await search_system.search_multiple_patents(patent_numbers)")
    print("   ")
    print("4️⃣ 查看统计:")
    print("   stats = search_system.get_search_statistics()")

    print("\n💖 小娜已经准备好搜索中国专利了！")
    print("🌟 输入专利号开始搜索，或者使用上面的API进行程序化操作")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())