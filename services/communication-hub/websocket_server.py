"""
WebSocket服务器
提供实时通信接口
"""

import asyncio
import json
import logging
from datetime import datetime

import websockets
from message_bus import (
    Message,
    MessageType,
    message_bus,
    request_collaboration,
    send_task_update,
)
from websockets.asyncio.server import ServerConnection

from core.logging_config import setup_logging

# 类型别名，保持向后兼容
WebSocketServerProtocol = ServerConnection

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.connections: dict[str, WebSocketServerProtocol] = {}
        self.ai_connections: dict[str, str] = {}  # AI名称 -> 连接ID
        self.client_info: dict[str, dict] = {}

    async def register(self, websocket: WebSocketServerProtocol, connection_id: str,
                      client_type: str = 'client', ai_name: str = None) -> str:
        """注册连接"""
        self.connections[connection_id] = websocket
        self.client_info[connection_id] = {
            'type': client_type,
            'ai_name': ai_name,
            'connected_at': datetime.now(),
            'last_ping': datetime.now()
        }

        if client_type == 'ai' and ai_name:
            self.ai_connections[ai_name] = connection_id
            # AI连接后订阅相关消息
            await self._setup_ai_subscriptions(ai_name)

        # 注册到消息总线
        message_bus.register_websocket(connection_id, websocket)

        logger.info(f"WebSocket连接已注册: {connection_id} ({client_type}:{ai_name or 'N/A'})")

        # 发送欢迎消息
        await self.send_to_connection(connection_id, {
            'type': 'welcome',
            'connection_id': connection_id,
            'timestamp': datetime.now().isoformat()
        })

        return connection_id

    async def unregister(self, connection_id: str):
        """注销连接"""
        if connection_id in self.connections:
            client_info = self.client_info.get(connection_id, {})
            logger.info(f"WebSocket连接已注销: {connection_id} ({client_info})")

            # 清理AI连接
            if client_info.get('type') == 'ai':
                ai_name = client_info.get('ai_name')
                if ai_name and ai_name in self.ai_connections:
                    del self.ai_connections[ai_name]

            # 从消息总线注销
            message_bus.unregister_websocket(connection_id)

            del self.connections[connection_id]
            del self.client_info[connection_id]

    async def _setup_ai_subscriptions(self, ai_name: str):
        """为AI设置消息订阅"""
        async def ai_message_handler(message: Message):
            if message.recipient is None or message.recipient == ai_name:
                await self.send_to_connection(
                    self.ai_connections.get(ai_name),
                    {
                        'type': 'message',
                        'message_id': message.id,
                        'message_type': message.type.value,
                        'sender': message.sender,
                        'content': message.content,
                        'priority': message.priority.value,
                        'timestamp': message.timestamp.isoformat(),
                        'correlation_id': message.correlation_id
                    }
                )

        # AI订阅所有相关消息类型
        message_types = [
            MessageType.TASK_CREATED,
            MessageType.TASK_UPDATED,
            MessageType.COLLABORATION_REQUEST,
            MessageType.STATUS_UPDATE,
            MessageType.SYSTEM_NOTIFICATION
        ]

        message_bus.subscribe(ai_name, message_types, ai_message_handler)

    async def send_to_connection(self, connection_id: str, data: dict):
        """发送数据到特定连接"""
        if connection_id in self.connections:
            try:
                await self.connections[connection_id].send(json.dumps(data))
            except Exception as e:
                logger.error(f"发送消息失败 {connection_id}: {e}")
                # 连接可能已断开，尝试清理
                await self.unregister(connection_id)

    async def broadcast_to_all(self, data: dict, exclude_connection: str = None):
        """广播到所有连接"""
        for connection_id in list(self.connections.keys()):
            if connection_id != exclude_connection:
                await self.send_to_connection(connection_id, data)

    async def send_to_ai(self, ai_name: str, data: dict):
        """发送数据到特定AI"""
        if ai_name in self.ai_connections:
            connection_id = self.ai_connections[ai_name]
            await self.send_to_connection(connection_id, {
                **data,
                'target_ai': ai_name
            })

    async def handle_message(self, connection_id: str, message_data: dict):
        """处理接收到的消息"""
        client_info = self.client_info.get(connection_id, {})
        client_type = client_info.get('type', 'client')
        ai_name = client_info.get('ai_name')

        message_type = message_data.get('type')

        if message_type == 'ping':
            # 响应ping
            await self.send_to_connection(connection_id, {
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            })
            # 更新最后ping时间
            client_info['last_ping'] = datetime.now()

        elif message_type == 'task_update':
            # 任务更新
            if client_type == 'ai':
                await send_task_update(
                    sender=ai_name,
                    task_id=message_data.get('task_id'),
                    status=message_data.get('status'),
                    details=message_data.get('details')
                )

        elif message_type == 'collaboration_request':
            # 协作请求
            if client_type in ['client', 'ai']:
                message_id = await request_collaboration(
                    requester=ai_name or connection_id,
                    task_info=message_data.get('task_info', {}),
                    required_ais=message_data.get('required_ais', [])
                )
                await self.send_to_connection(connection_id, {
                    'type': 'collaboration_requested',
                    'message_id': message_id,
                    'timestamp': datetime.now().isoformat()
                })

        elif message_type == 'ai_response':
            # AI响应
            if client_type == 'ai':
                await message_bus.send_to_ai(
                    sender=ai_name,
                    recipient='system',
                    message_type=MessageType.AI_RESPONSE,
                    content={
                        'ai': ai_name,
                        'response': message_data.get('response'),
                        'correlation_id': message_data.get('correlation_id')
                    }
                )

        else:
            logger.warning(f"未知消息类型: {message_type}")

    def get_connection_stats(self) -> dict:
        """获取连接统计"""
        total_connections = len(self.connections)
        ai_connections = len(self.ai_connections)
        client_connections = total_connections - ai_connections

        return {
            'total_connections': total_connections,
            'ai_connections': ai_connections,
            'client_connections': client_connections,
            'connected_ais': list(self.ai_connections.keys()),
            'connection_details': {
                conn_id: {
                    'type': info['type'],
                    'ai_name': info.get('ai_name'),
                    'connected_at': info['connected_at'].isoformat(),
                    'last_ping': info['last_ping'].isoformat()
                }
                for conn_id, info in self.client_info.items()
            }
        }

