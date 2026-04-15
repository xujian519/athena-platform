#!/usr/bin/env python3
"""
中国专利PDF下载 - 使用中国专利公布公告网
通过申请号获取公开号后下载PDF
"""

import os
import re
import time

import requests
from bs4 import BeautifulSoup

# 输出目录
OUTPUT_DIR = "/Users/xujian/工作/01_客户管理/01_正式客户/山东大齐4件"

# 需要下载HTML的专利（之前只下载了登录页）
HTML_PATENTS = [
    "CN201320508689.X",
    "CN201910818135.1",
    "CN201921189625.1",
    "CN201821113286.4",
    "CN201310587576.8",
    "CN201220722067.2",
    "CN201220731804.5",
    "CN201220587642.2",
    "CN201420099038.4",
    "CN201220709918.X",
    "CN201320846029.2",
    "CN201220300555.4",
    "CN201720969758.5",
    "CN201320732384.7",
    "CN201921117397.7",
]

def get_pub_number_from_app(app_number: str) -> str | None:
    """从申请号获取公开号"""
    try:
        # 使用万方专利查询API
        url = f"http://api.wanfangdata.com.cn/search/Search.svc?type=papers&condition={app_number}"
        requests.get(url, timeout=10)

        # 或者使用专利汇网站
        url2 = f"https://www.patentexpo.com/cn/{app_number}"
        response2 = requests.get(url2, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response2.status_code == 200:
            BeautifulSoup(response2.text, 'html.parser')
            # 尝试从页面提取公开号
            # 这里需要根据实际页面结构调整

        return None
    except Exception:
        return None

def download_from_pss(app_number: str, output_dir: str) -> bool:
    """从中国专利公布公告网下载"""
    try:
        # PSS系统URL

        # 搜索API
        search_api = "https://pss-system.cponline.cnipa.gov.cn/javascript/pss.search.js"

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://pss-system.cponline.cnipa.gov.cn/'
        })

        # 先访问首页获取cookies
        session.get("https://pss-system.cponline.cnipa.gov.cn/", timeout=10)

        # 搜索申请号
        search_data = {
            'searchCondition': app_number,
            'db': 'CN',
            'n': '1'
        }

        response = session.post(search_api, json=search_data, timeout=30)

        if response.status_code == 200:
            data = response.json()
            # 解析结果获取公开号和下载链接
            print(f"  🔍 PSS响应: {len(data)} bytes")

        return False
    except Exception as e:
        print(f"  ⚠️ PSS下载失败: {str(e)[:30]}")
        return False

def download_from_chemrxiv(app_number: str, output_dir: str) -> bool:
    """从chemrxiv（专利之星）下载"""
    try:
        # 专利之星URL
        url = f"http://www.patentstar.com.cn/Detail.aspx?pid={app_number}"

        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 查找PDF下载链接
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf'))

            for link in pdf_links:
                pdf_url = link.get('href')
                if pdf_url:
                    # 下载PDF
                    if not pdf_url.startswith('http'):
                        pdf_url = 'http://www.patentstar.com.cn' + pdf_url

                    pdf_response = requests.get(pdf_url, timeout=30)
                    if pdf_response.status_code == 200 and len(pdf_response.content) > 1000:
                        output_file = os.path.join(output_dir, f"{app_number}.pdf")
                        with open(output_file, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"  ✅ 专利之星: {app_number}")
                        return True

        return False
    except Exception as e:
        print(f"  ⚠️ 专利之星失败: {str(e)[:30]}")
        return False

def download_from_5ipath(app_number: str, output_dir: str) -> bool:
    """从5ipath（五维专利）下载"""
    try:
        url = f"https://www.5ipath.com/cn/{app_number}"

        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 查找PDF下载链接
            pdf_links = soup.find_all('a', string=re.compile(r'下载|PDF'))

            for link in pdf_links:
                pdf_url = link.get('href')
                if pdf_url:
                    pdf_response = requests.get(pdf_url, timeout=30)
                    if pdf_response.status_code == 200 and len(pdf_response.content) > 1000:
                        output_file = os.path.join(output_dir, f"{app_number}.pdf")
                        with open(output_file, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"  ✅ 5ipath: {app_number}")
                        return True

        return False
    except Exception as e:
        print(f"  ⚠️ 5ipath失败: {str(e)[:30]}")
        return False

def download_from_cpspark(app_number: str, output_dir: str) -> bool:
    """从CPSpark（专利火花）下载"""
    try:
        url = f"http://www.cpspark.com/patent/{app_number}"

        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            # 保存HTML
            output_file = os.path.join(output_dir, f"{app_number}_cpspark.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  ✅ CPSpark HTML: {app_number}")
            return True

        return False
    except Exception as e:
        print(f"  ⚠️ CPSpark失败: {str(e)[:30]}")
        return False

def download_patent(app_number: str, output_dir: str) -> dict:
    """尝试多个来源下载专利"""
    results = {
        'app_number': app_number,
        'success': False,
        'source': None
    }

    sources = [
        ("专利之星", download_from_chemrxiv),
        ("5ipath", download_from_5ipath),
        ("CPSpark", download_from_cpspark),
    ]

    for source_name, download_func in sources:
        if download_func(app_number, output_dir):
            results['success'] = True
            results['source'] = source_name
            break

        time.sleep(1)

    return results

def main():
    """主函数"""

    print("=" * 70)
    print("📥 中国专利PDF下载 - 替代数据源")
    print("=" * 70)
    print()

    pdf_dir = os.path.join(OUTPUT_DIR, "PDF原文")

    success_count = 0
    failed_count = 0
    failed_list = []
    sources = {}

    for app_num in HTML_PATENTS:
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
    print(f"总计: {len(HTML_PATENTS)} 条")
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

if __name__ == "__main__":
    main()
