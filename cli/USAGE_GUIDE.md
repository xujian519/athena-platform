# Athena CLI Week 1 - 使用指南

## 快速开始

### 安装和运行

```bash
cd /Users/xujian/Athena工作平台/cli

# 安装依赖
poetry install

# 测试基本命令
poetry run python -m athena_cli.main hello
poetry run python -m athena_cli.main status
```

## 核心命令

### 1. 专利检索

```bash
# 基础检索
poetry run python -m athena_cli.main search patent "AI专利" -n 10

# 指定格式输出
poetry run python -m athena_cli.main search patent "AI专利" -n 10 --format json
poetry run python -m athena_cli.main search patent "AI专利" -n 10 --format markdown
```

### 2. 专利分析

```bash
# 自动识别分析类型
poetry run python -m athena_cli.main analyze 201921401279.9

# 指定分析类型
poetry run python -m athena_cli.main analyze creativity 201921401279.9
poetry run python -m athena_cli.main analyze invalidation 201921401279.9

# 保存结果
poetry run python -m athena_cli.main analyze 201921401279.9 -o report.json
```

### 3. 批量操作（核心价值）⭐

```bash
# 批量检索
poetry run python -m athena_cli.main batch search --file queries.txt

# 批量分析
poetry run python -m athena_cli.main batch analyze --file patent_ids.txt

# 指定分析类型
poetry run python -m athena_cli.main batch analyze --file patent_ids.txt --type invalidation

# 指定输出目录
poetry run python -m athena_cli.main batch analyze --file patent_ids.txt --output reports/
```

### 4. 配置管理

```bash
# 查看配置
poetry run python -m athena_cli.main config list

# 获取配置
poetry run python -m athena_cli.main config get api_endpoint

# 设置配置
poetry run python -m athena_cli.main config set api_endpoint https://api.athena.ai
poetry run python -m athena_cli.main config set default_limit 20

# 登录
poetry run python -m athena_cli.main config login

# 测试连接
poetry run python -m athena_cli.main config test
```

## 测试数据

### queries.txt（批量检索）
```
人工智能专利
机器学习算法
深度学习模型
自然语言处理
计算机视觉
```

### patent_ids.txt（批量分析）
```
201921401279.9
202010123456.7
202020123456.3
CN202010123456A
CN202020123456A
CN201921401279A
```

## MVP验证场景

### 济南力邦无效案件（真实业务）

```bash
# 准备专利号列表（188个专利）
cat > jinan_libang.txt << EOF
201921401279.9
# ... 其他187个专利号
EOF

# 执行批量无效分析
poetry run python -m athena_cli.main batch analyze \
  --file jinan_libang.txt \
  --type invalidation \
  --output jinan_libang_reports/

# 预期:
# - 时间: <2小时（目标）
# - 成功率: >95%
# - 结果: 所有报告保存在jinan_libang_reports/
```

## 性能基准

### 当前性能（模拟数据）

| 操作 | 时间 | 说明 |
|------|------|------|
| 单个检索 | 0.5秒 | 符合<2秒目标 |
| 单个分析 | 2.0秒 | 符合<30秒目标 |
| 批量检索（10个） | 5秒 | 0.5秒/个 |
| 批量分析（6个） | 12秒 | 2秒/个 |

### 效率对比

| 场景 | Web时间 | CLI时间 | 效率提升 |
|------|---------|---------|---------|
| 6个专利分析 | 18分钟 | 0.2分钟 | 90倍 |
| 100个专利分析 | 5小时 | 3.3分钟 | 90倍 |
| 188个专利分析 | 9.4小时 | 6.3分钟 | 90倍 |

**注意**: 模拟数据性能，实际可能不同

## 故障排除

### 常见问题

**Q1: 命令显示版本信息后就退出**
- A: 检查是否使用了正确的子命令，例如：
  ```bash
  # 错误
  poetry run python -m athena_cli.main search "AI"
  
  # 正确
  poetry run python -m athena_cli.main search patent "AI"
  ```

**Q2: ModuleNotFoundError: No module named 'yaml'**
- A: 运行 `poetry install` 安装依赖

**Q3: 批量处理失败**
- A: 检查文件路径和格式，确保每行一个查询/专利号

## 下一步

- [ ] Week 1 Day 2-3: 性能优化
- [ ] Week 1 Day 4-5: 真实场景测试
- [ ] Week 1 Day 6-7: 集成测试
- [ ] Week 2: Gateway集成

## 联系方式

**项目负责人**: 徐健 (xujian519@gmail.com)  
**项目位置**: `/Users/xujian/Athena工作平台/cli/`

---

**🌸 Athena CLI - 小诺的爸爸专用工作平台！**
