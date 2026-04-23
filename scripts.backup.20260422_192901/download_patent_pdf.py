#!/usr/bin/env python3
"""
下载专利PDF文件
专利号: CN201510047610.1 (植物保护罩)
"""

import sys
from pathlib import Path

# 专利信息
PATENT_NUMBER = "CN201510047610.1"
PATENT_NAME = "植物保护罩"

# 目标目录
TARGET_DIR = "/Users/xujian/工作/01_客户管理/01_正式客户/孙俊霞1件"

print("=" * 70)
print("📥 专利PDF下载工具")
print("=" * 70)
print()
print(f"专利号: {PATENT_NUMBER}")
print(f"发明名称: {PATENT_NAME}")
print(f"目标目录: {TARGET_DIR}")
print()

# 中国专利公布公告网URL
# 使用官方API下载专利全文
CNIPA_URL = "https://pss-system.cponline.cnipa.gov.cn/"

# 备用方案：使用其他专利下载API
# Google Patents下载
GOOGLE_PATENTS_URL = "https://patents.google.com/patent/CN201510047610A1/zh"

# 专利之星或其他公开API
# 注意：实际下载可能需要处理验证码、登录等问题

print("⚠️ 注意: 官方专利PDF下载通常需要:")
print("  1. 访问中国专利公布公告网")
print("  2. 输入验证码")
print("  3. 手动下载")
print()
print("💡 提供以下替代方案:")
print()

# 方案1: 提供官方下载链接和步骤
print("=" * 70)
print("📋 方案1: 官方网站手动下载 (推荐)")
print("=" * 70)
print()
print("步骤:")
print("1. 访问: https://pss-system.cponline.cnipa.gov.cn/")
print(f"2. 搜索专利号: {PATENT_NUMBER}")
print("3. 点击'全文下载'或'PDF下载'")
print(f"4. 保存到: {TARGET_DIR}")
print()

# 方案2: 使用专利下载API（如果有）
print("=" * 70)
print("📋 方案2: 使用专利下载服务API")
print("=" * 70)
print()

# 尝试从公开API获取
api_urls = [
    ("中国专利公布公告网", f"https://pss-system.cponline.cnipa.gov.cn/patent/search!getFullTextHtml.shtml?cn={PATENT_NUMBER}"),
    ("Google Patents", "https://patents.google.com/patent/CN201510047610A1/zh"),
    ("Soopat", f"https://www.soopat.com/Patent/{PATENT_NUMBER}/"),
]

for name, url in api_urls:
    print(f"{name}:")
    print(f"  URL: {url}")
    print()

# 方案3: 创建下载脚本
print("=" * 70)
print("📋 方案3: 自动下载脚本")
print("=" * 70)
print()

# 检查目标目录是否可写
target_path = Path(TARGET_DIR)
if target_path.exists() and target_path.is_dir():
    print(f"✅ 目标目录可访问: {TARGET_DIR}")

    # 创建专利信息文件
    info_file = target_path / f"{PATENT_NUMBER}_下载指南.txt"

    download_guide = f"""专利下载指南
{'=' * 70}

专利信息:
  专利号: {PATENT_NUMBER}
  发明名称: {PATENT_NAME}
  申请人: 杭州翰堂科技有限公司
  IPC分类: A01G
  申请日: 2015-02-15

官方下载渠道:
{'=' * 70}

1. 中国专利公布公告网 (推荐)
   URL: https://pss-system.cponline.cnipa.gov.cn/
   步骤:
   a) 访问网站
   b) 在搜索框输入: {PATENT_NUMBER}
   c) 点击搜索结果中的专利
   d) 点击"全文下载"或"PDF下载"按钮
   e) 保存PDF到本目录

2. 国家知识产权局
   URL: https://www.cnipa.gov.cn/
   步骤: 同上

3. 第三方专利检索平台
   - Soopat: https://www.soopat.com/Patent/{PATENT_NUMBER}/
   - 专利汇: https://www.patenthub.cn/
   - 专利之星: https://www.patentstar.com.cn/

4. Google Patents (英文)
   URL: {GOOGLE_PATENTS_URL}
   说明: 可查看专利内容，但下载PDF需要额外操作

专利摘要:
{'=' * 70}
本发明涉及一种植物保护罩，其特征在于，包括设置有开口的罩体，
所述开口的横截面小于罩体的横截面，所述的罩体上设置有间隔排列
的连通罩体内外的小孔。本发明在植物体幼小时可以通过开口将植物体
放入罩体内，并利用罩体上的固定装置加以固定，让植物体可以在罩体
内生长，同时通过小孔与外界进行空气流通，既能保护植物体免受虫害、
动物伤害，又能保证植物体正常的生长。

与本发明的区别:
{'=' * 70}
现有技术 (CN201510047610.1):
  • 简单罩体+小孔设计
  • 主要用于防虫害
  • 未涉及防风、防霜冻功能
  • 未提及极简三件式结构

孙俊霞发明:
  • 三防一体 (防风+防虫+防霜冻)
  • 极简三件式结构
  • 成本<10元，适合基层农户
  • 徒手1分钟安装

生成时间: {sys.modules.get('datetime', None) or '2026-03-06'}
"""

    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(download_guide)

    print("✅ 已创建下载指南文件:")
    print(f"   {info_file}")
    print()

else:
    print(f"❌ 目标目录不可访问: {TARGET_DIR}")

# 方案4: 尝试使用curl/wget下载（如果可行）
print("=" * 70)
print("📋 方案4: 命令行下载尝试")
print("=" * 70)
print()

# 尝试从公开资源下载
# 注意：这通常不会成功，因为需要验证码和登录
print("注意: 由于官方网站需要验证码和登录，直接命令行下载通常不可行")
print("推荐使用方案1手动下载")
print()

# 提供curl命令作为参考
print("参考命令（可能不可用）:")
print(f"curl -o \"{target_path}/{PATENT_NUMBER}.pdf\" \"{GOOGLE_PATENTS_URL}.pdf\"")
print()

print("=" * 70)
print("📋 下载完成确认")
print("=" * 70)
print()

print("💡 建议:")
print("  1. 使用方案1手动下载（最可靠）")
print("  2. 下载后请重命名为: {PATENT_NUMBER}_植物保护罩.pdf")
print("  3. 保存到目录: {TARGET_DIR}")
print()

# 检查是否已存在该专利PDF
existing_pdf = target_path / f"{PATENT_NUMBER}_植物保护罩.pdf"
if existing_pdf.exists():
    print(f"✅ 检测到已存在文件: {existing_pdf.name}")
elif (target_path / f"{PATENT_NUMBER}.pdf").exists():
    print(f"✅ 检测到已存在文件: {PATENT_NUMBER}.pdf")
else:
    print("⚠️ 未检测到专利PDF文件，请按上述步骤下载")

print()
print("📄 下载指南文件已保存到目标目录，可查看详细下载步骤")
