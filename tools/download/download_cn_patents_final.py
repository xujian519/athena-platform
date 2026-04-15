#!/usr/bin/env python3
"""
中国专利PDF下载 - 使用公开号直接下载
通过查询公开号后从CNIPA官方服务器下载PDF
"""

import os
import re
import time

import requests

# 输出目录
OUTPUT_DIR = "/Users/xujian/工作/01_客户管理/01_正式客户/山东大齐4件"

# 需要下载的专利（只获取PDF失败的）
REMAINING_PATENTS = [
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

# 申请号到公开号的映射（手动查询或推算）
APP_TO_PUB_MAP = {
    # 课题一：管壳式换热器
    "CN201320508689.X": "CN203688789U",  # 实用新型
    "CN201910818135.1": "CN110345669A",  # 发明专利
    "CN201921189625.1": "CN210718357U",
    "CN201821113286.4": "CN208419676U",
    "CN201310587576.8": "CN103422874A",

    # 课题二：多功能反应釜
    "CN201220722067.2": "CN202876586U",
    "CN201220731804.5": "CN202876796U",
    "CN201220587642.2": "CN202860891U",

    # 课题三：填料塔分离装置
    "CN201420099038.4": "CN204034558U",
    "CN201220709918.X": "CN202860534U",
    "CN201320846029.2": "CN203494278U",
    "CN201220300555.4": "CN202620930U",

    # 课题四：双层储罐
    "CN201720969758.5": "CN207455882U",
    "CN201320732384.7": "CN203495798U",
    "CN201921117397.7": "CN210219466U",
}

def get_pdf_url_from_pub_number(pub_number: str) -> str | None:
    """
    根据公开号构造CNIPA PDF下载URL
    """
    # CNIPA PDF URL格式
    # 例如：CN203688789U -> https://cnipa.gov.cn/CN203688789U.pdf
    # 但实际需要使用官方的CDN地址

    base_urls = [
        f"https://cnipa.gov.cn/{pub_number}.pdf",
        f"https://epub.cnipa.gov.cn/{pub_number}.pdf",
        f"https://c.cponline.cnipa.gov.cn/{pub_number}.pdf",
    ]

    return base_urls

def download_from_cnipa(pub_number: str, app_number: str, output_dir: str) -> bool:
    """从CNIPA官方下载PDF"""
    pdf_urls = get_pdf_url_from_pub_number(pub_number)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for url in pdf_urls:
        try:
            response = requests.get(url, timeout=30, headers=headers)

            if response.status_code == 200 and len(response.content) > 5000:
                output_file = os.path.join(output_dir, f"{app_number}.pdf")
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"  ✅ CNIPA: {app_number} -> {pub_number}")
                return True
        except Exception:
            continue

    return False

def download_from_patent_viewer(app_number: str, pub_number: str, output_dir: str) -> bool:
    """从专利查看器下载"""
    try:
        # 使用专利浏览器的PDF下载接口
        url = f"https://patents.google.com/patent/{pub_number}/zh"

        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            # 尝试找到PDF下载链接
            pdf_pattern = re.search(r'href="(/patent/[^"]*download[^"]*)"', response.text)
            if pdf_pattern:
                pdf_url = f"https://patents.google.com{pdf_pattern.group(1)}"
                pdf_response = requests.get(pdf_url, timeout=30)

                if pdf_response.status_code == 200 and len(pdf_response.content) > 5000:
                    output_file = os.path.join(output_dir, f"{app_number}.pdf")
                    with open(output_file, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"  ✅ 专利浏览器: {app_number} -> {pub_number}")
                    return True

        return False
    except Exception as e:
        print(f"  ⚠️ 专利浏览器失败: {str(e)[:30]}")
        return False

def download_from_wanfang(app_number: str, output_dir: str) -> bool:
    """从万方数据下载"""
    try:
        url = f"http://www.wanfangdata.com.cn/details/detail.do?_type=patent&id={app_number}"

        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            # 保存HTML
            output_file = os.path.join(output_dir, f"{app_number}_wanfang.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"  ✅ 万方数据 HTML: {app_number}")
            return True

        return False
    except Exception as e:
        print(f"  ⚠️ 万方数据失败: {str(e)[:30]}")
        return False

def query_pub_number_from_db(app_number: str) -> str | None:
    """从本地数据库查询公开号"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="patent_db",
            user="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()

        query = """
        SELECT publication_number, authorization_number
        FROM patents
        WHERE application_number = %s
        LIMIT 1;
        """

        cursor.execute(query, (app_number,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            # 优先使用授权公告号（实用新型）
            return result.get('authorization_number') or result.get('publication_number')

        return None
    except Exception as e:
        print(f"  ⚠️ 数据库查询失败: {str(e)[:30]}")
        return None

def download_patent(app_number: str, output_dir: str) -> dict:
    """尝试多个来源下载专利"""
    results = {
        'app_number': app_number,
        'success': False,
        'source': None,
        'pub_number': None
    }

    # 首先查询数据库获取公开号
    pub_number = query_pub_number_from_db(app_number)

    # 如果数据库没有，使用预定义映射
    if not pub_number and app_number in APP_TO_PUB_MAP:
        pub_number = APP_TO_PUB_MAP[app_number]

    if pub_number:
        results['pub_number'] = pub_number
        print(f"  🔍 公开号: {pub_number}")

        # 尝试使用公开号下载
        if download_from_cnipa(pub_number, app_number, output_dir):
            results['success'] = True
            results['source'] = "CNIPA官方"
            return results

        if download_from_patent_viewer(app_number, pub_number, output_dir):
            results['success'] = True
            results['source'] = "专利浏览器"
            return results

    # 最后尝试万方数据
    if download_from_wanfang(app_number, output_dir):
        results['success'] = True
        results['source'] = "万方数据"

    time.sleep(2)
    return results

def main():
    """主函数"""

    print("=" * 70)
    print("📥 中国专利PDF下载 - 公开号版本")
    print("=" * 70)
    print()

    pdf_dir = os.path.join(OUTPUT_DIR, "PDF原文")

    success_count = 0
    failed_count = 0
    failed_list = []
    sources = {}

    for app_num in REMAINING_PATENTS:
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
    print(f"总计: {len(REMAINING_PATENTS)} 条")
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
