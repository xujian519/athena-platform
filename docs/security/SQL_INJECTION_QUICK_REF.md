# SQL注入防护快速参考指南

**版本**: v1.0.0
**更新日期**: 2026-01-26

---

## 🚀 快速开始

### 立即检查你的代码

```bash
# 搜索所有潜在的SQL注入风险
grep -r 'execute.*f".*{' core/ scripts/ services/

# 查找未参数化的查询
grep -r "execute.*WHERE.*{" core/ scripts/

# 检查表名拼接
grep -r "FROM.*{table}" core/ scripts/
```

---

## ✅ 正确做法 (安全的SQL查询)

### 1. 基本参数化查询

```python
# ✅ 正确 - 使用参数化查询
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

# PostgreSQL
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# asyncpg (PostgreSQL异步)
await conn.execute("SELECT * FROM users WHERE id = $1", user_id)
```

### 2. 表名安全处理

```python
from core.database.sql_injection_prevention import SQLInjectionPrevention

# ✅ 正确 - 验证表名后使用
def safe_table_query(table_name: str):
    # 1. 验证表名
    SQLInjectionPrevention.validate_table_name(table_name)

    # 2. 构建查询（表名已验证，值使用参数化）
    query = f"SELECT * FROM {table_name} WHERE status = ?"
    cursor.execute(query, ('active',))

# ✅ 正确 - 使用白名单
ALLOWED_TABLES = ["users", "orders", "products"]

def safe_table_query_whitelist(table_name: str):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"表名不在白名单中: {table_name}")

    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)
```

### 3. LIKE查询安全处理

```python
from core.database.sql_injection_prevention import SQLInjectionPrevention

# ✅ 正确 - 转义LIKE通配符
def safe_like_query(search_term: str):
    # 转义通配符
    escaped_term = SQLInjectionPrevention.escape_like_wildcards(search_term)

    # 使用参数化查询
    query = "SELECT * FROM products WHERE name LIKE ? ESCAPE '\\'"
    cursor.execute(query, (f'%{escaped_term}%',))
```

### 4. 使用SafeQueryBuilder

```python
from core.database.sql_injection_prevention import SafeQueryBuilder

# ✅ 最佳实践 - 使用查询构建器
query, params = (SafeQueryBuilder("users")
    .select(["id", "username", "email"])
    .where("status = ?", "active")
    .where("created_at > ?", "2024-01-01")
    .order_by("created_at", ascending=False)
    .limit(10)
    .build())

cursor.execute(query, params)
```

---

## ❌ 错误做法 (SQL注入风险)

### 1. 字符串拼接

```python
# ❌ 错误 - 永远不要这样做！
user_input = "admin' OR '1'='1"
query = f"SELECT * FROM users WHERE username = '{user_input}'"
cursor.execute(query)
# 结果: 返回所有用户！
```

### 2. 表名直接拼接

```python
# ❌ 错误 - 表名未验证
table_name = get_table_from_request()
query = f"SELECT * FROM {table_name}"
cursor.execute(query)
# 风险: 可以查询任意表
```

### 3. 格式化字符串

```python
# ❌ 错误 - 使用format
query = "SELECT * FROM users WHERE id = {}".format(user_id)
cursor.execute(query)

# ❌ 错误 - 使用%
query = "SELECT * FROM users WHERE id = %s" % user_id
cursor.execute(query)
```

### 4. LIKE查询未转义

```python
# ❌ 错误 - 未转义通配符
search_term = "user%"  # 恶意输入
query = f"SELECT * FROM users WHERE username LIKE '%{search_term}%'"
cursor.execute(query)
# 结果: 可以匹配所有用户
```

---

## 🔒 常见场景的安全实现

### 场景1: 用户登录

```python
# ✅ 安全实现
def login(username: str, password: str):
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    return cursor.fetchone()

# ❌ 不安全实现
def login_unsafe(username: str, password: str):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)  # SQL注入风险！
    return cursor.fetchone()
```

### 场景2: 搜索功能

```python
# ✅ 安全实现
def search_products(keyword: str):
    from core.database.sql_injection_prevention import SQLInjectionPrevention

    # 转义LIKE通配符
    escaped = SQLInjectionPrevention.escape_like_wildcards(keyword)

    query = "SELECT * FROM products WHERE name LIKE ? ESCAPE '\\'"
    cursor.execute(query, (f'%{escaped}%',))
    return cursor.fetchall()

# ❌ 不安全实现
def search_products_unsafe(keyword: str):
    query = f"SELECT * FROM products WHERE name LIKE '%{keyword}%'"
    cursor.execute(query)  # SQL注入风险！
    return cursor.fetchall()
```

### 场景3: 动态排序

```python
# ✅ 安全实现
def get_users(sort_column: str, ascending: bool = True):
    from core.database.sql_injection_prevention import SQLInjectionPrevention

    # 验证列名
    SQLInjectionPrevention.validate_column_name(sort_column)

    # 构建排序子句
    direction = "ASC" if ascending else "DESC"
    query = f"SELECT * FROM users ORDER BY {sort_column} {direction}"
    cursor.execute(query)
    return cursor.fetchall()

# ❌ 不安全实现
def get_users_unsafe(sort_column: str):
    query = f"SELECT * FROM users ORDER BY {sort_column}"
    cursor.execute(query)  # SQL注入风险！
    return cursor.fetchall()
```

### 场景4: 批量操作

