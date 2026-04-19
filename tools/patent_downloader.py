#!/usr/bin/env python3
"""
专利PDF批量下载脚本
支持从多个来源下载中国专利PDF文件
"""

import os
import subprocess
import time
from pathlib import Path


class PatentDownloader:
    """专利PDF下载器"""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.download_log = []
        self.fail_log = []

    def load_patent_list(self, list_file):
        """加载专利号列表"""
        patents = []
        with open(list_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line.startswith('#') or not line or line.startswith('CN'):
                    continue
                # 提取专利号
                patent_num = line.split()[0] if ' ' in line else line
                if patent_num and len(patent_num) >= 10:
                    patents.append(patent_num)
        return patents

    def download_from_google_patents(self, patent_num):
        """从Google Patents下载"""
        # Google Patents下载URL格式
        pdf_url = f"https://patentimages.storage.googleapis.com/58/{patent_num}/CN{patent_num}.pdf"
        output_file = self.output_dir / f"{patent_num}.pdf"

        # 使用wget下载
        try:
            result = subprocess.run([
                'wget', '-O', str(output_file), pdf_url,
                '--timeout=30',
                '--tries=3'
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and output_file.exists():
                file_size = output_file.stat().st_size
                if file_size > 1000:  # 文件大小大于1KB认为有效
                    self.download_log.append(f"{patent_num}: 成功下载 ({file_size} bytes)")
                    return True
                else:
                    output_file.unlink()
                    self.fail_log.append(f"{patent_num}: 文件太小 ({file_size} bytes)")
                    return False
            else:
                self.fail_log.append(f"{patent_num}: 下载失败")
                return False
        except Exception as e:
            self.fail_log.append(f"{patent_num}: 异常 - {str(e)}")
            return False

    def download_from_cnipa(self, patent_num):
        """从中国专利局下载"""
        # CNIPA下载需要使用专业工具或API
        # 这里提供下载接口地址
        return False

    def download_from_sooPAT(self, patent_num):
        """从SooPAT下载"""
        # SooPAT需要登录，这里提供下载链接格式
        return False

    def download_batch(self, patent_list, method='google'):
        """批量下载专利"""
        total = len(patent_list)
        print(f"开始下载 {total} 个专利...")
        print(f"目标目录: {self.output_dir}")
        print(f"下载方式: {method}")
        print("-" * 60)

        for i, patent_num in enumerate(patent_list, 1):
            print(f"\r[{i}/{total}] {patent_num}...", end='', flush=True)

            if method == 'google':
                success = self.download_from_google_patents(patent_num)
            elif method == 'cnipa':
                success = self.download_from_cnipa(patent_num)
            elif method == 'soopat':
                success = self.download_from_sooPAT(patent_num)
            else:
                success = False

            if success:
                print(f"\r[{i}/{total}] {patent_num}: ✓ 成功")
            else:
                print(f"\r[{i}/{total}] {patent_num}: ✗ 失败")

            # 避免请求过于频繁
            time.sleep(1)

        print("\n" + "=" * 60)
        print("下载完成！")
        print(f"成功: {len(self.download_log)}")
        print(f"失败: {len(self.fail_log)}")

        # 保存日志
        log_file = self.output_dir / "download_log.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== 成功下载 ===\n")
            for log in self.download_log:
                f.write(log + "\n")
            f.write("\n=== 下载失败 ===\n")
            for log in self.fail_log:
                f.write(log + "\n")

        print(f"日志已保存到: {log_file}")

    def generate_download_commands(self, patent_list):
        """生成下载命令供用户执行"""
        cmd_file = self.output_dir / "download_commands.sh"

        with open(cmd_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# 专利PDF批量下载命令\n")
            f.write("# 使用方法: bash download_commands.sh\n")
            f.write("\n")

            for patent_num in patent_list:
                # Google Patents下载命令
                pdf_url = f"https://patentimages.storage.googleapis.com/58/{patent_num}/CN{patent_num}.pdf"
                f.write(f"wget -O \"{patent_num}.pdf\" \"{pdf_url}\"\n")

        # 添加执行权限
        os.chmod(cmd_file, 0o755)

        print(f"已生成下载命令脚本: {cmd_file}")
        print(f"使用方法: bash {cmd_file}")

def main():
    # 配置路径
    list_file = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/下载专利PDF/未下载专利号列表_20260202_180357.txt"
    output_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/下载专利PDF"

    # 创建下载器
    downloader = PatentDownloader(output_dir)

    # 加载专利列表
    patents = downloader.load_patent_list(list_file)
    print(f"读取到 {len(patents)} 个专利号")

    # 批量下载
    downloader.download_batch(patents, method='google')

    # 生成备用下载命令
    print("\n" + "=" * 60)
    print("生成备用下载命令...")
    downloader.generate_download_commands(patents)

if __name__ == "__main__":
    main()
