#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持旧版.doc文件的专利分析器
Legacy Patent Document Analyzer

使用antiword提取.doc文件内容
"""

import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

# 导入专利检索集成模块
from patent_search_integration import PatentSearchIntegration


class LegacyPatentAnalyzer:
    """支持旧版Word文档的专利分析器"""
    
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
        
    def extract_text_from_doc(self, file_path: str) -> str | None:
        """使用antiword提取.doc文件文本"""
        try:
            # 使用antiword提取文本
            cmd = ['antiword', '-m', 'UTF-8', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.info(f"antiword执行失败: {result.stderr}")
                return None
        except Exception as e:
            logger.info(f"提取文本失败: {e}")
            return None
    
    def load_patent_document(self, file_path: str) -> Dict | None:
        """加载专利文档"""
        file_path = Path(file_path)
        
        # 提取文本
        text = self.extract_text_from_doc(str(file_path))
        if not text:
            return None
        
        # 解析各部分
        sections = self._parse_target_sections(text)
        
        return {
            'content': text,
            'sections': sections,
            'file_path': str(file_path),
            'file_type': 'doc_legacy'
        }
    
    def _parse_target_sections(self, content: str) -> Dict:
        """解析目标部分：摘要、权利要求书、说明书、说明书附图"""
        sections = {}
        
        # 清理内容
        content = re.sub(r'\x0c', '', content)  # 删除分页符
        
        # 摘要部分
        abstract_patterns = [
            r'摘要\s*[:：]?\s*(.+?)(?=权利要求书|说明书|说明书附图|$)',
            r'技术摘要\s*[:：]?\s*(.+?)(?=权利要求书|说明书|说明书附图|$)',
            r'发明内容\s*[:：]?\s*(.+?)(?=权利要求书|说明书|说明书附图|$)'
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                abstract_text = match.group(1).strip()
                # 清理空行
                abstract_text = re.sub(r'\n\s*\n', '\n', abstract_text)
                sections['abstract'] = abstract_text
                break
        
        # 权利要求书部分
        claims_match = re.search(r'权利要求书\s*[:：]?\s*(.+?)(?=说明书|说明书附图|说明书摘要|$)', 
                                content, re.DOTALL | re.IGNORECASE)
        if claims_match:
            claims_text = claims_match.group(1).strip()
            # 清理格式
            claims_text = re.sub(r'\n\s*\n', '\n', claims_text)
            sections['claims'] = claims_text
        
        # 说明书部分
        desc_match = re.search(r'说明书\s*[:：]?\s*(.+?)(?=说明书附图|说明书摘要|权利要求书|$)', 
                             content, re.DOTALL | re.IGNORECASE)
        if desc_match:
            desc_text = desc_match.group(1).strip()
            # 清理格式
            desc_text = re.sub(r'\n\s*\n', '\n', desc_text)
            sections['description'] = desc_text
        
        # 说明书附图部分
        drawings_match = re.search(r'说明书附图\s*[:：]?\s*(.+?)(?=说明书摘要|摘要附图|$)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if drawings_match:
            drawings_text = drawings_match.group(1).strip()
            # 清理格式
            drawings_text = re.sub(r'\n\s*\n', '\n', drawings_text)
            sections['drawings_description'] = drawings_text
        
        return sections
    
    def analyze_abstract(self, patent_doc: Dict) -> Dict:
        """分析说明书摘要"""
        sections = patent_doc.get('sections', {})
        abstract = sections.get('abstract', '')
        
        analysis = {
            'content': abstract[:500] + '...' if len(abstract) > 500 else abstract,
            'word_count': len(abstract),
            'has_technical_problem': '技术问题' in abstract or '问题' in abstract,
            'has_technical_solution': '技术方案' in abstract or '解决方案' in abstract,
            'has_beneficial_effect': '有益效果' in abstract or '效果' in abstract or '优点' in abstract,
            'issues': [],
            'score': 0
        }
        
        if not abstract:
            analysis['issues'].append('缺少说明书摘要')
            analysis['score'] = 0
            return analysis
        
        # 检查字数
        if analysis['word_count'] < 50:
            analysis['issues'].append('摘要过短（少于50字）')
        elif analysis['word_count'] > 300:
            analysis['issues'].append('摘要过长（超过300字）')
        
        # 计算得分
        score = 50
        if 50 <= analysis['word_count'] <= 300:
            score += 20
        if analysis['has_technical_problem']:
            score += 10
        if analysis['has_technical_solution']:
            score += 10
        if analysis['has_beneficial_effect']:
            score += 10
        
        analysis['score'] = min(100, score)
        
        return analysis
    
    def analyze_claims(self, patent_doc: Dict) -> Dict:
        """分析权利要求书"""
        sections = patent_doc.get('sections', {})
        claims = sections.get('claims', '')
        
        analysis = {
            'content': claims[:1000] + '...' if len(claims) > 1000 else claims,
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
        # 更宽松的匹配模式
        claim_pattern = r'([0-9一二三四五六七八九十]+)[\.\、．\s]\s*(.+?)(?=\n\s*[0-9一二三四五六七八九十]+[\.\、．\s]|\n\n|$)'
        claim_matches = re.findall(claim_pattern, claims, re.DOTALL)
        
        analysis['total_claims'] = len(claim_matches)
        
        # 转换数字
        def chinese_to_num(chinese):
            mapping = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
                      '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
            return mapping.get(chinese, chinese)
        
        # 分析权利要求层次
        for claim_num, claim_content in claim_matches:
            # 转换数字
            if isinstance(claim_num, str):
                try:
                    claim_num = int(claim_num)
                except:
                    claim_num = chinese_to_num(claim_num)
            
            claim_text = claim_content.strip()
            
            # 检查是否为从属权利要求
            dependent_match = re.search(r'根据权利要求([0-9一二三四五六七八九十]+)', claim_text)
            
            if dependent_match:
                analysis['dependent_claims'] += 1
                dep_on = dependent_match.group(1)
                try:
                    dependent_on = int(dep_on)
                except:
                    dependent_on = chinese_to_num(dep_on)
                
                analysis['claim_hierarchy'].append({
                    'number': claim_num,
                    'type': 'dependent',
                    'depends_on': dependent_on,
                    'content': claim_text[:100] + '...' if len(claim_text) > 100 else claim_text
                })
            else:
                if claim_num == 1 or (isinstance(claim_num, str) and claim_num in ['1', '一']):
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
        
        if analysis['total_claims'] > 20:
            analysis['issues'].append(f"权利要求总数过多({analysis['total_claims']}项)")
        
        # 计算得分
        score = 30
        if 1 <= analysis['independent_claims'] <= 2:
            score += 30
        if analysis['total_claims'] <= 10:
            score += 20
        if analysis['main_claim_features']:
            score += 20
        
        analysis['score'] = min(100, score)
        
        return analysis
    
    def analyze_description(self, patent_doc: Dict) -> Dict:
        """分析说明书"""
        sections = patent_doc.get('sections', {})
        description = sections.get('description', '')
        
        analysis = {
            'content_length': len(description),
            'has_technical_field': '技术领域' in description,
            'has_background_art': '背景技术' in description,
            'has_invention_content': '发明内容' in description or '技术方案' in description,
            'has_embodiments': '具体实施方式' in description or '实施例' in description,
            'has_beneficial_effects': '有益效果' in description or '技术效果' in description,
            'issues': [],
            'score': 0,
            'sections_found': []
        }
        
        if not description:
            analysis['issues'].append('缺少说明书')
            analysis['score'] = 0
            return analysis
        
        # 检查必要部分
        if analysis['has_technical_field']:
            analysis['sections_found'].append('技术领域')
        if analysis['has_background_art']:
            analysis['sections_found'].append('背景技术')
        if analysis['has_invention_content']:
            analysis['sections_found'].append('发明内容')
        if analysis['has_embodiments']:
            analysis['sections_found'].append('具体实施方式')
        
        # 检查问题
        if not analysis['has_technical_field']:
            analysis['issues'].append('未明确技术领域')
        if not analysis['has_background_art']:
            analysis['issues'].append('缺少背景技术描述')
        if not analysis['has_invention_content']:
            analysis['issues'].append('缺少发明内容或技术方案')
        if not analysis['has_embodiments']:
            analysis['issues'].append('缺少具体实施方式')
        if not analysis['has_beneficial_effects']:
            analysis['issues'].append('缺少有益效果说明')
        
        # 计算得分
        score = 20
        if analysis['content_length'] > 500:
            score += 20
        if len(analysis['sections_found']) >= 4:
            score += 40
        elif len(analysis['sections_found']) >= 3:
            score += 30
        elif len(analysis['sections_found']) >= 2:
            score += 20
        
        if not analysis['issues']:
            score += 20
        
        analysis['score'] = min(100, score)
        
        return analysis
    
    def analyze_drawings_description(self, patent_doc: Dict) -> Dict:
        """分析说明书附图"""
        sections = patent_doc.get('sections', {})
        drawings_desc = sections.get('drawings_description', '')
        
        analysis = {
            'content_length': len(drawings_desc),
            'has_figures': '图' in drawings_desc,
            'figure_count': len(re.findall(r'图\s*[0-9一二三四五六七八九十]+', drawings_desc)),
            'has_detailed_description': len(drawings_desc) > 100,
            'issues': [],
            'score': 0
        }
        
        if not drawings_desc:
            analysis['issues'].append('缺少说明书附图部分')
            analysis['score'] = 0
            return analysis
        
        # 计算得分
        score = 30
        if analysis['has_figures']:
            score += 30
        if analysis['figure_count'] > 0:
            score += 20
        if analysis['has_detailed_description']:
            score += 20
        
        analysis['score'] = min(100, score)
        
        return analysis
    
    def analyze_creativity_with_search(self, patent_doc: Dict) -> Dict:
        """结合专利检索进行创造性分析"""
        logger.info('   正在进行专利检索...')
        
        # 提取关键词
        claims_analysis = self.analysis_results.get('claims', {})
        features = claims_analysis.get('main_claim_features', [])
        
        # 从标题和内容中提取关键词
        content = patent_doc.get('content', '')
        title_match = re.search(r'发明名称\s*[:：]?\s*(.+)', content)
        title = title_match.group(1).strip() if title_match else ''
        
        # 生成关键词
        keywords = []
        
        # 从标题提取
        if title:
            title_words = [w for w in title.split() if len(w) > 1 and '的' not in w]
            keywords.extend(title_words[:3])
        
        # 从技术特征提取
        for feature in features[:3]:
            feature_words = [w for w in feature.split() if len(w) > 1 and w not in ['的', '用于', '设有', '包括', '其特征在于']]
            keywords.extend(feature_words[:2])
        
        # 执行检索
        local_results = self.patent_search.search_local_database(keywords[:5])
        external_results = self.patent_search.search_external_patents(keywords[:3])
        
        all_results = local_results + external_results
        
        # 进行对比分析
        comparison = self.patent_search.compare_with_prior_art(features, all_results)
        
        # 计算创造性得分
        novelty_score = comparison.get('novelty_analysis', {}).get('score', 0)
        
        creativity_score = 50
        creativity_score += novelty_score * 40
        
        # 基于文件内容调整
        if '酶解' in content or '反应器' in content or '水解' in content:
            creativity_score += 5  # 生物反应器相关
        
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
        
        return analysis
    
    def _generate_creativity_assessment(self, score: float, comparison: Dict) -> str:
        """生成创造性评估意见"""
        if score >= 85:
            return '具有突出的实质性特点和显著的进步，具备高度创造性'
        elif score >= 70:
            return '具有实质性特点和进步，具备创造性'
        elif score >= 55:
            return '具有一定创造性，建议补充技术效果数据'
        else:
            return '创造性不足，需要重新评估技术方案的创新点'
    
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
            if len(description) < 300:
                analysis['section_3']['issues'].append('说明书过于简短')
                clarity_score -= 30
            
            analysis['section_3']['clarity'] = max(0, clarity_score)
            
            # 完整性
            completeness_score = 100
            required_parts = ['技术领域', '背景技术', '发明内容', '具体实施方式']
            missing_count = 0
            for part in required_parts:
                if part not in description:
                    missing_count += 1
            
            if missing_count > 0:
                analysis['section_3']['issues'].append(f"缺少{missing_count}个必要部分")
                completeness_score -= missing_count * 25
            
            analysis['section_3']['completeness'] = max(0, completeness_score)
            
            # 能够实现
            enablement_score = 100
            if '实施例' not in description and '具体实施方式' not in description:
                analysis['section_3']['issues'].append('缺少具体实施方式')
                enablement_score -= 40
            
            if '有益效果' not in description:
                analysis['section_3']['issues'].append('缺少技术效果说明')
                enablement_score -= 20
            
            analysis['section_3']['enablement'] = max(0, enablement_score)
        
        # 第26条第4款：权利要求书以说明书为依据
        claims = sections.get('claims', '')
        if claims and description:
            # 支持度（简化检查）
            support_score = 100
            
            # 检查权利要求中的主要术语是否在说明书中出现
            claim_terms = set(re.findall(r'[\u4e00-\u9fa5]{3,}', claims))
            desc_terms = set(re.findall(r'[\u4e00-\u9fa5]{3,}', description))
            
            overlap = len(claim_terms & desc_terms) / len(claim_terms) if claim_terms else 0
            
            if overlap < 0.5:
                analysis['section_4']['issues'].append('权利要求可能未得到说明书充分支持')
                support_score -= 30
            
            analysis['section_4']['support'] = max(0, support_score)
            
            # 清楚性
            clarity_score = 100
            unclear_terms = ['优选', '大约', '左右']
            for term in unclear_terms:
                if term in claims:
                    analysis['section_4']['issues'].append(f"使用了不确定词语'{term}'")
                    clarity_score -= 10
            
            analysis['section_4']['clarity'] = max(0, clarity_score)
            
            # 简要性
            claim_count = len(re.findall(r'[0-9一二三四五六七八九十]+[\.\、．\s]', claims))
            brevity_score = 100
            
            if claim_count > 10:
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
        
        return analysis
    
    def generate_report(self, patent_doc: Dict, file_name: str) -> str:
        """生成分析报告"""
        report = []
        report.append(f"# {file_name} 专利申请文件分析报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 说明书摘要分析
        abstract = self.analysis_results.get('abstract', {})
        report.append("\n## 一、说明书摘要分析")
        report.append(f"得分: {abstract.get('score', 0)}/100")
        if abstract.get('content'):
            report.append(f"\n内容摘要:\n{abstract['content'][:300]}...")
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
        if claims.get('main_claim_features'):
            report.append(f"\n主要技术特征:")
            for i, feature in enumerate(claims['main_claim_features'][:5], 1):
                report.append(f"  {i}. {feature}")
        if claims.get('issues'):
            report.append("\n### ⚠️ 存在问题:")
            for issue in claims['issues']:
                report.append(f"- {issue}")
        
        # 3. 说明书分析
        description = self.analysis_results.get('description', {})
        report.append("\n## 三、说明书分析")
        report.append(f"得分: {description.get('score', 0)}/100")
        report.append(f"内容长度: {description.get('content_length', 0)}字符")
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
        
        if creativity.get('recommendations'):
            report.append(f"\n**改进建议**:")
            for rec in creativity['recommendations']:
                report.append(f"- {rec}")
        
        # 6. 专利法第26条符合性分析
        art26 = self.analysis_results.get('article_26', {})
        report.append("\n## 六、专利法第26条符合性分析")
        report.append(f"总体得分: {art26.get('overall_score', 0):.1f}/100")
        
        s3 = art26.get('section_3', {})
        report.append(f"\n### 第26条第3款（充分公开）")
        report.append(f"- 清楚性: {s3.get('clarity', 0)}/100")
        report.append(f"- 完整性: {s3.get('completeness', 0)}/100")
        report.append(f"- 能够实现: {s3.get('enablement', 0)}/100")
        if s3.get('issues'):
            report.append("\n**问题**:")
            for issue in s3['issues']:
                report.append(f"- {issue}")
        
        s4 = art26.get('section_4', {})
        report.append(f"\n### 第26条第4款（权利要求书以说明书为依据）")
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

def analyze_all_patents():
    """分析所有专利文件"""
    # 专利文件目录
    patent_dir = Path('/Users/xujian/Athena工作平台/工作/专利分析/2025.12.12三件')
    
    # 找出所有.doc文件
    patent_files = list(patent_dir.glob('*.doc'))
    
    logger.info(str('=' * 80))
    logger.info('专利申请文件分析报告')
    logger.info(str('=' * 80))
    
    # 创建分析器
    analyzer = LegacyPatentAnalyzer()
    
    # 分析每个文件
    all_reports = []
    
    for patent_file in patent_files:
        logger.info(f"\n正在分析: {patent_file.name}")
        logger.info(str('-' * 60))
        
        # 加载文档
        patent_doc = analyzer.load_patent_document(str(patent_file))
        
        if patent_doc:
            # 执行各项分析
            analyzer.analyze_abstract(patent_doc)
            analyzer.analyze_claims(patent_doc)
            analyzer.analyze_description(patent_doc)
            analyzer.analyze_drawings_description(patent_doc)
            analyzer.analyze_creativity_with_search(patent_doc)
            analyzer.analyze_article_26_compliance(patent_doc)
            
            # 生成报告
            report = analyzer.generate_report(patent_doc, patent_file.stem)
            all_reports.append(report)
            
            # 保存报告
            report_path = patent_file.parent / (patent_file.stem + '_分析报告.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"✅ 分析完成! 报告已保存至: {report_path}")
            
            # 显示简要结果
            abs_score = analyzer.analysis_results['abstract'].get('score', 0)
            claims_score = analyzer.analysis_results['claims'].get('score', 0)
            desc_score = analyzer.analysis_results['description'].get('score', 0)
            draw_score = analyzer.analysis_results['drawings'].get('score', 0)
            creat_score = analyzer.analysis_results['creativity'].get('score', 0)
            art26_score = analyzer.analysis_results['article_26'].get('overall_score', 0)
            
            # 计算综合得分
            total_score = (abs_score * 0.15 + claims_score * 0.30 + 
                          desc_score * 0.25 + draw_score * 0.10 + 
                          creat_score * 0.15 + art26_score * 0.05)
            
            logger.info(f"\n📊 分析结果摘要:")
            logger.info(f"  综合得分: {total_score:.1f}/100")
            
            # 显示关键问题
            issues = []
            if abs_score < 70: issues.append('摘要')
            if claims_score < 70: issues.append('权利要求书')
            if desc_score < 70: issues.append('说明书')
            if creat_score < 70: issues.append('创造性')
            if art26_score < 70: issues.append('专利法第26条')
            
            if issues:
                logger.info(f"⚠️  需要改进: {', '.join(issues)}")
            else:
                logger.info('✅ 各项指标均达到良好水平')
            
        else:
            logger.info(f"❌ 文件加载失败: {patent_file.name}")
    
    # 生成总报告
    if all_reports:
        logger.info(str("\n\n" + '=' * 80))
        logger.info('总报告')
        logger.info(str('=' * 80))
        for report in all_reports:
            logger.info(str(report))
            logger.info(str("\n" + '=' * 80 + "\n"))

if __name__ == '__main__':
    analyze_all_patents()
