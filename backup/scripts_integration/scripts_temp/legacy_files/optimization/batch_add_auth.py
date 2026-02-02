#!/usr/bin/env python3
"""
批量为API端点添加认证依赖
"""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

def add_auth_to_endpoints(file_path: Path):
    """为API端点添加认证依赖"""
    try:
        file_path = Path(file_path).resolve()
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 需要保护的端点列表（排除公开端点）
        public_endpoints = [
            '/', '/health', '/docs', '/openapi.json', '/metrics',
            '/api/v1/demo/', '/ws'  # WebSocket端点
        ]

        lines = content.split('\n')
        modified = False

        # 查找并修改API端点定义
        for i, line in enumerate(lines):
            # 匹配FastAPI路由装饰器
            route_match = re.match(r'^(\s*)@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line)
            if route_match:
                indent, method, path = route_match.groups()

                # 检查是否为公开端点
                is_public = any(pub_path in path for pub_path in public_endpoints)

                if not is_public:
                    # 查找对应的函数定义行
                    func_line_idx = i + 1
                    while func_line_idx < len(lines) and not lines[func_line_idx].strip().startswith('async def'):
                        func_line_idx += 1

                    if func_line_idx < len(lines):
                        func_line = lines[func_line_idx]
                        # 检查是否已经有认证参数
                        if 'current_user' not in func_line and 'get_current_user' not in func_line:
                            # 在函数参数中添加认证依赖
                            if 'request:' in func_line or 'background_tasks:' in func_line:
                                # 如果已有其他参数，在末尾添加
                                func_line = func_line.rstrip()
                                if func_line.endswith(':'):
                                    func_line = func_line[:-1]
                                    func_line += ', current_user: dict = Depends(get_current_user)):'
                                else:
                                    func_line += ', current_user: dict = Depends(get_current_user)'
                                lines[func_line_idx] = func_line
                                modified = True
                            else:
                                # 没有其他参数，添加认证参数
                                if '->' in func_line:
                                    # 有返回类型注解
                                    func_line = func_line.replace('):', ', current_user: dict = Depends(get_current_user)):')
                                else:
                                    # 无返回类型注解
                                    func_line = func_line.replace('):', ', current_user: dict = Depends(get_current_user)):')
                                lines[func_line_idx] = func_line
                                modified = True

        # 如果文件被修改，写回
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            logger.info(f"✅ 已更新: {file_path.name}")
            return True
        else:
            logger.info(f"⏭️  跳过（已包含认证）: {file_path.name}")
            return False

    except Exception as e:
        logger.info(f"❌ 处理失败 {file_path}: {str(e)}")
        return False


def main():
    """主函数"""
    # 获取当前工作目录
    cwd = Path.cwd()
    if cwd.name == 'scripts':
        # 如果在scripts目录下，需要调整路径
        base_path = cwd.parent
    else:
        base_path = cwd

    # 查找需要更新的API服务文件
    api_files = [
        base_path / 'services' / 'browser-automation' / 'api_server.py',
        base_path / 'services' / 'visualization-tools' / 'api_server.py',
        base_path / 'services' / 'platform_integration' / 'api_server.py',
        base_path / 'services' / 'intelligent-collaboration' / 'api_server.py',
        # base_path / "services" / "autonomous-control" / "api_server.py",  # 已有认证
        # base_path / "services" / "unified-identity" / "api_server.py",     # 已有认证
    ]

    updated_count = 0
    for file_path in api_files:
        if file_path.exists():
            if add_auth_to_endpoints(file_path):
                updated_count += 1
        else:
            logger.info(f"⚠️  文件不存在: {file_path}")

    logger.info(f"\n📊 总计更新了 {updated_count} 个文件")


if __name__ == '__main__':
    main()