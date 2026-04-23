#!/usr/bin/env python3
"""
专利三维交集检索分析器增强版
使用包含完整申请日期信息的JSON数据进行检索分析
"""

import json
from datetime import datetime
from typing import Any


class Enhanced3DSearchAnalyzer:
    """增强版三维检索分析器"""

    def __init__(self, target_patent_date: str = "2019-08-27"):
        """
        初始化分析器

        Args:
            target_patent_date: 目标专利申请日
        """
        self.target_date = datetime.strptime(target_patent_date, "%Y-%m-%d")

        # 三维维度定义 - 权重优化
        self.dimensions = {
            "应用领域": {
                "包装机": 5,
                "输送机": 3,
                "传送装置": 3,
                "限位装置": 2,
                "物料处理": 2,
                "物料限位": 3,
                "物品传送": 3
            },
            "执行部件": {
                "斜向滑轨": 6,
                "斜向导轨": 6,
                "斜向调节": 5,
                "滑轨": 4,
                "导轨": 3,
                "滑动座": 4,
                "滑块": 3,
                "限位板": 3,
                "物料限位板": 4,
                "纵向调节": 4,
                "调节单元": 3
            },
            "运动轨迹": {
                "间距变化": 5,
                "间距调节": 5,
                "间距渐变": 6,
                "横向位移": 4,
                "纵向位移": 4,
                "联动": 3,
                "同步": 3,
                "自动调节": 3,
                "高度调节": 2,
                "位置调节": 2,
                "纵向转化为横向": 8
            }
        }

        # 目标核心特征
        self.target_features = [
            "斜向导轨",
            "纵向位移转化为横向间距",
            "间距逐渐缩短",
            "自动调节",
            "物料限位板",
            "斜向滑轨",
            "纵向调节单元"
        ]

    def load_patent_data(self, json_file: str) -> list[dict[str, Any]:
        """
        加载专利JSON数据

        Args:
            json_file: JSON文件路径

        Returns:
            专利数据列表
        """
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)
        return data

    def parse_application_date(self, timestamp: int) -> datetime | None:
        """
        解析申请日时间戳

        Args:
            timestamp: Unix时间戳（毫秒）

        Returns:
            datetime对象
        """
        try:
            return datetime.fromtimestamp(timestamp / 1000)
        except Exception:
            return None

    def calculate_3d_score(self, patent: dict[str, Any]) -> dict[str, Any]:
        """
        计算三维匹配分数

        Args:
            patent: 专利数据字典

        Returns:
            三维评分结果
        """
        # 合并标题、摘要进行分析
        text = (
            patent.get("patent_name", "") + " " +
            patent.get("abstract_preview", "") + " " +
            patent.get("ipc_main_class", "")
        ).lower()

        scores = {
            "应用领域": 0,
            "执行部件": 0,
            "运动轨迹": 0,
            "扩展": 0
        }

        matched_keywords = {
            "应用领域": [],
            "执行部件": [],
            "运动轨迹": []
        }

        # 计算各维度分数
        for dimension, keywords in self.dimensions.items():
            if dimension == "应用领域":
                target_key = "应用领域"
            elif dimension == "执行部件":
                target_key = "执行部件"
            else:
                target_key = "运动轨迹"

            for keyword, weight in keywords.items():
                if keyword.lower() in text:
                    scores[target_key] += weight
                    matched_keywords[target_key].append(keyword)

        # 检查核心特征（扩展分）
        for feature in self.target_features:
            if feature.lower() in text:
                scores["扩展"] += 3

        return {
            "scores": scores,
            "matched_keywords": matched_keywords,
            "total_score": sum(scores.values())
        }

    def check_date_eligibility(self, application_date: datetime) -> dict[str, Any]:
        """
        检查申请日是否早于目标专利

        Args:
            application_date: 专利申请日

        Returns:
            日期资格检查结果
        """
        if not application_date:
            return {
                "eligible": False,
                "reason": "申请日未知",
                "days_before": None
            }

        days_diff = (self.target_date - application_date).days

        return {
            "eligible": days_diff > 0,
            "reason": f"申请日为{application_date.strftime('%Y-%m-%d')}",
            "days_before": days_diff
        }

    def analyze_patent(self, patent: dict[str, Any]) -> dict[str, Any]:
        """
        分析单个专利

        Args:
            patent: 专利数据字典

        Returns:
            完整的分析结果
        """
        # 解析申请日
        application_date = self.parse_application_date(patent.get("application_date"))

        # 计算三维评分
        score_result = self.calculate_3d_score(patent)

        # 检查日期资格
        date_check = self.check_date_eligibility(application_date)

        # 判断是否可作为证据
        can_be_evidence = (
            date_check["eligible"] and
            score_result["total_score"] >= 10
        )

        return {
            "申请号": patent.get("application_number"),
            "公开号": patent.get("publication_number"),
            "标题": patent.get("patent_name", ""),
            "摘要": patent.get("abstract_preview", "")[:300],
            "申请日": application_date.strftime("%Y-%m-%d") if application_date else "未知",
            "申请人": patent.get("applicant", "未知"),
            "IPC分类号": patent.get("ipc_main_class", "未知"),
            "匹配分数": score_result["total_score"],
            "三维匹配": score_result["scores"],
            "匹配关键词": list(set(
                score_result["matched_keywords"]["应用领域"] +
                score_result["matched_keywords"]["执行部件"] +
                score_result["matched_keywords"]["运动轨迹"]
            )),
            "日期资格": date_check,
            "可作证据": can_be_evidence,
            "检索组": patent.get("search_group", "未知")
        }

    def analyze_json_file(self, json_file: str) -> dict[str, Any]:
        """
        分析JSON文件中的所有专利

        Args:
            json_file: JSON文件路径

        Returns:
            完整分析报告
        """
        print(f"开始分析JSON文件: {json_file}")

        # 加载专利数据
        patents = self.load_patent_data(json_file)
        print(f"加载 {len(patents)} 个专利")

        # 分析每个专利
        results = {
            "高相关专利": [],  # 分数 >= 20
            "中相关专利": [],  # 分数 >= 15
            "低相关专利": [],  # 分数 >= 10
            "可用证据": [],    # 可作为证据的专利
            "所有专利": []
        }

        for patent in patents:
            analysis = self.analyze_patent(patent)
            results["所有专利"].append(analysis)

            score = analysis["匹配分数"]

            # 分类存储
            if score >= 20:
                results["高相关专利"].append(analysis)
            elif score >= 15:
                results["中相关专利"].append(analysis)
            elif score >= 10:
                results["低相关专利"].append(analysis)

            # 检查是否可用作证据
            if analysis["可作证据"]:
                results["可用证据"].append(analysis)

        # 按分数排序
        for key in ["高相关专利", "中相关专利", "低相关专利", "可用证据"]:
            results[key].sort(key=lambda x: x["匹配分数"], reverse=True)

        return results

    def generate_report(self, results: dict[str, Any], output_file: str):
        """
        生成分析报告

        Args:
            results: 分析结果
            output_file: 输出文件路径
        """
        report = {
            "检索策略": "三维交集检索法增强版",
            "目标特征": "斜向导轨将纵向位移转化为横向间距变化",
            "目标专利申请日": "2019-08-27",
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "统计信息": {
                "扫描专利总数": len(results["所有专利"]),
                "高相关专利数量": len(results["高相关专利"]),
                "中相关专利数量": len(results["中相关专利"]),
                "低相关专利数量": len(results["低相关专利"]),
                "可用证据数量": len(results["可用证据"])
            },
            "高相关专利": results["高相关专利"][:20],
            "中相关专利": results["中相关专利"][:20],
            "低相关专利": results["低相关专利"][:30],
            "可用证据": results["可用证据"]
        }

        # 保存JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"分析报告已保存到: {output_file}")

        return report


