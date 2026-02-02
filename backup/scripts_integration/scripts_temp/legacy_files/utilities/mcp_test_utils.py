#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务器测试工具模块
MCP Server Testing Utilities

提供MCP服务器测试的通用工具函数
控制者: 小诺 & Athena
创建时间: 2025年12月11日
版本: 1.0.0
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def extract_json_from_output(output: str) -> Dict[str, Any | None]:
    """
    从MCP服务器输出中提取JSON响应
    MCP服务器通常会输出日志信息，需要从多行输出中提取JSON部分
    """
    lines = output.strip().split('\n')

    # 从最后一行开始查找JSON
    for line in reversed(lines):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        elif line.startswith('{'jsonrpc''):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    # 如果没有找到完整JSON，尝试多行组合
    json_content = ''
    in_json = False

    for line in lines:
        if line.strip().startswith('{'jsonrpc'') or line.strip().startswith('{"result'):
            in_json = True
            json_content = line.strip()
        elif in_json:
            json_content += ' ' + line.strip()
            if line.strip().endswith('}'):
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    in_json = False
                    json_content = ''

    return None

async def test_mcp_server_tools(server_path: Path, server_name: str) -> Dict[str, Any]:
    """
    测试MCP服务器的工具列表
    """
    if not server_path.exists():
        return {
            'status': 'failed',
            'reason': '服务器目录不存在'
        }

    try:
        # 测试工具列表
        list_request = '{'jsonrpc': '2.0', 'method': 'tools/list', 'params': {}, 'id': 1}'

        result = subprocess.run(
            ['node', 'index.js'],
            input=list_request,
            cwd=server_path,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            # 解析JSON响应
            response = extract_json_from_output(result.stdout)

            if response:
                tools = response.get('result', {}).get('tools', [])

                # 测试系统信息工具
                info_request = '{'jsonrpc': '2.0', 'method': 'tools/call', 'params': {'name': 'get_system_info', 'arguments': {}}, 'id': 2}'

                result2 = subprocess.run(
                    ['node', 'index.js'],
                    input=info_request,
                    cwd=server_path,
                    capture_output=True,
                    text=True,
                    timeout=15
                )

                system_info_working = False
                if result2.returncode == 0:
                    response2 = extract_json_from_output(result2.stdout)
                    if response2 and 'result' in response2:
                        system_info_working = True

                return {
                    'status': 'passed',
                    'tools_count': len(tools),
                    'tools': [tool['name'] for tool in tools],
                    'system_info_working': system_info_working,
                    'stdout_sample': result.stdout[:200] + '...' if len(result.stdout) > 200 else result.stdout
                }
            else:
                return {
                    'status': 'failed',
                    'reason': '无法解析JSON响应',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
        else:
            return {
                'status': 'failed',
                'reason': '进程退出失败',
                'return_code': result.returncode,
                'stderr': result.stderr
            }

    except subprocess.TimeoutExpired:
        return {
            'status': 'failed',
            'reason': '超时'
        }
    except Exception as e:
        return {
            'status': 'error',
            'reason': str(e)
        }

async def test_mcp_tool_call(server_path: Path, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    测试MCP服务器工具调用
    """
    try:
        request = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': tool_name,
                'arguments': arguments
            },
            'id': 3
        }

        result = subprocess.run(
            ['node', 'index.js'],
            input=json.dumps(request),
            cwd=server_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            response = extract_json_from_output(result.stdout)

            if response:
                return {
                    'status': 'success',
                    'response': response
                }
            else:
                return {
                    'status': 'failed',
                    'reason': '无法解析JSON响应',
                    'stdout': result.stdout
                }
        else:
            return {
                'status': 'failed',
                'reason': '进程退出失败',
                'return_code': result.returncode,
                'stderr': result.stderr
            }

    except Exception as e:
        return {
            'status': 'error',
            'reason': str(e)
        }

class MCPServerHealthChecker:
    """MCP服务器健康检查器"""

    def __init__(self):
        self.platform_root = Path('/Users/xujian/Athena工作平台')

    async def check_all_servers(self) -> Dict[str, Any]:
        """检查所有MCP服务器的健康状态"""
        servers = {
            'jina-ai': self.platform_root / 'mcp-servers' / 'jina-ai-mcp-server',
            'bing-cn-search': self.platform_root / 'mcp-servers' / 'bing-cn-mcp-server',
        }

        results = {}

        for name, path in servers.items():
            logger.info(f"检查服务器: {name}")
            result = await test_mcp_server_tools(path, name)
            results[name] = result

            # 显示检查结果
            if result['status'] == 'passed':
                logger.info(f"  ✅ {name}: 正常 ({result['tools_count']} 个工具)")
            else:
                logger.info(f"  ❌ {name}: {result['reason']}")

        return results

    async def check_specific_functionality(self):
        """检查特定功能"""
        logger.info("\n🧪 执行功能测试...")

        # 测试Jina AI的嵌入功能
        jina_path = self.platform_root / 'mcp-servers' / 'jina-ai-mcp-server'

        logger.info('测试Jina AI文本嵌入功能...')
        result = await test_mcp_tool_call(
            jina_path,
            'embedding',
            {'texts': ['Hello', 'World'], 'model': 'jina-embeddings-v2'}
        )

        if result['status'] == 'success':
            logger.info('  ✅ 文本嵌入功能正常')
        else:
            logger.info(f"  ❌ 文本嵌入功能失败: {result['reason']}")

        # 测试Bing中文搜索功能
        bing_path = self.platform_root / 'mcp-servers' / 'bing-cn-mcp-server'

        logger.info('测试Bing中文搜索功能...')
        result = await test_mcp_tool_call(
            bing_path,
            'search_chinese',
            {'query': '人工智能', 'count': 3}
        )

        if result['status'] == 'success':
            logger.info('  ✅ 中文搜索功能正常')
        else:
            logger.info(f"  ❌ 中文搜索功能失败: {result['reason']}")

def generate_health_report(check_results: Dict[str, Any]) -> str:
    """生成健康检查报告"""
    total_servers = len(check_results)
    healthy_servers = sum(1 for r in check_results.values() if r.get('status') == 'passed')

    report = f"""
# MCP服务器健康检查报告

**检查时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**总服务器数**: {total_servers}
**健康服务器数**: {healthy_servers}
**健康率**: {healthy_servers/total_servers*100:.1f}%

## 详细状态

"""

    for name, result in check_results.items():
        status_icon = '✅' if result.get('status') == 'passed' else '❌'
        report += f"### {status_icon} {name}\n"
        report += f"- **状态**: {result.get('status', 'unknown')}\n"

        if result.get('status') == 'passed':
            report += f"- **工具数量**: {result.get('tools_count', 0)}\n"
            tools = result.get('tools', [])
            if tools:
                report += f"- **工具列表**: {', '.join(tools[:5])}"
                if len(tools) > 5:
                    report += f" (还有 {len(tools)-5} 个工具)"
                report += "\n"
        else:
            report += f"- **失败原因**: {result.get('reason', '未知')}\n"

        report += "\n"

    return report

# 便捷函数
async def quick_health_check() -> Dict[str, Any]:
    """快速健康检查"""
    checker = MCPServerHealthChecker()
    return await checker.check_all_servers()

if __name__ == '__main__':
    import asyncio

    async def main():
        checker = MCPServerHealthChecker()

        logger.info('🔍 开始MCP服务器健康检查...')
        results = await checker.check_all_servers()

        await checker.check_specific_functionality()

        report = generate_health_report(results)
        logger.info(str(report))

        # 保存报告
        report_file = Path('/Users/xujian/Athena工作平台/logs') / f"mcp_health_report_{int(time.time())}.md"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"📄 报告已保存到: {report_file}")

    asyncio.run(main())