#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化服务
Embedding Service

使用BGE模型对审查指南进行向量化
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# 配置日志
logger = logging.getLogger(__name__)

class PatentGuidelineEmbedder:
    """专利审查指南向量化器"""

    def __init__(self, model_name='bge-large-zh-v1.5'):
        """初始化向量化器

        Args:
            model_name: 模型名称或路径
        """
        # 使用本地模型路径
        self.model_name = f'/Users/xujian/Athena工作平台/models/{model_name}'
        self.model = None
        self.device = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
        self.vector_size = 1024  # BGE-Large-ZH-v1.5的维度

        # 加载模型
        self._load_model()

    def _load_model(self):
        """加载模型"""
        try:
            # 直接使用HuggingFace模型
            logger.info(f"加载模型: {self.model_name}")

            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder='/Users/xujian/Athena工作平台/models'
            )
            logger.info(f"模型加载成功，设备: {self.device}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """批量编码文本

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            向量矩阵
        """
        if not texts:
            return array([])

        logger.info(f"编码 {len(texts)} 个文本，批次大小: {batch_size}")

        # 批量编码
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch_texts,
                normalize_embeddings=True,  # 归一化向量
                show_progress_bar=True
            )
            embeddings.append(batch_embeddings)

        # 合并批次结果
        all_embeddings = np.vstack(embeddings) if embeddings else array([])

        logger.info(f"编码完成，向量维度: {all_embeddings.shape}")
        return all_embeddings

    def enhance_text_with_metadata(self, text: str, metadata: Dict[str, Any]) -> str:
        """使用元数据增强文本

        Args:
            text: 原始文本
            metadata: 元数据

        Returns:
            增强后的文本
        """
        enhanced_parts = []

        # 添加层级路径
        if 'hierarchy_path' in metadata:
            enhanced_parts.append(f"文档层级: {' > '.join(metadata['hierarchy_path'])}")

        # 添加章节标题
        if 'section_title' in metadata:
            enhanced_parts.append(f"章节标题: {metadata['section_title']}")

        # 添加章节编号
        if 'section_number' in metadata:
            enhanced_parts.append(f"章节编号: {metadata['section_number']}")

        # 添加关键词
        if 'keywords' in metadata:
            keywords = ', '.join(metadata['keywords'])
            enhanced_parts.append(f"关键词: {keywords}")

        # 添加相关概念
        if 'concepts' in metadata:
            concepts = ', '.join(metadata['concepts'])
            enhanced_parts.append(f"相关概念: {concepts}")

        # 添加原始内容
        enhanced_parts.append(f"内容: {text}")

        return '\n'.join(enhanced_parts)

    def embed_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对章节进行向量化

        Args:
            sections: 章节列表

        Returns:
            带向量的章节列表
        """
        logger.info(f"开始向量化 {len(sections)} 个章节")

        # 准备文本
        texts = []
        enhanced_texts = []

        for section in sections:
            # 创建元数据
            metadata = {
                'section_id': section.get('id', ''),
                'section_number': section.get('number', ''),
                'section_title': section.get('title', ''),
                'level': section.get('level', 0),
                'type': section.get('type', ''),
                'hierarchy_path': section.get('hierarchy_path', [])
            }

            # 提取关键词和概念
            content = section.get('content', '')
            metadata['keywords'] = self._extract_keywords(content)
            metadata['concepts'] = self._extract_concepts(content)

            # 增强文本
            enhanced_text = self.enhance_text_with_metadata(content, metadata)
            enhanced_texts.append(enhanced_text)

            # 保留原始文本用于显示
            texts.append(content)

        # 编码增强文本
        embeddings = self.encode_texts(enhanced_texts)

        # 组合结果
        results = []
        for i, section in enumerate(sections):
            result = {
                'section_id': section.get('id', ''),
                'text': section.get('content', ''),
                'enhanced_text': enhanced_texts[i],
                'vector': embeddings[i].tolist(),
                'metadata': {
                    'section_number': section.get('number', ''),
                    'section_title': section.get('title', ''),
                    'level': section.get('level', 0),
                    'type': section.get('type', ''),
                    'parent_id': section.get('parent_id'),
                    'hierarchy_path': section.get('hierarchy_path', []),
                    'keywords': self._extract_keywords(section.get('content', '')),
                    'concepts': self._extract_concepts(section.get('content', '')),
                    'start_page': section.get('start_page'),
                    'end_page': section.get('end_page')
                }
            }
            results.append(result)

        logger.info(f"向量化完成，生成了 {len(results)} 个向量")
        return results

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        if not text:
            return []

        # 专利领域关键词词典
        patent_keywords = {
            # 基本概念
            '新颖性', '创造性', '实用性', '优先权', '单一性', '公开不充分',
            '不支持', '驳回', '授权', '无效', '撤销',
            # 审查类型
            '实质审查', '初步审查', '复审', '无效宣告', '行政复议',
            # 专利类型
            '发明专利', '实用新型', '外观设计', 'PCT申请', '国际申请',
            # 法律依据
            '专利法', '专利法实施细则', '审查指南',
            # 技术领域
            '机械', '电子', '通信', '计算机', '医药', '化学', '生物',
            # 其他
            '申请日', '公开日', '授权公告日', '申请号', '专利号'
        }

        # 简单的关键词提取
        words = text.replace('\n', ' ').split(' ')
        found_keywords = []

        for word in words:
            word = word.strip('，。；：！""''')
            if word in patent_keywords:
                found_keywords.append(word)

        # 去重
        return list(set(found_keywords))

    def _extract_concepts(self, text: str) -> List[str]:
        """提取概念

        Args:
            text: 输入文本

        Returns:
            概念列表
        """
        # 这里可以使用更复杂的NLP方法
        # 目前使用简单的规则

        concepts = []
        text_lower = text.lower()

        # 寻找"XX的概念"、"XX的定义"等模式
        concepts_pattern = r'([^，。；：！''''\n]+)(的概念|的定义)'
        matches = re.findall(concepts_pattern, text_lower)
        for match in matches:
            concept = match[0].strip()
            if len(concept) > 1:
                concepts.append(concept)

        # 寻找"是指"、"指的是"等定义
        definition_pattern = r'([^，。；：！''''\n]+)(是指|指的是|指的是：|定义为|定义为：)'
        matches = re.findall(definition_pattern, text_lower)
        for match in matches:
            concept = match[0].strip()
            if len(concept) > 1 and concept not in concepts:
                concepts.append(concept)

        return concepts

    def save_embeddings(self, embeddings: List[Dict[str, Any]], output_path: str):
        """保存向量

        Args:
            embeddings: 向量列表
            output_path: 输出路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 准备保存数据
        save_data = {
            'model_name': self.model_name,
            'vector_size': self.vector_size,
            'device': self.device,
            'total_embeddings': len(embeddings),
            'embeddings': embeddings
        }

        # 保存为JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        logger.info(f"向量已保存到: {output_path}")

    def load_embeddings(self, input_path: str) -> List[Dict[str, Any]]:
        """加载向量

        Args:
            input_path: 输入路径

        Returns:
            向量列表
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"从 {input_path} 加载了 {data['total_embeddings']} 个向量")
        return data['embeddings']