def main():
    """主函数"""
    # 配置路径
    json_file = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/检索结果_全部分析_20260202_170946.json"
    output_file = "/Users/xujian/Athena工作平台/data/patents_verify/enhanced_3d_search_results_with_dates_201921401279.9.json"

    # 创建分析器
    analyzer = Enhanced3DSearchAnalyzer()

    # 执行分析
    results = analyzer.analyze_json_file(json_file)

    # 生成报告
    report = analyzer.generate_report(results, output_file)

    # 打印摘要
    print("\n" + "="*70)
    print("三维交集检索分析完成！")
    print("="*70)
    print(f"扫描专利总数: {report['统计信息']['扫描专利总数']}")
    print(f"高相关专利 (≥20分): {report['统计信息']['高相关专利数量']}")
    print(f"中相关专利 (≥15分): {report['统计信息']['中相关专利数量']}")
    print(f"低相关专利 (≥10分): {report['统计信息']['低相关专利数量']}")
    print(f"可用证据 (早于目标专利): {report['统计信息']['可用证据数量']}")

    # 显示高相关专利
    if report["高相关专利"]:
        print("\n高相关专利列表:")
        for i, patent in enumerate(report["高相关专利"], 1):
            print(f"{i}. {patent['公开号']} - {patent['标题'][:40]}")
            print(f"   分数: {patent['匹配分数']}, 申请日: {patent['申请日']}, "
                  f"差距: {patent['日期资格']['days_before']}天")
            print(f"   匹配关键词: {', '.join(patent['匹配关键词'][:5])}")

    # 显示可用证据
    if report["可用证据"]:
        print("\n可用作为证据的专利:")
        for i, evidence in enumerate(report["可用证据"], 1):
            print(f"{i}. {evidence['公开号']} - 分数: {evidence['匹配分数']}, "
                  f"申请日: {evidence['申请日']}, "
                  f"申请日差距: {evidence['日期资格']['days_before']}天")
    else:
        print("\n未找到可用的现有技术证据")


if __name__ == "__main__":
    main()
