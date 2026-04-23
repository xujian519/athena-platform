#!/usr/bin/env python3
"""
批量修复B904问题 (raise-without-from-inside-except)
"""

import subprocess


def get_b904_issues():
    """获取所有B904问题"""
    result = subprocess.run(
        ['ruff', 'check', 'core/', '--select', 'B904', '--output-format', 'json'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return []

    import json
    try:
        data = json.loads(result.stdout)
        return data
    except:
        return []

def fix_file(filepath, fix_lines):
    """修复单个文件"""
    try:
        with open(filepath) as f:
            lines = f.readlines()

        # 修复每一行
        for line_no in fix_lines:
            if line_no <= len(lines):
                line = lines[line_no - 1]
                # 如果这行包含raise且包含)但没有from e
                if 'raise' in line and ')' in line and 'from e' not in line:
                    # 在最后的)后添加from e
                    lines[line_no - 1] = line.rstrip().rstrip(')') + ') from e\n'

        # 写回文件
        with open(filepath, 'w') as f:
            f.writelines(lines)

        return True
    except Exception as e:
        print(f"修复文件失败 {filepath}: {e}")
        return False

def main():
    # 获取所有B904问题
    print("正在扫描B904问题...")
    issues = get_b904_issues()

    if not issues:
        print("没有发现B904问题!")
        return

    # 按文件分组
    from collections import defaultdict
    files = defaultdict(list)
    for issue in issues:
        filepath = issue['filename']
        line_no = issue['location']['row']
        files[filepath].append(line_no)

    print(f"发现 {len(issues)} 个B904问题，涉及 {len(files)} 个文件")

    # 修复每个文件
    fixed_count = 0
    for filepath, line_numbers in files.items():
        if fix_file(filepath, line_numbers):
            print(f"✅ {filepath}: {len(line_numbers)}个问题已修复")
            fixed_count += len(line_numbers)
        else:
            print(f"❌ {filepath}: 修复失败")

    print(f"\n总计修复了 {fixed_count} 个B904问题")

if __name__ == '__main__':
    main()
