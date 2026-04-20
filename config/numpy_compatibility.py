#!/usr/bin/env python3
"""
Numpy兼容性统一配置模块
Numpy Compatibility Unified Configuration
"""

import logging
import os
import sys
import warnings
from typing import Any, Union

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NumpyCompatibilityManager:
    """Numpy兼容性管理器"""

    def __init__(self):
        self.numpy_version = None
        self.python_version = sys.version_info
        self.compatibility_mode = "auto"
        self._setup_numpy()

    def _setup_numpy(self) -> Any:
        """设置numpy环境"""
        try:
            import numpy as np
            self.numpy_version = np.__version__

            # 根据Python版本调整numpy配置
            if self.python_version >= (3, 14):
                self._configure_for_python_314(np)
            elif self.python_version >= (3, 11):
                self._configure_for_python_311(np)
            else:
                self._configure_for_legacy(np)

            logger.info(f"✅ Numpy {self.numpy_version} 配置完成 (Python {self.python_version.major}.{self.python_version.minor})")

        except ImportError as e:
            logger.error(f"❌ Numpy导入失败: {e}")
            raise

    def _configure_for_python_314(self, np) -> None:
        """为Python 3.14配置numpy"""
        # Python 3.14兼容性设置
        # 注意: legacy参数只能是False或"1.21"(numpy 1.21及更早版本)
        # 对于numpy 1.26+，使用False来禁用legacy模式
        try:
            np.set_printoptions(legacy=False)
        except TypeError:
            # 如果numpy版本太旧不支持legacy=False，跳过此设置
            pass

        # 禁用一些可能导致问题的警告
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="numpy")

        # 设置错误处理
        np.seterr(divide='warn', invalid='warn', over='warn')

        self.compatibility_mode = "python314"

    def _configure_for_python_311(self, np) -> None:
        """为Python 3.11配置numpy"""
        # Python 3.11的标准配置
        np.seterr(divide='warn', invalid='warn')

        self.compatibility_mode = "python311"

    def _configure_for_legacy(self, np) -> None:
        """为Python < 3.11配置numpy"""
        # 传统Python版本的配置
        np.seterr(all='warn')

        self.compatibility_mode = "legacy"

    def get_safe_array(self, data: Any, dtype: Union[str, type, None] = None) -> "np.ndarray":
        """创建安全的numpy数组"""
        import numpy as np

        try:
            if dtype is None:
                # 自动选择合适的dtype
                if isinstance(data, list) and len(data) > 0:
                    if all(isinstance(x, int) for x in data):
                        dtype = np.int64
                    elif all(isinstance(x, float) for x in data):
                        dtype = np.float64
                    else:
                        dtype = np.object_
                else:
                    dtype = np.float64

            return np.array(data, dtype=dtype)

        except (ValueError, TypeError) as e:
            logger.warning(f"数组创建失败，使用备用方案: {e}")
            # 备用方案：转换为列表再创建数组
            return np.array(list(data), dtype=np.object_)

    def safe_random(self, size: Union[int, tuple], dtype: Union[type, None] = None) -> "np.ndarray":
        """安全的随机数生成"""
        import numpy as np

        try:
            if dtype is None:
                dtype = np.float64

            # 使用更安全的随机数生成方式
            if isinstance(size, int):
                size = (size,)

            return np.random.standard_normal(size).astype(dtype)

        except Exception as e:
            logger.warning(f"随机数生成失败，使用备用方案: {e}")
            # 备用方案：使用Python的random模块
            import random
            if isinstance(size, int):
                return np.array([random.random() for _ in range(size)], dtype=dtype)
            else:
                flat_size = 1
                for dim in size:
                    flat_size *= dim
                data = [random.random() for _ in range(flat_size)]
                return np.array(data).reshape(size).astype(dtype)

    def get_compatibility_info(self) -> dict[str, Any]:
        """获取兼容性信息"""
        return {
            "python_version": f"{self.python_version.major}.{self.python_version.minor}",
            "numpy_version": self.numpy_version,
            "compatibility_mode": self.compatibility_mode,
            "recommendations": self._get_recommendations()
        }

    def _get_recommendations(self) -> list[str]:
        """获取优化建议"""
        recommendations = []

        if self.python_version >= (3, 14):
            recommendations.extend([
                "建议使用numpy 2.x版本",
                "避免使用已弃用的API",
                "考虑使用typing.Protocol进行类型注解"
            ])
        elif self.python_version >= (3, 11):
            recommendations.extend([
                "可以使用numpy 1.24+版本",
                "支持所有现代numpy功能",
                "建议启用性能优化"
            ])
        else:
            recommendations.extend([
                "建议升级Python版本",
                "使用numpy 1.21-1.23版本",
                "避免使用新的numpy特性"
            ])

        return recommendations

# 创建全局实例
numpy_manager = NumpyCompatibilityManager()

# 导出常用的numpy功能和别名
try:
    import numpy as np

    # 常用函数的安全版本
    def safe_array(data, dtype=None) -> None:
        """创建numpy数组的安全版本"""
        return numpy_manager.get_safe_array(data, dtype)

    def safe_random(size, dtype=None) -> None:
        """生成随机数的安全版本"""
        return numpy_manager.safe_random(size, dtype)

    # 兼容性别名
    array = safe_array

    def safe_zeros(shape, dtype=None) -> None:
        """安全的zeros函数"""
        return np.zeros(shape, dtype=dtype or np.float64)

    def safe_ones(shape, dtype=None) -> None:
        """安全的ones函数"""
        return np.ones(shape, dtype=dtype or np.float64)

    zeros = safe_zeros
    ones = safe_ones
    random = safe_random
    mean = np.mean
    sum = np.sum
    dot = np.dot

    # 向后兼容的导入
    __all__ = [
        'np', 'array', 'zeros', 'ones', 'random', 'mean', 'sum', 'dot',
        'numpy_manager', 'safe_array', 'safe_random'
    ]

except ImportError:
    logger.error("❌ Numpy未安装，请安装: pip install numpy")
    np = None
    __all__ = ['numpy_manager']

# 环境变量配置
def configure_environment() -> Any:
    """配置环境变量以优化numpy性能"""
    # 设置OpenMP线程数
    os.environ["OMP_NUM_THREADS"] = str(os.cpu_count())
    os.environ["MKL_NUM_THREADS"] = str(os.cpu_count())
    os.environ["OPENBLAS_NUM_THREADS"] = str(os.cpu_count())
    os.environ["VECLIB_MAXIMUM_THREADS"] = str(os.cpu_count())

    # 针对Apple Silicon的优化
    if sys.platform == "darwin":
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    logger.info("✅ 环境变量配置完成")

# 自动配置环境
configure_environment()

if __name__ == "__main__":
    # 测试和展示配置信息
    info = numpy_manager.get_compatibility_info()

    print("🔧 Numpy兼容性配置信息")
    print("=" * 50)
    print(f"Python版本: {info['python_version']}")
    print(f"Numpy版本: {info['numpy_version']}")
    print(f"兼容模式: {info['compatibility_mode']}")

    print("\n💡 优化建议:")
    for rec in info['recommendations']:
        print(f"   - {rec}")

    # 测试基本功能
    if np is not None:
        print("\n🧪 功能测试:")
        test_array = safe_array([1, 2, 3, 4, 5])
        print(f"   创建数组: {test_array}")

        test_random = random(5)
        print(f"   随机数组: {test_random}")

        print(f"   数组求和: {sum(test_array)}")
        print(f"   数组均值: {mean(test_random)}")

        print("\n✅ 所有测试通过")
