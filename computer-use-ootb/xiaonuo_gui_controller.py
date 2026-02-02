#!/usr/bin/env python3
"""
小诺GUI控制器 - 基于GLM-4V的智能GUI操作工具
集成Athena平台的GLM视觉服务，实现本地电脑操作
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
try:
    import pyautogui
    import pyperclip
    from PIL import ImageGrab
    from pynput import mouse, keyboard
except ImportError as e:
    print(f"正在安装依赖: {e}")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui", "pyperclip", "pillow", "pynput", "--user"])
    import pyautogui
    import pyperclip
    from PIL import ImageGrab
    from pynput import mouse, keyboard

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="小诺GUI控制器",
    description="基于GLM-4V的智能GUI操作服务",
    version="1.0.0"
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
    GLM_VISION_ENDPOINT = "http://localhost:8091"
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

# GUI控制器类
class XiaonuoGUIController:
    def __init__(self):
        self.pyautogui = pyautogui
        self.pyautogui.PAUSE = 0.5
        self.pyautogui.FAILSAFE = True

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
        async with aiohttp.ClientSession() as session:
            # 构建multipart/form-data
            data = aiohttp.FormData()
            data.add_field('text', question)
            data.add_field('model', Config.GLM_MODEL)
            data.add_field('file', image_bytes,
                         filename='screenshot.png',
                         content_type='image/png')

            try:
                async with session.post(
                    f"{Config.GLM_VISION_ENDPOINT}/analyze-image",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        logger.error(f"GLM API错误: {response.status}")
                        return {"error": f"API错误: {response.status}"}
            except Exception as e:
                logger.error(f"GLM调用异常: {e}")
                return {"error": f"调用异常: {str(e)}"}

    def extract_actions_from_glm_response(self, glm_response: str) -> List[Dict]:
        """从GLM响应中提取操作指令"""
        actions = []

        # 简单的动作解析逻辑
        if "点击" in glm_response:
            # 尝试提取坐标（GLM可能不会直接给出坐标）
            actions.append({"type": "click", "description": "点击屏幕"})

        if "输入" in glm_response or "打字" in glm_response:
            actions.append({"type": "type", "description": "输入文本"})

        if "滚动" in glm_response:
            actions.append({"type": "scroll", "description": "滚动屏幕"})

        if "拖拽" in glm_response:
            actions.append({"type": "drag", "description": "拖拽操作"})

        return actions

    async def execute_action(self, action: Dict) -> bool:
        """执行GUI操作"""
        try:
            action_type = action.get("type")

            if action_type == "click":
                # GLM可能给出位置描述，我们需要尝试理解并执行
                # 这里简化为询问用户点击位置
                return await self.execute_click_with_guidance(action)

            elif action_type == "type":
                return await self.execute_type_with_guidance(action)

            elif action_type == "scroll":
                self.pyautogui.scroll()
                return True

            else:
                logger.warning(f"未知操作类型: {action_type}")
                return False

        except Exception as e:
            logger.error(f"执行操作失败: {e}")
            return False

    async def execute_click_with_guidance(self, action: Dict) -> bool:
        """引导式点击操作"""
        print("\n📍 请移动鼠标到要点击的位置，然后按回车键确认...")
        print("   (按ESC键取消操作)")

        # 等待用户确认
        while True:
            try:
                # 获取当前鼠标位置
                x, y = pyautogui.position()
                print(f"   当前鼠标位置: ({x}, {y}) - 按回车点击，ESC取消")

                # 等待按键
                import keyboard as kb
                key = kb.read_key()

                if key == 'enter':
                    self.pyautogui.click(x, y)
                    print(f"   ✓ 已点击位置 ({x}, {y})")
                    return True
                elif key == 'esc':
                    print("   ✗ 操作已取消")
                    return False

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
                print(f"   ✓ 已输入文本: {text}")
                return True
            return False
        except Exception as e:
            logger.error(f"输入操作异常: {e}")
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

            请提供：
            1. 当前屏幕的主要内容和布局
            2. 执行操作的步骤
            3. 需要点击的位置（如果能确定的话）
            4. 需要输入的文本（如果需要的话）
            """

            glm_result = await self.analyze_screen_with_glm(screen_bytes, analysis_question)

            if "error" in glm_result:
                return {
                    "success": False,
                    "error": glm_result["error"],
                    "message": "GLM分析失败"
                }

            # 3. 提取并执行操作
            glm_content = glm_result.get("content", "")
            logger.info(f"GLM分析结果: {glm_content[:200]}...")

            actions = self.extract_actions_from_glm_response(glm_content)

            if not actions:
                return {
                    "success": False,
                    "message": "无法从GLM响应中提取有效操作",
                    "glm_response": glm_content
                }

            # 4. 执行操作
            results = []
            for i, action in enumerate(actions):
                logger.info(f"执行操作 {i+1}: {action}")
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

        except Exception as e:
            logger.error(f"命令处理异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "命令处理失败"
            }

# 创建控制器实例
controller = XiaonuoGUIController()

# API路由
@app.get("/")
async def root():
    return {"message": "小诺GUI控制器运行中", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
    print("🚀 启动小诺GUI控制器...")
    print("📋 服务地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")

    # 检查依赖
    try:
        screen_size = pyautogui.size()
        print(f"🖥️  检测到屏幕分辨率: {screen_size}")
    except Exception as e:
        print(f"❌ 屏幕检测失败: {e}")
        print("请确保已授予屏幕录制权限")
        sys.exit(1)

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8000)