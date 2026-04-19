#!/usr/bin/env python3
"""
API密钥配置管理器
API Key Configuration Manager

安全管理和加载各种搜索引擎的API密钥

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self, config_file: str | None = None):
        """
        初始化API密钥管理器

        Args:
            config_file: 配置文件路径,默认使用项目根目录下的配置文件
        """
        if config_file is None:
            # 默认配置文件路径
            current_dir = Path(__file__).parent
            config_file = current_dir / "search_api_config.json"

        self.config_file = Path(config_file)
        self.config_data: dict[str, Any] = {}
        self.encrypted_fields = ["api_key", "search_engine_id"]

        # 加载配置
        self.load_config()

    def load_config(self) -> bool:
        """
        加载配置文件

        Returns:
            bool: 加载是否成功
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    self.config_data = json.load(f)
                logger.info(f"✅ 成功加载API配置: {self.config_file}")
            else:
                logger.warning(f"⚠️ 配置文件不存在,创建默认配置: {self.config_file}")
                self.config_data = self._create_default_config()
                self.save_config()

            return True

        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            self.config_data = self._create_default_config()
            return False

    def save_config(self) -> bool:
        """
        保存配置文件

        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 更新时间戳
            self.config_data["last_updated"] = datetime.now().isoformat()

            # 写入文件
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 成功保存API配置: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存配置失败: {e}")
            return False

    def get_api_key(self, service: str, prefer_backup: bool = False) -> str | None:
        """
        获取API密钥

        Args:
            service: 服务名称
            prefer_backup: 是否优先使用备用密钥

        Returns:
            Optional[str]: API密钥,如果不存在或未启用则返回None
        """
        try:
            service_config = self.config_data.get("search_api_keys", {}).get(service, {})

            if not service_config.get("enabled", False):
                logger.debug(f"🔒 服务 {service} 未启用")
                return None

            # 优先选择主密钥或备用密钥
            if prefer_backup:
                api_key = service_config.get("backup_api_key") or service_config.get("api_key", "")
            else:
                api_key = service_config.get("api_key") or service_config.get("backup_api_key", "")

            if not api_key:
                logger.warning(f"⚠️ 服务 {service} 启用但未配置API密钥")
                return None

            return api_key

        except Exception as e:
            logger.error(f"❌ 获取API密钥失败: {e}")
            return None

    def get_all_api_keys(self, service: str) -> list[str]:
        """
        获取所有API密钥(用于轮换)

        Args:
            service: 服务名称

        Returns:
            list[str]: 所有可用的API密钥列表
        """
        try:
            service_config = self.config_data.get("search_api_keys", {}).get(service, {})

            if not service_config.get("enabled", False):
                return []

            keys = []
            primary_key = service_config.get("api_key")
            backup_key = service_config.get("backup_api_key")

            if primary_key:
                keys.append(primary_key)
            if backup_key and backup_key != primary_key:
                keys.append(backup_key)

            return keys

        except Exception as e:
            logger.error(f"❌ 获取API密钥列表失败: {e}")
            return []

    def get_service_config(self, service: str) -> dict[str, Any]:
        """
        获取服务完整配置

        Args:
            service: 服务名称

        Returns:
            dict[str, Any]: 服务配置
        """
        return self.config_data.get("search_api_keys", {}).get(service, {})

    def get_enabled_services(self) -> list[str]:
        """
        获取所有启用的服务

        Returns:
            list[str]: 启用的服务名称列表
        """
        enabled_services = []
        api_keys = self.config_data.get("search_api_keys", {})

        for service, config in api_keys.items():
            if config.get("enabled", False) and config.get("api_key"):
                enabled_services.append(service)

        return enabled_services

    def update_api_key(self, service: str, api_key: str, **kwargs) -> bool:
        """
        更新API密钥

        Args:
            service: 服务名称
            api_key: API密钥
            **kwargs: 其他配置参数

        Returns:
            bool: 更新是否成功
        """
        try:
            if "search_api_keys" not in self.config_data:
                self.config_data["search_api_keys"] = {}

            if service not in self.config_data["search_api_keys"]:
                self.config_data["search_api_keys"][service] = {
                    "description": f"{service} API密钥",
                    "enabled": False,
                    "rate_limit": {},
                }

            # 更新配置
            self.config_data["search_api_keys"][service]["api_key"] = api_key
            self.config_data["search_api_keys"][service]["enabled"] = True

            # 更新其他参数
            for key, value in kwargs.items():
                self.config_data["search_api_keys"][service][key] = value

            logger.info(f"✅ 成功更新 {service} API密钥")
            return self.save_config()

        except Exception as e:
            logger.error(f"❌ 更新API密钥失败: {e}")
            return False

    def enable_service(self, service: str, enabled: bool = True) -> bool:
        """
        启用或禁用服务

        Args:
            service: 服务名称
            enabled: 是否启用

        Returns:
            bool: 操作是否成功
        """
        try:
            if service in self.config_data.get("search_api_keys", {}):
                self.config_data["search_api_keys"][service]["enabled"] = enabled
                logger.info(f"✅ {'启用' if enabled else '禁用'} 服务: {service}")
                return self.save_config()
            else:
                logger.warning(f"⚠️ 服务不存在: {service}")
                return False

        except Exception as e:
            logger.error(f"❌ {'启用' if enabled else '禁用'}服务失败: {e}")
            return False

    def get_patent_config(self) -> dict[str, Any]:
        """
        获取专利搜索配置

        Returns:
            dict[str, Any]: 专利搜索配置
        """
        return self.config_data.get("patent_search_config", {})

    def get_system_settings(self) -> dict[str, Any]:
        """
        获取系统设置

        Returns:
            dict[str, Any]: 系统设置
        """
        return self.config_data.get("system_settings", {})

    def validate_service(self, service: str) -> dict[str, Any]:
        """
        验证服务配置

        Args:
            service: 服务名称

        Returns:
            dict[str, Any]: 验证结果
        """
        result = {
            "service": service,
            "valid": False,
            "enabled": False,
            "has_api_key": False,
            "issues": [],
        }

        try:
            service_config = self.get_service_config(service)

            if not service_config:
                result["issues"].append("服务配置不存在")
                return result

            # 检查启用状态
            enabled = service_config.get("enabled", False)
            result["enabled"] = enabled

            if not enabled:
                result["issues"].append("服务未启用")
                return result

            # 检查API密钥
            api_key = service_config.get("api_key", "")
            result["has_api_key"] = bool(api_key)

            if not api_key:
                result["issues"].append("缺少API密钥")
                return result

            # 特殊检查:Google Custom Search需要search_engine_id
            if service == "google_custom_search":
                search_engine_id = service_config.get("search_engine_id", "")
                if not search_engine_id:
                    result["issues"].append("缺少搜索引擎ID")
                    return result

            # 通过所有检查
            result["valid"] = True
            logger.info(f"✅ 服务 {service} 配置有效")

        except Exception as e:
            logger.error(f"❌ 验证服务配置失败: {e}")
            result["issues"].append(f"验证异常: {e!s}")

        return result

    def get_validation_report(self) -> dict[str, Any]:
        """
        获取所有服务的验证报告

        Returns:
            dict[str, Any]: 验证报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_services": 0,
            "valid_services": 0,
            "enabled_services": 0,
            "service_details": {},
        }

        api_keys = self.config_data.get("search_api_keys", {})
        report["total_services"] = len(api_keys)

        for service in api_keys:
            validation = self.validate_service(service)
            report["service_details"][service] = validation

            if validation["enabled"]:
                report["enabled_services"] += 1

            if validation["valid"]:
                report["valid_services"] += 1

        return report

    def _create_default_config(self) -> dict[str, Any]:
        """创建默认配置"""
        return {
            "search_api_keys": {
                "tavily": {
                    "api_key": "",
                    "description": "Tavily AI搜索引擎API密钥",
                    "enabled": False,
                    "rate_limit": {"requests_per_minute": 60, "requests_per_month": 1000},
                },
                "google_custom_search": {
                    "api_key": "",
                    "search_engine_id": "",
                    "description": "Google自定义搜索引擎API密钥",
                    "enabled": False,
                    "rate_limit": {"requests_per_day": 100, "requests_per_month": 3000},
                },
                "bocha": {
                    "api_key": "",
                    "description": "Bocha AI搜索引擎API密钥",
                    "enabled": False,
                    "rate_limit": {"requests_per_minute": 20, "requests_per_month": 500},
                },
            },
            "patent_search_config": {
                "use_official_sources": True,
                "use_dads_enhancement": True,
                "guarantee_stability": True,
            },
            "system_settings": {
                "enable_fallback": True,
                "cache_enabled": True,
                "max_concurrent_requests": 10,
            },
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0",
        }

    def export_template(self, file_path: str = "api_key_template.json") -> bool:
        """
        导出配置模板(不包含实际API密钥)

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 导出是否成功
        """
        try:
            template = self._create_default_config()

            # 清空所有API密钥
            for service in template.get("search_api_keys", {}).values():
                if "api_key" in service:
                    service["api_key"] = ""
                if "search_engine_id" in service:
                    service["search_engine_id"] = ""

            # 写入模板文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 成功导出配置模板: {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 导出配置模板失败: {e}")
            return False


# 全局实例
_api_key_manager_instance: APIKeyManager | None = None


def get_api_key_manager() -> APIKeyManager:
    """
    获取全局API密钥管理器实例

    Returns:
        APIKeyManager: 全局实例
    """
    global _api_key_manager_instance
    if _api_key_manager_instance is None:
        _api_key_manager_instance = APIKeyManager()
    return _api_key_manager_instance


if __name__ == "__main__":
    # 示例用法
    manager = get_api_key_manager()

    logger.info("🔑 API密钥管理器")
    logger.info(f"配置文件: {manager.config_file}")
    logger.info(f"启用的服务: {manager.get_enabled_services()}")

    # 验证报告
    report = manager.get_validation_report()
    logger.info("\n📊 验证报告:")
    logger.info(f"总服务数: {report['total_services']}")
    logger.info(f"有效服务数: {report['valid_services']}")
    logger.info(f"启用服务数: {report['enabled_services']}")
