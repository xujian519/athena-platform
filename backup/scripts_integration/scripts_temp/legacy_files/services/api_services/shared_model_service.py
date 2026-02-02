#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享模型服务
Shared Model Service

提供统一的模型加载和管理服务，避免重复加载

作者: Athena (小娜)
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SharedModelService:
    """共享模型服务"""

    def __init__(self):
        self.models = {}
        self.model_configs = {
            'bert-base-chinese': {
                'cache_dir': 'models/pretrained/bert_base_chinese',
                'type': 'bert'
            },
            'paraphrase-multilingual-MiniLM-L12-v2': {
                'cache_dir': 'models/sentence_transformers',
                'type': 'sentence_transformer'
            }
        }
        self.load_times = {}
        self._loaded = False

    async def initialize(self):
        """初始化共享服务"""
        if self._loaded:
            return

        logger.info('🚀 初始化共享模型服务...')

        try:
            # 预加载常用模型
            await self._preload_models()
            self._loaded = True
            logger.info('✅ 共享模型服务初始化完成')

        except Exception as e:
            logger.error(f"❌ 共享模型服务初始化失败: {e}")
            raise

    async def _preload_models(self):
        """预加载模型"""
        for model_name, config in self.model_configs.items():
            try:
                start_time = time.time()

                if config['type'] == 'bert':
                    await self._load_bert_model(model_name, config['cache_dir'])
                elif config['type'] == 'sentence_transformer':
                    await self._load_sentence_model(model_name, config['cache_dir'])

                load_time = time.time() - start_time
                self.load_times[model_name] = load_time

                logger.info(f"✅ {model_name} 加载完成，耗时: {load_time:.2f}秒")

            except Exception as e:
                logger.error(f"❌ 模型 {model_name} 加载失败: {e}")

    async def _load_bert_model(self, model_name: str, cache_dir: str):
        """加载BERT模型"""
        cache_path = self.base_path / cache_dir

        # 确保缓存目录存在
        cache_path.mkdir(parents=True, exist_ok=True)

        # 检查是否已缓存
        model_file = cache_path / 'pytorch_model.bin'
        tokenizer_file = cache_path / 'tokenizer.json'

        if model_file.exists() and tokenizer_file.exists():
            logger.info(f"💾 从缓存加载 {model_name}")
            self.models[model_name] = {
                'tokenizer': AutoTokenizer.from_pretrained(cache_dir),
                'model': AutoModel.from_pretrained(cache_dir)
            }
        else:
            logger.info(f"📥 首次加载 {model_name}")
            self.models[model_name] = {
                'tokenizer': AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir),
                'model': AutoModel.from_pretrained(model_name, cache_dir=cache_dir)
            }

    async def _load_sentence_model(self, model_name: str, cache_dir: str):
        """加载句子向量模型"""
        cache_path = self.base_path / cache_dir
        cache_path.mkdir(parents=True, exist_ok=True)

        try:
            # 尝试从本地缓存加载
            local_model_path = cache_path / model_name.replace('/', '_')
            if local_model_path.exists():
                self.models[model_name] = SentenceTransformer(str(local_model_path))
                logger.info(f"💾 从本地缓存加载 {model_name}")
            else:
                # 首次加载
                self.models[model_name] = SentenceTransformer(model_name)
                logger.info(f"📥 首次加载 {model_name}")

        except Exception as e:
            logger.warning(f"⚠️ 句子向量模型 {model_name} 加载失败: {e}")
            raise

    def get_model(self, model_name: str):
        """获取模型"""
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未加载")
        return self.models[model_name]

    def get_load_stats(self) -> Dict[str, Any]:
        """获取加载统计"""
        return {
            'loaded_models': list(self.models.keys()),
            'load_times': self.load_times,
            'total_load_time': sum(self.load_times.values()),
            'service_loaded': self._loaded
        }

async def main():
    """主函数"""
    service = SharedModelService()
    await service.initialize()

    # 保持服务运行
    logger.info('🏃 共享模型服务已启动，按 Ctrl+C 停止...')

    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        logger.info('🛑 停止共享模型服务')
    finally:
        logger.info('👋 共享模型服务已停止')

if __name__ == '__main__':
    asyncio.run(main())
