#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合专利申请文件分析器
Comprehensive Patent Application Analyzer

集成多源检索，专注于分析说明书摘要、权利要求书、说明书和说明书附图
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

# 导入专利检索集成模块
from patent_search_integration import PatentSearchIntegration


class ComprehensivePatentAnalyzer:
    """综合专利申请文件分析器"""
    
    def __init__(self):
        self.patent_search = PatentSearchIntegration()
        self.analysis_results = {
            'abstract': {},
            'claims': {},
            'description': {},
            'drawings': {},
            'creativity': {},
            'article_26': {},
            'overall': {}
        }
        
    def load_patent_document(self, file_path: str) -> Dict | None:
        """加载专利文档"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() in ['.doc', '.docx']:
                return self._load_word_document(file_path)
            elif file_path.suffix.lower() in ['.txt', '.md']:
                return self._load_text_document(file_path)
            else:
                logger.info(f"不支持的文件格式: {file_path.suffix}")
                return None
                
        except Exception as e:
            logger.info(f"加载文件失败: {e}")
            return None
    
    def _load_word_document(self, file_path: Path) -> Dict:
        """加载Word文档"""
        try:
            from docx import Document
            doc = Document(file_path)
            
            # 提取文本内容
            content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text.strip())
            
            full_text = '\n'.join(content)
            
        except ImportError:
            logger.info('未安装python-docx库，尝试读取文本格式')
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
        
        # 解析各部分
        sections = self._parse_target_sections(full_text)
        
        return {
            'content': full_text,
            'sections': sections,
            'file_path': str(file_path),
            'file_type': 'word'
        }
    
    def _load_text_document(self, file_path: Path) -> Dict:
        """加载文本文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = self._parse_target_sections(content)
        
        return {
            'content': content,
            'sections': sections,
            'file_path': str(file_path),
            'file_type': 'text'
        }
    
    def _parse_target_sections(self, content: str) -> Dict:
        """解析目标部分：摘要、权利要求书、说明书、说明书附图"""
        sections = {}
        
        # 使用更精确的正则表达式匹配
        # 摘要部分
        abstract_match = re.search(r'(?:摘要|技术摘要)[\s\:：]\s*(.+?)(?=权利要求书|说明书|说明书附图|$)', content, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            sections['abstract'] = abstract_match.group(1).strip()
        
        # 权利要求书部分
        claims_patterns = [
            r'(?:权利要求书|权利要求)[\s\:：]\s*(.+?)(?=说明书|说明书附图|说明书摘要|$)',
            r'权利要求\s*\d+[\s\.\、]',
        ]
        
        for pattern in claims_patterns:
            if '\d+' in pattern:
                # 如果是权利要求开始模式，向上查找权利要求书开始
                claims_start = re.search(pattern, content)
                if claims_start:
                    start_pos = content.rfind('权利要求书', 0, claims_start.start())
                    if start_pos == -1:
                        start_pos = claims_start.start()
                    
                    claims_end = re.search(r'说明书[\s\:：]', content[start_pos:])
                    if claims_end:
                        claims_content = content[start_pos:start_pos+claims_end.start()]
                    else:
                        claims_content = content[start_pos:start_pos+2000]  # 取一段合理长度
                    
                    sections['claims'] = claims_content.strip()
                    break
            else:
                claims_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if claims_match:
                    sections['claims'] = claims_match.group(1).strip()
                    break
        
        # 说明书部分
        desc_patterns = [
            r'说明书[\s\:：]\s*(.+?)(?=说明书附图|说明书摘要|权利要求书|$)',
            r'技术领域[\s\:：]',  # 从技术领域开始到说明书附图
        ]
        
        for pattern in desc_patterns:
            if '技术领域' in pattern:
                tech_field_pos = re.search(pattern, content)
                if tech_field_pos:
                    desc_start = tech_field_pos.start()
                    desc_end = re.search(r'说明书附图[\s\:：]', content[desc_start:])
                    if desc_end:
                        sections['description'] = content[desc_start:desc_start+desc_end.start()].strip()
                        break
                    else:
                        # 取技术领域之后的大部分内容
                        sections['description'] = content[desc_start:desc_start+5000].strip()
                        break
            else:
                desc_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if desc_match:
                    sections['description'] = desc_match.group(1).strip()
                    break
        
        # 说明书附图部分
        drawings_match = re.search(r'说明书附图[\s\:：]\s*(.+?)(?=说明书摘要|摘要附图|$)', content, re.DOTALL | re.IGNORECASE)
        if drawings_match:
            sections['drawings_description'] = drawings_match.group(1).strip()
        
        return sections
    
    def analyze_abstract(self, patent_doc: Dict) -> Dict:
        """分析说明书摘要"""
        sections = patent_doc.get('sections', {})
        abstract = sections.get('abstract', '')
        
        analysis = {
            'content': abstract,
            'word_count': len(abstract),
            'has_technical_problem': False,
            'has_technical_solution': False,
            'has_beneficial_effect': False,
            'issues': [],
            'score': 0
        }
        
        if not abstract:
            analysis['issues'].append('缺少说明书摘要')
            analysis['score'] = 0
            return analysis
        
        # 检查字数（摘要通常50-300字）
        if analysis['word_count'] < 50:
            analysis['issues'].append('摘要过短（少于50字）')
        elif analysis['word_count'] > 300:
            analysis['issues'].append('摘要过长（超过300字）')
        
        # 检查必要内容
        if '技术问题' in abstract or '问题' in abstract:
            analysis['has_technical_problem'] = True
        
        if '技术方案' in abstract or '解决方案' in abstract or '实现' in abstract:
            analysis['has_technical_solution'] = True
        
        if '有益效果' in abstract or '效果' in abstract or '优点' in abstract:
            analysis['has_beneficial_effect'] = True
        
        # 计算得分
        score = 50  # 基础分
        if 50 <= analysis['word_count'] <= 300:
            score += 20
        if analysis['has_technical_problem']:
            score += 10
        if analysis['has_technical_solution']:
            score += 10
        if analysis['has_beneficial_effect']:
            score += 10
        
        analysis['score'] = min(100, score)
        
        self.analysis_results['abstract'] = analysis
        return analysis
    
    def analyze_claims(self, patent_doc: Dict) -> Dict:
        """分析权利要求书"""
        sections = patent_doc.get('sections', {})
        claims = sections.get('claims', '')
        
        analysis = {
            'content': claims,
            'total_claims': 0,
            'independent_claims': 0,
            'dependent_claims': 0,
            'main_claim_features': [],
            'issues': [],
            'score': 0,
            'claim_hierarchy': []
        }
        
        if not claims:
            analysis['issues'].append('缺少权利要求书')
            analysis['score'] = 0
            return analysis
        
        # 提取权利要求
        claim_pattern = r'(\d+)[\.\、]\s*(.+?)(?=\n\s*\d+[\.\、]|\n\n|$)'
        claim_matches = re.findall(claim_pattern, claims, re.DOTALL)
        
        analysis['total_claims'] = len(claim_matches)
        
        # 分析权利要求层次
        for claim_num, claim_content in claim_matches:
            claim_num = int(claim_num)
            claim_text = claim_content.strip()
            
            # 检查是否为从属权利要求
            is_dependent = re.search(r'根据权利要求(\d+)', claim_text)
            
            if is_dependent:
                analysis['dependent_claims'] += 1
                dependent_on = int(is_dependent.group(1))
                analysis['claim_hierarchy'].append({
                    'number': claim_num,
                    'type': 'dependent',
                    'depends_on': dependent_on,
                    'content': claim_text[:100] + '...' if len(claim_text) > 100 else claim_text
                })
            else:
                if claim_num == 1:
                    analysis['independent_claims'] += 1
                    # 提取独立权利要求1的技术特征
                    features = re.split(r'[，；;和及与]', claim_text)
                    analysis['main_claim_features'] = [f.strip() for f in features if f.strip() and len(f.strip()) > 2]
                
                analysis['claim_hierarchy'].append({
                    'number': claim_num,
                    'type': 'independent',
                    'content': claim_text[:100] + '...' if len(claim_text) > 100 else claim_text
                })
        
        # 检查问题
        if analysis['total_claims'] == 0:
            analysis['issues'].append('未找到有效的权利要求')
        
        if analysis['independent_claims'] > 2:
            analysis['issues'].append(f"独立权利要求过多({analysis['independent_claims']}项)")
        
        if analysis['total_claims'] > 30:
            analysis['issues'].append(f"权利要求总数过多({analysis['total_claims']}项)")
        
        # 检查引用关系
        invalid_refs = re.findall(r'如权利要求(\d+)', claims)
        if invalid_refs:
            analysis['issues'].append("权利要求中使用了'如权利要求'的不规范引用")
        
        # 计算得分
        score = 30  # 基础分
        if 1 <= analysis['independent_claims'] <= 2:
            score += 30
        if analysis['total_claims'] <= 20:
            score += 20
        if analysis['main_claim_features']:
            score += 10
        if not invalid_refs:
            score += 10
        
        analysis['score'] = min(100, score)
        
        self.analysis_results['claims'] = analysis
        return analysis
    
    def analyze_description(self, patent_doc: Dict) -> Dict:
        """分析说明书"""
        sections = patent_doc.get('sections', {})
        description = sections.get('description', '')
        
        analysis = {
            'content': description,
            'word_count': len(description),
            'has_technical_field': False,
            'has_background_art': False,
            'has_invention_content': False,
            'has_embodiments': False,
            'issues': [],
            'score': 0,
            'sections_found': []
        }
        
        if not description:
            analysis['issues'].append('缺少说明书')
            analysis['score'] = 0
            return analysis
        
        # 检查必要部分
        required_sections = {
            '技术领域': r'技术领域[\s\:：]\s*(.+?)(?=\n\n|背景技术|$)',
            '背景技术': r'背景技术[\s\:：]\s*(.+?)(?=\n\n|发明内容|技术问题|$)',
            '发明内容': r'发明内容[\s\:：]\s*(.+?)(?=\n\n|具体实施方式|有益效果|$)',
            '具体实施方式': r'具体实施方式[\s\:：]\s*(.+?)$',
            '实施例': r'实施例[\s\:：]\s*(.+?)(?=\n\n|$)'
        }
        
        for section_name, pattern in required_sections.items():
            if re.search(pattern, description, re.IGNORECASE | re.DOTALL):
                analysis['sections_found'].append(section_name)
                if section_name == '技术领域':
                    analysis['has_technical_field'] = True
                elif section_name == '背景技术':
                    analysis['has_background_art'] = True
                elif '发明内容' in section_name or '技术问题' in section_name:
                    analysis['has_invention_content'] = True
                elif '实施' in section_name:
                    analysis['has_embodiments'] = True
        
        # 检查技术问题
        if not re.search(r'技术问题|要解决|缺陷|不足', description):
            analysis['issues'].append('未明确要解决的技术问题')
        
        # 检查技术方案
        if not re.search(r'技术方案|解决方案|实现方式', description):
            analysis['issues'].append('缺少明确的技术方案描述')
        
        # 检查有益效果
        if not re.search(r'有益效果|技术效果|优点|优势', description):
            analysis['issues'].append('缺少技术效果说明')
        
        # 计算得分
        score = 20  # 基础分
        if analysis['word_count'] > 1000:
            score += 20
        if len(analysis['sections_found']) >= 4:
            score += 30
        elif len(analysis['sections_found']) >= 3:
            score += 20
        if analysis['has_embodiments']:
            score += 20
        if not analysis['issues']:
            score += 10
        
        analysis['score'] = min(100, score)
        
        self.analysis_results['description'] = analysis
        return analysis
    
    def analyze_drawings_description(self, patent_doc: Dict) -> Dict:
        """分析说明书附图"""
        sections = patent_doc.get('sections', {})
        drawings_desc = sections.get('drawings_description', '')
        
        analysis = {
            'content': drawings_desc,
            'has_figures': False,
            'figure_count': 0,
            'has_detailed_description': False,
            'issues': [],
            'score': 0
        }
        
        if not drawings_desc:
            analysis['issues'].append('缺少说明书附图部分')
            analysis['score'] = 0
            return analysis
        
        # 查找附图标记
        figures = re.findall(r'图(\d+)', drawings_desc)
        if figures:
            analysis['has_figures'] = True
            analysis['figure_count'] = len(set(figures))
        
        # 检查是否有详细的附图说明
        if len(drawings_desc) > 200:
            analysis['has_detailed_description'] = True
        
        # 计算得分
        score = 30  # 基础分
        if analysis['has_figures']:
            score += 30
        if analysis['figure_count'] > 0:
            score += 20
        if analysis['has_detailed_description']:
            score += 20
        
        analysis['score'] = min(100, score)
        
        self.analysis_results['drawings'] = analysis
        return analysis
    
    def analyze_creativity_with_search(self, patent_doc: Dict) -> Dict:
        """结合专利检索进行创造性分析"""
        logger.info("\n🔍 开始专利检索分析...")
        
        # 提取关键词
        claims_analysis = self.analysis_results.get('claims', {})
        features = claims_analysis.get('main_claim_features', [])
        
        # 从说明书中提取技术领域
        desc_analysis = self.analysis_results.get('description', {})
        technical_field = ''
        if desc_analysis.get('has_technical_field'):
            field_match = re.search(r'技术领域[\s\:：]\s*(.+?)(?=\n\n|背景技术|$)', 
                                   patent_doc.get('sections', {}).get('description', ''), 
                                   re.IGNORECASE | re.DOTALL)
            if field_match:
                technical_field = field_match.group(1).strip()
        
        # 生成关键词
        keywords = []
        for feature in features[:5]:  # 取前5个特征作为关键词
            # 提取关键词（去除常见词汇）
            feature_words = [w for w in feature.split() if len(w) > 1 and w not in ['的', '用于', '设有', '包括']]
            keywords.extend(feature_words[:2])  # 每个特征取前2个词
        
        # 执行检索
        local_results = self.patent_search.search_local_database(keywords, technical_field)
        external_results = self.patent_search.search_external_patents(keywords, technical_field)
        
        all_results = local_results + external_results
        
        # 进行对比分析
        comparison = self.patent_search.compare_with_prior_art(features, all_results)
        
        # 计算创造性得分
        novelty_score = comparison.get('novelty_analysis', {}).get('score', 0)
        
        # 基于检索结果调整创造性评分
        creativity_score = 50  # 基础分
        creativity_score += novelty_score * 40  # 新颖性占40%
        
        # 如果有最接近的现有技术，检查区别
        if comparison.get('closest_prior_art'):
            # 检查技术问题是否相同
            problem_keywords = ['解决', '克服', '改进', '提高']
            has_different_problem = True
            # 这里可以添加更复杂的逻辑判断
            
            if has_different_problem:
                creativity_score += 10
        
        # 结合之前的基础分析
        base_creativity = self._basic_creativity_assessment(patent_doc)
        creativity_score = (creativity_score + base_creativity) / 2
        
        analysis = {
            'search_results_count': len(all_results),
            'local_results': len(local_results),
            'external_results': len(external_results),
            'keywords_used': keywords[:5],
            'novelty_analysis': comparison.get('novelty_analysis', {}),
            'closest_prior_art': comparison.get('closest_prior_art', [])[:3],
            'obviousness_assessment': comparison.get('obviousness_assessment', ''),
            'recommendations': comparison.get('recommendations', []),
            'score': min(100, creativity_score),
            'assessment': self._generate_creativity_assessment(creativity_score, comparison)
        }
        
        self.analysis_results['creativity'] = analysis
        return analysis
    
    def _basic_creativity_assessment(self, patent_doc: Dict) -> float:
        """基础创造性评估（不依赖检索）"""
        score = 50
        
        # 检查技术特征的复杂度
        claims = self.analysis_results.get('claims', {})
        features = claims.get('main_claim_features', [])
        if len(features) > 5:
            score += 10
        
        # 检查说明书的完整性
        desc = self.analysis_results.get('description', {})
        if desc.get('has_embodiments'):
            score += 10
        
        # 检查技术效果
        sections = patent_doc.get('sections', {})
        if '有益效果' in sections.get('description', '') or '技术效果' in sections.get('description', ''):
            score += 10
        
        # 检查是否解决了技术问题
        if '技术问题' in sections.get('description', ''):
            score += 10
        
        return min(100, score)
    
    def _generate_creativity_assessment(self, score: float, comparison: Dict) -> str:
        """生成创造性评估意见"""
        novelty_status = comparison.get('novelty_analysis', {}).get('status', '')
        
        if score >= 85:
            return '具有突出的实质性特点和显著的进步，具备高度创造性'
        elif score >= 70:
            if novelty_status == 'highly_novel':
                return '技术方案具有新颖性，具备创造性'
            else:
                return '具备一定的创造性，建议强调技术效果和进步性'
        elif score >= 55:
            return '创造性一般，需要提供更多的技术效果证据'
        else:
            return '创造性不足，建议重新审视技术方案的创新点'
    
    def analyze_article_26_compliance(self, patent_doc: Dict) -> Dict:
        """分析专利法第26条符合性"""
        sections = patent_doc.get('sections', {})
        
        analysis = {
            'section_3': {
                'clarity': 0,
                'completeness': 0,
                'enablement': 0,
                'issues': []
            },
            'section_4': {
                'support': 0,
                'clarity': 0,
                'brevity': 0,
                'issues': []
            },
            'overall_score': 0
        }
        
        # 第26条第3款：充分公开
        description = sections.get('description', '')
        if description:
            # 清楚性
            clarity_score = 100
            if len(description) < 500:
                analysis['section_3']['issues'].append('说明书过于简短，描述不够清楚')
                clarity_score -= 30
            
            analysis['section_3']['clarity'] = max(0, clarity_score)
            
            # 完整性
            completeness_score = 100
            required_parts = ['技术领域', '背景技术', '发明内容', '具体实施方式']
            missing_parts = []
            for part in required_parts:
                if part not in description:
                    missing_parts.append(part)
                    completeness_score -= 25
            
            if missing_parts:
                analysis['section_3']['issues'].append(f"缺少必要部分: {', '.join(missing_parts)}")
            
            analysis['section_3']['completeness'] = max(0, completeness_score)
            
            # 能够实现
            enablement_score = 100
            if not re.search(r'实施例|具体实施方式', description):
                analysis['section_3']['issues'].append('缺少具体实施方式，可能无法实现')
                enablement_score -= 40
            
            if not re.search(r'技术效果|有益效果', description):
                analysis['section_3']['issues'].append('缺少技术效果说明')
                enablement_score -= 20
            
            analysis['section_3']['enablement'] = max(0, enablement_score)
        
        # 第26条第4款：权利要求书以说明书为依据
        claims = sections.get('claims', '')
        if claims and description:
            # 支持度
            support_score = 100
            # 提取权利要求中的术语
            claim_terms = set(re.findall(r'[\u4e00-\u9fa5]{2,}', claims))
            desc_terms = set(re.findall(r'[\u4e00-\u9fa5]{2,}', description))
            
            # 简单检查是否有大量权利要求中的术语在说明书中未出现
            missing_terms = len(claim_terms - desc_terms)
            if missing_terms > 20:  # 如果超过20个术语未在说明书中出现
                analysis['section_4']['issues'].append('权利要求中的部分技术特征未在说明书中充分描述')
                support_score -= 30
            
            analysis['section_4']['support'] = max(0, support_score)
            
            # 清楚性
            clarity_score = 100
            unclear_terms = ['优选', '大约', '左右', '约']
            for term in unclear_terms:
                if term in claims:
                    analysis['section_4']['issues'].append(f"权利要求中使用了不确定词语'{term}'")
                    clarity_score -= 10
            
            analysis['section_4']['clarity'] = max(0, clarity_score)
            
            # 简要性
            claim_count = len(re.findall(r'^\s*\d+[\.\、]', claims, re.MULTILINE))
            brevity_score = 100
            
            if claim_count > 20:
                analysis['section_4']['issues'].append(f"权利要求项数过多({claim_count}项)")
                brevity_score -= 20
            
            analysis['section_4']['brevity'] = max(0, brevity_score)
        
        # 计算总分
        section_3_avg = sum([analysis['section_3']['clarity'], 
                            analysis['section_3']['completeness'], 
                            analysis['section_3']['enablement']]) / 3
        section_4_avg = sum([analysis['section_4']['support'], 
                            analysis['section_4']['clarity'], 
                            analysis['section_4']['brevity']]) / 3
        analysis['overall_score'] = (section_3_avg + section_4_avg) / 2
        
        self.analysis_results['article_26'] = analysis
        return analysis
    
    def generate_comprehensive_report(self, patent_doc: Dict) -> str:
        """生成综合分析报告"""
        report = []
        report.append('# 专利申请文件综合分析报告')
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"文件路径: {patent_doc.get('file_path', 'N/A')}")
        report.append(f"文件类型: {patent_doc.get('file_type', 'N/A')}")
        
        # 1. 说明书摘要分析
        abstract = self.analysis_results.get('abstract', {})
        report.append("\n## 一、说明书摘要分析")
        report.append(f"得分: {abstract.get('score', 0)}/100")
        report.append(f"字数: {abstract.get('word_count', 0)}字")
        if abstract.get('issues'):
            report.append("\n### ⚠️ 存在问题:")
            for issue in abstract['issues']:
                report.append(f"- {issue}")
        
        # 2. 权利要求书分析
        claims = self.analysis_results.get('claims', {})
        report.append("\n## 二、权利要求书分析")
        report.append(f"得分: {claims.get('score', 0)}/100")
        report.append(f"权利要求总数: {claims.get('total_claims', 0)}")
        report.append(f"独立权利要求: {claims.get('independent_claims', 0)}")
        report.append(f"从属权利要求: {claims.get('dependent_claims', 0)}")
        if claims.get('issues'):
            report.append("\n### ⚠️ 存在问题:")
            for issue in claims['issues']:
                report.append(f"- {issue}")
        
        # 3. 说明书分析
        description = self.analysis_results.get('description', {})
        report.append("\n## 三、说明书分析")
        report.append(f"得分: {description.get('score', 0)}/100")
        report.append(f"字数: {description.get('word_count', 0)}字")
        report.append(f"包含部分: {', '.join(description.get('sections_found', []))}")
        if description.get('issues'):
            report.append("\n### ⚠️ 存在问题:")
            for issue in description['issues']:
                report.append(f"- {issue}")
        
        # 4. 说明书附图分析
        drawings = self.analysis_results.get('drawings', {})
        report.append("\n## 四、说明书附图分析")
        report.append(f"得分: {drawings.get('score', 0)}/100")
        report.append(f"附图数量: {drawings.get('figure_count', 0)}")
        if drawings.get('issues'):
            report.append("\n### ⚠️ 存在问题:")
            for issue in drawings['issues']:
                report.append(f"- {issue}")
        
        # 5. 创造性分析（含专利检索）
        creativity = self.analysis_results.get('creativity', {})
        report.append("\n## 五、创造性分析（含专利检索）")
        report.append(f"得分: {creativity.get('score', 0)}/100")
        report.append(f"评估意见: {creativity.get('assessment', '')}")
        
        if creativity.get('keywords_used'):
            report.append(f"\n**检索关键词**: {', '.join(creativity['keywords_used'])}")
        
        report.append(f"\n**检索结果**:")
        report.append(f"- 本地数据库: {creativity.get('local_results', 0)}个")
        report.append(f"- 外部数据库: {creativity.get('external_results', 0)}个")
        
        novelty = creativity.get('novelty_analysis', {})
        if novelty:
            report.append(f"\n**新颖性分析**:")
            report.append(f"- 状态: {novelty.get('status', 'N/A')}")
            report.append(f"- 得分: {novelty.get('score', 0):.2f}")
            report.append(f"- 理由: {novelty.get('reason', 'N/A')}")
        
        if creativity.get('closest_prior_art'):
            report.append(f"\n**最接近的现有技术**:")
            for i, art in enumerate(creativity['closest_prior_art'][:3], 1):
                report.append(f"{i}. {art.get('patent_name', 'N/A')} (来源: {art.get('source', 'N/A')})")
        
        if creativity.get('recommendations'):
            report.append(f"\n**改进建议**:")
            for rec in creativity['recommendations']:
                report.append(f"- {rec}")
        
        # 6. 专利法第26条符合性分析
        art26 = self.analysis_results.get('article_26', {})
        report.append("\n## 六、专利法第26条符合性分析")
        report.append(f"总体得分: {art26.get('overall_score', 0):.1f}/100")
        
        s3 = art26.get('section_3', {})
        report.append("\n### 第26条第3款（充分公开）")
        report.append(f"- 清楚性: {s3.get('clarity', 0)}/100")
        report.append(f"- 完整性: {s3.get('completeness', 0)}/100")
        report.append(f"- 能够实现: {s3.get('enablement', 0)}/100")
        if s3.get('issues'):
            report.append("\n**问题**:")
            for issue in s3['issues']:
                report.append(f"- {issue}")
        
        s4 = art26.get('section_4', {})
        report.append("\n### 第26条第4款（权利要求书以说明书为依据）")
        report.append(f"- 支持度: {s4.get('support', 0)}/100")
        report.append(f"- 清楚性: {s4.get('clarity', 0)}/100")
        report.append(f"- 简要性: {s4.get('brevity', 0)}/100")
        if s4.get('issues'):
            report.append("\n**问题**:")
            for issue in s4['issues']:
                report.append(f"- {issue}")
        
        # 7. 综合评价
        report.append("\n## 七、综合评价")
        
        # 计算综合得分
        scores = [
            abstract.get('score', 0) * 0.15,
            claims.get('score', 0) * 0.30,
            description.get('score', 0) * 0.25,
            drawings.get('score', 0) * 0.10,
            creativity.get('score', 0) * 0.15,
            art26.get('overall_score', 0) * 0.05
        ]
        total_score = sum(scores)
        
        report.append(f"\n**综合得分**: {total_score:.1f}/100")
        
        if total_score >= 85:
            report.append("\n✅ **总体评价**: 优秀，具备高度授权前景")
        elif total_score >= 70:
            report.append("\n✅ **总体评价**: 良好，具备授权前景")
        elif total_score >= 60:
            report.append("\n⚠️ **总体评价**: 合格，建议完善后提交")
        else:
            report.append("\n❌ **总体评价**: 需要重大修改")
        
        return '\n'.join(report)

