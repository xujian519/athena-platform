# 🤖 Athena平台UI自动化能力说明

## 现有工具

### 1. Browser-Use控制器
- **位置**: `core/orchestration/xiaonuo_browser_use_controller.py`
- **功能**: AI驱动的浏览器自动化
- **特点**:
  - 可以理解网页内容
  - 智能决策操作步骤
  - 支持多种浏览器引擎
  - 可执行复杂任务序列

### 2. 支持的浏览器引擎
- **Chromium** - 开源浏览器
- **Chrome** - Google Chrome
- **Firefox** - Mozilla Firefox
- **Safari** - Apple Safari
- **Playwright** - 跨浏览器引擎

### 3. 现有服务
- **browser-automation-service** (端口8002)
- **common-tools-service** (端口8007)

## 使用场景

小诺可以使用这些工具帮您：
1. **设置日历提醒**
2. **自动化网页操作**
3. **批量专利检索**
4. **自动填写表单**

## 示例：设置工作提醒

通过Browser-Use，小诺可以：
- 打开日历应用
- 创建明天9:00的提醒
- 添加您的四个工作任务
- 设置提前15分钟提醒

---

**注意**: 需要确保相关服务已启动才能使用这些自动化功能。