# Numpy开发规范指南

## 🎯 概述

本文档定义了Athena工作平台中使用numpy的标准规范，确保代码兼容性、性能和可维护性。

## 📦 标准导入方式

### ✅ 正确的导入方式

```python
# 推荐的numpy导入方式
from config.numpy_compatibility import (
    np,        # numpy模块本身
    array,     # 安全的数组创建
    zeros,     # 零数组创建
    ones,      # 一数组创建
    random,    # 随机数生成
    mean,      # 均值计算
    sum,       # 求和
    dot        # 点积运算
)

# 或者使用简化的导入
from config.numpy_compatibility import np, array, random
```

### ❌ 避免的导入方式

```python
# 不要直接使用这些导入
import numpy  # 缺少兼容性配置
import numpy as np
from numpy import array, random  # 可能不兼容
```

## 🔧 基础操作指南

### 数组创建

```python
# ✅ 使用安全的array函数
data = [1, 2, 3, 4, 5]
arr = array(data)              # 自动推断类型
arr_int = array(data, dtype=np.int64)  # 指定类型

# ✅ 使用安全的zeros和ones
zero_matrix = zeros((3, 3))    # 默认float64
one_vector = ones(100)         # 默认float64

# ✅ 特殊类型的数组
bool_array = array([True, False, True])
float_array = array([1.0, 2.0, 3.0])
```

### 随机数生成

```python
# ✅ 使用安全的random函数
random_values = random(100)                    # 100个随机数
random_matrix = random((10, 10))               # 10x10随机矩阵
random_ints = random(50)                       # 50个随机整数
```

### 数学运算

```python
# ✅ 使用提供的函数
values = array([1, 2, 3, 4, 5])
total = sum(values)                            # 求和
average = mean(values)                         # 均值
result = dot(array1, array2)                   # 点积

# ✅ 直接使用np的复杂函数
from config.numpy_compatibility import np
eigenvalues = np.linalg.eigvals(matrix)        # 特征值
```

## 🚀 性能优化建议

### 1. 利用M4 Pro的MPS加速

```python
import torch

# 配置MPS设备（已在numpy_compatibility.py中设置）
if torch.backends.mps.is_available():
    device = torch.device("mps")
    # 将大规模计算移到MPS
    tensor_data = torch.tensor(data).to(device)
```

### 2. 批处理优化

```python
# ✅ 使用适当的批处理大小
from config.m4_config import DEFAULT_BATCH_SIZE

for i in range(0, len(data), DEFAULT_BATCH_SIZE):
    batch = data[i:i+DEFAULT_BATCH_SIZE]
    processed = process_batch(array(batch))
```

### 3. 多进程并行

```python
from multiprocessing import Pool
from config.m4_config import DEFAULT_WORKERS

with Pool(processes=DEFAULT_WORKERS) as pool:
    results = pool.map(process_data, data_chunks)
```

## 📋 代码审查清单

在提交代码前，请确保：

- [ ] 使用了 `from config.numpy_compatibility import ...` 导入
- [ ] 避免使用已废弃的numpy类型（np.int, np.float等）
- [ ] 大型数组操作使用了批处理
- [ ] 随机数生成使用了random()函数
- [ ] 数组创建使用了array(), zeros(), ones()函数
- [ ] 性能关键代码考虑了MPS加速

## ⚠️ 常见陷阱

### 1. 类型不匹配

```python
# ❌ 错误：可能产生意外结果
result = np.array([1, 2, 3]) + np.array([1.0, 2.0, 3.0])

# ✅ 正确：明确指定类型
int_arr = array([1, 2, 3], dtype=np.int64)
float_arr = array([1.0, 2.0, 3.0])
result = int_arr + float_arr
```

### 2. 内存泄漏

```python
# ❌ 错误：循环中创建大数组
for i in range(10000):
    large_array = zeros(10000, 10000)  # 消耗大量内存

# ✅ 正确：复用数组或使用生成器
large_array = zeros(10000, 10000)
for i in range(10000):
    # 复用数组
    process_chunk(large_array)
```

### 3. 随机种子

```python
# ❌ 错误：全局设置随机种子可能影响其他模块
np.random.seed(42)

# ✅ 正确：使用局部随机数生成器
from config.numpy_compatibility import random
# random函数已封装了安全的随机数生成
```

## 🧪 测试指南

### 单元测试示例

```python
import unittest
from config.numpy_compatibility import array, random, mean, sum

class TestNumpyOperations(unittest.TestCase):

    def test_array_creation(self):
        """测试数组创建"""
        data = [1, 2, 3, 4, 5]
        arr = array(data)
        self.assertEqual(len(arr), 5)
        self.assertEqual(sum(arr), 15)

    def test_random_generation(self):
        """测试随机数生成"""
        rand_vals = random(100)
        self.assertEqual(len(rand_vals), 100)
        self.assertTrue(0 <= mean(rand_vals) <= 1)

    def test_type_safety(self):
        """测试类型安全"""
        int_arr = array([1, 2, 3], dtype=np.int64)
        self.assertEqual(int_arr.dtype, np.int64)

if __name__ == '__main__':
    unittest.main()
```

### 性能测试

```python
import time
from config.numpy_compatibility import array, random

def benchmark_operations():
    """基准测试numpy操作"""
    sizes = [1000, 10000, 100000]

    for size in sizes:
        # 测试数组创建
        start = time.time()
        arr = array(random(size))
        create_time = time.time() - start

        # 测试数学运算
        start = time.time()
        result = sum(arr)
        sum_time = time.time() - start

        print(f"Size {size}: create={create_time:.4f}s, sum={sum_time:.4f}s")
```

## 🔄 迁移指南

### 从传统numpy迁移

**旧代码:**
```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3])
zeros_arr = np.zeros((3, 3))
random_vals = np.random.rand(100)
```

**新代码:**
```python
from config.numpy_compatibility import array, zeros, random

# 创建数组
arr = array([1, 2, 3])
zeros_arr = zeros((3, 3))
random_vals = random(100)
```

### 批量迁移脚本

使用提供的工具：
```bash
# 分析需要迁移的文件
python3 dev/tools/unify_numpy_stack.py --directory . --dry-run

# 自动修复导入
python3 dev/tools/fix_numpy_compatibility.py --directory . --dry-run

# 应用修复
python3 dev/tools/fix_numpy_compatibility.py --directory .
```

## 📚 相关资源

- [Numpy官方文档](https://numpy.org/doc/)
- [Apple Silicon优化指南](./m4_optimization_guide.md)
- [PyTorch MPS文档](https://pytorch.org/docs/stable/notes/mps.html)

## 🤝 贡献指南

1. 所有新代码必须遵循本规范
2. 提交前运行兼容性测试：`python3 test_numpy_compatibility.py`
3. 更新文档时保持示例代码的最新性
4. 遇到兼容性问题时及时更新配置模块

---

*最后更新: 2025-12-18*
*版本: 1.0.0*