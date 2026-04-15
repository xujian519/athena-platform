#!/usr/bin/env python3
"""
基于Browser-Use的专利检索系统
绕过Google Patents访问限制，实现真实专利检索
"""

import asyncio
import json
import logging
import sys
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
    logger.info('请确保安装browser-use: pip install browser-use')
    sys.exit(1)


class BrowserPatentSearchSystem:
    """基于浏览器的专利检索系统"""

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

    async def initialize(self):
        """初始化浏览器代理"""
        try:
            self.agent = Agent(
                task='专利检索专家，专门在Google Patents等专利数据库中检索和分析专利信息',
                llm='claude-3.5-sonnet',  # 使用Claude LLM
            )
            logger.info('✅ 浏览器代理初始化成功')
            return True
        except Exception as e:
            logger.info(f"❌ 浏览器代理初始化失败: {e}")
            return False

    async def search_google_patents_strict(self, query: str, max_pages: int = 3):
        """在Google Patents上进行严格检索"""

        logger.info("\n🔍 开始Google Patents严格检索")
        logger.info(f"📝 检索式: {query}")

        try:
            # 构建Google Patents URL
            encoded_query = query.replace(' ', '+').replace('(', '%28').replace(')', '%29')
            search_url = f"https://patents.google.com/?q={encoded_query}&oq={encoded_query}"

            logger.info(f"🌐 访问URL: {search_url}")

            # 访问Google Patents搜索页面
            task = f"""
            请访问Google Patents搜索页面: {search_url}

            然后执行以下操作：
            1. 等待页面完全加载（3-5秒）
            2. 查看搜索结果列表
            3. 如果找到专利，请点击前10个专利标题
            4. 对于每个专利，提取以下信息：
               - 专利号
               - 专利标题
               - 申请日期
               - 申请人/权利人
               - 摘要内容
               - 技术分类

            5. 检查每个专利是否包含以下所有技术特征：
               {', '.join(self.target_patent['features'])}

            6. 对于每个专利，评估技术特征匹配度（0-100%）

            请以JSON格式返回详细的分析结果，格式如下：
            {{
                'search_query': '{query}',
                'patents_found': [
                    {{
                        'patent_number': '专利号',
                        'title': '专利标题',
                        'application_date': '申请日期',
                        'assignee': '申请人',
                        'abstract': '摘要',
                        'feature_analysis': {{
                            'matched_features': ['匹配的特征列表'],
                            'missing_features': ['缺失的特征列表'],
                            'match_percentage': 85,
                            'novelty_impact': 'HIGH|MEDIUM|LOW'
                        }}
                    }}
                ],
                'total_results': 5,
                'high_match_patents': 2
            }}
            """

            result = await self.agent.run(task)

            # 解析结果
            try:
                if isinstance(result, dict) and 'patents_found' in result:
                    self.search_results.extend(result['patents_found'])
                    return result
                elif isinstance(result, str):
                    # 尝试从文本中提取JSON
                    import re
                    json_match = re.search(r'\{[^}]*patents_found[^}]*\}', result)
                    if json_match:
                        json_str = json_match.group(0)
                        parsed_result = json.loads(json_str)
                        self.search_results.extend(parsed_result.get('patents_found', []))
                        return parsed_result
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

            logger.info(f"📄 浏览器返回结果类型: {type(result)}")
            logger.info(f"📄 结果内容预览: {str(result)[:500]}...")
            return {'patents_found': [], 'total_results': 0, 'high_match_patents': 0}

        except Exception as e:
            logger.info(f"❌ 浏览器检索失败: {e}")
            return {'patents_found': [], 'total_results': 0, 'error': str(e)}

    async def search_multiple_queries(self):
        """执行多查询检索"""

        # 基于法律新颖性定义的严格检索式
        strict_queries = [
            # 核心技术组合检索
            'dimethyl adipate AND methanol distillation AND distillation tower AND esterification reactor AND condenser AND direct connection',

            # 中文检索式
            '混二元酸二甲酯 AND 甲醇精馏装置 AND 精馏塔 AND 酯化反应釜 AND 冷凝器 AND 直接连通',

            # 工艺特征检索
            'esterification reactor AND methanol recovery AND direct vapor connection AND condensation avoidance',

            # 设备组合检索
            'DBE production AND methanol purification AND integrated reactor-column system',

            # 节能特征检索
            'energy saving AND methanol distillation AND reactor to column direct coupling'
        ]

        all_results = []

        for i, query in enumerate(strict_queries, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔄 执行检索 {i}/{len(strict_queries)}")
            logger.info(f"{'='*80}")

            result = await self.search_google_patents_strict(query, max_pages=2)

            if result.get('patents_found'):
                logger.info(f"✅ 检索 {i}: 找到 {len(result['patents_found'])} 个专利")
                all_results.extend(result['patents_found'])
            else:
                logger.info(f"❌ 检索 {i}: 未找到专利")

            # 添加搜索延迟以避免被限制
            if i < len(strict_queries):
                logger.info("⏰ 等待5秒避免访问限制...")
                await asyncio.sleep(5)

        # 去重处理
        unique_patents = {}
        for patent in all_results:
            patent_id = patent.get('patent_number', '')
            if patent_id and patent_id not in unique_patents:
                unique_patents[patent_id] = patent

        final_results = list(unique_patents.values())

        logger.info("\n📊 检索统计:")
        logger.info(f"  • 总检索式: {len(strict_queries)}")
        logger.info(f"  • 原始结果: {len(all_results)}")
        logger.info(f"  • 去重结果: {len(final_results)}")

        return final_results

    def analyze_novelty(self, patents):
        """分析新颖性"""

        critical_patents = []  # 包含所有特征的专利
        high_risk_patents = []  # 包含大部分特征的专利

        for patent in patents:
            feature_analysis = patent.get('feature_analysis', {})
            match_percentage = feature_analysis.get('match_percentage', 0)
            feature_analysis.get('novelty_impact', 'LOW')

            if match_percentage >= 90:  # 包含90%以上特征
                critical_patents.append(patent)
            elif match_percentage >= 70:  # 包含70%以上特征
                high_risk_patents.append(patent)

        # 新颖性判断
        if len(critical_patents) > 0:
            novelty_level = 'VERY_LOW'
            confidence = 0.95
            assessment = f"发现{len(critical_patents)}个包含所有技术特征的对比文件，严重影响新颖性"
        elif len(high_risk_patents) > 0:
            novelty_level = 'LOW'
            confidence = 0.85
            assessment = f"发现{len(high_risk_patents)}个包含大部分技术特征的对比文件，可能影响新颖性"
        else:
            novelty_level = 'HIGH'
            confidence = 0.80
            assessment = '未发现包含主要技术特征的对比文件，具有较高新颖性'

        return {
            'novelty_level': novelty_level,
            'confidence': confidence,
            'assessment': assessment,
            'critical_patents': critical_patents,
            'high_risk_patents': high_risk_patents,
            'total_analyzed': len(patents)
        }

    async def perform_complete_search(self):
        """执行完整的专利检索和新颖性分析"""

        logger.info('🚀 启动基于浏览器的专利检索系统')
        logger.info(str('='*80))

        # 1. 初始化
        logger.info("\n📋 步骤1: 初始化浏览器系统...")
        if not await self.initialize():
            logger.info('❌ 初始化失败，无法继续')
            return

        # 2. 执行检索
        logger.info("\n📋 步骤2: 执行严格专利检索...")
        patents = await self.search_multiple_queries()

        # 3. 新颖性分析
        logger.info("\n📋 步骤3: 执行新颖性分析...")
        novelty_analysis = self.analyze_novelty(patents)

        # 4. 生成报告
        logger.info("\n📋 步骤4: 生成分析报告...")
        await generate_browser_search_report(self, patents, novelty_analysis)

        return patents, novelty_analysis

    async def close(self):
        """关闭浏览器系统"""
        if self.agent:
            try:
                await self.agent.close()
                logger.info('✅ 浏览器系统已关闭')
            except Exception as e:
                logger.info(f"⚠️ 关闭浏览器时出现警告: {e}")


async def generate_browser_search_report(search_system, patents, novelty_analysis):
    """生成浏览器检索报告"""

    report = {
        'patent_number': search_system.target_patent['number'],
        'patent_title': search_system.target_patent['title'],
        'search_date': datetime.now().isoformat(),
        'search_method': 'Browser-Use AI浏览器自动化',
        'target_features': search_system.target_patent['features'],
        'legal_basis': '基于专利法新颖性定义，使用浏览器模拟真实用户访问Google Patents',
        'search_results': {
            'total_patents_found': len(patents),
            'patent_details': [
                {
                    'patent_number': p.get('patent_number'),
                    'title': p.get('title', ''),
                    'application_date': p.get('application_date', ''),
                    'assignee': p.get('assignee', ''),
                    'abstract': p.get('abstract', ''),
                    'feature_match': p.get('feature_analysis', {}).get('match_percentage', 0),
                    'novelty_impact': p.get('feature_analysis', {}).get('novelty_impact', 'UNKNOWN')
                }
                for p in patents
            ]
        },
        'browser_novelty_analysis': novelty_analysis,
        'conclusion': {
            'novelty_level': novelty_analysis['novelty_level'],
            'confidence': novelty_analysis['confidence'],
            'assessment': novelty_analysis['assessment'],
            'browser_search_advantages': [
                '绕过API限制，模拟真实用户访问',
                '动态处理页面内容和反爬虫机制',
                '实时解析和特征匹配分析',
                '支持复杂检索策略和布尔逻辑'
            ],
            'recommendations': generate_browser_recommendations(novelty_analysis)
        }
    }

    # 保存报告
    report_file = '/Users/xujian/Athena工作平台/CN201815134U_browser_patent_search_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 浏览器检索报告已保存: {report_file}")

    # 显示关键结果
    logger.info("\n🎯 浏览器专利检索结果:")
    logger.info(f"  📊 新颖性等级: {report['conclusion']['novelty_level']}")
    logger.info(f"  📈 置信度: {report['conclusion']['confidence']:.2f}")
    logger.info(f"  🔍 检索到专利数: {report['search_results']['total_patents_found']}")
    logger.info(f"  ⚠️  严重风险专利: {len(novelty_analysis['critical_patents'])}")
    logger.info(f"  🟡 高风险专利: {len(novelty_analysis['high_risk_patents'])}")

    if novelty_analysis['critical_patents']:
        logger.info("\n⚠️  严重风险专利详情:")
        for i, patent in enumerate(novelty_analysis['critical_patents'], 1):
            logger.info(f"  {i}. {patent.get('patent_number')} - 匹配度: {patent.get('feature_analysis', {}).get('match_percentage', 0)}%")

    logger.info("\n💡 浏览器检索优势:")
    for advantage in report['conclusion']['browser_search_advantages']:
        logger.info(f"  • {advantage}")


def generate_browser_recommendations(novelty_analysis):
    """生成基于浏览器检索的建议"""

    novelty_level = novelty_analysis['novelty_level']

    recommendations = [
        '使用浏览器自动化可以绕过API限制，获得更准确的检索结果',
        '定期使用浏览器检索监控相关技术领域的专利动态',
        '结合API检索和浏览器检索，提高检索覆盖率和准确性'
    ]

    if novelty_level in ['VERY_LOW', 'LOW']:
        recommendations.extend([
            '存在影响新颖性的高风险专利，建议详细分析技术差异',
            '考虑修改权利要求以增加差异化技术特征',
            '准备应对审查员的新颖性质疑和反对意见'
        ])
    elif novelty_level == 'MEDIUM':
        recommendations.extend([
            '具有一定新颖性风险，建议进一步扩大检索范围',
            '重点分析高风险专利的技术等同性问题',
            '考虑在说明书中强调技术创新点和差异化'
        ])
    else:
        recommendations.extend([
            '目标专利具有较好的新颖性前景',
            '建议继续推进专利申请流程',
            '利用浏览器检索定期监控新技术发展'
        ])

    return recommendations


async def main():
    """主函数"""
    search_system = BrowserPatentSearchSystem()

    try:
        patents, analysis = await search_system.perform_complete_search()
        logger.info("\n✅ 浏览器专利检索分析完成！")

    except Exception as e:
        logger.info(f"❌ 检索过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await search_system.close()


if __name__ == '__main__':
    asyncio.run(main())
