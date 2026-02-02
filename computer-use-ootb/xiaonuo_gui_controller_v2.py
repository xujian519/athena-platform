#!/usr/bin/env python3
"""
小诺GUI控制器 V2 - 集成真正的GLM-4V API
支持智能屏幕分析和GUI操作
"""

import asyncio
import base64
import io
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 导入GUI操作库
import pyautogui
import pyperclip
from PIL import ImageGrab

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 导入GLM视觉客户端
from glm_vision_client import GLMVisionClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="小诺GUI控制器 V2",
    description="基于GLM-4V的智能GUI操作服务",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置
class Config:
    GLM_API_KEY = "9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"
    GLM_MODEL = "glm-4v-plus"
    SCREENSHOT_DIR = Path("/tmp/xiaonuo_screenshots")

    @classmethod
    def init(cls):
        cls.SCREENSHOT_DIR.mkdir(exist_ok=True)

# 初始化配置
Config.init()

# 请求模型
class CommandRequest(BaseModel):
    command: str
    enable_confirmation: bool = True
    timeout: int = 30

class ScreenAnalysisRequest(BaseModel):
    question: str
    model: str = "glm-4v-plus"

# 增强的GUI控制器类
class XiaonuoGUIControllerV2:
    def __init__(self):
        self.pyautogui = pyautogui
        self.pyautogui.PAUSE = 0.5
        self.pyautogui.FAILSAFE = True
        self.glm_client = GLMVisionClient(Config.GLM_API_KEY)

    def capture_screen(self) -> bytes:
        """截取屏幕"""
        screenshot = ImageGrab.grab()
        # 转换为bytes
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()

    def save_screenshot(self, image_bytes: bytes, filename: str = None) -> str:
        """保存截图"""
        if filename is None:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = Config.SCREENSHOT_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        return str(filepath)

    async def analyze_screen_with_glm(self, image_bytes: bytes, question: str) -> Dict:
        """使用GLM-4V分析屏幕"""
        logger.info(f"GLM分析问题: {question[:100]}...")
        result = await self.glm_client.analyze_image(
            image_bytes,
            question,
            Config.GLM_MODEL
        )

        if result["success"]:
            logger.info(f"GLM分析成功: {result['content'][:200]}...")
        else:
            logger.error(f"GLM分析失败: {result.get('error', '未知错误')}")

        return result

    def extract_actions_from_glm_response(self, glm_response: str) -> List[Dict]:
        """从GLM响应中提取操作指令"""
        actions = []

        # 分析GLM响应，提取具体操作
        response_lower = glm_response.lower()

        # 检测点击操作
        if "点击" in response_lower or "click" in response_lower:
            actions.append({
                "type": "click",
                "description": "点击指定位置",
                "confidence": 0.8
            })

        # 检测输入操作
        if "输入" in response_lower or "打字" in response_lower or "type" in response_lower:
            actions.append({
                "type": "type",
                "description": "输入文本",
                "confidence": 0.8
            })

        # 检测滚动操作
        if "滚动" in response_lower or "scroll" in response_lower:
            actions.append({
                "type": "scroll",
                "description": "滚动屏幕",
                "confidence": 0.7
            })

        # 检测拖拽操作
        if "拖拽" in response_lower or "drag" in response_lower:
            actions.append({
                "type": "drag",
                "description": "拖拽操作",
                "confidence": 0.7
            })

        # 检测快捷键操作
        if "快捷键" in response_lower or "command" in response_lower or "ctrl" in response_lower:
            actions.append({
                "type": "hotkey",
                "description": "使用快捷键",
                "confidence": 0.6
            })

        return actions

    async def execute_action(self, action: Dict) -> bool:
        """执行GUI操作"""
        try:
            action_type = action.get("type")
            description = action.get("description", "")

            print(f"\n🎯 执行操作: {description}")

            if action_type == "click":
                return await self.execute_click_with_guidance(action)

            elif action_type == "type":
                return await self.execute_type_with_guidance(action)

            elif action_type == "scroll":
                # 根据GLM建议滚动方向
                await self.execute_scroll_with_guidance(action)

            elif action_type == "drag":
                return await self.execute_drag_with_guidance(action)

            elif action_type == "hotkey":
                return await self.execute_hotkey_with_guidance(action)

            else:
                logger.warning(f"未知操作类型: {action_type}")
                return False

        except Exception as e:
            logger.error(f"执行操作失败: {e}")
            return False

    async def execute_click_with_guidance(self, action: Dict) -> bool:
        """引导式点击操作"""
        print("\n📍 请移动鼠标到要点击的位置，然后按回车键确认...")
        print("   (按ESC键取消操作，按Q键跳过此操作)")

        while True:
            try:
                x, y = pyautogui.position()
                print(f"   当前鼠标位置: ({x}, {y})")

                # 简单的键盘输入处理
                import sys
                import select
                import termios
                import tty

                # 设置非阻塞输入
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())

                    # 等待用户输入
                    ready, _, _ = select.select([sys.stdin], [], [], 1)
                    if ready:
                        key = sys.stdin.read(1)
                        if key == '\r' or key == '\n':
                            self.pyautogui.click(x, y)
                            print(f"   ✓ 已点击位置 ({x}, {y})")
                            return True
                        elif key == '\x1b' or key.lower() == 'q':
                            print("   ✗ 操作已取消")
                            return False
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

            except Exception as e:
                logger.error(f"点击操作异常: {e}")
                return False

    async def execute_type_with_guidance(self, action: Dict) -> bool:
        """引导式文本输入"""
        print("\n⌨️  请输入要输入的文本:")
        try:
            text = input("   文本内容: ")
            if text:
                pyperclip.copy(text)
                # 模拟粘贴操作
                self.pyautogui.hotkey('command', 'v')
                print(f"   ✓ 已输入文本")
                return True
            return False
        except Exception as e:
            logger.error(f"输入操作异常: {e}")
            return False

    async def execute_scroll_with_guidance(self, action: Dict):
        """滚动操作"""
        print("   🔄 正在滚动屏幕...")
        # 默认向下滚动
        for _ in range(3):
            self.pyautogui.scroll(-3)
            await asyncio.sleep(0.5)
        print("   ✓ 滚动完成")
        return True

    async def execute_drag_with_guidance(self, action: Dict) -> bool:
        """拖拽操作"""
        print("📌 拖拽操作：请先按回车记录起始位置，然后移动鼠标并再次按回车...")
        # 简化的拖拽实现
        try:
            input("   按回车开始拖拽...")
            start_x, start_y = pyautogui.position()

            input("   移动到目标位置后按回车...")
            end_x, end_y = pyautogui.position()

            # 执行拖拽
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=1)
            print(f"   ✓ 拖拽完成: ({start_x},{start_y}) -> ({end_x},{end_y})")
            return True
        except Exception as e:
            logger.error(f"拖拽操作异常: {e}")
            return False

    async def execute_hotkey_with_guidance(self, action: Dict) -> bool:
        """快捷键操作"""
        print("⌨️  快捷键操作：请输入要执行的快捷键（如：command+c, command+v）")
        try:
            hotkey = input("   快捷键: ")
            if hotkey:
                keys = hotkey.split('+')
                if len(keys) == 2:
                    pyautogui.hotkey(keys[0], keys[1])
                    print(f"   ✓ 已执行快捷键: {hotkey}")
                    return True
        except Exception as e:
            logger.error(f"快捷键操作异常: {e}")
            return False

    async def process_command(self, command: str) -> Dict:
        """处理用户命令"""
        logger.info(f"处理命令: {command}")

        try:
            # 1. 截取当前屏幕
            screen_bytes = self.capture_screen()
            saved_path = self.save_screenshot(screen_bytes)
            logger.info(f"屏幕截图已保存: {saved_path}")

            # 2. 使用GLM-4V分析屏幕并理解命令
            analysis_question = f"""
            请分析这个屏幕截图，并告诉我如何执行以下操作：{command}

            请提供详细的步骤说明，包括：
            1. 当前屏幕的主要内容和布局分析
            2. 执行操作的具体步骤
            3. 需要点击的位置或区域描述
            4. 需要输入的文本内容（如果需要）
            5. 可能的快捷键操作（如果适用）

            请用中文回答，并提供清晰的操作指导。
            """

            glm_result = await self.analyze_screen_with_glm(screen_bytes, analysis_question)

            if not glm_result["success"]:
                return {
                    "success": False,
                    "error": glm_result.get("error", "GLM分析失败"),
                    "message": "GLM视觉分析失败"
                }

            # 3. 提取并执行操作
            glm_content = glm_result.get("content", "")
            logger.info(f"GLM分析成功")

            # 4. 执行操作
            print("\n📋 GLM分析结果:")
            print("=" * 50)
            print(glm_content)
            print("=" * 50)

            # 5. 询问用户是否要执行操作
            if input("\n❓ 是否要根据GLM的建议执行操作？(y/n): ").lower() == 'y':
                actions = self.extract_actions_from_glm_response(glm_content)

                if actions:
                    print(f"\n🎯 检测到 {len(actions)} 个操作:")
                    for i, action in enumerate(actions):
                        print(f"   {i+1}. {action['description']} (置信度: {action.get('confidence', 0):.1f})")

                    if input("\n❓ 确认执行这些操作？(y/n): ").lower() == 'y':
                        results = []
                        for i, action in enumerate(actions):
                            print(f"\n执行操作 {i+1}: {action['description']}")
                            success = await self.execute_action(action)
                            results.append({
                                "action": action,
                                "success": success
                            })

                            # 操作间暂停
                            await asyncio.sleep(1)

                        return {
                            "success": True,
                            "message": "命令执行完成",
                            "glm_analysis": glm_content,
                            "actions_executed": results,
                            "screenshot_path": saved_path
                        }

            return {
                "success": True,
                "message": "GLM分析完成，操作已由用户确认",
                "glm_analysis": glm_content,
                "screenshot_path": saved_path,
                "executed": False
            }

        except Exception as e:
            logger.error(f"命令处理异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "命令处理失败"
            }

