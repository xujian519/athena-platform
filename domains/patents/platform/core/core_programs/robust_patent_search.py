#!/usr/bin/env python3
"""
鲁棒性专利检索系统
专注解决API超时问题 + 提供专业专利分析
"""

import json
import logging
import os
import socket
import time
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()


class RobustPatentSearch:
    """鲁棒性专利检索系统"""

    def __init__(self):
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.search_results = []

        # 目标专利
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

    def test_network_connection(self):
        """测试网络连接"""
        try:
            # 测试基本连接
            socket.create_connection(('api.deepseek.com', 443), timeout=5)
            logger.info('✅ 网络连接正常')
            return True
        except Exception as e:
            logger.info(f"❌ 网络连接失败: {e}")
            return False

    def call_deepseek_with_retry(self, prompt: str, max_retries=5):
        """带有重试和回退机制的DeepSeek API调用"""

        # API配置
        url = 'https://api.deepseek.com/v1/chat/completions'
        headers = {
            'Authorization': f"Bearer {self.deepseek_api_key}",
            'Content-Type': 'application/json'
        }

        # 多种配置尝试
        configs = [
            {
                'model': 'deepseek-chat',
                'temperature': 0.1,
                'max_tokens': 1500,
                'timeout': 15
            },
            {
                'model': 'deepseek-chat',
                'temperature': 0.1,
                'max_tokens': 800,
                'timeout': 10
            }
        ]

        for config_idx, config in enumerate(configs):
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 尝试配置 {config_idx+1}/{len(configs)}, 第 {attempt+1} 次调用...")

                    payload = {
                        'model': config['model'],
                        'messages': [
                            {
                                'role': 'system',
                                'content': '你是一位专业的专利检索和分析专家，具有丰富的化学工程背景知识。请提供准确、专业的专利技术分析。'
                            },
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ],
                        'temperature': config['temperature'],
                        'max_tokens': config['max_tokens']
                    }

                    # 设置超时
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=config['timeout'],
                        verify=True  # SSL验证
                    )

                    response.raise_for_status()
                    result = response.json()

                    logger.info('✅ DeepSeek API调用成功')
                    return result['choices'][0]['message']['content']

                except requests.exceptions.Timeout:
                    logger.info(f"⏰ 超时 (配置{config_idx+1}, 尝试{attempt+1})")
                    if attempt < max_retries - 1:
                        # 递增等待时间
                        wait_time = 2 ** attempt + config_idx * 2
                        logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        if config_idx < len(configs) - 1:
                            logger.info('🔄 尝试下一个配置...')
                            break
                        else:
                            raise Exception('所有配置和重试均失败')

                except requests.exceptions.ConnectionError as e:
                    logger.info(f"🔌 连接错误: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    else:
                        if config_idx < len(configs) - 1:
                            break
                        else:
                            raise e

                except Exception as e:
                    logger.info(f"❌ 其他错误: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        if config_idx < len(configs) - 1:
                            break
                        else:
                            raise e

        raise Exception('所有API调用尝试均失败')

    def analyze_patent_novelty(self, search_query: str):
        """分析专利新颖性"""
        logger.info(f"\n🔍 分析查询: {search_query}")

        # 构建专业分析提示
        prompt = f"""
        作为专利检索专家，请对以下技术进行专业的新颖性分析：

        **目标专利信息:**
        - 专利号: {self.target_patent['number']}
        - 标题: {self.target_patent['title']}
        - 核心技术特征: {', '.join(self.target_patent['features'])}

        **检索查询:**
        {search_query}

        **专业分析要求:**
        请基于您的专利专业知识库，对该技术领域进行深入分析：

        1. **技术领域分析**
           - 该技术领域的现有技术水平
           - 主要技术路线和解决方案
           - 行业技术发展趋势

        2. **潜在冲突专利分析**
           - 可能存在的新颖性冲突点
           - 需要重点关注的现有技术
           - 可能的等同技术方案

        3. **新颖性评估**
           - 目标专利的技术创新点
           - 与现有技术的差异化
           - 新颖性前景评估

        4. **检索策略建议**
           - 推荐的检索式优化
           - 需要重点检索的技术方向
           - 检索关键词建议

        请以JSON格式返回专业分析结果：
        {{
            'technical_analysis': {{
                'field_assessment': '技术领域评估',
                'existing_solutions': ['现有解决方案'],
                'industry_trends': '行业发展趋势'
            }},
            'potential_conflicts': [
                {{
                    'technology_area': '技术领域',
                    'conflict_probability': 'HIGH/MEDIUM/LOW',
                    'key_concerns': ['关注要点'],
                    'mitigation_strategies': ['缓解策略']
                }}
            ],
            'novelty_assessment': {{
                'innovation_points': ['创新点'],
                'technical_differentiation': '技术差异化',
                'novelty_level': 'HIGH/MEDIUM/LOW',
                'confidence': 0.85,
                'key_advantages': ['主要优势']
            }},
            'search_strategy': {{
                'optimized_queries': ['优化检索式'],
                'focus_areas': ['重点关注领域'],
                'keyword_suggestions': ['关键词建议']
            }}
        }}
        """

        try:
            analysis_result = self.call_deepseek_with_retry(prompt)

            # 保存结果
            search_result = {
                'query': search_query,
                'analysis': analysis_result,
                'timestamp': datetime.now().isoformat(),
                'method': 'DeepSeek专业知识库分析'
            }

            self.search_results.append(search_result)
            logger.info('✅ 专业分析完成')
            return search_result

        except Exception as e:
            logger.info(f"❌ 分析失败: {e}")
            # 保存失败记录
            failed_result = {
                'query': search_query,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'status': 'failed'
            }
            self.search_results.append(failed_result)
            return failed_result

    def run_comprehensive_analysis(self):
        """运行综合专利分析"""
        logger.info('🤖 启动鲁棒性专利检索分析系统')
        logger.info(str('='*60))
        logger.info('✅ 专注解决网络超时问题')
        logger.info('✅ 提供专业专利分析')
        logger.info(str('='*60))

        # 检查API密钥
        if not self.deepseek_api_key:
            logger.info('❌ 请配置DEEPSEEK_API_KEY')
            return

        logger.info(f"✅ DeepSeek API密钥已配置 (长度: {len(self.deepseek_api_key)})")

        # 测试网络连接
        if not self.test_network_connection():
            logger.info('⚠️ 网络连接存在问题，但将继续尝试...')

        # 综合分析查询
        analysis_queries = [
            '混二元酸二甲酯生产中甲醇精馏装置的整体技术方案',
            '酯化反应釜与精馏塔直接连通的甲醇回收工艺',
            '化工生产中反应器与精馏塔气相直连节能技术',
            'dimethyl adipate methanol distillation esterification integration',
            'DBE生产中甲醇纯化和回收的反应器-精馏塔系统'
        ]

        success_count = 0

        # 执行分析
        for i, query in enumerate(analysis_queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 专业分析 {i}/{len(analysis_queries)}")
            logger.info(f"{'='*60}")

            result = self.analyze_patent_novelty(query)

            if result and 'error' not in result:
                success_count += 1
                logger.info('✅ 分析成功')
            else:
                logger.info('❌ 分析失败')

            # 添加间隔
            if i < len(analysis_queries):
                logger.info('⏰ 等待3秒...')
                time.sleep(3)

        # 生成综合报告
        self.generate_comprehensive_report(success_count)

    def generate_comprehensive_report(self, success_count):
        """生成综合分析报告"""
        logger.info("\n📋 生成综合分析报告...")

        # 统计信息
        total_queries = len(self.search_results)
        successful_analyses = len([r for r in self.search_results if r.get('analysis')])
        failed_analyses = total_queries - successful_analyses

        report = {
            'patent_number': self.target_patent['number'],
            'patent_title': self.target_patent['title'],
            'analysis_date': datetime.now().isoformat(),
            'method': 'DeepSeek专业知识库分析 (鲁棒性版本)',
            'target_features': self.target_patent['features'],
            'analysis_statistics': {
                'total_queries': total_queries,
                'successful_analyses': successful_analyses,
                'failed_analyses': failed_analyses,
                'success_rate': f"{successful_analyses/total_queries*100:.1f}%' if total_queries > 0 else '0%"
            },
            'search_results': self.search_results,
            'system_improvements': [
                '多配置重试机制，提高API调用成功率',
                '网络连接测试和自适应超时',
                '专业专利分析提示词优化',
                '鲁棒性错误处理和恢复'
            ],
            'professional_insights': self.extract_professional_insights(),
            'recommendations': [
                '基于成功分析结果优化专利申请策略',
                '在专业数据库中验证关键技术点',
                '准备应对可能的审查意见',
                '持续监控技术领域发展'
            ]
        }

        # 保存报告
        report_file = '/Users/xujian/Athena工作平台/CN201815134U_robust_patent_analysis_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 综合分析报告已保存: {report_file}")

        # 显示总结
        logger.info("\n🎯 鲁棒性专利分析总结:")
        logger.info(f"  📊 总查询数: {report['analysis_statistics']['total_queries']}")
        logger.info(f"  ✅ 成功分析: {report['analysis_statistics']['successful_analyses']}")
        logger.info(f"  ❌ 失败分析: {report['analysis_statistics']['failed_analyses']}")
        logger.info(f"  📈 成功率: {report['analysis_statistics']['success_rate']}")
        logger.info("  🔧 方法: DeepSeek专业知识库分析")

        logger.info("\n💡 系统改进:")
        for improvement in report['system_improvements']:
            logger.info(f"  • {improvement}")

    def extract_professional_insights(self):
        """提取专业见解"""
        insights = []
        successful_results = [r for r in self.search_results if r.get('analysis')]

        for result in successful_results:
            try:
                if isinstance(result['analysis'], str):
                    insights.append({
                        'query': result['query'],
                        'key_points': result['analysis'][:200] + '...' if len(result['analysis']) > 200 else result['analysis']
                    })
            except:
                continue

        return insights


def main():
    """主函数"""
    logger.info('🤖 鲁棒性专利检索分析系统')
    logger.info(str('='*50))

    # 检查API密钥
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_api_key:
        logger.info('❌ 未找到DEEPSEEK_API_KEY环境变量')
        logger.info('👉 请在.env文件中配置DEEPSEEK_API_KEY')
        return

    logger.info(f"✅ DeepSeek API密钥已配置 (长度: {len(deepseek_api_key)})")

    # 创建分析系统
    search_system = RobustPatentSearch()

    try:
        # 运行综合分析
        search_system.run_comprehensive_analysis()

        logger.info("\n🎉 鲁棒性专利分析完成！")
        logger.info("\n📄 查看详细报告:")
        logger.info("   CN201815134U_robust_patent_analysis_report.json")

        # 提供后续建议
        logger.info("\n📝 后续建议:")
        logger.info("   1. 基于成功分析结果优化专利申请")
        logger.info("   2. 在专业数据库中验证关键技术点")
        logger.info("   3. 准备应对审查意见的技术论证")
        logger.info("   4. 持续监控相关技术发展")

    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断分析")
    except Exception as e:
        logger.info(f"\n❌ 分析过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
