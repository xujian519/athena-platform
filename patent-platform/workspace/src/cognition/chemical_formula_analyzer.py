#!/usr/bin/env python3
"""
专利审查意见化学式分析器
Patent Opinion Chemical Formula Analyzer
"""

import json
import logging
import os
import re
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class ChemicalFormulaAnalyzer:
    """化学式分析器"""

    def __init__(self):
        # 化学式识别模式
        self.chemical_patterns = {
            # 化学元素和分子式模式
            'molecular_formula': r'\b[A-Z][a-z]?(?:\d*[+-]?\d*(?:\.\d+)?(?:\([^)]*\)\d*)?)*\b',
            # 有机物结构模式
            'organic_compound': r'\b(?:[A-Z][a-z]?\d*)+(?:-[A-Z][a-z]?\d*)*\b',
            # 化学反应箭头
            'reaction_arrow': r'[→↔⇌⇄⇆]',
            # 化学键
            'chemical_bond': r'[=-#]',
            # 同位素标记
            'isotope': r'\b\d+[A-Z][a-z]?\b',
            # 离子和电荷
            'ion_charge': r'\b[A-Z][a-z]?\d*[+-]\d*\b',
            # 中文化学物质名称模式
            'chinese_chemical': r'[\u4e00-\u9fff]*(?:酸|盐|酯|醛|酮|醇|酚|胺|酰胺|醌|醚|烃|苯|环|烷|烯|炔|蒽|萘|菲|啶|嗪|噻吩|呋喃|吡咯|吲哚|咪唑|噻唑|恶唑|嘧啶|嘌呤|吡啶|吡嗪|哒嗪|三嗪|四嗪|苯并|萘并|蒽并|菲并)',
        }

        # 审查意见中提到的具体化学物质
        self.target_chemicals = [
            'N-羟基琥珀酰亚胺', 'N,N\'-二环己基碳二亚胺', 'NHS', 'DCC', 'DMAP',
            '四氢呋喃', 'THF', '三乙胺', 'Et3N', '二氯甲烷', 'DCM', '甲醇', '乙醇',
            '乙酸乙酯', '石油醚', '硫酸钠', '碳酸氢钠', '氢氧化钠', '盐酸', '硫酸'
        ]

        # 常见化学缩写
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
            'H2SO4': '硫酸'
        }

    def extract_from_text(self, text: str) -> dict[str, Any]:
        """从文本中提取化学式和化学物质"""
        results = {
            'molecular_formulas': [],
            'organic_compounds': [],
            'reaction_arrows': [],
            'chinese_chemicals': [],
            'target_chemicals_found': [],
            'abbreviations_found': [],
            'confidence_scores': {}
        }

        # 提取分子式
        for match in re.finditer(self.chemical_patterns['molecular_formula'], text):
            formula = match.group()
            if self._is_likely_molecular_formula(formula):
                results['molecular_formulas'].append({
                    'text': formula,
                    'position': match.span(),
                    'type': 'molecular_formula'
                })

        # 提取有机化合物
        for match in re.finditer(self.chemical_patterns['organic_compound'], text):
            compound = match.group()
            if len(compound) > 2:  # 过滤太短的匹配
                results['organic_compounds'].append({
                    'text': compound,
                    'position': match.span(),
                    'type': 'organic_compound'
                })

        # 提取化学反应箭头
        for match in re.finditer(self.chemical_patterns['reaction_arrow'], text):
            results['reaction_arrows'].append({
                'text': match.group(),
                'position': match.span(),
                'type': 'reaction_arrow'
            })

        # 提取中文化学物质名称
        for match in re.finditer(self.chemical_patterns['chinese_chemical'], text):
            chemical = match.group()
            if len(chemical) >= 2:
                results['chinese_chemicals'].append({
                    'text': chemical,
                    'position': match.span(),
                    'type': 'chinese_chemical'
                })

        # 查找目标化学物质
        text_lower = text.lower()
        for chemical in self.target_chemicals:
            if chemical.lower() in text_lower:
                # 找到具体位置
                start = text.lower().find(chemical.lower())
                results['target_chemicals_found'].append({
                    'text': chemical,
                    'position': (start, start + len(chemical)),
                    'type': 'target_chemical'
                })

        # 查找化学缩写
        for abbr, full_name in self.chemical_abbreviations.items():
            if abbr in text or full_name in text:
                results['abbreviations_found'].append({
                    'abbreviation': abbr,
                    'full_name': full_name,
                    'found_abbr': abbr in text,
                    'found_full': full_name in text
                })

        # 计算置信度
        total_chemicals = (len(results['molecular_formulas']) +
                          len(results['organic_compounds']) +
                          len(results['chinese_chemicals']) +
                          len(results['target_chemicals_found']))

        results['confidence_scores'] = {
            'has_chemical_content': total_chemicals > 0,
            'chemical_density': total_chemicals / len(text.split()) if text.split() else 0,
            'has_reactions': len(results['reaction_arrows']) > 0,
            'target_coverage': len(results['target_chemicals_found']) / len(self.target_chemicals)
        }

        return results

    def _is_likely_molecular_formula(self, formula: str) -> bool:
        """判断是否为合理的分子式"""
        # 至少包含一个大写字母和可能的数字
        if not re.search(r'[A-Z]', formula):
            return False

        # 过滤常见的非化学式单词
        common_words = ['THE', 'AND', 'FOR', 'WITH', 'THIS', 'THAT', 'FROM', 'THEY', 'HAVE', 'BEEN']
        if formula.upper() in common_words:
            return False

        # 检查是否包含合理的元素模式
        element_pattern = r'[A-Z][a-z]?'
        elements = re.findall(element_pattern, formula)
        return len(elements) >= 1

    def analyze_patent_opinion_pdf(self, pdf_path: str) -> dict[str, Any]:
        """分析专利审查意见PDF"""
        if not os.path.exists(pdf_path):
            return {'error': f'文件不存在: {pdf_path}'}

        try:
            # 打开PDF
            pdf_document = fitz.open(pdf_path)
            all_text = ''
            page_texts = []

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                page_texts.append({
                    'page_number': page_num + 1,
                    'text': text
                })
                all_text += text + '\n'

            pdf_document.close()

            # 提取化学式
            chemical_analysis = self.extract_from_text(all_text)

            # 按页面分析
            page_analyses = []
            for page_info in page_texts:
                page_analysis = self.extract_from_text(page_info['text'])
                page_analysis['page_number'] = page_info['page_number']
                page_analyses.append(page_analysis)

            # 生成报告
            report = {
                'pdf_path': pdf_path,
                'total_pages': len(page_texts),
                'overall_analysis': chemical_analysis,
                'page_analyses': page_analyses,
                'summary': self._generate_summary(chemical_analysis, page_analyses),
                'recommendations': self._generate_recommendations(chemical_analysis)
            }

            return report

        except Exception as e:
            return {'error': f'PDF处理失败: {str(e)}'}

    def _generate_summary(self, overall: dict, pages: list[dict]) -> dict[str, Any]:
        """生成分析摘要"""
        total_formulas = sum(len(p.get('molecular_formulas', [])) for p in pages)
        total_chemicals = sum(len(p.get('chinese_chemicals', [])) for p in pages)
        total_targets = sum(len(p.get('target_chemicals_found', [])) for p in pages)

        return {
            'total_molecular_formulas': total_formulas,
            'total_chinese_chemicals': total_chemicals,
            'total_target_chemicals': total_targets,
            'pages_with_chemicals': sum(1 for p in pages if any([
                p.get('molecular_formulas'),
                p.get('chinese_chemicals'),
                p.get('target_chemicals_found')
            ])),
            'chemical_pages_percentage': sum(1 for p in pages if any([
                p.get('molecular_formulas'),
                p.get('chinese_chemicals'),
                p.get('target_chemicals_found')
            ])) / len(pages) * 100 if pages else 0
        }

    def _generate_recommendations(self, analysis: dict) -> list[str]:
        """生成建议"""
        recommendations = []

        if len(analysis['target_chemicals_found']) > 0:
            recommendations.append('✅ 审查意见中包含具体的化学物质名称，说明涉及化学发明')

        if len(analysis['molecular_formulas']) > 0:
            recommendations.append('✅ 发现化学分子式，需要确认权利要求中的化学式是否清楚表达')

        if analysis['confidence_scores']['chemical_density'] > 0.01:
            recommendations.append('⚠️  化学内容密度较高，需要特别注意技术方案的清楚表述')

        if len(analysis['chinese_chemicals']) > 0:
            recommendations.append('✅ 发现中文化学物质名称，需要与化学式对应检查')

        return recommendations

