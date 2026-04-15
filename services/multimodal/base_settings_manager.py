#!/usr/bin/env python3
"""
Athena项目基础设置管理器
Base Settings Manager for Athena Project

统一管理所有多模态文件处理功能
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class BaseSettingsManager:
    """基础设置管理器"""

    def __init__(self):
        self.settings_dir = Path("/Users/xujian/Athena工作平台/config/multimodal")
        self.settings_file = self.settings_dir / "base_settings.json"

        # 确保设置目录存在
        self.settings_dir.mkdir(parents=True, exist_ok=True)

        # 加载设置
        self.settings = self._load_settings()

    def _load_settings(self) -> dict[str, Any]:
        """加载设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_settings()
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
            return self._get_default_settings()

    def _get_default_settings(self) -> dict[str, Any]:
        """获取默认设置"""
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),

            # 文件存储设置
            "storage": {
                "base_path": "/Users/xujian/Athena工作平台/storage-system/data/multimodal_files",
                "max_file_size": 100 * 1024 * 1024,  # 100MB
                "allowed_types": {
                    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
                    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf"],
                    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
                    "video": [".mp4", ".avi", ".mkv", ".mov", ".webm"],
                    "data": [".json", ".xml", ".csv", ".xlsx"],
                    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"]
                },
                "auto_cleanup": True,
                "cleanup_days": 30
            },

            # 处理设置
            "processing": {
                "auto_generate_thumbnails": True,
                "thumbnail_size": [200, 200],
                "extract_metadata": True,
                "virus_scan": False,  # 本地环境暂时关闭
                "content_analysis": True
            },

            # 缓存设置
            "cache": {
                "enable_redis": True,
                "redis_host": "localhost",
                "redis_port": 6379,
                "redis_db": 2,
                "cache_timeout": 3600,
                "local_cache_enabled": True
            },

            # AI处理设置
            "ai_processing": {
                "image_recognition": True,
                "document_parsing": True,
                "text_analysis": True,
                "similarity_detection": True,
                "auto_tagging": True,
                "confidence_threshold": 0.8
            },

            # API设置
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 1,
                "reload": True,
                "log_level": "INFO",
                "cors_origins": ["*"],
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 60
                }
            },

            # 安全设置
            "security": {
                "file_validation": True,
                "file_size_limits": True,
                "type_validation": True,
                "content_filtering": False,  # 本地环境暂时关闭
                "access_logging": True
            },

            # 监控设置
            "monitoring": {
                "enable_metrics": True,
                "log_requests": True,
                "performance_tracking": True,
                "error_reporting": True
            }
        }

    def save_settings(self) -> None:
        """保存设置"""
        try:
            self.settings["last_updated"] = datetime.now().isoformat()

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)

            logger.info("设置已保存")
            return True
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return False

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """获取设置值（支持点分割路径）"""
        keys = key_path.split('.')
        current = self.settings

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def update_setting(self, key_path: str, value: Any) -> None:
        """更新设置值"""
        keys = key_path.split('.')
        current = self.settings

        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 设置值
        current[keys[-1]] = value

        # 保存设置
        return self.save_settings()

    def get_storage_config(self) -> dict[str, Any]:
        """获取存储配置"""
        return self.get_setting("storage", {})

    def get_processing_config(self) -> dict[str, Any]:
        """获取处理配置"""
        return self.get_setting("processing", {})

    def get_cache_config(self) -> dict[str, Any]:
        """获取缓存配置"""
        return self.get_setting("cache", {})

    def get_ai_config(self) -> dict[str, Any]:
        """获取AI处理配置"""
        return self.get_setting("ai_processing", {})

    def get_api_config(self) -> dict[str, Any]:
        """获取API配置"""
        return self.get_setting("api", {})

    def get_security_config(self) -> dict[str, Any]:
        """获取安全配置"""
        return self.get_setting("security", {})

    def is_file_type_allowed(self, file_path: str) -> bool:
        """检查文件类型是否允许"""
        file_ext = Path(file_path).suffix.lower()
        allowed_types = self.get_setting("storage.allowed_types", {})

        for _file_type, extensions in allowed_types.items():
            if file_ext in extensions:
                return True

        return False

    def get_max_file_size(self) -> int:
        """获取最大文件大小"""
        return self.get_setting("storage.max_file_size", 100 * 1024 * 1024)

    def validate_file(self, file_path: str, file_size: int) -> dict[str, Any]:
        """验证文件"""
        validation_result = {
            "valid": True,
            "errors": []
        }

        # 检查文件类型
        if not self.is_file_type_allowed(file_path):
            validation_result["valid"] = False
            validation_result["errors"].append("不支持的文件类型")

        # 检查文件大小
        max_size = self.get_max_file_size()
        if file_size > max_size:
            validation_result["valid"] = False
            validation_result["errors"].append(f"文件大小超出限制 ({max_size / (1024*1024):.1f}MB)")

        return validation_result

    def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        try:
            # 检查存储路径
            storage_path = self.get_setting("storage.base_path")
            storage_exists = os.path.exists(storage_path) if storage_path else False

            # 检查Redis连接
            cache_config = self.get_cache_config()
            redis_status = "disabled"
            if cache_config.get("enable_redis", False):
                try:
                    import redis
                    r = redis.Redis(
                        host=cache_config.get("redis_host", "localhost"),
                        port=cache_config.get("redis_port", 6379),
                        db=cache_config.get("redis_db", 2)
                    )
                    r.ping()
                    redis_status = "connected"
                except (FileNotFoundError, PermissionError, OSError):
                    redis_status = "disconnected"

            # 检查AI服务
            ai_config = self.get_ai_config()
            ai_services = []
            if ai_config.get("image_recognition", False):
                ai_services.append("图像识别")
            if ai_config.get("document_parsing", False):
                ai_services.append("文档解析")
            if ai_config.get("text_analysis", False):
                ai_services.append("文本分析")

            return {
                "storage_status": "available" if storage_exists else "unavailable",
                "storage_path": storage_path,
                "cache_status": redis_status,
                "ai_services": ai_services,
                "settings_version": self.get_setting("version"),
                "last_updated": self.get_setting("last_updated")
            }

        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return {"error": str(e)}

    def export_settings(self, export_path: str | None = None) -> str:
        """导出设置"""
        if export_path is None:
            export_path = self.settings_dir / f"settings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)

            logger.info(f"设置已导出到: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"导出设置失败: {e}")
            return ""

    def import_settings(self, import_path: str) -> bool:
        """导入设置"""
        try:
            with open(import_path, encoding='utf-8') as f:
                imported_settings = json.load(f)

            # 合并设置，保留当前版本信息
            current_version = self.get_setting("version")
            self.settings = {
                "version": current_version,
                "imported_at": datetime.now().isoformat(),
                **imported_settings
            }

            return self.save_settings()
        except Exception as e:
            logger.error(f"导入设置失败: {e}")
            return False

# 全局设置管理器实例
settings_manager = BaseSettingsManager()

def get_settings_manager() -> BaseSettingsManager:
    """获取设置管理器实例"""
    return settings_manager

# 使用示例
if __name__ == "__main__":
    manager = get_settings_manager()

    # 显示服务状态
    status = manager.get_service_status()
    print("=== 服务状态 ===")
    for key, value in status.items():
        print(f"{key}: {value}")

    # 显示一些配置
    print("\n=== 配置信息 ===")
    print(f"最大文件大小: {manager.get_max_file_size() / (1024*1024):.1f}MB")
    print(f"自动生成缩略图: {manager.get_setting('processing.auto_generate_thumbnails')}")
    print(f"Redis缓存: {manager.get_setting('cache.enable_redis')}")
