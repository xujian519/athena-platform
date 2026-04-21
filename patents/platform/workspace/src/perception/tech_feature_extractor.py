#!/usr/bin/env python3
"""
技术特征提取器
Technical Feature Extractor

深度理解技术方案并提取权利要求技术特征
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class FeatureType(Enum):
    """技术特征类型"""
    STRUCTURE = 'structure'           # 结构特征
    COMPONENT = 'component'          # 组成部分
    PARAMETER = 'parameter'          # 参数特征
    STEP = 'step'                   # 步骤特征
    CONDITION = 'condition'         # 条件特征
    FUNCTION = 'function'           # 功能特征
    EFFECT = 'effect'              # 效果特征
    MATERIAL = 'material'           # 材料特征
    CONNECTION = 'connection'       # 连接关系
    ARRANGEMENT = 'arrangement'     # 布置方式

@dataclass
class TechnicalFeature:
    """技术特征"""
    feature_id: str
    feature_type: FeatureType
    feature_text: str
    original_text: str
    claim_number: int
    position: Tuple[int, int]      # 在权利要求中的位置
    hierarchical_level: int         # 层次关系
    relationships: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_essential: bool = False      # 是否为必要技术特征
    is_distinguishing: bool = False  # 是否为区别特征

class TechnicalSchemeAnalyzer:
    """技术方案分析器"""

    def __init__(self):
        self.domain_patterns = self._load_domain_patterns()
        self.technical_keywords = self._load_technical_keywords()
        self.component_patterns = self._load_component_patterns()

    def _load_domain_patterns(self) -> Dict[str, Dict]:
        """加载领域模式"""
        return {
            'mechanical': {
                'components': ['装置', '设备', '机构', '部件', '组件', '零件', '结构件'],
                'connections': ['连接', '固定', '安装', '配合', '组装', '装配'],
                'materials': ['材料', '合金', '塑料', '金属', '陶瓷', '复合材料'],
                'functions': ['实现', '完成', '执行', '操作', '控制', '调节']
            },
            'electronic': {
                'components': ['电路', '芯片', '处理器', '传感器', '执行器', '控制器'],
                'connections': ['电连接', '信号连接', '数据传输', '接口'],
                'parameters': ['电压', '电流', '频率', '阻抗', '功率', '带宽'],
                'functions': ['处理', '控制', '检测', '通信', '存储', '计算']
            },
            'chemical': {
                'components': ['化合物', '组合物', '混合物', '试剂', '催化剂', '溶剂'],
                'parameters': ['浓度', '比例', '温度', '压力', 'pH值', '纯度'],
                'process': ['反应', '合成', '制备', '提取', '纯化', '分离'],
                'conditions': ['条件', '环境', '气氛', '催化剂', '时间']
            },
            'software': {
                'components': ['模块', '单元', '算法', '程序', '接口', '系统'],
                'operations': ['处理', '计算', '分析', '优化', '识别', '分类'],
                'parameters': ['阈值', '权重', '迭代次数', '精度', '速率'],
                'functions': ['实现', '完成', '提高', '优化', '解决', '克服']
            }
        }

    def _load_technical_keywords(self) -> Dict[str, List[str]]:
        """加载技术关键词"""
        return {
            '结构词': ['包括', '包含', '具有', '设有', '配备', '设置', '安装'],
            '功能词': ['用于', '能够', '可以', '实现', '完成', '执行', '进行'],
            '参数词': ['至少', '为', '是', '等于', '大于', '小于', '范围内'],
            '连接词': ['与', '和', '及', '或', '以及', '以及其'],
            '限定词': ['所述', '该', '该上述', '上述'],
            '条件词': ['当', '如果', '在...情况下', '基于', '根据']
        }

    def _load_component_patterns(self) -> List[re.Pattern]:
        """加载组件识别模式"""
        patterns = [
            # (一种/一个/所述) + 名词 + (装置/设备/机构等)
            re.compile(r'(一种|一个|所述|该)([^\uff0c\uff1b\uff1a\uff0e]+)(装置|设备|机构|系统|组件|单元|模块|部件)'),
            # 名词 + 包括/包含 + 具体描述
            re.compile(r'([^\uff0c\uff1b\uff1a\uff0e]+)(包括|包含|具有)([^\uff0c\uff1b\uff1a\uff0e]+)'),
            # 步骤/方法类
            re.compile(r'(步骤\d+[:：]?)([^。\uff0c\uff1b\uff1a\uff0e]+)'),
            # 参数限定
            re.compile(r'([^\uff0c\uff1b\uff1a\uff0e]+)(为|是|等于)([^\uff0c\uff1b\uff1a\uff0e]+)'),
            # 连接关系
            re.compile(r'([^\uff0c\uff1b\uff1a\uff0e]+)(与|和|及)([^\uff0c\uff1b\uff1a\uff0e]+)(连接|固定|安装|配合)'),
            # 功能描述
            re.compile(r'(用于|能够|可以)([^。\uff0c\uff1b\uff1a\uff0e]+)')
        ]
        return patterns

    def understand_technical_scheme(self, patent_text: str) -> Dict[str, Any]:
        """理解技术方案"""
        logger.info('开始理解技术方案...')

        # 1. 提取技术领域
        technical_field = self._extract_technical_field(patent_text)

        # 2. 识别技术问题
        technical_problem = self._extract_technical_problem(patent_text)

        # 3. 分析技术方案
        technical_solution = self._analyze_technical_solution(patent_text)

        # 4. 提取技术效果
        technical_effect = self._extract_technical_effect(patent_text)

        # 5. 识别关键组件
        key_components = self._identify_key_components(patent_text)

        # 6. 分析工作原理
        working_principle = self._analyze_working_principle(patent_text)

        scheme_understanding = {
            'technical_field': technical_field,
            'technical_problem': technical_problem,
            'technical_solution': technical_solution,
            'technical_effect': technical_effect,
            'key_components': key_components,
            'working_principle': working_principle,
            'scheme_summary': self._generate_scheme_summary(
                technical_field, technical_problem, technical_solution, technical_effect
            )
        }

        logger.info('技术方案理解完成')
        return scheme_understanding

    def _extract_technical_field(self, text: str) -> Dict[str, Any]:
        """提取技术领域"""
        field_info = {
            'primary_field': '',
            'secondary_fields': [],
            'keywords': [],
            'ipc_classification': [],
            'domain': 'unknown'
        }

        # 常见技术领域关键词
        field_patterns = {
            'mechanical': ['机械', '装置', '设备', '结构', '部件', '传动', '制造', '加工'],
            'electronic': ['电子', '电路', '芯片', '传感器', '信号', '通信', '控制', '系统'],
            'chemical': ['化学', '化合物', '合成', '反应', '催化剂', '材料', '组合物'],
            'software': ['软件', '程序', '算法', '数据', '网络', '计算', '处理', '分析'],
            'medical': ['医疗', '医学', '诊断', '治疗', '药物', '生物', '基因', '蛋白'],
            'agricultural': ['农业', '农用', '农药', '肥料', '种植', '收获', '加工']
        }

        # 统计各领域关键词出现次数
        field_scores = {}
        for field, keywords in field_patterns.items():
            score = 0
            found_keywords = []
            for keyword in keywords:
                count = text.count(keyword)
                if count > 0:
                    score += count
                    found_keywords.append(keyword)
            if score > 0:
                field_scores[field] = {
                    'score': score,
                    'keywords': found_keywords
                }

        # 确定主要技术领域
        if field_scores:
            sorted_fields = sorted(field_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            field_info['domain'] = sorted_fields[0][0]
            field_info['primary_field'] = sorted_fields[0][1]['keywords'][0] if sorted_fields[0][1]['keywords'] else ''
            field_info['keywords'] = sorted_fields[0][1]['keywords']

            # 次要领域
            if len(sorted_fields) > 1:
                field_info['secondary_fields'] = [
                    {'field': field, 'score': info['score'], 'keywords': info['keywords']}
                    for field, info in sorted_fields[1:]
                ]

        return field_info

    def _extract_technical_problem(self, text: str) -> Dict[str, Any]:
        """提取技术问题"""
        problem_info = {
            'main_problem': '',
            'secondary_problems': [],
            'problem_keywords': [],
            'pain_points': []
        }

        # 技术问题识别模式
        problem_patterns = [
            r"解决[了]?([^。\uff0c\uff1b\uff1a\uff0e]+)的问题",
            r"克服[了]?([^。\uff0c\uff1b\uff1a\uff0e]+)的缺陷",
            r"改进[了]?([^。\uff0c\uff1b\uff1a\uff0e]+)的不足",
            r"存在([^。\uff0c\uff1b\uff1a\uff0e]+)的(问题|缺陷|不足|弊端|困难)",
            r"针对([^。\uff0c\uff1b\uff1a\uff0e]+)的(需求|要求)"
        ]

        for pattern in problem_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    problem_info['problem_keywords'].extend(match)
                else:
                    problem_info['problem_keywords'].append(match)

        # 常见问题关键词
        common_problems = [
            '效率低', '成本高', '精度差', '稳定性差', '安全性不足', '环保性差',
            '结构复杂', '操作不便', '能耗高', '寿命短', '可靠性差', '适应性差'
        ]

        for problem in common_problems:
            if problem in text:
                problem_info['pain_points'].append(problem)

        # 提取主要问题（第一个出现的问题描述）
        for keyword in problem_info['problem_keywords']:
            if len(keyword) > 5:  # 过滤掉太短的
                problem_info['main_problem'] = keyword
                break

        return problem_info

    def _analyze_technical_solution(self, text: str) -> Dict[str, Any]:
        """分析技术方案"""
        solution_info = {
            'core_solution': '',
            'key_steps': [],
            'technical_means': [],
            'implementation_method': ''
        }

        # 提取技术方案核心描述
        solution_patterns = [
            r"技术方案([是]([^。\uff0c\uff1b\uff1a\uff0e]+))",
            r"其特征在于[：:]?([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"包括[：:]?([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"采用[了]?([^。\uff0c\uff1b\uff1a\uff0e]+)(方法|技术|手段)"
        ]

        for pattern in solution_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    solution_info['technical_means'].extend([m for m in match if len(m) > 5])
                else:
                    solution_info['technical_means'].append(match)

        # 识别关键步骤
        step_pattern = r'(步骤\d+[:：]?|第[一二三四五六七八九十\d]+步[:：]?)([^。\uff0c\uff1b\uff1a\uff0e]+)'
        steps = re.findall(step_pattern, text)
        for step in steps:
            if len(step[1]) > 2:
                solution_info['key_steps'].append(step[1].strip())

        # 如果没有明确步骤，尝试从方案描述中提取
        if not solution_info['key_steps'] and solution_info['technical_means']:
            # 将技术手段分割成步骤
            combined_means = ' '.join(solution_info['technical_means'])
            # 按连接词分割
            sentences = re.split(r'[；;，,]', combined_means)
            solution_info['key_steps'] = [s.strip() for s in sentences if len(s.strip()) > 3]

        return solution_info

    def _extract_technical_effect(self, text: str) -> Dict[str, Any]:
        """提取技术效果"""
        effect_info = {
            'main_effects': [],
            'quantitative_effects': [],
            'comparative_effects': []
        }

        # 效果描述模式
        effect_patterns = [
            r"([^\uff0c\uff1b\uff1a\uff0e]+)(效率|准确率|精度|速度|成本|寿命)([提降高低增减优化改进]+)([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"相比现有技术[，,]([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"([提降高低增减优化改进]+)([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"(具有|实现|达到|完成)([^。\uff0c\uff1b\uff1a\uff0e]+)(效果|作用|功能)"
        ]

        for pattern in effect_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    effect_info['main_effects'].extend([m for m in match if len(m) > 2])
                else:
                    effect_info['main_effects'].append(match)

        # 量化效果
        quantitative_pattern = r'(\d+\.?\d*[%]?)([提降高低增减])([^。\uff0c\uff1b\uff1a\uff0e]+)'
        quantitative_matches = re.findall(quantitative_pattern, text)
        for match in quantitative_matches:
            effect_info['quantitative_effects'].append(f"{match[0]}{match[1]}{match[2]}")

        return effect_info

    def _identify_key_components(self, text: str) -> List[Dict[str, Any]]:
        """识别关键组件"""
        components = []

        # 使用预定义的组件模式
        for pattern in self.component_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                component = {
                    'type': 'component',
                    'text': match.group(0),
                    'position': (match.start(), match.end()),
                    'description': match.group(0)
                }
                components.append(component)

        # 去重并合并相似组件
        unique_components = []
        seen = set()
        for comp in components:
            comp_key = comp['text'][:20]  # 使用前20个字符作为键
            if comp_key not in seen:
                seen.add(comp_key)
                unique_components.append(comp)

        return unique_components

    def _analyze_working_principle(self, text: str) -> Dict[str, Any]:
        """分析工作原理"""
        principle_info = {
            'working_process': [],
            'key_mechanism': '',
            'interaction': []
        }

        # 工作过程模式
        process_patterns = [
            r"首先([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"然后([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"接着([^。\uff0c\uff1b\uff1a\uff0e]+)",
            r"最后([^。\uff0c\uff1b\uff1a\uff0e]+)"
        ]

        for pattern in process_patterns:
            matches = re.findall(pattern, text)
            principle_info['working_process'].extend(matches)

        # 关键机理
        mechanism_patterns = [
            r"通过([^。\uff0c\uff1b\uff1a\uff0e]+)(实现|达到|完成)",
            r"利用([^。\uff0c\uff1b\uff1a\uff0e]+)(解决|克服)",
            r"基于([^。\uff0c\uff1b\uff1a\uff0e]+)(进行|执行)"
        ]

        for pattern in mechanism_patterns:
            matches = re.findall(pattern, text)
            if matches and not principle_info['key_mechanism']:
                principle_info['key_mechanism'] = matches[0][0]

        return principle_info

    def _generate_scheme_summary(self, field: Dict, problem: Dict,
                                solution: Dict, effect: Dict) -> str:
        """生成技术方案摘要"""
        summary_parts = []

        # 技术领域
        if field['primary_field']:
            summary_parts.append(f"技术领域：{field['primary_field']}")

        # 技术问题
        if problem['main_problem']:
            summary_parts.append(f"解决技术问题：{problem['main_problem']}")

        # 技术方案
        if solution['technical_means']:
            means = '、'.join(solution['technical_means'][:3])  # 只取前3个
            summary_parts.append(f"技术手段：{means}")

        # 技术效果
        if effect['main_effects']:
            effects = '、'.join(effect['main_effects'][:3])  # 只取前3个
            summary_parts.append(f"技术效果：{effects}")

        return '；'.join(summary_parts)

    def extract_claim_features(self, claim_text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取权利要求技术特征"""
        logger.info(f"开始提取权利要求{claim_number}的技术特征...")

        features = []

        # 清理和预处理权利要求文本
        cleaned_text = self._preprocess_claim_text(claim_text)

        # 识别不同类型的特征
        structure_features = self._extract_structure_features(cleaned_text, claim_number)
        component_features = self._extract_component_features(cleaned_text, claim_number)
        parameter_features = self._extract_parameter_features(cleaned_text, claim_number)
        step_features = self._extract_step_features(cleaned_text, claim_number)
        condition_features = self._extract_condition_features(cleaned_text, claim_number)
        function_features = self._extract_function_features(cleaned_text, claim_number)

        # 合并所有特征
        features.extend(structure_features)
        features.extend(component_features)
        features.extend(parameter_features)
        features.extend(step_features)
        features.extend(condition_features)
        features.extend(function_features)

        # 去重
        features = self._deduplicate_features(features)

        # 分析特征关系
        self._analyze_feature_relationships(features)

        # 识别必要技术特征
        self._identify_essential_features(features)

        logger.info(f"权利要求{claim_number}特征提取完成，共{len(features)}个特征")
        return features

    def _preprocess_claim_text(self, text: str) -> str:
        """预处理权利要求文本"""
        # 移除权利要求编号
        text = re.sub(r'^权利要求\d+[：:]\s*', '', text)
        # 标准化标点符号
        text = re.sub(r'[，。；；]', ',', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_structure_features(self, text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取结构特征"""
        features = []

        # 结构特征模式
        structure_patterns = [
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(装置|设备|机构|系统|结构|框架)',
            r'(包括|包含|具有|设有|配备)([^\uff0c\uff1b\uff1a\uff0e]+)(部件|组件|单元|模块)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(连接|固定|安装|设置|布置)([^\uff0c\uff1b\uff1a\uff0e]+)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(和|及|与)([^\uff0c\uff1b\uff1a\uff0e]+)(连接|配合|组装)'
        ]

        for pattern in structure_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature = TechnicalFeature(
                    feature_id=f"STR_{claim_number}_{len(features)}",
                    feature_type=FeatureType.STRUCTURE,
                    feature_text=match.group(0),
                    original_text=match.group(0),
                    claim_number=claim_number,
                    position=(match.start(), match.end()),
                    hierarchical_level=1
                )
                features.append(feature)

        return features

    def _extract_component_features(self, text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取组件特征"""
        features = []

        # 组件特征模式
        component_patterns = [
            r'([^,]+)(芯片|传感器|执行器|控制器|处理器|模块|单元)',
            r'([^,]+)(外壳|壳体|箱体|容器|管路|管道)',
            r'([^,]+)(传动机构|驱动机构|执行机构|控制机构)',
            r'([^,]+)(电路|线路|连接器|接口)'
        ]

        for pattern in component_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature = TechnicalFeature(
                    feature_id=f"COMP_{claim_number}_{len(features)}",
                    feature_type=FeatureType.COMPONENT,
                    feature_text=match.group(0),
                    original_text=match.group(0),
                    claim_number=claim_number,
                    position=(match.start(), match.end()),
                    hierarchical_level=1
                )
                features.append(feature)

        return features

    def _extract_parameter_features(self, text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取参数特征"""
        features = []

        # 参数特征模式
        parameter_patterns = [
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(为|是|等于)(\d+\.?\d*)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(在|范围)([^\uff0c\uff1b\uff1a\uff0e]+)之间',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(大于|小于|超过|不超过)(\d+\.?\d*)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(至少|最多|不多于)(\d+\.?\d*)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(mm|cm|m|g|kg|℃|℃|℃|V|A|Hz|MHz|GHz)'
        ]

        for pattern in parameter_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature = TechnicalFeature(
                    feature_id=f"PARAM_{claim_number}_{len(features)}",
                    feature_type=FeatureType.PARAMETER,
                    feature_text=match.group(0),
                    original_text=match.group(0),
                    claim_number=claim_number,
                    position=(match.start(), match.end()),
                    hierarchical_level=1
                )
                features.append(feature)

        return features

    def _extract_step_features(self, text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取步骤特征"""
        features = []

        # 步骤特征模式
        step_patterns = [
            r'(步骤\d+[:：]?|第[一二三四五六七八九十\d]+步[:：]?)([^,]+)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(处理|计算|分析|识别|提取|转换)',
            r'(首先|然后|接着|最后)([^,]+)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(方法|过程、程序、流程)'
        ]

        for pattern in step_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature = TechnicalFeature(
                    feature_id=f"STEP_{claim_number}_{len(features)}",
                    feature_type=FeatureType.STEP,
                    feature_text=match.group(0),
                    original_text=match.group(0),
                    claim_number=claim_number,
                    position=(match.start(), match.end()),
                    hierarchical_level=1
                )
                features.append(feature)

        return features

    def _extract_condition_features(self, text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取条件特征"""
        features = []

        # 条件特征模式
        condition_patterns = [
            r'(当|如果|在...情况下|基于|根据)([^,]+)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(时|时，|的情况下)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(的条件是|条件为)([^,]+)',
            r'满足([^,]+)'
        ]

        for pattern in condition_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature = TechnicalFeature(
                    feature_id=f"COND_{claim_number}_{len(features)}",
                    feature_type=FeatureType.CONDITION,
                    feature_text=match.group(0),
                    original_text=match.group(0),
                    claim_number=claim_number,
                    position=(match.start(), match.end()),
                    hierarchical_level=1
                )
                features.append(feature)

        return features

    def _extract_function_features(self, text: str, claim_number: int) -> List[TechnicalFeature]:
        """提取功能特征"""
        features = []

        # 功能特征模式
        function_patterns = [
            r'(用于|能够|可以)([^,]+)',
            r'(实现|完成|执行、达到)([^,]+)',
            r'([^\uff0c\uff1b\uff1a\uff0e]+)(功能|作用|效果)',
            r'(具有|具备)([^,]+)(的能力|功能)'
        ]

        for pattern in function_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature = TechnicalFeature(
                    feature_id=f"FUNC_{claim_number}_{len(features)}",
                    feature_type=FeatureType.FUNCTION,
                    feature_text=match.group(0),
                    original_text=match.group(0),
                    claim_number=claim_number,
                    position=(match.start(), match.end()),
                    hierarchical_level=1
                )
                features.append(feature)

        return features

    def _deduplicate_features(self, features: List[TechnicalFeature]) -> List[TechnicalFeature]:
        """去重特征"""
        unique_features = []
        seen_texts = set()

        for feature in features:
            # 使用特征文本的前20个字符作为去重键
            key = feature.feature_text[:20]
            if key not in seen_texts:
                seen_texts.add(key)
                unique_features.append(feature)

        return unique_features

    def _analyze_feature_relationships(self, features: List[TechnicalFeature]):
        """分析特征关系"""
        # 分析连接关系
        for i, feature1 in enumerate(features):
            for j, feature2 in enumerate(features):
                if i >= j:
                    continue

                # 检查是否相邻且有连接词
                if feature1.position[1] < feature2.position[0]:
                    between_text = feature2.position[0] - feature1.position[1]
                    if between_text < 50:  # 相邻较近
                        # 添加关系
                        feature1.relationships.append(feature2.feature_id)
                        feature2.relationships.append(feature1.feature_id)

    def _identify_essential_features(self, features: List[TechnicalFeature]):
        """识别必要技术特征"""
        # 根据特征类型和位置判断重要性
        for feature in features:
            # 前置限定特征通常是必要的
            if feature.position[0] < len(features) * 20:  # 前20%位置
                feature.is_essential = True

            # 结构特征和组件特征通常更重要
            if feature.feature_type in [FeatureType.STRUCTURE, FeatureType.COMPONENT]:
                feature.is_essential = True

            # 包含"所述"、"该"等限定词的特征可能是必要的
            if any(word in feature.original_text for word in ['所述', '该', '上述']):
                feature.is_essential = True

# 全局分析器实例
technical_feature_extractor = TechnicalSchemeAnalyzer()

# 测试代码
if __name__ == '__main__':
    # 测试示例
    test_claims = [
        '权利要求1：一种图像识别装置，其特征在于包括：图像采集单元，用于采集待识别图像；处理单元，连接所述图像采集单元，用于对图像进行预处理和特征提取；识别单元，连接所述处理单元，用于基于深度学习算法对特征进行分类识别；输出单元，连接所述识别单元，用于输出识别结果。',

        '权利要求2：根据权利要求1所述的装置，其特征在于，所述处理单元包括：卷积神经网络模块，用于提取图像的深度特征；注意力机制模块，用于增强关键特征的权重；残差连接模块，用于解决梯度消失问题。'
    ]

    for i, claim_text in enumerate(test_claims, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"分析权利要求{i}：")
        logger.info(f"{'='*80}")
        logger.info(str(claim_text))

        features = technical_feature_extractor.extract_claim_features(claim_text, i)

        logger.info(f"\n提取的技术特征（共{len(features)}个）：")
        for feature in features:
            logger.info(f"\n- 特征ID: {feature.feature_id}")
            logger.info(f"  类型: {feature.feature_type.value}")
            logger.info(f"  内容: {feature.feature_text}")
            logger.info(f"  必要特征: {'是' if feature.is_essential else '否'}")
            if feature.relationships:
                logger.info(f"  关联特征: {feature.relationships}")