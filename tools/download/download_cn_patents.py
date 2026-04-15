#!/usr/bin/env python3
"""
使用Jina AI Reader下载中国专利PDF
从中国专利公布公告网获取PDF
"""

import os
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

def cn_app_to_pub_number(app_number):
    """
    中国专利申请号转公开号规则
    例如: CN201320508689.X -> CN203688789U (实用新型)
    """
    # 去掉CN和最后的类型代码
    num_part = app_number.replace("CN", "").split(".")[0]

    # 判断专利类型
    if "201" in num_part or "202" in num_part or "203" in num_part:
        # 201x-203x年可能是发明专利
        year = num_part[:4]
        serial = num_part[4:9]
        # 发明专利公开号规则：CN + 年份(去掉20) + 序列号(5位) + B
        pub_num = f"CN{year[2:]}{serial}B"
    else:
        # 实用新型：CN + 年份(去掉20) + 序列号(5位) + U
        year = num_part[:4]
        serial = num_part[4:9]
        pub_num = f"CN{year[2:]}{serial}U"

    return pub_num

def get_prow_pdf_url(app_number):
    """
    获取中国专利网PDF下载链接
    使用prow.cn网站（第三方中国专利查询）
    """
    # 尝试多个PDF来源
    sources = [
        # 中国专利公布公告网
        f"https://pub.cnipa.gov.cn/{app_number}",
        # 百度专利
        f"https://zhuanli.baidu.com/patent/{app_number}",
        # 企查查专利
        f"https://www.qcc.com/patent/{app_number}",
    ]
    return sources

def download_from_jina_reader(app_number, output_dir):
    """
    使用Jina AI Reader获取专利内容并保存
    """
    # Prow网站URL (中国专利查询)
    prow_url = f"https://prow.cn/patent/{app_number}"

    # 使用Jina AI Reader获取内容
    jina_url = f"https://r.jina.ai/http:{prow_url}"

    try:
        print(f"  尝试下载 {app_number}...")
        response = requests.get(jina_url, timeout=30)
        response.raise_for_status()

        # 保存为markdown文件
        output_file = os.path.join(output_dir, f"{app_number}.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 专利: {app_number}\n\n")
            f.write(f"来源: {prow_url}\n\n")
            f.write("---\n\n")
            f.write(response.text)

        print(f"  ✅ {app_number} - 已保存")
        return True
    except Exception as e:
        print(f"  ❌ {app_number} - 失败: {str(e)[:50]}")
        return False

def main():
    """主函数"""

    print("=" * 70)
    print("📥 中国专利PDF/内容下载")
    print("=" * 70)
    print()

    # 创建输出目录
    pdf_dir = os.path.join(OUTPUT_DIR, "PDF原文")
    os.makedirs(pdf_dir, exist_ok=True)

    success_count = 0
    failed_count = 0
    failed_list = []

    for app_num in PATENT_NUMBERS:
        success = download_from_jina_reader(app_num, pdf_dir)
        if success:
            success_count += 1
        else:
            failed_count += 1
            failed_list.append(app_num)

        # 避免请求过快
        time.sleep(2)

    print()
    print("=" * 70)
    print("📊 下载汇总")
    print("=" * 70)
    print(f"总计: {len(PATENT_NUMBERS)} 条")
    print(f"成功: {success_count} 条")
    print(f"失败: {failed_count} 条")
    print()
    print(f"保存目录: {pdf_dir}")

    if failed_list:
        print("\n失败的专利:")
        for num in failed_list:
            print(f"  - {num}")

if __name__ == "__main__":
    main()
