"""
数据库查询优化模块

目标: 优化数据库查询性能，减少慢查询

优化策略:
1. 慢查询分析 - 识别性能瓶颈
2. 索引优化 - 添加合适的索引
3. 查询缓存 - 缓存常用查询结果
4. 批量操作 - 减少往返次数
5. N+1查询消除 - 使用JOIN或预加载

Author: Athena Team
Date: 2026-04-24
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


@dataclass
class QueryMetrics:
    """查询指标"""
    sql: str
    execution_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    rows_affected: int = 0
    last_executed: float = field(default_factory=time.time)

    def add_execution(self, duration_ms: float, rows: int = 0):
        """添加执行记录"""
        self.execution_count += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.execution_count
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.rows_affected += rows
        self.last_executed = time.time()


@dataclass
class SlowQuery:
    """慢查询"""
    sql: str
    duration_ms: float
    timestamp: float
    rows_affected: int
    suggested_index: Optional[str] = None
    optimization_hint: Optional[str] = None


class QueryAnalyzer:
    """查询分析器"""

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self._query_metrics: Dict[str, QueryMetrics] = {}
        self._slow_queries: List[SlowQuery] = []

    def analyze_query(self, sql: str, duration_ms: float, rows: int = 0) -> Dict[str, Any]:
        """分析查询性能"""
        # 获取或创建查询指标
        query_key = self._normalize_sql(sql)
        if query_key not in self._query_metrics:
            self._query_metrics[query_key] = QueryMetrics(sql=query_key)

        metrics = self._query_metrics[query_key]
        metrics.add_execution(duration_ms, rows)

        # 检查是否为慢查询
        is_slow = duration_ms > self.slow_query_threshold_ms
        if is_slow:
            slow_query = SlowQuery(
                sql=sql,
                duration_ms=duration_ms,
                timestamp=time.time(),
                rows_affected=rows,
                suggested_index=self._suggest_index(sql),
                optimization_hint=self._get_optimization_hint(sql),
            )
            self._slow_queries.append(slow_query)

        return {
            "is_slow": is_slow,
            "duration_ms": duration_ms,
            "threshold_ms": self.slow_query_threshold_ms,
            "metrics": metrics,
            "suggestions": self._get_optimization_suggestions(sql, duration_ms),
        }

    def _normalize_sql(self, sql: str) -> str:
        """规范化SQL（用于聚合相同查询）"""
        # 移除多余空格
        sql = re.sub(r'\s+', ' ', sql.strip())
        # 替换参数值为占位符
        sql = re.sub(r"'[^']*'", "'?'", sql)
        sql = re.sub(r'\d+', '?', sql)
        return sql

    def _suggest_index(self, sql: str) -> Optional[str]:
        """建议索引"""
        # 简单的索引建议逻辑
        if 'WHERE' in sql.upper():
            # 提取WHERE子句中的列
            match = re.search(r'WHERE\s+(\w+)\s*=', sql, re.IGNORECASE)
            if match:
                column = match.group(1)
                return f"CREATE INDEX idx_{column} ON table_name ({column})"

        return None

    def _get_optimization_hint(self, sql: str) -> Optional[str]:
        """获取优化提示"""
        sql_upper = sql.upper()

        # 检查SELECT *
        if 'SELECT *' in sql_upper:
            return "避免使用SELECT *，只查询需要的列"

        # 检查LIKE查询
        if 'LIKE' in sql_upper and sql_upper.startswith("LIKE '%"):
            return "前导通配符会导致全表扫描，考虑使用全文索引"

        # 检查子查询
        if 'IN (SELECT' in sql_upper:
            return "考虑使用JOIN替代子查询"

        # 检查ORDER BY
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            return "ORDER BY没有LIMIT可能导致大量排序"

        return None

    def _get_optimization_suggestions(self, sql: str, duration_ms: float) -> List[str]:
        """获取优化建议列表"""
        suggestions = []

        if duration_ms > 200:
            suggestions.append("查询较慢，考虑添加索引")

        if sql.count('JOIN') > 3:
            suggestions.append("多表JOIN可能影响性能，考虑分步查询")

        if 'OR' in sql.upper() and 'WHERE' in sql.upper():
            suggestions.append("OR条件可能导致索引失效，考虑使用UNION")

        return suggestions

    def get_slow_queries(self, limit: int = 10) -> List[SlowQuery]:
        """获取慢查询列表"""
        return sorted(self._slow_queries, key=lambda x: x.duration_ms, reverse=True)[:limit]

    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计"""
        total_queries = sum(m.execution_count for m in self._query_metrics.values())
        total_slow_queries = len(self._slow_queries)

        return {
            "total_queries": total_queries,
            "slow_queries": total_slow_queries,
            "slow_query_rate": total_slow_queries / total_queries if total_queries > 0 else 0,
            "unique_queries": len(self._query_metrics),
        }


