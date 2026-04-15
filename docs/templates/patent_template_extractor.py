#!/usr/bin/env python3
"""
专利申请文件模板提取器
用于根据JSON模板从专利申请文件中提取结构化信息
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

class PatentTemplateExtractor:
    """专利申请文件模板提取器"""

    def __init__(self, template_file: str = 'patent_application_templates.json'):
        """
        初始化提取器

        Args:
            template_file: JSON模板文件路径
        """
        with open(template_file, encoding='utf-8') as f:
            self.templates = json.load(f)

    def extract_abstract(self, text: str) -> dict[str, Any]:
        """
        提取说明书摘要信息

        Args:
            text: 摘要文本

        Returns:
            结构化的摘要信息
        """
        template = self.templates['patent_application_templates']['abstract_template']['structure']
        result = {}

        # 提取标题（通常在第一行）
        lines = text.split('\n')
        if lines:
            result['title'] = lines[0].strip()
            # 假设技术领域在前几句
            for line in lines[1:5]:
                if '技术领域' in line or '涉及' in line:
                    result['technical_field'] = line.strip()
                    break

        # 提取技术问题
        problem_patterns = [
            r"要解决的技术问题[：:]\s*(.+?)[；;。\n]",
            r"解决.*问题[：:]\s*(.+?)[；;。\n]",
            r"针对.*问题[：:]\s*(.+?)[；;。\n]"
        ]
        for pattern in problem_patterns:
            match = re.search(pattern, text)
            if match:
                result['technical_problem'] = match.group(1).strip()
                break

        # 提取技术方案
        solution_patterns = [
            r"技术方案[：:]\s*(.+?)[；;。\n]",
            r"采用.*方案[：:]\s*(.+?)[；;。\n]",
            r"实现.*方法[：:]\s*(.+?)[；;。\n]"
        ]
        for pattern in solution_patterns:
            match = re.search(pattern, text)
            if match:
                result['technical_solution'] = match.group(1).strip()
                break

        # 提取主要用途
        use_patterns = [
            r"主要用途[：:]\s*(.+?)[；;。\n]",
            r"可用于(.+?)[；;。\n]",
            r"适用于(.+?)[；;。\n]"
        ]
        for pattern in use_patterns:
            match = re.search(pattern, text)
            if match:
                result['main_use'] = match.group(1).strip()
                break

        # 验证字数
        if 'technical_problem' in result and 'technical_solution' in result:
            total_words = len(result['technical_problem'] + result['technical_solution'])
            result['word_count_check'] = {
                'actual': total_words,
                'limit': template['constraints']['word_count']['max'],
                'compliant': total_words <= template['constraints']['word_count']['max']
            }

        return result

    def extract_claims(self, text: str) -> dict[str, Any]:
        """
        提取权利要求书信息

        Args:
            text: 权利要求书文本

        Returns:
            结构化的权利要求信息
        """
        result = {
            'claims': [],
            'independent_claims': [],
            'dependent_claims': []
        }

        # 分割权利要求（按编号）
        claim_pattern = r"(\d+)\.([\s\S]+?)(?=\n\d+\.|\n\n|$)"
        matches = re.findall(claim_pattern, text)

        for claim_num, claim_text in matches:
            claim = {
                'number': int(claim_num),
                'text': claim_text.strip(),
                'type': self._determine_claim_type(claim_text)
            }

            # 分析权利要求结构
            if claim['type'] == 'independent':
                claim.update(self._parse_independent_claim(claim_text))
                result['independent_claims'].append(claim)
            else:
                claim.update(self._parse_dependent_claim(claim_text))
                result['dependent_claims'].append(claim)

            result['claims'].append(claim)

        # 检查权利要求引用关系
        result['reference_check'] = self._check_claim_references(result['claims'])

        return result

    def extract_specification(self, text: str) -> dict[str, Any]:
        """
        提取说明书信息

        Args:
            text: 说明书文本

        Returns:
            结构化的说明书信息
        """
        result = {}

        # 提取技术领域
        tech_field_pattern = r"技术领域[：:]?\s*([^\n]+)"
        match = re.search(tech_field_pattern, text)
        if match:
            result['technical_field'] = match.group(1).strip()

        # 提取背景技术
        bg_pattern = r"背景技术[：:]\s*([\s\S]+?)(?=发明内容|$)"
        match = re.search(bg_pattern, text)
        if match:
            result['background_art'] = {
                'description': match.group(1).strip()
            }
            # 尝试提取引用文件
            ref_pattern = r"\[(\d+)\]([\s\S]+?)(?=\[\d+\]|$)"
            refs = re.findall(ref_pattern, match.group(1))
            if refs:
                result['background_art']['references'] = [
                    {'number': ref[0], 'content': ref[1].strip()} for ref in refs
                ]

        # 提取发明内容
        invention_pattern = r"发明内容[：:]\s*([\s\S]+?)(?=\S+?附图说明|具体实施方式|$)"
        match = re.search(invention_pattern, text)
        if match:
            invention_content = match.group(1)
            result['disclosure'] = self._parse_disclosure(invention_content)

        # 提取附图说明
        drawing_pattern = r"附图说明[：:]\s*([\s\S]+?)(?=具体实施方式|$)"
        match = re.search(drawing_pattern, text)
        if match:
            result['brief_description_of_drawings'] = self._parse_drawings_description(match.group(1))

        # 提取具体实施方式
        implementation_pattern = r"具体实施方式[：:]\s*([\s\S]+?)(?=$)"
        match = re.search(implementation_pattern, text)
        if match:
            result['detailed_description'] = self._parse_implementation(match.group(1))

        return result

    def _determine_claim_type(self, claim_text: str) -> str:
        """判断权利要求类型"""
        if '其特征是' in claim_text or '包括' in claim_text.split('，')[0]:
            return 'independent'
        elif '根据权利要求' in claim_text:
            return 'dependent'
        return 'unknown'

    def _parse_independent_claim(self, claim_text: str) -> dict[str, Any]:
        """解析独立权利要求"""
        result = {}

        # 分割前序部分和特征部分
        if '其特征是' in claim_text:
            parts = claim_text.split('其特征是', 1)
            result['preamble'] = parts[0].strip()
            result['characterizing_part'] = '其特征是' + parts[1].strip()
        else:
            result['preamble'] = claim_text.strip()
            result['characterizing_part'] = ''

        # 提取技术特征
        result['technical_features'] = self._extract_technical_features(claim_text)

        return result

    def _parse_dependent_claim(self, claim_text: str) -> dict[str, Any]:
        """解析从属权利要求"""
        result = {}

        # 提取引用关系
        ref_pattern = r"根据权利要求(\d+)"
        match = re.search(ref_pattern, claim_text)
        if match:
            result['reference_part'] = {
                'referenced_claims': [int(match.group(1))],
                'reference_text': match.group(0)
            }

        # 提取限定部分
        if '所述的' in claim_text:
            parts = claim_text.split('所述的', 1)
            if len(parts) > 1:
                result['limitation_part'] = '所述的' + parts[1].strip()

        return result

    def _extract_technical_features(self, text: str) -> list[str]:
        """提取技术特征"""
        # 简单的特征提取（可以根据需要改进）
        features = []
        # 按逗号分割，过滤过短的片段
        segments = text.split('，')
        for seg in segments:
            seg = seg.strip()
            if len(seg) > 5:  # 过滤过短的片段
                features.append(seg)
        return features

    def _check_claim_references(self, claims: list[dict]) -> dict[str, Any]:
        """检查权利要求引用关系"""
        issues = []
        for claim in claims:
            if claim['type'] == 'dependent':
                if 'reference_part' in claim:
                    for ref_num in claim['reference_part'].get('referenced_claims', []):
                        if ref_num >= claim['number']:
                            issues.append(f"权利要求{claim['number']}错误引用了在后的权利要求{ref_num}")

        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

    def _parse_disclosure(self, text: str) -> dict[str, Any]:
        """解析发明内容"""
        result = {}

        # 提取技术问题
        problem_pattern = r"要解决.*问题[：:]\s*([^\n]+)"
        match = re.search(problem_pattern, text)
        if match:
            result['technical_problem'] = match.group(1).strip()

        # 提取技术方案
        solution_pattern = r"技术方案[：:]\s*([^\n]+)"
        match = re.search(solution_pattern, text)
        if match:
            result['technical_solution'] = match.group(1).strip()

        # 提取有益效果
        effect_pattern = r"有益效果[：:]\s*([^\n]+)"
        match = re.search(effect_pattern, text)
        if match:
            result['beneficial_effects'] = match.group(1).strip()

        return result

    def _parse_drawings_description(self, text: str) -> list[dict[str, str]]:
        """解析附图说明"""
        drawings = []
        pattern = r"图(\d+)[是]?\s*([^\n]+)"
        matches = re.findall(pattern, text)

        for fig_num, description in matches:
            drawings.append({
                'figure_number': fig_num,
                'figure_description': description.strip()
            })

        return drawings

    def _parse_implementation(self, text: str) -> dict[str, Any]:
        """解析具体实施方式"""
        result = {
            'implementation': text.strip()[:500] + '...' if len(text) > 500 else text.strip()
        }

        # 提取实施例
        example_pattern = r"实施例\s*[：:]?\s*([^\n]+)"
        matches = re.findall(example_pattern, text)
        if matches:
            result['dev/examples'] = matches

        return result

    def validate_extraction(self, data: dict[str, Any], template_type: str) -> dict[str, Any]:
        """
        验证提取数据的完整性和合规性

        Args:
            data: 提取的数据
            template_type: 模板类型

        Returns:
            验证结果
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # 根据模板类型进行具体验证
        if template_type == 'abstract':
            if 'title' not in data or not data['title']:
                validation['errors'].append('缺少标题')
                validation['valid'] = False

            if 'word_count_check' in data and not data['word_count_check']['compliant']:
                validation['errors'].append(f"摘要字数{data['word_count_check']['actual']}超过限制{data['word_count_check']['limit']}")
                validation['valid'] = False

        elif template_type == 'claims':
            if not data.get('independent_claims'):
                validation['errors'].append('缺少独立权利要求')
                validation['valid'] = False

            if not data.get('reference_check', {}).get('valid'):
                validation['errors'].extend(data['reference_check']['issues'])
                validation['valid'] = False

        # 可以添加更多验证规则

        return validation

# 使用示例
if __name__ == '__main__':
    # 创建提取器实例
    extractor = PatentTemplateExtractor()

    # 示例：提取摘要
    sample_abstract = """
    一种基于深度学习的图像识别方法
    本发明涉及人工智能技术领域，具体涉及图像识别技术。
    要解决的技术问题是：现有图像识别方法准确率低、速度慢。
    技术方案是：采用改进的卷积神经网络模型进行特征提取和分类。
    主要用途：智能安防监控、医学影像分析等场景。
    """

    abstract_data = extractor.extract_abstract(sample_abstract)
    validation = extractor.validate_extraction(abstract_data, 'abstract')

    logger.info('提取的摘要数据：')
    print(json.dumps(abstract_data, ensure_ascii=False, indent=2))
    logger.info("\n验证结果：")
    print(json.dumps(validation, ensure_ascii=False, indent=2))
