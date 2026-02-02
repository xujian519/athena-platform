# Athena 工作平台服务管理系统

## 🚀 快速开始

清理上下文后，您只需要一条命令即可快速恢复系统到完整工作状态：

```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台

# 快速启动核心服务
./dev/scripts/quick_start.sh
```

或者使用完整的管理脚本：

```bash
# 显示所有可用选项
./dev/scripts/athena_services_manager.sh help

# 快速恢复核心服务
./dev/scripts/athena_services_manager.sh quick

# 完整启动所有服务
./dev/scripts/athena_services_manager.sh start
```

## 📋 服务列表

| 服务名称 | 描述 | 端口 | 类型 | 状态 |
|---------|------|------|------|------|
| Redis | 缓存服务 | 6379 | 🟢 核心 | 基础设施 |
| PostgreSQL | 数据库 | 5432 | 🟢 核心 | 基础设施 |
| Elasticsearch | 搜索引擎 | 9200 | 🟡 可选 | 搜索功能 |
| 小诺智能问答 | AI问答系统 | 8080 | 🟢 核心 | 应用服务 |
| NLP服务 | 自然语言处理 | 8081 | 🟢 核心 | AI处理 |
| 向量检索服务 | 向量搜索 | 8082 | 🟢 核心 | 搜索功能 |
| 知识图谱服务 | 知识图谱 | 8083 | 🟡 可选 | 高级功能 |
| 专利检索服务 | 专利搜索 | 8084 | 🟡 可选 | 业务功能 |
| MCP管理服务 | MCP管理 | 8085 | 🟡 可选 | 管理功能 |
| 爬虫管理服务 | 爬虫管理 | 8086 | 🟡 可选 | 数据采集 |

## 🛠️ 环境设置

### 首次使用设置

```bash
# 运行环境设置脚本
./dev/scripts/setup_athena.sh
```

设置脚本会自动：
- ✅ 设置脚本执行权限
- ✅ 创建必要的目录结构
- ✅ 检查系统依赖
- ✅ 添加命令别名
- ✅ 创建桌面快捷方式

### 手动设置命令别名

如果您希望手动设置别名，可以运行：

```bash
# 加载别名到当前会话
source /Users/xujian/Athena工作平台/config/bash_aliases.sh

# 或者永久添加到您的 shell 配置文件
echo 'source /Users/xujian/Athena工作平台/config/bash_aliases.sh' >> ~/.zshrc
```

## 📖 使用指南

### 基础命令

```bash
# 快速启动（推荐日常使用）
athena-start

# 完整启动所有服务
athena-full

# 停止所有服务
athena-stop

# 重启所有服务
athena-restart

# 查看服务状态
athena-status

# 执行健康检查
athena-health
```

### 监控和调试

```bash
# 实时查看日志
athena-logs

# 查看最近日志
athena-log

# 检查端口状态
athena-ports

# 查看相关进程
athena-processes

# 调试模式
athena-debug
```

### 便捷组合命令

```bash
# 全面检查（状态 + 健康）
athena-check

# 重置服务（停止后重新启动）
athena-reset
```

## 📊 服务状态解读

服务状态表格显示以下信息：

- **状态图标**：
  - 🟢 running - 服务正在运行
  - 🔴 stopped - 服务已停止
  - ⚠️ 异常 - 服务运行但健康检查失败

- **健康检查**：
  - ✅ 健康 - 服务运行正常
  - ⚠️ 异常 - 服务运行但有问题
  - ❌ 停止 - 服务未运行

## 🚨 故障排查

### 常见问题解决

1. **服务启动失败**
   ```bash
   # 查看详细错误日志
   athena-log

   # 检查端口占用
   athena-ports
   ```

2. **端口被占用**
   ```bash
   # 查找占用进程
   lsof -i :8080

   # 杀死进程
   kill -9 <PID>
   ```

3. **权限问题**
   ```bash
   # 重新设置权限
   ./dev/scripts/setup_athena.sh
   ```

4. **依赖缺失**
   ```bash
   # macOS 安装依赖
   brew install redis postgresql elasticsearch

   # 检查安装状态
   athena-check
   ```

### 日志位置

```
/Users/xujian/Athena工作平台/logs/
├── athena_services_YYYYMMDD.log      # 主日志文件
├── status_report_YYYYMMDD_HHMMSS.json # 状态报告
└── service_status.json               # 实时状态
```

## ⚙️ 配置

### 主配置文件
位置：`/Users/xujian/Athena工作平台/config/athena_services.conf`

主要配置项：
- 服务超时设置
- 日志级别
- 核心服务列表
- 端口配置

### 自定义配置

您可以根据需要修改配置文件来调整：
- 服务启动超时时间
- 健康检查间隔
- 日志保留天数
- 服务端口

## 🔧 高级用法

### 自定义启动顺序

修改 `athena_services_manager.sh` 中的启动顺序：

```bash
startup_order=(
    "redis"           # 基础缓存
    "postgresql"      # 数据库
    "elasticsearch"   # 搜索引擎
    # ... 按依赖顺序添加
)
```

### 添加新服务

1. 在服务配置中添加新服务
2. 设置启动命令和端口
3. 配置依赖关系
4. 测试启动流程

### 集成到CI/CD

```bash
#!/bin/bash
# CI/CD 集成示例

# 启动服务
./dev/scripts/athena_services_manager.sh start

# 等待服务就绪
./dev/scripts/athena_services_manager.sh health

# 运行测试
# ... 您的测试代码

# 清理环境
./dev/scripts/athena_services_manager.sh stop
```

## 📞 技术支持

### 获取帮助

```bash
# 查看命令帮助
athena-help

# 查看详细文档
cat docs/services_usage_guide.md

# 查看配置说明
cat config/athena_services.conf
```

### 问题报告

如果遇到问题，请提供：
1. 错误日志文件
2. 服务状态报告
3. 系统环境信息
4. 具体操作步骤

联系方式：徐健 (xujian519@gmail.com)

---

## 🎯 最佳实践

### 日常使用建议

1. **清理上下文后**：始终使用 `athena-start` 快速恢复
2. **开发过程中**：使用 `athena-status` 定期检查状态
3. **遇到问题时**：使用 `athena-check` 全面诊断
4. **结束工作时**：使用 `athena-stop` 清理资源

### 性能优化建议

1. **优先使用快速模式**：`athena-start` 只启动核心服务
2. **按需启动可选服务**：需要时再启动完整服务
3. **定期清理日志**：避免日志文件过大
4. **监控资源使用**：定期检查内存和CPU占用

---

**快速开始命令**：
```bash
cd /Users/xujian/Athena工作平台
./dev/scripts/setup_athena.sh  # 首次设置
athena-start               # 快速启动
```

祝您使用愉快！🚀