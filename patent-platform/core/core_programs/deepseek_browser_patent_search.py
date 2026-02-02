#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于DeepSeek API的浏览器专利检索系统
绕过Google Patents访问限制，实现真实专利检索
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'projects' / 'browser-use-main'))

try:
    from browser_use import Agent
    logger.info('✅ Browser-Use导入成功')
except ImportError as e:
    logger.info(f"❌ Browser-Use导入失败: {e}")
    sys.exit(1)


class DeepSeekBrowserPatentSearch:
    """基于DeepSeek API的浏览器专利检索系统"""

    def __init__(self):
        self.agent = None
        self.search_results = []

        # 目标专利技术特征
        self.target_patent = {
            'number': 'CN201815134U',
            'title': '混二元酸二甲酯生产中的甲醇精馏装置',
            'features': [
                '混二元酸二甲酯生产',
                '甲醇精馏装置',
                '精馏塔',
                '酯化反应釜',
                '冷凝器',
                '直接连通',
                '气相连接',
                '节能工艺'
            ]
        }

    async def initialize_with_deepseek(self):
        """使用DeepSeek API初始化浏览器代理"""
        try:
            # 设置环境变量
            deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
            if not deepseek_api_key:
                logger.info('❌ 未找到DEEPSEEK_API_KEY环境变量')
                return False

            # 使用DeepSeek API创建代理
            self.agent = Agent(
                task='专利检索专家，专门在Google Patents等专利数据库中检索和分析专利信息',
                llm_config={
                    'provider': 'deepseek',
                    'api_key': deepseek_api_key,
                    'model': 'deepseek-chat'  # DeepSeek的聊天模型
                }
            )
            logger.info('✅ DeepSeek浏览器代理初始化成功')
            return True

        except Exception as e:
            logger.info(f"❌ DeepSeek浏览器代理初始化失败: {e}")
            # 尝试使用默认配置
            try:
                self.agent = Agent(
                    task='专利检索专家，专门在Google Patents等专利数据库中检索和分析专利信息'
                )
                logger.info('✅ 默认浏览器代理初始化成功')
                return True
            except Exception as e2:
                logger.info(f"❌ 默认浏览器代理初始化也失败: {e2}")
                return False

    async def search_patent_with_deepseek(self, search_query: str):
        """使用DeepSeek代理进行专利检索"""

        logger.info(f"\n🔍 DeepSeek检索: {search_query}")

        try:
            # 构建Google Patents URL
            encoded_query = search_query.replace(' ', '+').replace('(', '%28').replace(')', '%29')
            search_url = f"https://patents.google.com/?q={encoded_query}&oq={encoded_query}"

            logger.info(f"🌐 访问URL: {search_url}")

            # 使用DeepSeek驱动的检索任务
            task = f"""
            作为专利检索专家，请访问Google Patents页面: {search_url}

            执行以下专利检索任务：
            1. 等待页面完全加载（3-5秒）
            2. 分析搜索结果，查找相关专利
            3. 如果找到专利，点击前5个最相关的专利
            4. 提取每个专利的详细信息：
               - 专利号
               - 专利标题
               - 申请日期
               - 申请人/权利人
               - 摘要内容

            5. 技术特征分析 - 检查每个专利是否包含以下特征：
               {', '.join(self.target_patent['features'])}

            6. 对于每个专利，评估：
               - 技术特征匹配度（0-100%）
               - 新颖性影响（HIGH/MEDIUM/LOW）
               - 与目标专利的技术相似性

            7. 返回JSON格式的详细分析结果，包含所有找到的专利信息和技术对比

            请使用您的专业知识进行深入分析，确保检索结果的准确性和完整性。
            """

            result = await self.agent.run(task)

            # 保存结果
            search_result = {
                'query': search_query,
                'url': search_url,
                'llm_provider': 'DeepSeek',
                'result': result,
                'timestamp': datetime.now().isoformat()
            }

            self.search_results.append(search_result)

            logger.info('✅ DeepSeek检索完成')
            return search_result

        except Exception as e:
            logger.info(f"❌ DeepSeek检索失败: {e}")
            return None

    async def execute_comprehensive_search(self):
        """执行全面的专利检索"""

        logger.info('🚀 启动DeepSeek浏览器专利检索系统')
        logger.info(str('='*80))

        # 1. 初始化DeepSeek代理
        logger.info("\n📋 步骤1: 初始化DeepSeek浏览器代理...")
        if not await self.initialize_with_deepseek():
            logger.info('❌ 代理初始化失败')
            return

        # 2. 执行多策略检索
        logger.info("\n📋 步骤2: 执行多策略专利检索...")

        # 基于法律新颖性定义的严格检索式
        strict_search_queries = [
            # 核心技术组合检索（英文）
            'dimethyl adipate AND methanol distillation AND distillation tower AND esterification reactor AND condenser',

            # 核心技术组合检索（中文）
            '混二元酸二甲酯 AND 甲醇精馏装置 AND 精馏塔 AND 酯化反应釜 AND 冷凝器',

            # 工艺特征检索
            'esterification reactor AND methanol recovery AND direct vapor connection AND energy saving',

            # 设备组合检索
            'DBE production AND methanol purification AND integrated reactor-column system',

            # 节能特征检索
            'energy saving AND methanol distillation AND reactor to column direct coupling'
        ]

        for i, query in enumerate(strict_search_queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 执行DeepSeek检索 {i}/{len(strict_search_queries)}")
            logger.info(f"🔍 检索式: {query}")
            logger.info(f"{'='*60}")

            result = await self.search_patent_with_deepseek(query)

            if result:
                logger.info('✅ 检索成功完成')
            else:
                logger.info('❌ 检索失败')

            # 添加延迟避免访问限制
            if i < len(strict_search_queries):
                logger.info('⏰ 等待5秒避免访问限制...')
                await asyncio.sleep(5)

        # 3. 生成分析报告
        logger.info("\n📋 步骤3: 生成DeepSeek检索分析报告...")
        await self.generate_deepseek_analysis_report()

    async def generate_deepseek_analysis_report(self):
        """生成DeepSeek检索分析报告"""

        # 分析检索结果
        successful_searches = [r for r in self.search_results if r.get('result')]

        report = {
            'patent_number': self.target_patent['number'],
            'patent_title': self.target_patent['title'],
            'search_date': datetime.now().isoformat(),
            'search_method': 'DeepSeek AI + Browser-Use 自动化',
            'llm_provider': 'DeepSeek',
            'target_features': self.target_patent['features'],
            'search_statistics': {
                'total_queries': len(self.search_results),
                'successful_searches': len(successful_searches),
                'success_rate': f"{len(successful_searches)/len(self.search_results)*100:.1f}%' if self.search_results else '0%"
            },
            'search_results': self.search_results,
            'deepseek_advantages': [
                'DeepSeek AI提供强大的中文理解能力',
                '专业的专利领域知识推理',
                '高效的技术特征匹配分析',
                '绕过API限制，模拟真实用户访问',
                '支持复杂的中英文混合检索'
            ],
            'recommendations': [
                '定期使用DeepSeek检索监控技术发展',
                '结合其他AI模型进行交叉验证',
                '手动验证关键检索结果的准确性',
                '基于检索结果优化专利申请策略'
            ]
        }

        # 保存报告
        report_file = '/Users/xujian/Athena工作平台/CN201815134U_deepseek_patent_search_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 DeepSeek检索报告已保存: {report_file}")

        # 显示检索总结
        logger.info(f"\n🎯 DeepSeek专利检索总结:")
        logger.info(f"  📊 总检索数: {report['search_statistics']['total_queries']}")
        logger.info(f"  ✅ 成功检索: {report['search_statistics']['successful_searches']}")
        logger.info(f"  📈 成功率: {report['search_statistics']['success_rate']}")
        logger.info(f"  🤖 AI提供商: DeepSeek")

        logger.info(f"\n💡 DeepSeek检索优势:")
        for advantage in report['deepseek_advantages']:
            logger.info(f"  • {advantage}")

    async def close(self):
        """关闭浏览器代理"""
        if self.agent:
            try:
                await self.agent.close()
                logger.info('✅ DeepSeek浏览器代理已关闭')
            except Exception as e:
                logger.info(f"⚠️ 关闭代理时出现警告: {e}")


async def main():
    """主函数"""
    logger.info('🤖 DeepSeek浏览器专利检索系统')
    logger.info(str('='*50))

    # 检查DeepSeek API密钥
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_api_key:
        logger.info(f"✅ DeepSeek API密钥已配置 (长度: {len(deepseek_api_key)})")
    else:
        logger.info('❌ 未找到DeepSeek API密钥')
        logger.info('👉 请在.env文件中配置DEEPSEEK_API_KEY')
        return

    search_system = DeepSeekBrowserPatentSearch()

    try:
        await search_system.execute_comprehensive_search()
        logger.info(f"\n✅ DeepSeek专利检索完成！")

        logger.info(f"\n📝 下一步建议:")
        logger.info(f"   • 查看生成的详细检索报告")
        logger.info(f"   • 分析找到的相关专利的技术特征")
        logger.info(f"   • 基于检索结果进行新颖性判断")
        logger.info(f"   • 使用DeepSeek的强大分析能力进行深度技术对比")

    except Exception as e:
        logger.info(f"❌ DeepSeek检索过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await search_system.close()


if __name__ == '__main__':
    asyncio.run(main())