#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek直接专利检索系统
使用DeepSeek API分析 + 直接HTTP请求
绕过所有浏览器依赖
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()


class DeepSeekDirectPatentSearch:
    """DeepSeek直接专利检索系统"""

    def __init__(self):
        self.search_results = []
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')

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

    def call_deepseek_api(self, prompt: str):
        """调用DeepSeek API"""
        try:
            url = 'https://api.deepseek.com/v1/chat/completions'
            headers = {
                'Authorization': f"Bearer {self.deepseek_api_key}",
                'Content-Type': 'application/json'
            }

            payload = {
                'model': 'deepseek-chat',
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一位专业的专利检索专家，具有丰富的化学工程和专利分析经验。请准确分析技术特征，提供专业的专利检索建议。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 2000
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']

        except Exception as e:
            logger.info(f"❌ DeepSeek API调用失败: {e}")
            return None

    def search_patent_literature(self, query: str):
        """使用DeepSeek进行专利文献分析"""
        logger.info(f"\n🔍 DeepSeek分析: {query}")

        # 构建专业的专利检索提示
        prompt = f"""
        作为专利检索专家，请分析以下技术领域的现有专利情况：

        **目标专利信息：**
        - 专利号：{self.target_patent['number']}
        - 标题：{self.target_patent['title']}
        - 技术特征：{', '.join(self.target_patent['features'])}

        **检索查询：** {query}

        **分析任务：**
        1. 基于你的专业知识，分析该技术领域可能存在的现有专利
        2. 识别可能与目标专利构成冲突的对比文件
        3. 评估检索查询的技术特征覆盖度
        4. 提供改进的检索策略建议

        **输出格式：**
        请返回JSON格式的分析结果：
        {{
            'query_analysis': {{
                'technical_field': '技术领域',
                'key_concepts': ['关键概念列表'],
                'search_coverage': '检索覆盖度评估',
                'improved_queries': ['改进的检索式']
            }},
            'potential_prior_art': [
                {{
                    'patent_number': '可能的专利号',
                    'title': '专利标题',
                    'publication_date': '公开日期',
                    'assignee': '申请人',
                    'technology_description': '技术描述',
                    'feature_overlap': '技术特征重叠分析',
                    'novelty_impact': 'HIGH/MEDIUM/LOW'
                }}
            ],
            'novelty_assessment': {{
                'novelty_level': 'HIGH/MEDIUM/LOW',
                'confidence': 0.85,
                'key_concerns': ['主要关注点'],
                'recommendations': ['建议']
            }}
        }}

        请基于你的专利数据库知识提供专业分析，即使找不到具体的专利号，也要提供技术领域的一般性分析。
        """

        # 调用DeepSeek API
        result = self.call_deepseek_api(prompt)

        if result:
            # 保存结果
            search_result = {
                'query': query,
                'analysis': result,
                'timestamp': datetime.now().isoformat()
            }

            self.search_results.append(search_result)
            logger.info('✅ DeepSeek分析完成')
            return search_result
        else:
            logger.info('❌ DeepSeek分析失败')
            return None

    def run_comprehensive_analysis(self):
        """运行综合分析"""
        logger.info('🤖 启动DeepSeek直接专利检索系统')
        logger.info(str('='*50))
        logger.info('✅ 直接API调用，无浏览器依赖')
        logger.info('✅ 基于DeepSeek专业专利知识库')
        logger.info(str('='*50))

        if not self.deepseek_api_key:
            logger.info('❌ 请配置DEEPSEEK_API_KEY')
            return

        # 多角度分析查询
        analysis_queries = [
            '混二元酸二甲酯生产中的甲醇精馏装置技术',
            '酯化反应釜与精馏塔直接连通的甲醇回收工艺',
            'dimethyl adipate methanol distillation esterification reactor',
            'DBE production methanol recovery integrated reactor-column system',
            '化工生产中反应器与精馏塔气相直连节能技术'
        ]

        # 执行分析
        for i, query in enumerate(analysis_queries, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"🔄 DeepSeek分析 {i}/{len(analysis_queries)}")
            logger.info(f"{'='*50}")

            self.search_patent_literature(query)

        # 生成综合报告
        self.generate_comprehensive_report()

    def generate_comprehensive_report(self):
        """生成综合分析报告"""
        logger.info("\n📋 生成DeepSeek综合分析报告...")

        # 统计信息
        total_analyses = len(self.search_results)
        successful_analyses = len([r for r in self.search_results if r.get('analysis')])

        report = {
            'patent_number': self.target_patent['number'],
            'patent_title': self.target_patent['title'],
            'analysis_date': datetime.now().isoformat(),
            'method': 'DeepSeek API直接分析',
            'target_features': self.target_patent['features'],
            'analysis_statistics': {
                'total_queries': total_analyses,
                'successful_analyses': successful_analyses,
                'success_rate': f"{successful_analyses/total_analyses*100:.1f}%' if total_analyses > 0 else '0%"
            },
            'deepseek_analyses': self.search_results,
            'method_advantages': [
                '直接调用DeepSeek API，无浏览器限制',
                '基于DeepSeek的专业专利知识库',
                '快速响应，无需浏览器启动',
                '可以分析技术领域的整体专利态势',
                '提供专业的检索策略建议'
            ],
            'limitations': [
                '依赖DeepSeek的知识库截止日期',
                '无法获取最新的专利实时信息',
                '需要人工验证具体专利的存在性'
            ],
            'next_steps': [
                '使用分析结果优化传统检索策略',
                '在专业专利数据库中验证关键专利',
                '委托专利检索机构进行正式查新',
                '基于分析结果完善专利申请文件'
            ]
        }

        # 保存报告
        report_file = '/Users/xujian/Athena工作平台/CN201815134U_deepseek_direct_analysis_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 DeepSeek分析报告已保存: {report_file}")

        # 显示分析总结
        logger.info(f"\n🎯 DeepSeek分析总结:")
        logger.info(f"  📊 总分析数: {report['analysis_statistics']['total_queries']}")
        logger.info(f"  ✅ 成功分析: {report['analysis_statistics']['successful_analyses']}")
        logger.info(f"  📈 成功率: {report['analysis_statistics']['success_rate']}")
        logger.info(f"  🤖 方法: DeepSeek API直接分析")

        logger.info(f"\n💡 分析优势:")
        for advantage in report['method_advantages']:
            logger.info(f"  • {advantage}")

        logger.info(f"\n📝 后续建议:")
        for step in report['next_steps']:
            logger.info(f"  • {step}")


def main():
    """主函数"""
    logger.info('🤖 DeepSeek直接专利检索系统')
    logger.info(str('='*50))

    # 检查API密钥
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_api_key:
        logger.info('❌ 未找到DEEPSEEK_API_KEY环境变量')
        logger.info('👉 请在.env文件中配置DEEPSEEK_API_KEY')
        return

    logger.info(f"✅ DeepSeek API密钥已配置 (长度: {len(deepseek_api_key)})")

    # 创建分析系统
    search_system = DeepSeekDirectPatentSearch()

    try:
        # 运行综合分析
        search_system.run_comprehensive_analysis()

        logger.info(f"\n🎉 DeepSeek专利分析完成！")
        logger.info(f"\n📄 查看详细报告:")
        logger.info(f"   CN201815134U_deepseek_direct_analysis_report.json")

    except KeyboardInterrupt:
        logger.info(f"\n⏹️ 用户中断分析")
    except Exception as e:
        logger.info(f"\n❌ 分析过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()