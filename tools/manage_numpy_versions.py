#!/usr/bin/env python3
"""
Numpy版本管理工具
Numpy Version Management Tool
"""

import sys
from pathlib import Path

import requests


class NumpyVersionManager:
    """Numpy版本管理器"""

    def __init__(self):
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.current_numpy = self._get_current_numpy_version()
        self.compatibility_matrix = self._load_compatibility_matrix()

    def _get_current_numpy_version(self) -> str:
        """获取当前numpy版本"""
        try:
            import numpy
            return numpy.__version__
        except ImportError:
            return None

    def _load_compatibility_matrix(self) -> dict:
        """加载Python-numpy兼容性矩阵"""
        return {
            "3.11": {
                "min_numpy": "1.21.0",
                "recommended_numpy": "1.24.0",
                "max_numpy": "2.0.0",
                "note": "支持所有numpy版本，推荐1.24+"
            },
            "3.12": {
                "min_numpy": "1.23.0",
                "recommended_numpy": "1.25.0",
                "max_numpy": "2.1.0",
                "note": "推荐numpy 1.26+以获得最佳性能"
            },
            "3.13": {
                "min_numpy": "1.24.0",
                "recommended_numpy": "1.26.0",
                "max_numpy": "2.2.0",
                "note": "numpy 2.0+原生支持"
            },
            "3.14": {
                "min_numpy": "2.0.0",
                "recommended_numpy": "2.2.6",
                "max_numpy": None,  # 最新版本
                "note": "需要numpy 2.x版本"
            }
        }

    def check_compatibility(self) -> dict:
        """检查当前兼容性状态"""
        python_info = self.compatibility_matrix.get(self.python_version, {})

        if not python_info:
            return {
                "status": "error",
                "message": f"不支持的Python版本: {self.python_version}"
            }

        result = {
            "python_version": self.python_version,
            "current_numpy": self.current_numpy,
            "recommendations": python_info,
            "status": "unknown"
        }

        if not self.current_numpy:
            result["status"] = "error"
            result["message"] = "Numpy未安装"
        else:
            # 检查版本兼容性
            if self._version_compare(self.current_numpy, python_info.get("min_numpy", "0")) < 0:
                result["status"] = "error"
                result["message"] = f"Numpy版本过低，需要 >= {python_info['min_numpy']}"
            elif python_info.get("max_numpy") and \
                 self._version_compare(self.current_numpy, python_info["max_numpy"]) > 0:
                result["status"] = "warning"
                result["message"] = f"Numpy版本过高，推荐 <= {python_info['max_numpy']}"
            else:
                result["status"] = "ok"
                result["message"] = "版本兼容"

        return result

    def _version_compare(self, v1: str, v2: str) -> int:
        """比较版本号 (v1 > v2: 1, v1 == v2: 0, v1 < v2: -1)"""
        def normalize(v):
            return [int(x) for x in v.split('.')]

        v1_parts = normalize(v1)
        v2_parts = normalize(v2)

        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_val = v1_parts[i] if i < len(v1_parts) else 0
            v2_val = v2_parts[i] if i < len(v2_parts) else 0

            if v1_val > v2_val:
                return 1
            elif v1_val < v2_val:
                return -1

        return 0

    def get_latest_numpy_version(self) -> str | None:
        """获取最新的numpy版本"""
        try:
            response = requests.get(
                "https://pypi.org/pypi/numpy/json",
                timeout=10
            )
            data = response.json()
            return data["info"]["version"]
        except Exception as e:
            print(f"获取最新版本失败: {e}")
            return None

    def recommend_upgrade(self) -> dict:
        """推荐升级方案"""
        compat = self.check_compatibility()
        latest = self.get_latest_numpy_version()

        python_info = compat["recommendations"]
        recommended = python_info.get("recommended_numpy")

        recommendation = {
            "current": self.current_numpy,
            "recommended": recommended,
            "latest": latest,
            "upgrade_required": compat["status"] != "ok",
            "upgrade_command": None,
            "steps": []
        }

        if compat["status"] == "error":
            # 需要升级
            recommendation["steps"] = [
                "1. 卸载当前版本: pip uninstall numpy",
                f"2. 安装推荐版本: pip install numpy=={recommended}",
                "3. 运行兼容性测试: python3 test_numpy_compatibility.py"
            ]
            recommendation["upgrade_command"] = f"pip install numpy=={recommended}"

        elif compat["status"] == "warning":
            # 可选升级
            if self._version_compare(latest or "0", recommended) > 0:
                recommendation["steps"] = [
                    "1. 备份当前环境",
                    f"2. 升级到最新版本: pip install numpy=={latest}",
                    "3. 测试所有功能",
                    "4. 如有问题回退到: pip install numpy=={recommended}"
                ]
                recommendation["upgrade_command"] = f"pip install numpy=={latest}"

        return recommendation

    def update_requirements(self, dry_run: bool = True) -> list[str]:
        """更新requirements文件"""
        updated_files = []

        # 查找所有requirements文件
        for req_file in Path(".").rglob("requirements*.txt"):
            # 跳过备份目录
            if any(skip in str(req_file) for skip in [".git", "__pycache__", ".venv"]):
                continue

            try:
                content = req_file.read_text()
                lines = content.split('\n')
                new_lines = []
                modified = False

                for line in lines:
                    line = line.strip()

                    # 更新numpy版本
                    if line.startswith("numpy"):
                        compat = self.check_compatibility()
                        if compat["status"] == "ok":
                            # 当前版本合适，不修改
                            new_lines.append(line)
                        else:
                            # 更新到推荐版本
                            recommended = compat["recommendations"]["recommended_numpy"]
                            new_line = f"numpy>={recommended}"
                            if not new_line.startswith(line.split('>')[0]):
                                modified = True
                            new_lines.append(new_line)
                    else:
                        new_lines.append(line)

                if modified and not dry_run:
                    req_file.write_text('\n'.join(new_lines))
                    updated_files.append(str(req_file))
                    print(f"✅ 更新文件: {req_file}")
                elif modified:
                    print(f"🔍 需要更新: {req_file}")
                    updated_files.append(str(req_file))

            except Exception as e:
                print(f"❌ 处理文件失败 {req_file}: {e}")

        return updated_files

    def create_test_suite(self) -> str:
        """创建版本兼容性测试套件"""
        test_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numpy版本兼容性测试套件
