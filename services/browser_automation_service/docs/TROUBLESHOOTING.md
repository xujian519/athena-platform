# 故障排查指南

> Athena浏览器自动化服务 - 故障排查指南

本文档提供常见问题的诊断和解决方案。

---

## 目录

- [服务启动问题](#服务启动问题)
- [浏览器操作问题](#浏览器操作问题)
- [性能问题](#性能问题)
- [认证问题](#认证问题)
- [内存问题](#内存问题)
- [网络问题](#网络问题)

---

## 服务启动问题

### 问题：服务无法启动

**症状：**
```bash
$ python main.py
❌ 服务启动失败: Address already in use
```

**可能原因：**
1. 端口8030已被占用
2. 配置文件错误
3. 依赖未安装

**解决方案：**

1. **检查端口占用：**
```bash
# macOS/Linux
lsof -i :8030

# 或使用netstat
netstat -an | grep 8030
```

2. **更换端口或停止占用进程：**
```bash
# 停止占用进程
kill -9 <PID>

# 或修改.env中的PORT
PORT=8031
```

3. **检查依赖：**
```bash
pip install -r requirements.txt
```

### 问题：Playwright浏览器未安装

**症状：**
```bash
❌ Playwright引擎初始化失败: Executable doesn't exist
```

**解决方案：**
```bash
# 安装Playwright浏览器
playwright install chromium

# 验证安装
playwright install --help
```

### 问题：配置文件错误

**症状：**
```bash
❌ 服务启动失败: validation error
```

**解决方案：**
```bash
# 使用.env.example作为模板
cp .env.example .env

# 编辑.env，填写必要配置
nano .env
```

---

## 浏览器操作问题

### 问题：元素未找到

**症状：**
```json
{
  "success": false,
  "error": "BROWSER_ELEMENT_5000",
  "message": "元素未找到"
}
```

**可能原因：**
1. 选择器不正确
2. 元素尚未加载
3. 元素在iframe中
4. 页面还未完全加载

**解决方案：**

1. **验证选择器：**
```python
# 使用浏览器开发工具检查元素
# Chrome: F12 -> Elements -> Copy selector

# 尝试更通用的选择器
# 原来: "#submit-button.btn-primary"
# 改为: "button[type='submit']"
```

2. **增加等待时间：**
```bash
curl -X POST http://localhost:8030/api/v1/click \
  -H "Content-Type: application/json" \
  -d '{"selector": "#btn", "timeout": 10000}'
```

3. **使用JavaScript执行：**
```python
# 等待元素出现
script = """
await page.waitForSelector('#my-element', {timeout: 5000});
"""
```

### 问题：导航超时

**症状：**
```json
{
  "success": false,
  "error": "BROWSER_NAVIGATE_4002",
  "message": "导航超时"
}
```

**解决方案：**

1. **增加超时时间：**
```python
await client.navigate(
    url="https://slow-loading-site.com",
    wait_until="networkidle"  # 等待网络空闲
)
```

2. **检查网络连接：**
```bash
# 测试目标URL
curl -I https://target-site.com

# 检查DNS
nslookup target-site.com
```

3. **使用更宽松的等待条件：**
```python
# load - 页面加载完成
# domcontentloaded - DOM解析完成
# networkidle - 网络请求完成（最严格）
await client.navigate(url, wait_until="domcontentloaded")
```

### 问题：JavaScript执行失败

**症状：**
```json
{
  "success": false,
  "error": "BROWSER_JS_9003",
  "message": "禁止使用危险操作: window.location"
}
```

**解决方案：**

1. **检查JavaScript是否违反沙箱限制：**
```javascript
// ❌ 禁止的操作
window.location.href = "..."
document.cookie = "..."
eval("...")
fetch(...)

// ✅ 允许的操作
document.title
document.querySelector(...)
window.innerWidth
```

2. **使用允许的替代方案：**
```python
# 获取页面标题
await client.evaluate("document.title")

# 检查元素存在
await client.evaluate("!!document.querySelector('.btn')")

# 获取元素文本
await client.evaluate("document.querySelector('h1').textContent")
```

---

## 性能问题

### 问题：响应慢

**症状：**
- API响应时间 > 2秒
- 截图操作特别慢

**诊断步骤：**

1. **检查服务状态：**
```bash
curl http://localhost:8030/api/v1/status
```

2. **查看并发情况：**
```python
stats = await client.get_status()
print(f"活跃会话: {stats['active_sessions']}")
print(f"引擎初始化: {stats['engine_initialized']}")
```

3. **检查资源使用：**
```bash
# CPU使用
top | grep python

# 内存使用
ps aux | grep python | awk '{print $6}'

# 磁盘I/O
iostat -x 1
```

**解决方案：**

1. **调整并发限制：**
```bash
# .env
MAX_CONCURRENT_SESSIONS=5
MAX_CONCURRENT_TASKS=3
```

2. **启用无头模式：**
```bash
BROWSER_HEADLESS=true
```

3. **减少截图尺寸：**
```python
# 不使用full_page
await client.screenshot(full_page=False)
```

### 问题：内存持续增长

**症状：**
```bash
$ ps aux | grep browser_automation
user  12345  2.5  5.2  800000  400000  ?  Sl  12:00  0:05 python main.py
#                                         ^^^^^^ 内存持续增长
```

**可能原因：**
1. 会话未正确关闭
2. 页面对象未释放
3. 截图缓存累积

**解决方案：**

1. **检查会话清理：**
```python
# 获取状态
status = await client.get_status()
print(f"活跃会话: {status['active_sessions']}")

# 如果会话数过多，重启服务
```

2. **启用会话自动清理：**
```bash
# .env
SESSION_TIMEOUT=1800  # 30分钟
SESSION_CLEANUP_INTERVAL=300  # 5分钟
```

3. **限制截图缓存：**
```python
# 不要在循环中累积截图
for url in urls:
    result = await client.screenshot()
    # 立即处理或保存
    save_screenshot(result["screenshot"], f"{i}.png")
    # 不要将所有截图保存在内存中
```

---

## 认证问题

### 问题：认证失败

**症状：**
```json
{
  "success": false,
  "error": "BROWSER_AUTH_2001",
  "message": "无效的令牌"
}
```

**可能原因：**
1. 令牌过期
2. 密钥不匹配
3. 认证未正确配置

**解决方案：**

1. **检查令牌有效期：**
```python
import jwt

try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    exp = decoded.get("exp")
    if exp and exp < time.time():
        print("令牌已过期")
except Exception as e:
    print(f"令牌无效: {e}")
```

2. **验证SECRET_KEY配置：**
```bash
# .env
SECRET_KEY=your_strong_secret_key_here

# 生产环境使用强密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **检查认证状态：**
```bash
# .env
ENABLE_AUTH=false  # 临时禁用用于调试
```

---

## 内存问题

### 问题：内存不足错误

**症状：**
```python
MemoryError: Unable to allocate memory
```

**解决方案：**

1. **增加系统交换空间：**
```bash
# macOS
sudo sysctl vm.swappiness=60

# Linux
sudo swapon /swapfile
```

2. **限制浏览器实例数：**
```bash
MAX_CONCURRENT_SESSIONS=3
```

3. **使用更小的视口：**
```bash
BROWSER_WINDOW_WIDTH=1280
BROWSER_WINDOW_HEIGHT=720
```

---

## 网络问题

### 问题：无法访问目标网站

**症状：**
```json
{
  "success": false,
  "error": "BROWSER_NAVIGATE_4003",
  "message": "网络错误"
}
```

**可能原因：**
1. 网络连接问题
2. 防火墙阻止
3. 目标网站限制爬虫

**解决方案：**

1. **测试网络连接：**
```bash
ping target-site.com
curl -I https://target-site.com
```

2. **使用代理：**
```bash
# .env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
```

3. **设置用户代理：**
```python
# 在创建浏览器时设置用户代理
# 需要修改配置或添加自定义UA
```

### 问题：CORS错误

**症状：**
```
Access to fetch at 'http://localhost:8030' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**解决方案：**

1. **检查CORS配置：**
```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

2. **重启服务使配置生效**

---

## 调试技巧

### 启用详细日志

```bash
# .env
LOG_LEVEL=debug

# 或通过环境变量
export LOG_LEVEL=debug
python main.py
```

### 使用API文档

访问 Swagger UI 进行交互式调试：
```
http://localhost:8030/docs
```

### 检查日志文件

```bash
# 查看最近的日志
tail -f logs/browser_automation.log

# 搜索错误
grep "ERROR" logs/browser_automation.log

# 搜索特定请求ID
grep "ERR-ABC123" logs/browser_automation.log
```

### 性能分析

```python
# 使用cProfile分析性能
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 执行操作
await client.navigate("https://www.baidu.com")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(10)
```

---

## 获取帮助

如果以上方案无法解决问题：

1. **查看完整日志：**
```bash
cat logs/browser_automation.log | tail -100
```

2. **收集系统信息：**
```bash
# Python版本
python --version

# 依赖版本
pip list | grep playwright

# 系统资源
free -h  # Linux
vm_stat  # macOS
```

3. **提交Issue：**
   - 描述问题的详细步骤
   - 提供错误日志
   - 提供系统环境信息

---

## 相关文档

- [API使用示例](./API_USAGE.md)
- [部署指南](./DEPLOYMENT.md)
- [测试指南](./TESTING.md)
