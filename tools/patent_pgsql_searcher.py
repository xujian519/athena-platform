#!/usr/bin/env python3
"""
PostgreSQL中国专利数据库检索脚本
执行三维交集检索法的三个检索方案
"""

import json
from datetime import datetime
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


class PatentDBSearcher:
    """PostgreSQL专利数据库检索器"""

    def __init__(self, db_config: dict[str, str]):
        """
        初始化数据库连接

        Args:
            db_config: 数据库配置
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'patents'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', ''),
                cursor_factory=RealDictCursor
            )
            self.cursor = self.conn.cursor()
            print(f"成功连接到数据库: {self.db_config.get('database')}")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")

    def search_patents(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        执行专利检索

        Args:
            query: SQL查询语句
            limit: 返回结果数量限制

        Returns:
            检索结果列表
        """
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            print(f"检索到 {len(results)} 条结果")
            return [dict(row) for row in results]
        except Exception as e:
            print(f"查询执行失败: {e}")
            return []

    def build_search_query(self, scheme: str, scheme_name: str) -> str:
        """
        构建检索查询

        Args:
            scheme: 检索方案 (A, B, C)
            scheme_name: 方案名称

        Returns:
            SQL查询语句
        """
        # 基础查询结构
        base_query = """
        SELECT
            application_number AS 申请号,
            publication_number AS 公开号,
            patent_name AS 标题,
            applicant AS 申请人,
            application_date AS 申请日,
            publication_date AS 公开日,
            ipc_main_class AS IPC主分类,
            abstract_preview AS 摘要,
            patent_type AS 专利类型
        FROM patents
        WHERE """

        # 目标专利申请日之前
        date_filter = " application_date < TO_TIMESTAMP('2019-08-27', 'YYYY-MM-DD') "

        if scheme == "A":
            # 方案 A（高相关度组合）
            # (包装机 OR 输送机) AND (限位板 OR 导料板 OR 护栏) AND (斜 OR 倾斜 OR 斜向)
            # AND (滑轨 OR 导轨 OR 槽) AND (间距 OR 宽度) AND (调节 OR 调整)
            where_clause = f"""{date_filter}
                AND (
                    (patent_name ILIKE '%包装机%' OR abstract_preview ILIKE '%包装机%' OR
                     patent_name ILIKE '%输送机%' OR abstract_preview ILIKE '%输送机%')
                )
                AND (
                    (patent_name ILIKE '%限位板%' OR abstract_preview ILIKE '%限位板%' OR
                     patent_name ILIKE '%导料板%' OR abstract_preview ILIKE '%导料板%' OR
                     patent_name ILIKE '%护栏%' OR abstract_preview ILIKE '%护栏%')
                )
                AND (
                    (patent_name ILIKE '%斜向%' OR abstract_preview ILIKE '%斜向%' OR
                     patent_name ILIKE '%倾斜%' OR abstract_preview ILIKE '%倾斜%' OR
                     patent_name ILIKE '%斜轨%' OR abstract_preview ILIKE '%斜轨%')
                )
                AND (
                    (patent_name ILIKE '%滑轨%' OR abstract_preview ILIKE '%滑轨%' OR
                     patent_name ILIKE '%导轨%' OR abstract_preview ILIKE '%导轨%' OR
                     patent_name ILIKE '%滑槽%' OR abstract_preview ILIKE '%滑槽%')
                )
                AND (
                    (patent_name ILIKE '%间距%' OR abstract_preview ILIKE '%间距%' OR
                     patent_name ILIKE '%宽度%' OR abstract_preview ILIKE '%宽度%')
                )
                AND (
                    (patent_name ILIKE '%调节%' OR abstract_preview ILIKE '%调节%' OR
                     patent_name ILIKE '%调整%' OR abstract_preview ILIKE '%调整%')
                )
                AND publication_number NOT IN ('CN210456236U', 'CN201921401279.9')
            """

        elif scheme == "B":
            # 方案 B（结构联动特征）
            # (物料限位板 OR 导板) AND (驱动 OR 电机 OR 螺杆) AND (纵向)
            # AND (联动 OR 同步) AND (横向 OR 间距) AND (斜)
            where_clause = f"""{date_filter}
                AND (
                    (patent_name ILIKE '%物料限位板%' OR abstract_preview ILIKE '%物料限位板%' OR
                     patent_name ILIKE '%导板%' OR abstract_preview ILIKE '%导板%')
                )
                AND (
                    (patent_name ILIKE '%驱动%' OR abstract_preview ILIKE '%驱动%' OR
                     patent_name ILIKE '%电机%' OR abstract_preview ILIKE '%电机%' OR
                     patent_name ILIKE '%螺杆%' OR abstract_preview ILIKE '%螺杆%')
                )
                AND (
                    (patent_name ILIKE '%纵向%' OR abstract_preview ILIKE '%纵向%')
                )
                AND (
                    (patent_name ILIKE '%联动%' OR abstract_preview ILIKE '%联动%' OR
                     patent_name ILIKE '%同步%' OR abstract_preview ILIKE '%同步%')
                )
                AND (
                    (patent_name ILIKE '%横向%' OR abstract_preview ILIKE '%横向%' OR
                     patent_name ILIKE '%间距%' OR abstract_preview ILIKE '%间距%')
                )
                AND (
                    (patent_name ILIKE '%斜%' OR abstract_preview ILIKE '%斜%')
                )
                AND publication_number NOT IN ('CN210456236U', 'CN201921401279.9')
            """

        elif scheme == "C":
            # 方案 C（分类号限制）
            # IPC:(B65G21/20) AND (斜 OR 斜向 OR 倾斜) AND (调节 OR 自动) AND (限位 OR 导料 OR 护栏)
            where_clause = f"""{date_filter}
                AND ipc_main_class LIKE 'B65G21/20%'
                AND (
                    (patent_name ILIKE '%斜向%' OR abstract_preview ILIKE '%斜向%' OR
                     patent_name ILIKE '%倾斜%' OR abstract_preview ILIKE '%倾斜%' OR
                     patent_name ILIKE '%斜轨%' OR abstract_preview ILIKE '%斜轨%')
                )
                AND (
                    (patent_name ILIKE '%调节%' OR abstract_preview ILIKE '%调节%' OR
                     patent_name ILIKE '%自动%' OR abstract_preview ILIKE '%自动%')
                )
                AND (
                    (patent_name ILIKE '%限位%' OR abstract_preview ILIKE '%限位%' OR
                     patent_name ILIKE '%导料%' OR abstract_preview ILIKE '%导料%' OR
                     patent_name ILIKE '%护栏%' OR abstract_preview ILIKE '%护栏%')
                )
                AND publication_number NOT IN ('CN210456236U', 'CN201921401279.9')
            """

        else:
            raise ValueError(f"未知的检索方案: {scheme}")

        query = base_query + where_clause + " ORDER BY application_date DESC LIMIT 100"
        return query

    def execute_all_schemes(self) -> dict[str, Any]:
        """
        执行所有检索方案

        Returns:
            所有方案的检索结果
        """
        results = {
            "检索时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "目标专利申请日": "2019-08-27",
            "方案A": {"名称": "高相关度组合", "结果": []},
            "方案B": {"名称": "结构联动特征", "结果": []},
            "方案C": {"名称": "分类号限制", "结果": []},
            "合并去重结果": []
        }

        # 执行方案A
        print("\n" + "="*70)
        print("执行方案 A：高相关度组合")
        print("="*70)
        query_a = self.build_search_query("A", "高相关度组合")
        print(f"查询语句预览:\n{query_a[:500]}...")
        results["方案A"]["结果"] = self.search_patents(query_a)
        results["方案A"]["查询语句"] = query_a
        print(f"方案 A 检索到 {len(results['方案A']['结果'])} 条结果")

        # 执行方案B
        print("\n" + "="*70)
        print("执行方案 B：结构联动特征")
        print("="*70)
        query_b = self.build_search_query("B", "结构联动特征")
        print(f"查询语句预览:\n{query_b[:500]}...")
        results["方案B"]["结果"] = self.search_patents(query_b)
        results["方案B"]["查询语句"] = query_b
        print(f"方案 B 检索到 {len(results['方案B']['结果'])} 条结果")

        # 执行方案C
        print("\n" + "="*70)
        print("执行方案 C：分类号限制")
        print("="*70)
        query_c = self.build_search_query("C", "分类号限制")
        print(f"查询语句预览:\n{query_c[:500]}...")
        results["方案C"]["结果"] = self.search_patents(query_c)
        results["方案C"]["查询语句"] = query_c
        print(f"方案 C 检索到 {len(results['方案C']['结果'])} 条结果")

        # 合并去重
        all_results = {}
        for scheme_key in ["方案A", "方案B", "方案C"]:
            for patent in results[scheme_key]["结果"]:
                pub_num = patent.get("公开号")
                if pub_num and pub_num not in all_results:
                    all_results[pub_num] = {
                        **patent,
                        "来源方案": [],
                        "匹配分数": self.calculate_relevance_score(patent)
                    }
                if pub_num:
                    all_results[pub_num]["来源方案"].append(scheme_key)

        # 转换为列表并排序
        results["合并去重结果"] = sorted(
            all_results.values(),
            key=lambda x: x["匹配分数"],
            reverse=True
        )

        # 添加统计信息
        results["统计信息"] = {
            "方案A结果数": len(results["方案A"]["结果"]),
            "方案B结果数": len(results["方案B"]["结果"]),
            "方案C结果数": len(results["方案C"]["结果"]),
            "合并去重后总数": len(results["合并去重结果"]),
            "高分专利数(≥15分)": sum(1 for p in results["合并去重结果"] if p["匹配分数"] >= 15),
            "中分专利数(≥10分)": sum(1 for p in results["合并去重结果"] if 10 <= p["匹配分数"] < 15),
        }

        return results

    def calculate_relevance_score(self, patent: dict[str, Any]) -> int:
        """
        计算相关性分数

        Args:
            patent: 专利数据

        Returns:
            相关性分数
        """
        score = 0
        text = (patent.get("标题", "") + " " + patent.get("摘要", "")).lower()

        # 核心特征词及权重
        features = {
            "斜向滑轨": 10, "斜向导轨": 10, "斜向调节": 8,
            "物料限位板": 8, "限位板": 5,
            "纵向调节": 6, "纵向位移": 5,
            "横向间距": 6, "间距调节": 5,
            "联动": 4, "同步": 4,
            "自动调节": 4,
            "滑轨": 3, "导轨": 3, "滑块": 3,
            "包装机": 4, "输送机": 3
        }

        for feature, weight in features.items():
            if feature in text:
                score += weight

        return score

    def save_results(self, results: dict[str, Any], output_file: str):
        """
        保存检索结果

        Args:
            results: 检索结果
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n检索结果已保存到: {output_file}")


def main():
    """主函数"""
    # 数据库配置 - 根据实际情况修改
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'patents',  # 修改为实际数据库名
        'user': 'postgres',     # 修改为实际用户名
        'password': ''          # 修改为实际密码
    }

    # 输出文件
    output_file = "/Users/xujian/Athena工作平台/data/patents_verify/pgsql_search_results_201921401279.9.json"

    searcher = None
    try:
        # 创建检索器
        searcher = PatentDBSearcher(db_config)

        # 连接数据库
        searcher.connect()

        # 执行所有检索方案
        results = searcher.execute_all_schemes()

        # 打印统计摘要
        print("\n" + "="*70)
        print("检索完成！统计摘要")
        print("="*70)
        for key, value in results["统计信息"].items():
            print(f"{key}: {value}")

        # 显示高分专利
        print("\n高分专利 (≥15分):")
        high_score = [p for p in results["合并去重结果"] if p["匹配分数"] >= 15]
        for i, patent in enumerate(high_score[:10], 1):
            print(f"{i}. {patent.get('公开号')} - {patent.get('标题')[:50]}")
            print(f"   分数: {patent['匹配分数']}, 申请日: {patent.get('申请日')}, "
                  f"来源: {', '.join(patent['来源方案'])}")

        # 保存结果
        searcher.save_results(results, output_file)

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        if searcher:
            searcher.disconnect()


if __name__ == "__main__":
    main()
