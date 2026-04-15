#!/usr/bin/env python3
"""
DeepSeek-Coder 集成服务
为Athena工作平台提供智能代码生成能力
"""

import json
import logging
import os

# 导入安全配置
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent / "core"))


class ProgrammingLanguage(Enum):
    """支持的编程语言枚举"""
    PYTHON = 'python'
    JAVASCRIPT = 'javascript'
    JAVA = 'java'
    CPP = 'cpp'
    CSHARP = 'csharp'
    GO = 'go'
    RUST = 'rust'
    PHP = 'php'
    RUBY = 'ruby'
    SWIFT = 'swift'
    KOTLIN = 'kotlin'
    TYPESCRIPT = 'typescript'

@dataclass
class CodeGenerationRequest:
    """代码生成请求"""
    prompt: str
    language: ProgrammingLanguage
    max_tokens: int = 2000
    temperature: float = 0.1
    context: str | None = None  # 额外的上下文信息

@dataclass
class CodeGenerationResponse:
    """代码生成响应"""
    code: str
    explanation: str
    language: str
    tokens_used: int
    response_time: float
    timestamp: datetime

class DeepSeekCoderAPI:
    """DeepSeek-Coder API客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY', 'sk-7f0fa1165de249d0a30b62a2584bd4c5')
        self.base_url = 'https://api.deepseek.com/v1'
        self.model = 'deepseek-chat'
        self.session = None
        self.logger = self._setup_logger()

        # 统计信息
        self.total_requests = 0
        self.total_tokens = 0
        self.success_rate = 0.0

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('DeepSeekCoder')
        logger.set_level(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.set_formatter(formatter)
            logger.add_handler(handler)

        return logger

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def _create_system_prompt(self, language: ProgrammingLanguage) -> str:
        """创建针对特定编程语言的系统提示"""
        language_configs = {
            ProgrammingLanguage.PYTHON: """
你是一个专业的Python开发工程师。请根据用户需求生成高质量、符合PEP8规范的Python代码。
注意事项：
- 使用类型注解
- 添加适当的文档字符串
- 考虑异常处理
- 优先使用Python标准库
            """,

            ProgrammingLanguage.JAVASCRIPT: """
你是一个专业的前端/JavaScript开发工程师。请生成现代化、符合ES6+规范的JavaScript代码。
注意事项：
- 使用现代语法特性
- 考虑浏览器兼容性
- 添加适当的注释
- 遵循最佳实践
            """,

            ProgrammingLanguage.JAVA: """
你是一个专业的Java开发工程师。请生成符合Java编码规范的代码。
注意事项：
- 遵循Java命名规范
- 使用适当的异常处理
- 考虑面向对象设计原则
- 添加JavaDoc注释
            """,

            ProgrammingLanguage.CPP: """
你是一个专业的C++开发工程师。请生成现代C++（C++11及以上）代码。
注意事项：
- 使用智能指针管理内存
- 遵循RAII原则
- 添加适当的注释
- 考虑性能优化
            """,

            ProgrammingLanguage.GO: """
你是一个专业的Go语言开发工程师。请生成符合Go语言习惯的代码。
注意事项：
- 遵循Go的命名规范
- 正确处理错误
- 利用Go的并发特性
- 添加适当的注释
            """
        }

        return language_configs.get(language, """
你是一个专业的软件开发工程师。请根据用户需求生成高质量、符合行业标准的代码。
注意事项：
- 代码应该清晰、易读、易维护
- 添加适当的注释和文档
- 考虑错误处理和边界情况
- 遵循相应语言的最佳实践
        """)

    def _create_patent_context_prompt(self, patent_info: dict = None) -> str:
        """创建专利相关的上下文提示"""
        if not patent_info:
            return ''

        return f"""
以下是相关的专利信息，请在生成代码时参考这些技术方案：

专利标题：{patent_info.get('title', '未提供')}
专利摘要：{patent_info.get('abstract', '未提供')}
技术领域：{patent_info.get('field', '未提供')}
关键技术：{patent_info.get('key_technologies', [])}

请根据上述专利技术方案，生成相应的实现代码。代码应该：
1. 体现专利的核心技术特点
2. 实现专利描述的主要功能
3. 包含适当的注释说明与专利技术的对应关系
4. 考虑技术方案的创新点和优势
"""

    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        """
        生成代码

        Args:
            request: 代码生成请求

        Returns:
            CodeGenerationResponse: 生成的代码和相关信息
        """
        start_time = datetime.now()

        try:
            if not self.session:
                raise RuntimeError('Session not initialized. Use async context manager.')

            # 构建系统提示
            system_prompt = self._create_system_prompt(request.language)

            # 添加专利上下文（如果提供）
            if request.context:
                patent_info = json.loads(request.context) if isinstance(request.context, str) else request.context
                patent_context = self._create_patent_context_prompt(patent_info)
                system_prompt += patent_context

            # 构建用户提示
            user_prompt = f"""请使用{request.language.value}语言，根据以下需求生成代码：

