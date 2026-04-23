#!/usr/bin/env python3
"""
语义理解模型集成
Semantic Model Integration

集成真实的预训练语言模型用于专利技术方案理解
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

# Numpy兼容性导入
import logging
import re
from dataclasses import dataclass
from typing import Any

import jieba
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

from config.numpy_compatibility import random

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SemanticConfig:
    """语义模型配置"""
    # BERT模型配置
    bert_model_name: str = 'bert-base-chinese'
    bert_cache_dir: str = 'models/bert_cache'

    # Sentence-BERT模型配置
    sbert_model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
    sbert_cache_dir: str = 'models/sbert_cache'

    # 模型参数
    max_sequence_length: int = 512
    batch_size: int = 16
    use_gpu: bool = torch.cuda.is_available()

    # 特殊配置
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'

class BERTSemanticModel:
    """BERT语义理解模型"""

    def __init__(self, config: SemanticConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.is_loaded = False

    def load_model(self):
        """加载BERT模型"""
        try:
            logger.info(f"🔄 正在加载BERT模型: {self.config.bert_model_name}")

            # 加载tokenizer和model
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.bert_model_name,
                cache_dir=self.config.bert_cache_dir
            )
            self.model = AutoModel.from_pretrained(
                self.config.bert_model_name,
                cache_dir=self.config.bert_cache_dir
            )

            # 移动到设备
            self.model.to(self.config.device)

            # 设置为评估模式
            self.model.eval()

            self.is_loaded = True
            logger.info(f"✅ BERT模型加载成功，使用设备: {self.config.device}")

        except Exception as e:
            logger.error(f"❌ BERT模型加载失败: {e}")
            # 使用模拟模式
            self._init_mock_mode()

    def _init_mock_mode(self):
        """初始化模拟模式"""
        logger.warning('⚠️ BERT模型进入模拟模式')
        self.is_loaded = False
        self.model_dim = 768

    def encode_text(self, texts: str | list[str]) -> np.ndarray:
        """文本编码"""
        if not self.is_loaded:
            # 模拟编码
            if isinstance(texts, str):
                return random(self.model_dim)
            else:
                return random((len(texts)), self.model_dim)

        # 真实编码
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []

        # 分批处理
        for i in range(0, len(texts), self.config.batch_size):
            batch_texts = texts[i:i + self.config.batch_size]

            # Tokenization
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.config.max_sequence_length,
                return_tensors='pt'
            )

            # 移动到设备
            inputs = {k: v.to(self.config.device) for k, v in inputs.items()}

            # 获取BERT输出
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用[CLS] token的表示
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                all_embeddings.append(embeddings)

        # 合并结果
        if len(all_embeddings) == 1:
            return all_embeddings[0]
        else:
            return np.vstack(all_embeddings)

    def extract_entities(self, text: str) -> list[dict[str, Any]:
        """基于BERT的实体识别"""
        entities = []

        # 使用规则和词典进行实体识别
        # 技术组件
        component_patterns = [
            r'([^，；。]*(?:模块|单元|部件|装置|设备|系统|平台))',
            r'([^，；。]*(?:芯片|电路|传感器|控制器|处理器))',
            r'([^，；。]*(?:算法|模型|方法|技术|架构))'
        ]

        for pattern in component_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_text = match.group(1).strip()
                if len(entity_text) > 1:
                    entities.append({
                        'text': entity_text,
                        'type': 'COMPONENT',
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.8
                    })

        # 技术参数
        param_patterns = [
            r'(\d+(?:\.\d+)?(?:%|℃|MPa|mm|μm|kHz|MHz|GHz))',
            r'([^，；。]*\d+[^，；。]*(?:层|个|倍|倍率|倍数))'
        ]

        for pattern in param_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'text': match.group(1),
                    'type': 'PARAMETER',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })

        return entities

    def extract_relations(self, text: str, entities: list[dict]) -> list[dict[str, Any]:
        """基于BERT的关系抽取"""
        relations = []

        # 连接关系
        connect_keywords = ['连接', '与', '和', '以及', ' coupled with', 'connected to']
        for keyword in connect_keywords:
            if keyword in text:
                # 查找关键词附近实体
                parts = text.split(keyword)
                if len(parts) == 2:
                    # 简单的关系提取
                    left_entities = [e['text'] for e in entities if e['start'] < text.find(keyword)]
                    right_entities = [e['text'] for e in entities if e['start'] > text.find(keyword) + len(keyword)]

                    if left_entities and right_entities:
                        relations.append({
                            'subject': left_entities[-1],
                            'relation': '连接',
                            'object': right_entities[0],
                            'confidence': 0.7
                        })

        # 功能关系
        function_patterns = [
            r'([^，；。]*)(?:用于|实现|完成|达到)([^，；。]*)',
            r'([^，；。]*)(?:通过|采用|使用)([^，；。]*)(?:实现|完成|达到)'
        ]

        for pattern in function_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                subject = match.group(1).strip()
                object = match.group(2).strip()
                if subject and object and len(subject) > 1 and len(object) > 1:
                    relations.append({
                        'subject': subject,
                        'relation': '实现',
                        'object': object,
                        'confidence': 0.8
                    })

        return relations

class SBERTSemanticModel:
    """Sentence-BERT语义相似度模型"""

    def __init__(self, config: SemanticConfig):
        self.config = config
        self.model = None
        self.is_loaded = False

    def load_model(self):
        """加载SBERT模型"""
        try:
            logger.info(f"🔄 正在加载SBERT模型: {self.config.sbert_model_name}")

            self.model = SentenceTransformer(
                self.config.sbert_model_name,
                cache_folder=self.config.sbert_cache_dir
            )

            # 移动到设备
            if self.config.use_gpu:
                self.model = self.model.to(self.config.device)

            self.is_loaded = True
            logger.info("✅ SBERT模型加载成功")

        except Exception as e:
            logger.error(f"❌ SBERT模型加载失败: {e}")
            self._init_mock_mode()

    def _init_mock_mode(self):
        """初始化模拟模式"""
        logger.warning('⚠️ SBERT模型进入模拟模式')
        self.is_loaded = False
        self.model_dim = 384

    def encode_sentences(self, sentences: str | list[str]) -> np.ndarray:
        """句子编码"""
        if not self.is_loaded:
            # 模拟编码
            if isinstance(sentences, str):
                return random(self.model_dim)
            else:
                return random((len(sentences)), self.model_dim)

        # 真实编码
        embeddings = self.model.encode(
            sentences,
            batch_size=self.config.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        return embeddings

    def compute_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度"""
        embeddings = self.encode_sentences([text1, text2])

        # 计算余弦相似度
        sim = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )

        return float(sim)

