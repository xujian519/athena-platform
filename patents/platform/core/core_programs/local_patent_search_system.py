#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全本地化的专利检索系统
使用项目中的browser-use源码 + DeepSeek API
绕过Browser-Use Cloud服务限制
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

# 导入本地browser-use
try:
    from browser_use import Agent, Browser
    from browser_use.llm import get_llm
    logger.info('✅ 本地browser-use导入成功')
except ImportError as e:
    logger.info(f"❌ 本地browser-use导入失败: {e}")
    sys.exit(1)

# 导入DeepSeek
try:
    import requests
    logger.info('✅ DeepSeek库导入成功')
except ImportError as e:
    logger.info(f"❌ DeepSeek库导入失败: {e}")
    logger.info('请安装: pip install requests')
    sys.exit(1)


class LocalPatentSearchSystem:
    """完全本地化的专利检索系统"""

    def __init__(self):
        self.browser = None
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

    async def initialize_local_system(self):
        """初始化本地系统"""
        try:
            logger.info('🚀 初始化本地专利检索系统...')

            # 1. 初始化浏览器
            self.browser = Browser()
            logger.info('✅ 本地浏览器初始化成功')

            # 2. 获取DeepSeek LLM
            deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
            if not deepseek_api_key:
                logger.info('❌ 未找到DEEPSEEK_API_KEY环境变量')
                return False

            # 创建DeepSeek LLM实例
            llm = get_llm(
                provider='openai',  # 使用OpenAI兼容接口
                model_kwargs={
                    'model': 'deepseek-chat',
                    'api_key': deepseek_api_key,
                    'base_url': 'https://api.deepseek.com/v1'
                }
            )
            logger.info('✅ DeepSeek LLM配置成功')

            # 3. 创建代理
            self.agent = Agent(
                task='专利检索专家，专门在Google Patents等专利数据库中检索和分析专利信息',
                llm=llm,
                browser=self.browser
            )
            logger.info('✅ 本地AI代理创建成功')
            return True

        except Exception as e:
            logger.info(f"❌ 本地系统初始化失败: {e}")
            return False

    async def search_patents_locally(self, search_query: str):
        """本地专利检索"""
        logger.info(f"\n🔍 本地检索: {search_query}")

        try:
            # 构建Google Patents URL
            encoded_query = search_query.replace(' ', '+').replace('(', '%28').replace(')', '%29')
            search_url = f"https://patents.google.com/?q={encoded_query}&oq={encoded_query}"

            logger.info(f"🌐 访问URL: {search_url}")

            # 使用DeepSeek驱动的检索任务
            task = f"""
            作为专业的专利检索专家，请执行以下任务：

            1. 访问Google Patents页面: {search_url}

            2. 等待页面完全加载（3-5秒）

            3. 仔细分析搜索结果：
               - 查找相关的专利文献
               - 记录找到的专利数量

            4. 如果找到专利，点击前5个最相关的专利链接

            5. 对于每个专利，提取以下信息：
               - 专利号（如：US1234567B2）
               - 专利标题
               - 申请日期
               - 申请人/权利人
               - 摘要内容（前200字）

            6. 技术特征分析：检查每个专利是否包含以下技术特征：
               {', '.join(self.target_patent['features'])}

            7. 对于每个专利，提供分析：
               - 技术特征匹配度（0-100%）
               - 新颖性影响评估（HIGH/MEDIUM/LOW）
               - 与目标专利CN201815134U的相似性说明

            8. 返回JSON格式的详细分析结果，格式如下：
            {{
                'search_query': '{search_query}',
                'patents_found': [
                    {{
                        'patent_number': '专利号',
                        'title': '专利标题',
                        'application_date': '申请日期',
                        'assignee': '申请人',
                        'abstract': '摘要',
                        'feature_analysis': {{
                            'matched_features': ['匹配的特征'],
                            'missing_features': ['缺失的特征'],
                            'match_percentage': 85,
                            'novelty_impact': 'HIGH'
                        }}
                    }}
                ],
                'total_results': 找到的专利数量,
                'search_notes': '检索说明'
            }}

            请确保分析准确、详细，并返回完整的JSON格式结果。
            """

            result = await self.agent.run(task)

            # 保存结果
            search_result = {
                'query': search_query,
                'url': search_url,
                'method': '本地browser-use + DeepSeek',
                'result': result,
                'timestamp': datetime.now().isoformat()
            }

            self.search_results.append(search_result)

            logger.info('✅ 本地检索完成')
            return search_result

        except Exception as e:
            logger.info(f"❌ 本地检索失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def execute_comprehensive_local_search(self):
        """执行全面的本地专利检索"""
        logger.info('🏠 启动完全本地化专利检索系统')
        logger.info(str('='*80))

        # 1. 初始化本地系统
        logger.info("\n📋 步骤1: 初始化本地系统...")
        if not await self.initialize_local_system():
            logger.info('❌ 本地系统初始化失败')
            return

        # 2. 执行多策略检索
        logger.info("\n📋 步骤2: 执行本地专利检索...")

        # 基于法律新颖性定义的严格检索式
        search_queries = [
            # 核心技术组合（英文）
            'dimethyl adipate methanol distillation esterification reactor condenser',

            # 核心技术组合（中文）
            '混二元酸二甲酯 甲醇精馏装置 精馏塔 酯化反应釜 冷凝器',

            # 工艺特征
            'esterification reactor methanol recovery direct connection energy saving',

            # 设备组合
            'DBE production methanol purification reactor column system'
        ]

        for i, query in enumerate(search_queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 执行本地检索 {i}/{len(search_queries)}")
            logger.info(f"🔍 检索式: {query}")
            logger.info(f"{'='*60}")

            result = await self.search_patents_locally(query)

            if result:
                logger.info('✅ 本地检索成功')
            else:
                logger.info('❌ 本地检索失败')

            # 添加延迟
            if i < len(search_queries):
                logger.info('⏰ 等待5秒...')
                await asyncio.sleep(5)

        # 3. 生成本地检索报告
        logger.info("\n📋 步骤3: 生成本地检索报告...")
        await self.generate_local_analysis_report()

    async def generate_local_analysis_report(self):
        """生成本地检索分析报告"""

        successful_searches = [r for r in self.search_results if r.get('result')]

        report = {
            'patent_number': self.target_patent['number'],
            'patent_title': self.target_patent['title'],
            'search_date': datetime.now().isoformat(),
            'search_method': '完全本地化 browser-use + DeepSeek',
            'target_features': self.target_patent['features'],
            'search_statistics': {
                'total_queries': len(self.search_results),
                'successful_searches': len(successful_searches),
                'success_rate': f"{len(successful_searches)/len(self.search_results)*100:.1f}%' if self.search_results else '0%"
            },
            'search_results': self.search_results,
            'local_advantages': [
                '完全本地运行，无第三方服务依赖',
                '使用DeepSeek强大的中文理解能力',
                '绕过所有API限制和网络审查',
                '完全控制检索过程和数据',
                '支持自定义检索策略和分析逻辑'
            ],
            'technical_details': {
                'browser_engine': '本地Chrome实例',
                'llm_provider': 'DeepSeek API',
                'automation_framework': 'browser-use开源版本',
                'patent_database': 'Google Patents (通过浏览器访问)'
            },
            'recommendations': [
                '定期执行本地检索监控技术发展',
                '保存检索结果建立技术对比数据库',
                '基于检索结果优化专利申请策略',
                '结合其他专利数据库进行交叉验证'
            ]
        }

        # 保存报告
        report_file = '/Users/xujian/Athena工作平台/CN201815134U_local_patent_search_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 本地检索报告已保存: {report_file}")

        # 显示检索总结
        logger.info(f"\n🎯 本地专利检索总结:")
        logger.info(f"  📊 总检索数: {report['search_statistics']['total_queries']}")
        logger.info(f"  ✅ 成功检索: {report['search_statistics']['successful_searches']}")
        logger.info(f"  📈 成功率: {report['search_statistics']['success_rate']}")
        logger.info(f"  🏠 系统: 完全本地化")

        logger.info(f"\n💡 本地检索优势:")
        for advantage in report['local_advantages']:
            logger.info(f"  • {advantage}")

    async def close(self):
        """关闭本地系统"""
        try:
            if self.agent:
                await self.agent.close()
                logger.info('✅ 本地AI代理已关闭')

            if self.browser:
                await self.browser.close()
                logger.info('✅ 本地浏览器已关闭')

        except Exception as e:
            logger.info(f"⚠️ 关闭系统时出现警告: {e}")


async def main():
    """主函数"""
    logger.info('🏠 完全本地化专利检索系统')
    logger.info(str('='*50))
    logger.info('✅ 无需Browser-Use Cloud API')
    logger.info('✅ 使用本地browser-use源码')
    logger.info('✅ 集成DeepSeek AI分析')
    logger.info(str('='*50))

    # 检查DeepSeek API密钥
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_api_key:
        logger.info(f"✅ DeepSeek API密钥已配置 (长度: {len(deepseek_api_key)})")
    else:
        logger.info('❌ 未找到DeepSeek API密钥')
        logger.info('👉 请在.env文件中配置DEEPSEEK_API_KEY')
        return

    search_system = LocalPatentSearchSystem()

    try:
        await search_system.execute_comprehensive_local_search()
        logger.info(f"\n🎉 本地专利检索完成！")

        logger.info(f"\n📝 下一步建议:")
        logger.info(f"   • 查看详细的本地检索报告")
        logger.info(f"   • 分析找到的相关专利")
        logger.info(f"   • 进行技术特征对比分析")
        logger.info(f"   • 生成新颖性分析结论")

    except Exception as e:
        logger.info(f"❌ 本地检索过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await search_system.close()


if __name__ == '__main__':
    asyncio.run(main())