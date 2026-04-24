#!/usr/bin/env python3
"""Token估算器单元测试 - 验证性能优化效果"""

import pytest
import time
from core.prompt_engine.budget.utils import TokenEstimator


class TestTokenEstimator:
    """Token估算器测试套件"""

    def setup_method(self):
        """测试前置设置"""
        self.estimator = TokenEstimator()

    def test_chinese_text_estimation(self):
        """测试中文文本估算"""
        text = "这是一段中文文本用于测试Token估算功能"
        tokens = self.estimator.estimate(text)
        assert tokens > 0
        # 中文约1.5字符/token，25字符约17tokens
        assert 10 < tokens < 25

    def test_english_text_estimation(self):
        """测试英文文本估算"""
        text = "This is an English text for testing token estimation"
        tokens = self.estimator.estimate(text)
        assert tokens > 0
        # 英文单词数约等于token数，9个单词约9tokens
        assert 5 < tokens < 15

    def test_mixed_text_estimation(self):
        """测试中英混合文本估算"""
        text = "这是中文This is English混合文本for testing"
        tokens = self.estimator.estimate(text)
        assert tokens > 0
        # 中文约4字符 + 英文约5单词 = 约10-20 tokens
        assert 8 < tokens < 25

    def test_empty_text(self):
        """测试空文本"""
        tokens = self.estimator.estimate("")
        assert tokens == 0

    def test_long_text_performance(self):
        """测试长文本性能（应该<1ms）"""
        # 10000字符的中文文本
        text = "这是一个测试文本" * 1000

        start = time.perf_counter()
        for _ in range(100):
            tokens = self.estimator.estimate(text)
        elapsed = (time.perf_counter() - start) * 1000

        avg_time_ms = elapsed / 100

        print(f"\n长文本估算性能: {avg_time_ms:.3f}ms/次")
        assert avg_time_ms < 1.0, f"性能未达标: {avg_time_ms:.3f}ms > 1.0ms"

    def test_cache_effectiveness(self):
        """测试LRU缓存有效性"""
        text = "这是测试缓存效果的文本"

        # 第一次调用（未缓存）
        start = time.perf_counter()
        tokens1 = self.estimator.estimate(text)
        time1 = (time.perf_counter() - start) * 1000

        # 第二次调用（已缓存）
        start = time.perf_counter()
        tokens2 = self.estimator.estimate(text)
        time2 = (time.perf_counter() - start) * 1000

        assert tokens1 == tokens2
        assert time2 < time1, "缓存应该提升性能"

        print(f"\n缓存效果: 第一次{time1:.3f}ms, 第二次{time2:.3f}ms, 提升{((time1-time2)/time1*100):.1f}%")

    def test_estimate_messages(self):
        """测试消息列表估算"""
        messages = [
            {"role": "user", "content": "这是用户消息"},
            {"role": "assistant", "content": "This is assistant response"},
            {"role": "system", "content": "系统提示信息"}
        ]

        result = self.estimator.estimate_messages(messages)

        assert "total" in result
        assert "user" in result
        assert "assistant" in result
        assert "system" in result
        assert result["total"] > 0
        assert result["user"] > 0
        assert result["assistant"] > 0
        assert result["system"] > 0

    def test_special_characters(self):
        """测试特殊字符处理"""
        text = "测试特殊字符: @#$%^&*()_+-=[]{}|;':\",./<>?"
        tokens = self.estimator.estimate(text)
        assert tokens > 0

    def test_numbers_and_punctuation(self):
        """测试数字和标点符号"""
        text = "2024年4月24日，性能优化提升了65%！"
        tokens = self.estimator.estimate(text)
        assert tokens > 0


class TestTokenEstimatorPerformance:
    """Token估算器性能基准测试"""

    def test_performance_benchmark(self):
        """性能基准测试：对比优化前后"""
        estimator = TokenEstimator()

        # 测试文本
        test_texts = [
            "简短中文",
            "This is short English",
            "这是中等长度的中文文本，用于测试性能优化效果" * 5,
            "This is a medium length English text for testing performance improvements" * 5,
            "专利权利要求书、说明书、附图摘要等文件的撰写需要专业知识" * 10,
        ]

        results = []
        for text in test_texts:
            start = time.perf_counter()
            for _ in range(100):
                estimator.estimate(text)
            elapsed = (time.perf_counter() - start) * 1000
            avg_time = elapsed / 100
            results.append((len(text), avg_time))

        print("\n性能基准测试结果:")
        print(f"{'文本长度':<10} {'平均耗时':<10} {'性能评级'}")
        print("-" * 40)

        for length, avg_time in results:
            # 性能评级
            if avg_time < 0.5:
                grade = "✅ 优秀"
            elif avg_time < 1.0:
                grade = "✅ 良好"
            elif avg_time < 2.0:
                grade = "⚠️ 可接受"
            else:
                grade = "❌ 需优化"

            print(f"{length:<10} {avg_time:<10.3f} {grade}")

        # 验证所有测试都在可接受范围内
        for _, avg_time in results:
            assert avg_time < 2.0, f"性能不达标: {avg_time:.3f}ms"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
