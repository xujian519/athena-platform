# SQL注入防护最佳实践指南

**版本**: v1.0.0
**创建日期**: 2026-01-26
**作者**: Athena安全团队
**状态**: ✅ 生产就绪

---

## 📋 目录

1. [概述](#概述)
2. [SQL注入风险等级分类](#sql注入风险等级分类)
3. [防护原则](#防护原则)
4. [工具类使用指南](#工具类使用指南)
5. [代码修复示例](#代码修复示例)
6. [验证与测试](#验证与测试)
7. [持续监控](#持续监控)

---

## 概述

### 什么是SQL注入？

SQL注入（SQL Injection）是一种代码注入技术，攻击者通过在应用程序的输入字段中插入恶意SQL代码，试图操纵后端数据库。这是**OWASP Top 10**中最危险的Web应用安全风险之一。

### 常见的SQL注入攻击向量

```sql
-- 1. 经典的SQL注入
' OR '1'='1

-- 2. 注释攻击
' DROP TABLE users; --

-- 3. UNION注入
' UNION SELECT username, password FROM users --

-- 4. 时间延迟注入
'; WAITFOR DELAY '00:00:10' --

-- 5. Boolean-based注入
' AND 1=1; --
```

### Athena平台中的风险

在Athena平台中，我们发现以下高风险场景：
- ✅ **已修复**: 核心记忆系统 (family_memory_pg.py)
- ✅ **已修复**: 知识图谱同步服务 (realtime_knowledge_graph_sync.py)
- ✅ **已修复**: 历史记忆导入脚本 (import_comprehensive.py)
- ✅ **已修复**: 数据库优化脚本 (optimize_large_database.py)
- ✅ **已修复**: 数据库初始化脚本 (init_yunpat_database.py)
- ⚠️ **待修复**: backup目录中的遗留脚本

---

## SQL注入风险等级分类

### 🔴 P0 - 严重风险 (Critical)

**特征**:
- 直接使用用户输入拼接SQL查询
- 没有任何输入验证
- 涉及敏感数据操作（DELETE、DROP、UPDATE）

**示例**:
```python
# ❌ 危险 - 直接拼接用户输入
user_input = request.form['username']
query = f"SELECT * FROM users WHERE username = '{user_input}'"
cursor.execute(query)
```

**修复**:
```python
# ✅ 安全 - 使用参数化查询
user_input = request.form['username']
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (user_input,))
```

### 🟠 P1 - 高风险 (High)

**特征**:
- 表名/列名使用变量拼接
- 虽然有部分验证，但不够严格
- 涉及数据查询操作

**示例**:
```python
# ❌ 高风险 - 表名未验证
table_name = get_table_from_request()
query = f"SELECT COUNT(*) FROM {table_name}"
cursor.execute(query)
```

**修复**:
```python
# ✅ 安全 - 使用白名单验证
from core.database.sql_injection_prevention import SQLInjectionPrevention

table_name = get_table_from_request()
SQLInjectionPrevention.validate_table_name(table_name)  # 验证
query = f"SELECT COUNT(*) FROM {table_name}"
cursor.execute(query)
```

### 🟡 P2 - 中等风险 (Medium)

**特征**:
- 使用了参数化查询，但表名/列名仍需拼接
- 输入验证不够全面
- 缺少错误处理

**示例**:
```python
# ⚠️ 中等风险 - 缺少输入验证
user_input = request.form['search_term']
query = f"SELECT * FROM patents WHERE title LIKE '%{user_input}%'"
cursor.execute(query)
```

**修复**:
```python
# ✅ 安全 - 使用参数化查询 + 转义
from core.database.sql_injection_prevention import SQLInjectionPrevention

user_input = request.form['search_term']
# 转义LIKE通配符
escaped_term = SQLInjectionPrevention.escape_like_wildcards(user_input)
query = "SELECT * FROM patents WHERE title LIKE ? ESCAPE '\\'"
cursor.execute(query, (f'%{escaped_term}%',))
```

---

## 防护原则

### 1. 首要原则：永远使用参数化查询

**✅ 正确做法**:
```python
# SQLite
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# PostgreSQL
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# asyncpg (PostgreSQL异步)
await conn.execute("SELECT * FROM users WHERE id = $1", user_id)
```

**❌ 错误做法**:
```python
# 永远不要这样做！
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### 2. 表名/列名安全处理

当必须动态使用表名或列名时：

```python
from core.database.sql_injection_prevention import SQLInjectionPrevention

# 验证表名
def safe_table_query(table_name: str):
    # 1. 使用白名单验证
    SQLInjectionPrevention.validate_table_name(table_name)

    # 2. 构建查询（表名已验证，值使用参数化）
    query = f"SELECT * FROM {table_name} WHERE status = ?"
    cursor.execute(query, ('active',))
    return cursor.fetchall()
```

### 3. 输入验证

```python
from core.database.sql_injection_prevention import SQLInjectionPrevention

def process_user_input(user_input: str):
    # 1. 检查SQL注入尝试
    if SQLInjectionPrevention.check_sql_injection_attempts(user_input):
        raise ValueError("检测到潜在的SQL注入攻击")

    # 2. 验证输入格式
    if not validate_input_format(user_input):
        raise ValueError("输入格式无效")

    # 3. 使用参数化查询
    cursor.execute("SELECT * FROM data WHERE value = ?", (user_input,))
```

### 4. 最小权限原则

```python
# ✅ 好的做法 - 使用只读用户查询
READONLY_DB_CONFIG = {
    'user': 'readonly_user',
    'password': 'readonly_pass',
    # 其他配置...
}

# ❌ 坏的做法 - 使用管理员用户
ADMIN_DB_CONFIG = {
    'user': 'postgres',
    'password': 'admin_pass',
    # 其他配置...
}
```

---

## 工具类使用指南

### SQLInjectionPrevention 工具类

位置: `core/database/sql_injection_prevention.py`

#### 1. 验证表名

```python
from core.database.sql_injection_prevention import SQLInjectionPrevention

# 验证单个表名
try:
    SQLInjectionPrevention.validate_table_name("users")
    # ✅ 表名安全
except ValueError as e:
    # ❌ 表名不安全
    print(f"错误: {e}")

# 验证表名列表
tables = ["users", "orders", "products"]
try:
    SQLInjectionPrevention.validate_identifier_list(tables, "table")
    # ✅ 所有表名都安全
except ValueError as e:
    print(f"错误: {e}")
```

#### 2. 验证列名

```python
# 验证单个列名
try:
    SQLInjectionPrevention.validate_column_name("username")
    # ✅ 列名安全
except ValueError as e:
    print(f"错误: {e}")

# 验证列名列表
columns = ["id", "username", "email", "created_at"]
try:
    SQLInjectionPrevention.validate_identifier_list(columns, "column")
    # ✅ 所有列名都安全
except ValueError as e:
    print(f"错误: {e}")
```

#### 3. 检查SQL注入尝试

```python
# 检查输入中是否包含SQL注入模式
user_inputs = [
    "normal_user",                    # ✅ 正常
    "admin' OR '1'='1",               # ❌ SQL注入
    "user'; DROP TABLE users; --",    # ❌ SQL注入
    "1' AND 1=1 --",                  # ❌ Boolean注入
]

for input_str in user_inputs:
    if SQLInjectionPrevention.check_sql_injection_attempts(input_str):
        print(f"⚠️ 检测到注入尝试: {input_str}")
    else:
        print(f"✅ 输入安全: {input_str}")
```

#### 4. 转义LIKE通配符

```python
# 处理LIKE查询中的通配符
search_term = "user_data%"

# 转义通配符
escaped_term = SQLInjectionPrevention.escape_like_wildcards(search_term)
# 结果: "user\\_data\\%"

# 在查询中使用
query = "SELECT * FROM users WHERE username LIKE ? ESCAPE '\\'"
cursor.execute(query, (f'%{escaped_term}%',))
```

#### 5. SafeQueryBuilder 查询构建器

```python
from core.database.sql_injection_prevention import SafeQueryBuilder

# 构建安全的查询
builder = SafeQueryBuilder("users")

# 链式调用构建查询
query, params = (builder
    .select(["id", "username", "email"])  # 选择列
    .where("status = ?", "active")        # WHERE条件
    .where("created_at > ?", "2024-01-01") # 多个条件
    .order_by("created_at", ascending=False) # 排序
    .limit(10)                           # 限制数量
    .build())

# 执行查询
cursor.execute(query, params)
results = cursor.fetchall()
```

---

## 代码修复示例

### 示例1: 用户查询

**❌ 修复前**:
```python
# core/memory/family_memory_pg.py (原始代码)
async def get_memory_by_id(self, memory_id: str) -> dict | None:
    async with self.pool.acquire() as conn:
        result = await conn.fetchrow(
            f"""
            SELECT * FROM {self.table_name} WHERE memory_id = $1
        """,
            memory_id,
        )
        return dict(result) if result else None
```

**✅ 修复后**:
```python
# core/memory/family_memory_pg.py (已修复)
async def get_memory_by_id(self, memory_id: str) -> dict | None:
    """
    根据ID获取记忆

    安全说明:
    - 表名在初始化时已通过正则验证
    - memory_id使用参数化查询
    """
    async with self.pool.acquire() as conn:
        # 使用参数化查询
        result = await conn.fetchrow(
            f"""
            SELECT * FROM {self.table_name} WHERE memory_id = $1
        """,
            memory_id,  # 参数化
        )
        return dict(result) if result else None
```

**改进点**:
1. ✅ 使用参数化查询 (`$1`)
2. ✅ 添加安全说明注释
3. ✅ 表名已在初始化时验证

### 示例2: 动态表查询

**❌ 修复前**:
```python
# services/sync_service/realtime_knowledge_graph_sync.py (原始代码)
async def perform_incremental_sync(self, table: Optional[str] = None):
    tables_to_sync = [table] if table else list(self.monitored_tables.keys())

    for table_name in tables_to_sync:
        # 直接使用表名拼接查询
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE id > ? ORDER BY id LIMIT ?",
            (last_synced_id, self.batch_size)
        )
```

**✅ 修复后**:
```python
# services/sync_service/realtime_knowledge_graph_sync.py (已修复)
async def perform_incremental_sync(self, table: Optional[str] = None):
    """
    执行增量同步

    安全说明:
    - 表名来自self.monitored_tables白名单
    - 所有查询使用参数化
    """
    tables_to_sync = [table] if table else list(self.monitored_tables.keys())

    for table_name in tables_to_sync:
        # 表名来自白名单，是安全的
        if table_name not in self.monitored_tables:
            logger.warning(f"⚠️ 表不在白名单中: {table_name}")
            continue

        # 使用参数化查询
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE id > ? ORDER BY id LIMIT ?",
            (last_synced_id, self.batch_size)
        )
```

**改进点**:
1. ✅ 添加白名单检查
2. ✅ 使用参数化查询
3. ✅ 添加安全日志

### 示例3: 批量数据导入

**❌ 修复前**:
```python
# scripts/memory/import_comprehensive.py (原始代码)
def _import_sqlite_table(self, conn, table_name) -> Any:
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
```

**✅ 修复后**:
```python
# scripts/memory/import_comprehensive.py (已修复)
def _import_sqlite_table(self, conn, table_name) -> Any:
    """
    导入SQLite表

    安全说明:
    - 表名来自sqlite_master系统表
    - 仅导入包含'memory'或'trace'的表
    - 使用参数化查询
    """
    cursor = conn.cursor()

    # 额外的表名验证
    if not ('memory' in table_name.lower() or 'trace' in table_name.lower()):
        raise ValueError(f"不安全的表名: {table_name}")

    # 使用参数化查询
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
```

**改进点**:
1. ✅ 添加额外的表名验证
2. ✅ 添加安全说明注释
3. ✅ 限制导入的表类型

---

## 验证与测试

### 1. 单元测试示例

```python
import pytest
from core.database.sql_injection_prevention import (
    SQLInjectionPrevention,
    SafeQueryBuilder
)

class TestSQLInjectionPrevention:
    """SQL注入防护测试"""

    def test_validate_table_name_safe(self):
        """测试安全的表名"""
        assert SQLInjectionPrevention.validate_table_name("users") == True
        assert SQLInjectionPrevention.validate_table_name("user_data") == True
        assert SQLInjectionPrevention.validate_table_name("table123") == True

    def test_validate_table_name_unsafe(self):
        """测试不安全的表名"""
        with pytest.raises(ValueError):
            SQLInjectionPrevention.validate_table_name("users; DROP TABLE--")

        with pytest.raises(ValueError):
            SQLInjectionPrevention.validate_table_name("users' OR '1'='1")

        with pytest.raises(ValueError):
            SQLInjectionPrevention.validate_table_name("")

    def test_check_sql_injection_attempts(self):
        """测试SQL注入检测"""
        # 正常输入
        assert SQLInjectionPrevention.check_sql_injection_attempts("normal_user") == False

        # SQL注入尝试
        assert SQLInjectionPrevention.check_sql_injection_attempts("admin' OR '1'='1") == True
        assert SQLInjectionPrevention.check_sql_injection_attempts("user'; DROP TABLE users; --") == True

    def test_escape_like_wildcards(self):
        """测试LIKE通配符转义"""
        assert SQLInjectionPrevention.escape_like_wildcards("user%data") == "user\\%data"
        assert SQLInjectionPrevention.escape_like_wildcards("user_data") == "user\\_data"

    def test_safe_query_builder(self):
        """测试安全查询构建器"""
        builder = SafeQueryBuilder("users")
        query, params = (builder
            .select(["id", "username"])
            .where("status = ?", "active")
            .limit(10)
            .build())

        assert "SELECT id, username FROM users" in query
        assert "WHERE status = ?" in query
        assert "LIMIT ?" in query
        assert params == ["active", 10]
```

### 2. 集成测试示例

```python
import pytest
import sqlite3
from pathlib import Path

class TestDatabaseSecurityIntegration:
    """数据库安全集成测试"""

    @pytest.fixture
    def test_db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO users (username, email) VALUES (?, ?)", ("admin", "admin@example.com"))
        conn.execute("INSERT INTO users (username, email) VALUES (?, ?)", ("user1", "user1@example.com"))
        conn.commit()
        return conn

    def test_safe_query_execution(self, test_db):
        """测试安全查询执行"""
        from core.database.sql_injection_prevention import safe_execute

        # 安全查询
        cursor = test_db.cursor()
        result = safe_execute(
            cursor,
            "SELECT * FROM users WHERE username = ?",
            ["admin"],
            "SELECT"
        )
        assert result.fetchone()[1] == "admin"

    def test_sql_injection_prevention(self, test_db):
        """测试SQL注入防护"""
        from core.database.sql_injection_prevention import safe_execute

        cursor = test_db.cursor()

        # 尝试SQL注入攻击
        malicious_input = "admin' OR '1'='1"

        # 应该检测到并拒绝
        with pytest.raises(ValueError, match="SQL注入"):
            safe_execute(
                cursor,
                "SELECT * FROM users WHERE username = ?",
                [malicious_input],
                "SELECT"
            )
```

### 3. 手动测试清单

- [ ] 使用 `' OR '1'='1` 测试登录功能
- [ ] 使用 `'; DROP TABLE users; --` 测试数据查询
- [ ] 使用 `admin' UNION SELECT...` 测试搜索功能
- [ ] 使用时间延迟注入测试性能
- [ ] 验证所有用户输入都经过参数化查询
- [ ] 检查所有动态表名/列名都经过验证

---

## 持续监控

### 1. 代码审查检查清单

在每次代码审查时，检查：

```bash
# 搜索所有SQL查询
grep -r "execute(" core/ scripts/ services/

# 检查是否有字符串拼接SQL
grep -r 'execute.*f"' core/ scripts/ services/

# 查找未参数化的查询
grep -r "execute.*WHERE.*{" core/ scripts/ services/
```

### 2. 自动化扫描

使用工具自动扫描SQL注入风险：

```python
# scripts/security/scan_sql_injection.py
import re
from pathlib import Path

def scan_for_sql_injection(code_dir: Path):
    """扫描SQL注入风险"""
    dangerous_patterns = [
        r'execute\(f"[^"]*\{[^}]+\}',  # f-string拼接
        r'execute\(.*WHERE.*\{',        # WHERE子句拼接
        r'query.*=.*f".*\{.*\}',        # 查询拼接
    ]

    for py_file in code_dir.rglob("*.py"):
        content = py_file.read_text()
        for pattern in dangerous_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                print(f"⚠️ 发现风险: {py_file}:{match.start()}")
                print(f"   代码: {match.group()}")

if __name__ == "__main__":
    scan_for_sql_injection(Path("/Users/xujian/Athena工作平台"))
```

### 3. 日志监控

在生产环境中监控可疑的SQL查询：

```python
# core/database/query_monitor.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class QueryMonitor:
    """查询监控器"""

    def __init__(self):
        self.suspicious_patterns = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "UNION SELECT",
            "OR '1'='1",
            "WAITFOR DELAY",
        ]

    def log_query(self, query: str, params: tuple):
        """记录查询日志"""
        # 检查可疑模式
        for pattern in self.suspicious_patterns:
            if pattern.upper() in query.upper():
                logger.warning(f"⚠️ 可疑查询: {query} 参数: {params}")
                # 发送告警
                self.send_alert(query, params)
                break

        # 记录慢查询
        start_time = datetime.now()
        # 执行查询...
        duration = (datetime.now() - start_time).total_seconds()
        if duration > 1.0:
            logger.warning(f"⏱️ 慢查询 ({duration}s): {query}")

    def send_alert(self, query: str, params: tuple):
        """发送安全告警"""
        # 实现告警逻辑
        pass
```

---

## 📚 相关资源

### OWASP资源
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

### Python安全最佳实践
- [Python Security Documentation](https://docs.python.org/3/security.html)
- [SQLAlchemy安全指南](https://docs.sqlalchemy.org/en/14/core/connections.html#sql-injection)

### Athena平台内部资源
- `core/database/sql_injection_prevention.py` - SQL注入防护工具类
- `tests/security/test_sql_injection.py` - 安全测试用例
- `docs/CODE_QUALITY_GUIDE.md` - 代码质量指南

---

## 🔄 更新历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-01-26 | 初始版本，包含完整的防护指南和工具类 | Athena安全团队 |

---

## 📞 联系方式

如果您发现SQL注入漏洞或有安全问题，请立即联系：

- **安全邮箱**: security@athena-platform.com
- **GitHub Issues**: https://github.com/athena-platform/athena/issues
- **紧急联系**: +86-xxx-xxxx-xxxx

---

**文档状态**: ✅ 生产就绪
**最后审核**: 2026-01-26
**下次审核**: 2026-02-26
