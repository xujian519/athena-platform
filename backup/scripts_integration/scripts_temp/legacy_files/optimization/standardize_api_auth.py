#!/usr/bin/env python3
"""
API认证标准化脚本
为所有FastAPI服务添加统一的认证和授权
"""

import ast
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class APIAuthStandardizer:
    """API认证标准化器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.auth_template_path = self.project_root / 'shared' / 'auth' / 'auth_middleware.py'
        self.processed_files = []
        self.errors = []

    def find_fastapi_files(self) -> List[Path]:
        """查找所有FastAPI文件"""
        fastapi_files = []

        # 查找所有Python文件
        for py_file in self.project_root.rglob('*.py'):
            # 跳过测试文件和示例文件
            if any(part in py_file.parts for part in ['test', 'tests', '__pycache__', 'examples', '.venv']):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查是否包含FastAPI
                if 'FastAPI' in content or 'APIRouter' in content:
                    fastapi_files.append(py_file)
            except Exception as e:
                self.errors.append(f"读取文件失败 {py_file}: {str(e)}")

        return fastapi_files

    def analyze_fastapi_file(self, file_path: Path) -> Dict:
        """分析FastAPI文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content)

            analysis = {
                'path': str(file_path),
                'has_auth': False,
                'has_cors': False,
                'endpoints': [],
                'imports': [],
                'middleware_configured': False
            }

            # 检查导入
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis['imports'].append(node.module)

            # 检查认证相关
            auth_indicators = [
                'jwt', 'JWT', 'auth', 'Auth', 'HTTPBearer', 'Security',
                'Depends', 'OAuth2', 'authentication'
            ]

            for indicator in auth_indicators:
                if indicator in content:
                    analysis['has_auth'] = True
                    break

            # 检查CORS配置
            if 'CORS' in content or 'cors' in content:
                analysis['has_cors'] = True

            # 查找API端点
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            # 检查 @app.get, @router.post 等
                            if (isinstance(decorator.func, ast.Attribute) and
                                decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']):
                                endpoint_info = {
                                    'name': node.name,
                                    'method': decorator.func.attr.upper(),
                                    'path': '/',
                                    'has_auth': False
                                }

                                # 获取路径
                                if decorator.args:
                                    arg = decorator.args[0]
                                    if isinstance(arg, ast.Str):
                                        endpoint_info['path'] = arg.s
                                    elif isinstance(arg, ast.Constant):
                                        endpoint_info['path'] = arg.value

                                # 检查端点是否有认证
                                func_source = ast.get_source_segment(content, node) or ''
                                if any(auth in func_source for auth in ['Depends', 'Security', 'Bearer']):
                                    endpoint_info['has_auth'] = True

                                analysis['endpoints'].append(endpoint_info)

            # 检查中间件配置
            if 'add_middleware' in content or 'middleware' in content:
                analysis['middleware_configured'] = True

            return analysis

        except Exception as e:
            self.errors.append(f"分析文件失败 {file_path}: {str(e)}")
            return None

    def generate_auth_imports(self) -> str:
        """生成认证相关导入语句"""
        return '''
# 导入统一认证模块
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'shared'))

from auth.auth_middleware import (
    create_auth_middleware,
    setup_cors,
    require_permissions,
    get_current_user,
    get_api_key,
    HTTPBearer,
    Security,
    Depends
)
'''

    def generate_auth_setup(self, app_name: str = 'app') -> str:
        """生成认证设置代码"""
        return f'''
# 设置CORS
setup_cors({app_name})

# 添加认证中间件
{app_name}.add_middleware(
    create_auth_middleware,
    exclude_paths=['/', '/health', '/docs', '/openapi.json', '/metrics']
)
'''

    def add_auth_to_file(self, file_path: Path, analysis: Dict) -> bool:
        """为文件添加认证"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            new_lines = []

            # 检查是否已经有认证导入
            has_auth_imports = any('from auth' in line or 'import auth' in line for line in lines)

            # 1. 添加认证导入
            if not has_auth_imports and analysis['endpoints']:
                # 找到FastAPI导入的位置
                fastapi_import_idx = -1
                for i, line in enumerate(lines):
                    if 'from fastapi import' in line or 'import fastapi' in line:
                        fastapi_import_idx = i
                        break

                if fastapi_import_idx >= 0:
                    lines.insert(fastapi_import_idx + 1, self.generate_auth_imports())
                else:
                    # 如果没有找到FastAPI导入，在文件开头添加
                    lines.insert(0, self.generate_auth_imports())

            # 2. 添加认证设置（查找app = FastAPI()之后）
            app_creation_pattern = re.compile(r'^(\s*)(\w+)\s*=\s*FastAPI\(', re.MULTILINE)
            match = app_creation_pattern.search('\n'.join(lines))

            if match and analysis['endpoints']:
                app_name = match.group(2)
                indent = match.group(1)

                # 找到app创建的行号
                app_line_idx = -1
                for i, line in enumerate(lines):
                    if f"{app_name} = FastAPI(" in line:
                        app_line_idx = i
                        break

                if app_line_idx >= 0:
                    # 在app创建后添加认证设置
                    auth_setup = self.generate_auth_setup(app_name)
                    auth_lines = auth_setup.strip().split('\n')

                    for auth_line in auth_lines:
                        lines.insert(app_line_idx + 1, indent + auth_line)
                        app_line_idx += 1

            # 3. 为需要认证的端点添加认证装饰器
            # 这里需要更复杂的AST操作来准确添加依赖项
            # 暂时跳过这一步，因为需要确保不影响现有功能

            # 写回文件
            new_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.processed_files.append(str(file_path))
            return True

        except Exception as e:
            self.errors.append(f"添加认证失败 {file_path}: {str(e)}")
            return False

    def generate_report(self) -> str:
        """生成处理报告"""
        report = [
            "# API认证标准化报告\n",
            f"处理时间: {self.get_current_time()}",
            f"处理的文件数: {len(self.processed_files)}",
            f"错误数: {len(self.errors)}",
            "\n## 处理的文件\n",
        ]

        for file_path in self.processed_files:
            report.append(f"- {file_path}")

        if self.errors:
            report.append("\n## 错误信息\n")
            for error in self.errors:
                report.append(f"- {error}")

        report.append("\n## 后续建议\n")
        report.append('1. 检查每个修改过的文件，确保认证配置正确')
        report.append('2. 测试所有API端点，确保认证正常工作')
        report.append('3. 更新API文档，说明认证要求')
        report.append('4. 配置环境变量中的密钥和设置')
        report.append('5. 实施生产环境的密钥管理')

        return "\n".join(report)

    def get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def run(self):
        """运行标准化流程"""
        logger.info('🔐 开始API认证标准化...')

        # 1. 查找所有FastAPI文件
        fastapi_files = self.find_fastapi_files()
        logger.info(f"📁 找到 {len(fastapi_files)} 个FastAPI文件")

        # 2. 分析每个文件
        analyses = []
        for file_path in fastapi_files:
            logger.info(f"📖 分析文件: {file_path.relative_to(self.project_root)}")
            analysis = self.analyze_fastapi_file(file_path)
            if analysis:
                analyses.append(analysis)

        # 3. 筛选需要添加认证的文件
        files_need_auth = [
            analysis for analysis in analyses
            if not analysis['has_auth'] and analysis['endpoints']
        ]

        logger.info(f"🔧 需要添加认证的文件: {len(files_need_auth)} 个")

        # 4. 为文件添加认证
        for analysis in files_need_auth:
            file_path = Path(analysis['path'])
            logger.info(f"🛠️  正在处理: {file_path.relative_to(self.project_root)}")
            self.add_auth_to_file(file_path, analysis)

        # 5. 生成报告
        report_path = self.project_root / 'optimization_work' / 'logs' / 'api_auth_standardization_report.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        logger.info(f"\n✅ API认证标准化完成！")
        logger.info(f"📊 报告已保存到: {report_path}")

        return len(files_need_auth)


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    standardizer = APIAuthStandardizer(str(project_root))

    try:
        processed_count = standardizer.run()
        return processed_count
    except Exception as e:
        logger.info(f"❌ 执行失败: {str(e)}")
        return 0


if __name__ == '__main__':
    main()