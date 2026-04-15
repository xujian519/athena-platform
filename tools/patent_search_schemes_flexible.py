#!/usr/bin/env python3
"""
专利检索方案宽松版分析器
展示部分匹配和相关性评分
"""

import json
from datetime import datetime
from typing import Any


class FlexiblePatentSearchAnalyzer:
    """宽松专利检索分析器"""

    def __init__(self, json_file: str):
        self.json_file = json_file
        self.patents = self.load_patents()

    def load_patents(self) -> list[dict[str, Any]]:
        with open(self.json_file, encoding='utf-8') as f:
            data = json.load(f)
        return data

    def calculate_scheme_score(self, patent: dict[str, Any], scheme: str) -> dict[str, Any]:
        """计算方案匹配分数"""
        text = (
            patent.get("patent_name", "") + " " +
            patent.get("abstract_preview", "") + " " +
            patent.get("ipc_main_class", "")
        ).lower()

        score = 0
        max_score = 0
        matched_groups = []

        if scheme == "A":
            # 方案A评分标准
            groups = {
                "包装机/输送机": ["包装机", "输送机", "传送装置"],
                "限位装置": ["限位板", "导料板", "护栏", "限位"],
                "斜向特征": ["斜向", "倾斜", "斜轨"],
                "导轨/滑轨": ["滑轨", "导轨", "滑槽", "导槽"],
                "间距/宽度": ["间距", "宽度"],
                "调节/调整": ["调节", "调整"]
            }
            max_score = len(groups) * 3

            for group_name, keywords in groups.items():
                group_score = sum(1 for kw in keywords if kw in text)
                if group_score >= 1:
                    matched_groups.append(group_name)
                score += min(group_score, 3)

        elif scheme == "B":
            # 方案B评分标准
            groups = {
                "物料限位装置": ["物料限位板", "导板", "限位板"],
                "驱动部件": ["驱动", "电机", "螺杆", "驱动单元"],
                "纵向特征": ["纵向", "竖向"],
                "联动特征": ["联动", "同步"],
                "横向/间距": ["横向", "间距", "宽度"],
                "斜向特征": ["斜"]
            }
            max_score = len(groups) * 3

            for group_name, keywords in groups.items():
                group_score = sum(1 for kw in keywords if kw in text)
                if group_score >= 1:
                    matched_groups.append(group_name)
                score += min(group_score, 3)

        elif scheme == "C":
            # 方案C评分标准
            groups = {
                "IPC分类": ["b65g21/20", "b65g21"],
                "斜向特征": ["斜向", "倾斜", "斜轨"],
                "调节功能": ["调节", "自动调节"],
                "限位特征": ["限位", "导料", "护栏"]
            }
            max_score = len(groups) * 3

            for group_name, keywords in groups.items():
                group_score = sum(1 for kw in keywords if kw in text)
                if group_score >= 1:
                    matched_groups.append(group_name)
                score += min(group_score, 3)

        return {
            "分数": score,
            "最大分数": max_score,
            "匹配率": f"{int(score / max_score * 100)}%" if max_score > 0 else "0%",
            "匹配组": matched_groups,
            "是否完全匹配": score >= max_score * 0.8
        }

    def analyze_with_scores(self) -> dict[str, Any]:
        """执行带评分的分析"""
        results = {
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "方案A部分匹配": [],
            "方案B部分匹配": [],
            "方案C部分匹配": [],
            "高相关推荐": []
        }

        target_date = datetime(2019, 8, 27)

        for patent in self.patents:
            pub_num = patent.get("publication_number")
            if pub_num in ["CN210456236U", "CN201921401279.9"]:
                continue

            # 检查申请日
            app_date_ts = patent.get("application_date")
            if not app_date_ts:
                continue

            app_date = datetime.fromtimestamp(app_date_ts / 1000)
            days_before = (target_date - app_date).days

            if days_before <= 0:
                continue

            # 计算各方案分数
            score_a = self.calculate_scheme_score(patent, "A")
            score_b = self.calculate_scheme_score(patent, "B")
            score_c = self.calculate_scheme_score(patent, "C")

            patent_info = {
                "申请号": patent.get("application_number"),
                "公开号": pub_num,
                "标题": patent.get("patent_name"),
                "摘要": patent.get("abstract_preview", "")[:200],
                "申请日": app_date.strftime("%Y-%m-%d"),
                "早于目标天数": days_before,
                "IPC分类号": patent.get("ipc_main_class"),
                "申请人": patent.get("applicant")
            }

            # 方案A部分匹配（分数≥6）
            if score_a["分数"] >= 6:
                results["方案A部分匹配"].append({
                    **patent_info,
                    "评分": score_a
                })

            # 方案B部分匹配（分数≥6）
            if score_b["分数"] >= 6:
                results["方案B部分匹配"].append({
                    **patent_info,
                    "评分": score_b
                })

            # 方案C部分匹配（分数≥6）
            if score_c["分数"] >= 6:
                results["方案C部分匹配"].append({
                    **patent_info,
                    "评分": score_c
                })

            # 高相关推荐（任一方案≥10分）
            max_score = max(score_a["分数"], score_b["分数"], score_c["分数"])
            if max_score >= 10:
                best_scheme = "A" if score_a["分数"] == max_score else ("B" if score_b["分数"] == max_score else "C")
                results["高相关推荐"].append({
                    **patent_info,
                    "最佳方案": f"方案{best_scheme}",
                    "方案A评分": score_a,
                    "方案B评分": score_b,
                    "方案C评分": score_c,
                    "综合评分": max_score
                })

        # 排序
        results["方案A部分匹配"].sort(key=lambda x: x["评分"]["分数"], reverse=True)
        results["方案B部分匹配"].sort(key=lambda x: x["评分"]["分数"], reverse=True)
        results["方案C部分匹配"].sort(key=lambda x: x["评分"]["分数"], reverse=True)
        results["高相关推荐"].sort(key=lambda x: x["综合评分"], reverse=True)

        # 统计
        results["统计信息"] = {
            "方案A部分匹配数": len(results["方案A部分匹配"]),
            "方案B部分匹配数": len(results["方案B部分匹配"]),
            "方案C部分匹配数": len(results["方案C部分匹配"]),
            "高相关推荐数": len(results["高相关推荐"])
        }

        return results

    def save_and_print(self, results: dict[str, Any], output_file: str):
        """保存并打印结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {output_file}\n")

        print("="*80)
        print("三个检索方案宽松匹配分析报告")
        print("="*80)

        for scheme_key in ["方案A部分匹配", "方案B部分匹配", "方案C部分匹配"]:
            scheme_name = scheme_key.replace("部分匹配", "")
            print(f"\n【{scheme_name}】部分匹配结果 (分数≥6)")
            print(f"匹配数量: {len(results[scheme_key])} 个")

            for i, p in enumerate(results[scheme_key][:10], 1):
                print(f"\n{i}. {p['公开号']} - {p['标题'][:50]}")
                print(f"   申请日: {p['申请日']}, 早于目标专利: {p['早于目标天数']}天")
                print(f"   评分: {p['评分']['分数']}/{p['评分']['最大分数']} ({p['评分']['匹配率']})")
                print(f"   匹配组: {', '.join(p['评分']['匹配组'])}")

        print("\n" + "="*80)
        print("【高相关推荐】任一方案分数≥10的专利")
        print("="*80)

        for i, p in enumerate(results["高相关推荐"][:15], 1):
            print(f"\n{i}. {p['公开号']} - {p['标题'][:60]}")
            print(f"   申请日: {p['申请日']}, 早于目标专利: {p['早于目标天数']}天, 申请人: {p['申请人']}")
            print(f"   综合评分: {p['综合评分']}, 最佳方案: {p['最佳方案']}")
            print(f"   方案A: {p['方案A评分']['分数']}分 | 方案B: {p['方案B评分']['分数']}分 | 方案C: {p['方案C评分']['分数']}分")


def main():
    json_file = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/检索结果_全部分析_20260202_170946.json"
    output_file = "/Users/xujian/Athena工作平台/data/patents_verify/search_schemes_flexible_analysis_201921401279.9.json"

    analyzer = FlexiblePatentSearchAnalyzer(json_file)
    results = analyzer.analyze_with_scores()
    analyzer.save_and_print(results, output_file)


if __name__ == "__main__":
    main()
