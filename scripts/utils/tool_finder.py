#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena平台工具快速查找器
Athena Platform Tool Finder

根据用户需求快速推荐合适的工具和工作流

使用方法:
python scripts_new/utils/tool_finder.py --scene '专利检索'
python scripts_new/utils/tool_finder.py --keyword '审查意见'
python scripts_new/utils/tool_finder.py --list

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import argparse
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 工具数据库
TOOL_DATABASE = {
    '专利检索': {
        'primary_tools': [
            'patent_crawler.py',
            'patent_retrieval_workflow.py',
            'enhanced_patent_perception.py'
        ],
        'supporting_tools': [
            'vector_search_engine.py',
            'knowledge_graph_builder.py',
            'search_coordinator.py'
        ],
        'workflow': '专利检索工作流',
        'estimated_time': '30-60分钟'
    },

    '审查意见答复': {
        'primary_tools': [
            'patent_professional_workflow.py',
            'comprehensive_patent_processor.py',
            'enhanced_patent_perception.py'
        ],
        'supporting_tools': [
            'patent_judgment_kg_api.py',
            'patent_legal_vector_api.py',
            'chemical_analyzer.py'
        ],
        'workflow': '专利专业工作流',
        'estimated_time': '2-4小时'
    },

    '专利撰写': {
        'primary_tools': [
            'patent_professional_workflow.py',
            'patent_ai_agent.py',
            'document_generator.py'
        ],
        'supporting_tools': [
            'patent_knowledge_graph_builder.py',
            'technical_analyzer.py',
            'quality_checker.py'
        ],
        'workflow': '专利撰写工作流',
        'estimated_time': '4-8小时'
    },

    '侵权分析': {
        'primary_tools': [
            'patent_professional_workflow.py',
            'patent_judgment_kg_api.py',
            'patent_crawler.py'
        ],
        'supporting_tools': [
            'vector_search_engine.py',
            'legal_analyzer.py',
            'similarity_calculator.py'
        ],
        'workflow': '侵权分析工作流',
        'estimated_time': '1-2小时'
    },

    '技术评估': {
        'primary_tools': [
            'technical_analyzer.py',
            'patent_ai_agent.py',
            'super_reasoning_engine.py'
        ],
        'supporting_tools': [
            'knowledge_graph_builder.py',
            'decision_engine.py',
            'domain_expert_system.py'
        ],
        'workflow': '技术评估流程',
        'estimated_time': '30-90分钟'
    },

    '创意写作': {
        'primary_tools': [
            'xiaonuo_enhanced.py',
            'creative_writing_tool.py',
            'story_generator.py'
        ],
        'supporting_tools': [
            'text_processor.py',
            'nlp_service.py',
            'knowledge_recommender.py'
        ],
        'workflow': '创意写作流程',
        'estimated_time': '15-30分钟'
    },

    '系统监控': {
        'primary_tools': [
            'platform_manager.py',
            'health_monitor.py',
            'performance_monitor.py'
        ],
        'supporting_tools': [
            'log_analyzer.py',
            'metric_collector.py',
            'alert_system.py'
        ],
        'workflow': '系统监控流程',
        'estimated_time': '实时'
    },

    '数据分析': {
        'primary_tools': [
            'multimodal_processor.py',
            'vector_search_engine.py',
            'data_analyzer.py'
        ],
        'supporting_tools': [
            'statistical_analyzer.py',
            'visualizer.py',
            'report_generator.py'
        ],
        'workflow': '数据分析流程',
        'estimated_time': '30-120分钟'
    }
}

# 关键词映射
KEYWORD_MAPPING = {
    '检索': '专利检索',
    '搜索': '专利检索',
    '查新': '专利检索',
    '现有技术': '专利检索',

    '审查意见': '审查意见答复',
    '答复': '审查意见答复',
    '补正': '审查意见答复',
    '修改': '审查意见答复',

    '撰写': '专利撰写',
    '申请': '专利撰写',
    '权利要求': '专利撰写',

    '侵权': '侵权分析',
    'FTO': '侵权分析',
    '自由实施': '侵权分析',

    '评估': '技术评估',
    '分析': '技术评估',
    '评价': '技术评估',

    '写作': '创意写作',
    '创作': '创意写作',
    '故事': '创意写作',
    '文案': '创意写作',

    '监控': '系统监控',
    '健康检查': '系统监控',
    '性能': '系统监控',

    '数据': '数据分析',
    '统计': '数据分析',
    '报告': '数据分析'
}

