#!/usr/bin/env python3

"""
验证国内LLM API密钥是否可用
Verify Domestic LLM API Keys

测试三个国内LLM服务提供商的API密钥：
1. 智谱AI (GLM-4)
2. DeepSeek (深度求索)
3. 通义千问 (Qwen)

作者: Claude Code
日期: 2026-01-27
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.ai.llm.unified_llm_manager import get_unified_llm_manager
except ImportError as e:
    print(f"❌ 导入统一LLM管理器失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


class APIKeyVerifier:
    """API密钥验证器"""

    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        self.manager = None

    async def initialize_manager(self):
        """初始化统一LLM管理器"""
        print("🔄 初始化统一LLM管理器...")
        try:
            self.manager = await get_unified_llm_manager()
            await self.manager.initialize(enable_cache_warmup=False, warmup_cache=False)
            print("✅ 统一LLM管理器初始化完成")
            return True
        except Exception as e:
            print(f"❌ 统一LLM管理器初始化失败: {e}")
            return False

    async def verify_model(self, model_id: str, provider: str):
        """验证指定模型"""
        print(f"\n{'=' * 70}")
        print(f"🔍 验证 {provider} - {model_id}")
        print('=' * 70)

        try:
            # 健康检查
            print("🔄 执行健康检查...")
            health_results = await self.manager.health_check()

            is_available = model_id in health_results and health_results[model_id]

            if is_available:
                print(f"✅ {model_id} 健康检查通过")

                # 发送测试请求
                print("🔄 发送测试请求...")
                test_message = "你好，请用一句话介绍你自己。"

                start_time = datetime.now()
                response = await self.manager.generate(
                    message=test_message,
                    task_type="general_chat",
                    max_tokens=100,
                    temperature=0.7
                )
                latency_ms = (datetime.now() - start_time).total_seconds() * 1000

                if response and response.content:
                    print("✅ 请求成功!")
                    print(f"📊 响应延迟: {latency_ms:.0f}ms")
                    print(f"🤖 响应内容: {response.content[:100]}...")

                    result = {
                        "provider": provider,
                        "model": model_id,
                        "status": "PASS",
                        "message": "API密钥验证成功",
                        "latency_ms": latency_ms,
                        "response_preview": response.content[:100]
                    }
                    self.results["passed"] += 1
                else:
                    print("❌ 响应为空")
                    result = {
                        "provider": provider,
                        "model": model_id,
                        "status": "FAIL",
                        "message": "响应为空",
                        "latency_ms": latency_ms
                    }
                    self.results["failed"] += 1
            else:
                print(f"❌ {model_id} 健康检查失败")
                result = {
                    "provider": provider,
                    "model": model_id,
                    "status": "FAIL",
                    "message": "健康检查失败",
                    "latency_ms": 0
                }
                self.results["failed"] += 1

        except Exception as e:
            print(f"❌ 验证失败: {e}")
            result = {
                "provider": provider,
                "model": model_id,
                "status": "ERROR",
                "message": str(e),
                "latency_ms": 0
            }
            self.results["failed"] += 1

        self.results["total_tests"] += 1
        self.results["details"].append(result)
        return result

    async def verify_zhipuai(self):
        """验证智谱AI API密钥"""
        return await self.verify_model("glm-4-flash", "智谱AI")

    async def verify_deepseek(self):
        """验证DeepSeek API密钥"""
        return await self.verify_model("deepseek-chat", "DeepSeek")

    async def verify_qwen(self):
        """验证通义千问API密钥"""
        return await self.verify_model("qwen2.5-7b-instruct-gguf", "通义千问")

    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "=" * 70)
        print("📊 API密钥验证摘要")
        print("=" * 70)

        print(f"\n总测试数: {self.results['total_tests']}")
        print(f"✅ 通过: {self.results['passed']}")
        print(f"❌ 失败: {self.results['failed']}")

        if self.results['total_tests'] > 0:
            pass_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"📈 通过率: {pass_rate:.1f}%")

        print("\n详细结果:")
        print("-" * 70)

        for i, detail in enumerate(self.results['details'], 1):
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "⚠️",
                "SKIP": "⏭️"
            }.get(detail['status'], "❓")

            print(f"\n{i}. {detail['provider']} - {detail['model']}")
            print(f"   状态: {status_icon} {detail['status']}")
            print(f"   消息: {detail['message']}")

            if detail.get('latency_ms', 0) > 0:
                print(f"   延迟: {detail['latency_ms']:.0f}ms")

            if detail.get('response_preview'):
                print(f"   响应: {detail['response_preview'][:80]}...")

        print("\n" + "=" * 70)

        # 推荐
        if self.results['passed'] == self.results['total_tests']:
            print("🎉 所有API密钥验证成功！系统可以正常使用。")
        elif self.results['passed'] > 0:
            print(f"⚠️  部分API密钥验证成功 ({self.results['passed']}/{self.results['total_tests']})。")
            print("   建议检查失败的API密钥配置。")
        else:
            print("❌ 所有API密钥验证失败。请检查：")
            print("   1. 环境变量是否正确加载")
            print("   2. API密钥是否已配置")
            print("   3. 网络连接是否正常")
            print("   4. API密钥是否已过期")

        print("=" * 70)


async def main():
    """主函数"""
    print("=" * 70)
    print("🔑 国内LLM API密钥验证工具")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {project_root}")

    # 加载环境变量
    env_file = project_root / "config" / "env" / ".env"
    if env_file.exists():
        print(f"\n📄 加载环境变量: {env_file}")
        # 读取.env文件并设置环境变量
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ 环境变量加载完成")
    else:
        print(f"⚠️  环境变量文件不存在: {env_file}")

    # 创建验证器
    verifier = APIKeyVerifier()

    # 初始化管理器
    if not await verifier.initialize_manager():
        print("❌ 无法初始化统一LLM管理器，退出验证")
        return

    # 验证各个API密钥
    try:
        await verifier.verify_zhipuai()
    except Exception as e:
        print(f"❌ 智谱AI验证过程出错: {e}")

    try:
        await verifier.verify_deepseek()
    except Exception as e:
        print(f"❌ DeepSeek验证过程出错: {e}")

    try:
        await verifier.verify_qwen()
    except Exception as e:
        print(f"❌ 通义千问验证过程出错: {e}")

    # 打印摘要
    verifier.print_summary()

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())

