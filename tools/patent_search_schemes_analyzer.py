#!/usr/bin/env python3
"""
专利检索方案分析器
基于已有JSON数据模拟三个检索方案的分析
"""

import json
from datetime import datetime
from typing import Any


class PatentSearchSchemeAnalyzer:
    """专利检索方案分析器"""

    def __init__(self, json_file: str):
        """
        初始化分析器

        Args:
            json_file: 专利数据JSON文件路径
        """
        self.json_file = json_file
        self.patents = self.load_patents()

    def load_patents(self) -> list[dict[str, Any]]:
        """加载专利数据"""
        with open(self.json_file, encoding='utf-8') as f:
            data = json.load(f)
        return data

    def check_scheme_a(self, patent: dict[str, Any]) -> bool:
        """
        方案 A（高相关度组合）匹配检查
        (包装机 OR 输送机) AND (限位板 OR 导料板 OR 护栏)
        AND (斜 OR 倾斜 OR 斜向) AND (滑轨 OR 导轨 OR 槽)
        AND (间距 OR 宽度) AND (调节 OR 调整)
        """
        text = (
            patent.get("patent_name", "") + " " +
            patent.get("abstract_preview", "")
        ).lower()

        # 排除目标专利本身
        pub_num = patent.get("publication_number", "")
        if pub_num in ["CN210456236U", "CN201921401279.9"]:
            return False

        # 检查日期
        app_date = patent.get("application_date")
        if not app_date or app_date >= 1566892800000:  # 2019-08-27
            return False

        # 分组检查
        group1 = any(kw in text for kw in ["包装机", "输送机"])
        group2 = any(kw in text for kw in ["限位板", "导料板", "护栏"])
        group3 = any(kw in text for kw in ["斜向", "倾斜", "斜轨"])
        group4 = any(kw in text for kw in ["滑轨", "导轨", "滑槽"])
        group5 = any(kw in text for kw in ["间距", "宽度"])
        group6 = any(kw in text for kw in ["调节", "调整"])

        return all([group1, group2, group3, group4, group5, group6])

    def check_scheme_b(self, patent: dict[str, Any]) -> bool:
        """
        方案 B（结构联动特征）匹配检查
        (物料限位板 OR 导板) AND (驱动 OR 电机 OR 螺杆)
        AND (纵向) AND (联动 OR 同步) AND (横向 OR 间距) AND (斜)
        """
        text = (
            patent.get("patent_name", "") + " " +
            patent.get("abstract_preview", "")
        ).lower()

        pub_num = patent.get("publication_number", "")
        if pub_num in ["CN210456236U", "CN201921401279.9"]:
            return False

        app_date = patent.get("application_date")
        if not app_date or app_date >= 1566892800000:
            return False

        group1 = any(kw in text for kw in ["物料限位板", "导板"])
        group2 = any(kw in text for kw in ["驱动", "电机", "螺杆"])
        group3 = "纵向" in text
        group4 = any(kw in text for kw in ["联动", "同步"])
        group5 = any(kw in text for kw in ["横向", "间距"])
        group6 = "斜" in text

        return all([group1, group2, group3, group4, group5, group6])

    def check_scheme_c(self, patent: dict[str, Any]) -> bool:
        """
        方案 C（分类号限制）匹配检查
        IPC:(B65G21/20) AND (斜 OR 斜向 OR 倾斜)
        AND (调节 OR 自动) AND (限位 OR 导料 OR 护栏)
        """
        text = (
            patent.get("patent_name", "") + " " +
            patent.get("abstract_preview", "")
        ).lower()

        pub_num = patent.get("publication_number", "")
        if pub_num in ["CN210456236U", "CN201921401279.9"]:
            return False

        app_date = patent.get("application_date")
        if not app_date or app_date >= 1566892800000:
            return False

        ipc = patent.get("ipc_main_class", "")
        group1 = "B65G21/20" in ipc or ipc.startswith("B65G21")
        group2 = any(kw in text for kw in ["斜向", "倾斜", "斜轨"])
        group3 = any(kw in text for kw in ["调节", "自动"])
        group4 = any(kw in text for kw in ["限位", "导料", "护栏"])

        return all([group1, group2, group3, group4])

    def analyze_all_schemes(self) -> dict[str, Any]:
        """分析所有检索方案"""
        results = {
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "方案A": {
                "名称": "高相关度组合",
                "描述": "(包装机 OR 输送机) AND (限位板 OR 导料板 OR 护栏) AND (斜 OR 倾斜 OR 斜向) AND (滑轨 OR 导轨 OR 槽) AND (间距 OR 宽度) AND (调节 OR 调整)",
                "匹配结果": []
            },
            "方案B": {
                "名称": "结构联动特征",
                "描述": "(物料限位板 OR 导板) AND (驱动 OR 电机 OR 螺杆) AND (纵向) AND (联动 OR 同步) AND (横向 OR 间距) AND (斜)",
                "匹配结果": []
            },
            "方案C": {
                "名称": "分类号限制",
                "描述": "IPC:(B65G21/20) AND (斜 OR 斜向 OR 倾斜) AND (调节 OR 自动) AND (限位 OR 导料 OR 护栏)",
                "匹配结果": []
            },
            "合并结果": []
        }

        # 执行方案A
        scheme_a_patents = []
        for patent in self.patents:
            if self.check_scheme_a(patent):
                scheme_a_patents.append({
                    "申请号": patent.get("application_number"),
                    "公开号": patent.get("publication_number"),
                    "标题": patent.get("patent_name"),
                    "摘要": patent.get("abstract_preview", "")[:200],
                    "申请日": self._format_date(patent.get("application_date")),
                    "IPC分类号": patent.get("ipc_main_class"),
                    "申请人": patent.get("applicant")
                })
        results["方案A"]["匹配结果"] = scheme_a_patents

        # 执行方案B
        scheme_b_patents = []
        for patent in self.patents:
            if self.check_scheme_b(patent):
                scheme_b_patents.append({
                    "申请号": patent.get("application_number"),
                    "公开号": patent.get("publication_number"),
                    "标题": patent.get("patent_name"),
                    "摘要": patent.get("abstract_preview", "")[:200],
                    "申请日": self._format_date(patent.get("application_date")),
                    "IPC分类号": patent.get("ipc_main_class"),
                    "申请人": patent.get("applicant")
                })
        results["方案B"]["匹配结果"] = scheme_b_patents

        # 执行方案C
        scheme_c_patents = []
        for patent in self.patents:
            if self.check_scheme_c(patent):
                scheme_c_patents.append({
                    "申请号": patent.get("application_number"),
                    "公开号": patent.get("publication_number"),
                    "标题": patent.get("patent_name"),
                    "摘要": patent.get("abstract_preview", "")[:200],
                    "申请日": self._format_date(patent.get("application_date")),
                    "IPC分类号": patent.get("ipc_main_class"),
                    "申请人": patent.get("applicant")
                })
        results["方案C"]["匹配结果"] = scheme_c_patents

        # 合并去重
        all_results = {}
        for scheme_key in ["方案A", "方案B", "方案C"]:
            for patent in results[scheme_key]["匹配结果"]:
                pub_num = patent.get("公开号")
                if pub_num not in all_results:
                    all_results[pub_num] = {
                        **patent,
                        "来源方案": []
                    }
                all_results[pub_num]["来源方案"].append(scheme_key)

        results["合并结果"] = list(all_results.values())

        # 按申请日排序
        results["合并结果"].sort(
            key=lambda x: datetime.strptime(x["申请日"], "%Y-%m-%d") if x["申请日"] != "未知" else datetime.now(),
            reverse=False
        )

        # 统计信息
        results["统计信息"] = {
            "方案A匹配数": len(scheme_a_patents),
            "方案B匹配数": len(scheme_b_patents),
            "方案C匹配数": len(scheme_c_patents),
            "合并去重后总数": len(results["合并结果"]),
            "三方案共同匹配数": len([p for p in results["合并结果"] if len(p["来源方案"]) == 3]),
            "两方案共同匹配数": len([p for p in results["合并结果"] if len(p["来源方案"]) == 2]),
            "仅单方案匹配数": len([p for p in results["合并结果"] if len(p["来源方案"]) == 1])
        }

        return results

    def _format_date(self, timestamp: int) -> str:
        """格式化日期"""
        if not timestamp:
            return "未知"
        try:
            return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
        except Exception:
            return "未知"

    def save_results(self, results: dict[str, Any], output_file: str):
        """保存结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {output_file}")

    def print_summary(self, results: dict[str, Any]):
        """打印分析摘要"""
        print("\n" + "="*80)
        print("三个检索方案分析报告")
        print("="*80)

        print("\n【方案A】高相关度组合")
        print("检索式: (包装机 OR 输送机) AND (限位板 OR 导料板 OR 护栏) AND (斜 OR 倾斜 OR 斜向) AND (滑轨 OR 导轨 OR 槽) AND (间距 OR 宽度) AND (调节 OR 调整)")
        print(f"匹配结果: {results['统计信息']['方案A匹配数']} 个")

        if results["方案A"]["匹配结果"]:
            print("\n匹配专利:")
            for i, p in enumerate(results["方案A"]["匹配结果"][:5], 1):
                print(f"  {i}. {p['公开号']} - {p['标题'][:50]}")
                print(f"     申请日: {p['申请日']}, 申请人: {p['申请人']}")

        print("\n" + "-"*80)
        print("\n【方案B】结构联动特征")
        print("检索式: (物料限位板 OR 导板) AND (驱动 OR 电机 OR 螺杆) AND (纵向) AND (联动 OR 同步) AND (横向 OR 间距) AND (斜)")
        print(f"匹配结果: {results['统计信息']['方案B匹配数']} 个")

        if results["方案B"]["匹配结果"]:
            print("\n匹配专利:")
            for i, p in enumerate(results["方案B"]["匹配结果"][:5], 1):
                print(f"  {i}. {p['公开号']} - {p['标题'][:50]}")
                print(f"     申请日: {p['申请日']}, 申请人: {p['申请人']}")

        print("\n" + "-"*80)
        print("\n【方案C】分类号限制")
        print("检索式: IPC:(B65G21/20) AND (斜 OR 斜向 OR 倾斜) AND (调节 OR 自动) AND (限位 OR 导料 OR 护栏)")
        print(f"匹配结果: {results['统计信息']['方案C匹配数']} 个")

        if results["方案C"]["匹配结果"]:
            print("\n匹配专利:")
            for i, p in enumerate(results["方案C"]["匹配结果"][:5], 1):
                print(f"  {i}. {p['公开号']} - {p['标题'][:50]}")
                print(f"     申请日: {p['申请日']}, 申请人: {p['申请人']}")

        print("\n" + "="*80)
        print("综合分析")
        print("="*80)
        stats = results["统计信息"]
        print(f"方案A匹配数: {stats['方案A匹配数']}")
        print(f"方案B匹配数: {stats['方案B匹配数']}")
        print(f"方案C匹配数: {stats['方案C匹配数']}")
        print(f"合并去重后总数: {stats['合并去重后总数']}")
        print(f"三方案共同匹配数: {stats['三方案共同匹配数']}")
        print(f"两方案共同匹配数: {stats['两方案共同匹配数']}")
        print(f"仅单方案匹配数: {stats['仅单方案匹配数']}")

        print("\n【推荐证据】合并去重后的结果:")
        for i, p in enumerate(results["合并结果"][:10], 1):
            schemes = ", ".join(p["来源方案"])
            print(f"{i}. {p['公开号']} - {p['标题'][:50]}")
            print(f"   申请日: {p['申请日']}, 来源方案: [{schemes}]")


def main():
    """主函数"""
    # 数据文件路径
    json_file = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/检索结果_全部分析_20260202_170946.json"
    output_file = "/Users/xujian/Athena工作平台/data/patents_verify/search_schemes_analysis_201921401279.9.json"

    # 创建分析器
    analyzer = PatentSearchSchemeAnalyzer(json_file)

    # 执行分析
    print(f"加载数据: {json_file}")
    results = analyzer.analyze_all_schemes()

    # 打印摘要
    analyzer.print_summary(results)

    # 保存结果
    analyzer.save_results(results, output_file)


if __name__ == "__main__":
    main()