class ToolFinder:
    """工具查找器"""

    def __init__(self):
        self.tool_db = TOOL_DATABASE
        self.keyword_map = KEYWORD_MAPPING

    def find_tools_by_scene(self, scene: str) -> Dict[str, Any]:
        """根据场景查找工具"""
        # 标准化场景名称
        scene = self._normalize_scene(scene)

        if scene in self.tool_db:
            return self.tool_db[scene]
        else:
            # 尝试关键词匹配
            for keyword, mapped_scene in self.keyword_map.items():
                if keyword in scene:
                    return self.tool_db[mapped_scene]

            return {
                'primary_tools': ['athena_agent.py', 'xiaonuo_agent.py'],
                'supporting_tools': ['text_processor.py', 'search_engine.py'],
                'workflow': '通用处理流程',
                'estimated_time': '10-30分钟',
                'suggestion': f"未找到精确匹配的场景'{scene}'，使用通用工具处理"
            }

    def find_tools_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """根据关键词查找相关工具"""
        results = []

        for scene, tools in self.tool_db.items():
            if keyword.lower() in scene.lower():
                results.append({
                    'scene': scene,
                    'tools': tools,
                    'match_type': '场景匹配'
                })
            else:
                # 检查工具名称
                all_tools = tools['primary_tools'] + tools['supporting_tools']
                for tool in all_tools:
                    if keyword.lower() in tool.lower():
                        results.append({
                            'scene': scene,
                            'tools': tools,
                            'match_type': '工具匹配'
                        })
                        break

        return results

    def _normalize_scene(self, scene: str) -> str:
        """标准化场景名称"""
        # 移除空格和特殊字符
        scene = scene.strip().lower()

        # 关键词映射
        for keyword, mapped_scene in self.keyword_map.items():
            if keyword in scene:
                return mapped_scene

        return scene

    def list_all_scenes(self) -> List[str]:
        """列出所有可用场景"""
        return list(self.tool_db.keys())

    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具详细信息"""
        tool_info = {
            'name': tool_name,
            'category': '未分类',
            'usage_scenes': [],
            'description': '工具信息待补充',
            'dependencies': [],
            'file_path': ''
        }

        # 在所有场景中查找该工具
        for scene, tools in self.tool_db.items():
            if tool_name in tools['primary_tools']:
                tool_info['category'] = '主要工具'
                tool_info['usage_scenes'].append(scene)
            elif tool_name in tools['supporting_tools']:
                tool_info['category'] = '辅助工具'
                tool_info['usage_scenes'].append(scene)

        return tool_info

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena平台工具快速查找器')
    parser.add_argument('--scene', '-s', help='指定场景')
    parser.add_argument('--keyword', '-k', help='搜索关键词')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有场景')
    parser.add_argument('--info', '-i', help='获取工具详细信息')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出')

    args = parser.parse_args()

    finder = ToolFinder()

    if args.list:
        scenes = finder.list_all_scenes()
        logger.info("\n🎯 Athena平台可用场景:")
        logger.info(str('=' * 50))
        for i, scene in enumerate(scenes, 1):
            logger.info(f"{i:2d}. {scene}")

        logger.info(f"\n总计: {len(scenes)} 个场景")
        return

    if args.info:
        tool_info = finder.get_tool_info(args.info)
        logger.info(f"\n🔧 工具信息: {tool_info['name']}")
        logger.info(str('=' * 50))
        logger.info(f"类别: {tool_info['category']}")
        logger.info(f"使用场景: {', '.join(tool_info['usage_scenes']) if tool_info['usage_scenes'] else '无'}")
        logger.info(f"描述: {tool_info['description']}")
        return

    if args.scene:
        result = finder.find_tools_by_scene(args.scene)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info(f"\n🎯 场景: {args.scene}")
            logger.info(str('=' * 50))

            if 'suggestion' in result:
                logger.info(f"⚠️  {result['suggestion']}")
                print()

            logger.info(f"⏱️  预估时间: {result['estimated_time']}")
            logger.info(f"🔄 工作流程: {result['workflow']}")
            print()

            logger.info('🔧 主要工具:')
            for tool in result['primary_tools']:
                logger.info(f"  ✅ {tool}")

            logger.info("\n🔧 辅助工具:")
            for tool in result['supporting_tools']:
                logger.info(f"  ⚙️  {tool}")
        return

    if args.keyword:
        results = finder.find_tools_by_keyword(args.keyword)

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            logger.info(f"\n🔍 关键词 '{args.keyword}' 搜索结果:")
            logger.info(str('=' * 50))

            if not results:
                logger.info('未找到匹配的工具或场景')
                return

            for i, result in enumerate(results, 1):
                logger.info(f"\n{i}. {result['scene']} ({result['match_type']})")
                logger.info(f"   主要工具: {', '.join(result['tools']['primary_tools'][:3])}")
                if len(result['tools']['primary_tools']) > 3:
                    logger.info(f"   等 {len(result['tools']['primary_tools'])} 个工具")
        return

    # 默认显示使用帮助
    logger.info("\n🎯 Athena工具查找器")
    logger.info(str('=' * 30))
    logger.info('使用示例:')
    logger.info("  python tool_finder.py --scene '专利检索'")
    logger.info("  python tool_finder.py --keyword '审查意见'")
    logger.info('  python tool_finder.py --list')
    logger.info("  python tool_finder.py --info 'patent_crawler.py'")
    logger.info("\n参数说明:")
    logger.info('  --scene, -s     : 指定场景')
    logger.info('  --keyword, -k  : 搜索关键词')
    logger.info('  --list, -l     : 列出所有场景')
    logger.info('  --info, -i     : 获取工具信息')
    logger.info('  --json        : JSON格式输出')

if __name__ == '__main__':
    main()