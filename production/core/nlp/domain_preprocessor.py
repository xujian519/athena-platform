#!/usr/bin/env python3
"""
领域专用NLP预处理器
Domain-Specific NLP Preprocessor

为法律和专利领域提供专业的文本预处理、实体识别和语义分析
"""

from __future__ import annotations
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import jieba
    import jieba.posseg as pseg
    from jieba import analyse

    JIEBA_AVAILABLE = True
except ImportError:
    print("⚠️ jieba未安装,使用基础文本处理")
    JIEBA_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DomainSpecificPreprocessor:
    """领域专用预处理器"""

    def __init__(self):
        self.legal_entities: dict[str, Any] = {}
        self.patent_entities: dict[str, Any] = {}
        self.legal_terms = set()
        self.patent_terms = set()
        self.legal_patterns: dict[str, Any] = {}
        self.patent_patterns: dict[str, Any] = {}

        # 加载领域词典
        self._load_domain_dictionaries()

        # 初始化jieba
        if JIEBA_AVAILABLE:
            self._init_jieba()

    def _load_domain_dictionaries(self) -> Any:
        """加载领域词典"""
        try:
            # 法律术语词典
            legal_terms_file = Path(__file__).parent.parent / "data" / "legal_terms.json"
            if legal_terms_file.exists():
                with open(legal_terms_file, encoding="utf-8") as f:
                    legal_data = json.load(f)
                    self.legal_terms = set(legal_data.get("terms", []))
                    self.legal_entities = legal_data.get("entities", {})
                    self.legal_patterns = legal_data.get("patterns", {})
                logger.info(f"✅ 加载法律术语词典: {len(self.legal_terms)}个术语")

            # 专利术语词典
            patent_terms_file = Path(__file__).parent.parent / "data" / "patent_terms.json"
            if patent_terms_file.exists():
                with open(patent_terms_file, encoding="utf-8") as f:
                    patent_data = json.load(f)
                    self.patent_terms = set(patent_data.get("terms", []))
                    self.patent_entities = patent_data.get("entities", {})
                    self.patent_patterns = patent_data.get("patterns", {})
                logger.info(f"✅ 加载专利术语词典: {len(self.patent_terms)}个术语")

            # 如果词典文件不存在,创建默认词典
            if not legal_terms_file.exists() or not patent_terms_file.exists():
                self._create_default_dictionaries(legal_terms_file, patent_terms_file)

        except Exception as e:
            logger.error(f"❌ 加载领域词典失败: {e}")
            self._create_default_dictionaries(legal_terms_file, patent_terms_file)

    def _create_default_dictionaries(self, legal_file: Path, patent_file: Path) -> Any:
        """创建默认领域词典"""
        logger.info("📝 创建默认领域词典...")

        # 默认法律词典
        default_legal = {
            "terms": [
                "民法典",
                "专利法",
                "商标法",
                "著作权法",
                "民事诉讼法",
                "刑事诉讼法",
                "行政诉讼法",
                "合同法",
                "侵权责任法",
                "知识产权",
                "专利权",
                "商标权",
                "著作权",
                "商业秘密",
                "不正当竞争",
                "反垄断",
                "消费者权益保护",
                "劳动法",
                "公司法",
                "证券法",
                "破产法",
                "物权法",
                "债权法",
            ],
            "entities": {
                "法律法规": ["法", "条例", "规定", "办法", "解释", "决定"],
                "司法机关": ["法院", "检察院", "公安局", "司法局", "仲裁委员会"],
                "法律行为": ["起诉", "应诉", "上诉", "申诉", "执行", "仲裁", "调解"],
                "法律文书": ["判决书", "裁定书", "调解书", "起诉书", "答辩状"],
            },
            "patterns": {
                "引用法条": r"《([^》]+)》第([一二三四五六七八九十百千万\d]+)条",
                "案件编号": r"[(\(]\d{4}[)\)][^号]+号",
                "金额": r"[一二三四五六七八九十百千万\d]+[万亿元元角分]",
                "时间": r"\d{4}年\d{1,2}月\d{1,2}日",
            },
        }

        # 默认专利词典
        default_patent = {
            "terms": [
                "发明专利",
                "实用新型专利",
                "外观设计专利",
                "专利申请",
                "专利权",
                "专利审查",
                "专利授权",
                "专利无效",
                "专利侵权",
                "专利检索",
                "新颖性",
                "创造性",
                "实用性",
                "公开充分",
                "清楚完整",
                "技术方案",
                "技术特征",
                "背景技术",
                "现有技术",
                "发明点",
                "权利要求",
                "说明书",
                "附图",
                "摘要",
                "优先权",
            ],
            "entities": {
                "专利类型": ["发明专利", "实用新型", "外观设计"],
                "申请流程": ["申请", "受理", "初审", "公布", "实审", "授权", "公告"],
                "法律状态": ["有效", "无效", "终止", "放弃", "撤回"],
                "技术要素": ["结构", "组件", "装置", "系统", "方法", "工艺"],
            },
            "patterns": {
                "专利号": r"(CN|ZL)\d{9,13}[A-Z0-9.]*",
                "申请号": r"\d{13}[A-Z0-9.]*",
                "公开号": r"CN\d{9}[A-Z]",
                "国际分类": r"A\d{2}[A-Z]\s*\d+/\d+",
            },
        }

        # 保存词典文件
        legal_file.parent.mkdir(exist_ok=True)
        patent_file.parent.mkdir(exist_ok=True)

        with open(legal_file, "w", encoding="utf-8") as f:
            json.dump(default_legal, f, ensure_ascii=False, indent=2)

        with open(patent_file, "w", encoding="utf-8") as f:
            json.dump(default_patent, f, ensure_ascii=False, indent=2)

        # 加载到内存
        self.legal_terms = set(default_legal["terms"])
        self.patent_terms = set(default_patent["terms"])
        self.legal_entities = default_legal["entities"]
        self.patent_entities = default_patent["entities"]
        self.legal_patterns = default_legal["patterns"]
        self.patent_patterns = default_patent["patterns"]

        logger.info("✅ 默认领域词典创建完成")

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        try:
            # 添加自定义词典
            for term in self.legal_terms:
                jieba.add_word(term, freq=1000, tag="法律术语")

            for term in self.patent_terms:
                jieba.add_word(term, freq=1000, tag="专利术语")

            logger.info("✅ jieba自定义词典加载完成")
        except Exception as e:
            logger.error(f"❌ jieba初始化失败: {e}")

    async def preprocess_legal_text(self, text: str) -> dict[str, Any]:
        """法律文本预处理"""
        try:
            # 基础清理
            cleaned_text = self._basic_text_cleaning(text)

            # 实体识别
            entities = self._extract_legal_entities(cleaned_text)

            # 关键词提取
            keywords = await self._extract_legal_keywords(cleaned_text)

            # 模式匹配
            patterns = self._match_legal_patterns(cleaned_text)

            # 分词和词性标注
            tokens = self._tokenize_legal(cleaned_text)

            # 句子分割
            sentences = self._split_sentences(cleaned_text)

            # 法律术语标准化
            normalized_text = self._normalize_legal_terms(cleaned_text)

            result = {
                "original_text": text,
                "cleaned_text": cleaned_text,
                "normalized_text": normalized_text,
                "entities": entities,
                "keywords": keywords,
                "patterns": patterns,
                "tokens": tokens,
                "sentences": sentences,
                "domain": "legal",
                "processing_time": datetime.now().isoformat(),
            }

            logger.info(f"✅ 法律文本预处理完成,识别到 {len(entities)} 个实体")
            return result

        except Exception as e:
            logger.error(f"❌ 法律文本预处理失败: {e}")
            return {"error": str(e)}

    async def preprocess_patent_text(self, text: str) -> dict[str, Any]:
        """专利文本预处理"""
        try:
            # 基础清理
            cleaned_text = self._basic_text_cleaning(text)

            # 实体识别
            entities = self._extract_patent_entities(cleaned_text)

            # 关键词提取
            keywords = await self._extract_patent_keywords(cleaned_text)

            # 模式匹配
            patterns = self._match_patent_patterns(cleaned_text)

            # 技术特征提取
            tech_features = self._extract_technical_features(cleaned_text)

            # 分词和词性标注
            tokens = self._tokenize_patent(cleaned_text)

            # 句子分割
            sentences = self._split_sentences(cleaned_text)

            # 专利术语标准化
            normalized_text = self._normalize_patent_terms(cleaned_text)

            result = {
                "original_text": text,
                "cleaned_text": cleaned_text,
                "normalized_text": normalized_text,
                "entities": entities,
                "keywords": keywords,
                "patterns": patterns,
                "tech_features": tech_features,
                "tokens": tokens,
                "sentences": sentences,
                "domain": "patent",
                "processing_time": datetime.now().isoformat(),
            }

            logger.info(f"✅ 专利文本预处理完成,识别到 {len(entities)} 个实体")
            return result

        except Exception as e:
            logger.error(f"❌ 专利文本预处理失败: {e}")
            return {"error": str(e)}

    def _basic_text_cleaning(self, text: str) -> str:
        """基础文本清理"""
        # 去除多余空白
        text = re.sub(r"\s+", " ", text)
        # 去除特殊字符(保留中文、英文、数字、基本标点)
        text = re.sub(r"[^\u4e00-\u9fff\w\s.,;:!?()()。,;:!?]", " ", text)
        # 统一标点符号
        text = text.replace("(", "(").replace(")", ")")
        text = text.replace(",", ",").replace("。", ".")
        text = text.replace(";", ";").replace(":", ":")
        text = text.replace("!", "!").replace("?", "?")

        return text.strip()

    def _extract_legal_entities(self, text: str) -> list[dict[str, Any]]:
        """提取法律实体"""
        entities = []

        for entity_type, entity_list in self.legal_entities.items():
            for entity in entity_list:
                # 查找所有匹配
                matches = re.finditer(entity, text, re.IGNORECASE)
                for match in matches:
                    entities.append(
                        {
                            "type": entity_type,
                            "text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 0.8,
                        }
                    )

        # 查找法律术语
        for term in self.legal_terms:
            if term in text:
                start = text.find(term)
                entities.append(
                    {
                        "type": "法律术语",
                        "text": term,
                        "start": start,
                        "end": start + len(term),
                        "confidence": 0.9,
                    }
                )

        return entities

    def _extract_patent_entities(self, text: str) -> list[dict[str, Any]]:
        """提取专利实体"""
        entities = []

        for entity_type, entity_list in self.patent_entities.items():
            for entity in entity_list:
                # 查找所有匹配
                matches = re.finditer(entity, text, re.IGNORECASE)
                for match in matches:
                    entities.append(
                        {
                            "type": entity_type,
                            "text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 0.8,
                        }
                    )

        # 查找专利术语
        for term in self.patent_terms:
            if term in text:
                start = text.find(term)
                entities.append(
                    {
                        "type": "专利术语",
                        "text": term,
                        "start": start,
                        "end": start + len(term),
                        "confidence": 0.9,
                    }
                )

        return entities

    async def _extract_legal_keywords(self, text: str) -> list[str]:
        """提取法律关键词"""
        if JIEBA_AVAILABLE:
            try:
                # 使用TF-IDF提取关键词
                keywords = analyse.extract_tags(text, top_k=20, with_weight=False)
                # 过滤领域相关关键词
                domain_keywords = [kw for kw in keywords if kw in self.legal_terms or len(kw) > 1]
                return domain_keywords[:10]
            except Exception as e:
                logger.error(f"❌ 法律关键词提取失败: {e}")

        # 回退方法
        keywords = []
        for term in self.legal_terms:
            if term in text:
                keywords.append(term)
        return keywords[:10]

    async def _extract_patent_keywords(self, text: str) -> list[str]:
        """提取专利关键词"""
        if JIEBA_AVAILABLE:
            try:
                # 使用TF-IDF提取关键词
                keywords = analyse.extract_tags(text, top_k=20, with_weight=False)
                # 过滤领域相关关键词
                domain_keywords = [kw for kw in keywords if kw in self.patent_terms or len(kw) > 1]
                return domain_keywords[:10]
            except Exception as e:
                logger.error(f"❌ 专利关键词提取失败: {e}")

        # 回退方法
        keywords = []
        for term in self.patent_terms:
            if term in text:
                keywords.append(term)
        return keywords[:10]

    def _match_legal_patterns(self, text: str) -> list[dict[str, Any]]:
        """匹配法律模式"""
        patterns = []

        for pattern_name, pattern_regex in self.legal_patterns.items():
            matches = re.finditer(pattern_regex, text)
            for match in matches:
                patterns.append(
                    {
                        "type": pattern_name,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "groups": match.groups() if match.groups() else [],
                    }
                )

        return patterns

    def _match_patent_patterns(self, text: str) -> list[dict[str, Any]]:
        """匹配专利模式"""
        patterns = []

        for pattern_name, pattern_regex in self.patent_patterns.items():
            matches = re.finditer(pattern_regex, text)
            for match in matches:
                patterns.append(
                    {
                        "type": pattern_name,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "groups": match.groups() if match.groups() else [],
                    }
                )

        return patterns

    def _extract_technical_features(self, text: str) -> list[dict[str, Any]]:
        """提取技术特征"""
        features = []

        # 技术特征模式
        tech_patterns = [
            r"([^,。;:!?\n]+)(?:装置|设备|系统|组件|部件|机构)",
            r"([^,。;:!?\n]+)(?:方法|工艺|步骤|流程|过程)",
            r"([^,。;:!?\n]+)(?:包括|包含|设有|配置)",
            r"([^,。;:!?\n]+)(?:连接|固定|安装|设置)",
        ]

        for i, pattern in enumerate(tech_patterns):
            matches = re.finditer(pattern, text)
            for match in matches:
                features.append(
                    {
                        "type": f"技术特征_{i+1}",
                        "description": match.group(1).strip(),
                        "full_text": match.group().strip(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        return features[:20]  # 限制数量

    def _tokenize_legal(self, text: str) -> list[dict[str, Any]]:
        """法律文本分词"""
        if not JIEBA_AVAILABLE:
            # 简单分词
            words = re.findall(r"[\u4e00-\u9fff]+|[a-z_a-Z]+|\d+", text)
            return [{"word": word, "pos": "unknown"} for word in words]

        tokens = []
        try:
            # 使用jieba分词和词性标注
            words = pseg.cut(text)
            for word, flag in words:
                tokens.append(
                    {"word": word, "pos": flag, "is_legal_term": word in self.legal_terms}
                )
        except Exception as e:
            logger.error(f"❌ 法律文本分词失败: {e}")

        return tokens

    def _tokenize_patent(self, text: str) -> list[dict[str, Any]]:
        """专利文本分词"""
        if not JIEBA_AVAILABLE:
            # 简单分词
            words = re.findall(r"[\u4e00-\u9fff]+|[a-z_a-Z]+|\d+", text)
            return [{"word": word, "pos": "unknown"} for word in words]

        tokens = []
        try:
            # 使用jieba分词和词性标注
            words = pseg.cut(text)
            for word, flag in words:
                tokens.append(
                    {"word": word, "pos": flag, "is_patent_term": word in self.patent_terms}
                )
        except Exception as e:
            logger.error(f"❌ 专利文本分词失败: {e}")

        return tokens

    def _split_sentences(self, text: str) -> list[str]:
        """句子分割"""
        # 中文句子分割
        sentences = re.split(r"[。!?;\n]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _normalize_legal_terms(self, text: str) -> str:
        """法律术语标准化"""
        # 法律术语标准化映射
        term_mapping = {
            "民法": "民法典",
            "刑法": "刑法典",
            "诉讼法": "民事诉讼法",
            "专利": "专利法",
            "商标": "商标法",
            "著作权": "著作权法",
        }

        normalized = text
        for old_term, new_term in term_mapping.items():
            normalized = normalized.replace(old_term, new_term)

        return normalized

    def _normalize_patent_terms(self, text: str) -> str:
        """专利术语标准化"""
        # 专利术语标准化映射
        term_mapping = {
            "发明": "发明专利",
            "实用新型": "实用新型专利",
            "外观设计": "外观设计专利",
            "创造": "创造性",
            "新颖": "新颖性",
            "实用": "实用性",
        }

        normalized = text
        for old_term, new_term in term_mapping.items():
            normalized = normalized.replace(old_term, new_term)

        return normalized

    async def process_mixed_text(self, text: str) -> dict[str, Any]:
        """处理混合领域文本"""
        # 先判断主要领域
        legal_score = sum(1 for term in self.legal_terms if term in text)
        patent_score = sum(1 for term in self.patent_terms if term in text)

        if legal_score > patent_score:
            logger.info("🏛️ 判定为法律领域文本")
            return await self.preprocess_legal_text(text)
        elif patent_score > legal_score:
            logger.info("📄 判定为专利领域文本")
            return await self.preprocess_patent_text(text)
        else:
            logger.info("🔄 判定为混合领域文本,分别处理")
            legal_result = await self.preprocess_legal_text(text)
            patent_result = await self.preprocess_patent_text(text)

            # 合并结果
            return {
                "original_text": text,
                "domain": "mixed",
                "legal_processing": legal_result,
                "patent_processing": patent_result,
                "processing_time": datetime.now().isoformat(),
            }


async def main():
    """测试领域预处理器"""
    print("🔧 测试领域专用NLP预处理器...")

    preprocessor = DomainSpecificPreprocessor()

    # 测试文本
    test_texts = [
        {
            "type": "legal",
            "text": "根据《中华人民共和国专利法》第六十五条规定,侵犯专利权的赔偿数额按照权利人因被侵权所受到的实际损失确定。",
        },
        {
            "type": "patent",
            "text": "本发明涉及一种智能专利检索系统,包括数据采集模块、预处理模块、特征提取模块和匹配算法模块。该系统通过深度学习技术提高检索精度。",
        },
        {
            "type": "mixed",
            "text": "在专利侵权诉讼中,法院通常会依据《专利法》和《民事诉讼法》的相关规定,对被控侵权产品与专利权利要求进行技术特征对比分析。",
        },
    ]

    print("\n" + "=" * 80)
    print("📊 NLP预处理测试结果:")
    print("=" * 80)

    for i, test_case in enumerate(test_texts, 1):
        print(f"\n{i}. 测试文本 ({test_case['type']}):")
        print(f"   {test_case['text'][:50]}...")

        if test_case["type"] == "legal":
            result = await preprocessor.preprocess_legal_text(test_case["text"])
        elif test_case["type"] == "patent":
            result = await preprocessor.preprocess_patent(test_case["text"])
        else:
            result = await preprocessor.process_mixed_text(test_case["text"])

        if "error" not in result:
            print("   ✅ 预处理成功")
            print(f"   📝 实体数量: {len(result.get('entities', []))}")
            print(f"   🔑 关键词数量: {len(result.get('keywords', []))}")
            print(f"   🎯 模式匹配: {len(result.get('patterns', []))}")
        else:
            print(f"   ❌ 预处理失败: {result['error']}")

    print("\n🎉 NLP预处理器测试完成!")


# 入口点: @async_main装饰器已添加到main函数
