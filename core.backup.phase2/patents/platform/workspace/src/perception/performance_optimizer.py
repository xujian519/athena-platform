#!/usr/bin/env python3
"""
感知层性能优化器
Perception Layer Performance Optimizer

优化文档处理速度和系统性能
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import logging
import queue
import re
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """性能指标监控"""

    def __init__(self):
        self.metrics = {}
        self.timings = {}
        self.counts = {}
        self.errors = {}

    def record_timing(self, operation: str, duration: float):
        """记录操作耗时"""
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(duration)

        # 保持最近1000次记录
        if len(self.timings[operation]) > 1000:
            self.timings[operation] = self.timings[operation][-1000:]

    def record_count(self, operation: str, increment: int = 1):
        """记录操作计数"""
        self.counts[operation] = self.counts.get(operation, 0) + increment

    def record_error(self, operation: str, error: str):
        """记录错误"""
        if operation not in self.errors:
            self.errors[operation] = []
        self.errors[operation].append(error)

        # 保持最近100次错误
        if len(self.errors[operation]) > 100:
            self.errors[operation] = self.errors[operation][-100:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {}

        for operation, timings in self.timings.items():
            if timings:
                stats[operation] = {
                    'avg_time': sum(timings) / len(timings),
                    'min_time': min(timings),
                    'max_time': max(timings),
                    'total_calls': len(timings),
                    'calls_per_second': len(timings) / sum(timings) if sum(timings) > 0 else 0
                }

        return stats

# 全局性能监控器
performance_metrics = PerformanceMetrics()

def performance_monitor(operation_name: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_metrics.record_timing(operation_name, duration)
                performance_metrics.record_count(operation_name)
                return result
            except Exception as e:
                performance_metrics.record_error(operation_name, str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_metrics.record_timing(operation_name, duration)
                performance_metrics.record_count(operation_name)
                return result
            except Exception as e:
                performance_metrics.record_error(operation_name, str(e))
                raise

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class CacheManager:
    """缓存管理器"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）

        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self.cleanup_thread.start()

    def _cleanup_expired(self):
        """清理过期缓存"""
        while True:
            current_time = time.time()
            expired_keys = []

            for key, (_, timestamp) in self.cache.items():
                if current_time - timestamp > self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

            # 如果缓存过大，删除最久未使用的
            if len(self.cache) > self.max_size:
                sorted_items = sorted(
                    self.access_times.items(),
                    key=lambda x: x[1]
                )
                # 删除最旧的25%
                items_to_remove = int(len(sorted_items) * 0.25)
                for key, _ in sorted_items[:items_to_remove]:
                    if key in self.cache:
                        del self.cache[key]
                    del self.access_times[key]

            time.sleep(60)  # 每分钟清理一次

    def get(self, key: str) -> Any:
        """获取缓存"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            current_time = time.time()

            if current_time - timestamp < self.ttl:
                self.access_times[key] = current_time
                return value
            else:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

        return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        current_time = time.time()
        self.cache[key] = (value, current_time)
        self.access_times[key] = current_time

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()

class ParallelProcessor:
    """并行处理器"""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers

    async def process_parallel(self, tasks: List[Callable], batch_size: int = None) -> List[Any]:
        """并行处理任务"""
        if batch_size is None:
            batch_size = self.max_workers

        results = []

        # 分批处理
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]

            # 并行执行
            futures = []
            for task in batch:
                if asyncio.iscoroutinefunction(task):
                    future = asyncio.create_task(task())
                    futures.append(future)
                else:
                    future = asyncio.get_event_loop().run_in_executor(
                        self.executor, task
                    )
                    futures.append(future)

            # 等待完成
            batch_results = await asyncio.gather(*futures, return_exceptions=True)
            results.extend(batch_results)

        return results

    def shutdown(self):
        """关闭处理器"""
        self.executor.shutdown(wait=True)

class OptimizedTextProcessor:
    """优化的文本处理器"""

    def __init__(self):
        # 预编译正则表达式
        self.compiled_patterns = {
            'claim_pattern': re.compile(r'权利要求\s*(\d+)[:：]?\s*([^权利要求]+?)(?=权利要求\s*\d+|$)', re.DOTALL),
            'drawing_refs': re.compile(r'图\s*(\d+)'),
            'figure_refs': re.compile(r'Fig\.?\s*(\d+)', re.IGNORECASE),
            'tech_features': re.compile(r'([^，。；；]+?装置|[^，。；；]+?机构|[^，。；；]+?部件|[^，。；；]+?组件)', re.IGNORECASE),
            'technical_terms': re.compile(r'([A-Z]{2,}|[a-z]+[A-Z][a-z]+|[一-龯]{2,})'),
            'references': re.compile(r'(图\s*\d+|Fig\.?\s*\d+|附图\s*\d+|(\d+)[：:])', re.IGNORECASE)
        }

        # LRU缓存
        self.pattern_cache = lru_cache(maxsize=128)(self._extract_with_pattern)

    def _extract_with_pattern(self, text: str, pattern_name: str) -> List[str]:
        """使用预编译模式提取"""
        if pattern_name not in self.compiled_patterns:
            return []

        pattern = self.compiled_patterns[pattern_name]
        matches = pattern.findall(text)
        return matches

    def extract_claims(self, text: str) -> Dict[int, str]:
        """优化的权利要求提取"""
        start_time = time.time()

        try:
            claims = {}
            matches = self.pattern_cache(text, 'claim_pattern')

            for claim_num, claim_text in matches:
                claims[int(claim_num)] = claim_text.strip()

            performance_metrics.record_timing('extract_claims', time.time() - start_time)
            return claims

        except Exception as e:
            performance_metrics.record_error('extract_claims', str(e))
            return {}

    def extract_drawing_references(self, text: str) -> List[str]:
        """优化的图纸引用提取"""
        start_time = time.time()

        try:
            drawing_refs = self.pattern_cache(text, 'drawing_refs')
            figure_refs = self.pattern_cache(text, 'figure_refs')

            all_refs = drawing_refs + figure_refs
            unique_refs = list(set(all_refs))

            performance_metrics.record_timing('extract_drawing_references', time.time() - start_time)
            return unique_refs

        except Exception as e:
            performance_metrics.record_error('extract_drawing_references', str(e))
            return []

    def extract_technical_features(self, text: str) -> List[str]:
        """优化的技术特征提取"""
        start_time = time.time()

        try:
            features = self.pattern_cache(text, 'tech_features')

            # 清理和去重
            cleaned_features = []
            for feature in features:
                cleaned = feature.strip()
                if len(cleaned) > 2 and len(cleaned) < 100:
                    cleaned_features.append(cleaned)

            unique_features = list(set(cleaned_features))

            performance_metrics.record_timing('extract_technical_features', time.time() - start_time)
            return unique_features

        except Exception as e:
            performance_metrics.record_error('extract_technical_features', str(e))
            return []

class OptimizedDocumentProcessor:
    """优化的文档处理器"""

    def __init__(self):
        self.text_processor = OptimizedTextProcessor()
        self.cache_manager = CacheManager(max_size=500, ttl=1800)
        self.parallel_processor = ParallelProcessor(max_workers=4)

        # 文档处理队列
        self.processing_queue = queue.Queue()
        self.processing_thread = None

        logger.info('🚀 优化文档处理器初始化完成')

    @performance_monitor('process_document')
    async def process_document_optimized(self, file_path: str) -> Dict[str, Any]:
        """优化的文档处理"""
        # 检查缓存
        cache_key = f"document_{Path(file_path).stem}_{Path(file_path).stat().st_mtime}"
        cached_result = self.cache_manager.get(cache_key)

        if cached_result:
            performance_metrics.record_count('cache_hits')
            return cached_result

        performance_metrics.record_count('cache_misses')

        try:
            # 并行处理多个任务
            text_content = await self._extract_text_optimized(file_path)

            # 并行提取
            extraction_tasks = [
                lambda: self.text_processor.extract_claims(text_content),
                lambda: self.text_processor.extract_drawing_references(text_content),
                lambda: self.text_processor.extract_technical_features(text_content),
                lambda: self._extract_metadata(file_path)
            ]

            results = await self.parallel_processor.process_parallel(extraction_tasks)

            claims = results[0]
            drawing_refs = results[1]
            tech_features = results[2]
            metadata = results[3]

            # 构建结果
            processed_result = {
                'file_path': file_path,
                'claims': claims,
                'drawing_references': drawing_refs,
                'technical_features': tech_features,
                'metadata': metadata,
                'processing_time': time.time()
            }

            # 缓存结果
            self.cache_manager.set(cache_key, processed_result)

            return processed_result

        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            performance_metrics.record_error('process_document', str(e))
            return {'error': str(e), 'file_path': file_path}

    async def _extract_text_optimized(self, file_path: str) -> str:
        """优化的文本提取"""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text_parts = []

            # 批量处理页面
            pages = list(range(len(doc)))

            async def process_page_batch(page_batch):
                batch_text = []
                for page_num in page_batch:
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        batch_text.append(text)
                return "\n".join(batch_text)

            # 分批处理（每批5页）
            batch_size = 5
            all_text_parts = []

            for i in range(0, len(pages), batch_size):
                batch = pages[i:i + batch_size]
                batch_text = await process_page_batch(batch)
                all_text_parts.append(batch_text)

            doc.close()
            return "\n".join(all_text_parts)

        except Exception as e:
            logger.error(f"文本提取失败: {str(e)}")
            return ''

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文档元数据"""
        try:
            file_stat = Path(file_path).stat()

            metadata = {
                'file_size': file_stat.st_size,
                'last_modified': file_stat.st_mtime,
                'file_name': Path(file_path).name,
                'file_type': Path(file_path).suffix.lower()
            }

            return metadata

        except Exception as e:
            logger.error(f"元数据提取失败: {str(e)}")
            return {}

