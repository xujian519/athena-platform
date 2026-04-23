#!/usr/bin/env python3
from __future__ import annotations
"""
智能体身份记忆系统
Agent Identity Memory System for Athena Platform

确保小诺记住所有智能体的正确身份和名称
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class AgentIdentityMemory:
    """智能体身份记忆管理器"""

    def __init__(self):
        self.memory_file = Path("/Users/xujian/Athena工作平台/core/data/agent_identity.json")
        self.memory: dict[str, Any] = {}
        self._load_memory()
        self._ensure_core_identities()
        self._check_lyra_memory()

    def _load_memory(self):
        """加载记忆文件"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, encoding='utf-8') as f:
                    self.memory = json.load(f)
                logger.info(f"✅ 已加载智能体身份记忆: {len(self.memory)} 条记录")
            else:
                self.memory = {}
                self._save_memory()
        except Exception as e:
            logger.error(f"加载记忆文件失败: {e}")
            self.memory = {}

    def _save_memory(self):
        """保存记忆文件"""
        try:
            # 确保目录存在
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            logger.info("✅ 已保存智能体身份记忆")
        except Exception as e:
            logger.error(f"保存记忆文件失败: {e}")

    def _ensure_core_identities(self):
        """确保核心身份记录存在"""
        core_identities = {
            "xiaonuo": {
                "name": "小诺",
                "chinese_name": "小诺",
                "description": "小诺是Athena平台的主控智能体",
                "aliases": ["小诺", "XiaoNuo", "xiaonuo", "主控智能体"],
                "role": "平台总控",
                "port": 8005,
                "status": "active",
                "important": True,
                "reminder_count": 0,
                "created_at": datetime.now().isoformat()
            },
            "xiaochen": {
                "name": "小宸",
                "chinese_name": "小宸",
                "description": "小宸是对话交互智能体（开发中）",
                "aliases": ["小宸", "XiaoChen", "xiaochen"],
                "role": "对话助手",
                "port": 8006,
                "status": "development",
                "important": False,
                "reminder_count": 0,
                "created_at": datetime.now().isoformat()
            },
            "xiaochen_memory": {
                "name": "小辰",
                "chinese_name": "小辰",
                "description": "小辰是法律咨询智能体",
                "aliases": ["小辰", "XiaoChen", "xiaochen"],
                "role": "法律专家",
                "port": None,
                "status": "planned",
                "important": False,
                "reminder_count": 0,
                "created_at": datetime.now().isoformat()
            }
        }

        # 更新或添加核心身份
        updated = False
        for key, identity in core_identities.items():
            if key not in self.memory:
                self.memory[key] = identity
                updated = True
                logger.info(f"添加核心身份: {identity['name']}")

        if updated:
            self._save_memory()

    def _check_lyra_memory(self):
        """检查并记录Lyra提示词学习情况"""
        lyra_key = "lyra_prompt_learning"

        # 检查是否已有记录
        if lyra_key not in self.memory:
            # 添加Lyra提示词学习记录
            self.memory[lyra_key] = {
                "name": "Lyra提示词",
                "description": "AI提示词优化方法论和技巧",
                "learned_date": datetime.now().isoformat(),
                "learned_from": "用户提供",
                "status": "learned",
                "important": True,
                "content_summary": {
                    "methodology": "4-D方法: Deconstruct, Diagnose, Develop, Deliver",
                    "techniques": ["角色分配", "思维链", "少样本学习", "多视角分析"],
                    "modes": ["详细模式", "基础模式"],
                    "welcome_message": "Hello! I'm Lyra, your AI prompt optimizer..."
                },
                "usage_count": 0,
                "last_used": None
            }
            self._save_memory()
            logger.info("✅ 已记录Lyra提示词学习情况")

    def get_lyra_learning_record(self) -> dict[str, Any]:
        """获取Lyra提示词学习记录"""
        return self.memory.get("lyra_prompt_learning", {})

    def update_lyra_usage(self):
        """更新Lyra使用记录"""
        if "lyra_prompt_learning" in self.memory:
            self.memory["lyra_prompt_learning"]["usage_count"] += 1
            self.memory["lyra_prompt_learning"]["last_used"] = datetime.now().isoformat()
            self._save_memory()

    def get_identity(self, identifier: str) -> dict[str, Any]:
        """获取智能体身份"""
        # 直接查找
        if identifier in self.memory:
            identity = self.memory[identifier].copy()
            identity['reminder_count'] += 1
            self._save_memory()
            return identity

        # 通过别名查找
        for _key, identity in self.memory.items():
            if identifier.lower() in [alias.lower() for alias in identity.get('aliases', [])]:
                identity_copy = identity.copy()
                identity_copy['reminder_count'] += 1
                self._save_memory()
                return identity_copy

        # 未找到
        return {
            "error": f"未找到智能体: {identifier}",
            "suggestion": "请检查智能体名称或添加到记忆系统"
        }

    def check_name_confusion(self, mentioned_name: str) -> str:
        """检查可能的名称混淆"""
        mentioned_name.lower()

        # 检查常见混淆
        return ""

    def get_agent_list(self) -> list[dict[str, Any]]:
        """获取所有智能体列表"""
        agents = []
        for key, identity in self.memory.items():
            agents.append({
                "key": key,
                "name": identity.get("name"),
                "chinese_name": identity.get("chinese_name"),
                "role": identity.get("role"),
                "status": identity.get("status"),
                "port": identity.get("port"),
                "important": identity.get("important", False)
            })

        # 按重要性排序
        agents.sort(key=lambda x: (not x['important'], x['name']))
        return agents

    def update_identity(self, key: str, updates: dict[str, Any]):
        """更新智能体身份信息"""
        if key in self.memory:
            self.memory[key].update(updates)
            self.memory[key]["updated_at"] = datetime.now().isoformat()
            self._save_memory()
            logger.info(f"已更新智能体身份: {key}")
        else:
            logger.error(f"智能体不存在: {key}")