class QueryOptimizer:
    """查询优化器"""

    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self._query_cache: Dict[str, Tuple[Any, float]] = {}

    async def execute_query(
        self,
        sql: str,
        params: Optional[tuple] = None,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> Dict[str, Any]:
        """执行查询（带优化）"""
        start_time = time.time()

        # 检查缓存
        cache_key = self._generate_cache_key(sql, params)
        if use_cache and cache_key in self._query_cache:
            result, expiry = self._query_cache[cache_key]
            if time.time() < expiry:
                duration_ms = (time.time() - start_time) * 1000
                return {
                    "success": True,
                    "result": result,
                    "cached": True,
                    "duration_ms": duration_ms,
                }

        # 执行查询（模拟）
        result = await self._simulate_query_execution(sql, params)
        duration_ms = (time.time() - start_time) * 1000

        # 分析查询性能
        analysis = self.analyzer.analyze_query(sql, duration_ms)

        # 缓存结果
        if use_cache and not analysis.get("is_slow"):
            expiry = time.time() + cache_ttl
            self._query_cache[cache_key] = (result, expiry)

        return {
            "success": True,
            "result": result,
            "cached": False,
            "duration_ms": duration_ms,
            "analysis": analysis,
        }

    async def execute_batch(
        self,
        queries: List[Tuple[str, Optional[tuple]]]
    ) -> List[Dict[str, Any]]:
        """批量执行查询"""
        tasks = [self.execute_query(sql, params) for sql, params in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def execute_optimized_join(
        self,
        tables: List[str],
        conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行优化的JOIN查询"""
        # 构建优化的JOIN查询
        join_clause = " ".join([f"JOIN {table}" for table in tables[1:]])
        where_clause = " AND ".join([f"{k} = '{v}'" for k, v in conditions.items()])

        sql = f"""
        SELECT t1.*, t2.*, t3.*
        FROM {tables[0]} t1
        {join_clause}
        ON t1.id = t2.id AND t2.id = t3.id
        WHERE {where_clause}
        """

        return await self.execute_query(sql)

    async def _simulate_query_execution(self, sql: str, params: Optional[tuple]) -> Any:
        """模拟查询执行"""
        # 根据查询类型模拟不同的延迟
        sql_upper = sql.upper()

        if 'JOIN' in sql_upper:
            await asyncio.sleep(0.05)  # JOIN查询：50ms
        elif 'WHERE' in sql_upper:
            await asyncio.sleep(0.02)  # 带WHERE的查询：20ms
        else:
            await asyncio.sleep(0.01)  # 简单查询：10ms

        return {
            "rows": [],
            "row_count": 0,
            "sql": sql,
        }

    def _generate_cache_key(self, sql: str, params: Optional[tuple]) -> str:
        """生成缓存键"""
        import hashlib
        key_str = f"{sql}:{params}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def eliminate_n_plus_1(
        self,
        parent_query: str,
        child_query_template: str,
        parent_ids: List[Any]
    ) -> str:
        """
        消除N+1查询问题

        将：
        1. SELECT * FROM parent WHERE ...
        2. FOR EACH parent: SELECT * FROM child WHERE parent_id = ?

        改为：
        1. SELECT * FROM parent WHERE ...
        2. SELECT * FROM child WHERE parent_id IN (...)
        """
        # 构建优化的子查询
        ids_str = ", ".join([f"'{id}'" for id in parent_ids[:100]])  # 限制100个
        optimized_query = child_query_template.replace(
            "parent_id = ?",
            f"parent_id IN ({ids_str})"
        )

        return optimized_query

    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        slow_queries = self.analyzer.get_slow_queries(limit=20)
        query_stats = self.analyzer.get_query_stats()

        return {
            "slow_queries": [
                {
                    "sql": sq.sql[:100] + "..." if len(sq.sql) > 100 else sq.sql,
                    "duration_ms": sq.duration_ms,
                    "suggested_index": sq.suggested_index,
                    "optimization_hint": sq.optimization_hint,
                }
                for sq in slow_queries
            ],
            "query_stats": query_stats,
            "cache_stats": {
                "cached_queries": len(self._query_cache),
                "cache_hit_rate": 0.0,  # 需要额外跟踪
            },
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 分析慢查询
        slow_queries = self.analyzer.get_slow_queries(limit=10)
        if slow_queries:
            recommendations.append(f"发现{len(slow_queries)}个慢查询，建议添加索引或优化SQL")

        # 检查缓存效率
        if len(self._query_cache) > 1000:
            recommendations.append("查询缓存较大，考虑实施TTL策略")

        return recommendations


# 使用示例
async def example_query_optimization():
    """查询优化示例"""

    optimizer = QueryOptimizer()

    # 执行一些查询
    queries = [
        ("SELECT * FROM users WHERE id = 1", None),
        ("SELECT * FROM patents WHERE status = 'active'", None),
        ("SELECT * FROM users u JOIN patents p ON u.id = p.user_id", None),
        ("SELECT * FROM analytics WHERE date > '2026-01-01'", None),
    ]

    start = time.time()
    results = await optimizer.execute_batch(queries)
    total_duration = (time.time() - start) * 1000

    # 获取优化报告
    report = optimizer.get_optimization_report()

    return {
        "queries_executed": len(queries),
        "total_duration_ms": total_duration,
        "avg_duration_ms": total_duration / len(queries),
        "optimization_report": report,
    }


if __name__ == "__main__":
    # 测试查询优化
    async def test():
        print("测试数据库查询优化...")
        result = await example_query_optimization()
        print(f"结果: {result}")

    asyncio.run(test())