def main():
    """主函数"""
    logger.info(str('=' * 70))
    logger.info('        综合专利申请文件分析器')
    logger.info(str('=' * 70))
    logger.info("\n📋 分析范围:")
    logger.info('   ✓ 说明书摘要')
    logger.info('   ✓ 权利要求书') 
    logger.info('   ✓ 说明书')
    logger.info('   ✓ 说明书附图')
    logger.info("\n🔍 特色功能:")
    logger.info('   ✓ 集成本地PostgreSQL专利数据库检索')
    logger.info('   ✓ 外部专利数据库检索')
    logger.info('   ✓ 创造性对比分析')
    logger.info('   ✓ 专利法第26条符合性审查')
    
    file_path = input("\n\n请输入专利文件路径: ").strip().strip('"')
    if not Path(file_path).exists():
        logger.info('❌ 文件不存在!')
        return
    
    analyzer = ComprehensivePatentAnalyzer()
    patent_doc = analyzer.load_patent_document(file_path)
    
    if patent_doc:
        logger.info(f"\n✅ 文件加载成功")
        
        # 执行各项分析
        logger.info("\n🔍 开始分析专利文件...")
        
        logger.info("\n[1/6] 分析说明书摘要...")
        analyzer.analyze_abstract(patent_doc)
        
        logger.info('[2/6] 分析权利要求书...')
        analyzer.analyze_claims(patent_doc)
        
        logger.info('[3/6] 分析说明书...')
        analyzer.analyze_description(patent_doc)
        
        logger.info('[4/6] 分析说明书附图...')
        analyzer.analyze_drawings_description(patent_doc)
        
        logger.info('[5/6] 进行创造性分析（含专利检索）...')
        analyzer.analyze_creativity_with_search(patent_doc)
        
        logger.info('[6/6] 分析专利法第26条符合性...')
        analyzer.analyze_article_26_compliance(patent_doc)
        
        # 生成报告
        report = analyzer.generate_comprehensive_report(patent_doc)
        
        # 保存报告
        report_path = Path(file_path).with_suffix('_comprehensive_analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n✅ 分析完成! 报告已保存至: {report_path}")
        
        # 显示简要结果
        abs_score = analyzer.analysis_results['abstract'].get('score', 0)
        claims_score = analyzer.analysis_results['claims'].get('score', 0)
        desc_score = analyzer.analysis_results['description'].get('score', 0)
        draw_score = analyzer.analysis_results['drawings'].get('score', 0)
        creat_score = analyzer.analysis_results['creativity'].get('score', 0)
        art26_score = analyzer.analysis_results['article_26'].get('overall_score', 0)
        
        logger.info("\n📊 分析结果摘要:")
        logger.info(f"  说明书摘要:     {abs_score:>3}/100")
        logger.info(f"  权利要求书:     {claims_score:>3}/100")
        logger.info(f"  说明书:         {desc_score:>3}/100")
        logger.info(f"  说明书附图:     {draw_score:>3}/100")
        logger.info(f"  创造性分析:     {creat_score:>3}/100")
        logger.info(f"  专利法第26条:   {art26_score:>3}/100")
        
        # 询问是否显示完整报告
        show_full = input("\n是否显示完整报告? (y/n): ").strip().lower()
        if show_full == 'y':
            logger.info(str("\n" + '='*70))
            logger.info(str(report[:2000] + "\n...(完整报告请查看保存的文件))")

if __name__ == '__main__':
    main()
