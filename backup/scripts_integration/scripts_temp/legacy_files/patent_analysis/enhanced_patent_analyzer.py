#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版专利申请文件分析器
Enhanced Patent Application Analyzer

支持Word文档（.doc/.docx）和机械结构图分析
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 尝试导入所需的库
try:
    import pytesseract
    from docx import Document
    from PIL import Image
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

class EnhancedPatentAnalyzer:
    """增强版专利申请文件分析器"""
    
    def __init__(self):
        self.analysis_results = {
            'formalities': {},
            'creativity': {},
            'article_26': {},
            'drawings': {},
            'overall': {}
        }
        
    def check_dependencies(self):
        """检查依赖库"""
        if not DOCX_SUPPORT:
            logger.info('⚠️  警告: 未安装必要的依赖库，无法处理Word文档')
            logger.info('请运行: pip install python-docx pillow pytesseract')
            return False
        return True
    
    def load_patent_document(self, file_path: str) -> Dict | None:
        """加载专利文档（支持Word格式）"""
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
        if not self.check_dependencies():
            return None
            
        doc = Document(file_path)
        
        # 提取文本内容
        content = []
        sections = {}
        
        # 解析段落
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text.strip())
        
        full_text = '\n'.join(content)
        sections = self._parse_sections(full_text)
        
        # 提取图片
        drawings = self._extract_drawings_from_doc(doc, file_path)
        
        return {
            'content': full_text,
            'sections': sections,
            'drawings': drawings,
            'file_path': str(file_path),
            'file_type': 'word'
        }
    
    def _load_text_document(self, file_path: Path) -> Dict:
        """加载文本文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = self._parse_sections(content)
        
        return {
            'content': content,
            'sections': sections,
            'drawings': [],
            'file_path': str(file_path),
            'file_type': 'text'
        }
    
    def _extract_drawings_from_doc(self, doc, file_path: Path) -> List[Dict]:
        """从Word文档中提取图片"""
        drawings = []
        
        # 创建临时目录保存图片
        temp_dir = file_path.parent / f"{file_path.stem}_images"
        temp_dir.mkdir(exist_ok=True)
        
        # 提取内联图片
        for rel in doc.part.rels.values():
            if 'image' in rel.target_ref:
                try:
                    image_data = rel.target_part.blob
                    image_name = f"image_{len(drawings)+1}.png"
                    image_path = temp_dir / image_name
                    
                    # 保存图片
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    # 分析图片
                    drawing_info = {
                        'name': image_name,
                        'path': str(image_path),
                        'description': self._analyze_image(image_path),
                        'type': 'mechanical_drawing' if self._is_mechanical_drawing(image_path) else 'other'
                    }
                    drawings.append(drawing_info)
                    
                except Exception as e:
                    logger.info(f"提取图片失败: {e}")
        
        return drawings
    
    def _analyze_image(self, image_path: Path) -> str:
        """分析图片内容"""
        try:
            if not DOCX_SUPPORT:
                return '图片分析功能不可用（需要安装pytesseract）'
                
            # 使用OCR识别图片中的文字
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='chi_sim')
            
            # 简单分析
            if text:
                description = f"图片包含文字: {text[:100]}..."
            else:
                description = '机械结构图，未识别到文字'
            
            return description
            
        except Exception as e:
            return f"图片分析失败: {e}"
    
    def _is_mechanical_drawing(self, image_path: Path) -> bool:
        """判断是否为机械图纸"""
        # 简单判断逻辑
        keywords = ['图', 'Fig', '零件', '装配', '尺寸', 'mm']
        try:
            if DOCX_SUPPORT:
                image = Image.open(image_path)
                # 这里可以添加更复杂的图像识别逻辑
                # 例如使用深度学习模型识别图纸类型
            return True  # 暂时假设都是机械图纸
        except:
            return False
    
    def _parse_sections(self, content: str) -> Dict:
        """解析文档各部分"""
        sections = {}
        
        # 识别各部分的标题
        patterns = {
            'title': r'(?:发明名称|专利名称)[：:]\s*(.+?)(?=\n|$)',
            'abstract': r'摘要[：:]?\s*(.+?)(?=权利要求书|说明书|\n\n|$)',
            'claims': r'权利要求书[：:]?\s*(.+?)(?=说明书|附图说明|说明书摘要|$)',
            'description': r'说明书[：:]?\s*(.+?)(?=权利要求书|附图说明|说明书摘要|$)',
            'drawings_description': r'说明书附图[：:]?\s*(.+?)(?=说明书摘要|摘要附图|$)',
            'abstract_drawings': r'摘要附图[：:]?\s*(.+?)$'
        }
        
        for section, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(1).strip()
        
        return sections
    
    def analyze_formalities(self, patent_doc: Dict) -> Dict:
        """形式审查分析（增强版）"""
        sections = patent_doc.get('sections', {})
        issues = []
        score = 100
        
        # 检查必要部分
        required_sections = ['title', 'claims', 'description']
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
            elif claim_count > 20:
                issues.append(f"权利要求项数过多({claim_count}项，建议独立权利要求1-2项，从属权利合理)")
                score -= 10
            
            # 检查引用关系
            if re.search(r'如权利要求\d+', claims):
                issues.append('权利要求书中使用了不规范引用（说明书不可引用权利要求）')
                score -= 10
        
        # 检查说明书
        if 'description' in sections:
            desc = sections['description']
            
            # 必要部分
            required_parts = ['技术领域', '背景技术', '发明内容', '具体实施方式']
            for part in required_parts:
                if part not in desc:
                    issues.append(f"说明书缺少{part}部分")
                    score -= 10
            
            # 检查是否包含技术问题
            if not re.search(r'技术问题|技术难题|缺陷', desc):
                issues.append('说明书未明确要解决的技术问题')
                score -= 5
            
            # 检查是否包含技术方案
            if not re.search(r'技术方案|解决方案', desc):
                issues.append('说明书缺少明确的技术方案描述')
                score -= 5
        
        # 检查附图
        drawings = patent_doc.get('drawings', [])
        if not drawings and 'drawings_description' not in sections:
            if '机械' in patent_doc.get('content', ''):
                issues.append('机械发明建议包含结构图')
                score -= 5
        
        self.analysis_results['formalities'] = {
            'score': max(0, score),
            'issues': issues,
            'total_sections': len(sections),
            'missing_sections': [s for s in required_sections if s not in sections],
            'has_drawings': len(drawings) > 0
        }
        
        return self.analysis_results['formalities']
    
    def analyze_drawings(self, patent_doc: Dict) -> Dict:
        """分析图纸"""
        drawings = patent_doc.get('drawings', [])
        
        analysis = {
            'total_drawings': len(drawings),
            'mechanical_drawings': 0,
            'description_quality': 'good',
            'issues': []
        }
        
        for drawing in drawings:
            if drawing.get('type') == 'mechanical_drawing':
                analysis['mechanical_drawings'] += 1
            
            # 检查图纸说明
            if drawing.get('description') == '机械结构图，未识别到文字':
                analysis['description_quality'] = 'poor'
                analysis['issues'].append(f"{drawing['name']}缺少必要的文字说明")
        
        # 建议
        if analysis['total_drawings'] == 0:
            analysis['issues'].append('建议补充结构图以更好地说明发明')
        
        self.analysis_results['drawings'] = analysis
        return analysis
    
    def analyze_creativity(self, patent_doc: Dict) -> Dict:
        """创造性分析（增强版）"""
        sections = patent_doc.get('sections', {})
        analysis = {
            'score': 0,
            'technical_field': '',
            'problem_solved': '',
            'technical_features': [],
            'advantages': [],
            'novelty_points': [],
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
            problem_patterns = [
                r'要解决的技术问题[：:]?\s*(.+?)(?=\n\n|技术方案|$)',
                r'技术问题[：:]?\s*(.+?)(?=\n\n|技术方案|$)',
                r'缺陷[：:]?\s*(.+?)(?=\n\n|技术方案|$)'
            ]
            for pattern in problem_patterns:
                match = re.search(pattern, desc, re.DOTALL)
                if match:
                    analysis['problem_solved'] = match.group(1).strip()
                    break
        
        # 提取技术特征（从权利要求1）
        if 'claims' in sections:
            claims = sections['claims']
            independent_claims = re.findall(r'^\s*1[\.、]\s*(.+?)(?=\n\s*2|\n\n|$)', claims, re.DOTALL)
            if independent_claims:
                # 分解技术特征
                claim_text = independent_claims[0]
                features = re.split(r'[，；;和及与]', claim_text)
                analysis['technical_features'] = [
                    f.strip() 
                    for f in features 
                    if f.strip() and len(f.strip()) > 2
                ]
        
        # 提取有益效果和创新点
        if 'description' in sections:
            desc = sections['description']
            
            # 有益效果
            effects = re.findall(r'(?:有益效果|技术效果|优点|优势)[：:]?\s*([^。\n]+)', desc)
            analysis['advantages'] = [e.strip() for e in effects if e.strip()]
            
            # 创新点
            innovations = re.findall(r'(?:创新点|新颖性|独特之处)[：:]?\s*([^。\n]+)', desc)
            analysis['novelty_points'] = [i.strip() for i in innovations if i.strip()]
        
        # 评估创造性（更细致的评分）
        creativity_score = 30  # 基础分
        
        # 技术特征数量和复杂性
        feature_count = len(analysis['technical_features'])
        if feature_count >= 5:
            creativity_score += 15
        elif feature_count >= 3:
            creativity_score += 10
        
        # 解决了技术难题
        difficulty_keywords = ['长期存在', '一直未能解决', '技术瓶颈', '行业难题']
        for keyword in difficulty_keywords:
            if keyword in analysis['problem_solved']:
                creativity_score += 20
                break
        
        # 有益效果的质量
        strong_effect_keywords = ['显著提高', '大幅改善', '根本解决', '突破性']
        for effect in analysis['advantages']:
            for keyword in strong_effect_keywords:
                if keyword in effect:
                    creativity_score += 15
                    break
        
        # 技术方案的组合创新
        if '组合' in sections.get('claims', '') or '集成' in sections.get('claims', ''):
            creativity_score += 10
        
        # 克服了技术偏见
        if '偏见' in sections.get('description', ''):
            creativity_score += 10
        
        analysis['score'] = min(100, creativity_score)
        
        # 生成详细的评估意见
        if analysis['score'] >= 85:
            analysis['assessment'] = '具有突出的实质性特点和显著的进步，具备高度创造性'
        elif analysis['score'] >= 70:
            analysis['assessment'] = '具有实质性特点和进步，具备创造性'
        elif analysis['score'] >= 55:
            analysis['assessment'] = '具有一定创造性，建议补充技术效果的实验数据'
        else:
            analysis['assessment'] = '创造性不足，需要重新审视技术方案的创新点'
        
        self.analysis_results['creativity'] = analysis
        return analysis
    
    def analyze_article_26(self, patent_doc: Dict) -> Dict:
        """专利法第26条符合性分析（增强版）"""
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
            if len(desc) < 1000:
                analysis['section_3']['issues'].append('说明书过于简短，描述不够清楚')
                clarity_score -= 30
            
            # 检查技术方案描述
            if not re.search(r'技术方案|具体方案', desc):
                analysis['section_3']['issues'].append('缺少明确的技术方案描述')
                clarity_score -= 20
            
            # 检查技术问题
            if not re.search(r'技术问题|要解决', desc):
                analysis['section_3']['issues'].append('未明确要解决的技术问题')
                clarity_score -= 20
            
            analysis['section_3']['clarity'] = max(0, clarity_score)
            
            # 完整性
            completeness_score = 100
            required_parts = ['技术领域', '背景技术', '发明内容', '具体实施方式']
            missing_parts = []
            for part in required_parts:
                if part not in desc:
                    missing_parts.append(part)
                    completeness_score -= 25
            
            if missing_parts:
                analysis['section_3']['issues'].append(f"缺少必要部分: {', '.join(missing_parts)}")
            
            analysis['section_3']['completeness'] = max(0, completeness_score)
            
            # 能够实现
            enablement_score = 100
            if not re.search(r'实施例|具体实施方式', desc):
                analysis['section_3']['issues'].append('缺少具体实施方式，可能无法实现')
                enablement_score -= 40
            
            if not re.search(r'技术效果|有益效果', desc):
                analysis['section_3']['issues'].append('缺少技术效果说明，无法确认能够实现')
                enablement_score -= 30
            
            # 对于机械发明，检查是否有结构说明
            if '机械' in desc and not re.search(r'结构|构造|部件', desc):
                analysis['section_3']['issues'].append('机械发明缺少结构说明')
                enablement_score -= 20
            
            analysis['section_3']['enablement'] = max(0, enablement_score)
        
        # 分析第26条第4款（权利要求书以说明书为依据）
        if 'claims' in sections and 'description' in sections:
            claims = sections['claims']
            desc = sections['description']
            
            # 支持度 - 更精确的检查
            support_score = 100
            # 提取权利要求中的技术术语
            claim_terms = set(re.findall(r'[\u4e00-\u9fa5]{2,}', claims))
            # 提取说明书中的技术术语
            desc_terms = set(re.findall(r'[\u4e00-\u9fa5]{2,}', desc))
            
            # 检查权利要求是否超出说明书的范围
            unsupported_terms = claim_terms - desc_terms
            if unsupported_terms and len(unsupported_terms) > 5:
                analysis['section_4']['issues'].append('权利要求中的技术特征未在说明书中充分描述')
                support_score -= 30
            
            # 清楚性
            clarity_score = 100
            unclear_terms = ['优选', '例如', '最好是', '大约', '左右', '约', '等']
            for term in unclear_terms:
                if term in claims:
                    analysis['section_4']['issues'].append(f"权利要求中使用了不确定词语'{term}'")
                    clarity_score -= 10
            
            # 检查功能限定
            if re.search(r'能够.{1,20}的(装置|设备|机构)', claims):
                analysis['section_4']['issues'].append('权利要求中使用了功能限定，需要结构特征支持')
                clarity_score -= 15
            
            analysis['section_4']['clarity'] = max(0, clarity_score)
            
            # 简要性
            claim_count = len(re.findall(r'^\s*\d+\.', claims, re.MULTILINE))
            brevity_score = 100
            
            # 独立权利要求数量
            independent_count = len(re.findall(r'^\s*1[\.、]', claims, re.MULTILINE))
            if independent_count > 2:
                analysis['section_4']['issues'].append(f"独立权利要求过多({independent_count}项)")
                brevity_score -= 20
            
            # 权利要求总数
            if claim_count > 30:
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
    
    def generate_report(self, patent_doc: Dict) -> str:
        """生成详细的分析报告"""
        report = []
        report.append('# 专利申请文件分析报告')
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"文件路径: {patent_doc.get('file_path', 'N/A')}")
        report.append(f"文件类型: {patent_doc.get('file_type', 'N/A')}")
        
        # 形式审查结果
        form = self.analysis_results.get('formalities', {})
        report.append("\n## 一、形式审查结果")
        report.append(f"得分: {form.get('score', 0)}/100")
        report.append(f"包含部分: {form.get('total_sections', 0)}个")
        report.append(f"包含图纸: {'是' if form.get('has_drawings') else '否'}")
        
        if form.get('issues'):
            report.append("\n### ⚠️ 发现的问题:")
            for issue in form['issues']:
                report.append(f"- {issue}")
        
        # 图纸分析结果
        if patent_doc.get('drawings'):
            drawings = self.analysis_results.get('drawings', {})
            report.append("\n## 二、图纸分析结果")
            report.append(f"图纸总数: {drawings.get('total_drawings', 0)}")
            report.append(f"机械图纸: {drawings.get('mechanical_drawings', 0)}")
            report.append(f"说明质量: {drawings.get('description_quality', 'N/A')}")
            
            if drawings.get('issues'):
                report.append("\n### ⚠️ 图纸问题:")
                for issue in drawings['issues']:
                    report.append(f"- {issue}")
        
        # 创造性分析结果
        creat = self.analysis_results.get('creativity', {})
        report.append("\n## 三、创造性分析结果")
        report.append(f"得分: {creat.get('score', 0)}/100")
        report.append(f"评估意见: {creat.get('assessment', '')}")
        
        if creat.get('technical_field'):
            report.append(f"\n**技术领域**: {creat['technical_field']}")
        if creat.get('problem_solved'):
            report.append(f"\n**解决的技术问题**: {creat['problem_solved']}")
        
        if creat.get('technical_features'):
            report.append("\n**技术特征（独立权利要求）**:")
            for i, feature in enumerate(creat['technical_features'], 1):
                report.append(f"  {i}. {feature}")
        
        if creat.get('novelty_points'):
            report.append("\n**创新点**:")
            for point in creat['novelty_points']:
                report.append(f"- {point}")
        
        if creat.get('advantages'):
            report.append("\n**有益效果**:")
            for advantage in creat['advantages']:
                report.append(f"- {advantage}")
        
        # 专利法第26条符合性分析
        art26 = self.analysis_results.get('article_26', {})
        report.append("\n## 四、专利法第26条符合性分析")
        report.append(f"总体得分: {art26.get('overall_score', 0):.1f}/100")
        
        # 第26条第3款
        s3 = art26.get('section_3', {})
        report.append("\n### 第26条第3款（充分公开）")
        report.append(f"- 清楚性: {s3.get('clarity', 0)}/100")
        report.append(f"- 完整性: {s3.get('completeness', 0)}/100")
        report.append(f"- 能够实现: {s3.get('enablement', 0)}/100")
        if s3.get('issues'):
            report.append("\n⚠️ **问题**:")
            for issue in s3['issues']:
                report.append(f"- {issue}")
        
        # 第26条第4款
        s4 = art26.get('section_4', {})
        report.append("\n### 第26条第4款（权利要求书以说明书为依据）")
        report.append(f"- 支持度: {s4.get('support', 0)}/100")
        report.append(f"- 清楚性: {s4.get('clarity', 0)}/100")
        report.append(f"- 简要性: {s4.get('brevity', 0)}/100")
        if s4.get('issues'):
            report.append("\n⚠️ **问题**:")
            for issue in s4['issues']:
                report.append(f"- {issue}")
        
        # 总体评价和改进建议
        report.append("\n## 五、总体评价和改进建议")
        
        # 计算总分
        total_score = (
            form.get('score', 0) * 0.3 + 
            creat.get('score', 0) * 0.4 + 
            art26.get('overall_score', 0) * 0.3
        )
        
        report.append(f"\n**综合得分**: {total_score:.1f}/100")
        
        # 根据得分给出总体评价
        if total_score >= 85:
            report.append("\n✅ **总体评价**: 专利申请文件质量优秀，具有较好的授权前景")
        elif total_score >= 70:
            report.append("\n⚠️ **总体评价**: 专利申请文件基本合格，建议完善后提交")
        else:
            report.append("\n❌ **总体评价**: 专利申请文件存在较多问题，需要重点修改")
        
        # 具体改进建议
        report.append("\n### 📝 具体改进建议:")
        
        if form.get('score', 0) < 80:
            report.append("\n**形式方面**:")
            report.append('- 补充缺失的必要部分')
            report.append('- 检查并规范权利要求书格式')
            report.append('- 确保发明名称符合要求')
        
        if creat.get('score', 0) < 70:
            report.append("\n**创造性方面**:")
            report.append('- 详细描述技术方案的创新点')
            report.append('- 提供对比现有技术的优势说明')
            report.append('- 补充技术效果的实验数据或理论分析')
        
        if art26.get('overall_score', 0) < 80:
            report.append("\n**专利法第26条方面**:")
            report.append('- 确保说明书清楚完整')
            report.append('- 补充具体实施方式，使本领域技术人员能够实现')
            report.append('- 确保权利要求得到说明书充分支持')
            report.append('- 避免使用模糊不清的术语')
        
        # 特别针对机械发明的建议
        if patent_doc.get('drawings'):
            report.append("\n**机械发明特别建议**:")
            report.append('- 确保图纸包含必要的尺寸标注')
            report.append('- 在说明书中详细描述各部件的连接关系')
            report.append('- 提供装配图和关键部件的放大图')
        
        return '\n'.join(report)

def main():
    """主函数"""
    logger.info('增强版专利申请文件分析器')
    logger.info(str('=' * 60))
    logger.info('支持格式: .doc, .docx, .txt, .md')
    logger.info('功能: 形式审查、创造性分析、专利法第26条符合性分析、图纸分析')
    
    file_path = input("\n请输入专利文件路径: ").strip().strip('"')
    if not Path(file_path).exists():
        logger.info('❌ 文件不存在!')
        return
    
    analyzer = EnhancedPatentAnalyzer()
    patent_doc = analyzer.load_patent_document(file_path)
    
    if patent_doc:
        logger.info(f"\n✅ 文件加载成功: {patent_doc['file_type']}")
        
        # 执行各项分析
        logger.info("\n🔍 开始分析...")
        analyzer.analyze_formalities(patent_doc)
        analyzer.analyze_drawings(patent_doc)
        analyzer.analyze_creativity(patent_doc)
        analyzer.analyze_article_26(patent_doc)
        
        # 生成并保存报告
        report = analyzer.generate_report(patent_doc)
        
        # 保存报告
        report_path = Path(file_path).with_suffix('_analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n✅ 分析完成! 报告已保存至: {report_path}")
        logger.info(str("\n" + '='*60))
        
        # 显示简要结果
        form_score = analyzer.analysis_results['formalities'].get('score', 0)
        creat_score = analyzer.analysis_results['creativity'].get('score', 0)
        art26_score = analyzer.analysis_results['article_26'].get('overall_score', 0)
        
        logger.info(f"\n📊 简要结果:")
        logger.info(f"  - 形式审查: {form_score}/100")
        logger.info(f"  - 创造性分析: {creat_score}/100")
        logger.info(f"  - 专利法第26条: {art26_score}/100")
        
        # 显示详细报告的开头部分
        logger.info("\n📄 详细分析报告:")
        logger.info(str(report[:1000] + "\n...(完整报告请查看保存的文件))")

if __name__ == '__main__':
    main()
