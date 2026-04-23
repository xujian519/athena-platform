# Athena CLI - 专利AI平台命令行工具

> 小诺的爸爸专用工作平台 🌸

## 🚀 快速开始

### 安装

```bash
# 使用Poetry安装
cd cli
poetry install

# 或使用pip
pip install -e .
```

### 基础使用

```bash
# 交互模式
athena

# 专利检索
athena search "人工智能专利" -n 10

# 专利分析
athena analyze 201921401279.9

# 批量分析
athena batch analyze --file patent_ids.txt

# 配置管理
athena config set api_endpoint https://api.athena.ai
athena config login
```

## 📋 MVP功能范围

### P0 - 核心功能（MVP验证）

- ✅ `search` - 专利检索
- ✅ `analyze` - 专利分析
- ✅ `batch analyze` - 批量分析 ⭐ 核心价值
- ✅ `batch search` - 批量检索

### P1 - 重要功能（MVP后）

- ⚠️ 专利下载
- ⚠️ 配置管理
- ⚠️ 帮助系统

### P2 - 未来考虑

- ❌ 专利撰写CLI（Web体验更好）
- ❌ 审查意见答复CLI（高度复杂）

## 🎯 MVP验证目标

### 核心假设

1. **批量处理是杀手级功能** - 验证济南力邦188个专利分析场景
2. **CLI显著提升效率** - 检索速度提升50%+，批处理提升500%+
3. **用户愿意使用CLI** - 7日留存率>30%，NPS>40
4. **质量与Web一致** - 分析一致性>95%

### 成功标准

- 批处理采用率 >30%
- 检索速度提升 >50%
- 7日留存率 >30%
- NPS >40
- 满意度 >4.0/5.0

## 🛠️ 开发

```bash
# 安装开发依赖
poetry install --with dev

# 运行测试
pytest

# 代码格式化
black .
ruff check . --fix

# 类型检查
mypy athena_cli/
```

## 📚 文档

- [CLI参考文档](docs/CLI_REFERENCE.md)
- [用户指南](docs/USER_GUIDE.md)
- [MVP验证计划](docs/MVP_VALIDATION_PLAN.md)

## 🙏 致谢

基于以下工具的深度调研：
- Claude Code CLI
- GitHub CLI
- Qwen CLI
- iFlow CLI
