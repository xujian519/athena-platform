
"""
联邦记忆系统
支持多智能体之间的记忆共享、整合和协同学习
"""

import asyncio
import hashlib
import json
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import aiohttp
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class MemoryConsistencyLevel(Enum):
    """记忆一致性级别"""
    EVENTUAL = 'eventual'      # 最终一致性
    STRONG = 'strong'         # 强一致性
    CAUSAL = 'causal'         # 因果一致性
    SESSION = 'session'       # 会话一致性

class MemorySharingPolicy(Enum):
    """记忆共享策略"""
    PUBLIC = 'public'         # 公开共享
    PRIVATE = 'private'       # 私有不共享
    SELECTIVE = 'selective'   # 选择性共享
    ENCRYPTED = 'encrypted'   # 加密共享

class ConflictResolutionStrategy(Enum):
    """冲突解决策略"""
    LAST_WRITER_WINS = 'last_writer_wins'     # 最后写入获胜
    MERGE = 'merge'                           # 合并
    VOTING = 'voting'                         # 投票
    PRIORITY_BASED = 'priority_based'         # 基于优先级
    TIMESTAMP_BASED = 'timestamp_based'       # 基于时间戳

@dataclass
class AgentIdentity:
    """智能体身份"""
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: list[str]
    trust_score: float = 0.5
    public_key: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FederatedMemory:
    """联邦记忆项"""
    memory_id: str
    content: Any
    memory_type: str
    owner_agent_id: str
    sharing_policy: MemorySharingPolicy
    consistency_level: MemoryConsistencyLevel
    importance: float
    created_at: datetime
    last_modified: datetime
    version: int = 1
    checksum: str = ''
    endorsements: list[str] = field(default_factory=list)  # 其他智能体的背书
    conflicts: list[str] = field(default_factory=list)    # 冲突的记忆ID
    access_control: list[str] = field(default_factory=list)  # 允许访问的智能体ID
    encryption_key: Optional[str] = None
    federated_updates: list[dict[str, Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def calculate_checksum(self) -> str:
        """计算校验和"""
        content_str = json.dumps(self.content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

@dataclass
class MemoryUpdate:
    """记忆更新"""
    update_id: str
    memory_id: str
    agent_id: str
    update_type: str  # create, update, delete, merge
    update_data: dict[str, Any]
    timestamp: datetime
    previous_version: int
    new_version: int
    signature: Optional[str] = None

@dataclass
class ConflictResolution:
    """冲突解决记录"""
    conflict_id: str
    memory_id: str
    conflicting_memories: list[str]
    resolution_strategy: ConflictResolutionStrategy
    resolution_result: dict[str, Any]
    resolved_by: str
    resolved_at: datetime

class FederatedMemorySystem:
    """联邦记忆系统"""

    def __init__(self, agent_identity: AgentIdentity, config: Optional[dict[str, Any]] = None):
        self.agent_identity = agent_identity
        self.config = config or {
            'max_federated_memories': 5000,
            'sync_interval': 300,  # 5分钟
            'consistency_check_interval': 600,  # 10分钟
            'default_sharing_policy': MemorySharingPolicy.SELECTIVE,
            'default_consistency': MemoryConsistencyLevel.EVENTUAL,
            'conflict_resolution_strategy': ConflictResolutionStrategy.MERGE,
            'encryption_enabled': True,
            'max_endorsements': 10
        }

        self.local_memories = {}
        self.federated_memories = {}
        self.agent_registry = {}
        self.pending_updates = deque(maxlen=1000)
        self.conflict_resolutions = deque(maxlen=100)
        self.sync_lock = asyncio.Lock()
        self.encryption_key = Fernet.generate_key() if self.config['encryption_enabled'] else None
        self.cipher_suite = Fernet(self.encryption_key) if self.encryption_key else None

        # 性能统计
        self.statistics = {
            'total_memories': 0,
            'federated_memories': 0,
            'sync_operations': 0,
            'conflicts_resolved': 0,
            'last_sync_time': None,
            'active_peers': 0
        }

    async def register_with_federation(self, federation_node_url: str) -> bool:
        """向联邦注册"""
        try:
            async with aiohttp.ClientSession() as session:
                registration_data = {
                    'agent_id': self.agent_identity.agent_id,
                    'agent_name': self.agent_identity.agent_name,
                    'agent_type': self.agent_identity.agent_type,
                    'capabilities': self.agent_identity.capabilities,
                    'public_key': self.agent_identity.public_key,
                    'timestamp': datetime.now().isoformat()
                }

                async with session.post(f"{federation_node_url}/register", json=registration_data) as resp:
                    if resp.status == 200:
                        await resp.json()
                        logger.info(f"成功注册到联邦: {federation_node_url}")
                        return True
                    else:
                        logger.error(f"注册失败: {resp.status}")
                        return False

        except Exception as e:
            logger.error(f"注册到联邦失败: {e}")
            return False

    async def add_federated_memory(self, memory: FederatedMemory) -> bool:
        """添加联邦记忆"""
        try:
            # 计算校验和
            memory.checksum = memory.calculate_checksum()

            # 加密敏感内容
            if (memory.sharing_policy == MemorySharingPolicy.ENCRYPTED and
                self.cipher_suite and memory.owner_agent_id == self.agent_identity.agent_id):
                memory.content = self._encrypt_content(memory.content)
                memory.encryption_key = self.encryption_key.decode()

            # 添加到本地存储
            self.local_memories[memory.memory_id] = memory
            self.federated_memories[memory.memory_id] = memory

            # 创建更新事件
            update = MemoryUpdate(
                update_id=str(uuid.uuid4()),
                memory_id=memory.memory_id,
                agent_id=self.agent_identity.agent_id,
                update_type='create',
                update_data={'memory': asdict(memory)},
                timestamp=datetime.now(),
                previous_version=0,
                new_version=memory.version
            )

            self.pending_updates.append(update)

            # 更新统计
            self.statistics['total_memories'] += 1
            if memory.sharing_policy != MemorySharingPolicy.PRIVATE:
                self.statistics['federated_memories'] += 1

            logger.info(f"添加联邦记忆: {memory.memory_id}")
            return True

        except Exception as e:
            logger.error(f"添加联邦记忆失败: {e}")
            return False

    async def get_federated_memory(self, memory_id: str) -> Optional[FederatedMemory]:
        """获取联邦记忆"""
        # 首先检查本地
        memory = self.federated_memories.get(memory_id)
        if memory:
            # 检查访问权限
            if self._has_access(memory):
                # 解密内容
                if memory.encryption_key and memory.sharing_policy == MemorySharingPolicy.ENCRYPTED:
                    memory.content = self._decrypt_content(memory.content, memory.encryption_key)
                return memory
            else:
                logger.warning(f"无权访问记忆: {memory_id}")
                return None

        # 从联邦获取
        memory = await self._fetch_from_federation(memory_id)
        if memory:
            self.federated_memories[memory_id] = memory
            return memory

        return None

    def _has_access(self, memory: FederatedMemory) -> bool:
        """检查访问权限"""
        # 所有者总是有权限
        if memory.owner_agent_id == self.agent_identity.agent_id:
            return True

        # 检查共享策略
        if memory.sharing_policy == MemorySharingPolicy.PUBLIC:
            return True
        elif memory.sharing_policy == MemorySharingPolicy.PRIVATE:
            return False
        elif memory.sharing_policy == MemorySharingPolicy.SELECTIVE:
            return self.agent_identity.agent_id in memory.access_control
        elif memory.sharing_policy == MemorySharingPolicy.ENCRYPTED:
            # 加密记忆需要特定的密钥
            return self.agent_identity.agent_id in memory.access_control

        return False

    async def update_federated_memory(self, memory_id: str, updates: dict[str, Any]) -> bool:
        """更新联邦记忆"""
        memory = await self.get_federated_memory(memory_id)
        if not memory:
            logger.error(f"记忆不存在: {memory_id}")
            return False

        # 检查更新权限
        if (memory.owner_agent_id != self.agent_identity.agent_id and
            memory.consistency_level == MemoryConsistencyLevel.STRONG):
            logger.error(f"无权更新强一致性记忆: {memory_id}")
            return False

        try:
            # 记录原始版本
            previous_version = memory.version

            # 应用更新
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)

            # 更新版本和校验和
            memory.version += 1
            memory.last_modified = datetime.now()
            memory.checksum = memory.calculate_checksum()

            # 添加联邦更新记录
            memory.federated_updates.append({
                'agent_id': self.agent_identity.agent_id,
                'timestamp': datetime.now().isoformat(),
                'version': memory.version,
                'changes': updates
            })

            # 创建更新事件
            update = MemoryUpdate(
                update_id=str(uuid.uuid4()),
                memory_id=memory_id,
                agent_id=self.agent_identity.agent_id,
                update_type='update',
                update_data=updates,
                timestamp=datetime.now(),
                previous_version=previous_version,
                new_version=memory.version
            )

            self.pending_updates.append(update)

            logger.info(f"更新联邦记忆: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"更新联邦记忆失败: {e}")
            return False

    async def sync_with_federation(self) -> bool:
        """与联邦同步"""
        async with self.sync_lock:
            try:
                logger.info('开始与联邦同步...')

                # 获取待同步的更新
                updates_to_sync = list(self.pending_updates)
                self.pending_updates.clear()

                # 处理更新
                for update in updates_to_sync:
                    success = await self._sync_update(update)
                    if not success:
                        # 失败的更新重新加入队列
                        self.pending_updates.append(update)

                # 获取其他智能体的更新
                await self._fetch_peer_updates()

                # 检查冲突
                await self._detect_conflicts()

                # 解决冲突
                await self._resolve_conflicts()

                # 更新统计
                self.statistics['sync_operations'] += 1
                self.statistics['last_sync_time'] = datetime.now().isoformat()

                logger.info('联邦同步完成')
                return True

            except Exception as e:
                logger.error(f"联邦同步失败: {e}")
                return False

    async def _sync_update(self, update: MemoryUpdate) -> bool:
        """同步单个更新"""
        # 这里应该实现与联邦节点的通信
        # 简化实现，总是返回成功
        return True

    async def _fetch_peer_updates(self):
        """获取对等智能体的更新"""
        # 这里应该实现从其他智能体获取更新的逻辑
        pass

    async def _detect_conflicts(self):
        """检测冲突"""
        logger.info('检测记忆冲突...')

        # 检查版本冲突
        for memory_id, memory in self.federated_memories.items():
            if memory.conflicts:
                # 已知冲突，跳过
                continue

            # 检查本地版本与其他版本
            local_memory = self.local_memories.get(memory_id)
            if local_memory and local_memory.checksum != memory.checksum:
                # 发现冲突
                memory.conflicts.append(memory_id)
                logger.warning(f"发现冲突: {memory_id}")

    async def _resolve_conflicts(self):
        """解决冲突"""
        logger.info('解决记忆冲突...')

        unresolved_conflicts = [
            memory_id for memory_id, memory in self.federated_memories.items()
            if memory.conflicts
        ]

        for memory_id in unresolved_conflicts:
            memory = self.federated_memories[memory_id]
            conflicting_memories = [
                self.federated_memories[cid] for cid in memory.conflicts
                if cid in self.federated_memories
            ]

            if conflicting_memories:
                resolution = await self._resolve_memory_conflict(memory, conflicting_memories)
                if resolution:
                    self.conflict_resolutions.append(resolution)
                    memory.conflicts.clear()
                    self.statistics['conflicts_resolved'] += 1

    async def _resolve_memory_conflict(self, memory: FederatedMemory,
                                     conflicts: list[FederatedMemory]) -> Optional[ConflictResolution]:
        """解决单个记忆冲突"""
        strategy = ConflictResolutionStrategy(self.config['conflict_resolution_strategy'])

        conflict_id = str(uuid.uuid4())

        try:
            if strategy == ConflictResolutionStrategy.LAST_WRITER_WINS:
                # 选择最后更新的记忆
                resolved_memory = max([memory, *conflicts], key=lambda m: m.last_modified)
                resolution_data = {'resolved_memory_id': resolved_memory.memory_id}

            elif strategy == ConflictResolutionStrategy.MERGE:
                # 合并记忆
                resolved_memory = await self._merge_memories([memory, *conflicts])
                resolution_data = {'merged_memory': asdict(resolved_memory)}

            elif strategy == ConflictResolutionStrategy.VOTING:
                # 基于背书投票
                votes = {m.memory_id: len(m.endorsements) for m in [memory, *conflicts]}
                winner_id = max(votes, key=votes.get)
                resolution_data = {'voted_memory_id': winner_id}

            elif strategy == ConflictResolutionStrategy.PRIORITY_BASED:
                # 基于重要性
                resolved_memory = max([memory, *conflicts], key=lambda m: m.importance)
                resolution_data = {'priority_memory_id': resolved_memory.memory_id}

            else:
                # 默认基于时间戳
                resolved_memory = max([memory, *conflicts], key=lambda m: m.created_at)
                resolution_data = {'timestamp_memory_id': resolved_memory.memory_id}

            # 创建冲突解决记录
            resolution = ConflictResolution(
                conflict_id=conflict_id,
                memory_id=memory.memory_id,
                conflicting_memories=[c.memory_id for c in conflicts],
                resolution_strategy=strategy,
                resolution_result=resolution_data,
                resolved_by=self.agent_identity.agent_id,
                resolved_at=datetime.now()
            )

            logger.info(f"解决冲突: {conflict_id} 使用策略: {strategy.value}")
            return resolution

        except Exception as e:
            logger.error(f"解决冲突失败: {e}")
            return None

    async def _merge_memories(self, memories: list[FederatedMemory]) -> FederatedMemory:
        """合并多个记忆"""
        # 选择最老的作为基础
        base_memory = min(memories, key=lambda m: m.created_at)

        # 合并内容
        merged_content = []
        for memory in memories:
            if isinstance(memory.content, str):
                merged_content.append(f"[{memory.owner_agent_id}] {memory.content}")

        base_memory.content = "\n".join(merged_content)

        # 合并重要性
        base_memory.importance = max(m.importance for m in memories)

        # 合并背书
        all_endorsements = set()
        for memory in memories:
            all_endorsements.update(memory.endorsements)
        base_memory.endorsements = list(all_endorsements)

        # 更新版本
        base_memory.version = max(m.version for m in memories) + 1
        base_memory.last_modified = datetime.now()

        return base_memory

    async def endorse_memory(self, memory_id: str) -> bool:
        """背书记忆"""
        memory = await self.get_federated_memory(memory_id)
        if not memory:
            return False

        # 检查是否可以背书
        if (memory.owner_agent_id == self.agent_identity.agent_id or
            self.agent_identity.agent_id in memory.endorsements):
            logger.warning(f"不能背书自己的记忆或重复背书: {memory_id}")
            return False

        # 添加背书
        memory.endorsements.append(self.agent_identity.agent_id)

        # 限制背书数量
        if len(memory.endorsements) > self.config['max_endorsements']:
            memory.endorsements = memory.endorsements[-self.config['max_endorsements']:]

        logger.info(f"背书记忆: {memory_id}")
        return True

    async def search_federated_memories(self, query: str, filters: Optional[dict[str, Any]] = None,
                                      limit: int = 10) -> list[tuple[FederatedMemory, float]]:
        """搜索联邦记忆"""
        results = []
        query_words = set(query.lower().split())

        for memory in self.federated_memories.values():
            # 检查访问权限
            if not self._has_access(memory):
                continue

            # 应用过滤器
            if filters:
                if 'memory_type' in filters and memory.memory_type != filters['memory_type']:
                    continue
                if 'owner' in filters and memory.owner_agent_id != filters['owner']:
                    continue
                if 'min_importance' in filters and memory.importance < filters['min_importance']:
                    continue

            # 计算相关性分数
            if isinstance(memory.content, str):
                content_words = set(memory.content.lower().split())
                match_count = len(query_words.intersection(content_words))
                if match_count > 0:
                    score = match_count / len(query_words)
                    # 考虑重要性权重
                    score *= (1 + memory.importance)
                    # 考虑背书权重
                    score *= (1 + len(memory.endorsements) * 0.1)
                    results.append((memory, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:limit]

    def _encrypt_content(self, content: Any) -> str:
        """加密内容"""
        if not self.cipher_suite:
            return str(content)

        content_str = json.dumps(content, default=str)
        encrypted = self.cipher_suite.encrypt(content_str.encode())
        return encrypted.decode()

    def _decrypt_content(self, encrypted_content: str, key: str) -> Any:
        """解密内容"""
        try:
            if not self.cipher_suite or key != self.encryption_key.decode():
                return encrypted_content

            cipher_suite = Fernet(key.encode())
            decrypted = cipher_suite.decrypt(encrypted_content.encode())
            return json.loads(decrypted.decode())

        except Exception as e:
            logger.error(f"解密失败: {e}")
            return encrypted_content

    def get_federation_statistics(self) -> dict[str, Any]:
        """获取联邦统计信息"""
        # 计算活跃对等节点
        active_peers = len(self.agent_registry)

        # 记忆类型分布
        type_distribution = defaultdict(int)
        sharing_distribution = defaultdict(int)

        for memory in self.federated_memories.values():
            type_distribution[memory.memory_type] += 1
            sharing_distribution[memory.sharing_policy.value] += 1

        return {
            **self.statistics,
            'agent_id': self.agent_identity.agent_id,
            'active_peers': active_peers,
            'memory_type_distribution': dict(type_distribution),
            'sharing_policy_distribution': dict(sharing_distribution),
            'pending_updates': len(self.pending_updates),
            'unresolved_conflicts': len([m for m in self.federated_memories.values() if m.conflicts]),
            'total_endorsements': sum(len(m.endorsements) for m in self.federated_memories.values())
        }

# 创建联邦记忆系统实例的工厂函数
def create_federated_memory_system(agent_id: str, agent_name: str, agent_type: str,
                                  capabilities: list[str]) -> FederatedMemorySystem:
    """创建联邦记忆系统实例"""
    agent_identity = AgentIdentity(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_type=agent_type,
        capabilities=capabilities
    )
    return FederatedMemorySystem(agent_identity)

# 全局联邦记忆系统实例（如果需要单例模式）
federated_memory_system = None

def initialize_federated_memory(agent_id: str, agent_name: str, agent_type: str,
                              capabilities: list[str]) -> FederatedMemorySystem:
    """初始化全局联邦记忆系统"""
    global federated_memory_system
    federated_memory_system = create_federated_memory_system(
        agent_id, agent_name, agent_type, capabilities
    )
    return federated_memory_system

# 便捷函数
async def add_federated_memory(memory_id: str, content: Any, memory_type: str,
                              sharing_policy: MemorySharingPolicy = MemorySharingPolicy.SELECTIVE) -> bool:
    """添加联邦记忆"""
    if not federated_memory_system:
        raise RuntimeError('联邦记忆系统未初始化')

    memory = FederatedMemory(
        memory_id=memory_id,
        content=content,
        memory_type=memory_type,
        owner_agent_id=federated_memory_system.agent_identity.agent_id,
        sharing_policy=sharing_policy,
        consistency_level=MemoryConsistencyLevel.EVENTUAL,
        importance=0.5,
        created_at=datetime.now(),
        last_modified=datetime.now()
    )

    return await federated_memory_system.add_federated_memory(memory)

async def search_all_memories(query: str, limit: int = 10) -> list[tuple[FederatedMemory, float]]:
    """搜索所有记忆"""
    if not federated_memory_system:
        raise RuntimeError('联邦记忆系统未初始化')

    return await federated_memory_system.search_federated_memories(query, limit=limit)

