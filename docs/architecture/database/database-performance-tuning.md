# Athena平台数据库性能调优指南

## 1. 性能优化概述

### 1.1 优化目标
- **查询响应时间**: 95%的查询 < 100ms
- **并发处理能力**: 支持200个并发连接
- **数据导入速度**: 10,000条/秒
- **系统稳定性**: 99.9%可用性

### 1.2 性能指标监控
```sql
-- 启用查询统计
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 查看最耗时的查询
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## 2. 查询优化

### 2.1 专利搜索优化
```sql
-- 优化专利号查询
CREATE OR REPLACE FUNCTION search_patent_number(partial_number TEXT)
RETURNS TABLE(patent_id BIGINT, patent_number VARCHAR(50), title_zh TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.patent_number,
        p.title_zh
    FROM patents p
    WHERE p.patent_number ILIKE '%' || partial_number || '%'
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- 专利全文搜索函数
CREATE OR REPLACE FUNCTION search_patents_fulltext(search_text TEXT)
RETURNS TABLE(patent_id BIGINT, score REAL, title_zh TEXT, abstract_zh TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        ts_rank_cd(p.content_vector, plainto_tsquery('chinese', search_text)) as score,
        p.title_zh,
        p.abstract_zh
    FROM patents p
    WHERE p.content_vector @@ plainto_tsquery('chinese', search_text)
    ORDER BY score DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;
```

### 2.2 复杂查询优化
```sql
-- 专利分析统计视图（物化视图）
CREATE MATERIALIZED VIEW mv_patent_analysis_stats AS
SELECT
    p.patent_type,
    EXTRACT(YEAR FROM p.application_date) as year,
    COUNT(*) as patent_count,
    AVG(p.patent_value_score) as avg_value,
    COUNT(DISTINCT array_to_string(p.applicants, ',')) as unique_applicants,
    COUNT(DISTINCT array_to_string(p.inventors, ',')) as unique_inventors
FROM patents p
WHERE p.status IN ('granted', 'published')
GROUP BY p.patent_type, EXTRACT(YEAR FROM p.application_date);

-- 创建唯一索引
CREATE UNIQUE INDEX idx_mv_patent_analysis_stats_unique ON mv_patent_analysis_stats(patent_type, year);
```

### 2.3 连接查询优化
```sql
-- 专利与发明人连接优化
CREATE INDEX idx_participants_composite ON patent_participants(participant_type, participant_name, patent_id);

-- 优化的专利查询
CREATE OR REPLACE FUNCTION get_patent_with_inventors(patent_id BIGINT)
RETURNS TABLE(
    patent_info JSONB,
    inventors JSONB[],
    legal_history JSONB[]
) AS $$
BEGIN
    RETURN QUERY
    WITH patent_data AS (
        SELECT
            row_to_json(p.*) as patent_json
        FROM patents p
        WHERE p.id = $1
    ),
        inventor_data AS (
        SELECT
            json_agg(json_build_object(
                'name', participant_name,
                'country', country,
                'is_primary', is_primary
            ) ORDER BY sequence_number) as inventors_json
        FROM patent_participants pp
        WHERE pp.patent_id = $1 AND pp.participant_type = 'inventor'
        GROUP BY pp.patent_id
    ),
        legal_data AS (
        SELECT
            json_agg(json_build_object(
                'event_date', event_date,
                'event_type', event_type,
                'description', event_description
            ) ORDER BY event_date DESC) as legal_json
        FROM patent_legal_history plh
        WHERE plh.patent_id = $1
        GROUP BY plh.patent_id
    )
    SELECT
        pd.patent_json,
        COALESCE(id.inventors_json, '[]'::jsonb[]) as inventors,
        COALESCE(ld.legal_json, '[]'::jsonb[]) as legal_history
    FROM patent_data pd
    LEFT JOIN inventor_data id ON true
    LEFT JOIN legal_data ld ON true;
END;
$$ LANGUAGE plpgsql;
```

## 3. 索引优化进阶

### 3.1 部分索引
```sql
-- 只为活跃专利创建索引
CREATE INDEX CONCURRENTLY idx_patents_active_search
ON patents(LOWER(title_zh))
WHERE is_active = true;

-- 只为高价值专利创建索引
CREATE INDEX CONCURRENTLY idx_patents_high_value_ipc
ON patents(main_ipc)
WHERE patent_value_score >= 8.0;
```

### 3.2 表达式索引
```sql
-- 中文拼音搜索索引
CREATE EXTENSION IF NOT EXISTS zhparser;

-- 创建拼音搜索函数
CREATE OR REPLACE FUNCTION chinese_pinyin(text_input TEXT)
RETURNS TEXT AS $$
BEGIN
    -- 这里需要集成中文转拼音的扩展
    -- 示例实现，实际需要安装pg_jieba或类似扩展
    RETURN text_input;
END;
$$ LANGUAGE plpgsql;

-- 创建拼音索引
CREATE INDEX CONCURRENTLY idx_patents_title_pinyin
ON patents(chinese_pinyin(title_zh));
```

### 3.3 GIN索引优化
```sql
-- 为JSONB字段创建GIN索引
CREATE INDEX CONCURRENTLY idx_patents_citations_gin
ON patents USING GIN(citations jsonb_path_ops);

-- 优化数组搜索
CREATE INDEX CONCURRENTLY idx_patents_keywords_array
ON patents USING GIN(keywords) WITH (fastupdate = off);
```

## 4. 连接池配置

### 4.1 PgBouncer配置
```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
athena_patent = host=localhost port=5432 dbname=athena_patent

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# 连接池配置
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 5

# 超时设置
server_reset_query = DISCARD ALL
server_check_delay = 30
server_check_query = select 1
server_lifetime = 3600
server_idle_timeout = 600

# 日志设置
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

### 4.2 连接池脚本
```bash
#!/bin/bash
# setup_pgbouncer.sh - PgBouncer配置脚本

# 安装PgBouncer
apt-get install -y pgbouncer

# 配置文件
cp /etc/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini.bak

# 创建用户文件
echo "athena_admin = md5$(echo -n 'Ath3n@2024#PatentSecureathena_admin' | md5sum | cut -d' ' -f1)" > /etc/pgbouncer/userlist.txt
echo "athena_readonly = md5$(echo -n 'Readonly@2024#Patentathena_readonly' | md5sum | cut -d' ' -f1)" >> /etc/pgbouncer/userlist.txt

# 设置权限
chown pgbouncer:pgbouncer /etc/pgbouncer/userlist.txt
chmod 640 /etc/pgbouncer/userlist.txt

# 启动服务
systemctl enable pgbouncer
systemctl start pgbouncer

# 验证配置
psql -p 6432 -U athena_admin -h localhost -d pgbouncer -c "SHOW POOLS;"
```

## 5. 缓存策略

### 5.1 Redis缓存集成
```python
# cache_manager.py - Redis缓存管理器
import redis
import json
import pickle
from typing import Any, Optional
import hashlib

class PatentCacheManager:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=False,
            socket_keepalive=True,
            socket_keepalive_options={}
        )

    def _get_cache_key(self, key_prefix: str, identifier: str) -> str:
        """生成缓存键"""
        return f"athena:patents:{key_prefix}:{identifier}"

    def cache_patent_detail(self, patent_id: int, patent_data: dict, ttl: int = 3600):
        """缓存专利详情"""
        cache_key = self._get_cache_key("detail", str(patent_id))
        serialized_data = pickle.dumps(patent_data)
        self.redis_client.setex(cache_key, ttl, serialized_data)

    def get_patent_detail(self, patent_id: int) -> Optional[dict]:
        """获取缓存的专利详情"""
        cache_key = self._get_cache_key("detail", str(patent_id))
        cached_data = self.redis_client.get(cache_key)

        if cached_data:
            return pickle.loads(cached_data)
        return None

    def cache_search_results(self, query_hash: str, results: list, ttl: int = 1800):
        """缓存搜索结果"""
        cache_key = self._get_cache_key("search", query_hash)
        self.redis_client.setex(cache_key, ttl, json.dumps(results, ensure_ascii=False))

    def get_search_results(self, query: str) -> Optional[list]:
        """获取缓存的搜索结果"""
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_key = self._get_cache_key("search", query_hash)
        cached_results = self.redis_client.get(cache_key)

        if cached_results:
            return json.loads(cached_results)
        return None

    def invalidate_patent_cache(self, patent_id: int):
        """失效专利相关缓存"""
        patterns = [
            f"athena:patents:detail:{patent_id}",
            "athena:patents:search:*",
            "athena:patents:stats:*"
        ]

        for pattern in patterns:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
```

### 5.2 查询缓存装饰器
```python
# cache_decorators.py - 查询缓存装饰器
from functools import wraps
import hashlib
import time

def cache_query(ttl: int = 3600, key_prefix: str = "query"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_args = str(args) + str(sorted(kwargs.items()))
            query_hash = hashlib.md5(cache_args.encode('utf-8')).hexdigest()
            cache_key = f"athena:cache:{key_prefix}:{query_hash}"

            # 尝试从缓存获取
            cache_manager = PatentCacheManager()
            cached_result = cache_manager.redis_client.get(cache_key)

            if cached_result:
                return pickle.loads(cached_result)

            # 执行查询
            start_time = time.time()
            result = func(*args, **kwargs)
            query_time = time.time() - start_time

            # 缓存结果（如果查询时间超过阈值）
            if query_time > 0.1:  # 100ms
                cache_manager.redis_client.setex(
                    cache_key,
                    ttl,
                    pickle.dumps(result)
                )

            return result

        return wrapper
    return decorator

# 使用示例
@cache_query(ttl=1800, key_prefix="patent_stats")
def get_patent_statistics(date_range: str) -> dict:
    # 耗时的统计查询
    pass

@cache_query(ttl=3600, key_prefix="patent_detail")
def get_patent_with_relations(patent_id: int) -> dict:
    # 获取专利及其关联数据
    pass
```

## 6. 读写分离

### 6.1 主从复制配置
```sql
-- 在主服务器上创建复制用户
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'Replic@2024#Secure';

-- 修改pg_hba.conf允许复制连接
host replication replicator 10.0.1.0/24 md5
```

### 6.2 读写分离实现
```python
# db_router.py - 数据库路由
class DatabaseRouter:
    def __init__(self):
        self.write_db = {
            'host': 'localhost',
            'port': 5432,
            'user': 'athena_admin',
            'password': 'Ath3n@2024#PatentSecure',
            'infrastructure/infrastructure/database': 'athena_patent'
        }

        self.read_db = {
            'host': 'localhost',  # 从服务器地址
            'port': 5433,         # 从服务器端口
            'user': 'athena_readonly',
            'password': 'Readonly@2024#Patent',
            'infrastructure/infrastructure/database': 'athena_patent'
        }

    def get_connection(self, operation_type: str):
        """根据操作类型返回连接配置"""
        if operation_type in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER']:
            return self.write_db
        else:
            return self.read_db

    def execute_read_query(self, query: str, params: tuple = None):
        """执行读查询"""
        import psycopg2

        conn_config = self.get_connection('SELECT')
        conn = psycopg2.connect(**conn_config)

        try:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results]
                return cursor.fetchall()
        finally:
            conn.close()

    def execute_write_query(self, query: str, params: tuple = None):
        """执行写查询"""
        import psycopg2

        conn_config = self.get_connection('INSERT')
        conn = psycopg2.connect(**conn_config)

        try:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
```

## 7. 批量操作优化

### 7.1 批量插入
```sql
-- 创建批量插入函数
CREATE OR REPLACE FUNCTION batch_insert_patents(patents_array JSONB)
RETURNS INTEGER AS $$
DECLARE
    inserted_count INTEGER := 0;
    patent_record JSONB;
BEGIN
    FOR patent_record IN SELECT * FROM jsonb_array_elements(patents_array)
    LOOP
        INSERT INTO patents (
            patent_number,
            patent_type,
            title_zh,
            abstract_zh,
            application_date,
            inventors,
            applicants,
            keywords
        ) VALUES (
            patent_record->>'patent_number',
            patent_record->>'patent_type',
            patent_record->>'title_zh',
            patent_record->>'abstract_zh',
            (patent_record->>'application_date')::DATE,
            ARRAY(SELECT jsonb_array_elements_text(patent_record->'inventors')),
            ARRAY(SELECT jsonb_array_elements_text(patent_record->'applicants')),
            ARRAY(SELECT jsonb_array_elements_text(patent_record->'keywords'))
        )
        ON CONFLICT (patent_number) DO UPDATE SET
            title_zh = EXCLUDED.title_zh,
            abstract_zh = EXCLUDED.abstract_zh,
            updated_at = NOW();

        inserted_count := inserted_count + 1;

        -- 每1000条提交一次
        IF MOD(inserted_count, 1000) = 0 THEN
            COMMIT;
        END IF;
    END LOOP;

    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql;
```

### 7.2 批量更新脚本
```python
# batch_operations.py - 批量操作工具
import psycopg2
from psycopg2.extras import execute_batch
import logging

class PatentBatchOperations:
    def __init__(self, db_config):
        self.db_config = db_config
        self.batch_size = 1000

    def bulk_insert_patents(self, patents_data: list):
        """批量插入专利数据"""
        conn = psycopg2.connect(**self.db_config)

        try:
            with conn.cursor() as cursor:
                # 准备SQL语句
                insert_sql = """
                INSERT INTO patents (
                    patent_number, patent_type, title_zh, abstract_zh,
                    application_date, main_ipc, status, created_at
                ) VALUES %s
                ON CONFLICT (patent_number) DO NOTHING
                """

                # 分批处理
                for i in range(0, len(patents_data), self.batch_size):
                    batch = patents_data[i:i + self.batch_size]

                    # 使用execute_values提高性能
                    psycopg2.extras.execute_values(
                        cursor,
                        insert_sql,
                        batch,
                        template=None,
                        page_size=self.batch_size
                    )

                    logging.info(f"已插入 {min(i + self.batch_size, len(patents_data))} 条记录")

                conn.commit()
                logging.info(f"批量插入完成，总计 {len(patents_data)} 条记录")

        except Exception as e:
            conn.rollback()
            logging.error(f"批量插入失败: {e}")
            raise
        finally:
            conn.close()

    def bulk_update_patent_status(self, updates: list):
        """批量更新专利状态"""
        conn = psycopg2.connect(**self.db_config)

        try:
            with conn.cursor() as cursor:
                update_sql = """
                UPDATE patents
                SET status = %(status)s, updated_at = NOW()
                WHERE patent_number = %(patent_number)s
                """

                # 使用execute_batch提高性能
                execute_batch(cursor, update_sql, updates, self.batch_size)

                conn.commit()
                logging.info(f"批量更新完成，总计 {len(updates)} 条记录")

        except Exception as e:
            conn.rollback()
            logging.error(f"批量更新失败: {e}")
            raise
        finally:
            conn.close()
```

## 8. 性能监控和分析

### 8.1 慢查询监控
```sql
-- 创建慢查询日志表
CREATE TABLE slow_queries (
    id BIGSERIAL PRIMARY KEY,
    query_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    query_duration DECIMAL(10,3),
    query_text TEXT,
    rows_affected INTEGER,
    database_name VARCHAR(100),
    user_name VARCHAR(100)
);

-- 创建记录慢查询的函数
CREATE OR REPLACE FUNCTION log_slow_query()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.total_time - OLD.total_time) > 1000 THEN  -- 超过1秒的查询
        INSERT INTO slow_queries (
            query_duration,
            query_text,
            rows_affected,
            database_name,
            user_name
        ) VALUES (
            NEW.total_time - OLD.total_time,
            SUBSTRING(NEW.query, 1, 1000),
            NEW.rows,
            NEW.datname,
            NEW.usename
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 8.2 性能分析视图
```sql
-- 创建性能分析视图
CREATE OR REPLACE VIEW performance_analysis AS
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    vacuum_count,
    autovacuum_count
FROM pg_stat_user_tables
ORDER BY (seq_scan + idx_scan) DESC;
```

### 8.3 自动优化建议
```python
# auto_optimizer.py - 自动优化建议
class DatabaseOptimizer:
    def __init__(self, db_config):
        self.db_config = db_config
        self.optimization_rules = {
            'missing_index': '建议创建索引',
            'high_seq_scan': '建议优化查询或创建索引',
            'dead_tuples': '建议执行VACUUM',
            'bloat': '建议重建表或索引'
        }

    def analyze_missing_indexes(self):
        """分析缺失的索引"""
        conn = psycopg2.connect(**self.db_config)
        suggestions = []

        with conn.cursor() as cursor:
            # 查询频繁的慢查询
            cursor.execute("""
                SELECT query, calls, total_time, mean_time
                FROM pg_stat_statements
                WHERE mean_time > 1000
                ORDER BY mean_time DESC
                LIMIT 10
            """)

            slow_queries = cursor.fetchall()

            for query in slow_queries:
                query_text = query[0]

                # 简单的索引建议逻辑
                if 'WHERE' in query_text and 'apps/apps/patents' in query_text:
                    suggestions.append({
                        'type': 'missing_index',
                        'table': 'apps/apps/patents',
                        'columns': self._extract_where_columns(query_text),
                        'query': query_text,
                        'impact': query[2]  # total_time
                    })

        conn.close()
        return suggestions

    def generate_optimization_report(self):
        """生成优化报告"""
        report = {
            'timestamp': time.time(),
            'suggestions': []
        }

        # 分析各种性能问题
        report['suggestions'].extend(self.analyze_missing_indexes())
        report['suggestions'].extend(self.analyze_table_bloat())
        report['suggestions'].extend(self.analyze_dead_tuples())

        # 按影响程度排序
        report['suggestions'].sort(key=lambda x: x.get('impact', 0), reverse=True)

        return report
```

## 9. 性能测试基准

### 9.1 测试脚本
```python
# performance_benchmark.py - 性能基准测试
import time
import statistics
import psycopg2
from concurrent.futures import ThreadPoolExecutor

class PatentPerformanceBenchmark:
    def __init__(self, db_config):
        self.db_config = db_config
        self.test_results = {}

    def test_patent_search(self, search_terms: list, iterations: int = 100):
        """测试专利搜索性能"""
        results = []

        for term in search_terms:
            times = []

            for _ in range(iterations):
                start_time = time.time()

                # 执行搜索查询
                with psycopg2.connect(**self.db_config) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT id, patent_number, title_zh
                            FROM patents
                            WHERE title_zh ILIKE %s
                            LIMIT 50
                        """, (f'%{term}%',))
                        rows = cursor.fetchall()

                elapsed_time = time.time() - start_time
                times.append(elapsed_time)

            # 统计结果
            results.append({
                'search_term': term,
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'p95_time': sorted(times)[int(len(times) * 0.95)],
                'rows_returned': len(rows)
            })

        self.test_results['patent_search'] = results
        return results

    def test_concurrent_access(self, num_threads: int = 10):
        """测试并发访问性能"""
        def worker():
            start_time = time.time()

            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM patents")
                    count = cursor.fetchone()[0]

            return time.time() - start_time

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(100)]
            times = [future.result() for future in futures]

        concurrent_results = {
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'p95_time': sorted(times)[int(len(times) * 0.95)]
        }

        self.test_results['concurrent_access'] = concurrent_results
        return concurrent_results

    def generate_performance_report(self):
        """生成性能报告"""
        report = {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': self._get_system_info(),
            'reports/reports/results': self.test_results
        }

        return report
```

## 10. 持续优化建议

### 10.1 定期维护任务
```bash
#!/bin/bash
# db_maintenance.sh - 数据库定期维护

# 每日任务
daily_maintenance() {
    echo "$(date): 开始每日维护"

    # 更新统计信息
    psql -h localhost -U athena_admin -d athena_patent -c "ANALYZE;"

    # 清理临时文件
    psql -h localhost -U athena_admin -d athena_patent -c "SELECT pg_reload_conf();"

    # 检查数据库大小
    psql -h localhost -U athena_admin -d athena_patent -c "
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    "
}

# 每周任务
weekly_maintenance() {
    echo "$(date): 开始每周维护"

    # VACUUM分析（避免锁表）
    psql -h localhost -U athena_admin -d athena_patent -c "
        VACUUM ANALYZE patents;
        VACUUM ANALYZE patent_citations;
        VACUUM ANALYZE patent_legal_history;
    "

    # 重建索引
    psql -h localhost -U athena_admin -d athena_patent -c "REINDEX DATABASE athena_patent;"

    # 更新物化视图
    psql -h localhost -U athena_admin -d athena_patent -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_patent_citation_stats;"
}

# 每月任务
monthly_maintenance() {
    echo "$(date): 开始每月维护"

    # 全量VACUUM
    psql -h localhost -U athena_admin -d athena_patent -c "VACUUM FULL VERBOSE ANALYZE;"

    # 检查索引碎片
    psql -h localhost -U athena_admin -d athena_patent -c "
        SELECT
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid::oid)) as index_size,
            pg_stat_get_dead_tuples(indexrelid::oid) as dead_tuples
        FROM pg_stat_all_indexes
        WHERE pg_stat_get_dead_tuples(indexrelid::oid) > 1000
        ORDER BY dead_tuples DESC;
    "
}

# 执行相应的维护任务
case $1 in
    daily)
        daily_maintenance
        ;;
    weekly)
        weekly_maintenance
        ;;
    monthly)
        monthly_maintenance
        ;;
    *)
        echo "用法: $0 {daily|weekly|monthly}"
        exit 1
        ;;
esac
```

### 10.2 性能监控Dashboard
```python
# performance_dashboard.py - 性能监控面板
from flask import Flask, jsonify, render_template
import json
import time

app = Flask(__name__)

@app.route('/api/performance/metrics')
def get_performance_metrics():
    """获取性能指标"""
    metrics = {
        'timestamp': time.time(),
        'queries_per_second': get_qps(),
        'avg_response_time': get_avg_response_time(),
        'active_connections': get_active_connections(),
        'cache_hit_rate': get_cache_hit_rate(),
        'database_size': get_database_size()
    }

    return jsonify(metrics)

def get_qps():
    """获取每秒查询数"""
    # 实现QPS计算逻辑
    pass

def get_avg_response_time():
    """获取平均响应时间"""
    # 实现响应时间计算逻辑
    pass
```

---

**实施建议**:
1. 立即部署缓存系统
2. 配置读写分离
3. 建立性能监控体系
4. 定期执行优化建议
5. 持续监控和调整参数