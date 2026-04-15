#!/usr/bin/env python3
"""
专利缴费凭证OCR处理器
Patent Fee Payment OCR Processor

功能：
1. 使用OCR识别缴费凭证截图中的信息
2. 自动匹配申请号并关联
3. 提取关键信息（金额、日期、公司等）
4. 生成结构化的缴费记录

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PatentFeeOCRProcessor:
    """专利缴费凭证OCR处理器"""

    # 费用种类关键词模式
    FEE_TYPE_PATTERNS = [
        r"年费.*?第(\d+)年",
        r"申请费",
        r"实质审查费",
        r"公布印刷费",
        r"复审费",
        r"著录项目变更费",
        r"恢复费",
        r"延长期费",
    ]

    # 专利类型关键词
    PATENT_TYPE_PATTERNS = {
        "发明": "invention",
        "实用新型": "utility_model",
        "外观设计": "design",
    }

    def __init__(self, reader_language: list[str] | None = None):
        """初始化OCR处理器

        Args:
            reader_language: OCR识别语言列表，默认为中英文
        """
        self.reader_language = reader_language or ["ch_sim", "en"]
        self.reader = None
        self._init_reader()

    def _init_reader(self) -> None:
        """初始化OCR读取器"""
        if not EASYOCR_AVAILABLE:
            print("⚠️  easyocr未安装，OCR功能不可用")
            print("💡 安装命令: pip install easyocr")
            return

        print("📖 正在初始化OCR引擎...")
        try:
            self.reader = easyocr.Reader(
                self.reader_language,
                gpu=False,
                verbose=False
            )
            print("✅ OCR引擎初始化成功")
        except Exception as e:
            print(f"❌ OCR引擎初始化失败: {e}")
            self.reader = None

    def extract_text_from_image(self, image_path: str | Path) -> list[str]:
        """从图片中提取文本

        Args:
            image_path: 图片文件路径

        Returns:
            提取的文本行列表
        """
        if self.reader is None:
            raise RuntimeError("OCR引擎未初始化，请检查easyocr是否安装")

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        print(f"\n🔍 正在识别图片: {image_path.name}")

        # 执行OCR
        result = self.reader.readtext(str(image_path))

        # 提取文本
        texts = [item[1] for item in result if item[2] > 0.5]  # 置信度>0.5

        print(f"✅ 识别到 {len(texts)} 行文本")

        return texts

    def parse_payment_info(self, texts: list[str]) -> dict[str, Any]:
        """解析文本中的缴费信息

        Args:
            texts: 提取的文本行列表

        Returns:
            解析出的缴费信息字典
        """
        payment_info = {
            "application_numbers": [],
            "company_name": None,
            "credit_code": None,
            "fee_types": [],
            "amounts": [],
            "total_amount": None,
            "payment_date": None,
            "raw_text": "\n".join(texts),
        }

        # 合并所有文本用于匹配
        full_text = "\n".join(texts)

        # 1. 提取申请号/专利号 (13-15位数字，可能含X)
        app_pattern = r"\d{13,15}X?|\d{11}X?\d{2}"
        matches = re.findall(app_pattern, full_text)
        payment_info["application_numbers"] = list(set(matches))

        # 2. 提取统一社会信用代码 (18位)
        credit_pattern = r"[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}"
        credit_matches = re.findall(credit_pattern, full_text)
        if credit_matches:
            payment_info["credit_code"] = credit_matches[0]

        # 3. 提取公司名称 (通常在"票据抬头"后面)
        for i, text in enumerate(texts):
            if "票据抬头" in text or "公司" in text:
                # 尝试从当前或下一行获取
                company = text.replace("票据抬头", "").replace(":", "").replace("：", "").strip()
                if company and len(company) > 3:
                    payment_info["company_name"] = company
                    break
                elif i + 1 < len(texts):
                    company = texts[i + 1].strip()
                    if len(company) > 3:
                        payment_info["company_name"] = company
                        break

        # 4. 提取费用种类
        for pattern in self.FEE_TYPE_PATTERNS:
            matches = re.findall(pattern, full_text)
            for match in matches:
                if pattern not in payment_info["fee_types"]:
                    payment_info["fee_types"].append(match)

        # 5. 提取金额 (包括总金额)
        amount_patterns = [
            r"总金额.*?¥?\s*(\d+\.?\d*)",
            r"合计.*?¥?\s*(\d+\.?\d*)",
            r"¥\s*(\d+\.?\d*)",
            r"(\d+\.\d{2})\s*元",
        ]

        for pattern in amount_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                try:
                    amount = float(match)
                    if 0 < amount < 100000:  # 合理的金额范围
                        if "总金额" in pattern or "合计" in pattern:
                            payment_info["total_amount"] = amount
                        else:
                            payment_info["amounts"].append(amount)
                except ValueError:
                    continue

        # 6. 提取日期
        date_patterns = [
            r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?",
            r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                year, month, day = matches[0]
                payment_info["payment_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                break

        return payment_info

    def process_image(self, image_path: str | Path) -> dict:
        """处理单张图片

        Args:
            image_path: 图片文件路径

        Returns:
            处理结果字典
        """
        result = {
            "image_path": str(image_path),
            "processed_at": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "payment_info": None,
        }

        try:
            # 提取文本
            texts = self.extract_text_from_image(image_path)

            # 解析信息
            payment_info = self.parse_payment_info(texts)
            result["payment_info"] = payment_info
            result["success"] = True

            # 打印识别结果
            self._print_recognition_result(payment_info)

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 处理失败: {e}")

        return result

    def _print_recognition_result(self, payment_info: dict) -> None:
        """打印识别结果"""
        print("\n" + "-" * 50)
        print("  识别结果")
        print("-" * 50)

        if payment_info.get("application_numbers"):
            print(f"📋 申请号/专利号: {', '.join(payment_info['application_numbers'])}")

        if payment_info.get("company_name"):
            print(f"🏢 公司名称: {payment_info['company_name']}")

        if payment_info.get("credit_code"):
            print(f"📝 统一社会信用代码: {payment_info['credit_code']}")

        if payment_info.get("fee_types"):
            print(f"💰 费用种类: {', '.join(payment_info['fee_types'])}")

        if payment_info.get("total_amount"):
            print(f"💵 总金额: ¥{payment_info['total_amount']:.2f}")

        if payment_info.get("payment_date"):
            print(f"📅 缴费日期: {payment_info['payment_date']}")

        print("-" * 50)

    def match_with_existing_records(
        self,
        payment_info: dict,
        existing_records: list[dict]
    ) -> list[dict]:
        """与现有缴费记录匹配

        Args:
            payment_info: OCR识别的缴费信息
            existing_records: 现有的缴费记录列表

        Returns:
            匹配的记录列表
        """
        matched = []

        for record in existing_records:
            # 按申请号匹配
            app_number = str(record.get("申请号", ""))
            if app_number in payment_info.get("application_numbers", []):
                matched.append({
                    "record": record,
                    "match_type": "申请号匹配",
                    "confidence": "high",
                })
                continue

            # 按公司名称匹配
            company = record.get("票据抬头", "")
            if payment_info.get("company_name") and payment_info["company_name"] in company:
                matched.append({
                    "record": record,
                    "match_type": "公司名称匹配",
                    "confidence": "medium",
                })

            # 按金额匹配
            amount = record.get("费用金额", 0)
            if payment_info.get("total_amount") and abs(amount - payment_info["total_amount"]) < 0.01:
                matched.append({
                    "record": record,
                    "match_type": "金额匹配",
                    "confidence": "low",
                })

        return matched

    def batch_process_directory(
        self,
        image_dir: str | Path,
        existing_records: list[dict] | None = None,
        output_file: str | Path | None = None
    ) -> dict:
        """批量处理目录中的图片

        Args:
            image_dir: 图片目录路径
            existing_records: 现有的缴费记录列表
            output_file: 输出文件路径

        Returns:
            批量处理结果字典
        """
        image_path = Path(image_dir)
        if not image_path.exists():
            raise FileNotFoundError(f"图片目录不存在: {image_path}")

        results = {
            "processed_at": datetime.now().isoformat(),
            "total_images": 0,
            "successful": 0,
            "failed": 0,
            "matches": [],
            "details": [],
        }

        # 支持的图片格式
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

        for img_file in image_path.rglob("*"):
            if img_file.suffix.lower() not in image_extensions:
                continue

            results["total_images"] += 1

            # 处理单张图片
            result = self.process_image(img_file)
            results["details"].append(result)

            if result["success"]:
                results["successful"] += 1

                # 尝试匹配现有记录
                if existing_records and result["payment_info"]:
                    matches = self.match_with_existing_records(
                        result["payment_info"],
                        existing_records
                    )
                    if matches:
                        results["matches"].append({
                            "image": str(img_file),
                            "matches": matches,
                        })
            else:
                results["failed"] += 1

        # 保存结果
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"\n✅ 处理结果已保存到: {output_path}")

        return results


def main():
    """主函数 - 演示使用流程"""
    print("=" * 60)
    print("  专利缴费凭证OCR处理器")
    print("=" * 60)

    # 创建OCR处理器
    processor = PatentFeeOCRProcessor()

    if processor.reader is None:
        print("\n❌ OCR引擎未初始化，程序退出")
        print("\n💡 解决方案:")
        print("   pip install easyocr pillow")
        return

    # 检查是否有图片文件
    print("\n📝 使用说明:")
    print("""
1. 单张图片处理:
   processor.process_image("/path/to/image.png")

2. 批量处理目录:
   processor.batch_process_directory(
       image_dir="data/images/",
       existing_records=fee_records,
       output_file="data/ocr_results.json"
   )

3. 与缴费记录管理器结合使用:
   - 先使用OCR提取截图信息
   - 再使用管理器进行关联和导入

示例:
--------------------------------------
# 创建处理器
ocr = PatentFeeOCRProcessor()

# 加载现有记录
from tools.patent_fee_association_manager import PatentFeeAssociationManager
manager = PatentFeeAssociationManager()
manager.load_from_json("data/专利缴费记录_20260224.json")

# 批量处理图片
results = ocr.batch_process_directory(
    image_dir="data/images/",
    existing_records=manager.fee_records,
    output_file="data/ocr_match_results.json"
)

# 根据匹配结果关联图片
for match in results["matches"]:
    for m in match["matches"]:
        app_number = m["record"].get("申请号")
        image_path = match["image"]
        manager.associate_image(app_number, image_path)

# 保存增强记录
manager.save_enhanced_record("data/缴费记录_已关联.json")
    """)

    print("\n✅ OCR处理器已就绪！")
    print("=" * 60)


if __name__ == "__main__":
    main()