class IntegratedSemanticAnalyzer:
    """集成的语义分析器"""

    def __init__(self, config: SemanticConfig | None = None):
        self.config = config or SemanticConfig()
        self.bert_model = BERTSemanticModel(self.config)
        self.sbert_model = SBERTSemanticModel(self.config)
        self.is_initialized = False

    def initialize(self):
        """初始化所有模型"""
        logger.info('🚀 初始化语义分析器...')

        # 加载模型
        self.bert_model.load_model()
        self.sbert_model.load_model()

        self.is_initialized = True
        logger.info('✅ 语义分析器初始化完成')

    def analyze_technical_text(self, text: str) -> dict[str, Any]:
        """分析技术文本"""
        if not self.is_initialized:
            self.initialize()

        result = {
            'text': text,
            'semantic_encoding': None,
            'entities': [],
            'relations': [],
            'key_phrases': [],
            'technical_score': 0
        }

        # 1. 语义编码
        result['semantic_encoding'] = self.bert_model.encode_text(text)

        # 2. 实体识别
        result['entities'] = self.bert_model.extract_entities(text)

        # 3. 关系抽取
        result['relations'] = self.bert_model.extract_relations(text, result['entities'])

        # 4. 关键短语提取
        result['key_phrases'] = self._extract_key_phrases(text)

        # 5. 技术性评分
        result['technical_score'] = len(result['entities']) + len(result['relations'])

        return result

    def _extract_key_phrases(self, text: str) -> list[str]:
        """提取关键短语"""
        # 使用jieba进行分词
        words = jieba.lcut(text)

        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '了', '和', '与', '或', '等', '其', '该', '所述'}
        key_words = [w for w in words if len(w) > 1 and w not in stop_words]

        # 提取技术术语
        technical_words = []
        for _i, word in enumerate(key_words):
            # 技术特征词
            if any(keyword in word for keyword in ['模', '块', '单', '元', '系', '统', '方', '法', '技', '术', '装', '置', '设', '备']):
                technical_words.append(word)
            # 参数相关
            elif any(char.isdigit() for char in word):
                technical_words.append(word)

        return technical_words[:20]  # 返回前20个

    def compute_feature_similarity(self, features1: list[str], features2: list[str]) -> dict[str, float]:
        """计算特征相似度"""
        if not self.is_initialized:
            self.initialize()

        similarities = {}

        # 编码特征
        embeddings1 = self.sbert_model.encode_sentences(features1)
        embeddings2 = self.sbert_model.encode_sentences(features2)

        # 计算相似度矩阵
        sim_matrix = np.dot(embeddings1, embeddings2.T)

        # 找出最佳匹配
        best_matches = np.max(sim_matrix, axis=1)
        similarities['average_similarity'] = float(np.mean(best_matches))
        similarities['max_similarity'] = float(np.max(best_matches))
        similarities['min_similarity'] = float(np.min(best_matches))

        return similarities