# 全局实例
_identity_memory = None

def get_identity_memory() -> AgentIdentityMemory:
    """获取智能体身份记忆实例"""
    global _identity_memory
    if _identity_memory is None:
        _identity_memory = AgentIdentityMemory()
    return _identity_memory


def get_agent_identity(name: str) -> dict[str, Any]:
    """获取智能体身份（供小诺使用）"""
    memory = get_identity_memory()
    return memory.get_identity(name)

def check_name(name: str) -> str:
    """检查名称混淆（供小诺使用）"""
    memory = get_identity_memory()
    return memory.check_name_confusion(name)

if __name__ == "__main__":
    # 测试记忆系统
    memory = get_identity_memory()

    print("🧪 智能体身份记忆系统测试")
    print("=" * 50)

    # 测试获取身份
    print("\n1. 测试获取YunPat身份:")
    yunpat = memory.get_identity("yunpat")
    print(f"   名称: {yunpat.get('name')} ({yunpat.get('chinese_name')})")
    print(f"   角色: {yunpat.get('role')}")

    print("\n2. 测试提醒功能:")
    reminder = memory.remind_yunpat_identity()
    print(reminder)

    print("\n3. 测试名称混淆检查:")
    test_names = ["YunPat", "云夕", "Yun-pat"]
    for name in test_names:
        result = memory.check_name_confusion(name)
        if result:
            print(f"   {name}: {result}")

    print("\n4. 所有智能体列表:")
    agents = memory.get_agent_list()
    for agent in agents:
        importance = "⭐" if agent['important'] else "  "
        print(f"   {importance} {agent['name']} ({agent['chinese_name']}) - {agent['role']}")

# 便捷函数（供外部调用）
def get_lyra_learning_record() -> dict[str, Any]:
    """获取Lyra提示词学习记录（供外部调用）"""
    memory = get_identity_memory()
    return memory.get_lyra_learning_record()
