# 安全问题修复指南

本文档提供了Athena工作平台安全问题的具体修复方案。

---

## 1. 移除硬编码密码

### 1.1 数据库连接

**问题代码** (`tools/patent_archive_updater.py:98`):
```python
# ❌ 错误 - 硬编码密码
engine = create_engine(
    "postgresql://postgres:xj781102@localhost:5432/athena_business"
)
```

**修复方案**:
```python
# ✅ 正确 - 使用环境变量
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(database_url)
```

**环境变量配置** (`.env`):
```bash
DATABASE_URL=postgresql://postgres:secure_password@localhost:5432/athena_business
```

### 1.2 JWT密钥

**问题代码** (`core/auth/authentication.py:88`):
```python
# ❌ 错误 - 硬编码JWT密钥
jwt_secret: str = "your-super-secret-key-change-in-production"
```

**修复方案**:
```python
# ✅ 正确 - 从环境变量读取
import os
import secrets

jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    raise ValueError("JWT_SECRET_KEY not set in environment")

# 验证密钥长度
if len(jwt_secret) < 32:
    raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
```

**生成安全密钥**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**环境变量配置** (`.env`):
```bash
# 使用生成的密钥
JWT_SECRET_KEY=生成的随机密钥
```

---

## 2. 修复CORS配置

### 2.1 API CORS配置

**问题代码** (多个文件):
```python
# ❌ 错误 - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # 危险组合！
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**修复方案**:
```python
# ✅ 正确 - 限制特定来源
import os
from typing import List

def get_allowed_origins() -> List[str]:
    """从环境变量获取允许的来源"""
    origins_str = os.getenv('ALLOWED_ORIGINS', '')
    origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    
    if not origins:
        raise ValueError("ALLOWED_ORIGINS must be set in production")
    
    if '*' in origins:
        raise ValueError("Wildcard '*' not allowed in ALLOWED_ORIGINS")
    
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,  # 预检请求缓存时间
)
```

**环境变量配置** (`.env`):
```bash
# 开发环境
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# 生产环境
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## 3. 启用SSL验证

### 3.1 HTTP客户端配置

**问题代码** (`core/connection_pool/connection_manager.py:118`):
```python
# ❌ 错误 - 禁用SSL验证
client = httpx.AsyncClient(
    limits=limits,
    timeout=timeout,
    verify=False,  # 危险！
)
```

**修复方案**:
```python
# ✅ 正确 - 启用SSL验证
import os
import certifi
import httpx

def should_verify_ssl() -> bool:
    """根据环境决定是否验证SSL"""
    # 生产环境必须验证
    if os.getenv('ENVIRONMENT') == 'production':
        return True
    
    # 开发环境可以选择性禁用
    verify = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
    if not verify:
        logger.warning("SSL verification is DISABLED - not safe for production!")
    
    return verify

client = httpx.AsyncClient(
    limits=limits,
    timeout=timeout,
    verify=certifi.where() if should_verify_ssl() else False,
)
```

**环境变量配置** (`.env`):
```bash
# 生产环境必须启用
ENVIRONMENT=production
VERIFY_SSL=true

# 开发环境可以临时禁用（不推荐）
# ENVIRONMENT=development
# VERIFY_SSL=false
```

---

## 4. 文件上传安全

### 4.1 路径遍历防护

**问题代码** (`core/api/unified_report_routes.py:132`):
```python
# ❌ 错误 - 直接使用用户提供的文件名
file_path = upload_dir / file.filename
with open(file_path, "wb") as f:
    content = await file.read()
    f.write(content)
```

**修复方案**:
```python
# ✅ 正确 - 完整的安全验证
from pathlib import Path
import uuid
from fastapi import UploadFile, HTTPException

async def save_uploaded_file(
    upload_dir: Path,
    file: UploadFile,
    max_size: int = 10 * 1024 * 1024  # 10MB
) -> Path:
    """安全保存上传的文件"""
    
    # 1. 验证文件扩展名
    allowed_extensions = {'.pdf', '.docx', '.txt', '.md'}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}"
        )
    
    # 2. 生成安全的文件名（使用UUID）
    safe_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / safe_filename
    
    # 3. 验证路径在允许的目录内（防止路径遍历）
    resolved_path = file_path.resolve()
    resolved_upload_dir = upload_dir.resolve()
    
    if not str(resolved_path).startswith(str(resolved_upload_dir)):
        raise HTTPException(
            status_code=400,
            detail="无效的文件路径"
        )
    
    # 4. 限制文件大小
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大，最大允许 {max_size // (1024*1024)}MB"
        )
    
    # 5. 保存文件
    upload_dir.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path

# 使用示例
file_path = await save_uploaded_file(upload_dir, file, max_size=10*1024*1024)
```

