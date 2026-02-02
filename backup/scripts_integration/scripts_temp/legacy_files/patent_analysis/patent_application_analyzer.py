#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利申请文件分析器
Patent Application Analyzer

用于分析专利申请文件的形式、创造性和专利法第26条符合性
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PatentApplicationAnalyzer:
    """专利申请文件分析器"""
    
    def __init__(self):
        self.analysis_results = {
            'formalities': {},
            'creativity': {},
            'article_26': {},
            'overall': {}
        }
        
    def load_patent_document(self, file_path: str) -> Dict:
        """加载专利文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析文档结构
            sections = self._parse_sections(content)
            
            return {
                'content': content,
                'sections': sections,
                'file_path': file_path
            }
        except Exception as e:
            logger.info(f"加载文件失败: {e}")
            return None
    
    def _parse_sections(self, content: str) -> Dict:
        """解析文档各部分"""
        sections = {}
        
        # 识别各部分的标题
        patterns = {
            'title': r'(?:发明名称|专利名称)[：:]\s*(.+)',
            'abstract': r'(?:摘要|技术摘要)[：:]?\s*(.+?)(?=\n|\n\n)',
            'claims': r'权利要求书[：:]?\s*(.+?)(?=说明书|附图说明|$)',
            'description': r'说明书[：:]?\s*(.+?)(?=权利要求书|附图说明|$)',
            'drawings': r'说明书附图[：:]?\s*(.+?)(?=说明书摘要|摘要附图|$)',
            'abstract_drawings': r'摘要附图[：:]?\s*(.+?)$'
        }
        
        for section, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(1).strip()
        
        return sections
    
    def analyze_formalities(self, patent_doc: Dict) -> Dict:
        """形式审查分析"""
        sections = patent_doc.get('sections', {})
        issues = []
        score = 100
        
        # 检查必要部分
        required_sections = ['title', 'claims', 'description', 'abstract']
        for section in required_sections:
            if section not in sections:
                issues.append(f"缺少必要部分: {section}")
                score -= 20
        
        # 检查发明名称
        if 'title' in sections:
            title = sections['title']
            if len(title) > 25:
                issues.append('发明名称过长（应不超过25字）')
                score -= 5
            if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s\-\(\)]+$', title):
                issues.append('发明名称包含不规范字符')
                score -= 5
        
        # 检查权利要求书
        if 'claims' in sections:
            claims = sections['claims']
            claim_count = len(re.findall(r'^\s*\d+\.', claims, re.MULTILINE))
            if claim_count == 0:
                issues.append('权利要求书格式不正确')
                score -= 15
            elif claim_count > 10:
                issues.append(f"权利要求项数过多({claim_count}项，建议不超过10项)")
                score -= 5
            
            # 检查引用关系
            if re.search(r'如权利要求\d+', claims):
                issues.append('权利要求书中使用了不规范引用')
                score -= 10
        
        # 检查说明书
        if 'description' in sections:
            desc = sections['description']
            
            # 技术领域
            if not re.search(r'技术领域', desc):
                issues.append('说明书缺少技术领域部分')
                score -= 10
            
            # 背景技术
            if not re.search(r'背景技术', desc):
                issues.append('说明书缺少背景技术部分')
                score -= 10
            
            # 发明内容
            if not re.search(r'发明内容', desc):
                issues.append('说明书缺少发明内容部分')
                score -= 10
            
            # 具体实施方式
            if not re.search(r'具体实施方式', desc):
                issues.append('说明书缺少具体实施方式部分')
                score -= 10
        
        self.analysis_results['formalities'] = {
            'score': max(0, score),
            'issues': issues,
            'total_sections': len(sections),
            'missing_sections': [s for s in required_sections if s not in sections]
        }
        
        return self.analysis_results['formalities']
    
    def analyze_creativity(self, patent_doc: Dict) -> Dict:
        """创造性分析"""
        sections = patent_doc.get('sections', {})
        analysis = {
            'score': 0,
            'technical_field': '',
            'problem_solved': '',
            'technical_features': [],
            'advantages': [],
            'assessment': ''
        }
        
        # 提取技术领域
        if 'description' in sections:
            desc = sections['description']
            field_match = re.search(r'技术领域[：:]?\s*(.+?)(?=\n\n|背景技术|$)', desc, re.DOTALL)
            if field_match:
                analysis['technical_field'] = field_match.group(1).strip()
        
        # 提取技术问题
        if 'description' in sections:
            desc = sections['description']
            problem_match = re.search(r'要解决的技术问题[：:]?\s*(.+?)(?=\n\n|技术方案|$)', desc, re.DOTALL)
            if problem_match:
                analysis['problem_solved'] = problem_match.group(1).strip()
        
        # 提取技术特征
        if 'claims' in sections:
            claims = sections['claims']
            # 提取独立权利要求的技术特征
            independent_claims = re.findall(r'^\s*1[\.、]\s*(.+?)(?=\n\s*2|\n\n|$)', claims, re.DOTALL)
            if independent_claims:
                analysis['technical_features'] = [
                    feature.strip() 
                    for feature in re.split(r'[，；;]', independent_claims[0])
                    if feature.strip()
                ]
        
        # 提取有益效果
        if 'description' in sections:
            desc = sections['description']
            effects = re.findall(r'(?:有益效果|优点|优势)[：:]?\s*([^。\n]+)', desc)
            analysis['advantages'] = [e.strip() for e in effects if e.strip()]
        
        # 评估创造性
        creativity_score = 50  # 基础分
        
        # 技术特征数量
        if len(analysis['technical_features']) > 3:
            creativity_score += 10
        
        # 有益效果
        if len(analysis['advantages']) > 2:
            creativity_score += 10
        
        # 技术问题的创新性（简单判断）
        problem_keywords = ['首次提出', '创新性', '突破性', '解决了长期存在']
        for keyword in problem_keywords:
            if keyword in analysis['problem_solved']:
                creativity_score += 15
                break
        
        # 技术效果的显著性
        effect_keywords = ['显著提高', '大幅降低', '意想不到', '突破性']
        for effect in analysis['advantages']:
            for keyword in effect_keywords:
                if keyword in effect:
                    creativity_score += 15
                    break
        
        analysis['score'] = min(100, creativity_score)
        
        # 生成评估意见
        if analysis['score'] >= 80:
            analysis['assessment'] = '具有突出的实质性特点和显著的进步，具备创造性'
        elif analysis['score'] >= 60:
            analysis['assessment'] = '具有一定创造性，但可能需要进一步论证'
        else:
            analysis['assessment'] = '创造性不足，建议补充技术效果和进步性说明'
        
        self.analysis_results['creativity'] = analysis
        return analysis
    
    def analyze_article_26(self, patent_doc: Dict) -> Dict:
        """专利法第26条符合性分析"""
        sections = patent_doc.get('sections', {})
        analysis = {
            'section_3': {  # 第26条第3款：充分公开
                'clarity': 0,
                'completeness': 0,
                'enablement': 0,
                'issues': []
            },
            'section_4': {  # 第26条第4款：权利要求书以说明书为依据
                'support': 0,
                'clarity': 0,
                'brevity': 0,
                'issues': []
            },
            'overall_score': 0
        }
        
        # 分析第26条第3款（充分公开）
        if 'description' in sections:
            desc = sections['description']
            
            # 清楚性
            clarity_score = 100
            if len(desc) < 500:
                analysis['section_3']['issues'].append('说明书过于简短，可能不够清楚')
                clarity_score -= 30
            
            if not re.search(r'技术方案', desc):
                analysis['section_3']['issues'].append('缺少明确的技术方案描述')
                clarity_score -= 20
            
            analysis['section_3']['clarity'] = max(0, clarity_score)
            
            # 完整性
            completeness_score = 100
            required_parts = ['技术领域', '背景技术', '发明内容', '具体实施方式']
            for part in required_parts:
                if part not in desc:
                    analysis['section_3']['issues'].append(f"缺少{part}部分")
                    completeness_score -= 25
            
            analysis['section_3']['completeness'] = max(0, completeness_score)
            
            # 能够实现
            enablement_score = 100
            if not re.search(r'实施例', desc):
                analysis['section_3']['issues'].append('缺少实施例，可能无法实现')
                enablement_score -= 40
            
            if not re.search(r'技术效果', desc):
                analysis['section_3']['issues'].append('缺少技术效果说明')
                enablement_score -= 20
            
            analysis['section_3']['enablement'] = max(0, enablement_score)
        
        # 分析第26条第4款（权利要求书以说明书为依据）
        if 'claims' in sections and 'description' in sections:
            claims = sections['claims']
            desc = sections['description']
            
            # 支持度
            support_score = 100
            claim_terms = set(re.findall(r'[\u4e00-\u9fa5]+', claims))
            desc_terms = set(re.findall(r'[\u4e00-\u9fa5]+', desc))
            
            # 检查权利要求中的技术特征是否在说明书中记载
            missing_features = claim_terms - desc_terms
            if missing_features:
                analysis['section_4']['issues'].append(f"权利要求中的部分特征未在说明书中记载")
                support_score -= 30
            
            analysis['section_4']['support'] = max(0, support_score)
            
            # 清楚性
            clarity_score = 100
            if '优选' in claims:
                analysis['section_4']['issues'].append("权利要求中使用了'优选'等不确定词语")
                clarity_score -= 20
            
            if re.search(r'大约|左右|约', claims):
                analysis['section_4']['issues'].append('权利要求中使用了模糊的数量词')
                clarity_score -= 20
            
            analysis['section_4']['clarity'] = max(0, clarity_score)
            
            # 简要性
            claim_count = len(re.findall(r'^\s*\d+\.', claims, re.MULTILINE))
            brevity_score = 100
            if claim_count > 20:
                analysis['section_4']['issues'].append('权利要求项数过多，不够简要')
                brevity_score -= 20
            
            analysis['section_4']['brevity'] = max(0, brevity_score)
        
        # 计算总分
        section_3_avg = sum(analysis['section_3'].values()[:-1]) / 3  # 排除issues
        section_4_avg = sum(analysis['section_4'].values()[:-1]) / 3  # 排除issues
        analysis['overall_score'] = (section_3_avg + section_4_avg) / 2
        
        self.analysis_results['article_26'] = analysis
        return analysis
    
    def generate_report(self, patent_doc: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append('# 专利申请文件分析报告')
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"文件路径: {patent_doc.get('file_path', 'N/A')}")
        
        # 形式审查结果
        form = self.analysis_results.get('formalities', {})
        report.append("\n## 一、形式审查结果")
        report.append(f"得分: {form.get('score', 0)}/100")
        if form.get('issues'):
            report.append("\n### 发现的问题:")
            for issue in form['issues']:
                report.append(f"- {issue}")
        
        # 创造性分析结果
        creat = self.analysis_results.get('creativity', {})
        report.append("\n## 二、创造性分析结果")
        report.append(f"得分: {creat.get('score', 0)}/100")
        report.append(f"评估意见: {creat.get('assessment', '')}")
        report.append(f"\n技术领域: {creat.get('technical_field', '')}")
        report.append(f"解决的技术问题: {creat.get('problem_solved', '')}")
        if creat.get('technical_features'):
            report.append("\n技术特征:")
            for feature in creat['technical_features']:
                report.append(f"- {feature}")
        if creat.get('advantages'):
            report.append("\n有益效果:")
            for advantage in creat['advantages']:
                report.append(f"- {advantage}")
        
        # 专利法第26条符合性分析
        art26 = self.analysis_results.get('article_26', {})
        report.append("\n## 三、专利法第26条符合性分析")
        report.append(f"总体得分: {art26.get('overall_score', 0):.1f}/100")
        
        # 第26条第3款
        s3 = art26.get('section_3', {})
        report.append("\n### 第26条第3款（充分公开）")
        report.append(f"- 清楚性: {s3.get('clarity', 0)}/100")
        report.append(f"- 完整性: {s3.get('completeness', 0)}/100")
        report.append(f"- 能够实现: {s3.get('enablement', 0)}/100")
        if s3.get('issues'):
            report.append("\n问题:")
            for issue in s3['issues']:
                report.append(f"- {issue}")
        
        # 第26条第4款
        s4 = art26.get('section_4', {})
        report.append("\n### 第26条第4款（权利要求书以说明书为依据）")
        report.append(f"- 支持度: {s4.get('support', 0)}/100")
        report.append(f"- 清楚性: {s4.get('clarity', 0)}/100")
        report.append(f"- 简要性: {s4.get('brevity', 0)}/100")
        if s4.get('issues'):
            report.append("\n问题:")
            for issue in s4['issues']:
                report.append(f"- {issue}")
        
        # 总体建议
        report.append("\n## 四、改进建议")
        
        # 根据各项得分提供建议
        if form.get('score', 0) < 80:
            report.append("\n### 形式方面:")
            report.append('- 仔细检查文件格式是否符合规范')
            report.append('- 确保包含所有必要的部分')
            report.append('- 检查权利要求书格式是否正确')
        
        if creat.get('score', 0) < 70:
            report.append("\n### 创造性方面:")
            report.append('- 补充技术效果的实验数据')
            report.append('- 强调技术方案的创新点和突破')
            report.append('- 详细说明与现有技术的区别')
        
        if art26.get('overall_score', 0) < 80:
            report.append("\n### 专利法第26条方面:")
            report.append('- 确保说明书清楚完整地描述技术方案')
            report.append('- 补充实施例以支持技术效果')
            report.append('- 确保权利要求得到说明书支持')
        
        return '\n'.join(report)

def main():
    """主函数"""
    analyzer = PatentApplicationAnalyzer()
    
    logger.info('专利申请文件分析器')
    logger.info(str('=' * 50))
    logger.info('请选择分析方式:')
    logger.info('1. 分析单个文件')
    logger.info('2. 批量分析')
    
    choice = input("\n请输入选择 (1 或 2): ").strip()
    
    if choice == '1':
        file_path = input('请输入专利文件路径: ').strip()
        if not Path(file_path).exists():
            logger.info('文件不存在!')
            return
        
        patent_doc = analyzer.load_patent_document(file_path)
        if patent_doc:
            # 执行各项分析
            analyzer.analyze_formalities(patent_doc)
            analyzer.analyze_creativity(patent_doc)
            analyzer.analyze_article_26(patent_doc)
            
            # 生成并保存报告
            report = analyzer.generate_report(patent_doc)
            
            # 保存报告
            report_path = file_path.replace('.txt', '_analysis_report.md').replace('.docx', '_analysis_report.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"\n分析完成! 报告已保存至: {report_path}")
            logger.info(str("\n" + '='*50))
            logger.info(str(report))
    
    elif choice == '2':
        logger.info('批量分析功能待实现...')
    
    else:
        logger.info('无效选择!')

if __name__ == '__main__':
    main()