Auto-generated by manage_numpy_versions.py
"""

import sys
import unittest
import time
from datetime import datetime

# 导入配置
try:
    from config.numpy_compatibility import np, array, zeros, ones, random, mean, sum, dot
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    IMPORT_SUCCESS = False

class TestNumpyCompatibility(unittest.TestCase):
    """Numpy兼容性测试"""

    def setUp(self):
        """测试准备"""
        if not IMPORT_SUCCESS:
            self.skipTest("Numpy导入失败")

    def test_basic_operations(self):
        """测试基础操作"""
        # 数组创建
        arr = array([1, 2, 3, 4, 5])
        self.assertEqual(len(arr), 5)

        # 数学运算
        self.assertEqual(sum(arr), 15)
        self.assertAlmostEqual(mean(arr), 3.0)

        # 特殊数组
        zeros_arr = zeros((3, 3))
        self.assertEqual(zeros_arr.shape, (3, 3))

        ones_arr = ones(5)
        self.assertEqual(len(ones_arr), 5)

    def test_random_operations(self):
        """测试随机数操作"""
        # 随机数组
        rand_vals = random(100)
        self.assertEqual(len(rand_vals), 100)

        # 随机矩阵
        rand_matrix = random((10, 10))
        self.assertEqual(rand_matrix.shape, (10, 10))

    def test_type_safety(self):
        """测试类型安全"""
        # 整数数组
        int_arr = array([1, 2, 3], dtype=np.int64)
        self.assertEqual(int_arr.dtype, np.int64)

        # 浮点数组
        float_arr = array([1.0, 2.0, 3.0])
        self.assertEqual(float_arr.dtype, np.float64)

        # 布尔数组
        bool_arr = array([True, False, True])
        self.assertTrue(bool_arr.dtype in [np.bool_, bool])

    def test_advanced_operations(self):
        """测试高级操作"""
        # 矩阵运算
        a = array([[1, 2], [3, 4]])
        b = array([[5, 6], [7, 8]])
        c = dot(a, b)
        expected = array([[19, 22], [43, 50]])

        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(c[i, j], expected[i, j])

    def test_performance(self):
        """性能基准测试"""
        sizes = [1000, 10000]

        for size in sizes:
            # 测试数组创建性能
            start = time.time()
            arr = array(random(size))
            create_time = time.time() - start

            # 测试运算性能
            start = time.time()
            result = sum(arr)
            sum_time = time.time() - start

            # 简单的性能断言（根据实际情况调整）
            self.assertLess(create_time, 1.0, f"数组创建时间过长: {create_time}s")
            self.assertLess(sum_time, 1.0, f"求和时间过长: {sum_time}s")

def run_compatibility_report():
    """运行兼容性报告"""
    print("\\n" + "="*60)
    print(f"Numpy兼容性测试报告")
    print("="*60)
    print(f"Python版本: {sys.version}")
    print(f"测试时间: {datetime.now()}")

    if IMPORT_SUCCESS:
        print(f"Numpy版本: {np.__version__}")
        print(f"导入状态: ✅ 成功")
    else:
        print(f"Numpy版本: 未知")
        print(f"导入状态: ❌ 失败")

    print("="*60)

if __name__ == "__main__":
    run_compatibility_report()

    if IMPORT_SUCCESS:
        # 运行测试套件
        unittest.main(verbosity=2)
    else:
        print("\\n⚠️ 由于导入失败，跳过兼容性测试")
        sys.exit(1)
'''

        return test_content

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Numpy版本管理工具")
    parser.add_argument("--check", action="store_true", help="检查兼容性")
    parser.add_argument("--recommend", action="store_true", help="推荐升级方案")
    parser.add_argument("--update-requirements", action="store_true", help="更新requirements文件")
    parser.add_argument("--dry-run", action="store_true", help="预览模式")
    parser.add_argument("--create-test", action="store_true", help="创建测试套件")
    parser.add_argument("--latest", action="store_true", help="检查最新版本")

    args = parser.parse_args()

    manager = NumpyVersionManager()

    print("🔧 Numpy版本管理工具")
    print("=" * 50)
    print(f"Python版本: {manager.python_version}")
    print(f"当前Numpy: {manager.current_numpy or '未安装'}")

    if args.check or not any(vars(args).values()):
        # 默认执行检查
        compat = manager.check_compatibility()
        print(f"\n📊 兼容性状态: {compat['status']}")
        print(f"   消息: {compat['message']}")
        print(f"   推荐版本: {compat['recommendations'].get('recommended_numpy')}")
        print(f"   说明: {compat['recommendations'].get('note')}")

    if args.latest:
        latest = manager.get_latest_numpy_version()
        if latest:
            print(f"\n🆕 最新Numpy版本: {latest}")
            if manager._version_compare(latest, manager.current_numpy or "0") > 0:
                print("   📦 有新版本可用！")
            else:
                print("   ✅ 已是最新版本")

    if args.recommend:
        rec = manager.recommend_upgrade()
        print("\n💡 升级建议:")
        print(f"   当前版本: {rec['current']}")
        print(f"   推荐版本: {rec['recommended']}")
        print(f"   最新版本: {rec['latest']}")
        print(f"   需要升级: {'是' if rec['upgrade_required'] else '否'}")

        if rec['upgrade_command']:
            print(f"   升级命令: {rec['upgrade_command']}")

        if rec['steps']:
            print("\n📋 操作步骤:")
            for step in rec['steps']:
                print(f"   {step}")

    if args.update_requirements:
        print("\n🔄 更新requirements文件...")
        updated = manager.update_requirements(dry_run=args.dry_run)

        if updated:
            print(f"   {'将更新' if args.dry_run else '已更新'} {len(updated)} 个文件")
        else:
            print("   没有需要更新的文件")

    if args.create_test:
        print("\n🧪 创建兼容性测试套件...")
        test_content = manager.create_test_suite()

        test_file = Path("test_numpy_version_compatibility.py")
        test_file.write_text(test_content)

        print(f"   ✅ 测试文件已创建: {test_file}")
        print(f"   运行命令: python3 {test_file}")

if __name__ == "__main__":
    main()
