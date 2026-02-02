#!/bin/bash

# 小诺自动化权限配置脚本
# 配置macOS系统权限以支持自动化操作

echo "🔧 小诺自动化权限配置"
echo "===================="

# 检查并请求终端权限
echo "1. 检查终端权限..."
if [ -d "/Applications/Utilities/Terminal.app" ]; then
    echo "✅ 终端应用已安装"
fi

# 检查Python路径
echo "2. 检查Python环境..."
PYTHON_PATH=$(which python3)
if [ -n "$PYTHON_PATH" ]; then
    echo "✅ Python3 路径: $PYTHON_PATH"
else
    echo "❌ 未找到Python3"
    exit 1
fi

# 提示用户手动配置权限
echo ""
echo "📋 需要手动配置的权限："
echo "========================"
echo ""
echo "请按照以下步骤配置系统权限："
echo ""
echo "🔹 步骤1：开启辅助功能权限"
echo "1. 打开 系统偏好设置 → 安全性与隐私 → 辅助功能"
echo "2. 点击左下角的锁图标并输入密码"
echo "3. 添加以下应用到允许列表："
echo "   - Terminal（终端）"
echo "   - Python（如果显示）"
echo ""
echo "🔹 步骤2：开启自动化权限"
echo "1. 打开 系统偏好设置 → 安全性与隐私 → 隐私 → 自动化"
echo "2. 允许以下应用控制其他应用："
echo "   - Terminal → Reminders"
echo "   - Terminal → Calendar"
echo "   - Terminal → System Events"
echo ""
echo "🔹 步骤3：完全磁盘访问权限（可选）"
echo "1. 打开 系统偏好设置 → 安全性与隐私 → 隐私 → 完全磁盘访问"
echo "2. 添加Terminal"
echo ""
echo "⚠️ 注意：配置完成后可能需要重启终端"
echo ""

# 检查权限是否已配置
echo "3. 检查当前权限状态..."
osascript -e 'tell application "System Events" to get name of every process' > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ System Events 权限正常"
else
    echo "❌ 需要配置 System Events 权限"
fi

echo ""
echo "✨ 权限配置指南完成！"
echo "请按上述步骤手动配置权限，然后运行自动化脚本"