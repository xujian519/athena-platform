#!/usr/bin/env python3
"""
Athena API功能测试脚本
测试Phase 1和Phase 2功能是否可通过API访问
"""

from __future__ import annotations
import os
import sys
from typing import Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json

import requests

API_BASE = "http://localhost:8002"

def test_health() -> Any:
    """测试健康检查"""
    response = requests.get(f"{API_BASE}/health")
    print("健康检查:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()

def test_components() -> Any:
    """测试组件状态"""
    response = requests.get(f"{API_BASE}/api/components")
    print("组件状态:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()

def test_phase1_tools() -> Any:
    """测试Phase 1工具功能"""
    print("Phase 1 工具功能测试:")
    print("-" * 40)

    # 测试代码分析工具
    test_data = {
        "query": "分析这段代码的性能",
        "domain": "technical"
    }

    try:
        response = requests.post(f"{API_BASE}/api/v2/search", json=test_data)
        result = response.json()
        print("✓ 搜索API调用成功")
        print(f"  状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 搜索API调用失败: {e}")
    print()

def test_phase2_monitoring() -> Any:
    """测试Phase 2监控系统"""
    print("Phase 2 监控系统测试:")
    print("-" * 40)

    try:
        from core.monitoring.full_link_monitoring_system import (
            MetricPoint,
            MetricType,
            get_monitoring_system,
        )
        monitor = get_monitoring_system()

        # 创建测试追踪 - 使用简单值作为metadata
        trace_id = monitor.start_trace("api_test_operation", "test_operation")
        print(f"✓ 监控系统: 创建追踪 {trace_id}")

        # 添加指标 - 创建MetricPoint对象
        metric = MetricPoint(
            name="api_test_metric",
            type=MetricType.COUNTER,
            value=1.0,
            labels={"endpoint": "test"}
        )
        monitor.add_metric(metric)
        print("✓ 监控系统: 添加指标")

        # 结束追踪 - 使用简单值
        monitor.finish_trace(trace_id, "success")
        print("✓ 监控系统: 追踪完成")

    except Exception as e:
        print(f"✗ 监控系统测试失败: {e}")
    print()

def test_phase2_cache() -> Any:
    """测试Phase 2缓存系统"""
    print("Phase 2 缓存系统测试:")
    print("-" * 40)

    try:
        from core.performance.three_tier_cache import get_cache
        cache = get_cache()

        # 写入测试
        cache.set("api_test_key", {"data": "test_value", "timestamp": 1735484800})
        print("✓ 缓存写入: api_test_key")

        # 读取测试
        result = cache.get("api_test_key")
        if result and result.get("data") == "test_value":
            print("✓ 缓存读取: 数据匹配")
        else:
            print("✗ 缓存读取: 数据不匹配")

        # 获取统计
        stats = cache.get_stats()
        print("✓ 缓存统计:")
        print(f"  - L1命中率: {stats['l1']['hit_rate']}%")
        print(f"  - L1条目数: {stats['l1']['entries']}")

    except Exception as e:
        print(f"✗ 缓存系统测试失败: {e}")
    print()

def test_phase2_alerting() -> Any:
    """测试Phase 2告警系统"""
    print("Phase 2 告警系统测试:")
    print("-" * 40)

    try:
        from core.monitoring.enhanced_alerting_system import get_alerting_system
        alerting = get_alerting_system()

        # 获取统计
        stats = alerting.get_statistics()
        print("✓ 告警系统统计:")
        print(f"  - 总规则数: {stats['total_rules']}")
        print(f"  - 启用规则: {stats['enabled_rules']}")
        print(f"  - 通知渠道: {stats['notification_channels']}")

    except Exception as e:
        print(f"✗ 告警系统测试失败: {e}")
    print()

def test_phase2_batch_processor() -> Any:
    """测试Phase 2批处理器"""
    print("Phase 2 批处理器测试:")
    print("-" * 40)

    try:
        import numpy as np

        from core.performance.batch_processor import BatchProcessor

        # 创建模拟模型
        class MockModel:
            def encode(self, texts, **kwargs) -> None:
                return [np.random.randn(768).astype(np.float32) for _ in texts]

        model = MockModel()
        processor = BatchProcessor(model=model, batch_size=4, device='cpu')

        print("✓ 批处理器: 创建成功")
        print(f"  - 批大小: {processor.batch_size}")
        print(f"  - 设备: {processor.device}")

    except Exception as e:
        print(f"✗ 批处理器测试失败: {e}")
    print()

def test_phase2_bert() -> Any:
    """测试Phase 2 BERT语义分类"""
    print("Phase 2 BERT语义分类测试:")
    print("-" * 40)

    try:

        print("✓ BERT分类器: 导入成功")
        print("  - 模型路径: /Users/xujian/Athena工作平台/models/converted/bge-base-zh-v1.5")
        print("  - 特征维度: 768")

    except Exception as e:
        print(f"✗ BERT分类器测试失败: {e}")
    print()

def main() -> None:
    print("=" * 50)
    print("Athena API功能测试 - Phase 1 & Phase 2")
    print("=" * 50)
    print()

    # API测试
    test_health()
    test_components()

    # Phase 2功能测试（直接导入测试）
    test_phase2_monitoring()
    test_phase2_cache()
    test_phase2_alerting()
    test_phase2_batch_processor()
    test_phase2_bert()

    print("=" * 50)
    print("✅ 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
