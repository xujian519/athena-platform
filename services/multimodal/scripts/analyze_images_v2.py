#!/usr/bin/env python3
"""
使用多模态API分析图片
Analyze images using multimodal API
"""

import os
from core.async_main import async_main
import sys
import json
import requests
import logging
from core.logging_config import setup_logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 多模态API配置
MULTIMODAL_API_URL = "http://localhost:8088"
TARGET_FOLDER = "/Users/xujian/Nutstore Files/工作/曹立貞"

class ImageAnalyzer:
    """图片分析器"""

    def __init__(self):
        self.api_url = MULTIMODAL_API_URL
        self.target_folder = Path(TARGET_FOLDER)

    def scan_images(self) -> List[Path]:
        """扫描文件夹中的图片"""
        logger.info(f"扫描文件夹: {self.target_folder}")

        if not self.target_folder.exists():
            logger.error(f"文件夹不存在: {self.target_folder}")
            return []

        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.bmp', '.tiff', '.webp'}

        image_files = []
        for ext in image_extensions:
            image_files.extend(self.target_folder.glob(f"*{ext}"))
            image_files.extend(self.target_folder.glob(f"*{ext.upper()}"))

        logger.info(f"找到 {len(image_files)} 个图片文件")

        # 按文件名排序
        image_files.sort(key=lambda x: x.name)
        return image_files

    def analyze_image(self, image_path: Path) -> Dict[str, Any]:
        """分析单个图片"""
        try:
            # 上传文件
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                response = requests.post(
                    f"{self.api_url}/api/files/upload",
                    files=files,
                    timeout=30
                )

            if response.status_code == 200:
                upload_result = response.json()
                file_id = upload_result.get("file_id")

                logger.info(f"✅ 成功上传: {image_path.name} (ID: {file_id})")

                # 获取文件信息
                file_info = requests.get(
                    f"{self.api_url}/api/files/{file_id}"
                ).json()

                return {
                    "file_path": str(image_path),
                    "filename": image_path.name,
                    "file_id": file_id,
                    "file_info": file_info,
                    "status": "success"
                }
            else:
                logger.error(f"❌ 上传失败 {image_path.name}: {response.status_code}")
                return {
                    "file_path": str(image_path),
                    "filename": image_path.name,
                    "error": f"HTTP {response.status_code}",
                    "status": "error"
                }

        except Exception as e:
            logger.error(f"❌ 处理失败 {image_path}: {e}")
            return {
                "file_path": str(image_path),
                "filename": image_path.name,
                "error": str(e),
                "status": "error"
            }

    def extract_text_from_image(self, image_path: Path) -> str:
        """尝试从图片提取文字（使用OCR）"""
        try:
            # 使用Python的OCR库
            import pytesseract
            from PIL import Image

            # 打开图片
            image = Image.open(image_path)

            # 提取文字
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')

            return text.strip()

        except ImportError:
            logger.warning("未安装pytesseract，跳过OCR识别")
            return ""
        except Exception as e:
            logger.error(f"OCR识别失败 {image_path}: {e}")
            return ""

    def analyze_financial_content(self, texts: List[str]) -> Dict[str, Any]:
        """分析财务内容"""
        financial_data = {
            "amounts": [],
            "dates": [],
            "contracts": [],
            "parties": [],
            "unpaid_amounts": []
        }

        for text in texts:
            if not text:
                continue

            # 查找金额模式
            import re

            # 匹配金额
            amount_patterns = [
                r'(\d+[,.]?\d*)\s*[万千百十]*\s*元',
                r'[¥$]\s*(\d+[,.]?\d*)',
                r'人民币\s*(\d+[,.]?\d*)',
                r'(\d+[,.]?\d*)\s*[万千百十]*\s*[元圆]冤',
            ]

            for pattern in amount_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    financial_data["amounts"].append(match)
                    # 检查是否是未支付
                    if any(keyword in text for keyword in ["未付", "欠", "剩余", "还差", "应付"]):
                        financial_data["unpaid_amounts"].append({
                            "amount": match,
                            "context": text[:100]
                        })

            # 查找日期
            date_pattern = r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)'
            dates = re.findall(date_pattern, text)
            financial_data["dates"].extend(dates)

            # 查找合同相关关键词
            contract_keywords = ["合作经营协议", "终止协议", "合同", "协议", "丙方", "甲方", "乙方"]
            if any(keyword in text for keyword in contract_keywords):
                financial_data["contracts"].append({
                    "filename": "unknown",
                    "snippet": text[:200]
                })

            # 提取当事方
            party_patterns = [
                r'(甲方[:：]\s*([^，。；\n]+))',
                r'(乙方[:：]\s*([^，。；\n]+))',
                r'(丙方[:：]\s*([^，。；\n]+))',
            ]

            for pattern in party_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) > 1:
                        financial_data["parties"].append(match[1].strip())

        return financial_data

    def get_legal_advice(self, financial_data: Dict) -> List[str]:
        """获取法律建议"""
        advice = []

        # 基于发现的问题生成建议
        if financial_data["contracts"]:
            advice.append("📋 发现合同文件，建议审查以下方面：")
            advice.append("   1. 合同各方的主体资格是否合法")
            advice.append("   2. 合同条款是否明确具体")
            advice.append("   3. 违约责任是否约定清楚")
            advice.append("   4. 争议解决方式是否明确")

        if financial_data["unpaid_amounts"]:
            advice.append("\n💰 发现未付款项，建议：")
            advice.append("   1. 保留好付款凭证和合同文件")
            advice.append("   2. 及时发送催款通知")
            advice.append("   3. 必要时通过法律途径追讨")

        # 通用建议
        advice.extend([
            "\n⚖️ 法律风险提示：",
            "1. 所有协议应当采用书面形式",
            "2. 合同内容应当符合《合同法》规定",
            "3. 重要合同建议由专业律师审核",
            "4. 注意保存所有合同相关证据"
        ])

        return advice

    def generate_report(self, image_analyses: List[Dict], financial_data: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 60)
        report.append("丙方财务文件分析报告")
        report.append("=" * 60)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"分析文件数: {len(image_analyses)}")
        report.append("")

        # 文件列表
        report.append("一、文件清单")
        report.append("-" * 40)
        for analysis in image_analyses:
            status = "✅" if analysis["status"] == "success" else "❌"
            report.append(f"{status} {analysis['filename']}")
        report.append("")

        # 财务分析
        report.append("二、财务信息分析")
        report.append("-" * 40)

        if financial_data["amounts"]:
            report.append(f"发现金额信息 {len(financial_data['amounts'])} 处:")
            for amount in financial_data["amounts"][:10]:  # 只显示前10个
                report.append(f"  - {amount}")
        else:
            report.append("未发现明确的金额信息")

        report.append("")

        if financial_data["unpaid_amounts"]:
            report.append(f"未付款项 {len(financial_data['unpaid_amounts'])} 笔:")
            for unpaid in financial_data["unpaid_amounts"]:
                report.append(f"  💸 {unpaid['amount']}")
                if 'context' in unpaid:
                    report.append(f"     {unpaid['context'][:100]}...")
        else:
            report.append("未发现未付款项")

        report.append("")

        # 合同分析
        if financial_data["contracts"]:
            report.append("三、合同文件分析")
            report.append("-" * 40)
            report.append(f"发现合同相关内容 {len(financial_data['contracts'])} 处")
            for contract in financial_data["contracts"]:
                report.append(f"  📄 {contract['snippet'][:150]}...")
        report.append("")

        # 当事方
        if financial_data["parties"]:
            report.append("四、合同当事方")
            report.append("-" * 40)
            for party in set(financial_data["parties"]):  # 去重
                report.append(f"  👤 {party}")
        report.append("")

        # 法律建议
        advice = self.get_legal_advice(financial_data)
        report.append("五、法律建议")
        report.append("-" * 40)
        report.extend(advice)
        report.append("")

        # 结论
        report.append("六、分析结论")
        report.append("-" * 40)
        if financial_data["unpaid_amounts"]:
            report.append(f"⚠️  发现 {len(financial_data['unpaid_amounts'])} 笔未付款项，建议尽快通过合法途径解决。")
        else:
            report.append("✅ 未发现明显的未付款项，但建议进一步审查合同细节。")

        report.append("\n" + "=" * 60)
        report.append("注: 本分析基于图片内容识别，具体金额和法律问题建议咨询专业律师。")

        return "\n".join(report)

