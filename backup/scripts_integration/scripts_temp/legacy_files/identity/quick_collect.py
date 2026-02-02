#!/usr/bin/env python3
"""
快速收集Athena和小诺的身份信息
"""
import os
import json
from pathlib import Path
from datetime import datetime

def search_identity_files():
    """搜索身份相关文件"""
    backup_paths = [
        "/Volumes/xujian/开发项目备份/知识库0.01",
        "/Volumes/xujian/开发项目备份/Athena工作平台-air"
    ]

    # 关键词
    keywords = ["athena", "小娜", "xiaonuo", "小诺", "agent", "identity", "personality"]

    found_files = []

    for backup_path in backup_paths:
        print(f"\n🔍 搜索路径: {backup_path}")
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                if any(keyword in file.lower() for keyword in keywords):
                    file_path = os.path.join(root, file)
                    found_files.append(file_path)
                    print(f"  找到: {file_path}")

    return found_files

def extract_identity_info(file_path):
    """提取身份信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单提取关键信息
        info = {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "modified_time": os.path.getmtime(file_path)
        }

        # 检查文件类型
        if file_path.endswith('.json'):
            try:
                data = json.load(f)
                info["type"] = "json"
                info["has_name"] = "name" in str(data)
                info["has_personality"] = "personality" in str(data).lower()
            except:
                pass
        elif "athena" in content.lower() or "小娜" in content:
            info["type"] = "athena_related"
        elif "xiaonuo" in content.lower() or "小诺" in content:
            info["type"] = "xiaonuo_related"

        return info
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return None

def main():
    print("=" * 60)
    print("    🎯 快速收集Athena和小诺身份信息")
    print("=" * 60)

    # 1. 搜索文件
    print("\n📁 搜索身份相关文件...")
    files = search_identity_files()

    print(f"\n📊 找到 {len(files)} 个相关文件")

    # 2. 提取信息
    print("\n📚 提取身份信息...")
    collected_info = []

    for file_path in files[:20]:  # 限制前20个文件
        print(f"\n处理: {file_path}")
        info = extract_identity_info(file_path)
        if info:
            collected_info.append(info)

    # 3. 保存结果
    print("\n💾 保存收集结果...")
    storage_path = Path("/Users/xujian/Athena工作平台/data/identity_quick_collect")
    storage_path.mkdir(parents=True, exist_ok=True)

    # 保存文件列表
    with open(storage_path / "found_files.json", 'w', encoding='utf-8') as f:
        json.dump(files, f, ensure_ascii=False, indent=2)

    # 保存提取的信息
    with open(storage_path / "extracted_info.json", 'w', encoding='utf-8') as f:
        json.dump(collected_info, f, ensure_ascii=False, indent=2)

    # 生成报告
    report = f"""
# Athena和小诺身份信息快速收集报告

**收集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 收集统计
- **找到文件总数**: {len(files)}
- **成功提取信息**: {len(collected_info)}
- **备份路径**:
  - /Volumes/xujian/开发项目备份/知识库0.01
  - /Volumes/xujian/开发项目备份/Athena工作平台-air

## 📁 存储位置
- **文件列表**: {storage_path}/found_files.json
- **提取信息**: {storage_path}/extracted_info.json
- **存储目录**: {storage_path}

## 📋 文件类型分布
"""

    # 统计文件类型
    type_counts = {}
    for info in collected_info:
        t = info.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    for t, count in type_counts.items():
        report += f"- {t}: {count}\n"

    with open(storage_path / "quick_report.md", 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 快速收集完成！")
    print(f"📁 存储位置: {storage_path}")
    print(f"📄 报告文件: {storage_path}/quick_report.md")

if __name__ == "__main__":
    main()