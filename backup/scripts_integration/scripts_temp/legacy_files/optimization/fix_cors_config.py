#!/usr/bin/env python3
"""
修复CORS配置脚本
将不安全的CORS配置替换为安全的配置
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

class CORSFixer:
    """CORS配置修复器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixed_files = []
        self.errors = []

    def find_insecure_cors_files(self) -> List[Path]:
        """查找使用不安全CORS配置的文件"""
        insecure_files = []

        # 查找所有Python文件
        for py_file in self.project_root.rglob('*.py'):
            # 跳过虚拟环境和其他不需要检查的目录
            if any(part in py_file.parts for part in [
                '__pycache__', '.venv', 'venv', 'node_modules',
                '.git', 'dist', 'build', 'examples'
            ]):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查是否包含不安全的CORS配置
                if 'allow_origins=['*']' in content or 'allow_origins = ['*']' in content:
                    # 检查是否已经使用了统一CORS配置
                    if 'setup_cors' not in content:
                        insecure_files.append(py_file)
            except Exception as e:
                self.errors.append(f"读取文件失败 {py_file}: {str(e)}")

        return insecure_files

    def fix_cors_in_file(self, file_path: Path) -> bool:
        """修复文件中的CORS配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            new_lines = []
            modified = False

            # 记录需要处理的CORS配置块
            cors_blocks = []
            i = 0
            while i < len(lines):
                line = lines[i]

                # 检查是否是CORS中间件配置开始
                if 'app.add_middleware(' in line and 'CORSMiddleware' in lines[i+1]:
                    # 找到完整的CORS配置块
                    block_start = i
                    indent_level = len(line) - len(line.lstrip())

                    # 找到配置块结束
                    j = i + 1
                    while j < len(lines):
                        current_line = lines[j]
                        if current_line.strip() == ')':
                            # 找到结束
                            block_end = j
                            cors_blocks.append((block_start, block_end))
                            break
                        j += 1
                    i = j + 1
                else:
                    i += 1

            # 如果找到了CORS配置块，进行替换
            if cors_blocks:
                # 保留第一块之前的行
                new_lines.extend(lines[:cors_blocks[0][0]])

                # 添加统一CORS配置导入
                # 检查是否已经导入了所需模块
                has_imports = any('from shared.auth' in line or 'import shared.auth' in line
                                for line in lines[:cors_blocks[0][0]])

                if not has_imports:
                    # 找到FastAPI导入位置
                    fastapi_import_idx = -1
                    for k, line in enumerate(lines[:cors_blocks[0][0]]):
                        if 'from fastapi import' in line or 'import fastapi' in line:
                            fastapi_import_idx = k
                            break

                    if fastapi_import_idx >= 0:
                        new_lines.insert(fastapi_import_idx + 1, '')
                        new_lines.insert(fastapi_import_idx + 2, '# 导入统一认证模块')
                        new_lines.insert(fastapi_import_idx + 3, 'from shared.auth.auth_middleware import (')
                        new_lines.insert(fastapi_import_idx + 4, '    create_auth_middleware,')
                        new_lines.insert(fastapi_import_idx + 5, '    setup_cors')
                        new_lines.insert(fastapi_import_idx + 6, ')')
                    else:
                        # 如果没找到FastAPI导入，在文件开头添加
                        new_lines.insert(0, 'from shared.auth.auth_middleware import (')
                        new_lines.insert(1, '    create_auth_middleware,')
                        new_lines.insert(2, '    setup_cors')
                        new_lines.insert(3, ')')
                        new_lines.insert(4, '')

                # 跳过所有旧的CORS配置块
                last_block_end = cors_blocks[-1][1] + 1

                # 添加新的配置（在FastAPI应用创建后）
                # 查找 app = FastAPI() 的位置
                fastapi_app_idx = -1
                for k in range(last_block_end, len(lines)):
                    if 'app = FastAPI(' in lines[k]:
                        fastapi_app_idx = k
                        break

                if fastapi_app_idx >= 0:
                    # 在FastAPI创建后添加新配置
                    # 添加中间的代码（从上一个CORS块后到FastAPI创建）
                    new_lines.extend(lines[last_block_end:fastapi_app_idx + 1])

                    # 添加新的CORS和认证配置
                    new_lines.extend([
                        '',
                        '# 设置CORS（使用统一配置）',
                        'setup_cors(app)',
                        '',
                        '# 添加认证中间件',
                        'app.add_middleware(',
                        '    create_auth_middleware,',
                        '    exclude_paths=['/', '/health', '/docs', '/openapi.json', '/metrics']',
                        ')',
                    ])

                    # 添加剩余的代码
                    new_lines.extend(lines[fastapi_app_idx + 1:])
                else:
                    # 如果没找到FastAPI应用，直接添加剩余代码
                    new_lines.extend(lines[last_block_end:])

                modified = True

            # 如果没有找到完整的CORS配置块，查找并替换简单的allow_origins配置
            elif 'allow_origins=['*']' in content:
                # 简单替换
                content = re.sub(
                    r'allow_origins=\["\*"\]',
                    'allow_origins=['http://localhost:3000', 'http://localhost:8080']',
                    content
                )
                new_lines = content.split('\n')
                modified = True

            # 写回文件
            if modified:
                new_content = '\n'.join(new_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

            return False

        except Exception as e:
            self.errors.append(f"修复CORS配置失败 {file_path}: {str(e)}")
            return False

    def generate_report(self) -> str:
        """生成修复报告"""
        report = [
            "# CORS配置修复报告\n",
            f"处理时间: {self.get_current_time()}",
            f"修复的文件数: {len(self.fixed_files)}",
            f"错误数: {len(self.errors)}",
            "\n## 修复的文件\n",
        ]

        for file_path in self.fixed_files:
            report.append(f"- {file_path}")

        if self.errors:
            report.append("\n## 错误信息\n")
            for error in self.errors:
                report.append(f"- {error}")

        report.append("\n## 安全建议\n")
        report.append('1. 生产环境不应使用通配符(*)作为允许的源')
        report.append('2. 明确指定允许的域名列表')
        report.append('3. 使用环境变量管理CORS配置')
        report.append('4. 定期审查CORS配置')
        report.append('5. 实施额外的安全头')

        return "\n".join(report)

    def get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def run(self):
        """运行修复流程"""
        logger.info('🔧 开始修复CORS配置...')

        # 1. 查找使用不安全CORS配置的文件
        insecure_files = self.find_insecure_cors_files()
        logger.info(f"📁 找到 {len(insecure_files)} 个使用不安全CORS配置的文件")

        # 2. 修复每个文件
        for file_path in insecure_files:
            logger.info(f"🛠️  正在修复: {file_path.relative_to(self.project_root)}")
            if self.fix_cors_in_file(file_path):
                self.fixed_files.append(file_path)

        # 3. 生成报告
        report_path = self.project_root / 'optimization_work' / 'logs' / 'cors_fix_report.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        logger.info(f"\n✅ CORS配置修复完成！")
        logger.info(f"📊 修复了 {len(self.fixed_files)} 个文件")
        logger.info(f"📄 报告已保存到: {report_path}")

        return len(self.fixed_files)


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    fixer = CORSFixer(str(project_root))

    try:
        fixed_count = fixer.run()
        return fixed_count
    except Exception as e:
        logger.info(f"❌ 执行失败: {str(e)}")
        return 0


if __name__ == '__main__':
    main()