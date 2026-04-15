#!/usr/bin/env python3
"""
Athena平台实时协作系统
提供多用户实时协作、冲突解决、版本控制等功能
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import diff_match_patch as dmp_module
import websockets

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class CollaborationEventType(Enum):
    """协作事件类型"""
    USER_JOIN = 'user_join'
    USER_LEAVE = 'user_leave'
    DOCUMENT_CHANGE = 'document_change'
    CURSOR_MOVE = 'cursor_move'
    SELECTION_CHANGE = 'selection_change'
    COMMENT_ADD = 'comment_add'
    COMMENT_RESOLVE = 'comment_resolve'
    OPERATION = 'operation'
    LOCK_ACQUIRE = 'lock_acquire'
    LOCK_RELEASE = 'lock_release'
    PRESENCE_UPDATE = 'presence_update'

class OperationType(Enum):
    """操作类型"""
    INSERT = 'insert'
    DELETE = 'delete'
    RETAIN = 'retain'
    FORMAT = 'format'

class ConflictResolutionStrategy(Enum):
    """冲突解决策略"""
    LAST_WRITER_WINS = 'last_writer_wins'
    OPERATIONAL_TRANSFORM = 'operational_transform'
    THREE_WAY_MERGE = 'three_way_merge'
    MANUAL_INTERVENTION = 'manual_intervention'

@dataclass
class User:
    """协作用户"""
    user_id: str
    username: str
    email: str
    avatar_url: str | None = None
    role: str = 'editor'  # owner, editor, viewer
    permissions: set[str] = field(default_factory=set)
    is_online: bool = True
    last_active: datetime = field(default_factory=datetime.now)
    cursor_position: int | None = None
    selection_range: tuple | None = None

@dataclass
class DocumentVersion:
    """文档版本"""
    version_id: str
    document_id: str
    content: str
    timestamp: datetime
    author_id: str
    changes_summary: str
    parent_version_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Operation:
    """文档操作"""
    operation_id: str
    user_id: str
    document_id: str
    operation_type: OperationType
    position: int
    content: str | None = None
    length: int | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    author_info: dict[str, Any] = field(default_factory=dict)

@dataclass
class Comment:
    """文档注释"""
    comment_id: str
    document_id: str
    user_id: str
    position: int
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    replies: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class CollaborationEvent:
    """协作事件"""
    event_id: str
    event_type: CollaborationEventType
    user_id: str
    document_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class DocumentLockManager:
    """文档锁管理器"""

    def __init__(self):
        """初始化锁管理器"""
        self.locks = {}  # document_id -> {section_id -> lock_info}
        self.lock_timeouts = {}  # lock_id -> timeout_task

    async def acquire_lock(self, document_id: str, section_id: str, user_id: str,
                          timeout: int = 300) -> bool:
        """获取文档锁"""
        lock_key = f"{document_id}_{section_id}"

        # 检查是否已被锁定
        if lock_key in self.locks:
            existing_lock = self.locks[lock_key]
            if existing_lock['user_id'] != user_id:
                # 检查是否过期
                if datetime.now() < existing_lock['expires_at']:
                    return False
                else:
                    # 清理过期锁
                    await self.release_lock(document_id, section_id, existing_lock['user_id'])

        # 创建新锁
        lock_info = {
            'user_id': user_id,
            'acquired_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=timeout),
            'section_id': section_id
        }

        self.locks[lock_key] = lock_info

        # 设置自动过期
        lock_id = f"{lock_key}_{user_id}"
        if lock_id in self.lock_timeouts:
            self.lock_timeouts[lock_id].cancel()

        self.lock_timeouts[lock_id] = asyncio.create_task(
            self._auto_release_lock(document_id, section_id, user_id, timeout)
        )

        return True

    async def release_lock(self, document_id: str, section_id: str, user_id: str) -> bool:
        """释放文档锁"""
        lock_key = f"{document_id}_{section_id}"

        if lock_key in self.locks:
            lock_info = self.locks[lock_key]
            if lock_info['user_id'] == user_id:
                del self.locks[lock_key]

                # 取消自动过期任务
                lock_id = f"{lock_key}_{user_id}"
                if lock_id in self.lock_timeouts:
                    self.lock_timeouts[lock_id].cancel()
                    del self.lock_timeouts[lock_id]

                return True

        return False

    async def _auto_release_lock(self, document_id: str, section_id: str, user_id: str, timeout: int):
        """自动释放锁"""
        await asyncio.sleep(timeout)
        await self.release_lock(document_id, section_id, user_id)
        logger.info(f"自动释放过期锁: {document_id}_{section_id} by {user_id}")

    def is_locked(self, document_id: str, section_id: str, user_id: str = None) -> bool:
        """检查是否被锁定"""
        lock_key = f"{document_id}_{section_id}"

        if lock_key not in self.locks:
            return False

        if user_id is None:
            return True

        return self.locks[lock_key]['user_id'] != user_id

    def get_lock_info(self, document_id: str, section_id: str) -> dict[str, Any | None]:
        """获取锁信息"""
        lock_key = f"{document_id}_{section_id}"
        return self.locks.get(lock_key)

class OperationalTransform:
    """操作变换引擎"""

    def __init__(self):
        """初始化操作变换引擎"""
        self.dmp = dmp_module.diff_match_patch()

    def transform(self, op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """对两个操作进行变换"""
        if op1.operation_type == OperationType.INSERT and op2.operation_type == OperationType.INSERT:
            return self._transform_insert_insert(op1, op2)
        elif op1.operation_type == OperationType.INSERT and op2.operation_type == OperationType.DELETE:
            return self._transform_insert_delete(op1, op2)
        elif op1.operation_type == OperationType.DELETE and op2.operation_type == OperationType.INSERT:
            op2_prime, op1_prime = self._transform_insert_delete(op2, op1)
            return op1_prime, op2_prime
        elif op1.operation_type == OperationType.DELETE and op2.operation_type == OperationType.DELETE:
            return self._transform_delete_delete(op1, op2)
        else:
            # 对于其他操作类型，暂时返回原操作
            return op1, op2

    def _transform_insert_insert(self, op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """变换插入-插入操作"""
        if op1.position <= op2.position:
            # op1在op2之前或同位置
            op2_prime = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=op2.user_id,
                document_id=op2.document_id,
                operation_type=op2.operation_type,
                position=op2.position + len(op2.content or ''),
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp
            )
            return op1, op2_prime
        else:
            # op1在op2之后
            op1_prime = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=op1.user_id,
                document_id=op1.document_id,
                operation_type=op1.operation_type,
                position=op1.position + len(op2.content or ''),
                content=op1.content,
                length=op1.length,
                attributes=op1.attributes,
                timestamp=op1.timestamp
            )
            return op1_prime, op2

    def _transform_insert_delete(self, insert_op: Operation, delete_op: Operation) -> tuple[Operation, Operation]:
        """变换插入-删除操作"""
        if insert_op.position <= delete_op.position:
            # 插入在删除之前
            delete_prime = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=delete_op.user_id,
                document_id=delete_op.document_id,
                operation_type=delete_op.operation_type,
                position=delete_op.position + len(insert_op.content or ''),
                content=delete_op.content,
                length=delete_op.length,
                attributes=delete_op.attributes,
                timestamp=delete_op.timestamp
            )
            return insert_op, delete_prime
        elif insert_op.position >= delete_op.position + (delete_op.length or 0):
            # 插入在删除之后
            insert_prime = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=insert_op.user_id,
                document_id=insert_op.document_id,
                operation_type=insert_op.operation_type,
                position=insert_op.position - (delete_op.length or 0),
                content=insert_op.content,
                length=insert_op.length,
                attributes=insert_op.attributes,
                timestamp=insert_op.timestamp
            )
            return insert_prime, delete_op
        else:
            # 插入在删除范围内，删除操作优先
            return insert_op, delete_op

    def _transform_delete_delete(self, op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """变换删除-删除操作"""
        if op1.position + (op1.length or 0) <= op2.position:
            # op1完全在op2之前
            op2_prime = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=op2.user_id,
                document_id=op2.document_id,
                operation_type=op2.operation_type,
                position=op2.position - (op1.length or 0),
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp
            )
            return op1, op2_prime
        elif op2.position + (op2.length or 0) <= op1.position:
            # op2完全在op1之前
            op1_prime = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=op1.user_id,
                document_id=op1.document_id,
                operation_type=op1.operation_type,
                position=op1.position - (op2.length or 0),
                content=op1.content,
                length=op1.length,
                attributes=op1.attributes,
                timestamp=op1.timestamp
            )
            return op1_prime, op2
        else:
            # 删除范围重叠，需要合并
            start1 = op1.position
            end1 = op1.position + (op1.length or 0)
            start2 = op2.position
            end2 = op2.position + (op2.length or 0)

            # 计算新的删除范围
            new_start = min(start1, start2)
            new_end = max(end1, end2)
            new_length = new_end - new_start

            # 创建合并后的操作
            merged_op = Operation(
                operation_id=str(uuid.uuid4()),
                user_id=op1.user_id,  # 保留第一个操作的用户
                document_id=op1.document_id,
                operation_type=OperationType.DELETE,
                position=new_start,
                length=new_length,
                timestamp=max(op1.timestamp, op2.timestamp)
            )

            return merged_op, None

    def apply_operation(self, content: str, operation: Operation) -> str:
        """应用操作到内容"""
        if operation.operation_type == OperationType.INSERT:
            if operation.content:
                return content[:operation.position] + operation.content + content[operation.position:]
        elif operation.operation_type == OperationType.DELETE:
            if operation.length:
                return content[:operation.position] + content[operation.position + operation.length:]
        elif operation.operation_type == OperationType.FORMAT:
            # 格式化操作暂时不改变内容
            return content
        elif operation.operation_type == OperationType.RETAIN:
            # 保留操作不改变内容
            return content

        return content

class CollaborationSession:
    """协作会话"""

    def __init__(self, session_id: str, document_id: str):
        """初始化协作会话"""
        self.session_id = session_id
        self.document_id = document_id
        self.users = {}  # user_id -> User
        self.document_content = ''
        self.operations = []  # 操作历史
        self.comments = {}  # comment_id -> Comment
        self.versions = []  # 版本历史
        self.events = []  # 事件历史
        self.lock_manager = DocumentLockManager()
        self.ot_engine = OperationalTransform()
        self.websockets = set()  # 连接的WebSocket
        self.active_operations = {}  # user_id -> Operation

    async def add_user(self, user: User) -> bool:
        """添加用户到会话"""
        if user.user_id in self.users:
            # 更新现有用户
            self.users[user.user_id].is_online = True
            self.users[user.user_id].last_active = datetime.now()
            return True

        self.users[user.user_id] = user

        # 发送用户加入事件
        await self.broadcast_event(CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=CollaborationEventType.USER_JOIN,
            user_id=user.user_id,
            document_id=self.document_id,
            data={
                'user_info': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'avatar_url': user.avatar_url,
                    'role': user.role
                }
            }
        ))

        logger.info(f"用户 {user.username} 加入会话 {self.session_id}")
        return True

    async def remove_user(self, user_id: str) -> bool:
        """从会话移除用户"""
        if user_id not in self.users:
            return False

        user = self.users[user_id]
        user.is_online = False
        user.last_active = datetime.now()

        # 释放用户的所有锁
        for lock_key in list(self.lock_manager.locks.keys()):
            if lock_key.startswith(f"{self.document_id}_"):
                lock_info = self.lock_manager.locks[lock_key]
                if lock_info['user_id'] == user_id:
                    section_id = lock_info.split('_')[-1]
                    await self.lock_manager.release_lock(self.document_id, section_id, user_id)

        # 发送用户离开事件
        await self.broadcast_event(CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=CollaborationEventType.USER_LEAVE,
            user_id=user_id,
            document_id=self.document_id,
            data={'user_info': {'user_id': user.user_id, 'username': user.username}}
        ))

        logger.info(f"用户 {user.username} 离开会话 {self.session_id}")
        return True

    async def apply_operation(self, operation: Operation) -> bool:
        """应用文档操作"""
        # 检查用户权限
        user = self.users.get(operation.user_id)
        if not user or not self._has_permission(user, 'edit'):
            return False

        # 操作变换
        transformed_operation = operation
        for existing_op in self.operations:
            if existing_op.user_id != operation.user_id:
                # 对每个其他用户的操作进行变换
                transformed_operation, _ = self.ot_engine.transform(
                    transformed_operation, existing_op
                )

        # 应用操作
        self.document_content = self.ot_engine.apply_operation(
            self.document_content, transformed_operation
        )

        # 记录操作
        self.operations.append(transformed_operation)

        # 发送操作事件
        await self.broadcast_event(CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=CollaborationEventType.OPERATION,
            user_id=operation.user_id,
            document_id=self.document_id,
            data={
                'operation': {
                    'type': transformed_operation.operation_type.value,
                    'position': transformed_operation.position,
                    'content': transformed_operation.content,
                    'length': transformed_operation.length,
                    'attributes': transformed_operation.attributes
                },
                'author_info': transformed_operation.author_info
            }
        ))

        return True

    async def add_comment(self, comment: Comment) -> bool:
        """添加注释"""
        user = self.users.get(comment.user_id)
        if not user:
            return False

        self.comments[comment.comment_id] = comment

        # 发送注释事件
        await self.broadcast_event(CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=CollaborationEventType.COMMENT_ADD,
            user_id=comment.user_id,
            document_id=self.document_id,
            data={
                'comment': {
                    'id': comment.comment_id,
                    'position': comment.position,
                    'content': comment.content,
                    'user_id': comment.user_id,
                    'username': user.username,
                    'created_at': comment.created_at.isoformat()
                }
            }
        ))

        return True

    async def resolve_comment(self, comment_id: str, user_id: str) -> bool:
        """解决注释"""
        if comment_id not in self.comments:
            return False

        comment = self.comments[comment_id]
        comment.resolved = True
        comment.resolved_by = user_id
        comment.resolved_at = datetime.now()

        # 发送解决注释事件
        await self.broadcast_event(CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=CollaborationEventType.COMMENT_RESOLVE,
            user_id=user_id,
            document_id=self.document_id,
            data={
                'comment_id': comment_id,
                'resolved_by': user_id,
                'resolved_at': comment.resolved_at.isoformat()
            }
        ))

        return True

    async def update_cursor(self, user_id: str, position: int, selection: tuple = None):
        """更新用户光标位置"""
        user = self.users.get(user_id)
        if not user:
            return

        user.cursor_position = position
        user.selection_range = selection
        user.last_active = datetime.now()

        # 发送光标更新事件
        await self.broadcast_event(CollaborationEvent(
            event_id=str(uuid.uuid4()),
            event_type=CollaborationEventType.CURSOR_MOVE,
            user_id=user_id,
            document_id=self.document_id,
            data={
                'position': position,
                'selection': selection
            }
        ), exclude_user=user_id)

    async def broadcast_event(self, event: CollaborationEvent, exclude_user: str = None):
        """广播协作事件"""
        self.events.append(event)

        # 通过WebSocket广播
        message = {
            'type': 'collaboration_event',
            'event': {
                'id': event.event_id,
                'type': event.event_type.value,
                'user_id': event.user_id,
                'timestamp': event.timestamp.isoformat(),
                'data': event.data
            }
        }

        for websocket in self.websockets.copy():
            try:
                # 检查是否需要排除特定用户
                if hasattr(websocket, 'user_id') and websocket.user_id == exclude_user:
                    continue

                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"发送事件失败: {e}")
                self.websockets.discard(websocket)

    def _has_permission(self, user: User, permission: str) -> bool:
        """检查用户权限"""
        if user.role == 'owner':
            return True
        elif user.role == 'editor':
            return permission in ['edit', 'view', 'comment']
        elif user.role == 'viewer':
            return permission in ['view', 'comment']
        return permission in user.permissions

    def create_version(self, author_id: str, changes_summary: str) -> DocumentVersion:
        """创建文档版本"""
        version_id = str(uuid.uuid4())
        parent_version_id = self.versions[-1].version_id if self.versions else None

        version = DocumentVersion(
            version_id=version_id,
            document_id=self.document_id,
            content=self.document_content,
            timestamp=datetime.now(),
            author_id=author_id,
            changes_summary=changes_summary,
            parent_version_id=parent_version_id
        )

        self.versions.append(version)
        return version

    def get_session_stats(self) -> dict[str, Any]:
        """获取会话统计"""
        online_users = sum(1 for user in self.users.values() if user.is_online)

        return {
            'session_id': self.session_id,
            'document_id': self.document_id,
            'total_users': len(self.users),
            'online_users': online_users,
            'total_operations': len(self.operations),
            'total_comments': len(self.comments),
            'total_versions': len(self.versions),
            'active_locks': len(self.lock_manager.locks),
            'content_length': len(self.document_content)
        }

class RealtimeCollaborationServer:
    """实时协作服务器"""

    def __init__(self):
        """初始化协作服务器"""
        self.sessions = {}  # session_id -> CollaborationSession
        self.documents = {}  # document_id -> document_info
        self.websocket_sessions = {}  # websocket -> session_id

    async def create_session(self, document_id: str, user: User) -> CollaborationSession:
        """创建协作会话"""
        session_id = str(uuid.uuid4())
        session = CollaborationSession(session_id, document_id)

        # 添加创建者到会话
        await session.add_user(user)
        user.role = 'owner'  # 创建者为所有者

        self.sessions[session_id] = session

        logger.info(f"创建协作会话: {session_id} for document {document_id}")
        return session

    async def join_session(self, session_id: str, user: User) -> bool:
        """加入协作会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        return await session.add_user(user)

    async def leave_session(self, session_id: str, user_id: str) -> bool:
        """离开协作会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        return await session.remove_user(user_id)

    async def handle_websocket(self, websocket, path: str):
        """处理WebSocket连接"""
        try:
            # 解析路径和参数
            params = self._parse_websocket_path(path)
            session_id = params.get('session_id')
            user_id = params.get('user_id')

            if not session_id or not user_id:
                await websocket.close(code=4000, reason='缺少必要参数')
                return

            session = self.sessions.get(session_id)
            if not session:
                await websocket.close(code=4001, reason='会话不存在')
                return

            # 关联WebSocket和会话
            websocket.user_id = user_id
            session.websockets.add(websocket)
            self.websocket_sessions[websocket] = session_id

            logger.info(f"WebSocket连接建立: {user_id} -> {session_id}")

            # 发送初始状态
            await self._send_initial_state(websocket, session)

            # 处理消息
            async for message in websocket:
                await self._handle_websocket_message(websocket, session, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket连接关闭: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket处理异常: {e}")
        finally:
            # 清理连接
            if websocket in self.websocket_sessions:
                session_id = self.websocket_sessions[websocket]
                session = self.sessions.get(session_id)
                if session:
                    session.websockets.discard(websocket)

                del self.websocket_sessions[websocket]

                # 如果用户完全离线，从会话移除
                if session and websocket.user_id:
                    await self._handle_user_offline(session, websocket.user_id)

    def _parse_websocket_path(self, path: str) -> dict[str, str]:
        """解析WebSocket路径"""
        # 简单的路径解析: /ws/collaboration/{session_id}?user_id={user_id}
        parts = path.strip('/').split('/')

        if len(parts) >= 4 and parts[1] == 'ws' and parts[2] == 'collaboration':
            session_id = parts[3]

            # 解析查询参数
            query_params = {}
            if '?' in parts[3]:
                session_id, query = parts[3].split('?', 1)
                for param in query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value

            return {'session_id': session_id, **query_params}

        return {}

    async def _send_initial_state(self, websocket, session: CollaborationSession):
        """发送初始状态"""
        user = session.users.get(websocket.user_id)
        if not user:
            return

        state = {
            'type': 'initial_state',
            'session_info': session.get_session_stats(),
            'document_content': session.document_content,
            'online_users': [
                {
                    'user_id': u.user_id,
                    'username': u.username,
                    'avatar_url': u.avatar_url,
                    'role': u.role,
                    'cursor_position': u.cursor_position,
                    'selection_range': u.selection_range
                }
                for u in session.users.values() if u.is_online
            ],
            'comments': [
                {
                    'id': comment.comment_id,
                    'position': comment.position,
                    'content': comment.content,
                    'user_id': comment.user_id,
                    'created_at': comment.created_at.isoformat(),
                    'resolved': comment.resolved
                }
                for comment in session.comments.values()
            ],
            'user_permissions': {
                'can_edit': session._has_permission(user, 'edit'),
                'can_comment': session._has_permission(user, 'comment'),
                'can_view': session._has_permission(user, 'view')
            }
        }

        await websocket.send(json.dumps(state))

    async def _handle_websocket_message(self, websocket, session: CollaborationSession, message: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'operation':
                operation = Operation(
                    operation_id=str(uuid.uuid4()),
                    user_id=websocket.user_id,
                    document_id=session.document_id,
                    operation_type=OperationType(data['operation']['type']),
                    position=data['operation']['position'],
                    content=data['operation'].get('content'),
                    length=data['operation'].get('length'),
                    attributes=data['operation'].get('attributes', {}),
                    author_info=data.get('author_info', {})
                )
                await session.apply_operation(operation)

            elif message_type == 'cursor_update':
                await session.update_cursor(
                    websocket.user_id,
                    data['position'],
                    data.get('selection')
                )

            elif message_type == 'comment_add':
                comment = Comment(
                    comment_id=str(uuid.uuid4()),
                    document_id=session.document_id,
                    user_id=websocket.user_id,
                    position=data['position'],
                    content=data['content']
                )
                await session.add_comment(comment)

            elif message_type == 'comment_resolve':
                await session.resolve_comment(data['comment_id'], websocket.user_id)

            elif message_type == 'lock_acquire':
                success = await session.lock_manager.acquire_lock(
                    session.document_id,
                    data.get('section_id', 'document'),
                    websocket.user_id,
                    data.get('timeout', 300)
                )

                await websocket.send(json.dumps({
                    'type': 'lock_response',
                    'action': 'acquire',
                    'section_id': data.get('section_id', 'document'),
                    'success': success
                }))

            elif message_type == 'lock_release':
                success = await session.lock_manager.release_lock(
                    session.document_id,
                    data.get('section_id', 'document'),
                    websocket.user_id
                )

                await websocket.send(json.dumps({
                    'type': 'lock_response',
                    'action': 'release',
                    'section_id': data.get('section_id', 'document'),
                    'success': success
                }))

        except json.JSONDecodeError:
            logger.error('无效的JSON消息')
        except Exception as e:
            logger.error(f"处理WebSocket消息异常: {e}")

    async def _handle_user_offline(self, session: CollaborationSession, user_id: str):
        """处理用户离线"""
        # 检查用户是否还有其他连接
        has_connection = any(
            ws.user_id == user_id
            for ws in session.websockets
            if hasattr(ws, 'user_id')
        )

        if not has_connection:
            await session.remove_user(user_id)

    def get_all_sessions(self) -> list[dict[str, Any]]:
        """获取所有会话信息"""
        return [
            {
                'session_id': session.session_id,
                'document_id': session.document_id,
                'online_users': sum(1 for user in session.users.values() if user.is_online),
                'total_operations': len(session.operations),
                'total_comments': len(session.comments),
                'created_at': min(u.last_active for u in session.users.values()).isoformat() if session.users else None
            }
            for session in self.sessions.values()
        ]

# 全局协作服务器实例
_collaboration_server = None

def get_collaboration_server() -> RealtimeCollaborationServer:
    """获取协作服务器实例"""
    global _collaboration_server
    if _collaboration_server is None:
        _collaboration_server = RealtimeCollaborationServer()
    return _collaboration_server

# 工具函数
async def start_collaboration_server(host: str = '0.0.0.0', port: int = 8080):
    """启动协作服务器"""
    server = get_collaboration_server()

    logger.info(f"启动实时协作服务器: {host}:{port}")

    async with websockets.serve(server.handle_websocket, host, port, path='/ws/collaboration'):
        logger.info('协作服务器启动成功')
        await asyncio.Future()  # 永久运行

if __name__ == '__main__':
    async def test_collaboration():
        """测试协作系统"""
        server = get_collaboration_server()

        # 创建测试用户
        user1 = User(
            user_id='user1',
            username='Alice',
            email='alice@example.com',
            role='owner'
        )

        user2 = User(
            user_id='user2',
            username='Bob',
            email='bob@example.com',
            role='editor'
        )

        # 创建会话
        session = await server.create_session('doc1', user1)

        # 用户2加入会话
        await server.join_session(session.session_id, user2)

        # 应用操作
        operation1 = Operation(
            operation_id=str(uuid.uuid4()),
            user_id=user1.user_id,
            document_id='doc1',
            operation_type=OperationType.INSERT,
            position=0,
            content='Hello World'
        )

        await session.apply_operation(operation1)

        operation2 = Operation(
            operation_id=str(uuid.uuid4()),
            user_id=user2.user_id,
            document_id='doc1',
            operation_type=OperationType.INSERT,
            position=5,
            content=' Collaborative'
        )

        await session.apply_operation(operation2)

        # 添加注释
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            document_id='doc1',
            user_id=user1.user_id,
            position=0,
            content='这是一个测试注释'
        )

        await session.add_comment(comment)

        # 输出结果
        logger.info(f"文档内容: {session.document_content}")
        logger.info(f"会话统计: {session.get_session_stats()}")

    asyncio.run(test_collaboration())
