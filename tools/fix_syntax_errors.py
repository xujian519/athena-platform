#!/usr/bin/env python3
"""
Python语法错误修复工具
自动检测并修复常见的Python语法错误
"""

import ast
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class SyntaxErrorFixer:
    """Python语法错误修复器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixed_files = []
        self.failed_files = []

    def find_python_files(self) -> list[Path]:
        """查找所有Python文件"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # 跳过特定目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def check_syntax(self, file_path: Path) -> tuple[bool, str]:
        """检查文件语法"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # 尝试解析
            ast.parse(content)
            return True, '语法正确'

        except SyntaxError as e:
            return False, f"语法错误: {e.msg} (行 {e.lineno})"
        except Exception as e:
            return False, f"其他错误: {str(e)}"

    def fix_common_errors(self, file_path: Path) -> bool:
        """修复常见的语法错误"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 修复常见的语法错误
            fixes_applied = []

            # 1. 修复未闭合的括号、引号等
            content = self.fix_unmatched_brackets(content, fixes_applied)

            # 2. 修复f-string语法错误
            content = self.fix_fstring_errors(content, fixes_applied)

            # 3. 修复字典键缺少冒号
            content = self.fix_dict_key_errors(content, fixes_applied)

            # 4. 修复缩进错误
            content = self.fix_indentation_errors(content, fixes_applied)

            # 5. 修复未闭合的字符串
            content = self.fix_unclosed_strings(content, fixes_applied)

            # 6. 修复多余的特殊字符
            content = self.fix_special_characters(content, fixes_applied)

            # 如果有修复，保存文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            logger.info(f"修复文件失败 {file_path}: {e}")
            return False

    def fix_unmatched_brackets(self, content: str, fixes: list[str]) -> str:
        """修复未匹配的括号"""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # 简单的括号修复
            if line.count('(') > line.count(')'):
                line += ')' * (line.count('(') - line.count(')'))
                fixes.append("添加缺失的右括号")
            elif line.count(')') > line.count('('):
                # 移除多余的右括号
                excess = line.count(')') - line.count('(')
                line = line.replace(')', '', excess)
                fixes.append("移除多余的右括号")

            # 修复方括号
            if line.count('[') > line.count(']'):
                line += ']' * (line.count('[') - line.count(']'))
                fixes.append("添加缺失的右方括号")

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_fstring_errors(self, content: str, fixes: list[str]) -> str:
        """修复f-string错误"""
        # 修复f-string中的转义字符问题
        content = re.sub(
            r'f"([^"]*)\\([^\\n][^"]*)"',
            lambda m: 'f"' + m.group(1).replace('\\\\', '\\\\\\\\') + '\\\\' + m.group(2) + '"',
            content
        )

        # 修复未闭合的f-string
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            if 'f"' in line or "f'" in line:
                # 检查f-string是否闭合
                if line.count('f"') != line.count('"'):
                    if line.count('f"') > line.count('"'):
                        line += '"'
                        fixes.append('闭合f-string')
                    else:
                        # 复杂情况，标记但不过度修复
                        pass
            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_dict_key_errors(self, content: str, fixes: list[str]) -> str:
        """修复字典键语法错误"""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # 修复缺少冒号的字典键
            if ':' not in line and ('"' in line or "'" in line):
                # 简单检测是否是字典行
                if '{' in line or line.strip().startswith((' ', '\t')):
                    # 尝试修复
                    if line.strip().endswith((',', '}')):
                        parts = line.rsplit(',', 1)
                        if len(parts) == 2 and (parts[0].strip().startswith('"') or parts[0].strip().startswith("'")):
                            line = f"{parts[0]}: {parts[1]}"
                            fixes.append('添加字典键冒号')

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_indentation_errors(self, content: str, fixes: list[str]) -> str:
        """修复缩进错误"""
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue

            # 检查是否需要缩进
            if i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.endswith(':'):
                    if not line.startswith(' ') and not line.startswith('\t'):
                        line = '    ' + line
                        fixes.append('修复缩进')

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_unclosed_strings(self, content: str, fixes: list[str]) -> str:
        """修复未闭合的字符串"""
        # 修复三引号字符串
        lines = content.split('\n')
        fixed_lines = []

        in_triple_string = False
        triple_quote_char = None

        for line in lines:
            # 检查三引号
            if '"""' in line or "'''" in line:
                if not in_triple_string:
                    in_triple_string = True
                    triple_quote_char = '"""' if '"""' in line else "'''"
                else:
                    if triple_quote_char in line:
                        in_triple_string = False

            # 如果在三引号字符串中，检查是否需要闭合
            if in_triple_string and line.endswith('\\'):
                line = line.rstrip('\\') + '\n' + triple_quote_char
                fixes.append('闭合三引号字符串')

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_special_characters(self, content: str, fixes: list[str]) -> str:
        """修复特殊字符问题"""
        # 移除无效的特殊字符
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)

        # 修复数字字面量错误（如多余的数字）
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # 修复无效的数字字面量
            if re.search(r'\b\d+\s+\d+\b', line):
                # 如果数字之间有空格但不是有效的表达式
                line = re.sub(r'\b(\d+)\s+(\d+)\b', r'\1', line)
                fixes.append('移除无效的数字字面量')

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def process_files(self, file_list: list[str] | None = None):
        """处理文件列表"""
        if file_list is None:
            python_files = self.find_python_files()
        else:
            python_files = [Path(f) for f in file_list if f.endswith('.py')]

        logger.info(f"开始检查 {len(python_files)} 个Python文件...")

        # 首先找出有语法错误的文件
        error_files = []
        for file_path in python_files:
            is_valid, msg = self.check_syntax(file_path)
            if not is_valid:
                error_files.append((file_path, msg))
                logger.info(f"❌ {file_path}: {msg}")

        logger.info(f"\n发现 {len(error_files)} 个文件有语法错误\n")

        # 修复错误文件
        for file_path, _error_msg in error_files:
            logger.info(f"修复文件: {file_path}")
            self.fix_common_errors(file_path)

            # 再次检查
            is_valid, msg = self.check_syntax(file_path)
            if is_valid:
                logger.info("✅ 修复成功")
                self.fixed_files.append(str(file_path))
            else:
                logger.info(f"❌ 修复失败: {msg}")
                self.failed_files.append((str(file_path), msg))

        logger.info("\n修复完成:")
        logger.info(f"  成功: {len(self.fixed_files)}")
        logger.info(f"  失败: {len(self.failed_files)}")

