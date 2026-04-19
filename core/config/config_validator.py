#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台配置验证器
Configuration Validator for Athena Platform

创建时间: 2025-12-29
功能: 验证配置的完整性和正确性
"""

import os
import re
import socket
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ValidationLevel(Enum):
    """验证级别"""

    ERROR = "ERROR"  # 严重错误,必须修复
    WARNING = "WARNING"  # 警告,建议修复
    INFO = "INFO"  # 信息,仅供参考


@dataclass
class ValidationResult:
    """验证结果"""

    level: ValidationLevel
    category: str  # 验证类别
    item: str  # 验证项
    message: str  # 验证消息
    suggestion: str | None = None  # 修复建议

    def __str__(self) -> str:
        prefix = {
            ValidationLevel.ERROR: "❌",
            ValidationLevel.WARNING: "⚠️ ",
            ValidationLevel.INFO: "ℹ️ ",
        }[self.level]

        result = f"{prefix} [{self.category}] {self.item}: {self.message}"
        if self.suggestion:
            result += f"\n   建议: {self.suggestion}"
        return result


class ConfigValidator:
    """配置验证器"""

    # 必需的配置项
    REQUIRED_CONFIGS = {
        "platform.name": str,
        "platform.version": str,
        "platform.environment": str,
        "logging.level": str,
        "api.host": str,
        "api.port": int,
        "database.postgres.host": str,
        "database.postgres.port": int,
        "database.postgres.user": str,
        "database.postgres.password": str,
        "database.postgres.database": str,
        "database.postgres.pool_size": int,
        "redis.host": str,
        "redis.port": int,
        "database.qdrant.host": str,
        "database.qdrant.port": int,
        "models.embedding.model": str,
        "security.jwt.secret": str,
    }

    # 环境变量前缀映射
    ENV_PREFIX_MAPPINGS = {
        "POSTGRES_": "database.postgres.",
        "QDRANT_": "database.qdrant.",
        "REDIS_": "database.redis.",
        "NEBULA_": "database.nebula.",
        "LLM_": "models.llm.",
        "EMBEDDING_": "models.embedding.",
        "JWT_": "security.jwt.",
        "API_": "api.",
        "LOG_": "logging.",
    }

    # 端口范围
    PORT_RANGE = (1024, 65535)

    # 常用保留端口
    RESERVED_PORTS = {3306, 5432, 6379, 6333, 27017, 9090, 3000, 8080, 8000, 5000}

    def __init__(self, config: dict[str, Any]):
        """
        初始化验证器

        Args:
            config: 配置字典
        """
        self.config = self._expand_env_vars(config)
        self.results: list[ValidationResult] = []

    def _expand_env_vars(self, data: Any) -> Any:
        """
        递归展开环境变量占位符

        Args:
            data: 配置数据(可以是dict、list或基本类型)

        Returns:
            展开后的数据
        """
        if isinstance(data, dict):
            return {k: self._expand_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_env_vars(item) for item in data]
        elif isinstance(data, str):
            # 处理 ${VAR:default} 格式(允许前后有其他内容)
            def replace_env_var(match) -> None:
                env_var, default = match.groups()
                value = os.getenv(env_var)
                if value is not None:
                    return value
                return default if default is not None else match.group(0)

            # 替换所有环境变量占位符
            expanded = re.sub(r"\$\{([^:}]+)(?::([^}]*))?\}", replace_env_var, data)
            # 如果整个值都是占位符,尝试类型转换
            if expanded != data and "${" not in expanded:
                return self._convert_type(expanded)
            return expanded
        else:
            return data

    def _convert_type(self, value: str) -> Any:
        """自动类型转换"""
        # 布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 数字
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # 字符串
        return value

    def validate_all(self) -> list[ValidationResult]:
        """
        执行所有验证

        Returns:
            验证结果列表
        """
        self.results = []

        # 1. 必需配置检查
        self._validate_required_configs()

        # 2. 数据类型检查
        self._validate_types()

        # 3. 范围检查
        self._validate_ranges()

        # 4. 连接检查
        self._validate_connections()

        # 5. 安全检查
        self._validate_security()

        # 6. 路径检查
        self._validate_paths()

        # 7. 环境一致性检查
        self._validate_environment_consistency()

        return self.results

    def _add_result(
        self,
        level: ValidationLevel,
        category: str,
        item: str,
        message: str,
        suggestion: str | None = None,
    ) -> None:
        """添加验证结果"""
        self.results.append(
            ValidationResult(
                level=level, category=category, item=item, message=message, suggestion=suggestion
            )
        )

    def _get_nested_value(self, key_path: str) -> Any | None:
        """
        获取嵌套配置值

        Args:
            key_path: 配置键路径(如 "database.postgres.host")

        Returns:
            配置值,如果不存在返回None
        """
        keys = key_path.split(".")
        current = self.config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _validate_required_configs(self) -> None:
        """验证必需配置"""
        for key_path, expected_type in self.REQUIRED_CONFIGS.items():
            value = self._get_nested_value(key_path)

            if value is None:
                self._add_result(
                    level=ValidationLevel.ERROR,
                    category="必需配置",
                    item=key_path,
                    message="缺少必需配置项",
                    suggestion=f"在配置文件中添加 {key_path}",
                )
            elif not isinstance(value, expected_type):
                self._add_result(
                    level=ValidationLevel.ERROR,
                    category="类型检查",
                    item=key_path,
                    message=f"类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}",
                    suggestion=f"将 {key_path} 的值转换为 {expected_type.__name__}",
                )

    def _validate_types(self) -> None:
        """验证数据类型"""
        # 端口号必须是整数
        for port_key in [
            "api.port",
            "database.postgres.port",
            "database.redis.port",
            "database.qdrant.port",
            "monitoring.metrics_port",
        ]:
            value = self._get_nested_value(port_key)
            if value is not None and not isinstance(value, int):
                try:
                    int(value)
                except (ValueError, TypeError):
                    self._add_result(
                        level=ValidationLevel.ERROR,
                        category="类型检查",
                        item=port_key,
                        message="端口必须是整数",
                        suggestion=f"将 {port_key} 设置为整数值",
                    )

        # 布尔值检查
        for bool_key in ["platform.debug", "api.reload", "monitoring.enabled"]:
            value = self._get_nested_value(bool_key)
            if value is not None and not isinstance(value, bool):
                if not isinstance(value, str) or value.lower() not in ("true", "false"):
                    self._add_result(
                        level=ValidationLevel.WARNING,
                        category="类型检查",
                        item=bool_key,
                        message="布尔值格式不正确",
                        suggestion=f"将 {bool_key} 设置为 true 或 false",
                    )

    def _validate_ranges(self) -> None:
        """验证值范围"""
        # 端口范围检查
        port_keys = [
            "api.port",
            "database.postgres.port",
            "database.redis.port",
            "database.qdrant.port",
            "monitoring.metrics_port",
        ]

        for port_key in port_keys:
            value = self._get_nested_value(port_key)
            if value is not None:
                try:
                    port = int(value)
                    if not (self.PORT_RANGE[0] <= port <= self.PORT_RANGE[1]):
                        self._add_result(
                            level=ValidationLevel.ERROR,
                            category="范围检查",
                            item=port_key,
                            message=f"端口 {port} 超出范围 {self.PORT_RANGE}",
                            suggestion=f"将端口设置为 {self.PORT_RANGE[0]}-{self.PORT_RANGE[1]} 之间的值",
                        )

                    # 检查端口冲突
                    if port in self.RESERVED_PORTS and port_key != "database.postgres.port":
                        self._add_result(
                            level=ValidationLevel.WARNING,
                            category="端口冲突",
                            item=port_key,
                            message=f"端口 {port} 是常用保留端口",
                            suggestion="考虑使用其他端口避免冲突",
                        )
                except (ValueError, TypeError):
                    pass

        # 连接池大小检查
        pool_size = self._get_nested_value("database.postgres.pool_size")
        if pool_size is not None:
            try:
                size = int(pool_size)
                if size < 1:
                    self._add_result(
                        level=ValidationLevel.ERROR,
                        category="范围检查",
                        item="database.postgres.pool_size",
                        message="连接池大小必须大于0",
                        suggestion="将 pool_size 设置为至少 1",
                    )
                elif size > 100:
                    self._add_result(
                        level=ValidationLevel.WARNING,
                        category="范围检查",
                        item="database.postgres.pool_size",
                        message=f"连接池大小 {size} 过大",
                        suggestion="考虑设置为 10-50 之间的值",
                    )
            except (ValueError, TypeError):
                pass

        # 工作进程数检查
        workers = self._get_nested_value("api.workers")
        if workers is not None:
            try:
                worker_count = int(workers)
                cpu_count = os.cpu_count() or 1

                if worker_count < 1:
                    self._add_result(
                        level=ValidationLevel.ERROR,
                        category="范围检查",
                        item="api.workers",
                        message="工作进程数必须大于0",
                        suggestion="将 workers 设置为至少 1",
                    )
                elif worker_count > cpu_count * 2:
                    self._add_result(
                        level=ValidationLevel.WARNING,
                        category="范围检查",
                        item="api.workers",
                        message=f"工作进程数 {worker_count} 超过CPU核心数的2倍 (CPU: {cpu_count})",
                        suggestion=f"建议设置为 CPU核心数的1-2倍 (当前: {cpu_count})",
                    )
            except (ValueError, TypeError):
                pass

        # LLM温度参数检查
        temperature = self._get_nested_value("models.llm.temperature")
        if temperature is not None:
            try:
                temp = float(temperature)
                if not (0.0 <= temp <= 2.0):
                    self._add_result(
                        level=ValidationLevel.WARNING,
                        category="范围检查",
                        item="models.llm.temperature",
                        message=f"温度参数 {temp} 超出推荐范围 [0.0, 2.0]",
                        suggestion="将温度设置为 0.0-2.0 之间的值 (0=确定, 1=平衡, 2=创造)",
                    )
            except (ValueError, TypeError):
                pass

    def _validate_connections(self) -> None:
        """验证连接配置"""
        # PostgreSQL连接
        postgres_host = self._get_nested_value("database.postgres.host")
        postgres_port = self._get_nested_value("database.postgres.port")

        if postgres_host and postgres_port:
            if self._check_port_open(postgres_host, int(postgres_port)):
                self._add_result(
                    level=ValidationLevel.INFO,
                    category="连接检查",
                    item="database.postgres",
                    message=f"PostgreSQL 连接可用: {postgres_host}:{postgres_port}",
                    suggestion=None,
                )
            else:
                self._add_result(
                    level=ValidationLevel.WARNING,
                    category="连接检查",
                    item="database.postgres",
                    message=f"无法连接到 PostgreSQL: {postgres_host}:{postgres_port}",
                    suggestion="检查PostgreSQL服务是否运行,或检查主机/端口配置",
                )

        # Redis连接
        redis_host = self._get_nested_value("redis.host")
        redis_port = self._get_nested_value("redis.port")

        if redis_host and redis_port:
            if self._check_port_open(redis_host, int(redis_port)):
                self._add_result(
                    level=ValidationLevel.INFO,
                    category="连接检查",
                    item="redis",
                    message=f"Redis 连接可用: {redis_host}:{redis_port}",
                    suggestion=None,
                )
            else:
                self._add_result(
                    level=ValidationLevel.WARNING,
                    category="连接检查",
                    item="redis",
                    message=f"无法连接到 Redis: {redis_host}:{redis_port}",
                    suggestion="检查Redis服务是否运行,或检查主机/端口配置",
                )

        # Qdrant连接
        qdrant_host = self._get_nested_value("database.qdrant.host")
        qdrant_port = self._get_nested_value("database.qdrant.port")

        if qdrant_host and qdrant_port:
            if self._check_port_open(qdrant_host, int(qdrant_port)):
                self._add_result(
                    level=ValidationLevel.INFO,
                    category="连接检查",
                    item="database.qdrant",
                    message=f"Qdrant 连接可用: {qdrant_host}:{qdrant_port}",
                    suggestion=None,
                )
            else:
                self._add_result(
                    level=ValidationLevel.WARNING,
                    category="连接检查",
                    item="database.qdrant",
                    message=f"无法连接到 Qdrant: {qdrant_host}:{qdrant_port}",
                    suggestion="检查Qdrant服务是否运行,或检查主机/端口配置",
                )

    def _validate_security(self) -> None:
        """验证安全配置"""
        # JWT密钥强度
        jwt_secret = self._get_nested_value("security.jwt.secret")
        if jwt_secret:
            if len(jwt_secret) < 32:
                self._add_result(
                    level=ValidationLevel.ERROR,
                    category="安全检查",
                    item="security.jwt.secret",
                    message=f"JWT密钥长度不足: {len(jwt_secret)} 字符",
                    suggestion="使用至少32个字符的强随机密钥",
                )
            elif jwt_secret in ["changeme", "changeme-secret-key", "secret", "test-secret"]:
                self._add_result(
                    level=ValidationLevel.ERROR,
                    category="安全检查",
                    item="security.jwt.secret",
                    message="JWT密钥使用了默认值,存在安全风险",
                    suggestion="在生产环境中使用强随机密钥",
                )

        # 密码强度检查
        passwords = {
            "database.postgres.password": self._get_nested_value("database.postgres.password"),
            "database.redis.password": self._get_nested_value("database.redis.password"),
        }

        for key, password in passwords.items():
            if password:
                if len(password) < 8:
                    self._add_result(
                        level=ValidationLevel.WARNING,
                        category="安全检查",
                        item=key,
                        message=f"密码长度不足: {len(password)} 字符",
                        suggestion="使用至少8个字符的强密码",
                    )
                elif password in ["changeme", "password", "123456", "admin"]:
                    self._add_result(
                        level=ValidationLevel.ERROR,
                        category="安全检查",
                        item=key,
                        message="密码使用了弱值,存在安全风险",
                        suggestion="使用强随机密码",
                    )

        # HTTPS配置
        ssl_enabled = self._get_nested_value("security.ssl.enabled")
        environment = self._get_nested_value("platform.environment")

        if environment == "production" and not ssl_enabled:
            self._add_result(
                level=ValidationLevel.WARNING,
                category="安全检查",
                item="security.ssl.enabled",
                message="生产环境未启用HTTPS",
                suggestion="在生产环境中启用SSL/TLS加密",
            )

    def _validate_paths(self) -> None:
        """验证路径配置"""
        path_keys = [
            "logging.path",
            "storage.local.path",
            "storage.temp.path",
            "storage.upload.path",
        ]

        for key in path_keys:
            path = self._get_nested_value(key)
            if path:
                # 展开环境变量
                path = os.path.expandvars(path)

                # 检查路径是否可写
                path_obj = Path(path)
                try:
                    if path_obj.exists():
                        if not os.access(path_obj, os.W_OK):
                            self._add_result(
                                level=ValidationLevel.ERROR,
                                category="路径检查",
                                item=key,
                                message=f"路径不可写: {path}",
                                suggestion=f"检查目录权限或创建目录: mkdir -p {path}",
                            )
                    else:
                        # 尝试创建目录
                        try:
                            path_obj.mkdir(parents=True, exist_ok=True)
                            self._add_result(
                                level=ValidationLevel.INFO,
                                category="路径检查",
                                item=key,
                                message=f"已创建目录: {path}",
                                suggestion=None,
                            )
                        except Exception:
                            self._add_result(
                                level=ValidationLevel.ERROR,
                                category="路径检查",
                                item=key,
                                message=f"无法创建目录: {path}",
                                suggestion=f"手动创建目录并设置权限: mkdir -p {path} && chmod 755 {path}",
                            )
                except Exception as e:
                    self._add_result(
                        level=ValidationLevel.WARNING,
                        category="路径检查",
                        item=key,
                        message=f"路径验证失败: {e}",
                        suggestion=f"检查路径配置: {path}",
                    )

    def _validate_environment_consistency(self) -> None:
        """验证环境一致性"""
        environment = self._get_nested_value("platform.environment")

        if not environment:
            return

        # 开发环境检查
        if environment == "development":
            debug = self._get_nested_value("platform.debug")
            if not debug:
                self._add_result(
                    level=ValidationLevel.WARNING,
                    category="环境一致性",
                    item="platform.debug",
                    message="开发环境建议启用调试模式",
                    suggestion="将 platform.debug 设置为 true",
                )

            reload = self._get_nested_value("api.reload")
            if not reload:
                self._add_result(
                    level=ValidationLevel.INFO,
                    category="环境一致性",
                    item="api.reload",
                    message="开发环境可以启用热重载",
                    suggestion="将 api.reload 设置为 true 以获得更好的开发体验",
                )

        # 生产环境检查
        elif environment == "production":
            debug = self._get_nested_value("platform.debug")
            if debug:
                self._add_result(
                    level=ValidationLevel.ERROR,
                    category="环境一致性",
                    item="platform.debug",
                    message="生产环境不应启用调试模式",
                    suggestion="将 platform.debug 设置为 false",
                )

            log_level = self._get_nested_value("logging.level")
            if log_level and log_level.lower() == "debug":
                self._add_result(
                    level=ValidationLevel.WARNING,
                    category="环境一致性",
                    item="logging.level",
                    message="生产环境不建议使用DEBUG日志级别",
                    suggestion="将 logging.level 设置为 INFO 或 WARNING",
                )

    def _check_port_open(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """
        检查端口是否开放

        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间

        Returns:
            端口是否开放
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_summary(self) -> dict[str, int]:
        """
        获取验证摘要

        Returns:
            各级别的结果数量
        """
        summary = {
            ValidationLevel.ERROR.value: 0,
            ValidationLevel.WARNING.value: 0,
            ValidationLevel.INFO.value: 0,
        }

        for result in self.results:
            summary[result.level.value] += 1

        return summary

    def print_results(self) -> None:
        """打印验证结果"""
        if not self.results:
            print("✅ 配置验证通过,未发现问题")
            return

        # 按级别分组
        by_level = {
            ValidationLevel.ERROR: [],
            ValidationLevel.WARNING: [],
            ValidationLevel.INFO: [],
        }

        for result in self.results:
            by_level[result.level].append(result)

        # 打印结果
        for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
            results = by_level[level]
            if results:
                print(f"\n{'='*60}")
                print(f"{level.value} ({len(results)} 项)")
                print("=" * 60)

                for result in results:
                    print(f"\n{result}")

        # 打印摘要
        print(f"\n{'='*60}")
        print("验证摘要")
        print("=" * 60)
        summary = self.get_summary()
        print(f"❌ 错误: {summary[ValidationLevel.ERROR.value]}")
        print(f"⚠️  警告: {summary[ValidationLevel.WARNING.value]}")
        print(f"ℹ️  信息: {summary[ValidationLevel.INFO.value]}")

        # 判断是否通过
        if summary[ValidationLevel.ERROR.value] == 0:
            print("\n✅ 配置验证通过")
        else:
            print(f"\n❌ 配置验证失败: 发现 {summary[ValidationLevel.ERROR.value]} 个错误需要修复")


def validate_config_file(config_path: Path) -> bool:
    """
    验证配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        是否验证通过
    """
    import yaml

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    validator = ConfigValidator(config)
    validator.validate_all()
    validator.print_results()

    return validator.get_summary()[ValidationLevel.ERROR.value] == 0


def main() -> None:
    """主函数"""
    import sys

    # 默认验证base.yaml
    config_path = Path(__file__).parent.parent.parent / "config" / "unified" / "base.yaml"

    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])

    print(f"🔍 验证配置文件: {config_path}")
    print("=" * 60)

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    success = validate_config_file(config_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
