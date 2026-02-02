#!/bin/bash
# ArangoDB本地安装脚本 V2 - 适用于macOS

echo "🚀 开始本地安装ArangoDB..."

# 创建工作目录
WORK_DIR="$HOME/arangodb_install"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "📁 工作目录: $WORK_DIR"

# 方法1: 尝试通过Conda安装
if command -v conda &> /dev/null; then
    echo "📦 尝试通过Conda安装..."
    conda install -c conda-forge arangodb -y
    if [ $? -eq 0 ]; then
        echo "✅ Conda安装成功"
        echo "启动ArangoDB: conda run arangodb"
        exit 0
    fi
fi

# 方法2: 直接下载二进制包
echo "📦 直接下载ArangoDB..."

# 获取最新版本（使用固定版本避免网络问题）
ARANGO_VERSION="3.11.0"
ARCH="arm64"  # M4芯片使用arm64

# 下载链接（使用GitHub镜像）
DOWNLOAD_URL="https://github.com/arangodb/arangodb/releases/download/${ARANGO_VERSION}/arangodb3-macos-universal-${ARANGO_VERSION}.tar.gz"

echo "下载地址: $DOWNLOAD_URL"

# 尝试下载
if command -v curl &> /dev/null; then
    curl -L -o "arangodb-macos.tar.gz" "$DOWNLOAD_URL"
elif command -v wget &> /dev/null; then
    wget -O "arangodb-macos.tar.gz" "$DOWNLOAD_URL"
else
    echo "❌ 需要curl或wget来下载"
    exit 1
fi

# 检查下载
if [ ! -f "arangodb-macos.tar.gz" ]; then
    echo "❌ 下载失败"
    echo "请手动访问以下链接下载："
    echo "https://github.com/arangodb/arangodb/releases"
    exit 1
fi

echo "✅ 下载完成"

# 解压
echo "📂 解压..."
tar -xzf "arangodb-macos.tar.gz"

# 找到解压后的目录
ARANGO_DIR=$(find . -maxdepth 1 -type d -name "arangodb*" | head -1)
if [ -z "$ARANGO_DIR" ]; then
    echo "❌ 解压失败"
    exit 1
fi

echo "✅ 解压到: $ARANGO_DIR"

# 安装到系统目录
INSTALL_DIR="/usr/local/arangodb"
echo "📦 安装到: $INSTALL_DIR"

# 需要管理员权限
if [ "$EUID" -ne 0 ]; then
    echo "需要管理员权限安装到系统目录"
    echo "请输入密码..."
    sudo mv "$ARANGO_DIR" "$INSTALL_DIR"
    sudo ln -sf "$INSTALL_DIR/bin/arangod" /usr/local/bin/arangod
    sudo ln -sf "$INSTALL_DIR/bin/arangosh" /usr/local/bin/arangosh
    sudo ln -sf "$INSTALL_DIR/bin/arangobackup" /usr/local/bin/arangobackup
    sudo ln -sf "$INSTALL_DIR/bin/arangorestore" /usr/local/bin/arangorestore
else
    mv "$ARANGO_DIR" "$INSTALL_DIR"
    ln -sf "$INSTALL_DIR/bin/arangod" /usr/local/bin/arangod
    ln -sf "$INSTALL_DIR/bin/arangosh" /usr/local/bin/arangosh
fi

# 创建数据目录
DATA_DIR="$HOME/arangodb_data"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/databases"
mkdir -p "$DATA_DIR/apps"

# 创建配置
CONFIG_DIR="$HOME/.arangodb3"
mkdir -p "$CONFIG_DIR"

# 生成基础配置
cat > "$CONFIG_DIR/arangod.conf" << EOF
[database]
directory = $DATA_DIR

[log]
level = info
file = $DATA_DIR/arangodb.log

[server]
endpoint = tcp://127.0.0.1:8529
authentication = false
EOF

echo "✅ 配置文件已创建: $CONFIG_DIR/arangod.conf"

# 验证安装
echo "🔍 验证安装..."
if command -v arangod &> /dev/null; then
    echo "✅ ArangoDB安装成功!"
    arangod --version
else
    echo "❌ 安装失败"
    exit 1
fi

# 创建启动脚本
cat > "$HOME/start_arangodb.sh" << EOF
#!/bin/bash
# ArangoDB启动脚本

echo "🚀 启动ArangoDB..."

# 检查是否已运行
if pgrep -f "arangod" > /dev/null; then
    echo "ℹ️ ArangoDB已在运行"
    exit 0
fi

# 启动服务
arangod --config "$HOME/.arangodb3/arangod.conf" &

# 等待启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务
if curl -s http://localhost:8529/_api/version > /dev/null; then
    echo "✅ ArangoDB启动成功!"
    echo "📊 Web界面: http://localhost:8528"
    echo "🔌 API端点: http://localhost:8529"
else
    echo "❌ 启动失败"
    tail -n 20 "$DATA_DIR/arangodb.log"
fi
EOF

chmod +x "$HOME/start_arangodb.sh"

# 创建停止脚本
cat > "$HOME/stop_arangodb.sh" << EOF
#!/bin/bash
# ArangoDB停止脚本

echo "🛑 停止ArangoDB..."
pkill -f arangod
echo "✅ 已停止"
EOF

chmod +x "$HOME/stop_arangodb.sh"

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install python-arango > /dev/null 2>&1

echo ""
echo "✅ ArangoDB安装完成！"
echo ""
echo "使用方法："
echo "  启动: $HOME/start_arangodb.sh"
echo "  停止: $HOME/stop_arangodb.sh"
echo "  Web界面: http://localhost:8528"
echo ""
echo "数据目录: $DATA_DIR"
echo "配置文件: $CONFIG_DIR/arangod.conf"