```python
# ✅ 安全实现
def update_users_status(user_ids: List[int], new_status: str):
    # 使用executemany进行批量操作
    query = "UPDATE users SET status = ? WHERE id = ?"
    cursor.executemany(query, [(new_status, uid) for uid in user_ids])

# ❌ 不安全实现
def update_users_status_unsafe(user_ids: List[int], new_status: str):
    for user_id in user_ids:
        query = f"UPDATE users SET status = '{new_status}' WHERE id = {user_id}"
        cursor.execute(query)  # SQL注入风险！
```

---

## 🛡️ 输入验证

### 验证用户ID

```python
def validate_user_id(user_id: str) -> bool:
    """验证用户ID格式"""
    import re

    # 只允许字母和数字
    if not re.match(r'^[a-zA-Z0-9_]+$', user_id):
        raise ValueError(f"无效的用户ID: {user_id}")

    # 检查长度
    if len(user_id) > 50:
        raise ValueError("用户ID过长")

    # 检查SQL注入模式
    from core.database.sql_injection_prevention import SQLInjectionPrevention
    if SQLInjectionPrevention.check_sql_injection_attempts(user_id):
        raise ValueError("检测到SQL注入尝试")

    return True
```

### 验证搜索关键词

```python
def validate_search_keyword(keyword: str) -> str:
    """验证搜索关键词"""
    # 移除危险字符
    keyword = keyword.strip()

    # 限制长度
    if len(keyword) > 100:
        raise ValueError("搜索关键词过长")

    # 检查SQL注入
    from core.database.sql_injection_prevention import SQLInjectionPrevention
    if SQLInjectionPrevention.check_sql_injection_attempts(keyword):
        raise ValueError("检测到SQL注入尝试")

    return keyword
```

---

## 📊 不同数据库的参数化查询

### SQLite

```python
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 使用?作为占位符
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
```

### PostgreSQL (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# 使用%s作为占位符
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
```

### PostgreSQL (asyncpg)

```python
import asyncpg

conn = await asyncpg.connect(**db_config)

# 使用$1, $2, ...作为占位符
await conn.execute("SELECT * FROM users WHERE id = $1", user_id)
await conn.execute("INSERT INTO users (name) VALUES ($1)", name)
await conn.execute("UPDATE users SET name = $1 WHERE id = $2", name, user_id)
```

### MySQL

```python
import mysql.connector

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# 使用%s作为占位符
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
```

---

## 🧪 快速测试

### 测试你的代码是否安全

```python
def test_sql_injection_resistance():
    """测试SQL注入抵抗力"""
    # 测试用例
    malicious_inputs = [
        "admin' OR '1'='1",
        "admin'; DROP TABLE users; --",
        "admin' UNION SELECT password FROM users --",
        "' OR '1'='1' --",
        "1' AND 1=1 --",
    ]

    for malicious_input in malicious_inputs:
        try:
            # 调用你的函数
            result = your_database_function(malicious_input)

            # 如果返回了不应该返回的数据，则不安全
            if result:
                print(f"❌ 不安全! 恶意输入成功: {malicious_input}")
                return False
        except Exception as e:
            # 预期应该抛出异常或返回空结果
            print(f"✅ 安全! 恶意输入被阻止: {malicious_input}")

    return True
```

---

## 📝 检查清单

在提交代码前，检查以下项目：

### 代码审查清单

- [ ] 所有SQL查询都使用参数化
- [ ] 表名/列名使用白名单验证
- [ ] 用户输入经过验证和清理
- [ ] 没有字符串拼接SQL查询
- [ ] LIKE查询的通配符已转义
- [ ] 添加了安全注释
- [ ] 使用了SafeQueryBuilder（如适用）

### 测试清单

- [ ] 使用正常输入测试
- [ ] 使用恶意输入测试（' OR '1'='1）
- [ ] 使用特殊字符测试（'; --）
- [ ] 测试边界条件（空值、超长值）
- [ ] 性能测试（避免慢查询）

---

## 🆘 遇到问题？

### 常见错误和解决方案

**错误1: "invalid literal for int()"**
```python
# ❌ 错误
cursor.execute("SELECT * FROM users WHERE id = ?", user_id)  # 缺少元组

# ✅ 正确
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))  # 单元素元组
```

**错误2: "Incorrect number of bindings"**
```python
# ❌ 错误
cursor.execute("SELECT * FROM users WHERE id = ? AND name = ?", (user_id,))  # 缺少参数

# ✅ 正确
cursor.execute("SELECT * FROM users WHERE id = ? AND name = ?", (user_id, name))
```

**错误3: 表名无法参数化**
```python
# ❌ 错误 - 表名不能使用占位符
cursor.execute("SELECT * FROM ?", (table_name,))

# ✅ 正确 - 先验证表名，然后使用f-string
SQLInjectionPrevention.validate_table_name(table_name)
cursor.execute(f"SELECT * FROM {table_name}")
```

---

## 📚 更多资源

### 完整文档
- [SQL注入防护完整指南](SQL_INJECTION_PREVENTION_GUIDE.md)
- [SQL注入修复报告](SQL_INJECTION_FIX_REPORT.md)

### 工具类
- [SQL注入防护工具](../core/database/sql_injection_prevention.py)

### 外部资源
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [Python SQL注入防护](https://docs.python.org/3/security.html)

---

**最后更新**: 2026-01-26
**状态**: ✅ 生产就绪
