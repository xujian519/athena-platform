#!/usr/bin/env python3
"""
云端LLM连接测试脚本
Cloud LLM Connection Test for Lyra

测试各种云端LLM提供者的连接状态

作者: 小诺·双鱼公主
创建时间: 2026-02-06
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import aiohttp
except ImportError:
    print("❌ 需要安装 aiohttp: pip install aiohttp")
    sys.exit(1)


class CloudLLMTester:
    """云端LLM测试器"""

    def __init__(self):
        self.config_path = Path("/Users/xujian/Athena工作平台/config/lyra_llm_config.json")
        self.config = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ 已加载配置: {self.config_path}")
            else:
                print(f"⚠️ 配置文件不存在: {self.config_path}")
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")

    async def test_zhipu(self, api_key: str | None = None) -> dict:
        """测试智谱AI"""
        print("\n🔍 测试智谱AI (GLM-4)")
        print("-" * 50)

        # 获取API密钥
        if not api_key:
            api_key = self.config.get("providers", {}).get("zhipu", {}).get("api_key", "")

        if not api_key:
            return {"status": "skip", "message": "API密钥未配置"}

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "glm-4",
            "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
            "temperature": 0.7,
            "max_tokens": 100
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        print(f"✅ 连接成功！")
                        print(f"响应: {content[:100]}...")
                        return {
                            "status": "success",
                            "message": "连接成功",
                            "response": content[:100],
                            "model": data.get("model", "glm-4")
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ 错误 ({response.status}): {error_text[:100]}")
                        return {
                            "status": "failed",
                            "message": f"HTTP {response.status}",
                            "error": error_text[:200]
                        }
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return {"status": "error", "message": str(e)}

    async def test_deepseek(self, api_key: str | None = None) -> dict:
        """测试DeepSeek"""
        print("\n🔍 测试DeepSeek")
        print("-" * 50)

        # 获取API密钥
        if not api_key:
            api_key = self.config.get("providers", {}).get("deepseek", {}).get("api_key", "")

        if not api_key:
            return {"status": "skip", "message": "API密钥未配置"}

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
            "temperature": 0.7,
            "max_tokens": 100
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        print(f"✅ 连接成功！")
                        print(f"响应: {content[:100]}...")
                        return {
                            "status": "success",
                            "message": "连接成功",
                            "response": content[:100],
                            "model": data.get("model", "deepseek-chat")
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ 错误 ({response.status}): {error_text[:100]}")
                        return {
                            "status": "failed",
                            "message": f"HTTP {response.status}",
                            "error": error_text[:200]
                        }
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return {"status": "error", "message": str(e)}

    async def test_openai(self, api_key: str | None = None) -> dict:
        """测试OpenAI"""
        print("\n🔍 测试OpenAI (GPT)")
        print("-" * 50)

        # 获取API密钥
        if not api_key:
            api_key = self.config.get("providers", {}).get("openai", {}).get("api_key", "")

        if not api_key:
            return {"status": "skip", "message": "API密钥未配置"}

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello, please introduce yourself in one sentence."}],
            "temperature": 0.7,
            "max_tokens": 100
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        print(f"✅ 连接成功！")
                        print(f"响应: {content[:100]}...")
                        return {
                            "status": "success",
                            "message": "连接成功",
                            "response": content[:100],
                            "model": data.get("model", "gpt-4o-mini")
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ 错误 ({response.status}): {error_text[:100]}")
                        return {
                            "status": "failed",
                            "message": f"HTTP {response.status}",
                            "error": error_text[:200]
                        }
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return {"status": "error", "message": str(e)}

    async def test_anthropic(self, api_key: str | None = None) -> dict:
        """测试Anthropic Claude"""
        print("\n🔍 测试Anthropic (Claude)")
        print("-" * 50)

        # 获取API密钥
        if not api_key:
            api_key = self.config.get("providers", {}).get("anthropic", {}).get("api_key", "")

        if not api_key:
            return {"status": "skip", "message": "API密钥未配置"}

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Hello, please introduce yourself in one sentence."}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        print(f"✅ 连接成功！")
                        print(f"响应: {content[:100]}...")
                        return {
                            "status": "success",
                            "message": "连接成功",
                            "response": content[:100],
                            "model": data.get("model", "claude-3-5-sonnet")
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ 错误 ({response.status}): {error_text[:100]}")
                        return {
                            "status": "failed",
                            "message": f"HTTP {response.status}",
                            "error": error_text[:200]
                        }
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return {"status": "error", "message": str(e)}

    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🌐 云端LLM连接测试")
        print("=" * 60)

        results = {}

        # 测试各个提供者
        results["zhipu"] = await self.test_zhipu()
        results["deepseek"] = await self.test_deepseek()
        results["openai"] = await self.test_openai()
        results["anthropic"] = await self.test_anthropic()

        # 打印摘要
        self.print_summary(results)

        return results

    def print_summary(self, results: dict):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("📊 测试摘要")
        print("=" * 60)

        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        failed_count = sum(1 for r in results.values() if r.get("status") in ["failed", "error"])
        skip_count = sum(1 for r in results.values() if r.get("status") == "skip")

        print(f"\n✅ 成功: {success_count}")
        print(f"❌ 失败: {failed_count}")
        print(f"⏭️ 跳过: {skip_count}")

        print("\n详细结果:")
        for provider, result in results.items():
            status_icon = {
                "success": "✅",
                "failed": "❌",
                "error": "⚠️",
                "skip": "⏭️"
            }.get(result.get("status", "unknown"), "❓")

            print(f"  {status_icon} {provider.upper()}: {result.get('message', 'N/A')}")

        print("\n" + "=" * 60)

        # 配置建议
        if success_count == 0:
            print("\n💡 配置建议:")
            print("   1. 智谱AI: https://open.bigmodel.cn/")
            print("   2. DeepSeek: https://platform.deepseek.com/")
            print("   3. OpenAI: https://platform.openai.com/")
            print("   4. Anthropic: https://console.anthropic.com/")
            print("\n   获取API密钥后，更新配置文件:")
            print(f"   {self.config_path}")
        else:
            print("\n🎉 至少有一个LLM提供者可用！")


async def main():
    """主函数"""
    tester = CloudLLMTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
