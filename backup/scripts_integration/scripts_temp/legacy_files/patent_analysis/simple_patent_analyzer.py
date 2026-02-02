#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的专利分析器
Simple Patent Analyzer

专门用于分析给定的三个专利文件
"""

import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

# 导入专利检索集成模块
from patent_search_integration import PatentSearchIntegration


class SimplePatentAnalyzer:
    """简化的专利分析器"""
    
    def __init__(self):
        self.patent_search = PatentSearchIntegration()
        
    def extract_text_from_doc(self, file_path: str) -> str | None:
        """使用antiword提取.doc文件文本"""
        try:
            cmd = ['antiword', '-m', 'UTF-8', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                # 清理文本
                text = result.stdout
                # 删除图片标记
                text = re.sub(r'\[pic\]', '', text)
                # 删除过多空行
                text = re.sub(r'\n\s*\n+', '\n\n', text)
                return text
            else:
                logger.info(f"antiword执行失败: {result.stderr}")
                return None
        except Exception as e:
            logger.info(f"提取文本失败: {e}")
            return None
    
    def parse_patent_sections(self, text: str) -> Dict:
        """解析专利文档的各个部分"""
        sections = {
            'title': '',
            'abstract': '',
            'claims': '',
            'description': '',
            'drawings': ''
        }
        
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        # 查找标题
        title_match = re.search(r'一种集成式大豆蛋白酶解反应装置|一种耐强酸高温高压的豆粕水解反应釜|一种用于酵母梯度酶解的多温区连续流反应器', text)
        if title_match:
            sections['title'] = title_match.group(0)
        
        # 提取摘要（通常在开头的第一段）
        lines = [line.strip() for line in lines if line.strip()]
        if lines:
            # 找到"本实用新型公开了"开头的段落
            for i, line in enumerate(lines):
                if '本实用新型公开了' in line or '本发明公开了' in line:
                    # 合并相关段落作为摘要
                    abstract_lines = [line]
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith('根据权利要求') and not lines[j].startswith('技术领域'):
                        if lines[j] and len(lines[j]) > 10:
                            abstract_lines.append(lines[j])
                        j += 1
                        if len(abstract_lines) >= 3:
                            break
                    sections['abstract'] = '\n'.join(abstract_lines)
                    break
        
        # 提取权利要求
        claims_pattern = r'(根据权利要求\d+.*?)(?=\n\n|技术领域|说明书|背景技术|$)'
        claims_matches = re.findall(claims_pattern, text, re.DOTALL)
        if claims_matches:
            # 整理权利要求格式
            formatted_claims = []
            for claim in claims_matches:
                # 清理每个权利要求
                claim = claim.strip()
                if '根据权利要求' in claim:
                    # 提取权利要求编号
                    num_match = re.search(r'根据权利要求(\d+)', claim)
                    if num_match:
                        num = num_match.group(1)
                        # 提取特征部分
                        feature_part = claim.split('，其特征在于，')[-1] if '，其特征在于，' in claim else claim
                        formatted_claims.append(f"{num}. {feature_part}")
            
            if formatted_claims:
                sections['claims'] = '\n'.join(formatted_claims)
        
        # 提取说明书内容
        desc_patterns = [
            r'技术领域[：:]?\s*(.+?)(?=\n\n|$)',
            r'背景技术[：:]?\s*(.+?)(?=\n\n|$)',
            r'发明内容[：:]?\s*(.+?)(?=\n\n|$)',
            r'具体实施方式[：:]?\s*(.+?)(?=\n\n|$)'
        ]
        
        desc_parts = []
        for pattern in desc_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                desc_parts.append(match.group(0))
        
        if desc_parts:
            sections['description'] = '\n\n'.join(desc_parts)
        else:
            # 如果没有找到明确的标题，提取技术内容
            tech_content = []
            for line in lines:
                if '反应罐体' in line or '温度控制' in line or '酶解' in line:
                    tech_content.append(line)
            if tech_content:
                sections['description'] = '\n'.join(tech_content[:20])
        
        # 提取附图说明
        if '附图说明' in text or '图1' in text:
            drawings_pattern = r'(附图说明[：:]?\s*.+?)(?=\n\n|$)'
            match = re.search(drawings_pattern, text, re.DOTALL)
            if match:
                sections['drawings'] = match.group(1)
            elif '图1' in text:
                sections['drawings'] = '文档中包含附图标记'
        
        return sections
    
    def analyze_patent(self, file_path: str) -> Dict:
        """分析单个专利文件"""
        logger.info(f"\n分析文件: {Path(file_path).name}")
        logger.info(str('-' * 60))
        
        # 提取文本
        text = self.extract_text_from_doc(file_path)
        if not text:
            return {'error': '无法提取文档内容'}
        
        # 解析各部分
        sections = self.parse_patent_sections(text)
        
        # 分析各部分
        analysis = {
            'file_name': Path(file_path).name,
            'sections': sections,
            'analysis_results': {
                'abstract': self._analyze_abstract(sections['abstract']),
                'claims': self._analyze_claims(sections['claims']),
                'description': self._analyze_description(sections['description']),
                'drawings': self._analyze_drawings(sections['drawings']),
                'creativity': self._analyze_creativity(sections),
                'article_26': self._analyze_article_26(sections)
            }
        }
        
        # 计算综合得分
        scores = [
            analysis['analysis_results']['abstract']['score'] * 0.15,
            analysis['analysis_results']['claims']['score'] * 0.30,
            analysis['analysis_results']['description']['score'] * 0.25,
            analysis['analysis_results']['drawings']['score'] * 0.10,
            analysis['analysis_results']['creativity']['score'] * 0.15,
            analysis['analysis_results']['article_26']['score'] * 0.05
        ]
        analysis['overall_score'] = sum(scores)
        
        # 显示简要结果
        logger.info(f"  综合得分: {analysis['overall_score']:.1f}/100")
        
        issues = []
        for key, result in analysis['analysis_results'].items():
            if result['score'] < 70:
                issues.append(key)
        
        if issues:
            logger.info(f"  需要改进: {', '.join(issues)}")
        else:
            logger.info('  各项指标均达到良好水平')
        
        return analysis
    
    def _analyze_abstract(self, abstract: str) -> Dict:
        """分析摘要"""
        if not abstract:
            return {'score': 0, 'issues': ['缺少说明书摘要']}
        
        score = 50
        issues = []
        
        # 字数检查
        word_count = len(abstract)
        if word_count < 50:
            issues.append('摘要过短')
            score -= 20
        elif word_count > 300:
            issues.append('摘要过长')
            score -= 10
        
        # 内容检查
        if '技术问题' in abstract or '解决' in abstract:
            score += 10
        if '技术方案' in abstract or '实现' in abstract:
            score += 10
        if '有益效果' in abstract or '优点' in abstract or '效果' in abstract:
            score += 10
        
        return {'score': min(100, score), 'issues': issues, 'word_count': word_count}
    
    def _analyze_claims(self, claims: str) -> Dict:
        """分析权利要求书"""
        if not claims:
            return {'score': 0, 'issues': ['缺少权利要求书']}
        
        # 统计权利要求数量
        claim_count = len(re.findall(r'^\d+\.', claims, re.MULTILINE))
        
        score = 30
        issues = []
        
        if claim_count == 0:
            # 尝试其他格式
            claim_count = len(re.findall(r'\d+\.', claims))
        
        if claim_count > 0:
            score += 30
        
        if claim_count > 10:
            issues.append(f"权利要求数量过多({claim_count}项)")
            score -= 10
        
        # 检查是否有独立权利要求
        if '1.' in claims or '1、' in claims:
            score += 20
        
        # 检查是否有从属权利要求
        if '根据权利要求' in claims:
            score += 20
        
        return {'score': min(100, score), 'issues': issues, 'claim_count': claim_count}
    
    def _analyze_description(self, description: str) -> Dict:
        """分析说明书"""
        if not description:
            return {'score': 0, 'issues': ['缺少说明书']}
        
        score = 30
        issues = []
        
        # 检查必要部分
        required_parts = ['技术领域', '背景技术', '发明内容', '具体实施方式']
        found_parts = []
        for part in required_parts:
            if part in description:
                found_parts.append(part)
                score += 15
        
        # 检查技术问题
        if '技术问题' in description or '要解决' in description:
            score += 10
        
        # 检查技术方案
        if '技术方案' in description or '解决方案' in description:
            score += 10
        
        # 检查有益效果
        if '有益效果' in description or '技术效果' in description:
            score += 10
        
        if len(found_parts) < 2:
            issues.append(f"缺少必要部分（仅找到: {', '.join(found_parts)}）")
        
        return {'score': min(100, score), 'issues': issues, 'found_parts': found_parts}
    
    def _analyze_drawings(self, drawings: str) -> Dict:
        """分析附图说明"""
        if not drawings:
            return {'score': 50, 'issues': ['未找到附图说明']}
        
        score = 50
        issues = []
        
        if '图1' in drawings or '附图' in drawings:
            score += 30
        
        if len(drawings) > 100:
            score += 20
        
        return {'score': min(100, score), 'issues': issues}
    
    def _analyze_creativity(self, sections: Dict) -> Dict:
        """分析创造性"""
        score = 60  # 基础分
        issues = []
        
        # 基于内容评估
        content = '\n'.join(sections.values())
        
        # 技术特征数量
        if sections.get('claims'):
            features = re.findall(r'[，；;]\s*([^，；;]{10,30})', sections['claims'])
            if len(features) > 3:
                score += 10
        
        # 技术效果
        if '显著' in content or '提高' in content or '降低' in content:
            score += 10
        
        # 创新性词汇
        if '集成' in content or '创新' in content or '改进' in content:
            score += 10
        
        # 解决的问题
        if '背景技术' in sections.get('description', ''):
            score += 10
        
        return {'score': min(100, score), 'issues': issues}
    
    def _analyze_article_26(self, sections: Dict) -> Dict:
        """分析专利法第26条符合性"""
        score = 60  # 基础分
        issues = []
        
        # 检查充分公开
        description = sections.get('description', '')
        if description:
            if len(description) < 200:
                issues.append('说明书过于简短')
                score -= 20
            
            if not re.search(r'技术领域|背景技术|具体实施方式', description):
                issues.append('缺少必要的技术描述部分')
                score -= 20
        else:
            issues.append('缺少说明书')
            score -= 40
        
        # 检查权利要求支持
        claims = sections.get('claims', '')
        if claims and description:
            # 简单检查主要术语是否在说明书中出现
            claim_terms = set(re.findall(r'[\u4e00-\u9fa5]{3,}', claims))
            desc_terms = set(re.findall(r'[\u4e00-\u9fa5]{3,}', description))
            
            overlap = len(claim_terms & desc_terms) / len(claim_terms) if claim_terms else 0
            
            if overlap < 0.5:
                issues.append('权利要求可能未得到说明书充分支持')
                score -= 20
        elif not claims:
            issues.append('缺少权利要求书')
            score -= 30
        
        return {'score': min(100, score), 'issues': issues}
    
    def generate_report(self, analysis: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append(f"# {analysis['file_name']} 专利申请文件分析报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n## 综合得分: {analysis['overall_score']:.1f}/100")
        
        # 各部分分析结果
        for key, result in analysis['analysis_results'].items():
            section_name = {
                'abstract': '说明书摘要',
                'claims': '权利要求书',
                'description': '说明书',
                'drawings': '说明书附图',
                'creativity': '创造性分析',
                'article_26': '专利法第26条符合性'
            }.get(key, key)
            
            report.append(f"\n## {section_name}")
            report.append(f"得分: {result['score']}/100")
            
            if result.get('issues'):
                report.append("\n### ⚠️ 存在问题:")
                for issue in result['issues']:
                    report.append(f"- {issue}")
        
        # 总体评价
        report.append("\n## 总体评价")
        if analysis['overall_score'] >= 85:
            report.append('✅ 优秀，具备高度授权前景')
        elif analysis['overall_score'] >= 70:
            report.append('✅ 良好，具备授权前景')
        elif analysis['overall_score'] >= 60:
            report.append('⚠️ 合格，建议完善后提交')
        else:
            report.append('❌ 需要重大修改')
        
        return '\n'.join(report)

def analyze_all_patents():
    """分析所有专利"""
    patent_dir = Path('/Users/xujian/Athena工作平台/工作/专利分析/2025.12.12三件')
    patent_files = list(patent_dir.glob('*.doc'))
    
    logger.info(str('=' * 80))
    logger.info('专利申请文件分析报告')
    logger.info(str('=' * 80))
    
    analyzer = SimplePatentAnalyzer()
    
    for patent_file in patent_files:
        # 分析专利
        analysis = analyzer.analyze_patent(str(patent_file))
        
        if 'error' not in analysis:
            # 生成报告
            report = analyzer.generate_report(analysis)
            
            # 保存报告
            report_path = patent_file.parent / (patent_file.stem + '_分析报告.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"✅ 报告已保存至: {report_path}\n")

if __name__ == '__main__':
    analyze_all_patents()
