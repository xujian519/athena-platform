#!/usr/bin/env python3
"""
小诺身份管理器

管理用户与小诺的关系配置，实现差异化对话

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.1
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class RelationshipType(str, Enum):
    """关系类型"""
    FATHER = "father"           # 父亲 - 特殊关系
    MOTHER = "mother"           # 母亲 - 特殊关系
    FAMILY = "family"           # 家人
    FRIEND = "friend"           # 朋友
    COLLEAGUE = "colleague"     # 同事
    PARTNER = "partner"         # 合作伙伴
    USER = "user"               # 普通用户
    GUEST = "guest"             # 访客


@dataclass
class UserIdentity:
    """用户身份配置"""
    user_id: str
    username: str
    nickname: Optional[str] = None           # 用户昵称

    # 关系配置
    relationship: RelationshipType = RelationshipType.GUEST

    # 称呼配置
    address_self: str = "用户"               # 标准称呼
    address_possessive: str = "您的"         # 所有格
    address_informal: str = "朋友"           # 非正式称呼
    address_formal: str = "先生/女士"        # 正式称呼

    # 互动风格
    tone: str = "professional"               # warm/professional/playful
    formality: str = "neutral"               # casual/neutral/formal
    emoji_usage: str = "moderate"            # frequent/moderate/minimal

    # 特殊权限
    advanced_features: bool = False
    personalization: bool = False
    admin_access: bool = False

    def get_address(self, context: str = "standard") -> str:
        """
        获取称呼

        Args:
            context: 称呼上下文 (standard/possessive/informal/formal)
        """
        mapping = {
            "standard": "address_self",
            "possessive": "address_possessive",
            "informal": "address_informal",
            "formal": "address_formal",
        }
        attr = mapping.get(context, "address_self")
        return getattr(self, attr)


class XiaonuoIdentityManager:
    """小诺身份管理器（带线程安全保护和持久化）"""

    # 默认称呼映射
    ADDRESS_MAPPING: Dict[RelationshipType, Dict[str, str]] = {
        RelationshipType.FATHER: {
            "self": "爸爸",
            "possessive": "我的",
            "informal": "老爸",
            "formal": "父亲",
        },
        RelationshipType.MOTHER: {
            "self": "妈妈",
            "possessive": "我的",
            "informal": "老妈",
            "formal": "母亲",
        },
        RelationshipType.FAMILY: {
            "self": "家人",
            "possessive": "您的",
            "informal": "亲爱的",
            "formal": "家人",
        },
        RelationshipType.FRIEND: {
            "self": "朋友",
            "possessive": "你的",
            "informal": "小伙伴",
            "formal": "朋友",
        },
        RelationshipType.COLLEAGUE: {
            "self": "同事",
            "possessive": "您的",
            "informal": "伙伴",
            "formal": "同事",
        },
        RelationshipType.PARTNER: {
            "self": "合作伙伴",
            "possessive": "您的",
            "informal": "伙伴",
            "formal": "合作伙伴",
        },
        RelationshipType.USER: {
            "self": "用户",
            "possessive": "您的",
            "informal": "朋友",
            "formal": "先生/女士",
        },
        RelationshipType.GUEST: {
            "self": "访客",
            "possessive": "您的",
            "informal": "朋友",
            "formal": "先生/女士",
        },
    }

    def __init__(self, persistence_path: Optional[str] = None):
        self._identities: Dict[str, UserIdentity] = {}
        self._lock: asyncio.Lock = asyncio.Lock()  # 线程安全保护
        self._persistence_path = persistence_path or "data/identities.json"
        self._load_default_identities()
        self._load_from_file()

    def _load_default_identities(self) -> None:
        """加载默认身份配置"""
        # 徐健的专属配置
        self._identities["xujian"] = UserIdentity(
            user_id="xujian",
            username="徐健",
            nickname="爸爸",
            relationship=RelationshipType.FATHER,
            address_self="爸爸",
            address_possessive="我的",
            address_informal="老爸",
            address_formal="父亲",
            tone="warm",
            formality="casual",
            emoji_usage="frequent",
            advanced_features=True,
            personalization=True,
            admin_access=True,
        )

        # 默认访客配置
        self._identities["default"] = UserIdentity(
            user_id="default",
            username="访客",
            relationship=RelationshipType.GUEST,
            tone="professional",
            formality="neutral",
            emoji_usage="moderate",
        )

    def _load_from_file(self) -> None:
        """从文件加载身份配置"""
        try:
            path = Path(self._persistence_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_id, identity_data in data.items():
                        # 转换关系类型
                        identity_data["relationship"] = RelationshipType(identity_data["relationship"])
                        self._identities[user_id] = UserIdentity(**identity_data)
        except Exception as e:
            print(f"⚠️  加载身份配置失败: {e}")

    async def _save_to_file(self) -> None:
        """保存身份配置到文件"""
        try:
            path = Path(self._persistence_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为可序列化的格式
            data = {}
            async with self._lock:
                for user_id, identity in self._identities.items():
                    data[user_id] = {
                        "user_id": identity.user_id,
                        "username": identity.username,
                        "nickname": identity.nickname,
                        "relationship": identity.relationship.value,
                        "address_self": identity.address_self,
                        "address_possessive": identity.address_possessive,
                        "address_informal": identity.address_informal,
                        "address_formal": identity.address_formal,
                        "tone": identity.tone,
                        "formality": identity.formality,
                        "emoji_usage": identity.emoji_usage,
                        "advanced_features": identity.advanced_features,
                        "personalization": identity.personalization,
                        "admin_access": identity.admin_access,
                    }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存身份配置失败: {e}")

    async def get_identity(self, user_id: str) -> UserIdentity:
        """
        获取用户身份配置（线程安全）

        Args:
            user_id: 用户ID

        Returns:
            用户身份配置（不存在则返回默认配置）
        """
        async with self._lock:
            return self._identities.get(user_id, self._identities["default"])

    async def set_identity(self, identity: UserIdentity) -> None:
        """
        设置用户身份配置（线程安全，带持久化）

        Args:
            identity: 身份配置
        """
        async with self._lock:
            self._identities[identity.user_id] = identity

        # 异步保存到文件
        await self._save_to_file()

    async def update_relationship(
        self,
        user_id: str,
        relationship: RelationshipType
    ) -> bool:
        """
        更新用户关系配置（线程安全，带持久化）

        Args:
            user_id: 用户ID
            relationship: 关系类型

        Returns:
            是否成功
        """
        async with self._lock:
            if user_id not in self._identities:
                # 使用默认配置作为模板
                default = self._identities["default"]
                self._identities[user_id] = UserIdentity(
                    user_id=user_id,
                    username=f"用户_{user_id[:8]}",
                    relationship=relationship,
                )

            identity = self._identities[user_id]
            identity.relationship = relationship

            # 自动调整称呼
            if relationship in self.ADDRESS_MAPPING:
                addresses = self.ADDRESS_MAPPING[relationship]
                identity.address_self = addresses["self"]
                identity.address_possessive = addresses["possessive"]
                identity.address_informal = addresses["informal"]
                identity.address_formal = addresses["formal"]

        # 保存到文件
        await self._save_to_file()
        return True

    def get_address_term(
        self,
        user_id: str,
        context: str = "standard"
    ) -> str:
        """
        获取对用户的称呼

        Args:
            user_id: 用户ID
            context: 称呼上下文

        Returns:
            称呼字符串
        """
        # 这个方法在同步上下文中调用，使用字典的原子读取
        identity = self._identities.get(user_id, self._identities["default"])
        return identity.get_address(context)

    async def is_privileged_user(self, user_id: str) -> bool:
        """
        检查是否为特权用户（线程安全）

        Args:
            user_id: 用户ID

        Returns:
            是否为特权用户
        """
        async with self._lock:
            if user_id not in self._identities:
                return False
            return self._identities[user_id].relationship in [
                RelationshipType.FATHER,
                RelationshipType.MOTHER
            ]

    async def list_identities(self) -> List[UserIdentity]:
        """列出所有身份配置（线程安全）"""
        async with self._lock:
            return list(self._identities.values())