# 全局优化器实例
document_optimizer = OptimizedDocumentProcessor()

# 性能优化函数
def optimize_perception_engine():
    """优化感知引擎性能"""
    optimizations = {
        # 使用预编译正则表达式
        'precompile_patterns': True,

        # 启用LRU缓存
        'enable_lru_cache': True,

        # 并行处理
        'enable_parallel_processing': True,

        # 缓存结果
        'enable_result_caching': True,

        # 批量处理
        'enable_batch_processing': True
    }

    return optimizations

# 测试代码
if __name__ == '__main__':
    import asyncio

    async def test_performance_optimization():
        """测试性能优化"""
        logger.info('🚀 测试感知层性能优化...')

        # 测试优化器
        optimizations = optimize_perception_engine()
        logger.info(f"✅ 优化配置: {optimizations}")

        # 测试文本处理器
        text_processor = OptimizedTextProcessor()
        test_text = """
        权利要求1：一种混二元酸二甲酯生产中的甲醇精馏装置，其特征在于包括精馏塔。
        权利要求2：根据权利要求1所述的装置，其特征在于所述精馏塔顶部连接冷凝器。
        图1为装置结构图。
        """

        start_time = time.time()
        claims = text_processor.extract_claims(test_text)
        claims_time = time.time() - start_time

        start_time = time.time()
        refs = text_processor.extract_drawing_references(test_text)
        refs_time = time.time() - start_time

        start_time = time.time()
        features = text_processor.extract_technical_features(test_text)
        features_time = time.time() - start_time

        logger.info(f"✅ 文本处理测试:")
        logger.info(f"  权利要求提取: {len(claims)}个，耗时{claims_time:.4f}s")
        logger.info(f"  图纸引用提取: {len(refs)}个，耗时{refs_time:.4f}s")
        logger.info(f"  技术特征提取: {len(features)}个，耗时{features_time:.4f}s")

        # 测试性能指标
        stats = performance_metrics.get_stats()
        logger.info(f"\n📊 性能统计:")
        for operation, metrics in stats.items():
            print(f"  {operation}: 平均{metrics['avg_time']:.4f}s, "
                  f"调用{metrics['total_calls']}次, "
                  f"{metrics['calls_per_second']:.2f}次/s")

        return True

    # 运行测试
    result = asyncio.run(test_performance_optimization())
    logger.info(f"\n🎯 性能优化测试: {'成功' if result else '失败'}")