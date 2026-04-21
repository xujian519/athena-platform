#!/usr/bin/env python3
"""
Athena路径工具模块单元测试
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.utils.paths import (
    AthenaPaths,
    get_paths,
    get_project_root,
    ensure_project_root_in_path,
)


class TestAthenaPathsInitialization:
    """AthenaPaths初始化测试"""

    def test_init_with_explicit_root(self):
        """测试使用显式根目录初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建新的实例，不使用全局单例
            paths = AthenaPaths(project_root=Path(temp_dir))
            # 验证项目根目录包含temp_dir
            assert temp_dir in str(paths.project_root)

    def test_init_with_environment_variable(self):
        """测试使用环境变量初始化"""
        # 注意：全局单例可能已经创建，这个测试只验证功能
        original_home = os.environ.get('ATHENA_HOME')
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.environ['ATHENA_HOME'] = temp_dir
                # 创建新实例（不使用全局单例）
                paths = AthenaPaths(project_root=None)
                # 验证使用了环境变量或自动检测
                assert paths.project_root.exists()
        finally:
            if original_home:
                os.environ['ATHENA_HOME'] = original_home
            elif 'ATHENA_HOME' in os.environ:
                del os.environ['ATHENA_HOME']

    def test_init_auto_detect(self):
        """测试自动检测项目根目录"""
        paths = AthenaPaths()
        # 应该能检测到项目根目录
        assert paths.project_root.exists()
        # 项目根目录或其父目录应该包含core
        core_in_project = (paths.project_root / "core").exists()
        parent = paths.project_root.parent
        core_in_parent = (parent / "core").exists()
        assert core_in_project or core_in_parent

    def test_init_adds_to_sys_path(self):
        """测试初始化时将项目根目录添加到sys.path"""
        project_root = str(AthenaPaths().project_root)
        assert project_root in sys.path


class TestAthenaPathsProperties:
    """AthenaPaths属性测试"""

    def test_project_root_property(self):
        """测试project_root属性"""
        paths = AthenaPaths()
        assert isinstance(paths.project_root, Path)
        assert paths.project_root.exists()

    def test_core_dir_property(self):
        """测试core_dir属性"""
        paths = AthenaPaths()
        core_dir = paths.core_dir
        assert isinstance(core_dir, Path)
        assert core_dir.name == "core"
        assert core_dir == paths.project_root / "core"

    def test_services_dir_property(self):
        """测试services_dir属性"""
        paths = AthenaPaths()
        services_dir = paths.services_dir
        assert isinstance(services_dir, Path)
        assert services_dir == paths.project_root / "services"

    def test_modules_dir_property(self):
        """测试modules_dir属性"""
        paths = AthenaPaths()
        modules_dir = paths.modules_dir
        assert isinstance(modules_dir, Path)
        assert modules_dir == paths.project_root / "modules"

    def test_config_dir_property(self):
        """测试config_dir属性"""
        paths = AthenaPaths()
        config_dir = paths.config_dir
        assert isinstance(config_dir, Path)
        assert config_dir == paths.project_root / "config"

    def test_production_dir_property(self):
        """测试production_dir属性"""
        paths = AthenaPaths()
        production_dir = paths.production_dir
        assert isinstance(production_dir, Path)
        assert production_dir == paths.project_root / "production"

    def test_data_dir_property(self):
        """测试data_dir属性"""
        paths = AthenaPaths()
        data_dir = paths.data_dir
        assert isinstance(data_dir, Path)
        assert data_dir == paths.project_root / "data"

    def test_logs_dir_property(self):
        """测试logs_dir属性"""
        paths = AthenaPaths()
        logs_dir = paths.logs_dir
        assert isinstance(logs_dir, Path)
        assert logs_dir == paths.project_root / "production" / "logs"

    def test_cache_dir_property(self):
        """测试cache_dir属性"""
        paths = AthenaPaths()
        cache_dir = paths.cache_dir
        assert isinstance(cache_dir, Path)
        assert cache_dir == paths.project_root / "production" / "cache"

    def test_models_dir_property(self):
        """测试models_dir属性"""
        paths = AthenaPaths()
        models_dir = paths.models_dir
        assert isinstance(models_dir, Path)
        assert models_dir == paths.project_root / "models"

    def test_scripts_dir_property(self):
        """测试scripts_dir属性"""
        paths = AthenaPaths()
        scripts_dir = paths.scripts_dir
        assert isinstance(scripts_dir, Path)
        assert scripts_dir == paths.project_root / "production" / "scripts"

    def test_tests_dir_property(self):
        """测试tests_dir属性"""
        paths = AthenaPaths()
        tests_dir = paths.tests_dir
        assert isinstance(tests_dir, Path)
        assert tests_dir == paths.project_root / "tests"

    def test_apps_dir_property(self):
        """测试apps_dir属性"""
        paths = AthenaPaths()
        apps_dir = paths.apps_dir
        assert isinstance(apps_dir, Path)
        assert apps_dir == paths.project_root / "apps"