---

## 5. 改进错误处理

### 5.1 避免空的except块

**问题代码**:
```python
# ❌ 错误 - 吞掉所有错误
try:
    process_data()
except Exception:
    pass
```

**修复方案**:
```python
# ✅ 正确 - 记录并处理错误
import logging

logger = logging.getLogger(__name__)

try:
    process_data()
except ValidationError as e:
    # 预期的业务错误，记录并友好处理
    logger.warning(f"验证失败: {e}")
    return {"error": "数据验证失败"}
except DatabaseError as e:
    # 数据库错误，记录并重试或终止
    logger.error(f"数据库错误: {e}", exc_info=True)
    raise
except Exception as e:
    # 未预期的错误，记录详细信息并重新抛出
    logger.critical(f"未预期的错误: {e}", exc_info=True)
    raise  # 不要在生产环境吞掉未知异常
```

---

## 6. SQL注入防护

### 6.1 使用参数化查询

**问题代码** (潜在风险):
```python
# ❌ 错误 - 字符串拼接（可能导致SQL注入）
query = f"SELECT * FROM users WHERE name = '{user_name}'"
cursor.execute(query)
```

**修复方案**:
```python
# ✅ 正确 - 使用参数化查询
# 方法1: 使用%s占位符
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (user_name,))

# 方法2: 使用命名参数
query = "SELECT * FROM users WHERE name = %(name)s"
cursor.execute(query, {'name': user_name})

# 方法3: 使用asyncpg
await conn.execute(
    "SELECT * FROM users WHERE name = $1",
    user_name
)
```

---

## 7. 环境变量模板

创建 `.env.example` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/athena
POSTGRES_USER=athena_admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=athena_business

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password

# JWT配置
JWT_SECRET_KEY=your-random-32-byte-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS配置
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# SSL配置
VERIFY_SSL=true

# Qdrant向量数据库
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key

# OpenAI配置
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 环境标识
ENVIRONMENT=production
DEBUG=false
```

---

## 8. 安全检查清单

在部署到生产环境前，确保：

### 密码和密钥
- [ ] 所有密码从环境变量读取
- [ ] JWT密钥长度≥32字节且随机生成
- [ ] 数据库密码足够复杂
- [ ] API密钥已配置且安全

### CORS和认证
- [ ] CORS仅允许特定域名
- [ ] 不允许 `allow_origins=["*"]`
- [ ] JWT token有合理的过期时间
- [ ] 敏感操作需要重新认证

### SSL/TLS
- [ ] 所有HTTPS请求验证证书
- [ ] 不使用 `verify=False`
- [ ] 使用最新的TLS版本

### 文件上传
- [ ] 验证文件类型
- [ ] 限制文件大小
- [ ] 使用UUID生成文件名
- [ ] 验证路径在允许目录内

### 错误处理
- [ ] 不使用空的except块
- [ ] 记录所有错误
- [ ] 不在错误信息中泄露敏感数据

### SQL查询
- [ ] 所有查询使用参数化
- [ ] 不拼接SQL字符串
- [ ] 限制查询结果数量

---

## 9. 验证修复

运行以下命令验证修复：

```bash
# 1. 检查是否有硬编码密码
grep -rn "password.*=.*['\"]" core/ --include="*.py" | grep -v "os.getenv"

# 2. 检查CORS配置
grep -rn "allow_origins=\[\"\*\"\]" core/ --include="*.py"

# 3. 检查SSL验证
grep -rn "verify=False" core/ --include="*.py"

# 4. 检查空的except块
grep -rn "except.*:\s*pass" core/ --include="*.py"

# 5. 运行安全扫描
pip install bandit safety
bandit -r core/ -f json -o security_report.json
safety check --file requirements.txt
```

---

## 10. 持续监控

建议设置以下自动化监控：

1. **pre-commit钩子**：在提交前自动扫描安全问题
2. **CI/CD集成**：在构建流程中运行安全扫描
3. **定期审计**：每月进行一次全面安全审计
4. **依赖更新**：定期更新依赖包并检查漏洞

---

完成所有修复后，建议重新运行安全审计以验证效果。
