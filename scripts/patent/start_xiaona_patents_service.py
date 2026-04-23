#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动小娜专利服务脚本
Start Xiaona Patents Service Script

一键启动小娜的专业专利服务

作者: 小诺
创建时间: 2025-12-16
版本: v1.0.0
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XiaonaPatentsServiceStarter:
    """小娜专利服务启动器"""

    def __init__(self):
        self.service_name = "小娜专利服务"
        self.service_version = "v1.0.0"
        self.service_port = 8006
        self.service_url = f"http://localhost:{self.service_port}"
        self.script_path = Path("/Users/xujian/Athena工作平台/services/xiaona-patents/xiaona_patents_service.py")
        self.log_path = Path("/Users/xujian/Athena工作平台/logs/xiaona_patents")
        self.process = None

        # 确保日志目录存在
        self.log_path.mkdir(parents=True, exist_ok=True)

    def print_startup_header(self) -> Any:
        """打印启动头部信息"""
        print("\n" + "="*80)
        print("⚖️" + " "*25 + "小娜专利服务启动器" + " "*25 + "⚖️")
        print("="*80)
        print(f"💖 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 服务版本: {self.service_version}")
        print(f"📍 服务地址: {self.service_url}")
        print(f"👩‍⚖️ 控制者: 小娜·天秤女神 (专利法律专家)")
        print(f"📄 脚本路径: {self.script_path}")
        print("="*80)

    def check_prerequisites(self) -> bool:
        """检查先决条件"""
        print("\n🔍 检查先决条件...")

        # 检查脚本文件
        if not self.script_path.exists():
            print(f"❌ 脚本文件不存在: {self.script_path}")
            return False
        print(f"✅ 脚本文件存在: {self.script_path}")

        # 检查Python环境
        try:
            import fastapi
            print(f"✅ FastAPI已安装: {fastapi.__version__}")
        except ImportError:
            print("❌ FastAPI未安装，请运行: pip install fastapi uvicorn")
            return False

        # 检查端口是否被占用
        if self._is_port_occupied():
            print(f"⚠️ 端口 {self.service_port} 已被占用，尝试停止现有服务...")
            self._stop_existing_service()
            time.sleep(2)

        return True

    def _is_port_occupied(self) -> bool:
        """检查端口是否被占用"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.service_port))
            sock.close()
            return result == 0
        except:
            return False

    def _stop_existing_service(self) -> Any:
        """停止现有服务"""
        try:
            # 查找占用端口的进程
            result = subprocess.run(
                ['lsof', '-ti', f':{self.service_port}'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip()
                print(f"🔄 停止占用端口的进程: PID {pid}")
                subprocess.run(['kill', '-9', pid])
                time.sleep(1)
        except Exception as e:
            print(f"⚠️ 停止现有服务时出错: {e}")

    async def start_service(self):
        """启动服务"""
        print("\n🚀 启动小娜专利服务...")

        try:
            # 启动服务进程
            log_file = self.log_path / f"service_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            self.process = subprocess.Popen(
                [sys.executable, str(self.script_path)],
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                text=True
            )

            print(f"✅ 服务进程已启动 (PID: {self.process.pid})")
            print(f"📝 日志文件: {log_file}")

            # 等待服务启动
            print("⏳ 等待服务启动...")
            await self._wait_for_service_ready()

            # 验证服务状态
            await self._verify_service()

            print("\n🎉 小娜专利服务启动成功！")
            await self._display_service_info()

            return True

        except Exception as e:
            print(f"❌ 启动服务失败: {e}")
            if self.process:
                self.process.terminate()
            return False

    async def _wait_for_service_ready(self, timeout: int = 30):
        """等待服务就绪"""
        import aiohttp

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.service_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            print("✅ 服务已就绪")
                            return True
            except:
                pass

            print(".", end="", flush=True)
            await asyncio.sleep(1)

        print("\n❌ 服务启动超时")
        return False

    async def _verify_service(self):
        """验证服务状态"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                # 检查健康状态
                async with session.get(f"{self.service_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ 健康检查通过: {health_data.get('status', 'unknown')}")

                # 检查系统状态
                async with session.get(f"{self.service_url}/status") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        print(f"✅ 系统状态: {status_data.get('status', 'unknown')}")
                        print(f"👩‍⚖️ 控制者: {status_data.get('controller', 'unknown')}")

                        # 显示统计信息
                        stats = status_data.get('statistics', {})
                        if stats:
                            print(f"📊 服务统计:")
                            print(f"   总请求数: {stats.get('total_requests', 0)}")
                            print(f"   成功获取: {stats.get('successful_retrievals', 0)}")
                            print(f"   失败获取: {stats.get('failed_retrievals', 0)}")

        except Exception as e:
            print(f"⚠️ 验证服务状态时出错: {e}")

    async def _display_service_info(self):
        """显示服务信息"""
        print("\n" + "="*80)
        print("🌟" + " "*25 + "服务信息" + " "*25 + "🌟")
        print("="*80)
        print(f"🔗 服务地址: {self.service_url}")
        print(f"📚 API文档: {self.service_url}/docs")
        print(f"🔍 ReDoc文档: {self.service_url}/redoc")
        print(f"💚 健康检查: {self.service_url}/health")
        print(f"📊 系统状态: {self.service_url}/status")
        print()
        print("💡 使用示例:")
        print(f"  # 获取单个专利")
        print(f"  curl {self.service_url}/patent/CN108765432A")
        print()
        print(f"  # 获取专利详情")
        print(f"  curl -X POST {self.service_url}/patent/retrieve \\")
        print(f"    -H 'Content-Type: application/json' \\")
        print(f"    -d '{{\"patent_number\": \"CN108765432A\", \"retrieval_type\": \"full_text\"}}'")
        print("="*80)

    async def stop_service(self):
        """停止服务"""
        print("\n🛑 停止小娜专利服务...")

        if self.process:
            print(f"🔄 终止服务进程 (PID: {self.process.pid})")
            self.process.terminate()

            try:
                self.process.wait(timeout=10)
                print("✅ 服务已停止")
            except subprocess.TimeoutExpired:
                print("⚠️ 强制终止服务进程")
                self.process.kill()
                self.process.wait()

            self.process = None
        else:
            print("⚠️ 没有运行中的服务进程")

    def display_usage_info(self) -> Any:
        """显示使用信息"""
        print("\n" + "="*80)
        print("📖" + " "*25 + "使用说明" + " "*25 + "📖")
        print("="*80)
        print("1. 启动服务:")
        print("   python scripts/start_xiaona_patents_service.py")
        print()
        print("2. 访问API文档:")
        print(f"   浏览器打开: {self.service_url}/docs")
        print()
        print("3. 主要API端点:")
        print(f"   GET  {self.service_url}/patent/{{patent_number}}  - 获取专利")
        print(f"   POST {self.service_url}/patent/retrieve             - 获取专利详情")
        print(f"   POST {self.service_url}/patents/batch             - 批量获取专利")
        print(f"   GET  {self.service_url}/status                    - 获取系统状态")
        print()
        print("4. 停止服务:")
        print("   Ctrl+C 或关闭终端")
        print("="*80)

async def main():
    """主函数"""
    starter = XiaonaPatentsServiceStarter()

    # 显示启动信息
    starter.print_startup_header()

    # 检查先决条件
    if not starter.check_prerequisites():
        print("\n❌ 先决条件检查失败，无法启动服务")
        return

    try:
        # 启动服务
        success = await starter.start_service()

        if success:
            # 显示使用说明
            starter.display_usage_info()

            # 保持服务运行
            print("\n⏳ 服务运行中... (按 Ctrl+C 停止)")
            while True:
                await asyncio.sleep(1)
                if starter.process and starter.process.poll() is not None:
                    print("\n❌ 服务进程意外退出")
                    break

    except KeyboardInterrupt:
        print("\n⚠️ 收到中断信号，正在停止服务...")
    except Exception as e:
        print(f"\n❌ 运行时出错: {e}")
    finally:
        # 停止服务
        await starter.stop_service()

if __name__ == "__main__":
    asyncio.run(main())