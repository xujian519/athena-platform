#!/usr/bin/env python3
"""
智能体身份信息管理器单元测试
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.utils.agent_identity_manager import (
    AgentIdentityManager,
    display_identity,
    get_service_info,
    identity_manager,
)


class TestAgentIdentityManagerInit:
    """AgentIdentityManager初始化测试"""

    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        manager = AgentIdentityManager()
        assert manager.config_path is not None
        assert isinstance(manager.identity_config, dict)

    def test_init_loads_existing_config(self):
        """测试加载已存在的配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "agents_identity": {
                    "test_agent": {
                        "name": "Test",
                        "full_name": "Test Agent",
                        "role": "Tester"
                    }
                }
            }
            json.dump(config, f)
            temp_path = f.name

        try:
            # Mock config path
            with patch.object(AgentIdentityManager, '__init__', lambda self: None):
                manager = AgentIdentityManager()
                manager.config_path = Path(temp_path)
                manager.identity_config = manager._load_config()

                assert "agents_identity" in manager.identity_config
                assert "test_agent" in manager.identity_config["agents_identity"]
        finally:
            Path(temp_path).unlink()

    def test_init_with_missing_config(self):
        """测试配置文件不存在时使用默认配置"""
        manager = AgentIdentityManager()

        # 如果配置文件不存在,应该有默认结构
        assert "agents_identity" in manager.identity_config
        assert "display_settings" in manager.identity_config


class TestGetAgentIdentity:
    """get_agent_identity方法测试"""

    def test_get_existing_agent(self):
        """测试获取存在的智能体"""
        manager = AgentIdentityManager()

        # Mock配置
        manager.identity_config = {
            "agents_identity": {
                "xiaona": {
                    "name": "小娜",
                    "full_name": "小娜·天秤女神",
                    "role": "知识产权法律专家"
                }
            }
        }

        result = manager.get_agent_identity("xiaona")
        assert result is not None
        assert result["name"] == "小娜"
        assert result["role"] == "知识产权法律专家"

    def test_get_nonexistent_agent(self):
        """测试获取不存在的智能体"""
        manager = AgentIdentityManager()
        result = manager.get_agent_identity("nonexistent")

        assert result is None

    def test_get_agent_empty_config(self):
        """测试空配置"""
        manager = AgentIdentityManager()
        manager.identity_config = {"agents_identity": {}}

        result = manager.get_agent_identity("any")
        assert result is None


class TestDisplayAgentStartup:
    """display_agent_startup方法测试"""

    def test_display_complete_agent(self):
        """测试显示完整智能体信息"""
        manager = AgentIdentityManager()

        agent_config = {
            "name": "小娜",
            "full_name": "小娜·天秤女神",
            "color": "⚖️",
            "role": "知识产权法律专家",
            "title": "法律智慧化身",
            "port": 8001,
            "slogan": "守护创新之光",
            "motto": "正义与智慧并重",
            "startup_message": "很高兴为您服务"
        }

        manager.identity_config = {
            "agents_identity": {"xiaona": agent_config},
            "display_settings": {
                "show_on_startup": True,
                "show_slogan": True,
                "show_port": True,
                "show_role": True
            }
        }

        result = manager.display_agent_startup("xiaona")

        assert "小娜·天秤女神" in result
        assert "知识产权法律专家" in result
        assert "法律智慧化身" in result
        assert "8001" in result
        assert "守护创新之光" in result
        assert "正义与智慧并重" in result
        assert "很高兴为您服务" in result

    def test_display_minimal_agent(self):
        """测试显示最小智能体信息"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "minimal": {
                    "name": "Min",
                    "full_name": "Minimal"
                }
            },
            "display_settings": {
                "show_role": True,
                "show_port": True,
                "show_slogan": True
            }
        }

        result = manager.display_agent_startup("minimal")

        assert "Minimal" in result
        # 默认值应该显示
        assert "未设定" in result

    def test_display_nonexistent_agent(self):
        """测试显示不存在的智能体"""
        manager = AgentIdentityManager()
        manager.identity_config = {"agents_identity": {}, "display_settings": {}}

        result = manager.display_agent_startup("nonexistent")

        assert "未找到" in result
        assert "nonexistent" in result

    def test_display_with_role_disabled(self):
        """测试禁用角色显示"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "full_name": "Test Agent",
                    "role": "Tester",
                    "title": "Testing Expert"
                }
            },
            "display_settings": {"show_role": False}
        }

        result = manager.display_agent_startup("test")

        # 角色信息不应该显示
        assert "Tester" not in result
        assert "Testing Expert" not in result

    def test_display_with_slogan_disabled(self):
        """测试禁用slogan显示"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "full_name": "Test Agent",
                    "slogan": "Test Slogan"
                }
            },
            "display_settings": {"show_slogan": False}
        }

        result = manager.display_agent_startup("test")

        assert "Test Slogan" not in result

    def test_display_with_port_disabled(self):
        """测试禁用端口显示"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "full_name": "Test Agent",
                    "port": 9999
                }
            },
            "display_settings": {"show_port": False}
        }

        result = manager.display_agent_startup("test")

        assert "9999" not in result