# 创建控制器实例
controller = XiaonuoGUIControllerV2()

# API路由
@app.get("/")
async def root():
    return {
        "message": "小诺GUI控制器 V2 运行中",
        "version": "2.0.0",
        "features": ["GLM-4V视觉分析", "智能GUI操作", "用户确认机制"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "glm_model": Config.GLM_MODEL
    }

@app.post("/analyze-screen")
async def analyze_screen(request: ScreenAnalysisRequest):
    """分析当前屏幕"""
    try:
        screen_bytes = controller.capture_screen()
        result = await controller.analyze_screen_with_glm(screen_bytes, request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-command")
async def execute_command(request: CommandRequest):
    """执行用户命令"""
    try:
        result = await controller.process_command(request.command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/screenshot")
async def take_screenshot():
    """截取屏幕"""
    try:
        screen_bytes = controller.capture_screen()
        saved_path = controller.save_screenshot(screen_bytes)
        return {
            "success": True,
            "screenshot_path": saved_path,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 启动小诺GUI控制器 V2...")
    print("📋 服务地址: http://localhost:8001")
    print("📖 API文档: http://localhost:8001/docs")
    print("🔍 健康检查: http://localhost:8001/health")
    print("✨ 特性: 集成GLM-4V视觉分析")

    # 检查依赖
    try:
        screen_size = pyautogui.size()
        print(f"🖥️  检测到屏幕分辨率: {screen_size}")
    except Exception as e:
        print(f"❌ 屏幕检测失败: {e}")
        print("请确保已授予屏幕录制权限")
        sys.exit(1)

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8001)