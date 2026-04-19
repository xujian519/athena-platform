#!/usr/bin/env python3
"""
专利全文处理系统 - 配置管理工具
Patent Full Text Processing System - Configuration Manager

管理环境配置、验证配置、切换环境

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import argparse
import os
import shutil
from pathlib import Path


class PatentConfigManager:
    """专利系统配置管理器"""

    def __init__(self, root_dir: Path | None = None):
        """
        初始化配置管理器

        Args:
            root_dir: 专利系统根目录
        """
        if root_dir is None:
            root_dir = Path(__file__).parent
        self.root_dir = Path(root_dir)
        self.config_dir = self.root_dir / "config"
        self.phase3_dir = self.root_dir / "phase3"

        # 环境配置
        self.env_files = {
            "production": self.config_dir / ".env",
            "development": self.config_dir / ".env.development",
            "testing": self.config_dir / ".env.testing",
            "template": self.config_dir / ".env.template"
        }

    def validate_config(self, env: str = "production") -> bool:
        """
        验证配置

        Args:
            env: 环境名称

        Returns:
            是否验证通过
        """
        print(f"\n{'='*60}")
        print(f"  验证配置: {env}")
        print(f"{'='*60}")

        env_file = self.env_files.get(env)
        if not env_file or not env_file.exists():
            print(f"❌ 配置文件不存在: {env_file}")
            return False

        # 加载环境变量
        env_vars = self._load_env_file(env_file)

        # 验证必需配置
        required_vars = [
            "PATENT_ENV",
            "PATENT_VERSION",
            "QDRANT_COLLECTION_NAME",
            "NEBULA_SPACE_NAME"
        ]

        missing_vars = []
        for var in required_vars:
            if var not in env_vars:
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ 缺少必需配置: {', '.join(missing_vars)}")
            return False

        # 验证路径
        paths_to_check = [
            ("ATHENA_HOME", env_vars.get("ATHENA_HOME")),
            ("PATENT_PDF_PATH", env_vars.get("PATENT_PDF_PATH")),
            ("PATENT_LOG_PATH", env_vars.get("PATENT_LOG_PATH"))
        ]

        print("\n📂 路径验证:")
        for name, path in paths_to_check:
            if path:
                path_obj = Path(path)
                exists = path_obj.exists()
                icon = "✅" if exists else "⚠️ "
                print(f"  {icon} {name}: {path}")
                if not exists and name == "PATENT_PDF_PATH":
                    print("      → 将自动创建")

        # 验证数据库配置
        print("\n🗄️  数据库配置:")
        print(f"  ✅ Qdrant: {env_vars.get('QDRANT_HOST')}:{env_vars.get('QDRANT_PORT')}")
        print(f"  ✅ Nebula: {env_vars.get('NEBULA_HOST')}:{env_vars.get('NEBULA_PORT')}")
        print(f"  ✅ Redis: {env_vars.get('REDIS_HOST')}:{env_vars.get('REDIS_PORT')}")

        # 验证模型配置
        print("\n🤖 模型配置:")
        print(f"  ✅ 向量化模型: {env_vars.get('PATENT_EMBEDDING_MODEL')}")
        print(f"  ✅ 序列标注模型: {env_vars.get('PATENT_SEQUENCE_TAGGER')}")

        # 验证处理配置
        print("\n⚙️  处理配置:")
        print(f"  ✅ 批量大小: {env_vars.get('PATENT_BATCH_SIZE')}")
        print(f"  ✅ 最大工作线程: {env_vars.get('PATENT_MAX_WORKERS')}")
        print(f"  ✅ 缓存TTL: {env_vars.get('PATENT_CACHE_TTL')}秒")

        print(f"\n✅ 配置验证通过: {env}")
        return True

    def switch_environment(self, env: str) -> bool:
        """
        切换环境

        Args:
            env: 目标环境

        Returns:
            是否切换成功
        """
        print(f"\n{'='*60}")
        print(f"  切换环境: {env}")
        print(f"{'='*60}")

        # 验证目标环境配置
        if not self.validate_config(env):
            return False

        # 复制环境配置
        target_env = self.env_files.get(env)
        if not target_env or not target_env.exists():
            print(f"❌ 目标环境配置不存在: {env}")
            return False

        # 创建 .env 文件链接/副本
        env_link = self.root_dir / ".env"
        if env_link.exists():
            env_link.unlink()

        shutil.copy(target_env, env_link)
        print(f"✅ 已切换到环境: {env}")
        print(f"   配置文件: {target_env}")

        return True

    def init_environment(self, env: str = "production") -> bool:
        """
        初始化环境

        Args:
            env: 环境名称

        Returns:
            是否初始化成功
        """
        print(f"\n{'='*60}")
        print(f"  初始化环境: {env}")
        print(f"{'='*60}")

        # 验证配置
        if not self.validate_config(env):
            return False

        # 切换环境
        if not self.switch_environment(env):
            return False

        # 创建必要目录
        env_vars = self._load_env_file(self.env_files[env])
        self._create_directories(env_vars)

        # 初始化NebulaGraph配置
        self._init_nebula_config()

        print(f"\n✅ 环境初始化完成: {env}")
        return True

    def show_config(self, env: str = "production") -> None:
        """
        显示配置

        Args:
            env: 环境名称
        """
        print(f"\n{'='*60}")
        print(f"  配置信息: {env}")
        print(f"{'='*60}")

        env_file = self.env_files.get(env)
        if not env_file or not env_file.exists():
            print(f"❌ 配置文件不存在: {env_file}")
            return

        env_vars = self._load_env_file(env_file)

        # 分组显示
        groups = {
            "环境标识": ["PATENT_ENV", "PATENT_VERSION"],
            "路径配置": ["ATHENA_HOME", "PATENT_PDF_PATH", "PATENT_LOG_PATH", "PATENT_MODEL_PATH"],
            "数据库配置": ["QDRANT_HOST", "QDRANT_PORT", "NEBULA_HOST", "NEBULA_PORT", "REDIS_HOST"],
            "模型配置": ["PATENT_EMBEDDING_MODEL", "PATENT_SEQUENCE_TAGGER"],
            "处理配置": ["PATENT_BATCH_SIZE", "PATENT_MAX_WORKERS", "PATENT_CACHE_TTL"],
            "API配置": ["PATENT_API_HOST", "PATENT_API_PORT", "PATENT_API_WORKERS"],
            "监控配置": ["PATENT_ENABLE_PERFORMANCE_MONITORING", "PATENT_ENABLE_HEALTH_CHECK"],
            "日志配置": ["PATENT_LOG_LEVEL", "PATENT_LOG_FORMAT"]
        }

        for group_name, vars_list in groups.items():
            print(f"\n📌 {group_name}:")
            for var_name in vars_list:
                value = env_vars.get(var_name, "")
                if value:
                    # 隐藏敏感信息
                    if "PASSWORD" in var_name or "SECRET" in var_name:
                        value = "***"
                    print(f"  {var_name}={value}")

    def _load_env_file(self, env_file: Path) -> dict[str, str]:
        """加载环境变量文件"""
        env_vars = {}
        if env_file.exists():
            with open(env_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 展开变量引用
                        value = os.path.expandvars(value)
                        env_vars[key.strip()] = value.strip()
        return env_vars

    def _create_directories(self, env_vars: dict[str, str]) -> None:
        """创建必要目录"""
        dirs_to_create = [
            env_vars.get("PATENT_PDF_PATH"),
            env_vars.get("PATENT_LOG_PATH"),
            env_vars.get("PATENT_CHECKPOINT_PATH"),
            env_vars.get("PATENT_MODEL_PATH")
        ]

        print("\n📁 创建目录:")
        for dir_path in dirs_to_create:
            if dir_path:
                dir_obj = Path(dir_path)
                try:
                    dir_obj.mkdir(parents=True, exist_ok=True)
                    print(f"  ✅ {dir_path}")
                except Exception as e:
                    print(f"  ❌ {dir_path}: {e}")

    def _init_nebula_config(self) -> None:
        """初始化NebulaGraph配置"""
        nebula_config_dir = self.root_dir / "config" / "nebula"
        nebula_config_dir.mkdir(parents=True, exist_ok=True)

        # 创建基础配置文件
        config_files = {
            "nebula-metad.conf": self._get_nebula_metad_config(),
            "nebula-storaged.conf": self._get_nebula_storaged_config(),
            "nebula-graphd.conf": self._get_nebula_graphd_config()
        }

        print("\n📝 创建NebulaGraph配置:")
        for filename, content in config_files.items():
            config_file = nebula_config_dir / filename
            if not config_file.exists():
                config_file.write_text(content, encoding='utf-8')
                print(f"  ✅ {filename}")

    def _get_nebula_metad_config(self) -> str:
        """获取Nebula Meta配置"""
        return """-- Meta服务配置
