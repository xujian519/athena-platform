#!/usr/bin/env python3
"""
专利三维交集检索分析器
遍历指定目录下的所有专利文件，使用三维交集检索法进行分析
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PatentInfo:
    """专利信息数据类"""
    公开号: str
    标题: str
    摘要: str
    申请日: str | None = None
    授权公告日: str | None = None
    申请人: str | None = None
    IPC分类号: str | None = None
    文件路径: str = ""


class ThreeDimensionalSearchAnalyzer:
    """三维交集检索分析器"""

    def __init__(self, target_patent_date: str = "2019-08-27"):
        """
        初始化分析器

        Args:
            target_patent_date: 目标专利申请日，早于此日期的专利才能作为证据
        """
        self.target_date = datetime.strptime(target_patent_date, "%Y-%m-%d")

        # 三维维度定义
        self.dimensions = {
            "应用领域": {
                "包装机": 3,
                "输送机": 2,
                "传送装置": 2,
                "限位装置": 1,
                "物料处理": 1
            },
            "执行部件": {
                "斜向滑轨": 5,
                "斜向导轨": 5,
                "斜向调节": 4,
                "滑轨": 3,
                "导轨": 3,
                "滑动座": 3,
                "滑块": 2,
                "限位板": 2,
                "物料限位板": 3,
                "纵向调节": 3
            },
            "运动轨迹": {
                "间距变化": 4,
                "间距调节": 4,
                "横向位移": 3,
                "纵向位移": 3,
                "联动": 2,
                "同步": 2,
                "自动调节": 2,
                "高度调节": 1,
                "位置调节": 1
            }
        }

        # 目标核心特征
        self.target_features = [
            "斜向导轨",
            "纵向位移转化为横向间距",
            "间距逐渐缩短",
            "自动调节",
            "物料限位板"
        ]

    def parse_patent_markdown(self, file_path: str) -> PatentInfo | None:
        """
        解析专利markdown文件

        Args:
            file_path: markdown文件路径

        Returns:
            PatentInfo对象，解析失败返回None
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # 提取公开号（从文件名）
            公开号 = Path(file_path).stem

            # 提取标题 - 从权利要求书或摘要后的部分
            标题 = "未知标题"
            title_patterns = [
                r'\((\d+)\)\s*实用新型名称\s*\n\s*(.+?)\n',  # 从权利要求书部分
                r'##\s*基本信息\s*.*?\|\s*\*\*专利号\*\*\s*\|\s*(.+?)\s*\|',  # 从基本信息表格
                r'#\s+(.+?)\s*\n##\s*基本信息'  # 从主标题
            ]
            for pattern in title_patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    标题 = match.group(2) if match.lastindex >= 2 else match.group(1)
                    标题 = 标题.strip()
                    if 标题 and 标题 != "CN" + 公开号:
                        break

            # 提取摘要 - 从摘要部分
            摘要 = ""
            abstract_section = re.search(r'##\s*摘要\s*\n(.*?)(?=##|---|\Z)', content, re.DOTALL)
            if abstract_section:
                # 清理摘要文本
                摘要 = abstract_section.group(1).strip()
                # 移除页码和页脚信息
                摘要 = re.sub(r'\n\d+\n', ' ', 摘要)
                摘要 = re.sub(r'NC\s*\d+', '', 摘要)
                摘要 = re.sub(r'\(.+?\)', '', 摘要)
                摘要 = ' '.join(摘要.split())  # 合并多余空格

            # 如果摘要部分没有内容，从实用新型内容提取
            if not 摘要 or len(摘要) < 20:
                content_match = re.search(r'\[000[5-9]\].*?\n\s*(.*?)(?=\[00\d+\]|##)', content, re.DOTALL)
                if content_match:
                    摘要 = content_match.group(1).strip()
                    摘要 = ' '.join(摘要.split())

            # 提取申请日 - 从基本信息表格
            申请日 = None
            date_match = re.search(r'\|\s*\*\*申请日\*\*\s*\|\s*(.*?)\s*\|', content)
            if date_match:
                申请日 = date_match.group(1).strip()
                if 申请日 == "" or 申请日 == " ":
                    申请日 = None

            # 提取申请人
            申请人 = None
            applicant_match = re.search(r'\|\s*\*\*申请人\*\*\s*\|\s*(.*?)\s*\|', content)
            if applicant_match:
                申请人 = applicant_match.group(1).strip()
                if 申请人 == "" or 申请人 == " ":
                    申请人 = None

            # 提取IPC分类号
            IPC分类号 = None
            ipc_match = re.search(r'\|\s*\*\*IPC分类\*\*\s*\|\s*(.*?)\s*\|', content)
            if ipc_match:
                IPC分类号 = ipc_match.group(1).strip()
                if IPC分类号 == "" or IPC分类号 == " ":
                    IPC分类号 = None

            return PatentInfo(
                公开号=公开号,
                标题=标题,
                摘要=摘要[:500] if 摘要 else "",  # 限制摘要长度
                申请日=申请日,
                申请人=申请人,
                IPC分类号=IPC分类号,
                文件路径=file_path
            )

        except Exception as e:
            print(f"解析文件失败 {file_path}: {e}")
            return None

    def calculate_3d_score(self, patent: PatentInfo) -> dict[str, Any]:
        """
        计算三维匹配分数

        Args:
            patent: 专利信息

        Returns:
            三维评分结果
        """
        # 合并标题和摘要进行分析
        text = (patent.标题 + " " + patent.摘要).lower()

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
                scores["扩展"] += 2

        return {
            "scores": scores,
            "matched_keywords": matched_keywords,
            "total_score": sum(scores.values())
        }

    def check_date_eligibility(self, 申请日: str | None) -> dict[str, Any]:
        """
        检查申请日是否早于目标专利

        Args:
            申请日: 专利申请日字符串

        Returns:
            日期资格检查结果
        """
        if not 申请日:
            return {
                "eligible": False,
                "reason": "申请日未知",
                "days_before": None
            }

        try:
            # 尝试多种日期格式
            for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y%m%d"]:
                try:
                    patent_date = datetime.strptime(申请日, fmt)
                    break
                except ValueError:
                    continue
            else:
                return {
                    "eligible": False,
                    "reason": f"申请日格式无法解析: {申请日}",
                    "days_before": None
                }

            days_diff = (self.target_date - patent_date).days

            return {
                "eligible": days_diff > 0,
                "reason": f"申请日为{申请日}",
                "days_before": days_diff
            }

        except Exception as e:
            return {
                "eligible": False,
                "reason": f"日期解析错误: {e}",
                "days_before": None
            }

    def analyze_patent(self, patent: PatentInfo) -> dict[str, Any]:
        """
        分析单个专利

        Args:
            patent: 专利信息

        Returns:
            完整的分析结果
        """
        # 计算三维评分
        score_result = self.calculate_3d_score(patent)

        # 检查日期资格
        date_check = self.check_date_eligibility(patent.申请日)

        # 判断是否可作为证据
        can_be_evidence = (
            date_check["eligible"] and
            score_result["total_score"] >= 10
        )

        return {
            "公开号": patent.公开号,
            "标题": patent.标题[:100],  # 限制标题长度
            "摘要": patent.摘要[:300],   # 限制摘要长度
            "申请日": patent.申请日 or "未知",
            "申请人": patent.申请人 or "未知",
            "IPC分类号": patent.IPC分类号 or "未知",
            "匹配分数": score_result["total_score"],
            "三维匹配": score_result["scores"],
            "匹配关键词": list(set(
                score_result["matched_keywords"]["应用领域"] +
                score_result["matched_keywords"]["执行部件"] +
                score_result["matched_keywords"]["运动轨迹"]
            )),
            "日期资格": date_check,
            "可作证据": can_be_evidence,
            "文件路径": patent.文件路径
        }

    def scan_directory(self, directory: str) -> list[PatentInfo]:
        """
        扫描目录获取所有专利文件

        Args:
            directory: 目录路径

        Returns:
            专利信息列表
        """
        patents = []
        directory = Path(directory)

        # 查找所有markdown专利文件
        for md_file in directory.rglob("*.md"):
            # 跳过非专利文件
            if not re.match(r'CN\d+[A-ZU]', md_file.stem):
                continue

            patent_info = self.parse_patent_markdown(str(md_file))
            if patent_info:
                patents.append(patent_info)

        return patents

    def analyze_directory(self, directory: str) -> dict[str, Any]:
        """
        分析目录下的所有专利

        Args:
            directory: 目录路径

        Returns:
            完整分析报告
        """
        print(f"开始扫描目录: {directory}")

        # 扫描专利文件
        patents = self.scan_directory(directory)
        print(f"找到 {len(patents)} 个专利文件")

        # 分析每个专利
        results = {
            "高相关专利": [],  # 分数 >= 15
            "中相关专利": [],  # 分数 >= 10
            "低相关专利": [],  # 分数 >= 5
            "可用证据": [],    # 可作为证据的专利
            "所有专利": []
        }

        for patent in patents:
            analysis = self.analyze_patent(patent)
            results["所有专利"].append(analysis)

            score = analysis["匹配分数"]

            # 分类存储
            if score >= 15:
                results["高相关专利"].append(analysis)
            elif score >= 10:
                results["中相关专利"].append(analysis)
            elif score >= 5:
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
            "检索策略": "三维交集检索法",
            "目标特征": "斜向导轨将纵向位移转化为横向间距变化",
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "统计信息": {
                "扫描专利总数": len(results["所有专利"]),
                "高相关专利数量": len(results["高相关专利"]),
                "中相关专利数量": len(results["中相关专利"]),
                "低相关专利数量": len(results["低相关专利"]),
                "可用证据数量": len(results["可用证据"])
            },
            "高相关专利": results["高相关专利"][:20],  # 限制数量
            "中相关专利": results["中相关专利"][:20],
            "低相关专利": results["低相关专利"][:20],
            "可用证据": results["可用证据"],
            "所有专利摘要": [
                {
                    "公开号": p["公开号"],
                    "申请日": p["申请日"],
                    "匹配分数": p["匹配分数"],
                    "可作证据": p["可作证据"]
                }
                for p in results["所有专利"]
            ]
        }

        # 保存JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"分析报告已保存到: {output_file}")

        return report


