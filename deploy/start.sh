#!/bin/bash

echo "🚀 启动按需启动AI系统"

# 检查Python
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3.8+ 未安装"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 运行测试
echo "🧪 运行测试..."
python3 test_basic.py
if [ $? -ne 0 ]; then
    echo "❌ 测试失败"
    exit 1
fi

# 启动应用
echo "🚀 启动应用..."
python3 app.py