def main():
    """主函数"""
    project_root = '/Users/xujian/Athena工作平台'

    # 已知有错误的文件列表（来自之前的分析）
    known_error_files = [
        '/Users/xujian/Athena工作平台/patent-guideline-system/src/models/graph_schema.py',
        '/Users/xujian/Athena工作平台/domains/legal-ai/services/hybrid_clause_search.py',
        '/Users/xujian/Athena工作平台/core/search/patent_query_processor.py',
        '/Users/xujian/Athena工作平台/core/autonomous_control/xiaonuo_executor.py',
        '/Users/xujian/Athena工作平台/core/authenticity/zero_simulation_data_enforcer.py',
        '/Users/xujian/Athena工作平台/patent-platform/workspace/src/knowledge_graph/neo4j_manager.py',
        '/Users/xujian/Athena工作平台/patent-platform/workspace/src/tools/patent_tools/__init__.py',
        '/Users/xujian/Athena工作平台/patent-platform/workspace/src/action/workflow_orchestrator.py',
        '/Users/xujian/Athena工作平台/patent-platform/workspace/src/perception/enhanced_vector_database.py',
        '/Users/xujian/Athena工作平台/utils/patent-search/use_boolean_patent_search.py',
        '/Users/xujian/Athena工作平台/patent_hybrid_retrieval/chinese_bert_integration/demo_bert_integration.py',
        '/Users/xujian/Athena工作平台/scripts/analyze_crawler_tools.py',
        '/Users/xujian/Athena工作平台/scripts/system_operations/enhanced_cleaner.py',
        '/Users/xujian/Athena工作平台/services/optimization/quality_assurance_system.py',
        '/Users/xujian/Athena工作平台/services/ai-services/ai-models/deepseek-math-v2/self_verifying_patent_agent.py',
        '/Users/xujian/Athena工作平台/services/ai-services/ai-models/deepseek-math-v2/deploy_deepseek_v2.py',
        '/Users/xujian/Athena工作平台/services/ai-services/ai-models/deepseek-math-v2/data_generator.py',
        '/Users/xujian/Athena工作平台/services/ai-services/ai-models/deepseek-math-v2/deployment_integrator.py',
        '/Users/xujian/Athena工作平台/services/ai-services/ai-models/deepseek-math-v2/core/data_generator.py',
        '/Users/xujian/Athena工作平台/services/ai-services/ai-models/pqai-integration/models/chinese_patent_models.py'
    ]

    # 创建修复器
    fixer = SyntaxErrorFixer(project_root)

    # 处理已知错误文件
    fixer.process_files(known_error_files)

    # 生成报告
    report = {
        'timestamp': '2025-12-12T17:00:00+08:00',
        'fixed_files': fixer.fixed_files,
        'failed_files': fixer.failed_files,
        'total_processed': len(known_error_files),
        'success_rate': f"{len(fixer.fixed_files) / len(known_error_files) * 100:.1f}%"
    }

    # 保存报告
    import json
    report_path = os.path.join(project_root, 'reports', 'syntax_fix_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"\n修复报告已保存到: {report_path}")

if __name__ == '__main__':
    main()
