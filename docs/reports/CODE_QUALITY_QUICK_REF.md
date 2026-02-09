# 代码质量快速参考卡片

## 扫描结果速览

```
总问题数: 14,480个
├── P0安全问题: 55个 🔴 (立即修复)
├── P1错误问题: 725个 🟠 (本周修复)
├── P2警告问题: 6,266个 🟡 (本月修复)
└── P3风格问题: 7,434个 🟢 (持续改进)
```

## P0级问题TOP 5（必须立即修复）

| 排名 | 问题类型 | 数量 | 风险等级 |
|------|---------|------|---------|
| 1 | 不安全的随机数生成器 | 81 | 🔴 高 |
| 2 | SQL注入风险 | 17 | 🔴 严重 |
| 3 | 不安全的哈希函数(MD5) | 38 | 🔴 中 |
| 4 | 空except块 | 29 | 🔴 严重 |
| 5 | 不安全的序列化(pickle) | 18 | 🔴 高 |

## 一键修复命令

```bash
# 快速修复（自动）
ruff check --select I --fix .          # 导入排序
ruff check --select F401 --fix .       # 清理未使用的导入
black --line-length 88 .               # 统一代码格式

# 质量检查
ruff check .                            # 全面检查
mypy core/                             # 类型检查
black --check .                         # 格式检查
```

## 关键文件路径

```
报告文件:
├── CODE_QUALITY_SCAN_REPORT_20260126_224913.md  (详细报告)
├── CODE_QUALITY_SUMMARY_20260126.md             (总结报告)
└── CODE_QUALITY_QUICK_REF.md                    (本文件)

修复工具:
└── scripts/fix_p0_issues.sh                     (P0问题修复脚本)
```

## 紧急修复检查清单

- [ ] 修复3个语法错误（10分钟）
- [ ] 修复29个空except块（1小时）
- [ ] 修复4个硬编码密码（30分钟）
- [ ] 修复17个SQL注入风险（3-5小时）
- [ ] 修复14个不安全的临时路径（1小时）

## 修复示例

### 空except块
```python
# ❌ 修复前
try:
    process()
except:
    pass

# ✅ 修复后
try:
    process()
except Exception as e:
    logger.error(f"失败: {e}", exc_info=True)
    raise
```

### SQL注入
```python
# ❌ 修复前
query = f"SELECT * FROM users WHERE name = '{name}'"
cursor.execute(query)

# ✅ 修复后
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (name,))
```

### 硬编码密码
```python
# ❌ 修复前
jwt_secret = "jwt_secret"

# ✅ 修复后
jwt_secret = os.getenv("JWT_SECRET")
```

## 质量目标

| 指标 | 当前 | 1个月目标 | 3个月目标 |
|------|------|----------|----------|
| P0安全问题 | 55 | **0** | 0 |
| P1错误 | 725 | <100 | <50 |
| P2警告 | 6,266 | <2000 | <1000 |
| 代码覆盖率 | 未知 | 60% | 80% |

## 联系方式

- **项目**: Athena工作平台
- **扫描时间**: 2026-01-26
- **扫描工具**: Ruff 0.14.14, Mypy 1.19.1
- **下次扫描**: 修复P0问题后（2-3天）

---

**记住**: 先修复P0安全问题，再逐步改进其他问题！