def main():
    """主函数"""
    # 配置路径
    target_directory = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9"
    output_file = "/Users/xujian/Athena工作平台/data/patents_verify/full_directory_3d_search_results_201921401279.9.json"

    # 创建分析器
    analyzer = ThreeDimensionalSearchAnalyzer()

    # 执行分析
    results = analyzer.analyze_directory(target_directory)

    # 生成报告
    report = analyzer.generate_report(results, output_file)

    # 打印摘要
    print("\n" + "="*60)
    print("分析完成！")
    print("="*60)
    print(f"扫描专利总数: {report['统计信息']['扫描专利总数']}")
    print(f"高相关专利: {report['统计信息']['高相关专利数量']}")
    print(f"中相关专利: {report['统计信息']['中相关专利数量']}")
    print(f"低相关专利: {report['统计信息']['低相关专利数量']}")
    print(f"可用证据: {report['统计信息']['可用证据数量']}")

    # 显示可用证据
    if report["可用证据"]:
        print("\n可用证据列表:")
        for i, evidence in enumerate(report["可用证据"], 1):
            print(f"{i}. {evidence['公开号']} - 分数: {evidence['匹配分数']}, "
                  f"申请日: {evidence['申请日']}, "
                  f"申请日差距: {evidence['日期资格']['days_before']}天")
    else:
        print("\n未找到可用的现有技术证据（所有专利申请日晚于目标专利或分数过低）")


if __name__ == "__main__":
    main()