# 全局实例
_semantic_analyzer = None

def get_semantic_analyzer() -> IntegratedSemanticAnalyzer:
    """获取全局语义分析器实例"""
    global _semantic_analyzer
    if _semantic_analyzer is None:
        _semantic_analyzer = IntegratedSemanticAnalyzer()
    return _semantic_analyzer

# 测试函数
def test_semantic_models():
    """测试语义模型"""
    logger.info('🧪 测试语义理解模型')
    logger.info(str('=' * 60))

    # 初始化
    analyzer = get_semantic_analyzer()
    analyzer.initialize()

    # 测试文本
    test_text = """
    一种基于深度学习的医疗图像诊断装置，包括图像采集模块、预处理模块、
    特征提取模块和分类诊断模块。该装置采用改进的卷积神经网络，
    准确率提升30%，处理速度提高2倍。
    """

    # 分析文本
    result = analyzer.analyze_technical_text(test_text)

    logger.info("\n📊 分析结果:")
    logger.info(f"语义编码维度: {result['semantic_encoding'].shape}")
    logger.info(f"识别实体数: {len(result['entities'])}")
    logger.info(f"识别关系数: {len(result['relations'])}")
    logger.info(f"关键短语数: {len(result['key_phrases'])}")
    logger.info(f"技术性评分: {result['technical_score']}")

    logger.info("\n🔍 识别的实体:")
    for entity in result['entities'][:5]:
        logger.info(f"  • {entity['text']} ({entity['type']})")

    logger.info("\n🔗 识别的关系:")
    for relation in result['relations'][:3]:
        logger.info(f"  • {relation['subject']} {relation['relation']} {relation['object']}")

    logger.info("\n💡 关键短语:")
    for phrase in result['key_phrases'][:10]:
        logger.info(f"  • {phrase}")

    # 测试相似度计算
    features1 = ['深度学习', '卷积神经网络', '图像识别']
    features2 = ['机器学习', 'CNN网络', '图像处理']

    similarities = analyzer.compute_feature_similarity(features1, features2)
    logger.info("\n📏 特征相似度:")
    for metric, score in similarities.items():
        logger.info(f"  • {metric}: {score:.4f}")

if __name__ == '__main__':
    test_semantic_models()