需求描述：
{request.prompt}

请提供：
1. 完整的代码实现
2. 代码的详细说明
3. 关键技术点的解释

"""

            # 调用DeepSeek API
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]

            payload = {
                'model': self.model,
                'messages': messages,
                'max_tokens': request.max_tokens,
                'temperature': request.temperature,
                'stream': False
            }

            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")

                result = await response.json()

                # 解析响应
                content = result['choices'][0]['message']['content']
                tokens_used = result.get('usage', {}).get('total_tokens', 0)

                # 提取代码和解释
                code, explanation = self._parse_code_response(content)

                # 计算响应时间
                response_time = (datetime.now() - start_time).total_seconds()

                # 更新统计信息
                self.total_requests += 1
                self.total_tokens += tokens_used
                self.success_rate = min(1.0, self.success_rate + 0.01)

                self.logger.info(f"代码生成成功: {request.language.value}, 耗时: {response_time:.2f}s, tokens: {tokens_used}")

                return CodeGenerationResponse(
                    code=code,
                    explanation=explanation,
                    language=request.language.value,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    timestamp=start_time
                )

        except Exception as e:
            self.logger.error(f"代码生成失败: {str(e)}")
            self.success_rate = max(0.0, self.success_rate - 0.05)

            # 返回错误响应
            return CodeGenerationResponse(
                code='',
                explanation=f"代码生成失败: {str(e)}",
                language=request.language.value,
                tokens_used=0,
                response_time=(datetime.now() - start_time).total_seconds(),
                timestamp=start_time
            )

    def _parse_code_response(self, content: str) -> tuple[str, str]:
        """
        解析API响应，分离代码和解释

        Args:
            content: API响应内容

        Returns:
            tuple: (代码, 解释)
        """
        lines = content.split('\n')
        code_lines = []
        explanation_lines = []

        in_code_block = False
        code_fence = None

        for line in lines:
            # 检测代码块开始
            if not in_code_block and line.strip().startswith('```'):
                code_fence = line.strip()
                in_code_block = True
                continue

            # 检测代码块结束
            elif in_code_block and line.strip() == code_fence:
                in_code_block = False
                code_fence = None
                continue

            # 处理内容
            if in_code_block:
                code_lines.append(line)
            else:
                explanation_lines.append(line)

        # 如果没有检测到代码块，尝试其他方式提取
        if not code_lines:
            # 查找可能包含代码的行
            for line in lines:
                if any(keyword in line for keyword in ['def ', 'class ', 'function', 'import ', 'using ', 'public ']):
                    code_lines.append(line)
                else:
                    explanation_lines.append(line)

        code = '\n'.join(code_lines).strip()
        explanation = '\n'.join(explanation_lines).strip()

        return code, explanation

    def get_statistics(self) -> dict[str, Any]:
        """获取使用统计信息"""
        return {
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'success_rate': self.success_rate,
            'average_tokens_per_request': self.total_tokens / max(1, self.total_requests),
            'model': self.model
        }

    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            test_request = CodeGenerationRequest(
                prompt='Hello World in Python',
                language=ProgrammingLanguage.PYTHON,
                max_tokens=100
            )

            response = await self.generate_code(test_request)
            return len(response.code) > 0

        except Exception as e:
            self.logger.error(f"连接测试失败: {str(e)}")
            return False

# 全局实例
_deepseek_client = None

async def get_deepseek_client() -> DeepSeekCoderAPI:
    """获取DeepSeek客户端实例"""
    global _deepseek_client

    if _deepseek_client is None:
        _deepseek_client = DeepSeekCoderAPI()

    return _deepseek_client

# 使用示例
async def main():
    """测试函数"""
    async with await get_deepseek_client() as client:
        # 测试连接
        if await client.test_connection():
            logger.info('✅ DeepSeek-Coder API连接成功!')

            # 生成代码示例
            request = CodeGenerationRequest(
                prompt='创建一个计算斐波那契数列的函数，包含输入验证和错误处理',
                language=ProgrammingLanguage.PYTHON,
                max_tokens=1000
            )

            response = await client.generate_code(request)

            logger.info("\n📊 生成统计:")
            logger.info(f"- 语言: {response.language}")
            logger.info(f"- 耗时: {response.response_time:.2f}秒")
            logger.info(f"- Tokens: {response.tokens_used}")

            logger.info("\n💻 生成的代码:")
            logger.info(str(response.code))

            logger.info("\n📝 代码说明:")
            logger.info(str(response.explanation))

            # 显示统计信息
            stats = client.get_statistics()
            logger.info("\n📈 使用统计:")
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            logger.info('❌ DeepSeek-Coder API连接失败!')

# 入口点: @async_main装饰器已添加到main函数
