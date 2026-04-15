#!/usr/bin/env python3
"""
山东大齐专利PDF批量下载脚本
使用Google Patents下载PDF格式专利原文
"""

import os
import sys
from pathlib import Path

# 添加MCP服务器路径
sys.path.insert(0, str(Path(__file__).parent / "mcp-servers" / "patent_downloader" / "src"))

import datetime
import logging

from patent_downloader.downloader import PatentDownloader
from patent_downloader.progress_logger import ProgressLogger

# 输出目录
OUTPUT_DIR = "/Users/xujian/工作/01_客户管理/01_正式客户/山东大齐4件"

# 所有检索到的专利申请号列表
PATENT_NUMBERS = [
    # 课题一：管壳式换热器
    "CN201320508689.X",
    "CN201910818135.1",
    "CN201921189625.1",
    "CN201821113286.4",
    "CN201310587576.8",

    # 课题二：多功能反应釜
    "CN201210575269.3",
    "CN201220722067.2",
    "CN201110242333.1",
    "CN201220731804.5",
    "CN201220587642.2",
    "CN201320220578.9",
    "CN202410882450.1",
    "CN202022616673.3",
    "CN201220431536.5",
    "CN200320103388.5",
    "CN02222944.2",

    # 课题三：填料塔分离装置
    "CN201420099038.4",
    "CN201220709918.X",
    "CN201320846029.2",
    "CN201210212171.1",
    "CN201220300555.4",
    "CN201920603698.4",
    "CN201410112590.7",
    "CN201320681068.1",

    # 课题四：双层储罐
    "CN201720969758.5",
    "CN201210356732.5",
    "CN201320732384.7",
    "CN201921117397.7",
    "CN201810202573.0",
    "CN202110159126.3",
    "CN201910779372.1",
    "CN201720186137.X",
    "CN202121543748.8",
    "CN202121782596.7",
]

def download_all_patents():
    """下载所有专利PDF"""

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    print("=" * 70)
    print("📥 山东大齐专利PDF下载")
    print("=" * 70)
    print()

    # 创建输出目录
    topic_dirs = {
        "topic1": os.path.join(OUTPUT_DIR, "课题一_管壳式换热器", "PDF"),
        "topic2": os.path.join(OUTPUT_DIR, "课题二_多功能反应釜", "PDF"),
        "topic3": os.path.join(OUTPUT_DIR, "课题三_填料塔分离装置", "PDF"),
        "topic4": os.path.join(OUTPUT_DIR, "课题四_双层储罐", "PDF"),
    }

    for dir_path in topic_dirs.values():
        os.makedirs(dir_path, exist_ok=True)

    # 按课题分组
    topic_patents = {
        "topic1": PATENT_NUMBERS[0:5],
        "topic2": PATENT_NUMBERS[5:17],
        "topic3": PATENT_NUMBERS[17:25],
        "topic4": PATENT_NUMBERS[25:37],
    }

    # 创建下载器
    progress_logger = ProgressLogger()
    downloader = PatentDownloader(timeout=30, max_retries=3, progress_logger=progress_logger)

    total_success = 0
    total_failed = 0
    failed_patents = []

    def progress_callback(completed, total, patent_number, success):
        """进度回调"""
        if success:
            print(f"  ✅ [{completed}/{total}] {patent_number}")
        else:
            print(f"  ❌ [{completed}/{total}] {patent_number} - 失败")

    # 按课题下载
    for topic, patent_list in topic_patents.items():
        print(f"📁 下载 {topic} ({len(patent_list)} 条专利)...")
        print("-" * 70)

        results = downloader.download_patents(
            patent_list,
            topic_dirs[topic],
            progress_callback=progress_callback
        )

        # 统计结果
        for patent_num, success in results.items():
            if success:
                total_success += 1
            else:
                total_failed += 1
                failed_patents.append(patent_num)

        print()

    # 打印汇总
    print("=" * 70)
    print("📊 下载完成汇总")
    print("=" * 70)
    print(f"总计: {len(PATENT_NUMBERS)} 条")
    print(f"成功: {total_success} 条")
    print(f"失败: {total_failed} 条")
    print()

    if failed_patents:
        print("失败的专利:")
        for patent in failed_patents:
            print(f"  - {patent}")

    # 生成下载报告
    report_file = os.path.join(OUTPUT_DIR, "PDF下载报告.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 山东大齐专利PDF下载报告\n\n")
        f.write(f"**下载时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 下载统计\n\n")
        f.write(f"- 总计: {len(PATENT_NUMBERS)} 条\n")
        f.write(f"- 成功: {total_success} 条\n")
        f.write(f"- 失败: {total_failed} 条\n\n")
        f.write("## PDF文件目录\n\n")
        f.write("```\n")
        f.write("山东大齐4件/\n")
        f.write("├── 课题一_管壳式换热器/PDF/\n")
        f.write("├── 课题二_多功能反应釜/PDF/\n")
        f.write("├── 课题三_填料塔分离装置/PDF/\n")
        f.write("├── 课题四_双层储罐/PDF/\n")
        f.write("└── PDF下载报告.md\n")
        f.write("```\n\n")

        if failed_patents:
            f.write("## 下载失败的专利\n\n")
            for patent in failed_patents:
                f.write(f"- {patent}\n")

    print(f"报告已保存: {report_file}")

if __name__ == "__main__":
    import datetime
    download_all_patents()
