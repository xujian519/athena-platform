# 后台任务和Teammates清理指南

> **日期**: 2026-04-21
> **问题**: 状态栏显示18个后台任务和8个teammates

---

## 🔍 问题分析

### 状态栏提示
```
18 background tasks
------´
⏵⏵ accept edits on · 8 teammates
```

### 可能的原因

1. **Agent工具在后台运行**
   - 之前启动的Agent任务未关闭
   - MCP服务器在运行
   - 测试任务在后台执行

2. **Teammate会话未关闭**
   - OMC (oh-my-claudecode) 的teammate会话
   - 协作的Agent实例未清理

3. **后台进程**
   - Docker容器在运行
   - 服务进程在后台

---

## 🧹 清理步骤

### 步骤 1: 检查后台进程

```bash
# 查看Python进程
ps aux | grep python | grep -v grep

# 查看Docker容器
docker ps

# 查看后台任务
jobs -l
```

### 步骤 2: 停止Docker容器（如果在运行）

```bash
# 查看运行中的容器
docker ps

# 停止所有容器
docker stop $(docker ps -q)

# 或停止特定容器
docker-compose -f docker-compose.unified.yml down
```

### 步骤 3: 清理Teammate会话

**方法 1: 重启Claude Code**
```bash
# 完全退出Claude Code
# 然后重新启动
```

**方法 2: 清理OMC状态**
```bash
# 清理teammate会话状态
rm -rf .claude/projects/*/sessions/*

# 或清理特定会话
ls .claude/projects/*/sessions/
```

### 步骤 4: 清理后台任务

**在Claude Code中**:
1. 打开命令面板 (`Cmd/Ctrl + Shift + P`)
2. 输入: `Kill all background tasks`
3. 确认操作

**或使用命令**:
```bash
# 杀死所有Python后台进程
pkill -f "python.*agent"
pkill -f "python.*mcp"

# 清理pytest缓存
rm -rf .pytest_cache/
```

---

## 🔧 预防措施

### 1. 及时关闭后台任务

**规则**:
- 完成任务后，立即关闭后台进程
- 不要长时间保留不必要的teammate会话
- 定期检查并清理Docker容器

### 2. 使用会话管理

**推荐做法**:
```bash
# 使用tmux或screen管理长期任务
tmux new -s work
# 在tmux中运行任务
# 完成后detach: Ctrl+B D

# 重新连接
tmux attach -t work
```

### 3. 监控资源使用

```bash
# 查看系统资源
top

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

---

## 📊 常见后台任务类型

### Agent任务

**特征**:
- Python进程运行agent相关代码
- 占用CPU和内存

**清理**:
```bash
pkill -f "xiaona|xiaonuo|agent"
```

### MCP服务器

**特征**:
- MCP服务器进程在运行
- 可能有端口监听

**清理**:
```bash
# 停止MCP服务器
docker-compose down
# 或
pkill -f "mcp.*server"
```

### 测试任务

**特征**:
- pytest进程在运行
- 可能有测试数据库连接

**清理**:
```bash
# 停止测试进程
pkill -f pytest

# 清理测试缓存
rm -rf .pytest_cache/
```

---

## ✅ 清理验证

清理完成后，确认：

- [ ] 状态栏不再显示后台任务
- [ ] 没有不必要的Python进程
- [ ] Docker容器已停止（如果不需要）
- [ ] 系统资源使用正常
- [ ] Claude Code响应速度正常

---

## 🎯 最佳实践

### 1. 定期清理

**频率**: 每天结束时

**检查项**:
- 后台任务
- Docker容器
- Teammate会话
- 临时文件

### 2. 资源监控

**工具**:
- Activity Monitor (macOS)
- htop (Linux)
- docker stats (容器)

### 3. 会话管理

**建议**:
- 使用tmux/screen管理长期任务
- 及时关闭不需要的会话
- 定期重启Claude Code

---

## 🚨 如果清理失败

### 1. 强制终止进程

```bash
# 查找并终止特定进程
ps aux | grep <process_name>
kill -9 <pid>
```

### 2. 重启系统

**最后手段**:
```bash
# macOS
sudo shutdown -r now

# Linux
sudo reboot
```

### 3. 重启Claude Code

**彻底清理**:
```bash
# 退出Claude Code
# 清理状态
rm -rf .claude/tmp/
# 重新启动
```

---

**生成时间**: 2026-04-21
**预期效果**: 清理所有后台任务和teammate会话
