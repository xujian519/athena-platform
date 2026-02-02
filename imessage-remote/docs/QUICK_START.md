# Athena iMessage Remote Control - 快速入门

通过 iMessage 远程控制 Athena 工作平台和小诺智能体的快速入门指南。

## 📋 前置要求

### 1. 安装 imsg（iMessage RPC 工具）

```bash
# 使用 npm 安装
npm install -g imsg

# 或使用 Homebrew
brew tap mdf0xx/imsg
brew install imsg

# 验证安装
imsg --version
```

### 2. 配置 iMessage 权限

首次使用时，需要授予 imsg 访问 iMessage 的权限：

```bash
# 启动 imsg（会弹出权限请求）
imsg rpc

# 按提示允许访问
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/xujian/Athena工作平台/imessage-remote

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 配置文件

编辑 `config/config.yaml`，设置允许的发件人号码：

```yaml
imessage:
  allowed_senders:
    - "+8613800138000"  # 替换为你的号码

agents:
  xiaonuo:
    endpoint: "http://localhost:8000/api/xiaonuo"
  athena:
    endpoint: "http://localhost:8000/api/athena"

obsidian:
  vault_path: "/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/Athena"
```

### 3. 启动服务

```bash
# 开发模式（前台运行，日志输出到控制台）
python -m src.main --dev

# 生产模式（后台运行）
python -m src.main --daemon
```

### 4. 发送测试命令

通过 iMessage 发送命令：

```
小诺，帮我检索关于人工智能的专利
```

预期反馈：

```
✅ 专利检索完成
关键词：人工智能
结果：找到 23 件相关专利
详情：📊 专利检索/2026-01-31/人工智能专利检索.md
```

## 📝 命令示例

### 专利检索

```
小诺，帮我检索关于量子计算的专利
小诺搜索人工智能相关的专利
查找深度学习专利
```

### 专利分析

```
小诺，分析这个专利的创造性：CN202310123456.7
评估专利 CN202310123456.7 的创造性
```

### 信息查询

```
小诺，查询曹新乐的联系信息
找傅玉秀的电话
```

### 复杂分析（Athena）

```
@Athena 分析这个专利的技术方案：CN202310123456.7
Athena，深度分析这个领域的专利布局
```

## 🔧 高级配置

### 调整反馈详细程度

在 `config/config.yaml` 中修改：

```yaml
feedback:
  mode: "smart"  # simple | standard | detailed | smart
  summary_max_length: 500
  include_file_links: true
  include_suggestions: true
```

### 修改 Obsidian 组织方式

```yaml
obsidian:
  organize_by: "task_type"  # task_type | date | agent
```

### 设置任务超时

```yaml
agents:
  xiaonuo:
    timeout: 300  # 秒
  athena:
    timeout: 600  # 秒
```

## 🐛 故障排除

### 问题：imsg 命令找不到

```bash
# 检查安装
which imsg

# 重新安装
npm install -g imsg
```

### 问题：无法接收 iMessage

1. 检查权限设置
2. 重启 imsg: `imsg rpc`
3. 查看日志文件

### 问题：智能体无响应

1. 确认智能体服务是否运行
2. 检查 endpoint 配置
3. 查看日志中的错误信息

## 📊 查看日志

```bash
# 实时查看日志
tail -f /Users/xujian/Athena工作平台/logs/imessage_remote.log

# 查看最近50行
tail -n 50 /Users/xujian/Athena工作平台/logs/imessage_remote.log
```

## 🔐 安全建议

1. **启用白名单**：只允许可信号码发送命令
2. **使用强密码**：保护配置文件
3. **定期更新**：保持依赖最新
4. **监控日志**：定期检查异常活动

## 📖 更多文档

- [完整配置参考](../config/config.yaml)
- [API 文档](./API.md)
- [架构设计](./ARCHITECTURE.md)