def main():
    """主函数"""
    analyzer = ChemicalFormulaAnalyzer()

    # 分析审查意见PDF
    pdf_path = '/Users/xujian/Athena工作平台/工作/锦州大学审查意见答复/202311334091.8-第一次审查意见-锦州医科大学-2025.9.17.pdf'

    logger.info('🧪 开始分析专利审查意见PDF中的化学式...')
    logger.info(f"📁 文件路径: {pdf_path}")

    result = analyzer.analyze_patent_opinion_pdf(pdf_path)

    if 'error' in result:
        logger.info(f"❌ 分析失败: {result['error']}")
        return

    # 打印结果
    logger.info("\n📊 分析结果:")
    logger.info(f"📄 总页数: {result['total_pages']}")

    summary = result['summary']
    logger.info(f"🧪 分子式总数: {summary['total_molecular_formulas']}")
    logger.info(f"🔤 中文化学物质: {summary['total_chinese_chemicals']}")
    logger.info(f"🎯 目标化学物质: {summary['total_target_chemicals']}")
    logger.info(f"📈 包含化学内容的页面: {summary['pages_with_chemicals']}/{result['total_pages']} ({summary['chemical_pages_percentage']:.1f}%)")

    # 显示目标化学物质
    target_chemicals = result['overall_analysis']['target_chemicals_found']
    if target_chemicals:
        logger.info("\n🎯 发现的目标化学物质:")
        for chemical in target_chemicals:
            logger.info(f"  ✅ {chemical['text']}")

    # 显示化学缩写
    abbreviations = result['overall_analysis']['abbreviations_found']
    if abbreviations:
        logger.info("\n📝 发现的化学缩写:")
        for abbr_info in abbreviations:
            found_marks = []
            if abbr_info['found_abbr']:
                found_marks.append(f"缩写: {abbr_info['abbreviation']}")
            if abbr_info['found_full']:
                found_marks.append(f"全称: {abbr_info['full_name']}")
            logger.info(f"  📋 {abbr_info['abbreviation']} = {abbr_info['full_name']} ({', '.join(found_marks)})")

    # 显示中文化学物质
    chinese_chemicals = result['overall_analysis']['chinese_chemicals']
    if chinese_chemicals:
        logger.info("\n🔤 发现的中文化学物质 (前10个):")
        for chemical in chinese_chemicals[:10]:
            logger.info(f"  🔤 {chemical['text']}")

    # 显示建议
    recommendations = result['recommendations']
    if recommendations:
        logger.info("\n💡 分析建议:")
        for rec in recommendations:
            logger.info(f"  {rec}")

    # 保存详细结果
    output_file = '/Users/xujian/Athena工作平台/工作/锦州大学审查意见答复/chemical_analysis_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"\n💾 详细分析结果已保存到: {output_file}")
    logger.info('✅ 化学式分析完成!')

if __name__ == '__main__':
    main()
