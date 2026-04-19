#!/usr/bin/env python3
from __future__ import annotations
"""
测试：重型依赖懒加载
Test: Heavy Dependencies Lazy Loading
"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.lazy_imports import (
    PIL,
    LazyLoader,
    cv2,
    cv2_extended,
    lazy_import,
    numpy,
    torch,
    torchvision,
)


class TestLazyLoader:
    """测试懒加载器类"""

    def test_lazy_loader_creation(self):
        """测试创建懒加载器"""
        loader = LazyLoader("math", "math")
        assert loader.module_name == "math"
        assert loader.import_path == "math"
        assert not loader.is_loaded()

    def test_lazy_loader_attribute_access(self):
        """测试访问属性时加载模块"""
        loader = LazyLoader("math", "math")
        assert not loader.is_loaded()

        # 访问sqrt属性应该触发加载
        result = loader.sqrt(16)
        assert loader.is_loaded()
        assert result == 4.0

    def test_lazy_loader_with_nonexistent_module(self):
        """测试不存在的模块"""
        loader = LazyLoader("nonexistent_module", "nonexistent_module")

        with pytest.raises(ImportError):
            _ = loader.some_attribute


class TestLazyImportFunction:
    """测试lazy_import便捷函数"""

    def test_lazy_import_function(self):
        """测试lazy_import函数"""
        math_loader = lazy_import("math", "math")
        assert isinstance(math_loader, LazyLoader)
        assert math_loader.module_name == "math"

        # 使用懒加载的模块
        result = math_loader.pow(2, 3)
        assert result == 8.0


class TestPredefinedLazyLoaders:
    """测试预定义的懒加载器"""

    def test_numpy_lazy_loader(self):
        """测试numpy懒加载器"""
        # 在测试环境中，numpy可能已安装
        # 这里我们测试懒加载器本身是否存在
        assert hasattr(numpy, "module_name")
        assert numpy.module_name == "numpy"

    def test_cv2_lazy_loader(self):
        """测试cv2懒加载器"""
        assert hasattr(cv2, "module_name")
        assert cv2.module_name == "opencv-python"

    def test_torch_lazy_loader(self):
        """测试torch懒加载器"""
        assert hasattr(torch, "module_name")
        assert torch.module_name == "torch"

    def test_torchvision_lazy_loader(self):
        """测试torchvision懒加载器"""
        assert hasattr(torchvision, "module_name")
        assert torchvision.module_name == "torchvision"

    def test_pil_lazy_loader(self):
        """测试PIL懒加载器"""
        assert hasattr(PIL, "module_name")
        assert PIL.module_name == "pillow"


class TestCV2ExtendedLoader:
    """测试CV2扩展加载器"""

    def test_cv2_extended_loader(self):
        """测试cv2_extended加载器"""
        # cv2_extended是CV2Loader类的实例
        assert hasattr(cv2_extended, "_cv2")

    def test_cv2_extended_not_loaded_initially(self):
        """测试cv2_extended初始时未加载"""
        # 创建新的CV2Loader实例
        from core.perception.lazy_imports import CV2Loader
        loader = CV2Loader()
        assert loader._cv2 is None


class TestLazyLoadingBehavior:
    """测试懒加载行为"""

    def test_lazy_loading_delays_import(self):
        """测试懒加载延迟导入"""
        # 创建一个记录导入的变量
        import_count = [0]

        # 创建自定义懒加载器
        class CustomLazyLoader(LazyLoader):
            def __getattr__(self, name: str):
                import_count[0] += 1
                return super().__getattr__(name)

        loader = CustomLazyLoader("math", "math")
        assert import_count[0] == 0
        assert not loader.is_loaded()

        # 访问属性触发导入
        _ = loader.sqrt
        assert import_count[0] == 1
        assert loader.is_loaded()

    def test_lazy_loading_one_time_import(self):
        """测试懒加载只导入一次"""
        loader = LazyLoader("math", "math")

        # 多次访问不同属性
        _ = loader.sqrt
        _ = loader.pow
        _ = loader.sin

        # 模块应该只导入一次
        # is_loaded()在第一次访问后就应该返回True
        assert loader.is_loaded()

    def test_lazy_loading_with_fallback(self):
        """测试懒加载的降级处理"""
        # 使用一个可能不存在的模块
        loader = LazyLoader("unlikely_module_name_xyz", "unlikely_module_name_xyz")

        # 尝试访问属性应该抛出ImportError
        with pytest.raises(ImportError):
            _ = loader.some_attribute


class TestLazyLoadingMemoryEfficiency:
    """测试懒加载的内存效率"""

    def test_lazy_loader_small_memory_footprint(self):
        """测试懒加载器的小内存占用"""
        # 创建多个懒加载器，但未实际加载模块
        loaders = [
            LazyLoader("module1", "unlikely_module_1"),
            LazyLoader("module2", "unlikely_module_2"),
            LazyLoader("module3", "unlikely_module_3"),
        ]

        # 所有加载器都应该未加载
        for loader in loaders:
            assert not loader.is_loaded()

        # 懒加载器本身应该占用很少内存
        # （这里我们只是验证它们存在且未加载）
        assert len(loaders) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
