#!/usr/bin/env python3
"""
专利缴费记录关联管理器
Patent Fee Payment Association Manager

功能：
1. 导入缴费记录到数据库
2. 关联缴费凭证（截图）
3. 查询和统计缴费记录
4. 生成缴费报表

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PatentFeeAssociationManager:
    """专利缴费记录关联管理器"""

    def __init__(self, data_dir: Path | None = None):
        """初始化管理器

        Args:
            data_dir: 数据目录，默认为项目根目录下的data目录
        """
        self.data_dir = data_dir or project_root / "data"
        self.fee_records: list[dict] = []
        self.image_records: dict[str, str] = {}  # 申请号 -> 图片路径

    def load_from_json(self, json_file: str | Path) -> dict:
        """从JSON文件加载缴费记录

        Args:
            json_file: JSON文件路径

        Returns:
            加载的数据字典
        """
        json_path = self.data_dir / json_file if isinstance(json_file, str) else json_file

        if not json_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        self.fee_records = data.get("缴费明细", [])
        print(f"✅ 从JSON加载了 {len(self.fee_records)} 条缴费记录")

        return data

    def load_from_csv(self, csv_file: str | Path) -> pd.DataFrame:
        """从CSV文件加载缴费记录

        Args:
            csv_file: CSV文件路径

        Returns:
            加载的DataFrame
        """
        csv_path = self.data_dir / csv_file if isinstance(csv_file, str) else csv_file

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV文件不存在: {csv_path}")

        df = pd.read_csv(csv_path, encoding="utf-8-sig")

        # 转换为字典列表
        self.fee_records = df.to_dict("records")
        print(f"✅ 从CSV加载了 {len(self.fee_records)} 条缴费记录")

        return df

    def associate_image(self, application_number: str, image_path: str) -> None:
        """关联缴费凭证图片

        Args:
            application_number: 申请号/专利号
            image_path: 图片文件路径
        """
        self.image_records[application_number] = image_path
        print(f"✅ 关联图片: {application_number} -> {image_path}")

    def associate_images_from_directory(self, image_dir: str | Path) -> dict:
        """从目录批量关联图片（通过文件名匹配申请号）

        Args:
            image_dir: 图片目录路径

        Returns:
            关联结果字典
        """
        image_path = Path(image_dir)
        if not image_path.exists():
            raise FileNotFoundError(f"图片目录不存在: {image_path}")

        results = {
            "matched": 0,
            "unmatched": 0,
            "associations": []
        }

        # 支持的图片格式
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

        # 遍历图片文件
        for img_file in image_path.rglob("*"):
            if img_file.suffix.lower() not in image_extensions:
                continue

            # 从文件名中提取申请号
            filename = img_file.stem
            for record in self.fee_records:
                app_number = str(record.get("申请号", ""))
                if app_number in filename or filename in app_number:
                    self.associate_image(app_number, str(img_file))
                    results["matched"] += 1
                    results["associations"].append({
                        "申请号": app_number,
                        "图片路径": str(img_file),
                        "费用金额": record.get("费用金额", 0)
                    })
                    break
            else:
                results["unmatched"] += 1

        print("\n📊 关联统计:")
        print(f"   成功关联: {results['matched']} 个")
        print(f"   未匹配: {results['unmatched']} 个")

        return results

    def generate_enhanced_record(self) -> dict:
        """生成增强的缴费记录（包含图片关联）

        Returns:
            增强的缴费记录字典
        """
        enhanced_records = []

        for record in self.fee_records:
            app_number = record.get("申请号", "")
            enhanced_record = record.copy()

            # 添加图片关联信息
            if app_number in self.image_records:
                enhanced_record["凭证图片"] = self.image_records[app_number]
                enhanced_record["已关联凭证"] = True
            else:
                enhanced_record["凭证图片"] = None
                enhanced_record["已关联凭证"] = False

            enhanced_records.append(enhanced_record)

        return {
            "生成时间": datetime.now().isoformat(),
            "总记录数": len(enhanced_records),
            "已关联凭证数": sum(1 for r in enhanced_records if r["已关联凭证"]),
            "缴费明细": enhanced_records
        }

    def save_enhanced_record(self, output_file: str | Path) -> None:
        """保存增强的缴费记录到JSON文件

        Args:
            output_file: 输出文件路径
        """
        enhanced_data = self.generate_enhanced_record()

        output_path = self.data_dir / output_file if isinstance(output_file, str) else output_file

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 增强记录已保存到: {output_path}")

    def get_statistics(self) -> dict:
        """获取缴费统计信息

        Returns:
            统计信息字典
        """
        if not self.fee_records:
            return {"message": "没有缴费记录"}

        total_amount = sum(r.get("费用金额", 0) for r in self.fee_records)

        # 按公司统计
        company_stats: dict[str, float] = {}
        for record in self.fee_records:
            company = record.get("票据抬头", "未知")
            amount = record.get("费用金额", 0)
            company_stats[company] = company_stats.get(company, 0) + amount

        # 按费用种类统计
        fee_type_stats: dict[str, int] = {}
        for record in self.fee_records:
            fee_type = record.get("费用种类", "未知")
            fee_type_stats[fee_type] = fee_type_stats.get(fee_type, 0) + 1

        return {
            "总缴费额": total_amount,
            "总记录数": len(self.fee_records),
            "已关联凭证": len(self.image_records),
            "公司统计": company_stats,
            "费用种类统计": fee_type_stats,
        }

    def print_summary(self) -> None:
        """打印缴费摘要"""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("  专利缴费记录摘要")
        print("=" * 60)

        print("\n📊 总览:")
        print(f"   总缴费额: ¥{stats.get('总缴费额', 0):.2f}")
        print(f"   总记录数: {stats.get('总记录数', 0)}")
        print(f"   已关联凭证: {stats.get('已关联凭证', 0)}")

        print("\n🏢 按公司统计:")
        for company, amount in stats.get("公司统计", {}).items():
            print(f"   {company}: ¥{amount:.2f}")

        print("\n💰 按费用种类统计:")
        for fee_type, count in stats.get("费用种类统计", {}).items():
            print(f"   {fee_type}: {count}笔")

        print("\n" + "=" * 60)

    def export_for_database(self) -> dict:
        """导出为数据库导入格式

        Returns:
            适合数据库导入的数据字典
        """
        db_records = []

        for record in self.fee_records:
            app_number = record.get("申请号", "")

            db_record = {
                "application_number": app_number,
                "business_type": record.get("业务类型", ""),
                "company_name": record.get("票据抬头", ""),
                "credit_code": record.get("统一社会信用代码", ""),
                "fee_type": record.get("费用种类", ""),
                "fee_amount": float(record.get("费用金额", 0)),
                "payment_date": datetime.now().date().isoformat(),
                "payment_voucher_path": self.image_records.get(app_number),
                "notes": record.get("备注", ""),
                "created_at": datetime.now().isoformat(),
            }

            db_records.append(db_record)

        return {
            "table_name": "patent_fee_payments",
            "records": db_records,
            "total_count": len(db_records),
            "total_amount": sum(r["fee_amount"] for r in db_records),
        }


def main():
    """主函数 - 演示使用流程"""
    print("=" * 60)
    print("  专利缴费记录关联管理器")
    print("=" * 60)

    # 创建管理器
    manager = PatentFeeAssociationManager()

    # 1. 加载JSON格式的缴费记录
    print("\n📝 步骤1: 加载缴费记录")
    try:
        manager.load_from_json("专利缴费记录_20260224.json")
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("💡 提示: 请先将缴费记录文件保存到data目录")
        return

    # 2. 显示统计信息
    print("\n📊 步骤2: 统计信息")
    manager.print_summary()

    # 3. 生成增强记录
    print("\n✨ 步骤3: 生成增强记录")
    enhanced_data = manager.generate_enhanced_record()
    print(f"   总记录数: {enhanced_data['总记录数']}")
    print(f"   已关联凭证数: {enhanced_data['已关联凭证数']}")

    # 4. 保存增强记录
    print("\n💾 步骤4: 保存增强记录")
    output_file = f"专利缴费记录_增强_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    manager.save_enhanced_record(output_file)

    # 5. 导出数据库格式
    print("\n🗄️  步骤5: 导出数据库格式")
    db_data = manager.export_for_database()
    db_file = f"专利缴费记录_数据库导入_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(manager.data_dir / db_file, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"   数据库格式已保存到: {db_file}")
    print(f"   表名: {db_data['table_name']}")
    print(f"   记录数: {db_data['total_count']}")
    print(f"   总金额: ¥{db_data['total_amount']:.2f}")

    # 6. 使用说明
    print("\n" + "=" * 60)
    print("  📖 图片关联说明")
    print("=" * 60)
    print("""
如果您有缴费凭证截图需要关联，请按以下步骤操作：

方法1: 将图片复制到项目目录
--------------------------------------
1. 将微信/截图中的缴费凭证图片复制到 data/images/ 目录
2. 命名格式建议: 申请号_公司名.png (如 2025203047164_星迪科技.png)
3. 运行批量关联:
   manager.associate_images_from_directory("data/images/")

方法2: 手动关联单个图片
--------------------------------------
manager.associate_image(
    application_number="2025203047164",
    image_path="/path/to/your/image.png"
)

方法3: 使用OCR识别截图内容
--------------------------------------
1. 将截图保存到项目可访问目录
2. 使用OCR工具提取信息
3. 根据提取的信息自动关联

推荐数据存储方案:
--------------------------------------
主数据库: PostgreSQL (patent_fee_payments表)
   - 存储结构化缴费数据
   - 支持复杂查询和统计
   - 便于与其他表关联

文件存储: data/images/
   - 存储原始凭证图片
   - 数据库中记录路径
   - 支持后续查看和审核
    """)

    print("\n✅ 处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