def main() -> None:
    """主函数"""
    print("\n📄 丙方财务文件分析")
    print("=" * 60)
    print(f"目标文件夹: {TARGET_FOLDER}")
    print("")

    # 创建分析器
    analyzer = ImageAnalyzer()

    # 扫描图片
    image_files = analyzer.scan_images()
    if not image_files:
        print("❌ 未找到任何图片文件")
        return

    print(f"✅ 找到 {len(image_files)} 个文件")
    print("\n开始分析...")

    # 分析图片
    image_analyses = []
    all_texts = []

    for i, image_file in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] 处理: {image_file.name}")

        # 上传并分析图片
        analysis = analyzer.analyze_image(image_file)
        image_analyses.append(analysis)

        # 尝试OCR识别文字
        text = analyzer.extract_text_from_image(image_file)
        all_texts.append(text)

        if text:
            print(f"  📝 识别文字: {len(text)} 字符")

    # 分析财务内容
    print("\n📊 分析财务内容...")
    financial_data = analyzer.analyze_financial_content(all_texts)

    # 生成报告
    print("\n📋 生成分析报告...")
    report = analyzer.generate_report(image_analyses, financial_data)

    # 保存报告
    report_path = Path("/Users/xujian/Athena工作平台/services/multimodal/丙方财务分析报告.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 分析完成！")
    print(f"📄 报告已保存: {report_path}")
    print("\n" + report)

if __name__ == "__main__":
    main()