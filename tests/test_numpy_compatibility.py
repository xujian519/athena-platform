#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numpy兼容性测试
Numpy Compatibility Test
"""

import sys
import warnings
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_numpy_compatibility():
    """测试numpy兼容性"""
    print("🧪 开始Numpy兼容性测试...")

    try:
        # 测试基础导入
        from config.numpy_compatibility import np, array, zeros, ones, random, mean, sum, dot
        print("✅ 基础导入成功")

        # 测试数组创建
        test_arr = array([1, 2, 3, 4, 5])
        print(f"✅ 数组创建: {test_arr}")

        # 测试零数组
        zeros_arr = zeros((3, 3))
        print(f"✅ 零数组创建: {zeros_arr.shape}")

        # 测试随机数
        rand_arr = random(5)
        print(f"✅ 随机数组: {rand_arr[:3]}...")

        # 测试数学运算
        print(f"✅ 数组求和: {sum(test_arr)}")
        print(f"✅ 数组均值: {mean(test_arr)}")

        # 测试高级功能
        a = array([[1, 2], [3, 4]])
        b = array([[5, 6], [7, 8]])
        c = dot(a, b)
        print(f"✅ 矩阵乘法:\n{c}")

        # 测试类型兼容性
        int_arr = array([1, 2, 3], dtype=np.int64)
        float_arr = array([1.0, 2.0, 3.0], dtype=np.float64)
        bool_arr = array([True, False, True])
        print(f"✅ 类型测试: int={int_arr.dtype}, float={float_arr.dtype}, bool={bool_arr.dtype}")

        print("\n🎉 所有兼容性测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_numpy_compatibility()
    sys.exit(0 if success else 1)
