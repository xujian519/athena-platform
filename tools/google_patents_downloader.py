#!/usr/bin/env python3
"""
Google Patents PDF Downloader
基于Google Patents公开接口下载专利PDF
支持单个和批量下载
"""

import requests
import argparse
import sys
import time
from urllib.parse import quote

def download_patent_pdf(patent_number, output_path=None, verbose=True):
    """
    下载Google Patents上的专利PDF

    Args:
        patent_number: 专利号 (如 "US20230012345", "CN112345678A")
        output_path: 输出文件路径 (可选)
        verbose: 是否显示详细输出

    Returns:
        保存的文件路径，失败返回None
    """
    # 构建Google Patents URL
    base_url = "https://patents.google.com/patent"
    url = f"{base_url}/{quote(patent_number)}/en?oq={quote(patent_number)}"

    if verbose:
        print(f"🔍 查找专利: {patent_number}")
        print(f"📋 URL: {url}")

    try:
        # 访问专利页面
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }, timeout=30)

        response.raise_for_status()
        html = response.text

        # 查找PDF下载链接
        import re

        # 模式1: 查找Google Patents的PDF链接
        # 通常格式: https://patentimages.storage.googleapis.com/xxx/xxx.pdf
        pdf_pattern = r'href="([^"]+\.pdf[^"]*)"'
        pdf_links = re.findall(pdf_pattern, html)

        if pdf_links:
            # 找到第一个PDF链接
            pdf_url = pdf_links[0]

            # 修复相对路径
            if not pdf_url.startswith('http'):
                pdf_url = f"https://patents.google.com{pdf_url}"

            if verbose:
                print(f"📄 找到PDF链接: {pdf_url}")

            # 下载PDF
            pdf_response = requests.get(pdf_url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }, timeout=60)

            pdf_response.raise_for_status()

            # 保存文件
            if not output_path:
                # 清理专利号作为文件名
                clean_number = patent_number.replace('/', '-').replace('\\', '-').replace(':', '-')
                output_path = f"/Users/xujian/Documents/patents/{clean_number}.pdf"

            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(pdf_response.content)

            if verbose:
                print(f"✅ PDF已保存到: {output_path}")

            return output_path

        else:
            if verbose:
                print(f"❌ 未找到PDF下载链接")
                print("提示: 可能是专利号格式不正确，或者该专利没有PDF版本")
            return None

    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"❌ 下载失败: {e}")
        return None

def batch_download(patent_numbers, output_dir=None, delay=1.0):
    """
    批量下载专利PDF

    Args:
        patent_numbers: 专利号列表 (支持文件或命令行参数)
        output_dir: 输出目录 (默认: workspace/patents)
        delay: 每次下载之间的延迟（秒）

    Returns:
        (成功数量, 失败数量)
    """
    # 确定输出目录
    import os
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = "/Users/xujian/Documents/patents"

    # 处理专利号列表
    # 如果是文件路径，读取文件
    if len(patent_numbers) == 1 and patent_numbers[0].endswith('.txt'):
        with open(patent_numbers[0], 'r') as f:
            patent_numbers = [line.strip() for line in f if line.strip()]

    # 过滤空行和注释
    patent_numbers = [p for p in patent_numbers if p and not p.startswith('#')]

    if not patent_numbers:
        print("❌ 没有找到专利号")
        return (0, 0)

    print(f"📦 批量下载 {len(patent_numbers)} 个专利")
    print(f"📁 输出目录: {output_dir}")
    print(f"⏱️  下载延迟: {delay} 秒")
    print("-" * 60)

    success_count = 0
    failed_count = 0
    failed_patents = []

    for i, patent_number in enumerate(patent_numbers, 1):
        print(f"\n[{i}/{len(patent_numbers)}] 下载: {patent_number}")

        # 清理专利号作为文件名
        clean_number = patent_number.replace('/', '-').replace('\\', '-').replace(':', '-')
        output_path = f"{output_dir}/{clean_number}.pdf"

        # 下载
        result = download_patent_pdf(patent_number, output_path, verbose=False)

        if result:
            success_count += 1
            print(f"  ✅ 成功: {result}")
        else:
            failed_count += 1
            failed_patents.append(patent_number)
            print(f"  ❌ 失败")

        # 延迟，避免被封
        if i < len(patent_numbers) and delay > 0:
            time.sleep(delay)

    # 汇总
    print("\n" + "=" * 60)
    print(f"📊 下载完成！")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ❌ 失败: {failed_count}")

    if failed_patents:
        print(f"\n失败的专利号:")
        for p in failed_patents:
            print(f"  - {p}")

    return (success_count, failed_count)

def search_patent(query):
    """
    在Google Patents上搜索专利

    Args:
        query: 搜索关键词
    """
    search_url = f"https://patents.google.com/?q={quote(query)}"
    print(f"🔍 搜索专利: {query}")
    print(f"📋 搜索URL: {search_url}")
    print("提示: 请在浏览器中打开上述链接查看搜索结果")

def main():
    parser = argparse.ArgumentParser(
        description='Google Patents PDF下载器 - 支持单个和批量下载',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个下载
  python3 %(prog)s US9876543B2

  # 批量下载
  python3 %(prog)s US9876543B2 US11234567A1 CN12345678A

  # 从文件批量下载
  python3 %(prog)s patents.txt

  # 指定输出目录
  python3 %(prog)s US9876543B2 -o ./my_patents/

  # 批量下载，每次间隔2秒
  python3 %(prog)s patents.txt -d 2

  # 搜索专利
  python3 %(prog)s -s "artificial intelligence"
        """
    )

    parser.add_argument('patents', nargs='*', help='专利号列表 (如: US20230012345 CN112345678A)')
    parser.add_argument('-o', '--output', help='输出目录路径')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='批量下载时的延迟时间（秒，默认1.0）')
    parser.add_argument('-s', '--search', help='搜索专利关键词')
    parser.add_argument('-l', '--list', help='列出常用专利号格式示例', action='store_true')

    args = parser.parse_args()

    if args.list:
        print("常用专利号格式示例:")
        print("  美国专利申请: US20230012345A1")
        print("  美国授权专利: US9876543B2")
        print("  中国专利: CN112345678A")
        print("  欧洲专利: EP1234567B1")
        print("  PCT专利: WO2023001234A1")
        print("  日本专利: JP2023001234A")
        return

    if args.search:
        search_patent(args.search)
        return

    if not args.patents:
        print("❌ 错误: 请提供专利号")
        print("使用 -l 查看专利号格式示例")
        print("使用 -s 搜索专利")
        parser.print_help()
        sys.exit(1)

    # 判断是单个还是批量下载
    if len(args.patents) == 1 and not args.patents[0].endswith('.txt'):
        # 单个下载
        output_path = None
        if args.output:
            clean_number = args.patents[0].replace('/', '-').replace('\\', '-').replace(':', '-')
            import os
            os.makedirs(args.output, exist_ok=True)
            output_path = f"{args.output}/{clean_number}.pdf"

        download_patent_pdf(args.patents[0], output_path)
    else:
        # 批量下载
        batch_download(args.patents, args.output, args.delay)

if __name__ == '__main__':
    main()
