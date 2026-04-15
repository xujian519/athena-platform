#!/usr/bin/env python3
"""
专利缴费凭证图片关联助手
Patent Fee Payment Image Association Helper

使用方法:
1. 将缴费截图手动复制到 data/images/ 目录
2. 运行此脚本进行自动关联

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.patent_fee_association_manager import PatentFeeAssociationManager


def main():
    """主函数"""
    print("=" * 70)
    print("  专利缴费凭证图片关联助手")
    print("=" * 70)

    # 图片目录
    image_dir = project_root / "data" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    # ========================================
    # 步骤1: 显示待缴费记录
    # ========================================
    print("\n📋 步骤1: 待关联的缴费记录")
    print("-" * 70)

    # 加载缴费记录
    manager = PatentFeeAssociationManager()

    try:
        manager.load_from_json("专利缴费记录_20260224.json")
    except FileNotFoundError:
        print("❌ 找不到缴费记录文件")
        return

    # 按申请号分组显示
    app_groups = {}
    for record in manager.fee_records:
        app_num = record.get("申请号")
        if app_num not in app_groups:
            app_groups[app_num] = []
        app_groups[app_num].append(record)

    print(f"\n共有 {len(app_groups)} 个申请号需要关联凭证:\n")

    for i, (app_num, records) in enumerate(app_groups.items(), 1):
        total_amount = sum(r.get("费用金额", 0) for r in records)
        company = records[0].get("票据抬头", "未知")

        print(f"  [{i}] {app_num}")
        print(f"      公司: {company}")
        print(f"      费用: {len(records)}笔，共¥{total_amount:.0f}")
        print()

    # ========================================
    # 步骤2: 检查现有图片
    # ========================================
    print("🖼️  步骤2: 检查data/images/目录")
    print("-" * 70)

    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    existing_images = [f for f in image_dir.iterdir() if f.suffix.lower() in image_extensions]

    if existing_images:
        print(f"\n现有 {len(existing_images)} 个图片文件:\n")
        for img in existing_images:
            print(f"  📷 {img.name}")
    else:
        print("\n⚠️  data/images/ 目录为空")
        print("\n📝 请按以下步骤操作:\n")
        print("  1. 打开微信，找到缴费凭证截图")
        print("  2. 右键点击图片 -> 用'访达'显示")
        print("  3. 复制图片到以下位置:")
        print(f"     {image_dir.absolute()}")
        print("\n  建议命名格式（按申请号）:")
        for i, app_num in enumerate(app_groups.keys(), 1):
            print(f"     {app_num}.png")
        print("\n  复制完成后，按回车继续...")
        input()

        # 重新检查
        existing_images = [f for f in image_dir.iterdir() if f.suffix.lower() in image_extensions]

    # ========================================
    # 步骤3: 自动匹配关联
    # ========================================
    print("\n🔗 步骤3: 自动匹配关联")
    print("-" * 70)

    if not existing_images:
        print("⚠️  仍然没有找到图片文件")
        print("\n💡 您可以手动指定图片路径关联")
        return

    print(f"\n找到 {len(existing_images)} 个图片文件，开始匹配...\n")

    # 尝试按文件名匹配
    matched_count = 0
    for img_file in existing_images:
        filename_stem = img_file.stem  # 不含扩展名的文件名

        # 尝试直接匹配申请号
        for app_num in app_groups.keys():
            if app_num in filename_stem or filename_stem in app_num:
                manager.associate_image(app_num, str(img_file))
                matched_count += 1
                company = app_groups[app_num][0].get("票据抬头", "")
                print(f"  ✅ {app_num} ({company})")
                print(f"     -> {img_file.name}")
                break

    if matched_count == 0:
        print("⚠️  没有找到自动匹配")
        print("\n💡 请手动命名图片文件")
        print("   命名格式: 申请号.png")
        print("   例如: 2025203047164.png")
    else:
        print(f"\n🎉 成功关联 {matched_count} 个凭证!")

    # ========================================
    # 步骤4: 手动关联未匹配的
    # ========================================
    unmatched = len(app_groups) - matched_count
    if unmatched > 0:
        print(f"\n⚠️  还有 {unmatched} 个申请号未关联")
        print("\n是否需要手动指定图片路径? (y/n): ", end="")

        choice = input().strip().lower()
        if choice == 'y':
            print("\n未关联的申请号:")
            for app_num, records in app_groups.items():
                if app_num not in manager.image_records:
                    company = records[0].get("票据抬头", "")
                    print(f"  - {app_num} ({company})")

            print("\n请输入: 申请号=图片路径")
            print("例如: 2025203047164=/path/to/image.png")
            print("输入空行结束\n")

            while True:
                line = input("> ").strip()
                if not line:
                    break

                if '=' in line:
                    app_num, img_path = line.split('=', 1)
                    app_num = app_num.strip()
                    img_path = img_path.strip()

                    if Path(img_path).exists():
                        manager.associate_image(app_num, img_path)
                        print(f"  ✅ 已关联: {app_num}")
                    else:
                        print(f"  ❌ 文件不存在: {img_path}")

    # ========================================
    # 步骤5: 保存结果
    # ========================================
    print("\n💾 步骤5: 保存关联结果")
    print("-" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"专利缴费记录_已关联凭证_{timestamp}.json"

    manager.save_enhanced_record(output_file)

    # ========================================
    # 最终统计
    # ========================================
    print("\n📊 最终统计")
    print("-" * 70)

    stats = manager.get_statistics()
    print(f"\n总记录数: {stats['总记录数']}")
    print(f"已关联凭证: {stats['已关联凭证']}")
    print(f"未关联: {stats['总记录数'] - stats['已关联凭证']}")

    # 显示关联详情
    print("\n关联详情:")
    for app_num, records in app_groups.items():
        company = records[0].get("票据抬头", "")
        if app_num in manager.image_records:
            img_path = Path(manager.image_records[app_num])
            print(f"  ✅ {app_num} - {company}")
            print(f"     {img_path.name}")
        else:
            print(f"  ⚠️  {app_num} - {company} (未关联)")

    print("\n" + "=" * 70)
    print("  ✅ 处理完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
