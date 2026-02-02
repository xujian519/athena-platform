#!/usr/bin/env python3
"""
专利感知层框架
支持PDF专利文档解析、权利要求提取、技术特征识别
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF for PDF processing

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """文档类型枚举"""
    DISCLOSURE = 'disclosure'  # 技术交底书
    PATENT = 'patent'          # 专利文档
    PRIOR_ART = 'prior_art'    # 对比文件

class PatentSection(Enum):
    """专利章节枚举"""
    TITLE = 'title'                    # 标题
    ABSTRACT = 'abstract'              # 摘要
    CLAIMS = 'claims'                  # 权利要求
    DESCRIPTION = 'description'        # 说明书
    DRAWINGS = 'drawings'              # 附图说明
    DETAILED_DESCRIPTION = 'detailed'  # 具体实施方式

@dataclass
class PatentDocument:
    """专利文档数据结构"""
    doc_id: str
    doc_type: DocumentType
    file_path: str
    title: str
    abstract: str
    claims: Dict[int, str]  # 权利要求号 -> 权利要求内容
    description: str
    sections: Dict[PatentSection, str]
    metadata: Dict

@dataclass
class TechnicalFeature:
    """技术特征数据结构"""
    feature_id: str
    description: str
    category: str  # structural, functional, performance
    importance: float  # 0-1
    keywords: List[str]
    source_section: PatentSection  # 来源章节
    claim_reference: Optional[int]  # 引用的权利要求号
    confidence: float  # 提取置信度 0-1

@dataclass
class ClaimAnalysis:
    """权利要求分析结果"""
    claim_number: int
    claim_type: str  # independent, dependent
    preamble: str   # 前序部分
    body: str       # 主体部分
    technical_features: List[TechnicalFeature]
    limitations: List[str]  # 技术限定
    structural_elements: List[str]  # 结构要素
    functional_elements: List[str]  # 功能要素

class PDFPatentParser:
    """PDF专利文档解析器"""

    def __init__(self):
        self.section_patterns = {
            PatentSection.TITLE: [
                r"发明名称[：:]\s*(.+)",
                r"专利名称[：:]\s*(.+)",
                r"标题[：:]\s*(.+)"
            ],
            PatentSection.ABSTRACT: [
                r"摘要[：:]\s*(.+?)(?=\n\n|\n[一二三四五六七八九十]|权利要求)",
                r"技术领域[：:]\s*(.+?)(?=\n\n|\n[一二三四五六七八九十])"
            ],
            PatentSection.CLAIMS: [
                r"权利要求书[：:]\s*(.+?)(?=\n\n说明书|\n具体实施方式|说明书|$)",
                r"权利要求[：:]\s*(.+?)(?=\n\n说明书|\n具体实施方式|说明书|$)",
                # 添加针对OCR识别的模糊匹配
                r"权 利 要 求 书\s*(.+?)(?=\n\n说 明 书|\n具 体 实 施 方 式|说明书|$)"
            ],
            PatentSection.DESCRIPTION: [
                r"说明书[：:]\s*(.+?)(?=\n\n具体实施方式|附图说明|$)",
                r"技术方案[：:]\s*(.+?)(?=\n\n具体实施方式|附图说明|$)"
            ]
        }

        # 优化权利要求匹配模式，适应OCR识别的格式
        self.claim_pattern = re.compile(r"(\d+)\.?\s*[、.]?\s*(.+?)(?=\n\s*\d+\.|\n\s*[权利要求书|说明书|附图说明]|$)", re.DOTALL)

    def parse_pdf(self, file_path: str, doc_id: str = None) -> PatentDocument:
        """
        解析PDF专利文档

        Args:
            file_path: PDF文件路径
            doc_id: 文档ID

        Returns:
            解析后的专利文档
        """
        logger.info(f"开始解析PDF文档: {file_path}")

        # 提取文本
        text = self._extract_text_from_pdf(file_path)

        # 提取各章节
        sections = self._extract_sections(text)

        # 解析权利要求
        claims = self._parse_claims(sections.get(PatentSection.CLAIMS, ''))

        # 生成文档ID
        if not doc_id:
            doc_id = Path(file_path).stem

        # 创建专利文档对象
        patent_doc = PatentDocument(
            doc_id=doc_id,
            doc_type=DocumentType.PATENT,
            file_path=file_path,
            title=sections.get(PatentSection.TITLE, '').strip(),
            abstract=sections.get(PatentSection.ABSTRACT, '').strip(),
            claims=claims,
            description=sections.get(PatentSection.DESCRIPTION, '').strip(),
            sections=sections,
            metadata={
                'file_size': Path(file_path).stat().st_size,
                'page_count': self._get_page_count(file_path),
                'parsing_time': self._get_current_time()
            }
        )

        logger.info(f"PDF解析完成，提取到 {len(claims)} 个权利要求")
        return patent_doc

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """从PDF提取文本（支持图像型PDF的OCR）"""
        try:
            doc = fitz.open(file_path)
            text = ''

            for page_num, page in enumerate(doc):
                # 首先尝试直接提取文本
                page_text = page.get_text()

                if len(page_text.strip()) > 50:  # 有足够的文本，不需要OCR
                    text += page_text
                    logger.info(f"第{page_num+1}页：直接提取文本 ({len(page_text)} 字符)")
                else:
                    # 文本太少，尝试OCR
                    try:
                        ocr_text = self._ocr_page(page)
                        if ocr_text:
                            text += ocr_text
                            logger.info(f"第{page_num+1}页：OCR识别文本 ({len(ocr_text)} 字符)")
                        else:
                            logger.warning(f"第{page_num+1}页：OCR识别失败")
                    except Exception as ocr_error:
                        logger.error(f"第{page_num+1}页：OCR处理失败: {str(ocr_error)}")
                        # 仍然添加原始文本（可能是空文本）
                        text += page_text

            doc.close()
            return text

        except Exception as e:
            logger.error(f"PDF文本提取失败: {str(e)}")
            return ''

    def _ocr_page(self, page) -> str:
        """对PDF页面进行OCR识别"""
        try:
            import io

            import pytesseract
            from PIL import Image

            # 将页面转换为图像
            mat = fitz.Matrix(2.0, 2.0)  # 提高分辨率以改善OCR效果
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes('png')
            img = Image.open(io.BytesIO(img_data))

            # 配置Tesseract参数，专门针对中文专利文档
            custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'
            ocr_text = pytesseract.image_to_string(img, config=custom_config)

            return ocr_text

        except ImportError:
            logger.warning('pytesseract未安装，无法进行OCR识别')
            return ''
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            return ''

    def _extract_sections(self, text: str) -> Dict[PatentSection, str]:
        """提取专利各章节内容"""
        sections = {}

        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    sections[section_type] = match.group(1).strip()
                    break

        return sections

    def _parse_claims(self, claims_text: str) -> Dict[int, str]:
        """解析权利要求"""
        claims = {}

        if not claims_text:
            return claims

        # 清理文本
        claims_text = re.sub(r'\s+', ' ', claims_text.strip())

        # 匹配权利要求
        matches = self.claim_pattern.finditer(claims_text)

        for match in matches:
            claim_num = int(match.group(1))
            claim_text = match.group(2).strip()
            claims[claim_num] = claim_text

        return claims

    def _get_page_count(self, file_path: str) -> int:
        """获取PDF页数"""
        try:
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            return page_count
        except:
            return 0

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().isoformat()

class PatentFeatureExtractor:
    """专利技术特征提取器"""

    def __init__(self):
        # 结构特征模式
        self.structural_patterns = [
            r"包括(.+?)(?:，|；|。|$)",
            r"由(.+?)组成",
            r"具有(.+?)(?:，|；|。|$)",
            r"设置(.+?)(?:，|；|。|$)",
            r"安装(.+?)(?:，|；|。|$)",
            r"连接(.+?)(?:，|；|。|$)",
            r"(.+?)模块",
            r"(.+?)装置",
            r"(.+?)机构",
            r"(.+?)部件"
        ]

        # 功能特征模式
        self.functional_patterns = [
            r"用于(.+?)(?:，|；|。|$)",
            r"能够(.+?)(?:，|；|。|$)",
            r"实现(.+?)(?:，|；|。|$)",
            r"控制(.+?)(?:，|；|。|$)",
            r"处理(.+?)(?:，|；|。|$)",
            r"检测(.+?)(?:，|；|。|$)",
            r"调节(.+?)(?:，|；|。|$)",
            r"驱动(.+?)(?:，|；|。|$)"
        ]

        # 性能特征模式
        self.performance_patterns = [
            r"精度为(.+?)(?:，|；|。|$)",
            r"速度(.+?)(?:，|；|。|$)",
            r"效率(.+?)(?:，|；|。|$)",
            r"响应时间(.+?)(?:，|；|。|$)",
            r"功耗(.+?)(?:，|；|。|$)",
            r"温度(.+?)(?:，|；|。|$)",
            r"压力(.+?)(?:，|；|。|$)"
        ]

    def extract_features_from_claim(self, claim_text: str, claim_number: int) -> ClaimAnalysis:
        """
        从权利要求中提取技术特征

        Args:
            claim_text: 权利要求文本
            claim_number: 权利要求号

        Returns:
            权利要求分析结果
        """
        logger.info(f"开始分析权利要求 {claim_number}")

        # 分析权利要求类型
        claim_type = self._analyze_claim_type(claim_text, claim_number)

        # 分离前序部分和主体部分
        preamble, body = self._split_claim_preamble_body(claim_text)

        # 提取各类技术特征
        structural_features = self._extract_structural_features(body)
        functional_features = self._extract_functional_features(body)
        performance_features = self._extract_performance_features(body)

        # 合并所有特征
        all_features = structural_features + functional_features + performance_features

        # 提取技术限定
        limitations = self._extract_limitations(body)

        # 提取结构要素和功能要素
        structural_elements = [f.description for f in structural_features]
        functional_elements = [f.description for f in functional_features]

        return ClaimAnalysis(
            claim_number=claim_number,
            claim_type=claim_type,
            preamble=preamble,
            body=body,
            technical_features=all_features,
            limitations=limitations,
            structural_elements=structural_elements,
            functional_elements=functional_elements
        )

    def _analyze_claim_type(self, claim_text: str, claim_number: int) -> str:
        """分析权利要求类型"""
        # 独立权利要求通常不包含"如权利要求X所述"
        if '如权利要求' in claim_text or '根据权利要求' in claim_text:
            return 'dependent'
        else:
            return 'independent'

    def _split_claim_preamble_body(self, claim_text: str) -> Tuple[str, str]:
        """分离权利要求的前序部分和主体部分"""
        # 查找特征部分通常开始的关键词
        feature_keywords = ['其特征在于', '包括', '包含', '具有']

        for keyword in feature_keywords:
            if keyword in claim_text:
                parts = claim_text.split(keyword, 1)
                if len(parts) == 2:
                    return parts[0].strip(), keyword + parts[1].strip()

        # 如果没有找到明确的分隔，整个文本作为主体
        return '', claim_text.strip()

    def _extract_structural_features(self, text: str) -> List[TechnicalFeature]:
        """提取结构特征"""
        features = []
        feature_id = 1

        for pattern in self.structural_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature_text = match.group(1).strip()
                if len(feature_text) > 2:  # 过滤过短的匹配
                    feature = TechnicalFeature(
                        feature_id=f"S{feature_id:03d}",
                        description=feature_text,
                        category='structural',
                        importance=0.9,  # 结构特征重要性高
                        keywords=self._extract_keywords(feature_text),
                        source_section=PatentSection.CLAIMS,
                        claim_reference=None,
                        confidence=0.8
                    )
                    features.append(feature)
                    feature_id += 1

        return features

    def _extract_functional_features(self, text: str) -> List[TechnicalFeature]:
        """提取功能特征"""
        features = []
        feature_id = 1

        for pattern in self.functional_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature_text = match.group(1).strip()
                if len(feature_text) > 2:
                    feature = TechnicalFeature(
                        feature_id=f"F{feature_id:03d}",
                        description=feature_text,
                        category='functional',
                        importance=0.8,
                        keywords=self._extract_keywords(feature_text),
                        source_section=PatentSection.CLAIMS,
                        claim_reference=None,
                        confidence=0.75
                    )
                    features.append(feature)
                    feature_id += 1

        return features

    def _extract_performance_features(self, text: str) -> List[TechnicalFeature]:
        """提取性能特征"""
        features = []
        feature_id = 1

        for pattern in self.performance_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                feature_text = match.group(1).strip()
                if len(feature_text) > 2:
                    feature = TechnicalFeature(
                        feature_id=f"P{feature_id:03d}",
                        description=feature_text,
                        category='performance',
                        importance=0.7,
                        keywords=self._extract_keywords(feature_text),
                        source_section=PatentSection.CLAIMS,
                        claim_reference=None,
                        confidence=0.7
                    )
                    features.append(feature)
                    feature_id += 1

        return features

    def _extract_limitations(self, text: str) -> List[str]:
        """提取技术限定"""
        # 技术限定通常包含限定词
        limitation_patterns = [
            r"所述的(.+?)(?:，|；|。|$)",
            r"(.+?)的(.+?)(?:，|；|。|$)",
            r"由(.+?)制成",
            r"材料为(.+?)(?:，|；|。|$)"
        ]

        limitations = []
        for pattern in limitation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                limitation = match.group(0).strip()
                if limitation not in limitations:
                    limitations.append(limitation)

        return limitations

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，可以后续优化
        import jieba
        words = jieba.lcut(text)
        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '了', '和', '与', '或', '但', '而', '及', '等', '其', '该'}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        return keywords[:5]  # 返回前5个关键词

class EnhancedPerceptionLayer:
    """增强的感知层"""

    def __init__(self):
        self.pdf_parser = PDFPatentParser()
        self.feature_extractor = PatentFeatureExtractor()

    def analyze_patent_document(self, file_path: str, doc_id: str = None) -> PatentDocument:
        """
        分析专利文档

        Args:
            file_path: 文件路径
            doc_id: 文档ID

        Returns:
            分析后的专利文档
        """
        # 解析PDF文档
        patent_doc = self.pdf_parser.parse_pdf(file_path, doc_id)

        # 为每个权利要求进行深度分析
        patent_doc.metadata['claim_analyses'] = {}
        for claim_num, claim_text in patent_doc.claims.items():
            claim_analysis = self.feature_extractor.extract_features_from_claim(claim_text, claim_num)
            patent_doc.metadata['claim_analyses'][claim_num] = claim_analysis

        return patent_doc

    def get_claim_1_features(self, file_path: str) -> List[TechnicalFeature]:
        """
        获取权利要求1的技术特征（专门用于新颖性分析）

        Args:
            file_path: PDF专利文件路径

        Returns:
            权利要求1的技术特征列表
        """
        # 解析专利文档
        patent_doc = self.analyze_patent_document(file_path)

        # 获取权利要求1的分析结果
        claim_1_analysis = patent_doc.metadata.get('claim_analyses', {}).get(1)

        if claim_1_analysis:
            logger.info(f"权利要求1分析完成，提取到 {len(claim_1_analysis.technical_features)} 个技术特征")
            return claim_1_analysis.technical_features
        else:
            logger.warning('未找到权利要求1')
            return []

# 测试代码
if __name__ == '__main__':
    perception = EnhancedPerceptionLayer()

    # 测试文件路径
    test_file = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures/CN201815134U.pdf'

    if Path(test_file).exists():
        logger.info(f"🔍 开始分析专利文档: {test_file}")

        # 分析权利要求1的特征
        features = perception.get_claim_1_features(test_file)

        logger.info(f"\n📋 权利要求1技术特征:")
        for i, feature in enumerate(features, 1):
            logger.info(f"{i}. {feature.description}")
            logger.info(f"   类型: {feature.category}, 重要性: {feature.importance}")
            logger.info(f"   关键词: {', '.join(feature.keywords)}")
            print()
    else:
        logger.info(f"❌ 测试文件不存在: {test_file}")