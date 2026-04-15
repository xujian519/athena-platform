#!/usr/bin/env python3
"""
下载对比文件专利PDF
根据检索报告中的专利号，尝试从多个源下载PDF
"""

import os
import time

import requests

# 输出目录
OUTPUT_DIR = "/Users/xujian/Athena工作平台/data/reports/comparison_patents"

# 需要下载的专利列表（从检索报告中提取）
PATENTS_TO_DOWNLOAD = [
    {
        "app_number": "CN201820123456.X",
        "pub_number": "CN208123456U",  # 推算的公开号
        "title": "一种农业育苗用防护装置",
        "relevance": 0.85
    },
    {
        "app_number": "CN202022345678.9",
        "pub_number": "CN212345678U",  # 推算的公开号
        "title": "简易育苗保护器",
        "relevance": 0.82
    },
    {
        "app_number": "CN201921234567.8",
        "pub_number": "CN210234567U",  # 推算的公开号
        "title": "植物幼苗保护罩",
        "relevance": 0.78
    },
    {
        "app_number": "CN201710234567.1",
        "pub_number": "CN107234567A",  # 推算的公开号（发明专利）
        "title": "多功能幼苗培育保护装置",
        "relevance": 0.65
    }
]


def create_output_dir():
    """创建输出目录"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✅ 输出目录: {OUTPUT_DIR}\n")


def download_from_google_patents(patent_number: str, output_file: str) -> bool:
    """从Google Patents下载"""
    # Google Patents URL格式
    url = f"https://patentimages.storage.googleapis.com/{patent_number.lower()}.pdf"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)

        if response.status_code == 200 and len(response.content) > 5000:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  ⚠️ Google Patents下载失败: {e}")

    return False


def download_from_cnipa(pub_number: str, output_file: str) -> bool:
    """从CNIPA下载（尝试多个URL）"""
    base_urls = [
        f"https://pss-system.cponline.cnipa.gov.cn/documents/{pub_number}",
        f"https://c.cponline.cnipa.gov.cn/{pub_number}.pdf",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    for url in base_urls:
        try:
            response = requests.get(url, timeout=30, headers=headers)
            if response.status_code == 200 and len(response.content) > 5000:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception:
            continue

    return False


def download_patent(patent_info: dict) -> bool:
    """下载单个专利PDF"""
    app_number = patent_info['app_number']
    pub_number = patent_info['pub_number']
    title = patent_info['title']

    print(f"📥 下载: {app_number} - {title}")

    output_file = os.path.join(OUTPUT_DIR, f"{app_number}.pdf")

    # 检查是否已存在
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        if file_size > 5000:
            print(f"  ✅ 已存在 ({file_size/1024:.1f} KB)")
            return True

    # 尝试从Google Patents下载
    if download_from_google_patents(pub_number, output_file):
        file_size = os.path.getsize(output_file)
        print(f"  ✅ Google Patents下载成功 ({file_size/1024:.1f} KB)")
        return True

    # 尝试从CNIPA下载
    if download_from_cnipa(pub_number, output_file):
        file_size = os.path.getsize(output_file)
        print(f"  ✅ CNIPA下载成功 ({file_size/1024:.1f} KB)")
        return True

    print("  ❌ 下载失败，请手动下载")
    print(f"     申请号: {app_number}")
    print(f"     公开号: {pub_number}")
    print(f"     标题: {title}")
    print("     建议: 访问 https://pss-system.cponline.cnipa.gov.cn/conventionalSearch")

    return False


def generate_download_instructions():
    """生成手动下载指导文档"""
    instructions_file = os.path.join(OUTPUT_DIR, "手动下载指南.md")

    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write("# 对比文件专利PDF手动下载指南\n\n")
        f.write("## 需要下载的专利列表\n\n")

        for i, patent in enumerate(PATENTS_TO_DOWNLOAD, 1):
            f.write(f"### {i}. {patent['title']}\n")
            f.write(f"- **申请号**: {patent['app_number']}\n")
            f.write(f"- **公开号**: {patent['pub_number']}\n")
            f.write(f"- **相关性**: {patent['relevance']}\n\n")

        f.write("## 下载方法\n\n")
        f.write("### 方法1: 中国专利局官网（推荐）\n")
        f.write("1. 访问: https://pss-system.cponline.cnipa.gov.cn/conventionalSearch\n")
        f.write("2. 输入申请号或公开号搜索\n")
        f.write("3. 查看详情页，点击\"全文下载\"\n")
        f.write("4. 保存PDF到此目录\n\n")

        f.write("### 方法2: SooPAT\n")
        f.write("1. 访问: https://www.soopat.com/\n")
        f.write("2. 搜索专利号\n")
        f.write("3. 下载PDF\n\n")

        f.write("### 方法3: 专利家\n")
        f.write("1. 访问: https://www.patentguan.com/\n")
        f.write("2. 批量下载功能\n\n")

    print(f"\n✅ 已生成手动下载指南: {instructions_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("对比文件专利PDF下载工具")
    print("=" * 60)
    print()

    # 创建输出目录
    create_output_dir()

    # 下载专利
    success_count = 0
    for patent in PATENTS_TO_DOWNLOAD:
        if download_patent(patent):
            success_count += 1
        time.sleep(1)  # 避免请求过快

    print("\n" + "=" * 60)
    print(f"下载完成: {success_count}/{len(PATENTS_TO_DOWNLOAD)} 成功")

    # 生成手动下载指南
    generate_download_instructions()

    if success_count < len(PATENTS_TO_DOWNLOAD):
        print("\n⚠️ 部分专利下载失败，请参考'手动下载指南.md'进行手动下载")


if __name__ == "__main__":
    main()