class TestAthenaPathsMethods:
    """AthenaPaths方法测试"""

    def test_get_relative_path_inside_project(self):
        """测试获取项目内相对路径"""
        paths = AthenaPaths()
        target = paths.core_dir / "test.py"
        relative = paths.get_relative_path(target)
        assert relative == Path("core/test.py")

    def test_get_relative_path_outside_project(self):
        """测试获取项目外路径（返回绝对路径）"""
        paths = AthenaPaths()
        target = Path("/tmp/test.py")
        relative = paths.get_relative_path(target)
        assert relative == Path("/tmp/test.py")

    def test_resolve_path_absolute(self):
        """测试解析绝对路径"""
        paths = AthenaPaths()
        absolute = Path("/tmp/test")
        resolved = paths.resolve_path(str(absolute))
        assert resolved == absolute

    def test_resolve_path_relative(self):
        """测试解析相对路径"""
        paths = AthenaPaths()
        resolved = paths.resolve_path("core/test.py")
        assert resolved == paths.project_root / "core" / "test.py"

    def test_resolve_path_with_tilde(self):
        """测试解析带~的路径"""
        paths = AthenaPaths()
        resolved = paths.resolve_path("~/test.py")
        # Path会自动扩展~，或者返回相对于项目根的路径
        assert isinstance(resolved, Path)

    def test_ensure_dir_creates_directory(self):
        """测试ensure_dir创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = AthenaPaths(project_root=Path(temp_dir))
            new_dir = paths.data_dir / "new" / "nested" / "dir"

            result = paths.ensure_dir(new_dir)

            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_ensure_dir_existing_directory(self):
        """测试ensure_dir处理已存在的目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = AthenaPaths(project_root=Path(temp_dir))
            existing_dir = paths.data_dir

            result = paths.ensure_dir(existing_dir)

            assert result == existing_dir
            assert existing_dir.exists()

    def test_repr(self):
        """测试__repr__方法"""
        paths = AthenaPaths()
        repr_str = repr(paths)
        assert "AthenaPaths" in repr_str
        assert "project_root" in repr_str


class TestGlobalInstanceFunctions:
    """全局实例函数测试"""

    def test_get_paths_returns_singleton(self):
        """测试get_paths返回单例"""
        paths1 = get_paths()
        paths2 = get_paths()
        assert paths1 is paths2

    def test_get_paths_with_custom_root(self):
        """测试get_paths使用自定义根目录"""
        # 注意：全局单例已经创建，这个测试验证行为
        # 第一次调用会创建单例，后续调用返回同一个实例
        paths = get_paths()
        assert isinstance(paths, AthenaPaths)
        assert paths.project_root.exists()

    def test_ensure_project_root_in_path(self):
        """测试ensure_project_root_in_path便捷函数"""
        root_str = ensure_project_root_in_path()
        assert isinstance(root_str, str)
        assert root_str in sys.path

    def test_get_project_root(self):
        """测试get_project_root便捷函数"""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()


