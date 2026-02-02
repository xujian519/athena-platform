#!/usr/bin/env python3
"""
📋 专利规则分析工具
小诺的智能专利规则提取器

功能:
1. 查询专利规则向量库
2. 分析专利规则分类
3. 提取申请相关规则
4. 生成专利规则清单

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from loguru import logger

logger = logging.getLogger(__name__)

class PatentRuleAnalyzer:
    """专利规则分析器"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333'):
        self.qdrant_url = qdrant_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_all_patent_rules(self) -> List[Dict]:
        """获取所有专利规则"""
        try:
            all_rules = []
            scroll_data = {
                'limit': 1000,
                'with_payload': True,
                'with_vector': False
            }

            offset = None

            while True:
                if offset:
                    scroll_data['offset'] = offset

                response = await self.client.post(
                    f"{self.qdrant_url}/collections/patent_rules_unified_1024/points/scroll",
                    json=scroll_data
                )
                response.raise_for_status()

                result = response.json()['result']
                points = result.get('points', [])

                if not points:
                    break

                all_rules.extend(points)

                if len(points) < scroll_data['limit']:
                    break

                # 使用最后一个点的ID作为偏移
                offset = points[-1]['id']

                logger.info(f"已获取 {len(all_rules)} 条专利规则...")

            logger.info(f"专利规则获取完成，共 {len(all_rules)} 条")
            return all_rules

        except Exception as e:
            logger.error(f"获取专利规则失败: {e}")
            return []

    async def analyze_rule_categories(self, rules: List[Dict]) -> Dict:
        """分析专利规则分类"""
        categories = {}
        rule_types = {}
        application_stages = {}

        for rule in rules:
            payload = rule.get('payload', {})

            # 按类别分类
            category = payload.get('category', '未分类')
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': rule.get('id'),
                'rule_name': payload.get('rule_name', ''),
                'description': payload.get('description', '')
            })

            # 按类型分类
            rule_type = payload.get('rule_type', '未分类')
            if rule_type not in rule_types:
                rule_types[rule_type] = 0
            rule_types[rule_type] += 1

            # 按申请阶段分类
            stage = payload.get('application_stage', '')
            if stage and stage not in application_stages:
                application_stages[stage] = []
            if stage:
                application_stages[stage].append(payload.get('rule_name', ''))

        return {
            'categories': categories,
            'rule_types': rule_types,
            'application_stages': application_stages,
            'total_rules': len(rules)
        }

    async def extract_application_rules(self, rules: List[Dict]) -> Dict:
        """提取专利申请相关规则"""
        application_rules = []

        for rule in rules:
            payload = rule.get('payload', {})

            # 判断是否为申请相关规则
            is_application_rule = (
                '申请' in payload.get('rule_name', '') or
                'application' in payload.get('rule_name', '').lower() or
                'patent' in payload.get('rule_name', '').lower() or
                payload.get('application_stage') or
                payload.get('category') == '申请流程'
            )

            if is_application_rule:
                application_rules.append({
                    'id': rule.get('id'),
                    'rule_name': payload.get('rule_name', ''),
                    'rule_type': payload.get('rule_type', ''),
                    'category': payload.get('category', ''),
                    'application_stage': payload.get('application_stage', ''),
                    'description': payload.get('description', ''),
                    'requirements': payload.get('requirements', []),
                    'steps': payload.get('steps', []),
                    'key_points': payload.get('key_points', [])
                })

        return {
            'total_application_rules': len(application_rules),
            'rules': application_rules
        }

    def generate_rule_summary(self, analysis: Dict, application_rules: Dict) -> Dict:
        """生成规则摘要"""
        total_rules = analysis['total_rules']
        application_count = application_rules['total_application_rules']

        return {
            'summary': {
                'total_patent_rules': total_rules,
                'application_related_rules': application_count,
                'application_ratio': f"{(application_count/total_rules)*100:.1f}%' if total_rules > 0 else '0%",
                'categories_count': len(analysis['categories']),
                'rule_types_count': len(analysis['rule_types'])
            },
            'categories_overview': {
                category: len(rules) for category, rules in analysis['categories'].items()
            },
            'rule_types_overview': analysis['rule_types'],
            'application_stages': analysis['application_stages']
        }

    async def generate_patent_application_guide(self, application_rules: Dict) -> Dict:
        """生成专利申请指南"""
        rules = application_rules['rules']

        # 按申请阶段分组
        stages = {}
        for rule in rules:
            stage = rule.get('application_stage', '通用规则')
            if stage not in stages:
                stages[stage] = []
            stages[stage].append(rule)

        # 生成申请指南
        guide = {
            'title': '发明专利申请指南',
            'subtitle': f"基于 {len(rules)} 条专利规则",
            'generated_time': datetime.now().isoformat(),
            'application_stages': {},
            'key_checkpoints': [],
            'common_requirements': [],
            'recommended_steps': []
        }

        # 为每个阶段生成指南
        for stage_name, stage_rules in stages.items():
            guide['application_stages'][stage_name] = {
                'stage_name': stage_name,
                'rules_count': len(stage_rules),
                'key_rules': [
                    {
                        'name': rule['rule_name'],
                        'description': rule['description'][:200] + '...' if len(rule['description']) > 200 else rule['description'],
                        'requirements': rule.get('requirements', []),
                        'key_points': rule.get('key_points', [])
                    }
                    for rule in stage_rules[:5]  # 每个阶段最多5条关键规则
                ]
            }

            # 提取关键检查点
            for rule in stage_rules:
                if rule.get('key_points'):
                    guide['key_checkpoints'].extend(rule['key_points'])

                if rule.get('requirements'):
                    guide['common_requirements'].extend(rule['requirements'])

        # 去重
        guide['key_checkpoints'] = list(set(guide['key_checkpoints']))[:10]
        guide['common_requirements'] = list(set(guide['common_requirements']))[:15]

        return guide

    async def analyze_patent_rules(self) -> Dict:
        """执行专利规则分析"""
        logger.info('🔍 开始分析专利规则向量库')

        # 1. 获取所有专利规则
        logger.info('获取专利规则数据...')
        all_rules = await self.get_all_patent_rules()

        if not all_rules:
            return {'error': '无法获取专利规则数据'}

        # 2. 分析规则分类
        logger.info('分析规则分类...')
        analysis = await self.analyze_rule_categories(all_rules)

        # 3. 提取申请相关规则
        logger.info('提取专利申请相关规则...')
        application_rules = await self.extract_application_rules(all_rules)

        # 4. 生成规则摘要
        logger.info('生成规则摘要...')
        summary = self.generate_rule_summary(analysis, application_rules)

        # 5. 生成申请指南
        logger.info('生成专利申请指南...')
        guide = await self.generate_patent_application_guide(application_rules)

        # 6. 整合结果
        result = {
            'analysis_time': datetime.now().isoformat(),
            'vector_database_info': {
                'collection': 'patent_rules_unified_1024',
                'total_vectors': len(all_rules),
                'vector_dimension': 1024
            },
            'analysis': analysis,
            'application_rules': application_rules,
            'summary': summary,
            'application_guide': guide
        }

        logger.info(f"专利规则分析完成: {len(all_rules)} 条规则，{application_rules['total_application_rules']} 条申请相关")
        return result

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

