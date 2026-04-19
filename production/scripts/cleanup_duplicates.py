#!/usr/bin/env python3
"""
清理重复数据脚本
Cleanup Duplicate Data

识别并清理散落的重复数据文件

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class DuplicateCleanup:
    """重复数据清理器"""

    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.production_path = self.base_path / "production"
        self.cleanup_log = []

    def run_cleanup(self) -> Any:
        """执行清理流程"""
        print("\n🧹 开始清理重复数据...")

        cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "cleaned_files": {},
            "space_freed_mb": 0,
            "cleanup_log": []
        }

        # 1. 清理知识图谱重复文件
        kg_cleaned = self.cleanup_knowledge_graph_files()
        cleanup_report["cleaned_files"]["knowledge_graph"] = kg_cleaned

        # 2. 清理重复的测试报告
        reports_cleaned = self.cleanup_test_reports()
        cleanup_report["cleaned_files"]["reports"] = reports_cleaned

        # 3. 清理临时文件
        temp_cleaned = self.cleanup_temp_files()
        cleanup_report["cleaned_files"]["temp"] = temp_cleaned

        # 4. 整理数据目录结构
        self.organize_data_structure()

        # 5. 生成清理报告
        self.save_cleanup_report(cleanup_report)

        print("\n✅ 清理完成！")
        return cleanup_report

    def cleanup_knowledge_graph_files(self) -> Any:
        """清理知识图谱重复文件"""
        print("\n📚 清理知识图谱重复文件...")

        kg_files = list(self.production_path.rglob("*legal*.json"))
        kg_files.extend(list(self.production_path.rglob("*kg*.json")))

        # 按文件类型分组
        file_groups = {
            "entities": [],
            "relations": [],
            "other": []
        }

        for file_path in kg_files:
            if "entities" in file_path.name:
                file_groups["entities"].append(file_path)
            elif "relations" in file_path.name:
                file_groups["relations"].append(file_path)
            else:
                file_groups["other"].append(file_path)

        cleaned = {"entities": 0, "relations": 0, "other": 0}

        # 处理实体文件
        for group_name, files in file_groups.items():
            if files:
                # 按修改时间排序，保留最新的
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                if len(files) > 1:
                    print(f"\n{group_name} 文件:")
                    for i, f in enumerate(files):
                        age_hours = (datetime.now().timestamp() - f.stat().st_mtime) / 3600
                        status = "保留" if i == 0 else "删除"
                        print(f"  {status}: {f.name} ({age_hours:.1f}小时前)")

                    # 删除旧文件
                    for f in files[1:]:
                        size_mb = f.stat().st_size / 1024 / 1024
                        f.unlink()
                        cleaned[group_name] += 1
                        self.cleanup_log.append(f"删除: {f.name} ({size_mb:.2f} MB)")

        return cleaned

    def cleanup_test_reports(self) -> Any:
        """清理重复的测试报告"""
        print("\n📄 清理测试报告文件...")

        reports_dir = self.production_path / "output" / "reports"
        if not reports_dir.exists():
            return {"deleted": 0}

        report_types = {
            "vector_search_test": [],
            "vector_import_report": [],
            "legal_import_report": [],
            "other": []
        }

        # 按类型分组
        for file_path in reports_dir.glob("*.json"):
            matched = False
            for prefix in report_types:
                if prefix in file_path.name:
                    report_types[prefix].append(file_path)
                    matched = True
                    break
            if not matched:
                report_types["other"].append(file_path)

        cleaned = {"deleted": 0, "by_type": {}}

        for report_type, files in report_types.items():
            if files and report_type != "other":
                # 按时间排序
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # 保留最近3个
                if len(files) > 3:
                    for f in files[3:]:
                        size_kb = f.stat().st_size / 1024
                        f.unlink()
                        cleaned["deleted"] += 1
                        if report_type not in cleaned["by_type"]:
                            cleaned["by_type"][report_type] = 0
                        cleaned["by_type"][report_type] += 1
                        self.cleanup_log.append(f"删除报告: {f.name} ({size_kb:.1f} KB)")

        return cleaned

    def cleanup_temp_files(self) -> Any:
        """清理临时文件"""
        print("\n🗂️ 清理临时文件...")

        temp_patterns = [
            "*.tmp",
            "*.bak",
            "*.log",
            "__pycache__",
            ".DS_Store",
            "*.pyc"
        ]

        cleaned = {"files": 0, "dirs": 0, "space_mb": 0}

        for pattern in temp_patterns:
            for item in self.production_path.rglob(pattern):
                try:
                    if item.is_file():
                        size_kb = item.stat().st_size / 1024
                        item.unlink()
                        cleaned["files"] += 1
                        cleaned["space_mb"] += size_kb / 1024
                        self.cleanup_log.append(f"删除临时文件: {item.relative_to(self.base_path)}")
                    elif item.is_dir() and pattern == "__pycache__":
                        shutil.rmtree(item)
                        cleaned["dirs"] += 1
                        self.cleanup_log.append(f"删除临时目录: {item.relative_to(self.base_path)}")
                except Exception as e:
                    print(f"  ⚠️ 无法删除 {item}: {e}")

        return cleaned

    def organize_data_structure(self) -> Any:
        """整理数据目录结构"""
        print("\n📁 整理数据目录结构...")

        # 创建标准目录结构
        standard_dirs = [
            self.production_path / "data" / "raw",
            self.production_path / "data" / "processed",
            self.production_path / "data" / "vectors",
            self.production_path / "data" / "knowledge_graph",
            self.production_path / "data" / "metadata"
        ]

        for dir_path in standard_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 移动文件到标准位置
        output_path = self.production_path / "output"

        # 移动kg_data到标准位置
        kg_src = output_path / "kg_data"
        kg_dst = self.production_path / "data" / "knowledge_graph"
        if kg_src.exists() and not kg_dst.exists():
            shutil.move(str(kg_src), str(kg_dst))
            self.cleanup_log.append("移动知识图谱数据到标准位置")

        # 复制最近的报告到metadata
        reports_src = output_path / "reports"
        meta_dst = self.production_path / "data" / "metadata"
        if reports_src.exists():
            # 复制向量导入报告
            import_report = reports_src / "vector_import_report.json"
            if import_report.exists():
                shutil.copy2(str(import_report), str(meta_dst / "vector_import_latest.json"))

            # 复制最新的质量报告
            latest_report = max(
                reports_src.glob("vector_search_test_*.json"),
                key=lambda x: x.stat().st_mtime,
                default=None
            )
            if latest_report:
                shutil.copy2(
                    str(latest_report),
                    str(meta_dst / f"quality_report_{latest_report.stem.split('_')[-1]}.json")
                )

        self.cleanup_log.append("数据目录结构已整理")

    def save_cleanup_report(self, report: dict) -> None:
        """保存清理报告"""
        report["cleanup_log"] = self.cleanup_log

        report_path = self.production_path / "data" / "metadata" / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📋 清理报告已保存: {report_path}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("🧹 清理重复数据 🧹")
    print("="*100)

    cleanup = DuplicateCleanup()
    report = cleanup.run_cleanup()

    print("\n📊 清理统计:")
    for category, cleaned in report["cleaned_files"].items():
        if isinstance(cleaned, dict):
            for sub_cat, count in cleaned.items():
                print(f"  {category}.{sub_cat}: {count} 个文件")
        else:
            print(f"  {category}: {cleaned} 个文件")

    print(f"\n💾 释放空间: {report['space_freed_mb']:.2f} MB")

    return report

if __name__ == "__main__":
    main()