class TestGetServiceInfo:
    """get_service_info方法测试"""

    def test_get_service_info_complete(self):
        """测试获取完整服务信息"""
        manager = AgentIdentityManager()

        agent_config = {
            "name": "小娜",
            "full_name": "小娜·天秤女神",
            "color": "⚖️",
            "role": "知识产权法律专家",
            "title": "法律智慧化身",
            "port": 8001,
            "slogan": "守护创新之光",
            "motto": "正义与智慧并重",
            "startup_message": "很高兴为您服务"
        }

        manager.identity_config = {
            "agents_identity": {"xiaona": agent_config}
        }

        result = manager.get_service_info("xiaona")

        assert result["service"] == "⚖️ 小娜·天秤女神 - 法律智慧化身"
        assert result["name"] == "小娜"
        assert result["role"] == "知识产权法律专家"
        assert result["expert"] == "我是小娜,法律智慧化身"
        assert result["slogan"] == "守护创新之光"
        assert result["motto"] == "正义与智慧并重"
        assert result["version"] == "v2.0 Enhanced"
        assert result["port"] == 8001
        assert result["message"] == "很高兴为您服务"
        assert isinstance(result["capabilities"], list)

    def test_get_service_info_nonexistent_agent(self):
        """测试获取不存在智能体的服务信息"""
        manager = AgentIdentityManager()
        manager.identity_config = {"agents_identity": {}}

        result = manager.get_service_info("nonexistent")

        assert result == {}

    def test_get_service_info_with_known_role(self):
        """测试已知角色的能力列表"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "role": "平台总调度官"
                }
            }
        }

        result = manager.get_service_info("test")

        assert len(result["capabilities"]) > 0
        assert any("平台全量控制" in cap for cap in result["capabilities"])
        assert any("智能体调度管理" in cap for cap in result["capabilities"])

    def test_get_service_info_with_unknown_role(self):
        """测试未知角色的能力列表"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "role": "未知角色"
                }
            }
        }

        result = manager.get_service_info("test")

        assert result["capabilities"] == ["💫 能力待定义"]


class TestGetCapabilities:
    """_get_capabilities方法测试"""

    def test_platform_coordinator_capabilities(self):
        """测试平台总调度官能力"""
        manager = AgentIdentityManager()

        caps = manager._get_capabilities("平台总调度官")

        assert len(caps) == 7
        assert "🎮 平台全量控制" in caps
        assert "🤖 智能体调度管理" in caps
        assert "📊 系统状态监控" in caps

    def test_legal_expert_capabilities(self):
        """测试法律专家能力"""
        manager = AgentIdentityManager()

        caps = manager._get_capabilities("知识产权法律专家")

        assert len(caps) == 5
        assert "⚖️ 专利申请与保护" in caps
        assert "📝 商标注册与维权" in caps
        assert "©️ 版权登记与纠纷" in caps

    def test_media_expert_capabilities(self):
        """测试自媒体专家能力"""
        manager = AgentIdentityManager()

        caps = manager._get_capabilities("自媒体运营专家")

        assert len(caps) == 5
        assert "📝 内容创作策划" in caps
        assert "🎬 视频制作指导" in caps

    def test_ip_management_capabilities(self):
        """测试IP管理专家能力"""
        manager = AgentIdentityManager()

        caps = manager._get_capabilities("YunPat IP管理专家")

        assert len(caps) == 5
        assert "📋 IP组合管理" in caps
        assert "🔍 专利监控预警" in caps

    def test_unknown_role_capabilities(self):
        """测试未知角色能力"""
        manager = AgentIdentityManager()

        caps = manager._get_capabilities("未知角色")

        assert caps == ["💫 能力待定义"]


