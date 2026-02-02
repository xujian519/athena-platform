#!/usr/bin/env python3
"""
Qwen Code客户端集成演示
Qwen Code Client Integration Demo
"""

import asyncio
import json
import logging
import websockets
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QwenCodeClient:
    """Qwen Code客户端"""

    def __init__(self, client_id: str = "qwen_code_demo"):
        self.client_id = client_id
        self.server_url = "http://localhost:8090"
        self.ws_url = "ws://localhost:8090"
        self.capability = {
            "client_id": client_id,
            "llm_providers": [
                {
                    "name": "qwen",
                    "models": ["qwen-coder", "qwen-vl", "qwen-turbo"],
                    "max_tokens": 8000
                }
            ],
            "modalities": ["text", "code", "image"],
            "max_concurrent_tasks": 3,
            "resources": {
                "cpu": 8,
                "memory": "16GB",
                "gpu": "N/A"
            }
        }

    async def register(self):
        """注册客户端能力"""
        try:
            response = requests.post(
                f"{self.server_url}/api/v1/client/register",
                json=self.capability
            )
            if response.status_code == 200:
                logger.info(f"✅ 客户端 {self.client_id} 注册成功")
                return True
            else:
                logger.error(f"❌ 注册失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 注册异常: {e}")
            return False

    async def heartbeat_loop(self, websocket):
        """心跳循环"""
        while True:
            try:
                # 发送心跳
                await websocket.send(json.dumps({
                    "type": "heartbeat"
                }))
                logger.debug("💓 发送心跳")

                # 等待30秒
                await asyncio.sleep(30)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("❌ WebSocket连接已断开")
                break
            except Exception as e:
                logger.error(f"❌ 心跳异常: {e}")
                break

    async def handle_task(self, websocket, task_data):
        """处理接收到的任务"""
        task_id = task_data.get("task_id")
        task_type = task_data.get("task_type")
        payload = task_data.get("payload")

        logger.info(f"📋 接收到任务: {task_id}, 类型: {task_type}")

        try:
            # 根据任务类型执行相应处理
            if task_type == "code_generation":
                result = await self.generate_code(payload)
            elif task_type == "document_processing":
                result = await self.process_document(payload)
            elif task_type == "image_analysis":
                result = await self.analyze_image(payload)
            else:
                result = await self.process_with_llm(payload)

            # 发送任务结果
            result_message = {
                "type": "task_result",
                "result": {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result,
                    "execution_time": 1.5
                }
            }

            await websocket.send(json.dumps(result_message))
            logger.info(f"✅ 任务 {task_id} 完成")

        except Exception as e:
            logger.error(f"❌ 任务处理失败: {e}")
            # 发送错误结果
            error_message = {
                "type": "task_result",
                "result": {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(e)
                }
            }
            await websocket.send(json.dumps(error_message))

    async def generate_code(self, payload):
        """生成代码（模拟）"""
        prompt = payload.get("prompt", "")
        language = payload.get("language", "python")

        # 这里应该调用真实的Qwen Code模型
        # 示例返回
        if "二分查找" in prompt:
            return {
                "code": f"def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
                "language": language,
                "explanation": "实现了二分查找算法，时间复杂度O(log n)"
            }
        else:
            return {
                "code": f"# {prompt}\nprint('Hello from Qwen Code!')",
                "language": language,
                "explanation": "生成的示例代码"
            }

    async def process_document(self, payload):
        """处理文档（模拟）"""
        doc_path = payload.get("document_path", "")
        analysis_type = payload.get("analysis_type", "summary")

        # 模拟文档处理
        return {
            "summary": "这是一份关于人工智能技术的专利文档",
            "key_points": [
                "涉及深度学习算法",
                "应用于图像识别领域",
                "具有创新性的架构设计"
            ],
            "analysis_type": analysis_type,
            "confidence": 0.92
        }

    async def analyze_image(self, payload):
        """分析图像（模拟）"""
        image_path = payload.get("image_path", "")
        query = payload.get("query", "描述图像内容")

        # 模拟图像分析
        return {
            "description": "图像显示了一个技术架构图，包含多个模块和数据流向",
            "objects": ["服务器", "数据库", "客户端", "网络连接"],
            "confidence": 0.88
        }

    async def process_with_llm(self, payload):
        """使用LLM处理（模拟）"""
        query = payload.get("query", "")

        return {
            "response": f"Qwen处理结果：{query}",
            "confidence": 0.85
        }

    async def run(self):
        """运行客户端"""
        # 1. 注册客户端
        if not await self.register():
            return

        # 2. 建立WebSocket连接
        ws_uri = f"{self.ws_url}/ws/{self.client_id}"
        logger.info(f"🔗 连接到WebSocket: {ws_uri}")

        try:
            async with websockets.connect(ws_uri) as websocket:
                logger.info("✅ WebSocket连接成功")

                # 启动心跳任务
                heartbeat_task = asyncio.create_task(
                    self.heartbeat_loop(websocket)
                )

                # 主循环处理消息
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)

                        # 处理不同类型的消息
                        if data.get("action") == "execute_task":
                            await self.handle_task(websocket, data.get("task"))
                        elif data.get("type") == "heartbeat_response":
                            logger.debug("💗 收到心跳响应")
                        else:
                            logger.info(f"📨 收到消息: {data.get('type')}")

                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket连接关闭")
                    heartbeat_task.cancel()

        except Exception as e:
            logger.error(f"❌ WebSocket连接失败: {e}")


async def test_task_submission():
    """测试任务提交"""
    logger.info("🧪 测试任务提交...")

    # 提交代码生成任务
    task_request = {
        "task_id": f"test_{datetime.now().timestamp()}",
        "task_type": "code_generation",
        "payload": {
            "prompt": "实现一个快速排序算法",
            "language": "python"
        },
        "requirements": {
            "max_tokens": 500,
            "temperature": 0.3
        }
    }

    try:
        response = requests.post(
            "http://localhost:8090/api/v1/task/submit",
            json=task_request
        )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ 任务提交成功: {result}")
        else:
            logger.error(f"❌ 任务提交失败: {response.text}")
    except Exception as e:
        logger.error(f"❌ 任务提交异常: {e}")


async def main():
    """主函数"""
    print("="*60)
    print("🚀 Qwen Code客户端集成演示")
    print("="*60)
    print()

    # 创建客户端
    client = QwenCodeClient()

    # 运行客户端
    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("\n👋 客户端已停止")


if __name__ == "__main__":
    # 演示选项
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 测试任务提交
        asyncio.run(test_task_submission())
    else:
        # 运行客户端
        asyncio.run(main())