--meta_server_addrs=nebula-metad:9559
--local_ip=nebula-metad
--ws_ip=nebula-metad
--port=9559
--data_path=/data/meta
--log_dir=/logs
--v=2
"""

    def _get_nebula_storaged_config(self) -> str:
        """获取Nebula Storage配置"""
        return """-- Storage服务配置
--meta_server_addrs=nebula-metad:9559
--local_ip=nebula-storaged
--ws_ip=nebula-storaged
--port=9779
--data_path=/data/storage
--log_dir=/logs
--v=2
"""

    def _get_nebula_graphd_config(self) -> str:
        """获取Nebula Graph配置"""
        return """-- Graph服务配置
--meta_server_addrs=nebula-metad:9559
--local_ip=nebula-graphd
--ws_ip=nebula-graphd
--port=9669
--log_dir=/logs
--v=2
--enable_authority=true
"""


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="专利全文处理系统 - 配置管理工具"
    )
    parser.add_argument(
        "action",
        choices=["validate", "switch", "init", "show"],
        help="操作: validate(验证)/switch(切换)/init(初始化)/show(显示)"
    )
    parser.add_argument(
        "--env",
        choices=["production", "development", "testing"],
        default="production",
        help="环境名称"
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="专利系统根目录"
    )

    args = parser.parse_args()

    # 创建配置管理器
    manager = PatentConfigManager(root_dir=args.root)

    # 执行操作
    if args.action == "validate":
        manager.validate_config(args.env)
    elif args.action == "switch":
        manager.switch_environment(args.env)
    elif args.action == "init":
        manager.init_environment(args.env)
    elif args.action == "show":
        manager.show_config(args.env)


if __name__ == "__main__":
    main()