# 全局WebSocket管理器
ws_manager = WebSocketManager()

# WebSocket处理函数
async def handle_client_connection(websocket: WebSocketServerProtocol, path: str):
    """处理客户端连接"""
    connection_id = f"client_{datetime.now().timestamp()}_{id(websocket)}"

    try:
        # 等待认证消息
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)

        if auth_data.get('type') == 'auth':
            client_type = auth_data.get('client_type', 'client')
            ai_name = auth_data.get('ai_name')

            # 注册连接
            await ws_manager.register(websocket, connection_id, client_type, ai_name)

            # 处理消息循环
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await ws_manager.handle_message(connection_id, data)
                except json.JSONDecodeError:
                    logger.error(f"无效的JSON消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"连接关闭: {connection_id}")
    except Exception as e:
        logger.error(f"连接错误 {connection_id}: {e}")
    finally:
        await ws_manager.unregister(connection_id)

# API函数
async def send_message_to_ai(ai_name: str, message: dict):
    """发送消息到特定AI"""
    await ws_manager.send_to_ai(ai_name, message)

async def broadcast_message(message: dict):
    """广播消息到所有连接"""
    await ws_manager.broadcast_to_all(message)

def get_active_connections():
    """获取活跃连接信息"""
    return ws_manager.get_connection_stats()

# 启动WebSocket服务器
async def start_websocket_server(host: str = '0.0.0.0', port: int = 8092):
    """启动WebSocket服务器"""
    logger.info(f"WebSocket服务器启动: ws://{host}:{port}")

    # 同时启动消息总线心跳
    asyncio.create_task(message_bus.start_heartbeat())

    # 启动WebSocket服务器
    server = await websockets.serve(handle_client_connection, host, port)

    return server

if __name__ == '__main__':
    logger.info(str("\n" + '='*60))
    logger.info('🔌 WebSocket通信服务器')
    logger.info(str('='*60))
    logger.info('📍 服务器地址: ws://localhost:8092')
    logger.info("\n📋 连接认证格式:")
    logger.info("  {'type': 'auth', 'client_type': 'ai', 'ai_name': 'athena'}")
    logger.info("  {'type': 'auth', 'client_type': 'client'}")
    logger.info("\n💬 支持的消息类型:")
    logger.info('  • ping - 心跳检测')
    logger.info('  • task_update - 任务更新')
    logger.info('  • collaboration_request - 协作请求')
    logger.info('  • ai_response - AI响应')
    logger.info(str('='*60 + "\n"))

    async def main():
        server = await start_websocket_server()
        await server.wait_closed()

    asyncio.run(main())