async def main():
    """主函数"""
    analyzer = PatentRuleAnalyzer()

    try:
        # 执行分析
        result = await analyzer.analyze_patent_rules()

        # 显示结果
        logger.info(str('='*60))
        logger.info('📋 专利规则向量库分析结果')
        logger.info(str('='*60))

        summary = result['summary']
        logger.info(f"📊 数据统计:")
        logger.info(f"  总专利规则数: {summary['total_patent_rules']:,}")
        logger.info(f"  申请相关规则: {summary['application_related_rules']}")
        logger.info(f"  申请规则占比: {summary['application_ratio']}")
        logger.info(f"  规则类别数: {summary['categories_count']}")
        logger.info(f"  规则类型数: {summary['rule_types_count']}")

        logger.info(f"\n🎯 申请相关规则详情:")
        application_rules = result['application_rules']['rules']
        for i, rule in enumerate(application_rules[:10], 1):  # 显示前10条
            logger.info(f"  {i}. {rule['rule_name']}")
            logger.info(f"     类型: {rule['rule_type']}")
            logger.info(f"     阶段: {rule['application_stage']}")
            if rule['description']:
                desc = rule['description'][:100] + '...' if len(rule['description']) > 100 else rule['description']
                logger.info(f"     描述: {desc}")
            print()

        if len(application_rules) > 10:
            logger.info(f"  ... 还有 {len(application_rules) - 10} 条规则")

        # 显示规则类别分布
        logger.info(f"\n📂 规则类别分布:")
        for category, count in summary['categories_overview'].items():
            logger.info(f"  • {category}: {count} 条规则")

        # 显示规则类型分布
        logger.info(f"\n🏷️ 规则类型分布:")
        for rule_type, count in summary['rule_types_overview'].items():
            logger.info(f"  • {rule_type}: {count} 条规则")

        # 显示申请阶段
        if summary['application_stages']:
            logger.info(f"\n⏰ 申请阶段:")
            for stage, rules in summary['application_stages'].items():
                logger.info(f"  • {stage}: {len(rules)} 条规则")

        # 保存详细报告
        output_file = '.runtime/patent_rules_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 详细分析报告已保存到: {output_file}")

        # 保存申请指南
        guide_file = '.runtime/patent_application_guide.json'
        with open(guide_file, 'w', encoding='utf-8') as f:
            json.dump(result['application_guide'], f, ensure_ascii=False, indent=2)

        logger.info(f"📖 专利申请指南已保存到: {guide_file}")

    except Exception as e:
        logger.error(f"分析过程出错: {e}")
        logger.info(f"❌ 分析失败: {e}")
    finally:
        await analyzer.close()

if __name__ == '__main__':
    asyncio.run(main())