# 测试函数
def test_embedder():
    """测试向量化器"""
    logger.info('=== 测试专利审查指南向量化器 ===')

    # 创建向量化器
    embedder = PatentGuidelineEmbedder()

    # 创建测试数据
    test_sections = [
        {
            'id': 'P1-C1-S1.1',
            'number': '1.1',
            'title': '新颖性',
            'level': 3,
            'type': 'section',
            'content': '新颖性，是指该发明或者实用新型不属于现有技术；也没有任何单位或者个人就同样的发明或者实用新型在申请日以前向国务院专利行政部门提出过申请，并记载在申请日以后公布的专利申请文件或者公告的专利文件中。',
            'hierarchy_path': ['第一部分', '第一章', '1.1']
        },
        {
            'id': 'P1-C1-S1.2',
            'number': '1.2',
            'title': '创造性',
            'level': 3,
            'type': 'section',
            'content': '创造性，是指与现有技术相比，该发明具有突出的实质性特点和显著的进步。',
            'hierarchy_path': ['第一部分', '第一章', '1.2']
        }
    ]

    logger.info(f"\n向量化 {len(test_sections)} 个测试章节...")

    # 向量化
    embedded_sections = embedder.embed_sections(test_sections)

    # 显示结果
    for section in embedded_sections:
        logger.info(f"\n章节ID: {section['metadata']['section_number']}")
        logger.info(f"标题: {section['metadata']['section_title']}")
        logger.info(f"向量维度: {len(section['vector'])}")
        logger.info(f"关键词: {section['metadata']['keywords']}")
        logger.info(f"概念: {section['metadata']['concepts']}")

        # 显示部分向量值
        vector_preview = section['vector'][:5]
        logger.info(f"向量预览: {vector_preview}")

    # 保存结果
    embedder.save_embeddings(
        embedded_sections,
        '/Users/xujian/Athena工作平台/patent_guideline_system/data/embeddings/test_embeddings.json'
    )

    logger.info("\n✅ 向量化测试完成！")

if __name__ == '__main__':
    test_embedder()