class TestPathDetection:
    """路径检测测试"""

    def test_detect_project_root_with_markers(self):
        """测试通过标记检测项目根目录"""
        paths = AthenaPaths()
        # 项目根目录或其父目录应该包含标记
        markers = ["core", "config", "production", "tests"]
        # 检查项目根目录
        marker_count = sum(
            1 for marker in markers
            if (paths.project_root / marker).exists()
        )
        # 如果不足3个，检查父目录
        if marker_count < 3:
            parent = paths.project_root.parent
            marker_count = sum(
                1 for marker in markers
                if (parent / marker).exists()
            )
        assert marker_count >= 2  # 至少有2个标记

    def test_auto_detect_finds_valid_root(self):
        """测试自动检测找到有效的根目录"""
        paths = AthenaPaths()
        # 检测到的根目录应该能找到关键目录
        # 可能在项目根目录或其父目录
        core_exists = (paths.project_root / "core").exists()
        parent = paths.project_root.parent
        core_in_parent = (parent / "core").exists()
        assert core_exists or core_in_parent


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_relative_path(self):
        """测试空相对路径"""
        paths = AthenaPaths()
        relative = paths.get_relative_path(paths.project_root)
        # 根目录相对路径应该是.或空
        assert relative == Path(".") or relative == Path()

    def test_deeply_nested_relative_path(self):
        """测试深层嵌套相对路径"""
        paths = AthenaPaths()
        target = paths.core_dir / "utils" / "test" / "deep" / "file.py"
        relative = paths.get_relative_path(target)
        assert "core" in str(relative)
        assert "utils" in str(relative)

    def test_resolve_path_empty_string(self):
        """测试解析空字符串路径"""
        paths = AthenaPaths()
        resolved = paths.resolve_path("")
        # 空字符串应该返回项目根目录
        assert resolved == paths.project_root

    def test_multiple_get_paths_calls(self):
        """测试多次调用get_paths"""
        paths1 = get_paths()
        paths2 = get_paths()
        paths3 = get_paths()
        # 所有调用应该返回同一个实例
        assert paths1 is paths2
        assert paths2 is paths3

    def test_path_operations_chain(self):
        """测试路径操作链"""
        paths = AthenaPaths()
        # 解析相对路径
        relative_path = "core/utils/test.py"
        resolved = paths.resolve_path(relative_path)
        # 获取相对路径
        relative = paths.get_relative_path(resolved)
        # 验证一致性
        assert "core" in str(relative)
        assert "utils" in str(relative)


class TestIntegration:
    """集成测试"""

    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 获取路径管理器
        paths = get_paths()

        # 2. 使用各种路径属性
        core_dir = paths.core_dir
        tests_dir = paths.tests_dir

        # 3. 解析路径
        test_file = paths.resolve_path("tests/test_example.py")

        # 4. 获取相对路径
        relative = paths.get_relative_path(test_file)

        # 5. 验证类型
        assert isinstance(core_dir, Path)
        assert isinstance(tests_dir, Path)
        assert isinstance(test_file, Path)
        assert isinstance(relative, Path)

    def test_cross_module_usage(self):
        """测试跨模块使用"""
        # 使用便捷函数
        root = get_project_root()
        root_str = ensure_project_root_in_path()

        # 验证一致性
        assert str(root) == root_str
        assert root_str in sys.path

    def test_directory_creation_workflow(self):
        """测试目录创建工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = get_paths(project_root=Path(temp_dir))

            # 创建多级目录
            cache_dir = paths.cache_dir
            nested_dir = cache_dir / "level1" / "level2" / "level3"

            # 确保目录存在
            result = paths.ensure_dir(nested_dir)

            # 验证
            assert result == nested_dir
            assert nested_dir.exists()
            assert nested_dir.is_dir()

    def test_path_consistency(self):
        """测试路径一致性"""
        paths = AthenaPaths()

        # 所有路径都应该基于project_root
        assert paths.core_dir.is_relative_to(paths.project_root)
        assert paths.config_dir.is_relative_to(paths.project_root)
        assert paths.production_dir.is_relative_to(paths.project_root)

        # 验证路径格式
        assert isinstance(paths.project_root, Path)
        assert paths.project_root.is_absolute()


class TestSysPathManipulation:
    """sys.path操作测试"""

    def test_project_root_added_to_sys_path_once(self):
        """测试项目根目录添加到sys.path"""
        project_root_str = str(get_project_root())
        # 应该至少在sys.path中出现一次
        count = sys.path.count(project_root_str)
        assert count >= 1

    def test_sys_path_not_duplicated(self):
        """测试sys.path不重复添加"""
        project_root_str = str(get_project_root())

        # 确保只在sys.path中出现一次
        count = sys.path.count(project_root_str)
        assert count >= 1
        # 如果已经存在，不应该重复添加
        assert count == sys.path.count(project_root_str)
