#!/usr/bin/env python3
"""
专利缴费记录完整处理脚本
Patent Fee Payment Complete Processing Script

整合功能：
1. 加载现有缴费记录
2. OCR识别缴费凭证截图
3. 自动匹配并关联
4. 生成增强记录
5. 导出数据库格式

使用方法:
1. 将缴费凭证截图复制到 data/images/ 目录
2. 运行此脚本
3. 查看生成的关联记录

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.patent_fee_association_manager import PatentFeeAssociationManager
from tools.patent_fee_ocr_processor import PatentFeeOCRProcessor


def process_payment_with_vouchers(
    json_record_file: str = "专利缴费记录_20260224.json",
    image_dir: str = "data/images/",
    output_prefix: str | None = None
):
    """完整处理缴费记录和凭证

    Args:
        json_record_file: JSON格式的缴费记录文件
        image_dir: 凭证图片目录
        output_prefix: 输出文件前缀
    """
    print("=" * 70)
    print("  专利缴费记录完整处理流程")
    print("=" * 70)

    # 生成输出文件前缀
    if output_prefix is None:
        output_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ========================================
    # 步骤1: 加载现有缴费记录
    # ========================================
    print("\n📝 步骤1: 加载现有缴费记录")
    print("-" * 70)

    manager = PatentFeeAssociationManager()

    try:
        manager.load_from_json(json_record_file)
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        return None

    # ========================================
    # 步骤2: 检查图片目录
    # ========================================
    print("\n🖼️  步骤2: 检查凭证图片目录")
    print("-" * 70)

    image_path = Path(image_dir)
    if not image_path.exists():
        print(f"⚠️  图片目录不存在: {image_dir}")
        print("💡 请将缴费凭证截图复制到该目录后重新运行")
        print("\n📖 操作步骤:")
        print("   1. 打开微信/文件管理器")
        print("   2. 找到缴费凭证截图")
        print(f"   3. 复制到: {image_path.absolute()}")
        print("   4. 重新运行此脚本")

        # 继续处理，只是没有图片关联
        print("\n⏭️  跳过图片关联，继续处理数据...")
        has_images = False
    else:
        # 统计图片文件
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        image_files = [f for f in image_path.rglob("*") if f.suffix.lower() in image_extensions]

        if image_files:
            print(f"✅ 找到 {len(image_files)} 个图片文件")
            for img in image_files[:5]:  # 显示前5个
                print(f"   - {img.name}")
            if len(image_files) > 5:
                print(f"   ... 还有 {len(image_files) - 5} 个文件")
            has_images = True
        else:
            print("⚠️  目录中没有找到图片文件")
            has_images = False

    # ========================================
    # 步骤3: OCR识别图片（如果有）
    # ========================================
    if has_images:
        print("\n🔍 步骤3: OCR识别缴费凭证")
        print("-" * 70)

        try:
            ocr = PatentFeeOCRProcessor()

            if ocr.reader is not None:
                ocr_results = ocr.batch_process_directory(
                    image_dir=image_dir,
                    existing_records=manager.fee_records,
                    output_file=f"data/ocr_results_{output_prefix}.json"
                )

                print("\n📊 OCR处理结果:")
                print(f"   处理图片数: {ocr_results['total_images']}")
                print(f"   成功识别: {ocr_results['successful']}")
                print(f"   识别失败: {ocr_results['failed']}")
                print(f"   匹配记录数: {len(ocr_results['matches'])}")

                # 自动关联匹配的图片
                print("\n🔗 自动关联匹配的图片:")
                for match_item in ocr_results['matches']:
                    image_file = match_item['image']
                    for match in match_item['matches']:
                        record = match['record']
                        app_number = record.get('申请号')
                        company = record.get('票据抬头')

                        manager.associate_image(app_number, image_file)
                        print(f"   ✅ {app_number} ({company})")

        except Exception as e:
            print(f"⚠️  OCR处理失败: {e}")
            print("💡 可以手动关联图片")

    # ========================================
    # 步骤4: 手动关联图片（可选）
    # ========================================
    print("\n📝 步骤4: 手动关联选项")
    print("-" * 70)
    print("""
如果需要手动关联图片，可以使用以下方法：

方法1: 使用文件名自动匹配
--------------------------------------
将图片重命名为: 申请号_任意描述.png
例如: 2025203047164_星迪科技缴费凭证.png

然后运行:
manager.associate_images_from_directory("data/images/")

方法2: 手动指定关联
--------------------------------------
manager.associate_image(
    application_number="2025203047164",
    image_path="data/images/凭证1.png"
)
    """)

    # ========================================
    # 步骤5: 生成增强记录
    # ========================================
    print("\n✨ 步骤5: 生成增强记录")
    print("-" * 70)

    enhanced_file = f"专利缴费记录_增强_{output_prefix}.json"
    manager.save_enhanced_record(enhanced_file)

    # ========================================
    # 步骤6: 导出数据库格式
    # ========================================
    print("\n🗄️  步骤6: 导出数据库导入格式")
    print("-" * 70)

    db_data = manager.export_for_database()
    db_file = f"专利缴费记录_数据库导入_{output_prefix}.json"

    with open(manager.data_dir / db_file, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据库格式已保存到: {db_file}")
    print(f"   表名: {db_data['table_name']}")
    print(f"   记录数: {db_data['total_count']}")
    print(f"   总金额: ¥{db_data['total_amount']:.2f}")

    # ========================================
    # 步骤7: 显示统计摘要
    # ========================================
    print("\n📊 最终统计摘要")
    print("-" * 70)

    manager.print_summary()

    # ========================================
    # 完成
    # ========================================
    print("\n" + "=" * 70)
    print("  ✅ 处理完成！")
    print("=" * 70)

    print(f"""
生成的文件:
--------------------------------------
1. 增强记录: data/{enhanced_file}
2. 数据库导入格式: data/{db_file}
3. OCR结果: data/ocr_results_{output_prefix}.json (如有图片)

下一步操作:
--------------------------------------
1. 审查生成的记录是否正确
2. 如有错误，手动编辑JSON文件修正
3. 使用数据库导入脚本导入PostgreSQL
4. 将原始凭证图片归档保存

数据库导入脚本示例:
--------------------------------------
from tools.import_fee_payments_to_db import import_to_database

import_to_database(
    json_file="data/{db_file}",
    table_name="patent_fee_payments"
)
    """)

    return manager


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="专利缴费记录完整处理")
    parser.add_argument(
        "--record",
        default="专利缴费记录_20260224.json",
        help="缴费记录JSON文件 (默认: 专利缴费记录_20260224.json)"
    )
    parser.add_argument(
        "--images",
        default="data/images/",
        help="凭证图片目录 (默认: data/images/)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件前缀 (默认: 当前时间戳)"
    )

    args = parser.parse_args()

    process_payment_with_vouchers(
        json_record_file=args.record,
        image_dir=args.images,
        output_prefix=args.output
    )


if __name__ == "__main__":
    main()
