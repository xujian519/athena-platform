#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作文件夹整理工具
Organize Work Folder Tool

自动整理'/Users/xujian/工作'文件夹中的文件和目录
"""

import os
import shutil
from pathlib import Path
import re
from datetime import datetime
import json

class WorkFolderOrganizer:
    """工作文件夹整理器"""

    def __init__(self, work_folder="/Users/xujian/工作"):
        self.work_folder = Path(work_folder)
        self.organized_folders = {
            "01_客户管理": [
                "客户", "客户管理", "委托人", "客户资料", "客户档案"
            ],
            "02_专利管理": [
                "专利", "专利申请", "专利档案", "发明", "实用新型",
                "外观设计", "专利分析", "专利检索", "专利审查"
            ],
            "03_法律文书": [
                "法律", "文书", "合同", "协议", "起诉状", "答辩状",
                "法律文件", "法务", "诉讼"
            ],
            "04_审查意见": [
                "审查意见", "审查", "答复", "OA", "审查通知",
                "驳回分析", "审查意见答复"
            ],
            "05_技术资料": [
                "技术", "研发", "技术资料", "研发资料", "实验",
                "测试", "技术文档"
            ],
            "06_财务档案": [
                "财务", "费用", "缴费", "发票", "账单", "成本",
                "财务档案", "收费"
            ],
            "07_系统管理": [
                "系统", "管理", "档案", "档案管理", "归档",
                "备案", "登记", "统计"
            ],
            "08_模板库": [
                "模板", "范本", "样本", "格式", "样板",
                "模板库", "范例"
            ]
        }
        self.temp_folder = "09_临时文件"
        self.archive_folder = "10_归档文件"

        # 创建目标文件夹
        self._ensure_folders()

    def _ensure_folders(self):
        """确保目标文件夹存在"""
        for folder_name in list(self.organized_folders.keys()) + [self.temp_folder, self.archive_folder]:
            folder_path = self.work_folder / folder_name
            folder_path.mkdir(exist_ok=True)

    def classify_folder(self, folder_name):
        """分类文件夹"""
        folder_name_lower = folder_name.lower()

        # 直接匹配
        for target_folder, keywords in self.organized_folders.items():
            for keyword in keywords:
                if keyword in folder_name:
                    return target_folder

        # 专利申请号模式
        patent_patterns = [
            r'^\d{12}\.\d+',  # 申请号格式：202211101541.4
            r'^\d{13}[\.-X]\d+',  # 申请号变体
            r'.*专利.*',
            r'.*申请.*',
            r'.*审查意见.*',
            r'.*实用新型.*',
            r'.*发明.*',
            r'.*外观.*'
        ]

        for pattern in patent_patterns:
            if re.search(pattern, folder_name):
                return "02_专利管理"

        # 客户名称模式
        client_keywords = [
            "大学", "学院", "公司", "集团", "研究所", "研究院",
            "医院", "医科大学", "大学", "学院", "科技"
        ]

        for keyword in client_keywords:
            if keyword in folder_name:
                return "01_客户管理"

        # 审查意见模式
        review_keywords = [
            "审查意见", "审查", "答复", "驳回分析", "OA"
        ]

        for keyword in review_keywords:
            if keyword in folder_name:
                return "04_审查意见"

        # 个人姓名模式（律师客户）
        person_patterns = [
            r'^[^\d]+[0-9]*件$',  # "姓名3件"格式
            r'^[^\d]+实用新型\d*件',  # "姓名实用新型X件"格式
            r'^[^\d]+$'  # 只有姓名
        ]

        for pattern in person_patterns:
            if re.search(pattern, folder_name):
                return "01_客户管理"

        # 默认归入临时文件
        return self.temp_folder

    def organize_folder(self, source_path, dry_run=True):
        """整理单个文件夹"""
        if not source_path.exists():
            return False, "源路径不存在"

        if not source_path.is_dir():
            return False, "不是文件夹"

        folder_name = source_path.name

        # 跳过已组织的文件夹（以数字开头的分类文件夹）
        if folder_name.startswith(("01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_", "09_", "10_")):
            return True, "已跳过（已整理）"

        # 跳过系统文件
        if folder_name.startswith((".", "整理日志")):
            return True, "已跳过（系统文件）"

        # 分类目标
        target_folder_name = self.classify_folder(folder_name)
        target_folder_path = self.work_folder / target_folder_name
        target_path = target_folder_path / folder_name

        # 检查是否已经在正确位置
        current_parent = source_path.parent.name
        if current_parent == target_folder_name:
            return True, "已跳过（已在正确位置）"

        # 检查目标路径是否已存在
        if target_path.exists():
            target_path = target_folder_path / f"{folder_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        action = "将要移动" if dry_run else "移动"

        print(f"{action}: {folder_name} -> {target_folder_name}/{target_path.name}")

        if not dry_run:
            try:
                # 移动文件夹
                shutil.move(str(source_path), str(target_path))

                # 记录移动信息
                self.log_move(folder_name, str(source_path), str(target_path), target_folder_name)

                return True, "整理成功"
            except Exception as e:
                return False, f"移动失败: {str(e)}"

        return True, "预览成功"

    def log_move(self, folder_name, source_path, target_path, category):
        """记录整理日志"""
        log_file = self.work_folder / "整理日志.json"

        log_entry = {
            "folder_name": folder_name,
            "source_path": source_path,
            "target_path": target_path,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }

        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []

        logs.append(log_entry)

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def organize_all(self, dry_run=True):
        """整理所有文件夹"""
        print(f"{'预览' if dry_run else '开始'}整理工作文件夹...")
        print("=" * 60)

        # 获取所有子文件夹
        folders = [f for f in self.work_folder.iterdir() if f.is_dir()]

        # 排除系统文件夹
        exclude_folders = [
            ".DS_Store", "整理日志.json", ".git"
        ]

        organized_count = 0
        skipped_count = 0
        error_count = 0

        for folder in folders:
            if folder.name in exclude_folders:
                continue

            success, message = self.organize_folder(folder, dry_run)

            if success:
                if "跳过" in message:
                    skipped_count += 1
                else:
                    organized_count += 1
            else:
                error_count += 1
                print(f"❌ 错误: {folder.name} - {message}")

        print("=" * 60)
        print(f"整理{'预览' if dry_run else '完成'}:")
        print(f"  组织文件夹: {organized_count}")
        print(f"  跳过文件夹: {skipped_count}")
        print(f"  错误数量: {error_count}")

        if dry_run:
            print("\n要执行整理，请使用 --execute 参数")

    def show_classification_preview(self):
        """显示分类预览"""
        print("文件夹分类预览:")
        print("=" * 60)

        folders = [f for f in self.work_folder.iterdir() if f.is_dir()]
        exclude_folders = [".DS_Store", "整理日志.json", ".git"]

        classification = {}

        for folder in folders:
            if folder.name in exclude_folders:
                continue

            # 跳过已整理的文件夹
            if folder.name.startswith(("01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_", "09_", "10_")):
                continue

            category = self.classify_folder(folder.name)
            if category not in classification:
                classification[category] = []
            classification[category].append(folder.name)

        if not classification:
            print("\n✅ 所有文件夹已经整理完毕！")
            return

        for category, folders_list in classification.items():
            print(f"\n📁 {category} ({len(folders_list)}个文件夹待整理):")
            for folder in sorted(folders_list):
                print(f"  - {folder}")

    def archive_old_files(self, days_old=365):
        """归档旧文件"""
        archive_path = self.work_folder / self.archive_folder
        archive_path.mkdir(exist_ok=True)

        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 3600)

        for folder in self.work_folder.iterdir():
            if not folder.is_dir() or folder.name.startswith("10_"):
                continue

            try:
                folder_mtime = folder.stat().st_mtime
                if folder_mtime < cutoff_date:
                    # 归档旧文件夹
                    target = archive_path / folder.name
                    if target.exists():
                        target = archive_path / f"{folder.name}_{datetime.now().strftime('%Y%m%d')}"

                    print(f"归档: {folder.name}")
                    shutil.move(str(folder), str(target))
            except Exception as e:
                print(f"归档失败 {folder.name}: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="工作文件夹整理工具")
    parser.add_argument("--execute", action="store_true", help="执行整理（不预览）")
    parser.add_argument("--preview", action="store_true", help="显示分类预览")
    parser.add_argument("--archive", type=int, help="归档指定天数前的文件")

    args = parser.parse_args()

    organizer = WorkFolderOrganizer()

    if args.preview:
        organizer.show_classification_preview()
    elif args.archive:
        print(f"归档 {args.archive} 天前的文件...")
        organizer.archive_old_files(args.archive)
    else:
        organizer.organize_all(dry_run=not args.execute)


if __name__ == "__main__":
    main()