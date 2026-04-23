#!/usr/bin/env python3
"""
CORS安全修复工具
CORS Security Fix Tool

功能：
1. 搜索所有使用通配符的CORS配置
2. 替换为从环境变量读取的安全配置
3. 生成修复报告
"""

import os
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class CORSFixer:
    """CORS配置修复器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixed_files = []
        self.errors = []

        # 需要排除的目录
        self.exclude_dirs = {
            "backup",
            "archive",
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "venv",
            ".venv",
            "build",
            "dist",
            "docs",
            "data",
        }

    def should_process_file(self, file_path: Path) -> bool:
        """判断文件是否需要处理"""
        # 检查文件扩展名
        if file_path.suffix != ".py":
            return False

        # 检查是否在排除目录中
        parts = file_path.parts
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in parts:
                return False

        # 排除备份文件
        if any(pattern in str(file_path) for pattern in ["backup", "old", "deprecated", "bak"]):
            return False

        # 排除测试文件
        if "test" in file_path.name:
            return False

        return True

    def find_cors_files(self) -> list[Path]:
        """查找所有包含CORS配置的Python文件"""
        cors_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 移除排除的目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = Path(root) / file

                if not self.should_process_file(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")

                    # 检查是否包含CORS配置
                    if "CORSMiddleware" in content or "allow_origins" in content:
                        cors_files.append(file_path)
                except Exception as e:
                    self.errors.append(f"读取文件失败 {file_path}: {e}")

        return cors_files

    def has_unsafe_cors(self, content: str) -> bool:
        """检查是否包含不安全的CORS配置"""
        # 检查 allow_origins=ALLOWED_ORIGINS
        if re.search(r'allow_origins\s*=\s*\["\*"\]', content):
            return True
        if re.search(r'allow_origins:\s*\["\*"\]', content):
            return True

        return False

    def has_safe_cors_import(self, content: str) -> bool:
        """检查是否已经导入了安全CORS配置"""
        # 检查是否从 core.security 导入 ALLOWED_ORIGINS
        if "from core.security.auth import" in content and "ALLOWED_ORIGINS" in content:
            return True
        if "from core.security import" in content and "ALLOWED_ORIGINS" in content:
            return True
        return False

    def fix_cors_config(self, file_path: Path) -> bool:
        """修复单个文件的CORS配置"""
        try:
            content = file_path.read_text(encoding="utf-8")

            # 如果已经是安全的配置，跳过
            if not self.has_unsafe_cors(content):
                return False

            # 如果已经导入了安全配置，只需替换通配符
            if self.has_safe_cors_import(content):
                # 替换 allow_origins=ALLOWED_ORIGINS 为 allow_origins=ALLOWED_ORIGINS
                new_content = re.sub(
                    r'allow_origins\s*=\s*\["\*"\]',
                    'allow_origins=ALLOWED_ORIGINS',
                    content
                )
                new_content = re.sub(
                    r'allow_origins:\s*\["\*"\]',
                    'allow_origins: ALLOWED_ORIGINS',
                    new_content
                )

                if new_content != content:
                    file_path.write_text(new_content, encoding="utf-8")
                    self.fixed_files.append(str(file_path))
                    return True
                return False

            # 需要添加导入和替换
            lines = content.split('\n')
            new_lines = []
            import_added = False
            cors_import_idx = -1

            # 找到CORSMiddleware的导入位置
            for i, line in enumerate(lines):
                if 'from fastapi.middleware.cors import CORSMiddleware' in line:
                    cors_import_idx = i
                new_lines.append(line)

            # 如果找到了CORS导入，在其后添加安全配置导入
            if cors_import_idx >= 0 and not import_added:
                insert_pos = cors_import_idx + 1
                # 在插入位置前添加空行
                if insert_pos < len(new_lines) and new_lines[insert_pos].strip():
                    new_lines.insert(insert_pos, '')
                    insert_pos += 1

                # 添加导入
                import_line = 'from core.security.auth import ALLOWED_ORIGINS'
                new_lines.insert(insert_pos, import_line)
                import_added = True

            # 替换不安全的CORS配置
            content = '\n'.join(new_lines)
            content = re.sub(
                r'allow_origins\s*=\s*\["\*"\]',
                'allow_origins=ALLOWED_ORIGINS',
                content
            )
            content = re.sub(
                r'allow_origins:\s*\["\*"\]',
                'allow_origins: ALLOWED_ORIGINS',
                content
            )

            if content != '\n'.join(lines):
                file_path.write_text(content, encoding="utf-8")
                self.fixed_files.append(str(file_path))
                return True

            return False

        except Exception as e:
            self.errors.append(f"修复文件失败 {file_path}: {e}")
            return False

    def run(self) -> dict:
        """执行修复"""
        print("🔍 搜索CORS配置文件...")

        cors_files = self.find_cors_files()
        print(f"📊 找到 {len(cors_files)} 个包含CORS配置的文件")

        unsafe_count = 0
        for file_path in cors_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                if self.has_unsafe_cors(content):
                    unsafe_count += 1
            except:
                pass

        print(f"⚠️  发现 {unsafe_count} 个不安全的CORS配置")
        print("🔧 开始修复...")

        fixed_count = 0
        for file_path in cors_files:
            if self.fix_cors_config(file_path):
                fixed_count += 1
                print(f"  ✅ {file_path.relative_to(self.project_root)}")

        print("\n✅ 修复完成！")
        print(f"   - 修复文件数: {fixed_count}")
        print(f"   - 错误数: {len(self.errors)}")

        if self.errors:
            print("\n❌ 错误列表:")
            for error in self.errors:
                print(f"   - {error}")

        return {
            "total_files": len(cors_files),
            "unsafe_files": unsafe_count,
            "fixed_files": fixed_count,
            "errors": self.errors
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="CORS安全修复工具")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅扫描，不实际修复"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=str(Path(__file__).parent.parent.parent),
        help="项目根目录"
    )

    args = parser.parse_args()

    project_root = Path(args.project_root)
    if not project_root.exists():
        print(f"❌ 项目根目录不存在: {project_root}")
        return 1

    fixer = CORSFixer(project_root)

    if args.dry_run:
        print("🔍 仅扫描模式 (dry-run)")
        cors_files = fixer.find_cors_files()
        print("\n📊 扫描结果:")
        print(f"   - 总文件数: {len(cors_files)}")

        unsafe_files = []
        for file_path in cors_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                if fixer.has_unsafe_cors(content):
                    unsafe_files.append(file_path)
            except:
                pass

        print(f"   - 不安全配置: {len(unsafe_files)}")
        print("\n⚠️  不安全文件列表:")
        for file_path in unsafe_files:
            print(f"   - {file_path.relative_to(project_root)}")

        return 0

    # 执行修复
    result = fixer.run()

    # 生成报告
    report_path = project_root / "docs" / "CORS_FIX_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# CORS安全修复报告\n\n")
        f.write(f"**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 修复统计\n\n")
        f.write(f"- 总文件数: {result['total_files']}\n")
        f.write(f"- 不安全配置: {result['unsafe_files']}\n")
        f.write(f"- 已修复: {result['fixed_files']}\n")
        f.write(f"- 错误数: {len(result['errors'])}\n\n")

        if result['fixed_files'] > 0:
            f.write("## 已修复文件\n\n")
            for file_path in fixer.fixed_files[:50]:  # 只列出前50个
                f.write(f"- {file_path}\n")

        if result['errors']:
            f.write("\n## 错误列表\n\n")
            for error in result['errors']:
                f.write(f"- {error}\n")

    print(f"\n📄 报告已生成: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
