#!/usr/bin/env python3
"""
中国专利PDF下载脚本 - 使用多个数据源
支持申请号和公开号自动转换
"""

import os
import re
import time

import requests

# 输出目录
OUTPUT_DIR = "/Users/xujian/工作/01_客户管理/01_正式客户/山东大齐4件"

# 专利申请号列表
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

    # 课题三：填料塔分离装置
    "CN201420099038.4",
    "CN201220709918.X",
    "CN201320846029.2",
    "CN201210212171.1",
    "CN201220300555.4",

    # 课题四：双层储罐
    "CN201720969758.5",
    "CN201210356732.5",
    "CN201320732384.7",
    "CN201921117397.7",
]

def app_to_pub_number(app_number: str) -> str | None:
    """
    申请号转公开号（中国实用新型）
    注意：这是估算，实际公开号需要查询
    """
    # 解析申请号
    match = re.match(r'CN(\d{4})(\d)(\d+)\.\d+', app_number)
    if not match:
        return None

    year = match.group(1)  # 2013
    type_code = match.group(2)  # 8=实用新型, 1=发明
    serial = match.group(3)  # 序列号

    # 实用新型公开号规则：CN + (年份-2000) + 序列号 + U
    if type_code in ['2', '3', '8', '9']:
        pub_num = f"CN{int(year)-2000}{serial}U"
    else:
        # 发明专利公开号规则
        pub_num = f"CN{int(year)-2000}{serial}A"

    return pub_num

def download_from_google_patents(app_number: str, output_dir: str) -> bool:
    """从Google Patents下载PDF"""
    try:
        # Google Patents支持申请号
        pdf_url = f"https://patents.google.com/patent/{app_number}/zh?oq={app_number}"

        response = requests.get(pdf_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            # 尝试获取PDF链接
            pdf_link = f"https://patents.google.com/patent/{app_number}/zh/download"
            pdf_response = requests.get(pdf_link, timeout=30)

            if pdf_response.status_code == 200 and len(pdf_response.content) > 1000:
                output_file = os.path.join(output_dir, f"{app_number}.pdf")
                with open(output_file, 'wb') as f:
                    f.write(pdf_response.content)
                print(f"  ✅ Google Patents: {app_number}")
                return True

        return False
    except Exception as e:
        print(f"  ⚠️ Google Patents 失败: {str(e)[:30]}")
        return False

def download_from_soopat(app_number: str, output_dir: str) -> bool:
    """从Soopat下载"""
    try:
        url = f"https://www.soopat.com/Patent/{app_number}"
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            # Soopat可能需要解析页面获取PDF链接
            # 这里简化处理，保存HTML
            output_file = os.path.join(output_dir, f"{app_number}_soopat.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  ✅ Soopat HTML: {app_number}")
            return True

        return False
    except Exception as e:
        print(f"  ⚠️ Soopat 失败: {str(e)[:30]}")
        return False

def download_from_xjishu(app_number: str, output_dir: str) -> bool:
    """从XJishu（技象网）下载"""
    try:
        url = f"https://www.xjishu.com/patent/{app_number}.html"
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            output_file = os.path.join(output_dir, f"{app_number}_xjishu.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  ✅ XJishu HTML: {app_number}")
            return True

        return False
    except Exception as e:
        print(f"  ⚠️ XJishu 失败: {str(e)[:30]}")
        return False

def download_from_patents_googlen_cn(app_number: str, output_dir: str) -> bool:
    """从Google Patents中国版下载"""
    try:
        # 尝试使用公开号
        pub_number = app_to_pub_number(app_number)
        if not pub_number:
            return False

        pdf_url = f"https://patents.google.com/patent/{pub_number}/zh/download"

        response = requests.get(pdf_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200 and len(response.content) > 1000:
            output_file = os.path.join(output_dir, f"{app_number}.pdf")
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"  ✅ Google Patents (公开号): {app_number} -> {pub_number}")
            return True

        return False
    except Exception as e:
        print(f"  ⚠️ Google CN 失败: {str(e)[:30]}")
        return False

def download_patent(app_number: str, output_dir: str) -> dict:
    """尝试多个来源下载专利"""
    results = {
        'app_number': app_number,
        'success': False,
        'source': None,
        'files': []
    }

    # 尝试多个来源
    sources = [
        ("Google Patents", download_from_google_patents),
        ("Google Patents CN", download_from_patents_googlen_cn),
        ("Soopat", download_from_soopat),
        ("XJishu", download_from_xjishu),
    ]

    for source_name, download_func in sources:
        if download_func(app_number, output_dir):
            results['success'] = True
            results['source'] = source_name
            break

        # 避免请求过快
        time.sleep(1)

    return results

def main():
    """主函数"""

    print("=" * 70)
    print("📥 中国专利PDF下载 - 多数据源版本")
    print("=" * 70)
    print()

    # 创建输出目录
    pdf_dir = os.path.join(OUTPUT_DIR, "PDF原文")
    os.makedirs(pdf_dir, exist_ok=True)

    success_count = 0
    failed_count = 0
    failed_list = []
    sources = {}

    for app_num in PATENT_NUMBERS:
        print(f"🔍 处理: {app_num}")
        result = download_patent(app_num, pdf_dir)

        if result['success']:
            success_count += 1
            source = result['source']
            sources[source] = sources.get(source, 0) + 1
        else:
            failed_count += 1
            failed_list.append(app_num)
            print("  ❌ 所有来源均失败")

        print()

    print("=" * 70)
    print("📊 下载汇总")
    print("=" * 70)
    print(f"总计: {len(PATENT_NUMBERS)} 条")
    print(f"成功: {success_count} 条")
    print(f"失败: {failed_count} 条")
    print()

    if sources:
        print("数据源统计:")
        for source, count in sources.items():
            print(f"  - {source}: {count} 条")
        print()

    if failed_list:
        print("失败的专利:")
        for num in failed_list:
            print(f"  - {num}")

    print(f"\n保存目录: {pdf_dir}")

if __name__ == "__main__":
    main()
