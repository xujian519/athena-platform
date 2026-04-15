#!/usr/bin/env python3
"""
IPC分类系统
IPC Classification System

提供IPC分类查询、匹配和新颖性分析支持
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IPCClassification:
    """IPC分类信息"""
    code: str
    name: str
    section: str
    class_code: str | None = None
    subclass: str | None = None
    group: str | None = None
    subgroup: str | None = None
    level: str = 'unknown'  # section, class, subclass, group, subgroup
    keywords: list[str] | None = None
    examples: list[str] | None = None
    domain: str = 'unknown'

@dataclass
class IPCMatchResult:
    """IPC匹配结果"""
    matched_codes: list[IPCClassification]
    confidence_scores: list[float]
    matching_keywords: list[list[str]]
    analysis_summary: str
    novelty_implications: dict[str, Any]

class IPCClassificationSystem:
    """IPC分类系统"""

    def __init__(self, ipc_data_path: str | None = None):
        self.ipc_data_path = ipc_data_path or \
            '/Users/xujian/Athena工作平台/patent-platform/workspace/data/ipc_classification_knowledge.json'
        self.ipc_data: dict[str, Any] = {}
        self.code_index: dict[str, IPCClassification] = {}
        self.keyword_index: dict[str, list[IPCClassification]] = defaultdict(list)
        self.domain_index: dict[str, list[IPCClassification]] = defaultdict(list)
        self.is_loaded = False

    def load_ipc_data(self):
        """加载IPC分类数据"""
        try:
            with open(self.ipc_data_path, encoding='utf-8') as f:
                self.ipc_data = json.load(f)

            # 构建索引
            self._build_indices()

            self.is_loaded = True
            logger.info(f"✅ IPC分类数据加载成功，共{len(self.code_index)}个分类")

        except FileNotFoundError:
            logger.error(f"❌ IPC数据文件不存在: {self.ipc_data_path}")
            self._load_default_ipc_data()
        except Exception as e:
            logger.error(f"❌ IPC数据加载失败: {e}")
            self._load_default_ipc_data()

    def _build_indices(self):
        """构建IPC分类索引"""
        # 处理部级别
        sections = self.ipc_data.get('ipc_sections', {})
        for section_code, section_data in sections.items():
            ipc_class = IPCClassification(
                code=section_code,
                name=section_data['name'],
                section=section_code,
                level='section',
                keywords=[],
                examples=[],
                domain=self._map_section_to_domain(section_code)
            )
            self.code_index[section_code] = ipc_class

            # 处理子类
            subclasses = section_data.get('subclasses', {})
            for subclass_code, subclass_name in subclasses.items():
                subclass_ipc = IPCClassification(
                    code=subclass_code,
                    name=subclass_name,
                    section=section_code,
                    class_code=subclass_code[:3] if len(subclass_code) >= 3 else None,
                    subclass=subclass_code,
                    level='subclass',
                    keywords=self.ipc_data.get('technical_keywords', {}).get(subclass_code, {}).get('keywords', []),
                    examples=self.ipc_data.get('technical_keywords', {}).get(subclass_code, {}).get('examples', []),
                    domain=self._map_subclass_to_domain(subclass_code)
                )
                self.code_index[subclass_code] = subclass_ipc

                # 构建关键词索引
                for keyword in subclass_ipc.keywords:
                    self.keyword_index[keyword.lower()].append(subclass_ipc)

                # 构建领域索引
                self.domain_index[subclass_ipc.domain].append(subclass_ipc)

    def _load_default_ipc_data(self):
        """加载默认IPC数据（简化版）"""
        logger.warning('⚠️ 使用默认IPC数据')
        default_ipc = {
            'A': {'name': '人类生活必需', 'subclasses': {'A61': '医学；兽医学；卫生学'}},
            'G': {'name': '物理', 'subclasses': {'G06F': '电数字数据处理'}},
            'H': {'name': '电学', 'subclasses': {'H04L': '数字信息的传输'}}
        }
        self.ipc_data = {'ipc_sections': default_ipc}
        self._build_indices()

    def _map_section_to_domain(self, section_code: str) -> str:
        """映射部到领域"""
        mapping = {
            'A': 'human_necessities',
            'B': 'operations_transport',
            'C': 'chemistry_metallurgy',
            'D': 'textiles_paper',
            'E': 'fixed_constructions',
            'F': 'mechanical_engineering',
            'G': 'physics',
            'H': 'electricity'
        }
        return mapping.get(section_code, 'unknown')

    def _map_subclass_to_domain(self, subclass_code: str) -> str:
        """映射子类到领域"""
        domain_correlations = self.ipc_data.get('mapping_rules', {}).get('domain_correlations', {})

        for domain, codes in domain_correlations.items():
            if subclass_code in codes:
                return domain

        # 默认映射
        if subclass_code.startswith('A'):
            return 'medical'
        elif subclass_code.startswith('G'):
            if 'G06' in subclass_code:
                return 'software'
            return 'physics'
        elif subclass_code.startswith('H'):
            if 'H04' in subclass_code:
                return 'communication'
            return 'electronic'
        elif subclass_code.startswith('B'):
            return 'mechanical'
        elif subclass_code.startswith('C'):
            return 'chemical'

        return 'unknown'

    def search_ipc_by_code(self, code: str) -> IPCClassification | None:
        """根据IPC代码搜索"""
        # 精确匹配
        if code in self.code_index:
            return self.code_index[code]

        # 前缀匹配
        for ipc_code, ipc_class in self.code_index.items():
            if ipc_code.startswith(code) or code.startswith(ipc_code):
                return ipc_class

        return None

    def search_ipc_by_keywords(self, text: str, top_k: int = 5) -> list[tuple[IPCClassification, float]]:
        """根据关键词搜索IPC分类"""
        if not self.is_loaded:
            self.load_ipc_data()

        # 提取文本中的关键词
        text_lower = text.lower()
        matched_ipc_scores = defaultdict(float)

        # 关键词匹配
        for keyword, ipc_classes in self.keyword_index.items():
            if keyword in text_lower:
                for ipc_class in ipc_classes:
                    # 计算匹配分数
                    score = text_lower.count(keyword) * 0.1
                    matched_ipc_scores[ipc_class.code] += score

        # 技术术语匹配
        tech_terms = self._extract_technical_terms(text)
        for term in tech_terms:
            for ipc_code, ipc_class in self.code_index.items():
                if term.lower() in ipc_class.name.lower():
                    matched_ipc_scores[ipc_code] += 0.2

        # 排序并返回
        results = []
        for ipc_code, score in sorted(matched_ipc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            results.append((self.code_index[ipc_code], score))

        return results

    def _extract_technical_terms(self, text: str) -> list[str]:
        """提取技术术语"""
        # 使用正则表达式提取技术术语
        patterns = [
            r'深度学习|人工智能|机器学习|神经网络',
            r'算法|模型|系统|平台|框架',
            r'通信|网络|传输|信号',
            r'传感器|控制|处理|计算',
            r'诊断|治疗|医疗|医学',
            r'机械|加工|制造|设备',
            r'化学|合成|材料|化合物',
            r'电子|电路|芯片|半导体'
        ]

        terms = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.extend(matches)

        return list(set(terms))

    def match_patent_to_ipc(self, patent_text: str, title: str = '', abstract: str = '') -> IPCMatchResult:
        """将专利匹配到IPC分类"""
        if not self.is_loaded:
            self.load_ipc_data()

        # 组合所有文本
        full_text = f"{title} {abstract} {patent_text}".strip()

        # 关键词搜索
        keyword_matches = self.search_ipc_by_keywords(full_text, top_k=10)

        # 代码模式匹配
        code_pattern = r'\b([A-H]\d{2}[A-Z]?\d*\/?\d*)\b'
        found_codes = re.findall(code_pattern, full_text.upper())
        code_matches = []
        for code in found_codes:
            ipc_class = self.search_ipc_by_code(code)
            if ipc_class:
                code_matches.append((ipc_class, 1.0))

        # 合并结果
        all_matches = {}
        for ipc_class, score in keyword_matches + code_matches:
            if ipc_class.code in all_matches:
                all_matches[ipc_class.code] = (ipc_class, max(all_matches[ipc_class.code][1], score))
            else:
                all_matches[ipc_class.code] = (ipc_class, score)

        # 排序
        sorted_matches = sorted(all_matches.values(), key=lambda x: x[1], reverse=True)

        matched_codes = [match[0] for match in sorted_matches[:5]]
        confidence_scores = [match[1] for match in sorted_matches[:5]]

        # 匹配的关键词
        matching_keywords = []
        for ipc_class, _ in sorted_matches[:5]:
            keywords = []
            for keyword in ipc_class.keywords:
                if keyword.lower() in full_text.lower():
                    keywords.append(keyword)
            matching_keywords.append(keywords)

        # 分析摘要
        analysis_summary = self._generate_match_summary(matched_codes, confidence_scores)

        # 新颖性含义
        novelty_implications = self._analyze_novelty_implications(matched_codes)

        return IPCMatchResult(
            matched_codes=matched_codes,
            confidence_scores=confidence_scores,
            matching_keywords=matching_keywords,
            analysis_summary=analysis_summary,
            novelty_implications=novelty_implications
        )

    def _generate_match_summary(self, matched_codes: list[IPCClassification], scores: list[float]) -> str:
        """生成匹配摘要"""
        if not matched_codes:
            return '未找到匹配的IPC分类'

        summary_parts = []

        # 主要分类
        if scores[0] > 0.5:
            main_ipc = matched_codes[0]
            summary_parts.append(f"主要技术领域：{main_ipc.code} {main_ipc.name}")

        # 多领域分析
        sections = {ipc.section for ipc in matched_codes}
        if len(sections) > 1:
            summary_parts.append(f"涉及{len(sections)}个技术部：{', '.join(sorted(sections))}")

        # 置信度分析
        avg_confidence = np.mean(scores)
        if avg_confidence > 0.7:
            summary_parts.append('分类置信度：高')
        elif avg_confidence > 0.4:
            summary_parts.append('分类置信度：中等')
        else:
            summary_parts.append('分类置信度：低，建议人工确认')

        return '；'.join(summary_parts)

    def _analyze_novelty_implications(self, matched_codes: list[IPCClassification]) -> dict[str, Any]:
        """分析新颖性含义"""
        implications = {
            'technical_field_analysis': '',
            'search_strategy': '',
            'novelty_considerations': [],
            'comparable_domains': []
        }

        if not matched_codes:
            return implications

        # 技术领域分析
        main_ipc = matched_codes[0]
        implications['technical_field_analysis'] = f"主要技术领域：{main_ipc.section}部 {main_ipc.code}类"

        # 检索策略
        search_strategies = []
        for ipc in matched_codes[:3]:
            if ipc.keywords:
                search_strategies.append(f"{ipc.code}: {', '.join(ipc.keywords[:3])}")
        implications['search_strategy'] = '；'.join(search_strategies)

        # 新颖性考虑
        self.ipc_data.get('novelty_analysis_guidelines', {})

        if len(matched_codes) == 1:
            implications['novelty_considerations'].append('单一技术领域，需要重点关注技术特征的具体差异')
        else:
            sections = {ipc.section for ipc in matched_codes}
            if len(sections) > 1:
                implications['novelty_considerations'].append('跨领域技术，可能具有组合创新的新颖性')

        # 可比领域
        comparable = []
        for ipc in matched_codes:
            if ipc.domain != 'unknown':
                comparable.append(ipc.domain)
        implications['comparable_domains'] = list(set(comparable))

        return implications

    def compare_ipc_classes(self, code1: str, code2: str) -> dict[str, Any]:
        """比较两个IPC分类"""
        ipc1 = self.search_ipc_by_code(code1)
        ipc2 = self.search_ipc_by_code(code2)

        if not ipc1 or not ipc2:
            return {'error': '未找到指定的IPC分类'}

        comparison = {
            'ipc1': {
                'code': ipc1.code,
                'name': ipc1.name,
                'section': ipc1.section,
                'domain': ipc1.domain
            },
            'ipc2': {
                'code': ipc2.code,
                'name': ipc2.name,
                'section': ipc2.section,
                'domain': ipc2.domain
            },
            'similarity': self._calculate_ipc_similarity(ipc1, ipc2),
            'relationship': self._determine_ipc_relationship(ipc1, ipc2),
            'novelty_implications': self._get_comparison_novelty_implications(ipc1, ipc2)
        }

        return comparison

    def _calculate_ipc_similarity(self, ipc1: IPCClassification, ipc2: IPCClassification) -> float:
        """计算IPC相似度"""
        # 相同分类
        if ipc1.code == ipc2.code:
            return 1.0

        # 相同子类
        if ipc1.subclass and ipc1.subclass == ipc2.subclass:
            return 0.9

        # 相同大类
        if ipc1.class_code and ipc1.class_code == ipc2.class_code:
            return 0.7

        # 相同部
        if ipc1.section == ipc2.section:
            return 0.5

        # 相同领域
        if ipc1.domain == ipc2.domain and ipc1.domain != 'unknown':
            return 0.3

        # 不同领域但有技术重叠
        if set(ipc1.keywords) & set(ipc2.keywords):
            return 0.2

        return 0.1

    def _determine_ipc_relationship(self, ipc1: IPCClassification, ipc2: IPCClassification) -> str:
        """确定IPC关系"""
        if ipc1.code == ipc2.code:
            return '相同分类'
        elif ipc1.section == ipc2.section:
            return '同一技术部'
        elif ipc1.domain == ipc2.domain and ipc1.domain != 'unknown':
            return '相同技术领域'
        else:
            return '不同技术领域'

    def _get_comparison_novelty_implications(self, ipc1: IPCClassification, ipc2: IPCClassification) -> str:
        """获取比较的新颖性含义"""
        relationship = self._determine_ipc_relationship(ipc1, ipc2)

        implications_map = {
            '相同分类': '技术领域高度相关，需要仔细对比具体技术特征',
            '同一技术部': '技术领域相近，关注技术方案的具体应用和实现',
            '相同技术领域': '技术领域有重叠，分析技术方案的侧重点',
            '不同技术领域': '可能涉及跨领域创新，具有潜在新颖性'
        }

        return implications_map.get(relationship, '需要进一步分析技术方案的关联性')

    def get_ipc_statistics(self) -> dict[str, Any]:
        """获取IPC分类统计信息"""
        if not self.is_loaded:
            self.load_ipc_data()

        stats = {
            'total_ipc_classes': len(self.code_index),
            'sections': {},
            'domains': {},
            'levels': {}
        }

        # 部统计
        section_counts = defaultdict(int)
        for ipc in self.code_index.values():
            section_counts[ipc.section] += 1
        stats['sections'] = dict(section_counts)

        # 领域统计
        domain_counts = defaultdict(int)
        for ipc in self.code_index.values():
            domain_counts[ipc.domain] += 1
        stats['domains'] = dict(domain_counts)

        # 级别统计
        level_counts = defaultdict(int)
        for ipc in self.code_index.values():
            level_counts[ipc.level] += 1
        stats['levels'] = dict(level_counts)

        return stats

# 全局实例
_ipc_system = None

def get_ipc_system() -> IPCClassificationSystem:
    """获取全局IPC系统实例"""
    global _ipc_system
    if _ipc_system is None:
        _ipc_system = IPCClassificationSystem()
        _ipc_system.load_ipc_data()
    return _ipc_system

# 测试函数
def test_ipc_system():
    """测试IPC分类系统"""
    logger.info('🧪 测试IPC分类系统')
    logger.info(str('=' * 60))

    # 获取IPC系统
    ipc_system = get_ipc_system()

    # 显示统计信息
    stats = ipc_system.get_ipc_statistics()
    logger.info("\n📊 IPC分类统计:")
    logger.info(f"总分类数: {stats['total_ipc_classes']}")
    logger.info(f"技术部分布: {stats['sections']}")
    logger.info(f"领域分布: {stats['domains']}")

    # 测试搜索功能
    test_queries = [
        '基于深度学习的医疗图像诊断',
        '智能交通信号控制系统',
        '新型催化剂的化学合成方法',
        '高精度机床控制系统'
    ]

    logger.info("\n🔍 IPC分类测试:")
    for query in test_queries:
        logger.info(f"\n查询: {query}")
        matches = ipc_system.search_ipc_by_keywords(query, top_k=3)
        if matches:
            for ipc_class, score in matches:
                logger.info(f"  • {ipc_class.code} {ipc_class.name} (置信度: {score:.2f})")
        else:
            logger.info('  未找到匹配的IPC分类')

    # 测试专利匹配
    test_patent = {
        'title': '基于人工智能的医疗图像分析系统',
        'abstract': '本发明涉及一种使用深度学习算法进行医疗图像自动分析的系统，包括图像采集、预处理、特征提取和诊断模块。',
        'claims': '一种基于深度学习的医疗图像诊断装置，包括：图像采集模块、预处理模块、特征提取模块和诊断模块。'
    }

    logger.info("\n📄 专利IPC匹配测试:")
    match_result = ipc_system.match_patent_to_ipc(
        test_patent['claims'],
        test_patent['title'],
        test_patent['abstract']
    )

    logger.info(f"匹配摘要: {match_result.analysis_summary}")
    logger.info("匹配的IPC分类:")
    for i, (ipc, score) in enumerate(zip(match_result.matched_codes, match_result.confidence_scores, strict=False)):
        logger.info(f"  {i+1}. {ipc.code} {ipc.name} (置信度: {score:.2f})")

    # 测试IPC比较
    logger.info("\n🔄 IPC分类比较测试:")
    comparison = ipc_system.compare_ipc_classes('G06F', 'A61')
    logger.info("G06F vs A61:")
    logger.info(f"  相似度: {comparison['similarity']:.2f}")
    logger.info(f"  关系: {comparison['relationship']}")
    logger.info(f"  新颖性含义: {comparison['novelty_implications']}")

if __name__ == '__main__':
    test_ipc_system()
