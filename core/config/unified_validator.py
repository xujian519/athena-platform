"""
配置验证器（第2阶段重构版本）
Configuration Validator (Phase 2 Refactored Version)
"""
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional
from core.config.unified_settings import UnifiedSettings


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_settings(settings: UnifiedSettings) -> bool:
        """验证Settings实例

        Args:
            settings: UnifiedSettings实例

        Returns:
            验证是否通过
        """
        try:
            # 验证数据库端口
            if not 1 <= settings.database_port <= 65535:
                raise ValueError("database_port must be between 1 and 65535")

            # 验证Redis端口
            if not 1 <= settings.redis_port <= 65535:
                raise ValueError("redis_port must be between 1 and 65535")

            # 验证LLM温度
            if not 0 <= settings.llm_temperature <= 2:
                raise ValueError("llm_temperature must be between 0 and 2")

            # 生产环境需要验证密码
            if settings.environment == "production":
                if len(settings.database_password) < 8:
                    raise ValueError("Production environment requires password with at least 8 characters")

            return True

        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

    @staticmethod
    def validate_config_dict(config: Dict[str, Any]) -> bool:
        """验证配置字典

        Args:
            config: 配置字典

        Returns:
            验证是否通过
        """
        try:
            settings = UnifiedSettings.from_yaml_dict(config)
            return ConfigValidator.validate_settings(settings)
        except Exception as e:
            print(f"配置字典验证失败: {e}")
            return False


# 便捷函数
def validate_unified_settings(settings: Optional[UnifiedSettings] = None) -> bool:
    """验证配置

    Args:
        settings: UnifiedSettings实例，如果为None则使用全局实例

    Returns:
        验证是否通过
    """
    if settings is None:
        from core.config.unified_settings import unified_settings
        settings = unified_settings

    return ConfigValidator.validate_settings(settings)
