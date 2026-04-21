#!/usr/bin/env python3
from __future__ import annotations
"""
统一Agent记忆系统 - 工具函数
Unified Agent Memory System - Utility Functions

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

import asyncio
import functools
import logging
import os

# 添加项目路径
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent.parent))


# ==================== 日志配置 ====================
class RequestIdFilter(logging.Filter):
    """添加request_id字段的过滤器"""

    def filter(self, record) -> bool:
        # 如果record中没有request_id,使用"N/A"
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return True


# 创建logger (模块内部使用，不导出)
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

# 添加过滤器
_logger.addFilter(RequestIdFilter())

# 配置handler
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
_logger.addHandler(handler)


# ==================== 嵌入模型加载 ====================
# 支持多种嵌入模型,按优先级尝试加载
_embedding_model = None
_embedding_model_name = None


def _load_embedding_model() -> Any:
    """
    加载嵌入模型,按优先级尝试多种模型

    优先级:
    1. 本地BGE-M3模型 (平台已有) ✅
    2. 其他sentence-transformers模型
    3. OpenAI API (如果配置)
    4. fallback到MD5 (临时方案)

    平台已有模型:
    - BGE-M3本地模型 (1024维,多语言,支持 dense/sparse/colbert) ✅
    - paraphrase-multilingual-MiniLM-L12-v2 (384维,多语言)

    BGE-M3本地路径: http://127.0.0.1:8766/v1/embeddings

    Returns:
        模型和模型名称
    """
    global _embedding_model, _embedding_model_name

    if _embedding_model is not None:
        return _embedding_model, _embedding_model_name

    # 检查是否启用真实嵌入模型(通过环境变量控制)
    if os.environ.get("ENABLE_REAL_EMBEDDINGS", "").lower() != "true":
        _logger.info("嵌入模型加载已禁用(ENABLE_REAL_EMBEDDINGS!=true),使用MD5 fallback")
        _embedding_model = "md5"
        _embedding_model_name = "md5-fallback"
        return _embedding_model, _embedding_model_name

    # 尝试1: 使用本地BGE-M3模型 (平台已有)
    try:
        import torch
        from sentence_transformers import SentenceTransformer

        # 本地BGE-M3模型路径 - 从环境变量或默认路径读取
        project_root = Path(__file__).parent.parent.parent
        local_bge_m3_path = os.environ.get(
            "BGE_M3_MODEL_PATH",
            str(project_root / "models" / "converted" / "BAAI" / "bge-m3"),
        )

        if os.path.exists(local_bge_m3_path):
            _logger.info(f"✅ 发现本地BGE-M3模型: {local_bge_m3_path}")
            model = SentenceTransformer(local_bge_m3_path)
            _embedding_model = model
            _embedding_model_name = "BGE-M3 (本地)"

            # MPS加速 (Apple Silicon GPU)
            if torch.backends.mps.is_available():
                _logger.info("🚀 启用MPS加速 (Apple Silicon GPU)")
                # 注意: sentence-transformers模型不一定完全支持MPS
                # 如果遇到问题，会自动降级到CPU
                try:
                    model = model.to("mps")
                    _logger.info("✅ BGE-M3已加载到MPS设备")
                except Exception as e:
                    _logger.error(f"加载MPS设备失败: {e}", exc_info=True)
                    # 降级到CPU继续运行
                    _logger.info("降级到CPU模式")

            dim = model.get_sentence_embedding_dimension()
            _logger.info(f"✅ 成功加载本地BGE-M3模型, 向量维度: {dim}")
            return model, "BGE-M3 (本地)"

    except ImportError:
        _logger.debug("sentence-transformers 未安装,尝试其他方案...")
    except Exception as e:
        _logger.error(f"加载BGE-M3模型失败: {e}", exc_info=True)
        raise

    # 尝试2: 使用其他平台已有模型
    try:
        from sentence_transformers import SentenceTransformer

        model_names = [
            "paraphrase-multilingual-MiniLM-L12-v2",  # ✅ 平台已有,384维,多语言
            "BAAI/bge-small-zh-v1.5",  # 中文优化,512维
            "BAAI/bge-base-zh-v1.5",  # 中文优化,768维
        ]
        for model_name in model_names:
            try:
                _logger.info(f"尝试加载嵌入模型: {model_name}")
                model = SentenceTransformer(model_name)
                _embedding_model = model
                _embedding_model_name = model_name
                dim = model.get_sentence_embedding_dimension()
                _logger.info(f"✅ 成功加载嵌入模型: {model_name}, 向量维度: {dim}")
                return model, model_name
            except Exception as e:
                _logger.debug(f"加载 {model_name} 失败: {e}, 尝试下一个模型...")
                continue
    except ImportError:
        _logger.debug("sentence-transformers 未安装,尝试其他方案...")

    # 尝试3: 使用OpenAI API (如果配置了API密钥)
    if os.environ.get("OPENAI_API_KEY"):
        _logger.info("检测到OPENAI_API_KEY,将使用OpenAI嵌入API")
        _embedding_model = "openai"
        _embedding_model_name = "text-embedding-3-small"
        return _embedding_model, _embedding_model_name

    # fallback: 使用MD5临时方案
    _logger.warning(
        "⚠️ 未找到可用的嵌入模型,使用MD5临时方案。建议安装: pip install sentence-transformers"
    )
    _embedding_model = "md5"
    _embedding_model_name = "md5-fallback"
    return _embedding_model, _embedding_model_name


# 在导入时尝试加载模型
_load_embedding_model()


# ==================== 上下文管理器 ====================
@contextmanager
def request_context(request_id: str) -> Any:
    """设置请求ID上下文"""
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = getattr(record, "request_id", request_id)
        return record

    logging.setLogRecordFactory(record_factory)
    try:
        yield
    finally:
        logging.setLogRecordFactory(old_factory)


# ==================== 重试装饰器 ====================
def retry_with_backoff(
    max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0
) -> Any:
    """
    重试装饰器，使用指数退避策略

    Args:
        max_retries: 最大重试次数（默认3次）
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）

    Returns:
        装饰器函数
    """

    def decorator(func) -> None:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            request_id = kwargs.get("request_id", str(uuid.uuid4())[:8])

            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        _logger.info(
                            f"[{request_id}] 重试 {func.__name__} (第{attempt}次)"
                        )
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # 计算指数退避延迟
                        delay = min(base_delay * (2**attempt), max_delay)
                        _logger.warning(
                            f"[{request_id}] {func.__name__} 失败: {e}, {delay}秒后重试..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        _logger.error(
                            f"[{request_id}] {func.__name__} 达到最大重试次数: {e}"
                        )
                        raise

            # 所有重试都失败，抛出最后一个异常（理论上不应该到达这里）
            raise last_exception if last_exception else RuntimeError("重试失败且未捕获到异常")

        return wrapper

    return decorator
