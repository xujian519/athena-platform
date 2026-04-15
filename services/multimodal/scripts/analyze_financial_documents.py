#!/usr/bin/env python3
"""
分析财务文档和合同
Analyze financial documents and contracts
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 多模态API配置
MULTIMODAL_API_URL = "http://localhost:8088"
TARGET_FOLDER = "/Users/xujian/Nutstore Files/工作/曹立貞"

class FinancialDocumentAnalyzer:
    """财务文档分析器"""

    def __init__(self):
        self.api_url = MULTIMODAL_API_URL
        self.target_folder = Path(TARGET_FOLDER)

    def scan_images(self) -> list[Path]:
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

    def analyze_image_with_api(self, image_path: Path) -> dict[str, Any]:
        """使用多模态API分析图片"""
        try:
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Base64编码
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # 获取文件扩展名
            file_ext = image_path.suffix.lower()

            # 构建请求数据
            request_data = {
                "image": image_base64,
                "filename": image_path.name,
                "file_type": file_ext,
                "analysis_type": "financial_document",
                "extract_info": [
                    "amounts",
                    "dates",
                    "parties",
                    "contract_terms",
                    "signatures",
                    "financial_data"
                ]
            }

            # 调用API
            response = requests.post(
                f"{self.api_url}/analyze/image",
                json=request_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"成功分析: {image_path.name}")
                return {
                    "file_path": str(image_path),
                    "filename": image_path.name,
                    "analysis": result,
                    "status": "success"
                }
            else:
                logger.error(f"分析失败 {image_path.name}: {response.status_code}")
                return {
                    "file_path": str(image_path),
                    "filename": image_path.name,
                    "error": response.text,
                    "status": "error"
                }

        except Exception as e:
            logger.error(f"处理文件失败 {image_path}: {e}")
            return {
                "file_path": str(image_path),
                "filename": image_path.name,
                "error": str(e),
                "status": "error"
            }

    def extract_financial_info(self, analyses: list[dict]) -> dict[str, Any]:
        """提取财务信息"""
        financial_info = {
            "total_amounts": [],
            "contracts": [],
            "parties": set(),
            "dates": [],
            "key_terms": {},
            "unpaid_amounts": []
        }

        for analysis in analyses:
            if analysis.get("status") == "success" and "analysis" in analysis:
                result = analysis["analysis"]

                # 提取金额
                if "amounts" in result:
                    financial_info["total_amounts"].extend(result["amounts"])
                    # 查找未支付金额
                    for amount_info in result["amounts"]:
                        if any(keyword in str(amount_info).lower() for keyword in ["未付", "欠", "剩余", "unpaid"]):
                            financial_info["unpaid_amounts"].append({
                                "amount": amount_info,
                                "source": analysis["filename"]
                            })

                # 提取合同信息
                if "contract_terms" in result:
                    financial_info["contracts"].append({
                        "file": analysis["filename"],
                        "terms": result["contract_terms"]
                    })

                # 提取当事方
                if "parties" in result:
                    financial_info["parties"].update(result["parties"])

                # 提取日期
                if "dates" in result:
                    financial_info["dates"].extend(result["dates"])

        # 转换set为list
        financial_info["parties"] = list(financial_info["parties"])

        return financial_info

    def analyze_contract_legality(self, financial_info: dict) -> dict[str, Any]:
        """分析合同合法性"""
        # 使用小娜的法律服务
        try:
            # 准备法律分析请求
            {
                "query": "请分析以下合作经营协议和终止协议的合法性和潜在漏洞",
                "context": {
                    "contracts": financial_info["contracts"],
                    "parties": financial_info["parties"],
                    "amounts": financial_info["unpaid_amounts"]
                }
            }

            # 调用Laws API
            response = requests.get(
                "http://localhost:8099/api/laws/search",
                params={
                    "query": "合作经营协议 终止协议 合同法漏洞",
                    "limit": 10
                }
            )

            relevant_laws = []
            if response.status_code == 200:
                data = response.json()
                relevant_laws = data.get("laws", [])

            return {
                "relevant_laws": relevant_laws,
                "legal_recommendations": self.generate_legal_recommendations(financial_info),
                "risk_assessment": self.assess_risks(financial_info)
            }

        except Exception as e:
            logger.error(f"法律分析失败: {e}")
            return {
                "error": str(e),
                "recommendations": []
            }

    def generate_legal_recommendations(self, financial_info: dict) -> list[str]:
        """生成法律建议"""
        recommendations = [
            "1. 检查合同是否具备完整的签名和盖章",
            "2. 验证合同各方主体的合法资质",
            "3. 确认合同条款是否符合《合同法》规定",
            "4. 审查终止协议的条件是否合法有效",
            "5. 核实未付款项的具体计算方式和依据"
        ]

        # 根据具体情况添加建议
        if financial_info["unpaid_amounts"]:
            recommendations.append("6. 确认未付款项的付款期限和违约责任")

        if "丙方" in financial_info["parties"]:
            recommendations.append("7. 特别关注丙方的权利和义务条款")

        return recommendations

    def assess_risks(self, financial_info: dict) -> dict[str, Any]:
        """评估风险"""
        risks = {
            "high_risks": [],
            "medium_risks": [],
            "low_risks": []
        }

        # 高风险
        if not financial_info["contracts"]:
            risks["high_risks"].append("缺少正式合同文件")

        # 中风险
        if len(financial_info["unpaid_amounts"]) > 0:
            unpaid_count = len(financial_info['unpaid_amounts'])
            risks["medium_risks"].append(f"存在 {unpaid_count} 笔未付款项")

        # 低风险
        risks["low_risks"].append("建议进行法律审查以确认所有条款的合法性")

        return risks

    def generate_report(self, analyses: list[dict], financial_info: dict, legal_analysis: dict) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 60)
        report.append("财务文档和合同分析报告")
        report.append("=" * 60)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"分析文件数: {len(analyses)}")
        report.append("")

        # 1. 财务概况
        report.append("一、财务概况")
        report.append("-" * 40)
        report.append(f"发现金额信息: {len(financial_info['total_amounts'])} 处")
        report.append(f"未付款项: {len(financial_info['unpaid_amounts'])} 笔")
        report.append("")

        if financial_info["unpaid_amounts"]:
            report.append("未付款项明细:")
            for unpaid in financial_info["unpaid_amounts"]:
                report.append(f"  - {unpaid['amount']} (来源: {unpaid['source']})")
            report.append("")

        # 2. 合同分析
        report.append("二、合同分析")
        report.append("-" * 40)
        report.append(f"涉及合同: {len(financial_info['contracts'])} 份")
        report.append(f"当事方: {', '.join(financial_info['parties'])}")
        report.append("")

        # 3. 法律分析
        if legal_analysis.get("relevant_laws"):
            report.append("三、相关法律条文")
            report.append("-" * 40)
            for law in legal_analysis["relevant_laws"][:5]:
                report.append(f"- {law.get('name', '未知法律')}")
            report.append("")

        if legal_analysis.get("legal_recommendations"):
            report.append("四、法律建议")
            report.append("-" * 40)
            for rec in legal_analysis["legal_recommendations"]:
                report.append(rec)
            report.append("")

        # 5. 风险评估
        if legal_analysis.get("risk_assessment"):
            risk_assessment = legal_analysis["risk_assessment"]
            report.append("五、风险评估")
            report.append("-" * 40)

            if risk_assessment.get("high_risks"):
                report.append("高风险:")
                for risk in risk_assessment["high_risks"]:
                    report.append(f"  ⚠️  {risk}")

            if risk_assessment.get("medium_risks"):
                report.append("中风险:")
                for risk in risk_assessment["medium_risks"]:
                    report.append(f"  ⚡ {risk}")

            if risk_assessment.get("low_risks"):
                report.append("低风险:")
                for risk in risk_assessment["low_risks"]:
                    report.append(f"  ℹ️  {risk}")
            report.append("")

        # 6. 结论
        report.append("六、结论")
        report.append("-" * 40)
        if financial_info["unpaid_amounts"]:
            total_unpaid = len(financial_info["unpaid_amounts"])
            report.append(f"结论: 发现 {total_unpaid} 笔未付款项，建议尽快通过法律途径追讨。")
        else:
            report.append("结论: 未发现明显的未付款项，但仍建议审查合同完整性。")

        report.append("")
        report.append("注: 本分析基于AI识别，建议由专业律师进行最终审核。")

        return "\n".join(report)

def main() -> None:
    """主函数"""
    print("\n📄 财务文档和合同分析工具")
    print("=" * 60)
    print(f"目标文件夹: {TARGET_FOLDER}")
    print("")

    # 创建分析器
    analyzer = FinancialDocumentAnalyzer()

    # 扫描图片
    image_files = analyzer.scan_images()
    if not image_files:
        print("❌ 未找到任何图片文件")
        return

    print(f"✅ 找到 {len(image_files)} 个文件")
    print("\n开始分析...")

    # 分析每个文件
    analyses = []
    for i, image_file in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] 分析: {image_file.name}")
        analysis = analyzer.analyze_image_with_api(image_file)
        analyses.append(analysis)

    # 提取财务信息
    print("\n📊 提取财务信息...")
    financial_info = analyzer.extract_financial_info(analyses)

    # 法律分析
    print("\n⚖️ 进行法律分析...")
    legal_analysis = analyzer.analyze_contract_legality(financial_info)

    # 生成报告
    print("\n📋 生成分析报告...")
    report = analyzer.generate_report(analyses, financial_info, legal_analysis)

    # 保存报告
    report_path = Path("financial_analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print("\n✅ 分析完成！")
    print(f"📄 报告已保存: {report_path.absolute()}")
    print("\n" + "=" * 60)
    print(report)

if __name__ == "__main__":
    main()
