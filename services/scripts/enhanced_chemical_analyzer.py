#!/usr/bin/env python3
"""
增强化学式分析器 - 集成ChemPy库
Enhanced Chemical Formula Analyzer with ChemPy Integration
"""

import logging
import re
from typing import Any

from core.logging_config import setup_logging

# 尝试导入ChemPy
try:
    from chempy import Reaction, Substance
    CHEMPY_AVAILABLE = True
    logging.info('ChemPy库已加载 - 可进行高级化学计算')
except ImportError:
    CHEMPY_AVAILABLE = False
    logging.warning('ChemPy库未找到 - 仅使用基础分析功能')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class EnhancedChemicalAnalyzer:
    """增强的化学式分析器，集成ChemPy库功能"""

    def __init__(self):
        # 基础化学模式 (来自原有分析器)
        self.chemical_patterns = {
            'molecular_formula': r'\b[A-Z][a-z]?(?:\d*[+-]?\d*(?:\.\d+)?(?:\([^)]*\)\d*)?)*\b',
            'organic_compound': r'\b(?:[A-Z][a-z]?\d*)+(?:-[A-Z][a-z]?\d*)*\b',
            'reaction_arrow': r'[→↔⇌⇄⇆]',
            'chemical_bond': r'[=-#]',
            'isotope': r'\b\d+[A-Z][a-z]?\b',
            'ion_charge': r'\b[A-Z][a-z]?\d*[+-]\d*\b',
            'chinese_chemical': r'[\u4e00-\u9fff]*(?:酸|盐|酯|醛|酮|醇|酚|胺|酰胺|醌|醚|烃|苯|环|烷|烯|炔|蒽|萘|菲|啶|嗪|噻吩|呋喃|吡咯|吲哚|咪唑|噻唑|恶唑|嘧啶|嘌呤|吡啶|吡嗪|哒嗪|三嗪|四嗪|苯并|萘并|蒽并|菲并)',
        }

        # ChemPy增强功能
        self.chempy_enabled = CHEMPY_AVAILABLE

        # 常见化学缩写映射
        self.chemical_abbreviations = {
            'NHS': 'N-羟基琥珀酰亚胺',
            'DCC': 'N,N\'-二环己基碳二亚胺',
            'DMAP': '4-二甲氨基吡啶',
            'THF': '四氢呋喃',
            'Et3N': '三乙胺',
            'DCM': '二氯甲烷',
            'MeCN': '乙腈',
            'EtOAc': '乙酸乙酯',
            'NaHCO3': '碳酸氢钠',
            'Na2SO4': '硫酸钠',
            'NaOH': '氢氧化钠',
            'HCl': '盐酸',
            'H2SO4': '硫酸',
            'DMF': 'N,N-二甲基甲酰胺',
            'DMSO': '二甲基亚砜',
            'EDTA': '乙二胺四乙酸'
        }

    def analyze_with_chempy(self, formula: str) -> dict[str, Any | None]:
        """使用ChemPy分析化学式"""
        if not self.chempy_enabled:
            return None

        try:
            substance = Substance.from_formula(formula)
            return {
                'formula': formula,
                'molecular_weight': substance.mass,
                'composition': substance.composition,
                'elements': list(substance.composition.keys()),
                'valid': True,
                'method': 'ChemPy'
            }
        except Exception as e:
            logger.debug(f"ChemPy解析失败 {formula}: {str(e)}")
            return None

    def validate_formula_basic(self, formula: str) -> dict[str, Any]:
        """基础化学式验证"""
        result = {
            'formula': formula,
            'valid': False,
            'method': 'basic_regex',
            'issues': []
        }

        # 基础格式检查
        if not re.match(r'^[A-Za-z0-9\(\)\[\]\{\}\+\-\.\s]*$', formula):
            result['issues'].append('包含无效字符')

        # 元素模式检查
        if not re.search(r'[A-Z]', formula):
            result['issues'].append('缺少大写字母（元素符号）')

        # 过滤常见非化学式单词
        common_words = ['THE', 'AND', 'FOR', 'WITH', 'THIS', 'THAT', 'FROM', 'THEY', 'HAVE', 'BEEN']
        if formula.upper() in common_words:
            result['issues'].append('常见非化学式单词')
            return result

        # 检查元素模式
        element_pattern = r'[A-Z][a-z]?'
        elements = re.findall(element_pattern, formula)
        if len(elements) >= 1:
            result['valid'] = True
            result['elements_found'] = elements

        return result

    def extract_chemical_formulas(self, text: str) -> list[dict[str, Any]:
        """提取并分析化学式"""
        formulas = []

        # 使用正则表达式查找潜在的化学式
        potential_formulas = re.finditer(self.chemical_patterns['molecular_formula'], text)

        for match in potential_formulas:
            formula = match.group().strip()

            # 跳过太短的匹配
            if len(formula) < 2:
                continue

            # 跳过常见的非化学式
            if formula.upper() in ['A', 'I', 'AN', 'IN', 'ON', 'OF', 'TO', 'BY']:
                continue

            analysis_result = {
                'text': formula,
                'position': match.span(),
                'type': 'molecular_formula'
            }

            # 尝试ChemPy分析
            if self.chempy_enabled:
                chempy_result = self.analyze_with_chempy(formula)
                if chempy_result:
                    analysis_result.update(chempy_result)
                    analysis_result['confidence'] = 'high'
                else:
                    # ChemPy失败，使用基础验证
                    basic_result = self.validate_formula_basic(formula)
                    analysis_result.update(basic_result)
                    analysis_result['confidence'] = 'medium' if basic_result['valid'] else 'low'
            else:
                # 只有基础验证
                basic_result = self.validate_formula_basic(formula)
                analysis_result.update(basic_result)
                analysis_result['confidence'] = 'medium' if basic_result['valid'] else 'low'

            formulas.append(analysis_result)

        return formulas

    def analyze_chemical_abbreviations(self, text: str) -> list[dict[str, Any]:
        """分析化学缩写"""
        abbreviations = []

        for abbr, full_name in self.chemical_abbreviations.items():
            found_info = {
                'abbreviation': abbr,
                'full_name': full_name,
                'found_abbr': abbr in text,
                'found_full': full_name in text,
                'positions': {
                    'abbr': [],
                    'full': []
                }
            }

            # 查找位置
            if found_info['found_abbr']:
                for match in re.finditer(re.escape(abbr), text):
                    found_info['positions']['abbr'].append(match.span())

            if found_info['found_full']:
                for match in re.finditer(re.escape(full_name), text):
                    found_info['positions']['full'].append(match.span())

            if found_info['found_abbr'] or found_info['found_full']:
                abbreviations.append(found_info)

        return abbreviations

    def extract_chinese_chemical_terms(self, text: str) -> list[dict[str, Any]:
        """提取中文化学术语"""
        chinese_chemicals = []

        for match in re.finditer(self.chemical_patterns['chinese_chemical'], text):
            chemical = match.group()
            if len(chemical) >= 2:  # 过滤太短的匹配
                chinese_chemicals.append({
                    'text': chemical,
                    'position': match.span(),
                    'type': 'chinese_chemical',
                    'category': self._classify_chinese_chemical(chemical)
                })

        return chinese_chemicals

    def _classify_chinese_chemical(self, term: str) -> str:
        """分类中文化学术语"""
        if any(suffix in term for suffix in ['酸', '盐']):
            return 'acid_salt'
        elif any(suffix in term for suffix in ['酯', '内酯']):
            return 'ester'
        elif any(suffix in term for suffix in ['醛', '酮']):
            return 'aldehyde_ketone'
        elif any(suffix in term for suffix in ['醇', '酚']):
            return 'alcohol_phenol'
        elif any(suffix in term for suffix in ['胺', '酰胺']):
            return 'amine_amide'
        elif any(suffix in term for suffix in ['烃', '烷', '烯', '炔']):
            return 'hydrocarbon'
        elif any(suffix in term for suffix in ['苯', '环', '蒽', '萘', '菲']):
            return 'aromatic_ring'
        else:
            return 'other'

    def comprehensive_analysis(self, text: str) -> dict[str, Any]:
        """综合化学分析"""
        logger.info(f"开始综合化学分析，文本长度: {len(text)} 字符")

        results = {
            'text_length': len(text),
            'chempy_enabled': self.chempy_enabled,
            'analysis_timestamp': logging.time.time(),
            'chemical_formulas': [],
            'chinese_chemicals': [],
            'abbreviations': [],
            'statistics': {},
            'recommendations': []
        }

        # 1. 化学式提取和分析
        results['chemical_formulas'] = self.extract_chemical_formulas(text)

        # 2. 中文化学术语提取
        results['chinese_chemicals'] = self.extract_chinese_chemical_terms(text)

        # 3. 化学缩写分析
        results['abbreviations'] = self.analyze_chemical_abbreviations(text)

        # 4. 生成统计信息
        results['statistics'] = self._generate_statistics(results)

        # 5. 生成建议
        results['recommendations'] = self._generate_recommendations(results)

        logger.info(f"分析完成: 发现 {len(results['chemical_formulas'])} 个化学式")

        return results

    def _generate_statistics(self, results: dict[str, Any]) -> dict[str, Any]:
        """生成统计信息"""
        formulas = results['chemical_formulas']

        stats = {
            'total_formulas': len(formulas),
            'valid_formulas': len([f for f in formulas if f.get('valid', False)]),
            'high_confidence': len([f for f in formulas if f.get('confidence') == 'high']),
            'medium_confidence': len([f for f in formulas if f.get('confidence') == 'medium']),
            'low_confidence': len([f for f in formulas if f.get('confidence') == 'low']),
            'chempy_analyzed': len([f for f in formulas if f.get('method') == 'ChemPy']),
            'avg_molecular_weight': 0,
            'elements_distribution': {},
            'chinese_chemicals_count': len(results['chinese_chemicals']),
            'abbreviations_count': len(results['abbreviations'])
        }

        # 计算平均分子量
        valid_weights = [f['molecular_weight'] for f in formulas if f.get('molecular_weight')]
        if valid_weights:
            stats['avg_molecular_weight'] = sum(valid_weights) / len(valid_weights)

        # 统计元素分布
        for formula in formulas:
            if formula.get('elements'):
                for element in formula['elements']:
                    stats['elements_distribution'][element] = stats['elements_distribution'].get(element, 0) + 1

        return stats

    def _generate_recommendations(self, results: dict[str, Any]) -> list[str]:
        """生成分析建议"""
        recommendations = []
        stats = results['statistics']

        if stats['total_formulas'] > 0:
            recommendations.append(f"✅ 发现 {stats['total_formulas']} 个化学式")

        if stats['high_confidence'] > 0:
            recommendations.append(f"🎯 {stats['high_confidence']} 个高置信度化学式（ChemPy验证）")

        if stats['chempy_analyzed'] > 0:
            recommendations.append(f"🧪 {stats['chempy_analyzed']} 个化学式经过ChemPy专业分析")

        if stats['chinese_chemicals_count'] > 0:
            recommendations.append(f"🔤 发现 {stats['chinese_chemicals_count']} 个中文化学术语")

        if stats['abbreviations_count'] > 0:
            recommendations.append(f"📝 识别 {stats['abbreviations_count']} 个化学缩写")

        if stats['avg_molecular_weight'] > 0:
            recommendations.append(f"📊 平均分子量: {stats['avg_molecular_weight']:.2f} g/mol")

        if not results['chempy_enabled']:
            recommendations.append('⚠️ ChemPy库未安装，建议安装以获得更准确的化学式分析')

        return recommendations

def demo_enhanced_analyzer() -> Any:
    """演示增强化学分析器"""
    logger.info('🧪 增强化学式分析器演示')
    logger.info(str('=' * 50))

    analyzer = EnhancedChemicalAnalyzer()

    # 测试文本
    test_text = """
    本发明涉及一种新型有机化合物的合成方法，该化合物分子式为C12H22O4。
    反应过程如下：N-羟基琥珀酰亚胺(NHS)和N,N'-二环己基碳二亚胺(DCC)在四氢呋喃(THF)中反应，
    生成中间体C8H15NO2，然后与乙酸乙酯反应得到最终产物。
    反应式：C8H15NO2 + CH3COOH → C10H19NO3 + H2O

    该方法还包括使用盐酸催化剂和氢氧化钠中和步骤。
    """

    logger.info('📝 分析文本:')
    logger.info(str(test_text))
    logger.info(str("\n" + '=' * 50))

    # 执行分析
    results = analyzer.comprehensive_analysis(test_text)

    # 显示结果
    logger.info("🔬 化学式分析结果:")
    logger.info(f"   总数: {results['statistics']['total_formulas']}")
    logger.info(f"   有效: {results['statistics']['valid_formulas']}")
    logger.info(f"   高置信度: {results['statistics']['high_confidence']}")
    logger.info(f"   ChemPy分析: {results['statistics']['chempy_analyzed']}")

    logger.info("\n📊 详细化学式:")
    for formula in results['chemical_formulas']:
        if formula.get('valid'):
            logger.info(f"   ✅ {formula['text']} - 分子量: {formula.get('molecular_weight', 'N/A')} g/mol ({formula.get('confidence', 'N/A')} 置信度)")
        else:
            logger.info(f"   ❌ {formula['text']} - 验证失败")

    logger.info("\n🔤 中文化学术语:")
    for chemical in results['chinese_chemicals']:
        logger.info(f"   🔤 {chemical['text']} ({chemical.get('category', 'unknown')})")

    logger.info("\n📝 化学缩写:")
    for abbr in results['abbreviations']:
        logger.info(f"   📝 {abbr['abbreviation']} = {abbr['full_name']}")

    logger.info("\n💡 分析建议:")
    for rec in results['recommendations']:
        logger.info(f"   {rec}")

    logger.info(f"\n🔧 ChemPy状态: {'✅ 已启用' if results['chempy_enabled'] else '❌ 未启用'}")

if __name__ == '__main__':
    demo_enhanced_analyzer()
