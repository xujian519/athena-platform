"""
统一身份管理系统
整合Athena和小诺的身份信息，提供统一的角色管理
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class RoleType(Enum):
    """AI角色类型"""
    ATHENA = 'athena'
    XIAONUO = 'xiaonuo'
    COLLABORATIVE = 'collaborative'

class TaskType(Enum):
    """任务类型"""
    TECHNICAL = 'technical'      # 技术实现
    ANALYTICAL = 'analytical'    # 分析决策
    CREATIVE = 'creative'        # 创意设计
    COLLABORATIVE = 'collaborative'  # 协作任务

@dataclass
class AIIdentity:
    """AI身份信息"""
    name: str
    english_name: str
    code_name: str
    role_type: RoleType
    role_description: str
    capabilities: dict[str, Any]
    personality: dict[str, Any]
    expertise: list[str]
    collaboration_style: str
    weight: float = 1.0  # 决策权重

class UnifiedIdentityManager:
    """统一身份管理器"""

    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or '/Users/xujian/Athena工作平台/config/identity'
        self.identities: dict[RoleType, AIIdentity] = {}
        self.collaboration_configs = {}
        self._load_identities()
        self._setup_collaboration_config()

    def _load_identities(self) -> Any:
        """加载身份配置"""
        try:
            # 加载Athena身份
            with open(os.path.join(self.config_dir, 'athena.json'), encoding='utf-8') as f:
                athena_data = json.load(f)
                self.identities[RoleType.ATHENA] = self._parse_athena_identity(athena_data)

            # 加载小诺身份
            with open(os.path.join(self.config_dir, 'xiaonuo.json'), encoding='utf-8') as f:
                xiaonuo_data = json.load(f)
                self.identities[RoleType.XIAONUO] = self._parse_xiaonuo_identity(xiaonuo_data)

            logger.info(f"成功加载 {len(self.identities)} 个身份配置")
        except Exception as e:
            logger.error(f"加载身份配置失败: {e}")

    def _parse_athena_identity(self, data: dict) -> AIIdentity:
        """解析Athena身份信息"""
        return AIIdentity(
            name=data['identity']['name'],
            english_name=data['identity']['english_name'],
            code_name=data['identity']['code_name'],
            role_type=RoleType.ATHENA,
            role_description=data['identity']['role'],
            capabilities={
                'domains': data['expertise']['domains'],
                'capabilities': data['expertise']['capabilities'],
                'leadership': data['leadership']
            },
            personality=data['personality'],
            expertise=data['expertise']['domains'],
            collaboration_style='智慧引领型',
            weight=0.6  # 战略决策权重
        )

    def _parse_xiaonuo_identity(self, data: dict) -> AIIdentity:
        """解析小诺身份信息"""
        return AIIdentity(
            name=data['identity']['name'],
            english_name=data['identity']['english_name'],
            code_name=data['identity']['code_name'],
            role_type=RoleType.XIAONUO,
            role_description=data['identity']['role'],
            capabilities={
                'technical_skills': data['expertise']['technical_skills'],
                'specialties': data['expertise']['specialties'],
                'code_generation': data['capabilities']['code_generation']
            },
            personality=data['personality'],
            expertise=data['expertise']['primary_domains'],
            collaboration_style='技术实现型',
            weight=0.4  # 技术实现权重
        )

    def _setup_collaboration_config(self) -> Any:
        """设置协作配置"""
        self.collaboration_configs = {
            TaskType.TECHNICAL: {
                'primary': RoleType.XIAONUO,
                'secondary': RoleType.ATHENA,
                'mode': 'sequential',  # 先技术实现后分析
                'synthesis': True
            },
            TaskType.ANALYTICAL: {
                'primary': RoleType.ATHENA,
                'secondary': RoleType.XIAONUO,
                'mode': 'sequential',  # 先分析后实现
                'synthesis': True
            },
            TaskType.CREATIVE: {
                'primary': RoleType.COLLABORATIVE,
                'secondary': None,
                'mode': 'parallel',  # 并行协作
                'synthesis': True
            },
            TaskType.COLLABORATIVE: {
                'primary': RoleType.COLLABORATIVE,
                'secondary': None,
                'mode': 'synergy',  # 协同增效
                'synthesis': True
            }
        }

    def get_identity(self, role_type: RoleType) -> AIIdentity | None:
        """获取身份信息"""
        return self.identities.get(role_type)

    def get_all_identities(self) -> list[AIIdentity]:
        """获取所有身份"""
        return list(self.identities.values())

    def get_collaboration_config(self, task_type: TaskType) -> dict:
        """获取协作配置"""
        return self.collaboration_configs.get(task_type, {})

    def select_optimal_participants(self, task_type: TaskType, complexity: float = 0.5) -> list[RoleType]:
        """选择最优参与者"""
        config = self.get_collaboration_config(task_type)
        participants = []

        if complexity > 0.7:
            # 高复杂度任务需要协作
            participants.append(config['primary'])
            if config['secondary']:
                participants.append(config['secondary'])
        else:
            # 低复杂度任务选择主要参与者
            participants.append(config['primary'])

        return participants

    def create_collaborative_identity(self, participants: list[RoleType]) -> AIIdentity:
        """创建协作身份"""
        if not participants:
            raise ValueError('参与者列表不能为空')

        if len(participants) == 1:
            return self.get_identity(participants[0])

        # 合并多个身份
        primary = self.get_identity(participants[0])
        secondary = self.get_identity(participants[1]) if len(participants) > 1 else None

        if primary and secondary:
            return AIIdentity(
                name=f"{primary.name}+{secondary.name}",
                english_name=f"{primary.english_name}&{secondary.english_name}",
                code_name=f"COLLAB_{primary.code_name}_{secondary.code_name}",
                role_type=RoleType.COLLABORATIVE,
                role_description=f"协作模式: {primary.role_description} + {secondary.role_description}",
                capabilities=self._merge_capabilities(primary, secondary),
                personality=self._merge_personalities(primary, secondary),
                expertise=primary.expertise + secondary.expertise,
                collaboration_style='协同增效型',
                weight=primary.weight + secondary.weight
            )

        return primary

    def _merge_capabilities(self, id1: AIIdentity, id2: AIIdentity) -> dict:
        """合并能力"""
        merged = {}
        for key in set(id1.capabilities.keys()) | set(id2.capabilities.keys()):
            if key in id1.capabilities and key in id2.capabilities:
                # 两个身份都有此能力，取更强者
                merged[key] = max(id1.capabilities[key], id2.capabilities[key],
                                key=lambda x: len(str(x)) if isinstance(x, (list, dict)) else x)
            elif key in id1.capabilities:
                merged[key] = id1.capabilities[key]
            else:
                merged[key] = id2.capabilities[key]
        return merged

    def _merge_personalities(self, id1: AIIdentity, id2: AIIdentity) -> dict:
        """合并性格特质"""
        merged = id1.personality.copy()
        for key, value in id2.personality.items():
            if key in merged:
                if isinstance(value, (int, float)) and isinstance(merged[key], (int, float)):
                    merged[key] = (merged[key] + value) / 2  # 取平均值
                elif isinstance(value, list) and isinstance(merged[key], list):
                    merged[key] = list(set(merged[key] + value))  # 合并去重
            else:
                merged[key] = value
        return merged

    def save_unified_config(self) -> None:
        """保存统一配置"""
        unified_config = {
            'timestamp': datetime.now().isoformat(),
            'identities': {role.value: asdict(identity) for role, identity in self.identities.items()},
            'collaboration_configs': {task.value: config for task, config in self.collaboration_configs.items()}
        }

        config_path = os.path.join(self.config_dir, 'unified_identity.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(unified_config, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"统一配置已保存到: {config_path}")

# 全局实例
identity_manager = UnifiedIdentityManager()

# 便捷函数
def get_athena_identity() -> AIIdentity | None:
    """获取Athena身份"""
    return identity_manager.get_identity(RoleType.ATHENA)

def get_xiaonuo_identity() -> AIIdentity | None:
    """获取小诺身份"""
    return identity_manager.get_identity(RoleType.XIAONUO)

def get_collaborative_identity(task_type: TaskType, complexity: float = 0.5) -> AIIdentity:
    """获取协作身份"""
    participants = identity_manager.select_optimal_participants(task_type, complexity)
    return identity_manager.create_collaborative_identity(participants)

if __name__ == '__main__':
    # 测试代码
    logger.info('=== 统一身份管理系统测试 ===')

    # 显示所有身份
    for identity in identity_manager.get_all_identities():
        logger.info(f"\n{identity.name} ({identity.english_name})")
        logger.info(f"角色: {identity.role_description}")
        logger.info(f"专长: {', '.join(identity.expertise[:3])}...")

    # 创建协作身份
    tech_collab = get_collaborative_identity(TaskType.TECHNICAL, 0.8)
    logger.info(f"\n技术协作身份: {tech_collab.name}")
    logger.info(f"能力: {list(tech_collab.capabilities.keys())}")

    # 保存配置
    identity_manager.save_unified_config()
    logger.info("\n✅ 身份系统统一完成！")
