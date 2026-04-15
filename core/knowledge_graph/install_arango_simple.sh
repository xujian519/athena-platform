#!/bin/bash
# ArangoDB简单安装脚本

echo "🚀 开始安装ArangoDB..."

# 设置安装目录
INSTALL_DIR="/usr/local/arangodb3"
DATA_DIR="$HOME/arangodb_data"

# 创建数据目录
mkdir -p "$DATA_DIR"

echo "1. 检查系统架构..."
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    ARCH_SUFFIX="arm64"
else
    ARCH_SUFFIX="x86_64"
fi
echo "   检测到架构: $ARCH ($ARCH_SUFFIX)"

# 尝试多个下载源
DOWNLOAD_URLS=(
    "https://download.arangodb.com/arangodb311/Community/macos/arangodb3-macos-${ARCH_SUFFIX}.tar.gz"
    "https://github.com/arangodb/arangodb/releases/download/3.11.0/arangodb3-macos-universal-3.11.0.tar.gz"
)

# 下载目录
cd ~/Downloads

echo "2. 尝试下载ArangoDB..."
DOWNLOADED=false

for url in "${DOWNLOAD_URLS[@]}"; do
    echo "   尝试: $url"
    filename=$(basename "$url")

    if wget -O "$filename" "$url" 2>/dev/null; then
        echo "   ✅ 下载成功: $filename"
        DOWNLOADED=true
        break
    elif curl -L -o "$filename" "$url" 2>/dev/null; then
        echo "   ✅ 下载成功: $filename"
        DOWNLOADED=true
        break
    else
        echo "   ❌ 下载失败，尝试下一个源"
    fi
done

if [ "$DOWNLOADED" = false ]; then
    echo ""
    echo "❌ 所有下载源都失败了"
    echo ""
    echo "请手动下载："
    echo "1. 访问: https://www.arangodb.com/download-major/"
    echo "2. 选择 macOS Community Edition"
    echo "3. 下载后运行: sudo tar -xzf ~/Downloads/arangodb*.tar.gz -C /usr/local/"
    echo "4. sudo ln -sf /usr/local/arangodb3/bin/arangod /usr/local/bin/"
    exit 1
fi

echo "3. 解压安装..."
# 找到下载的文件
ARANGO_FILE=$(ls ~/Downloads/arangodb3-macos*.tar.gz | head -1)

if [ -z "$ARANGO_FILE" ]; then
    echo "❌ 找不到下载的文件"
    exit 1
fi

# 解压到临时目录
TEMP_DIR=$(mktemp -d)
tar -xzf "$ARANGO_FILE" -C "$TEMP_DIR"

# 找到解压后的目录
EXTRACTED_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "arangodb*" | head -1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo "❌ 解压失败"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# 移动到安装目录
echo "   安装到: $INSTALL_DIR"
sudo rm -rf "$INSTALL_DIR"
sudo mv "$EXTRACTED_DIR" "$INSTALL_DIR"
sudo chown -R $(whoami) "$INSTALL_DIR"

# 创建符号链接
echo "4. 创建命令链接..."
sudo ln -sf "$INSTALL_DIR/bin/arangod" /usr/local/bin/arangod
sudo ln -sf "$INSTALL_DIR/bin/arangosh" /usr/local/bin/arangosh

# 清理临时文件
rm -rf "$TEMP_DIR"

echo "5. 验证安装..."
if command -v arangod &> /dev/null; then
    echo "   ✅ arangod: $(arangod --version 2>&1 | head -1)"
else
    echo "   ❌ arangod未找到"
fi

echo "6. 创建启动脚本..."
cat > "$HOME/start_arangodb.sh" << 'EOF'
#!/bin/bash

# 检查是否已经运行
if pgrep -f "arangod" > /dev/null; then
    echo "ℹ️  ArangoDB已在运行"
    echo "Web界面: http://localhost:8528"
    exit 0
fi

# 启动ArangoDB
echo "🚀 启动ArangoDB..."
arangod \
    --server.endpoint tcp://127.0.0.1:8529 \
    --server.authentication false \
    --database.directory "$HOME/arangodb_data" \
    --log.file "$HOME/arangodb_data/arangodb.log" &

# 等待启动
echo "⏳ 等待服务启动..."
sleep 8

# 检查服务状态
if curl -s http://localhost:8529/_api/version > /dev/null 2>&1; then
    echo "✅ ArangoDB启动成功!"
    echo ""
    echo "📊 访问信息:"
    echo "   Web界面: http://localhost:8528"
    echo "   API端点: http://localhost:8529/_db"
    echo ""
else
    echo "❌ 启动失败，查看日志:"
    tail -n 20 "$HOME/arangodb_data/arangodb.log"
fi
EOF

chmod +x "$HOME/start_arangodb.sh"

echo ""
echo "✅ ArangoDB安装完成！"
echo ""
echo "使用方法："
echo "  启动: $HOME/start_arangodb.sh"
echo "  Web界面: http://localhost:8528"
echo ""
echo "注意：首次运行时会自动创建数据库"