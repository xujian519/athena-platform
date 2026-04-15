#!/usr/bin/env python3
"""
多模态专利分析集成测试

测试范围:
1. API端到端测试
2. 模型加载和推理
3. 图像分析完整流程
"""

from __future__ import annotations
import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
import requests
from PIL import Image

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMultimodalAPI:
    """多模态API集成测试"""

    @pytest.fixture(scope="class")
    def api_base_url(self):
        """API基础URL"""
        return os.getenv("API_BASE_URL", "http://127.0.0.1:8888")

    @pytest.fixture(scope="class")
    def sample_image(self):
        """创建示例图像"""
        img = Image.new('RGB', (800, 600), color='white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # 画一个简单的流程图
        draw.rectangle([100, 100, 300, 200], outline='black', width=3)
        draw.rectangle([100, 300, 300, 400], outline='black', width=3)
        draw.line([200, 200, 200, 300], fill='black', width=2)
        draw.line([300, 150, 400, 250], fill='black', width=2)

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            yield f.name

    def test_health_check(self, api_base_url):
        """测试健康检查端点"""
        response = requests.get(f"{api_base_url}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_image_analysis_api(self, api_base_url, sample_image):
        """测试图像分析API"""
        with open(sample_image, 'rb') as f:
            files = {'file': ('test.png', f, 'image/png')}
            data = {'reference_text': '测试流程图'}

        response = requests.post(
            f"{api_base_url}/api/v1/patent/image/analyze",
            files=files,
            data=data,
            timeout=30
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
        assert "result" in result
        assert result["result"]["image_type"] in ["figure", "flowchart", "structure", "other"]
        assert isinstance(result["result"]["caption"], str)
        assert result["result"]["processing_time"] > 0

    def test_text_search_api(self, api_base_url):
        """测试文本搜索API"""
        params = {
            "query": "无线通信基站",
            "top_k": 3
        }
        response = requests.get(
            f"{api_base_url}/api/v1/patent/search",
            params=params,
            timeout=30
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_concurrent_requests(self, api_base_url, sample_image):
        """测试并发请求"""
        async def send_request():
            with open(sample_image, 'rb') as f:
                files = {'file': ('test.png', f, 'image/png')}
                data = {'reference_text': '并发测试'}

            response = requests.post(
                f"{api_base_url}/api/v1/patent/image/analyze",
                files=files,
                data=data,
                timeout=30
            )
            return response.json()

        # 发送3个并发请求
        results = asyncio.run(asyncio.gather(
            send_request(),
            send_request(),
            send_request()
        ))

        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"


class TestModelLoading:
    """模型加载集成测试"""

    def test_clip_model_loading(self):
        """测试CLIP模型加载"""
        from production.core.perception.processors.patent_image_analyzer import PatentImageAnalyzer

        analyzer = PatentImageAnalyzer(device="cpu")
        analyzer.load_models()

        assert analyzer.clip_model is not None
        assert analyzer.clip_processor is not None

    def test_blip_model_loading_from_modelscope(self):
        """测试从ModelScope加载BLIP模型"""
        from production.core.perception.processors.patent_image_analyzer import (
            ModelPaths,
            PatentImageAnalyzer,
        )

        ms_path = os.path.expanduser(ModelPaths.MODELSCOPE_BLIP)
        if not os.path.exists(ms_path):
            pytest.skip(f"ModelScope模型不存在: {ms_path}")

        analyzer = PatentImageAnalyzer(device="cpu")
        analyzer.load_models()

        assert analyzer.blip_model is not None
        assert analyzer.blip_processor is not None

    def test_model_loading_timeout(self):
        """测试模型加载超时控制"""
        from production.core.perception.processors.patent_image_analyzer import (
            ModelLoading,
            PatentImageAnalyzer,
        )

        assert ModelLoading.CLIP_TIMEOUT == 120
        assert ModelLoading.BLIP_TIMEOUT == 120


class TestImageAnalysisWorkflow:
    """图像分析工作流测试"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        from production.core.perception.processors.patent_image_analyzer import PatentImageAnalyzer
        return PatentImageAnalyzer(device="cpu")

    def test_complete_analysis_workflow(self, analyzer):
        """测试完整的分析工作流"""
        # 创建测试图像
        img = Image.new('RGB', (800, 1200), color='white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # 画流程图元素
        draw.rectangle([200, 100, 600, 250], outline='black', width=3)
        draw.rectangle([200, 400, 600, 550], outline='black', width=3)
        draw.rectangle([200, 700, 600, 850], outline='black', width=3)
        draw.line([400, 250, 400, 400], fill='black', width=2)
        draw.line([400, 550, 400, 700], fill='black', width=2)

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            temp_path = f.name

        try:
            # 异步分析图像
            async def run_analysis():
                return await analyzer.analyze(temp_path, reference_text="测试流程")

            result = asyncio.run(run_analysis())

            # 验证结果
            assert result.image_id is not None
            assert len(result.image_id) == 16
            assert result.image_type in ["figure", "flowchart", "structure", "other"]
            assert isinstance(result.caption, str)
            assert result.processing_time > 0
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0

        finally:
            os.unlink(temp_path)

    def test_fallback_degradation(self, analyzer):
        """测试优雅降级"""
        # 模拟BLIP模型未加载
        analyzer.blip_model = None
        analyzer.blip_processor = None

        img = Image.new('RGB', (400, 600), color='white')

        async def run_analysis():
            return await analyzer._generate_caption(img)

        caption = asyncio.run(run_analysis())

        # 应该返回备用描述或空字符串
        assert isinstance(caption, str)


class TestImageValidation:
    """图像验证集成测试"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        from production.core.perception.processors.patent_image_analyzer import PatentImageAnalyzer
        return PatentImageAnalyzer()

    def test_valid_image_validation(self, analyzer):
        """测试有效图像验证"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            img = Image.new('RGB', (800, 600), color='white')
            img.save(f)

        try:
            result = analyzer._validate_image_file(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_invalid_extension_validation(self, analyzer):
        """测试无效扩展名验证"""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            temp_path = f.name
            f.write(b"fake content")

        try:
            with pytest.raises(ValueError, match="不支持的文件类型"):
                analyzer._validate_image_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_missing_file_validation(self, analyzer):
        """测试文件不存在验证"""
        with pytest.raises(ValueError, match="图像文件不存在"):
            analyzer._validate_image_file("/nonexistent/file.png")


class TestConfiguration:
    """配置集成测试"""

    def test_modelscope_path_configuration(self):
        """测试ModelScope路径配置"""
        import os

        from production.core.perception.processors.patent_image_analyzer import ModelPaths

        path = os.path.expanduser(ModelPaths.MODELSCOPE_BLIP)
        assert "modelscope" in path.lower()
        assert "blip" in path.lower()

    def test_huggingface_cache_configuration(self):
        """测试HuggingFace缓存配置"""
        import os

        from production.core.perception.processors.patent_image_analyzer import ModelPaths

        path = os.path.expanduser(ModelPaths.HUGGINGFACE_CACHE)
        assert "huggingface" in path.lower()

    def test_timeout_configuration(self):
        """测试超时配置"""
        from production.core.perception.processors.patent_image_analyzer import ModelLoading

        assert ModelLoading.CLIP_TIMEOUT == 120
        assert ModelLoading.BLIP_TIMEOUT == 120
        assert ModelLoading.MAX_RETRIES == 2


# ============================================================================
# 运行配置
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
