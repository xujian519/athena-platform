#!/bin/bash

# Athena项目P0级安全问题自动修复脚本
# 使用方法: bash fix_p0_issues.sh

set -e

echo "=== Athena项目P0级安全问题修复脚本 ==="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 备份当前代码
echo -e "${YELLOW}[1/6] 创建备份...${NC}"
BACKUP_DIR="/tmp/athena_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r core/ "$BACKUP_DIR/"
echo -e "${GREEN}✓ 备份完成: $BACKUP_DIR${NC}"
echo ""

# 2. 修复空except块（最危险）
echo -e "${YELLOW}[2/6] 查找空except块...${NC}"
echo "找到以下空except块:"
grep -rn "except.*:" core/ --include="*.py" | grep -E "(except:|except\s*:)" || echo "无"
echo ""
echo -e "${RED}⚠️  空except块需要手动修复，请查看上述文件${NC}"
echo ""

# 3. 修复语法错误
echo -e "${YELLOW}[3/6] 修复语法错误...${NC}"
echo "语法错误文件:"
echo "1. core/decision/claude_code_hitl.py:262 - 重复的except语句"
echo "2. core/agent_collaboration/agents.py:112 - 无效的type: ignore"
echo "3. core/agent_collaboration/agents.py:625 - 无效的type: ignore"
echo ""
echo -e "${RED}⚠️  语法错误需要手动修复${NC}"
echo ""

# 4. 查找SQL注入风险
echo -e "${YELLOW}[4/6] 查找SQL注入风险...${NC}"
echo "SQL注入风险文件:"
ruff check core/ --select=S608 --exclude='*.pyc,__pycache__/.git/*,*.egg-info/*,build/*,dist/*' 2>&1 | grep -v "warning:" | grep "S608" | head -10
echo ""
echo -e "${RED}⚠️  SQL注入风险需要手动修复，建议使用参数化查询${NC}"
echo ""

# 5. 查找硬编码密码
echo -e "${YELLOW}[5/6] 查找硬编码密码...${NC}"
echo "硬编码密码位置:"
grep -rn "jwt_secret\|password.*=.*\"[^\"]*\"" core/ --include="*.py" | grep -v "\.env\|example\|test" | head -10 || echo "无"
echo ""
echo -e "${RED}⚠️  硬编码密码需要替换为环境变量${NC}"
echo ""

# 6. 生成修复清单
echo -e "${YELLOW}[6/6] 生成修复清单...${NC}"
cat > /tmp/p0_fix_checklist.md << 'FIXLIST'
# P0级安全问题修复清单

## 紧急修复（24小时内）

### 1. 语法错误（3处）
- [ ] `core/decision/claude_code_hitl.py:262` - 删除重复的except语句
- [ ] `core/agent_collaboration/agents.py:112` - 修复type: ignore注释
- [ ] `core/agent_collaboration/agents.py:625` - 修复type: ignore注释

### 2. 空except块（29处）
- [ ] `core/memory/enhanced_memory_system.py:200` - 添加日志记录
- [ ] `core/memory/enhanced_memory_system.py:213` - 添加日志记录
- [ ] `core/memory/knowledge_graph_adapter.py:78` - 添加日志记录
- [ ] `core/memory/knowledge_graph_adapter.py:134` - 添加日志记录
- [ ] `core/memory/knowledge_graph_adapter.py:154` - 添加日志记录
- [ ] `core/memory/knowledge_graph_adapter.py:292` - 添加日志记录
- [ ] `core/memory/knowledge_graph_adapter.py:335` - 添加日志记录
- [ ] `core/orchestration/xiaonuo_iterative_search_controller.py:74` - 添加日志记录
- [ ] `core/orchestration/xiaonuo_mcp_adapter.py:354` - 添加日志记录
- [ ] 其他20处...

### 3. SQL注入风险（17处）
- [ ] `core/decision/claude_code_hitl.py` - 12处
- [ ] `core/integration/module_integration_test.py` - 31处
- [ ] `core/execution/test_optimized_execution.py` - 7处
- [ ] `core/memory/family_memory_pg.py` - 7处
- [ ] `core/knowledge/storage/pg_graph_store.py` - 2处

### 4. 硬编码密码（4处）
- [ ] 查找并替换所有硬编码的"jwt_secret"
- [ ] 查找并替换所有硬编码的"password"
- [ ] 创建.env.example模板
- [ ] 更新环境变量文档

## 修复示例

### 空except块修复
```python
# 修复前
try:
    process_data()
except:
    pass

# 修复后
import logging
logger = logging.getLogger(__name__)

try:
    process_data()
except Exception as e:
    logger.error(f"处理失败: {e}", exc_info=True)
    raise
```

### SQL注入修复
```python
# 修复前
query = f"SELECT * FROM users WHERE name = '{user_name}'"
cursor.execute(query)

# 修复后
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (user_name,))
```

### 硬编码密码修复
```python
# 修复前
jwt_secret = "jwt_secret"

# 修复后
import os
jwt_secret = os.getenv("JWT_SECRET", "default_secret_change_me")
```

## 验证修复

修复完成后运行以下命令验证：

```bash
# 检查语法错误
python -m py_compile core/decision/claude_code_hitl.py
python -m py_compile core/agent_collaboration/agents.py

# 检查安全问题
ruff check core/ --select=S110,S105,S106,S608

# 运行测试
pytest tests/ -v
```
FIXLIST

echo -e "${GREEN}✓ 修复清单已生成: /tmp/p0_fix_checklist.md${NC}"
echo ""

# 总结
echo "=== 修复脚本执行完成 ==="
echo ""
echo "下一步行动:"
echo "1. 查看修复清单: cat /tmp/p0_fix_checklist.md"
echo "2. 手动修复P0问题"
echo "3. 验证修复: ruff check core/ --select=S"
echo "4. 运行测试: pytest tests/"
echo ""
echo "备份位置: $BACKUP_DIR"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