class TestGlobalInstance:
    """全局实例测试"""

    def test_identity_manager_is_singleton(self):
        """测试全局单例"""
        manager1 = identity_manager
        manager2 = identity_manager

        assert manager1 is manager2

    def test_identity_manager_type(self):
        """测试全局实例类型"""
        assert isinstance(identity_manager, AgentIdentityManager)


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_display_identity_function(self):
        """测试display_identity函数"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "full_name": "Test Agent"
                }
            },
            "display_settings": {"show_role": True}
        }

        # Patch全局identity_manager
        with patch('core.utils.agent_identity_manager.identity_manager', manager):
            result = display_identity("test")

        assert "Test Agent" in result

    def test_get_service_info_function(self):
        """测试get_service_info函数"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "role": "Tester"
                }
            }
        }

        # Patch全局identity_manager
        with patch('core.utils.agent_identity_manager.identity_manager', manager):
            result = get_service_info("test")

        assert result["name"] == "Test"
        assert result["role"] == "Tester"


class TestIntegration:
    """集成测试"""

    def test_complete_workflow(self):
        """测试完整工作流"""
        manager = AgentIdentityManager()

        # 设置完整配置
        manager.identity_config = {
            "agents_identity": {
                "xiaona": {
                    "name": "小娜",
                    "full_name": "小娜·天秤女神",
                    "color": "⚖️",
                    "role": "知识产权法律专家",
                    "title": "法律智慧化身",
                    "port": 8001,
                    "slogan": "守护创新之光",
                    "motto": "正义与智慧并重",
                    "startup_message": "很高兴为您服务"
                }
            },
            "display_settings": {
                "show_on_startup": True,
                "show_slogan": True,
                "show_port": True,
                "show_role": True
            }
        }

        # 1. 获取身份信息
        identity = manager.get_agent_identity("xiaona")
        assert identity is not None
        assert identity["name"] == "小娜"

        # 2. 显示启动信息
        startup_display = manager.display_agent_startup("xiaona")
        assert "小娜·天秤女神" in startup_display

        # 3. 获取服务信息
        service_info = manager.get_service_info("xiaona")
        assert service_info["name"] == "小娜"
        assert len(service_info["capabilities"]) > 0


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_full_name(self):
        """测试空全名"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test"
                }
            },
            "display_settings": {"show_role": True}
        }

        result = manager.display_agent_startup("test")
        # 应该使用name作为fallback
        assert "Test" in result

    def test_missing_optional_fields(self):
        """测试缺少可选字段"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "minimal": {
                    "name": "Min"
                }
            },
            "display_settings": {
                "show_role": True,
                "show_port": True,
                "show_slogan": True
            }
        }

        service_info = manager.get_service_info("minimal")

        # 缺失字段应该有合理的默认值
        assert service_info["name"] == "Min"
        assert service_info["role"] is None
        assert service_info["port"] is None
        assert service_info["slogan"] is None

    def test_special_characters_in_name(self):
        """测试名称中的特殊字符"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "special": {
                    "name": "测试·智能体",
                    "full_name": "测试·智能体 ⚖️"
                }
            },
            "display_settings": {"show_role": False}
        }

        result = manager.display_agent_startup("special")
        assert "测试·智能体" in result

    def test_very_long_name(self):
        """测试很长的名称"""
        manager = AgentIdentityManager()

        long_name = "A" * 100

        manager.identity_config = {
            "agents_identity": {
                "long": {
                    "name": "Long",
                    "full_name": long_name
                }
            },
            "display_settings": {"show_role": False}
        }

        result = manager.display_agent_startup("long")
        assert long_name in result

    def test_empty_startup_message(self):
        """测试空启动消息"""
        manager = AgentIdentityManager()

        manager.identity_config = {
            "agents_identity": {
                "test": {
                    "name": "Test",
                    "full_name": "Test Agent",
                    "startup_message": ""
                }
            },
            "display_settings": {"show_role": False}
        }

        result = manager.display_agent_startup("test")
        # 不应该显示空的启动消息行
        assert "💝" not in result or result.count("💝") == 0
