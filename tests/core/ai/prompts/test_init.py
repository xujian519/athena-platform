#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.ai.prompts import evaluate_prompt_file
from core.ai.prompts.quality_evaluator import QualityMetric, QualityReport


class TestEvaluatePromptFile:
    """evaluate_prompt_file 递归 bug 修复测试。"""

    def test_evaluate_prompt_file_no_longer_recursive(self):
        """调用 evaluate_prompt_file 不应导致递归溢出。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Prompt\nThis is a test.")
            tmp_path = f.name

        try:
            # Mock evaluate_prompt 避免依赖完整的评估器
            with patch(
                "core.ai.prompts.evaluate_prompt",
                return_value=QualityReport(
                    overall_score=85.0,
                    clarity=QualityMetric(name="clarity", score=0.9),
                    completeness=QualityMetric(name="completeness", score=0.8),
                    consistency=QualityMetric(name="consistency", score=0.85),
                    token_efficiency=QualityMetric(name="token_efficiency", score=0.8),
                    actionability=QualityMetric(name="actionability", score=0.8),
                    recommendations=[],
                ),
            ) as mock_eval:
                result = evaluate_prompt_file(tmp_path)
                assert result.overall_score == 85.0
                mock_eval.assert_called_once()
                # 验证传入的是文件内容而非 Path 对象
                call_arg = mock_eval.call_args[0][0]
                assert isinstance(call_arg, str)
                assert "# Test Prompt" in call_arg
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_evaluate_prompt_file_nonexistent(self):
        """文件不存在时应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            evaluate_prompt_file("/nonexistent/path/test.md")

    def test_evaluate_prompt_file_reads_utf8(self):
        """应正确读取 UTF-8 编码文件。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# 测试提示词\n包含中文内容。\n")
            tmp_path = f.name

        try:
            with patch(
                "core.ai.prompts.evaluate_prompt",
                return_value=QualityReport(
                    overall_score=90.0,
                    clarity=QualityMetric(name="clarity", score=0.95),
                    completeness=QualityMetric(name="completeness", score=0.85),
                    consistency=QualityMetric(name="consistency", score=0.9),
                    token_efficiency=QualityMetric(name="token_efficiency", score=0.8),
                    actionability=QualityMetric(name="actionability", score=0.8),
                    recommendations=[],
                ),
            ) as mock_eval:
                result = evaluate_prompt_file(tmp_path)
                assert result.overall_score == 90.0
                call_arg = mock_eval.call_args[0][0]
                assert "测试提示词" in call_arg
        finally:
            Path(tmp_path).unlink(missing_ok=True)
