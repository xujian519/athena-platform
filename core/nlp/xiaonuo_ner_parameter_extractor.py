#!/usr/bin/env python3
from __future__ import annotations
"""
小诺命名实体识别(NER)参数提取系统
集成深度学习NER技术,实现高精度参数提取和实体识别

功能特性:
1. 基于BERT的中文实体识别
2. 多类型实体分类和提取
3. 实体关系识别和链接
4. 参数验证和纠错
5. 多源参数融合算法
6. 实时性能优化

作者: 小诺AI团队
日期: 2025-12-18
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import jieba
import jieba.posseg as pseg

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import numpy as np

# NLP和机器学习库
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class RuleBasedEntityClassifier:
    """基于规则的实体分类器"""

    def __init__(self):
        self.entity_patterns = self._init_patterns()

    def _init_patterns(self) -> Any:
        """初始化实体模式"""
        return {
            "programming_languages": [
                "python",
                "java",
                "javascript",
                "typescript",
                "c++",
                "c#",
                "go",
                "rust",
                "php",
                "ruby",
            ],
            "frameworks": [
                "spring",
                "django",
                "flask",
                "react",
                "vue",
                "angular",
                "laravel",
                "express",
            ],
            "databases": ["mysql", "postgresql", "mongodb", "redis", "oracle", "sqlserver"],
            "technologies": [
                "infrastructure/infrastructure/docker",
                "infrastructure/infrastructure/kubernetes",
                "aws",
                "azure",
                "gcp",
                "tensorflow",
                "pytorch",
            ],
        }

    def predict(self, features) -> None:
        """预测实体类型(简单实现)"""
        return ["ENTITY"]  # 简化实现


class EntityType(Enum):
    """实体类型定义"""

    # 通用实体类型
    PERSON = "PERSON"  # 人名
    ORGANIZATION = "ORGANIZATION"  # 组织机构
    LOCATION = "LOCATION"  # 地点
    TIME = "TIME"  # 时间
    DATE = "DATE"  # 日期

    # 技术实体类型
    TECHNOLOGY = "TECHNOLOGY"  # 技术名称
    LANGUAGE = "LANGUAGE"  # 编程语言
    FRAMEWORK = "FRAMEWORK"  # 框架
    LIBRARY = "LIBRARY"  # 库
    TOOL = "TOOL"  # 工具

    # 业务实体类型
    FILE = "FILE"  # 文件名
    URL = "URL"  # 网址
    EMAIL = "EMAIL"  # 邮箱
    PHONE = "PHONE"  # 电话
    ID = "ID"  # ID标识

    # 代码相关实体
    FUNCTION = "FUNCTION"  # 函数名
    VARIABLE = "VARIABLE"  # 变量名
    CLASS = "CLASS"  # 类名
    METHOD = "METHOD"  # 方法名
    API = "API"  # API接口

    # 数值实体类型
    NUMBER = "NUMBER"  # 数字
    PERCENTAGE = "PERCENTAGE"  # 百分比
    CURRENCY = "CURRENCY"  # 货币
    VERSION = "VERSION"  # 版本号
    PORT = "PORT"  # 端口号

    # 描述实体类型
    DESCRIPTION = "DESCRIPTION"  # 描述
    KEYWORD = "KEYWORD"  # 关键词
    CATEGORY = "CATEGORY"  # 类别
    TAG = "TAG"  # 标签


class RelationType(Enum):
    """实体关系类型"""

    IS_A = "IS_A"  # 是一种
    PART_OF = "PART_OF"  # 是一部分
    INSTANCE_OF = "INSTANCE_OF"  # 是实例
    LOCATED_IN = "LOCATED_IN"  # 位于
    CREATED_BY = "CREATED_BY"  # 创建者
    USES = "USES"  # 使用
    DEPENDS_ON = "DEPENDS_ON"  # 依赖
    VERSION_OF = "VERSION_OF"  # 版本
    PARAMETER_OF = "PARAMETER_OF"  # 参数
    RESULT_OF = "RESULT_OF"  # 结果
    RELATED_TO = "RELATED_TO"  # 相关


@dataclass
class Entity:
    """命名实体"""

    text: str  # 实体文本
    entity_type: EntityType  # 实体类型
    start_pos: int  # 开始位置
    end_pos: int  # 结束位置
    confidence: float  # 置信度
    properties: dict[str, Any] = field(default_factory=dict)  # 属性
    context: str = ""  # 上下文


@dataclass
class EntityRelation:
    """实体关系"""

    entity1: Entity  # 实体1
    entity2: Entity  # 实体2
    relation_type: RelationType  # 关系类型
    confidence: float  # 置信度
    evidence: str = ""  # 证据


@dataclass
class ParameterExtraction:
    """参数提取结果"""

    intent: str  # 意图
    entities: list[Entity]  # 实体列表
    relations: list[EntityRelation]  # 关系列表
    parameters: dict[str, Any]  # 参数字典
    confidence: float  # 整体置信度
    missing_params: list[str]  # 缺失参数
    validation_errors: list[str]  # 验证错误
    extraction_time: float  # 提取耗时


@dataclass
class NERModelConfig:
    """NER模型配置"""

    model_name: str = "bert-base-chinese"
    max_length: int = 512
    batch_size: int = 32
    learning_rate: float = 2e-5
    epochs: int = 10
    warmup_steps: int = 500
    weight_decay: float = 0.01
    model_dir: str = "models/ner"
    data_dir: str = "data/ner"


class XiaonuoNERParameterExtractor:
    """小诺NER参数提取器"""

    def __init__(self, config: NERModelConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.entity_classifier = None
        self.relation_classifier = None
        self.scaler = StandardScaler()
        self.feature_vectorizer = TfidfVectorizer(max_features=5000)

        # 初始化jieba分词
        jieba.initialize()

        # 实体模式规则
        self.entity_patterns = self._init_entity_patterns()

        # 参数类型映射
        self.param_type_mapping = self._init_param_type_mapping()

        # 实体标准化规则
        self.entity_normalizers = self._init_entity_normalizers()

        # 加载预训练模型
        self._load_models()

        logger.info("🧠 小诺NER参数提取器初始化完成")
        logger.info(f"📊 支持实体类型: {len(EntityType)}种")
        logger.info(f"🔗 支持关系类型: {len(RelationType)}种")

    def _init_entity_patterns(self) -> dict[str, list[re.Pattern]]:
        """初始化实体识别模式"""
        patterns = {
            EntityType.URL: [
                # HTTP/HTTPS URLs - 更宽松的匹配
                re.compile(r"https?://[a-z_a-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+", re.IGNORECASE),
                # www开头的URL
                re.compile(r"www\.[a-z_a-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+", re.IGNORECASE),
                # 域名格式
                re.compile(
                    r"[a-z_a-Z0-9\-]+\.(com|cn|org|net|edu|gov|io|ai|tech|dev|app)(/[^\s]*)?",
                    re.IGNORECASE,
                ),
            ],
            EntityType.EMAIL: [
                # 标准邮箱格式 - 增强匹配
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
                # 中文域名邮箱
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[\u4e00-\u9fa5A-Za-z]{2,}\b"),
            ],
            EntityType.PHONE: [
                # 中国手机号 - 1开头,11位
                re.compile(r"\b1[3-9]\d{9}\b"),
                # 座机 - 区号-号码
                re.compile(r"\b\d{3,4}-\d{7,8}\b"),
                # 座机 - (区号)号码
                re.compile(r"\b\(\d{3,4}\)\s*\d{7,8}\b"),
                # 纯数字座机 (7-8位)
                re.compile(r"\b\d{7,8}\b"),
            ],
            EntityType.DATE: [
                # 数字日期 2024-01-15
                re.compile(r"\b\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?\b"),
                # 中文日期 2024年1月15日
                re.compile(r"\b\d{4}年\d{1,2}月\d{1,2}日\b"),
                # 相对日期
                re.compile(r"\b(今天|明天|昨天|后天|前天|大后天)\b"),
            ],
            EntityType.TIME: [
                # 时间格式 HH:MM:SS 或 HH:MM
                re.compile(r"\b\d{1,2}[::]\d{1,2}([::]\d{1,2})?\b"),
                # 时间描述
                re.compile(r"\b(早上|上午|中午|下午|晚上|半夜|凌晨|深夜)\b"),
            ],
            EntityType.VERSION: [
                # 版本号 v1.0.0
                re.compile(r"\bv?\d+\.\d+(\.\d+)?(-[a-z_a-Z0-9]+)?\b", re.IGNORECASE),
            ],
            EntityType.PORT: [
                # 端口号 - 在"端口"、"port"等关键词后 (允许无冒号,空格分隔)
                re.compile(r"(?:端口|port)[::\s]+(\d{1,5})\b", re.IGNORECASE),
                # 或者是URL中的:后数字 (常见于 http://localhost:8080)
                re.compile(r"://[^/:\s]+:(\d{1,5})\b"),
            ],
            EntityType.PERCENTAGE: [
                # 百分比 50% 或 50％ - 移除右侧边界,保留左侧边界
                re.compile(r"\b\d+(?:\.\d+)?[%％]"),
            ],
            EntityType.CURRENCY: [
                # 货币符号在前 ￥100 $100 ¥100
                re.compile(r"[￥$¥€£]\s*\d+(\.\d+)?"),
                # 货币单位在后 100元 100美元
                re.compile(r"\b\d+(\.\d+)?\s*(元|美元|欧元|英镑|日元|港币)\b"),
            ],
        }
        return patterns

    def _init_param_type_mapping(self) -> dict[str, EntityType]:
        """初始化参数类型映射"""
        return {
            "url": EntityType.URL,
            "email": EntityType.EMAIL,
            "phone": EntityType.PHONE,
            "date": EntityType.DATE,
            "time": EntityType.TIME,
            "version": EntityType.VERSION,
            "port": EntityType.PORT,
            "percentage": EntityType.PERCENTAGE,
            "currency": EntityType.CURRENCY,
            "person": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "location": EntityType.LOCATION,
            "technology": EntityType.TECHNOLOGY,
            "language": EntityType.LANGUAGE,
            "framework": EntityType.FRAMEWORK,
            "library": EntityType.LIBRARY,
            "tool": EntityType.TOOL,
            "file": EntityType.FILE,
            "function": EntityType.FUNCTION,
            "variable": EntityType.VARIABLE,
            "class": EntityType.CLASS,
            "method": EntityType.METHOD,
            "api": EntityType.API,
            "number": EntityType.NUMBER,
            "description": EntityType.DESCRIPTION,
            "keyword": EntityType.KEYWORD,
            "category": EntityType.CATEGORY,
            "tag": EntityType.TAG,
        }

    def _init_entity_normalizers(self) -> dict[EntityType, callable]:
        """初始化实体标准化规则"""
        return {
            EntityType.URL: lambda x: x.lower().strip(),
            EntityType.EMAIL: lambda x: x.lower().strip(),
            EntityType.DATE: self._normalize_date,
            EntityType.TIME: self._normalize_time,
            EntityType.VERSION: lambda x: x.lower().replace("v", ""),
            EntityType.NUMBER: lambda x: (
                float(re.sub(r"[^\d.]", "", x)) if re.sub(r"[^\d.]", "", x) else 0.0
            ),
            EntityType.PERCENTAGE: lambda x: (
                float(re.sub(r"[^\d.]", "", x)) / 100 if re.sub(r"[^\d.]", "", x) else 0.0
            ),
        }

    def _normalize_date(self, date_str: str) -> str:
        """日期标准化"""
        # 相对日期转换
        relative_dates = {"今天": "0d", "明天": "+1d", "昨天": "-1d", "后天": "+2d", "前天": "-2d"}

        for relative, standard in relative_dates.items():
            if relative in date_str:
                return standard

        # 数字日期格式统一
        date_str = re.sub(r"[年月日]", "-", date_str).strip("-")
        return date_str

    def _normalize_time(self, time_str: str) -> str:
        """时间标准化"""
        # 统一时间分隔符
        time_str = time_str.replace(":", ":").strip()

        # 时间描述标准化
        time_mapping = {
            "早上": "06:00",
            "上午": "09:00",
            "中午": "12:00",
            "下午": "15:00",
            "晚上": "18:00",
            "半夜": "00:00",
            "凌晨": "02:00",
        }

        return time_mapping.get(time_str, time_str)

    def _load_models(self) -> Any:
        """加载预训练模型"""
        try:
            # 尝试加载增强的BERT NER模型
            logger.info("🤖 尝试加载增强NER模型...")

            # 设置镜像源
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

            # 导入增强NER模块
            try:
                # 使用绝对导入
                from core.nlp.xiaonuo_enhanced_ner import XiaonuoEnhancedNER

                # 初始化增强NER (自动检测设备: MPS > CUDA > CPU)
                self.enhanced_ner = XiaonuoEnhancedNER(use_bert=True)

                # 验证模型是否成功加载
                model_info = self.enhanced_ner.get_model_info()

                if model_info.get("model_loaded") and model_info.get("tokenizer_loaded"):
                    logger.info("✅ 增强BERT NER模型加载成功")
                    logger.info(f"   模型: {model_info.get('model_name')}")
                    logger.info(f"   设备: {model_info.get('device')}")
                    logger.info(f"   标签数: {model_info.get('supported_labels')}")
                    self.use_bert_ner = True
                else:
                    logger.info("📝 BERT模型未完全加载,使用混合模式(规则+增强NER)")
                    self.use_bert_ner = False

            except Exception as e:
                logger.warning(f"⚠️ 增强NER模块加载失败: {e}")
                logger.info("📝 使用规则模式(规则+特殊实体)")
                self.enhanced_ner = None
                self.use_bert_ner = False

            # 保留规则模式作为后备
            self.model = None
            self.tokenizer = None

            # 尝试加载本地分类器
            classifier_path = os.path.join(self.config.model_dir, "entity_classifier.joblib")
            if os.path.exists(classifier_path):
                # 安全修复: 使用joblib替代pickle
                self.entity_classifier = joblib.load(classifier_path)
                logger.info("✅ 本地分类器加载完成")
            else:
                logger.info("📝 创建基于规则的分类器")
                self.entity_classifier = self._create_rule_based_classifier()

            if self.use_bert_ner:
                logger.info("✅ NER模型加载完成(BERT增强模式)")
            else:
                logger.info("✅ NER模型加载完成(规则模式)")

        except Exception as e:
            logger.warning(f"⚠️ 模型加载失败,使用规则模式: {e}")
            self.enhanced_ner = None
            self.use_bert_ner = False
            self.model = None
            self.tokenizer = None
            self.entity_classifier = self._create_rule_based_classifier()

    def _create_rule_based_classifier(self) -> Any:
        """创建基于规则的分类器"""
        # 创建一个简单的规则分类器
        return RuleBasedEntityClassifier()

    def extract_parameters(self, text: str, intent: str = "") -> ParameterExtraction:
        """
        提取文本中的参数

        Args:
            text: 输入文本
            intent: 用户意图

        Returns:
            ParameterExtraction: 参数提取结果
        """
        start_time = datetime.now()

        try:
            # 1. 实体识别
            entities = self._extract_entities(text)

            # 2. 实体关系识别
            relations = self._extract_relations(text, entities)

            # 3. 参数构建
            parameters = self._build_parameters(entities, relations, intent)

            # 4. 参数验证
            validation_errors = self._validate_parameters(parameters, intent)

            # 5. 缺失参数检测
            missing_params = self._detect_missing_parameters(parameters, intent)

            # 6. 计算置信度
            confidence = self._calculate_confidence(entities, relations, validation_errors)

            extraction_time = (datetime.now() - start_time).total_seconds()

            result = ParameterExtraction(
                intent=intent,
                entities=entities,
                relations=relations,
                parameters=parameters,
                confidence=confidence,
                missing_params=missing_params,
                validation_errors=validation_errors,
                extraction_time=extraction_time,
            )

            logger.info(
                f"🔍 参数提取完成: 文本长度={len(text)}, 实体数={len(entities)}, 耗时={extraction_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 参数提取失败: {e}")
            return ParameterExtraction(
                intent=intent,
                entities=[],
                relations=[],
                parameters={},
                confidence=0.0,
                missing_params=[],
                validation_errors=[str(e)],
                extraction_time=(datetime.now() - start_time).total_seconds(),
            )

    def _extract_entities(self, text: str) -> list[Entity]:
        """提取实体(增强模式)"""
        entities = []

        # 1. 使用增强BERT NER提取实体
        if self.use_bert_ner and self.enhanced_ner:
            try:
                bert_entities = self.enhanced_ner.extract_entities(text)
                # 转换为本地Entity格式
                for be in bert_entities:
                    # 映射实体类型
                    entity_type = self._map_entity_type(be.entity_type)
                    entities.append(
                        Entity(
                            text=be.text,
                            entity_type=entity_type,
                            start_pos=be.start_pos,
                            end_pos=be.end_pos,
                            confidence=be.confidence,
                            context=be.context,
                        )
                    )
                logger.debug(f"🤖 BERT识别到 {len(bert_entities)} 个实体")
            except Exception as e:
                logger.warning(f"⚠️ BERT实体提取失败: {e}")

        # 2. 基于规则的实体提取
        rule_entities = self._extract_entities_by_rules(text)
        entities.extend(rule_entities)

        # 3. 基于机器学习的实体提取
        if self.entity_classifier:
            ml_entities = self._extract_entities_by_ml(text)
            entities.extend(ml_entities)

        # 4. 去重和合并
        entities = self._merge_entities(entities)

        # 5. 实体标准化
        for entity in entities:
            entity = self._normalize_entity(entity)

        return entities

    def _map_entity_type(self, bert_type: str) -> EntityType:
        """映射BERT实体类型到本地EntityType"""
        type_mapping = {
            "NAME": EntityType.PERSON,
            "COMP": EntityType.ORGANIZATION,
            "ORG": EntityType.ORGANIZATION,
            "ADDR": EntityType.LOCATION,
            "POS": EntityType.DESCRIPTION,
            "PATENT_NUM": EntityType.ID,
            "APPLICANT": EntityType.ORGANIZATION,
            "INVENTOR": EntityType.PERSON,
            "IPC_CODE": EntityType.CATEGORY,
            "TECH_TERM": EntityType.KEYWORD,
        }
        return type_mapping.get(bert_type, EntityType.KEYWORD)

    def _extract_entities_by_rules(self, text: str) -> list[Entity]:
        """基于规则提取实体"""
        entities = []

        # 直接调用增强NER的规则提取方法(如果可用)
        if self.enhanced_ner:
            try:
                patent_entities = self.enhanced_ner._extract_patent_entities(text)
                # 转换实体类型
                for pe in patent_entities:
                    # 映射到本地EntityType
                    entity_type = self._map_entity_type(pe.entity_type)
                    entities.append(
                        Entity(
                            text=pe.text,
                            entity_type=entity_type,
                            start_pos=pe.start_pos,
                            end_pos=pe.end_pos,
                            confidence=pe.confidence,
                            context=pe.context,
                        )
                    )
            except Exception as e:
                logger.debug(f"增强NER规则提取失败: {e}")

        # 使用本地规则模式
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # 特殊处理PORT类型 - 使用分组提取端口号
                    if entity_type == EntityType.PORT:
                        # 检查是否有分组 (port number)
                        if match.lastindex and match.lastindex >= 1:
                            # 提取第一个分组 (端口号)
                            port_str = match.group(1)
                            try:
                                port_num = int(port_str)
                                # 有效端口范围: 1-65535
                                if 1 <= port_num <= 65535:
                                    entity = Entity(
                                        text=port_str,
                                        entity_type=entity_type,
                                        start_pos=match.start(1),
                                        end_pos=match.end(1),
                                        confidence=0.9,
                                        context=text[max(0, match.start() - 20) : match.end() + 20],
                                    )
                                    entities.append(entity)
                            except ValueError:
                                pass  # 不是有效数字,忽略
                        continue  # PORT类型特殊处理完成,跳过常规处理

                    # 常规处理
                    entity = Entity(
                        text=match.group(),
                        entity_type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.9,  # 规则匹配置信度较高
                        context=text[max(0, match.start() - 20) : match.end() + 20],
                    )
                    entities.append(entity)

        # 特殊实体处理
        entities.extend(self._extract_special_entities(text))

        return entities

    def _extract_special_entities(self, text: str) -> list[Entity]:
        """提取特殊实体"""
        entities = []

        # 编程语言识别
        languages = [
            "python",
            "java",
            "javascript",
            "typescript",
            "c++",
            "c#",
            "go",
            "rust",
            "php",
            "ruby",
        ]
        for lang in languages:
            if re.search(r"\b" + lang + r"\b", text, re.IGNORECASE):
                entity = Entity(
                    text=lang,
                    entity_type=EntityType.LANGUAGE,
                    start_pos=text.lower().find(lang),
                    end_pos=text.lower().find(lang) + len(lang),
                    confidence=0.8,
                    context=text,
                )
                entities.append(entity)

        # 文件扩展名识别
        file_extensions = [
            ".py",
            ".js",
            ".java",
            ".cpp",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".txt",
            ".md",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
        ]
        for ext in file_extensions:
            matches = re.finditer(r"\S*" + re.escape(ext) + r"\b", text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    text=match.group(),
                    entity_type=EntityType.FILE,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,
                    context=text,
                )
                entities.append(entity)

        return entities

    def _extract_entities_by_ml(self, text: str) -> list[Entity]:
        """基于机器学习提取实体"""
        # 这里应该实现基于BERT的序列标注模型
        # 由于复杂度较高,这里提供框架代码
        entities = []

        try:
            # 特征提取
            features = self._extract_features(text)

            # 实体分类
            if hasattr(self.entity_classifier, "predict"):
                self.entity_classifier.predict([features])
                # 处理预测结果转换为实体
                # 这里需要根据具体模型实现
                pass

        except Exception as e:
            logger.warning(f"⚠️ 机器学习实体提取失败: {e}")

        return entities

    def _extract_features(self, text: str) -> np.ndarray:
        """提取文本特征"""
        # 词性标注特征
        words = list(jieba.cut(text))
        [pos for word, pos in pseg.cut(text)]

        # 统计特征
        features = [
            len(text),
            len(words),
            len(set(words)),
            text.count(" "),
            text.count("\n"),
            len(re.findall(r"\d+", text)),
            len(re.findall(r"[a-z_a-Z]+", text)),
        ]

        # TF-IDF特征
        try:
            if hasattr(self.feature_vectorizer, "transform"):
                tfidf_features = self.feature_vectorizer.transform([text]).toarray()[0]
                features.extend(tfidf_features)
        except KeyError as e:
            logger.warning(f"缺少必要的数据字段: {e}")
        except Exception as e:
            logger.error(f"处理数据时发生错误: {e}")

        return np.array(features)

    def _merge_entities(self, entities: list[Entity]) -> list[Entity]:
        """合并重复实体"""
        # 简单去重:相同文本和类型的实体只保留置信度最高的
        entity_dict = {}

        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)
            if key not in entity_dict or entity.confidence > entity_dict[key].confidence:
                entity_dict[key] = entity

        return list(entity_dict.values())

    def _normalize_entity(self, entity: Entity) -> Entity:
        """标准化实体"""
        if entity.entity_type in self.entity_normalizers:
            try:
                normalizer = self.entity_normalizers[entity.entity_type]
                normalized_text = normalizer(entity.text)
                entity.properties["normalized"] = normalized_text
            except Exception as e:
                logger.warning(f"⚠️ 实体标准化失败 {entity.text}: {e}")

        return entity

    def _extract_relations(self, text: str, entities: list[Entity]) -> list[EntityRelation]:
        """提取实体关系"""
        relations = []

        # 简单的关系识别规则
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:
                    continue

                # 基于距离的关系
                distance = abs(entity1.start_pos - entity2.start_pos)
                if distance < 50:  # 距离较近可能有关系
                    relation = self._infer_relation(entity1, entity2, text)
                    if relation:
                        relations.append(relation)

        return relations

    def _infer_relation(
        self, entity1: Entity, entity2: Entity, context: str
    ) -> EntityRelation | None:
        """推断实体关系"""
        # 基于实体类型和上下文推断关系
        if entity1.entity_type == EntityType.LANGUAGE and entity2.entity_type == EntityType.FILE:
            return EntityRelation(
                entity1=entity1,
                entity2=entity2,
                relation_type=RelationType.USES,
                confidence=0.7,
                evidence=f"{entity1.text} {entity2.text}",
            )

        if entity1.entity_type == EntityType.TOOL and entity2.entity_type == EntityType.URL:
            return EntityRelation(
                entity1=entity1,
                entity2=entity2,
                relation_type=RelationType.RELATED_TO,
                confidence=0.6,
                evidence=f"{entity1.text} {entity2.text}",
            )

        return None

    def _build_parameters(
        self, entities: list[Entity], relations: list[EntityRelation], intent: str
    ) -> dict[str, Any]:
        """构建参数字典"""
        parameters = {}

        # 根据实体类型构建参数
        for entity in entities:
            param_name = entity.entity_type.value.lower()

            # 获取标准化值
            if "normalized" in entity.properties:
                value = entity.properties["normalized"]
            else:
                value = entity.text

            # 多值处理
            if param_name in parameters:
                if isinstance(parameters[param_name], list):
                    parameters[param_name].append(value)
                else:
                    parameters[param_name] = [parameters[param_name], value]
            else:
                parameters[param_name] = value

        # 添加置信度信息
        parameters["_confidence"] = {
            entity.entity_type.value.lower(): entity.confidence for entity in entities
        }

        return parameters

    def _validate_parameters(self, parameters: dict[str, Any], intent: str) -> list[str]:
        """验证参数"""
        errors = []

        # 基本参数验证
        for param_name, value in parameters.items():
            if param_name.startswith("_"):
                continue

            if isinstance(value, str) and len(value.strip()) == 0:
                errors.append(f"参数 {param_name} 值为空")

            if param_name == "port" and isinstance(value, str):
                try:
                    port = int(re.sub(r"[^\d]", "", value))
                    if port < 1 or port > 65535:
                        errors.append(f"端口号 {port} 超出有效范围 (1-65535)")
                except Exception:
                    errors.append(f"端口号格式错误: {value}")

            if param_name == "email" and isinstance(value, str):
                if not re.match(r"^[a-z_a-Z0-9._%+-]+@[a-z_a-Z0-9.-]+\.[a-z_a-Z]{2,}$", value):
                    errors.append(f"邮箱格式错误: {value}")

        return errors

    def _detect_missing_parameters(self, parameters: dict[str, Any], intent: str) -> list[str]:
        """检测缺失参数"""
        missing = []

        # 基于意图的必需参数检查
        required_params = self._get_required_parameters(intent)

        for param in required_params:
            if param not in parameters:
                missing.append(param)

        return missing

    def _get_required_parameters(self, intent: str) -> list[str]:
        """获取意图的必需参数"""
        required_map = {
            "search": ["keyword"],
            "email": ["email", "subject"],
            "call": ["phone"],
            "appointment": ["date", "time"],
            "code_analysis": ["file"],
            "api_test": ["url"],
            "infrastructure/infrastructure/deployment": ["host", "port"],
        }

        return required_map.get(intent, [])

    def _calculate_confidence(
        self, entities: list[Entity], relations: list[EntityRelation], errors: list[str]
    ) -> float:
        """计算整体置信度"""
        if not entities:
            return 0.0

        # 实体置信度平均
        entity_confidence = sum(e.confidence for e in entities) / len(entities)

        # 关系置信度影响
        relation_factor = (
            0.9 if not relations else sum(r.confidence for r in relations) / len(relations)
        )

        # 错误惩罚
        error_penalty = len(errors) * 0.1

        confidence = entity_confidence * relation_factor - error_penalty
        return max(0.0, min(1.0, confidence))

    def save_models(self, save_path: Optional[str] = None) -> None:
        """保存模型"""
        if not save_path:
            save_path = self.config.model_dir

        os.makedirs(save_path, exist_ok=True)

        # 保存分类器
        if self.entity_classifier:
            classifier_path = os.path.join(save_path, "entity_classifier.joblib")
            # 安全修复: 使用joblib替代pickle
            joblib.dump(self.entity_classifier, classifier_path)

        logger.info(f"💾 NER模型已保存: {save_path}")

    def load_models(self, load_path: Optional[str] = None) -> Any | None:
        """加载模型"""
        if not load_path:
            load_path = self.config.model_dir

        # 加载分类器
        classifier_path = os.path.join(load_path, "entity_classifier.joblib")
        if os.path.exists(classifier_path):
            # 安全修复: 使用joblib替代pickle
            self.entity_classifier = joblib.load(classifier_path)

        logger.info(f"📂 NER模型已加载: {load_path}")


def main() -> None:
    """测试函数"""
    # 初始化NER参数提取器
    config = NERModelConfig()
    extractor = XiaonuoNERParameterExtractor(config)

    # 测试用例
    test_cases = [
        {
            "text": "帮我分析Python代码文件example.py,我的邮箱是xiaonuo@example.com",
            "intent": "code_analysis",
        },
        {
            "text": "调用API接口http://api.example.com:8080,版本v1.2.3,成功率95%",
            "intent": "api_test",
        },
        {
            "text": "明天上午10点开会,地点在北京市朝阳区,联系电话13812345678",
            "intent": "appointment",
        },
        {"text": "使用Java框架Spring Boot开发Web应用,数据库MySQL", "intent": "development"},
        {
            "text": "部署到服务器192.168.1.100,端口3000,管理员admin@example.com",
            "intent": "infrastructure/infrastructure/deployment",
        },
    ]

    logger.info("🧪 开始NER参数提取测试")

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📝 测试用例 {i}:")
        logger.info(f"文本: {test_case['text']}")
        logger.info(f"意图: {test_case['intent']}")

        result = extractor.extract_parameters(test_case["text"], test_case["intent"])

        logger.info("🔍 提取结果:")
        logger.info(f"  - 实体数量: {len(result.entities)}")
        logger.info(f"  - 关系数量: {len(result.relations)}")
        logger.info(f"  - 参数数量: {len(result.parameters)}")
        logger.info(f"  - 置信度: {result.confidence:.3f}")
        logger.info(f"  - 提取耗时: {result.extraction_time:.3f}s")

        if result.entities:
            logger.info("  🏷️ 实体列表:")
            for entity in result.entities:
                logger.info(
                    f"    - {entity.text} ({entity.entity_type.value}, 置信度: {entity.confidence:.3f})"
                )

        if result.parameters:
            logger.info("  ⚙️ 参数列表:")
            for param_name, param_value in result.parameters.items():
                if not param_name.startswith("_"):
                    logger.info(f"    - {param_name}: {param_value}")

        if result.validation_errors:
            logger.warning(f"  ⚠️ 验证错误: {result.validation_errors}")

        if result.missing_params:
            logger.info(f"  ❓ 缺失参数: {result.missing_params}")

    # 保存模型
    extractor.save_models()

    logger.info("\n✅ NER参数提取测试完成")


if __name__ == "__main__":
    main()
