#!/usr/bin/env python3
"""
数据库性能测试和分析
Database Performance Testing and Analysis
"""

import json
import sqlite3
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class DatabasePerformanceAnalyzer:
    """数据库性能分析器"""

    def __init__(self):
        self.results = {}

    def analyze_database_schema(self, db_path: str) -> dict[str, Any]:
        """分析数据库结构"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            schema_info = {
                "database_path": db_path,
                "file_size_mb": Path(db_path).stat().st_size / (1024**2),
                "table_count": len(tables),
                "tables": {},
            }

            for table in tables:
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()

                # 获取记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]

                # 获取索引信息
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = cursor.fetchall()

                schema_info["tables"][table] = {
                    "column_count": len(columns),
                    "row_count": row_count,
                    "index_count": len(indexes),
                    "columns": [
                        {"name": col[1], "type": col[2], "primary_key": col[5]} for col in columns
                    ],
                    "indexes": [{"name": idx[1], "unique": idx[2]} for idx in indexes],
                }

            conn.close()
            return schema_info

        except Exception as e:
            return {"error": str(e)}

    def test_query_performance(self, db_path: str, table_name: str) -> dict[str, Any]:
        """测试查询性能"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 基础查询测试
            queries = [
                {
                    "name": "count_all",
                    "sql": f"SELECT COUNT(*) FROM {table_name}",
                    "description": "统计总记录数",
                },
                {
                    "name": "select_first_10",
                    "sql": f"SELECT * FROM {table_name} LIMIT 10",
                    "description": "获取前10条记录",
                },
                {
                    "name": "select_with_order",
                    "sql": f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 10",
                    "description": "按ID倒序获取前10条记录",
                },
            ]

            # 检查是否有文本字段可以进行搜索测试
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            text_columns = [col[1] for col in columns if "TEXT" in col[2].upper()]

            if text_columns:
                queries.append(
                    {
                        "name": "text_search",
                        "sql": f"SELECT * FROM {table_name} WHERE {text_columns[0]} LIKE '%test%' LIMIT 10",
                        "description": f"在{text_columns[0]}字段中搜索",
                    }
                )

            query_results = {}

            for query_info in queries:
                times = []
                errors = []

                # 执行10次取平均值
                for _i in range(10):
                    try:
                        start_time = time.time()
                        cursor.execute(query_info["sql"])
                        result = cursor.fetchall()
                        query_time = time.time() - start_time
                        times.append(query_time)
                    except Exception as e:
                        errors.append(str(e))

                if times:
                    query_results[query_info["name"]] = {
                        "sql": query_info["sql"],
                        "description": query_info["description"],
                        "avg_time_ms": statistics.mean(times) * 1000,
                        "min_time_ms": min(times) * 1000,
                        "max_time_ms": max(times) * 1000,
                        "std_dev_ms": statistics.stdev(times) * 1000 if len(times) > 1 else 0,
                        "result_count": len(result) if "result" in locals() else 0,
                        "success_rate": len(times) / 10,
                    }
                else:
                    query_results[query_info["name"]] = {
                        "sql": query_info["sql"],
                        "description": query_info["description"],
                        "error": "所有查询都失败了",
                        "errors": errors,
                    }

            conn.close()
            return {"table": table_name, "query_performance": query_results}

        except Exception as e:
            return {"error": str(e)}

    def test_write_performance(
        self, db_path: str, table_name: str = "performance_test"
    ) -> dict[str, Any]:
        """测试写入性能"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 创建测试表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    number INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 单条插入测试
            single_insert_times = []
            for i in range(100):
                start_time = time.time()
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} (data, number)
                    VALUES (?, ?)
                """,
                    (f"test_data_{i}", i),
                )
                conn.commit()
                insert_time = time.time() - start_time
                single_insert_times.append(insert_time)

            # 批量插入测试
            batch_sizes = [10, 50, 100, 500]
            batch_results = {}

            for batch_size in batch_sizes:
                start_time = time.time()

                cursor.executemany(
                    f"""
                    INSERT INTO {table_name} (data, number)
                    VALUES (?, ?)
                """,
                    [(f"batch_data_{i}", i) for i in range(batch_size)],
                )

                conn.commit()
                batch_time = time.time() - start_time

                batch_results[f"batch_{batch_size}"] = {
                    "total_time_ms": batch_time * 1000,
                    "avg_time_per_record_ms": (batch_time * 1000) / batch_size,
                    "records_per_second": batch_size / batch_time,
                }

            # 更新性能测试
            update_times = []
            for i in range(50):
                start_time = time.time()
                cursor.execute(
                    f"""
                    UPDATE {table_name}
                    SET data = ? WHERE id = ?
                """,
                    (f"updated_data_{i}", i + 1),
                )
                conn.commit()
                update_time = time.time() - start_time
                update_times.append(update_time)

            # 删除性能测试
            delete_times = []
            for i in range(50):
                start_time = time.time()
                cursor.execute(
                    f"""
                    DELETE FROM {table_name}
                    WHERE id = ?
                """,
                    (i + 101,),
                )  # 删除之前插入的记录
                conn.commit()
                delete_time = time.time() - start_time
                delete_times.append(delete_time)

            # 清理测试表
            cursor.execute(f"DROP TABLE {table_name}")
            conn.commit()
            conn.close()

            return {
                "table": table_name,
                "single_insert": {
                    "avg_time_ms": statistics.mean(single_insert_times) * 1000,
                    "min_time_ms": min(single_insert_times) * 1000,
                    "max_time_ms": max(single_insert_times) * 1000,
                    "total_records": len(single_insert_times),
                },
                "batch_insert": batch_results,
                "update": {
                    "avg_time_ms": statistics.mean(update_times) * 1000,
                    "min_time_ms": min(update_times) * 1000,
                    "max_time_ms": max(update_times) * 1000,
                    "total_records": len(update_times),
                },
                "delete": {
                    "avg_time_ms": statistics.mean(delete_times) * 1000,
                    "min_time_ms": min(delete_times) * 1000,
                    "max_time_ms": max(delete_times) * 1000,
                    "total_records": len(delete_times),
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_optimization_recommendations(
        self,
        schema_info: dict[str, Any],
        query_performance: dict[str, Any],
        write_performance: dict[str, Any],
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 检查表大小和索引
        if "tables" in schema_info:
            for table_name, table_info in schema_info["tables"].items():
                row_count = table_info.get("row_count", 0)
                index_count = table_info.get("index_count", 0)

                if row_count > 10000 and index_count == 0:
                    recommendations.append(
                        f"🔍 表 {table_name} 有 {row_count} 行记录但无索引，建议添加适当的索引来提升查询性能"
                    )

                if row_count > 100000 and index_count < 2:
                    recommendations.append(
                        f"🚀 表 {table_name} 是大型表({row_count}行)，建议添加更多索引以优化查询"
                    )

        # 检查查询性能
        if "query_performance" in query_performance:
            for query_name, query_info in query_performance["query_performance"].items():
                if "avg_time_ms" in query_info and query_info["avg_time_ms"] > 100:
                    recommendations.append(
                        f"⚡ 查询 '{query_name}' 平均耗时 {query_info['avg_time_ms']:.2f}ms，建议优化或添加索引"
                    )

        # 检查写入性能
        if "batch_insert" in write_performance:
            single_avg = write_performance["single_insert"]["avg_time_ms"]
            batch_100_avg = write_performance["batch_insert"]["batch_100"]["avg_time_per_record_ms"]

            if batch_100_avg < single_avg * 0.5:
                recommendations.append(
                    f"💾 批量写入性能显著优于单条写入({batch_100_avg:.2f}ms vs {single_avg:.2f}ms)，建议使用批量操作"
                )

        # 通用建议
        recommendations.extend(
            [
                "🔧 定期执行 VACUUM 命令清理数据库碎片",
                "📊 监控数据库文件大小，避免过度增长",
                "🛡️ 对重要表添加外键约束确保数据完整性",
                "📈 定期分析查询计划，优化慢查询",
            ]
        )

        return recommendations

    def analyze_all_databases(self) -> dict[str, Any]:
        """分析所有主要数据库"""
        main_databases = [
            "/Users/xujian/Athena工作平台/data/xiaonuo_knowledge.db",
            "/Users/xujian/Athena工作平台/data/online_learning.db",
            "/Users/xujian/Athena工作平台/data/user_preferences.db",
        ]

        all_results = {"analysis_timestamp": datetime.now().isoformat(), "databases": {}}

        for db_path in main_databases:
            if Path(db_path).exists():
                print(f"🗄️ 分析数据库: {Path(db_path).name}")

                # 结构分析
                schema_info = self.analyze_database_schema(db_path)

                # 选择主要表进行性能测试
                if "tables" in schema_info and schema_info["tables"]:
                    main_table = max(
                        schema_info["tables"].items(),
                        key=lambda x: x[1]["row_count"] if "row_count" in x[1] else 0,
                    )[0]

                    query_performance = self.test_query_performance(db_path, main_table)
                    write_performance = self.test_write_performance(db_path)

                    # 生成优化建议
                    recommendations = self.generate_optimization_recommendations(
                        schema_info, query_performance, write_performance
                    )

                    all_results["databases"][Path(db_path).name] = {
                        "schema_analysis": schema_info,
                        "query_performance": query_performance,
                        "write_performance": write_performance,
                        "optimization_recommendations": recommendations,
                    }
                else:
                    all_results["databases"][Path(db_path).name] = {
                        "schema_analysis": schema_info,
                        "error": "无可用表进行性能测试",
                    }
            else:
                all_results["databases"][Path(db_path).name] = {"error": "数据库文件不存在"}

        return all_results

    def save_results(self, results: dict[str, Any], filename: str = None):
        """保存分析结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"database_performance_analysis_{timestamp}.json"

        reports_dir = Path("/Users/xujian/Athena工作平台/tests/reports")
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / filename
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 数据库性能分析报告已保存: {report_file}")
        return str(report_file)


def main():
    """主函数"""
    print("🚀 开始数据库性能分析...")
    print("=" * 60)

    analyzer = DatabasePerformanceAnalyzer()

    # 分析所有数据库
    results = analyzer.analyze_all_databases()

    # 保存结果
    report_file = analyzer.save_results(results)

    # 显示优化建议摘要
    print("\n" + "=" * 60)
    print("🎯 数据库优化建议摘要")
    print("=" * 60)

    total_recommendations = 0
    for db_name, db_result in results["databases"].items():
        if "optimization_recommendations" in db_result:
            recommendations = db_result["optimization_recommendations"]
            total_recommendations += len(recommendations)

            print(f"\n📊 {db_name}:")
            for rec in recommendations[:3]:  # 显示前3个建议
                print(f"  {rec}")
            if len(recommendations) > 3:
                print(f"  ... 还有 {len(recommendations) - 3} 个建议")

    if total_recommendations == 0:
        print("✅ 所有数据库性能表现良好，无特殊优化建议")

    print(f"\n📋 详细报告: {report_file}")


if __name__ == "__main__":
    main()
