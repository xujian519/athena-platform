#!/bin/bash
# -*- coding: utf-8 -*-
"""
Athena多模态文件系统优化启动脚本
Optimized Startup Script for Athena Multimodal File System
"""

echo "🌐 Athena多模态文件系统优化启动"
echo "=================================="

# 设置工作目录
cd "/Users/xujian/Athena工作平台"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "📦 激活Python虚拟环境..."
    source venv/bin/activate
else
    echo "❌ 未找到虚拟环境，请先创建："
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 检查Python版本
python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python版本: $python_version"

# 设置环境变量
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
export PYTHONIOENCODING=utf-8

# 检查数据库连接
echo ""
echo "🔍 检查PostgreSQL数据库连接..."
if nc -z localhost 5432 2>/dev/null; then
    echo "✅ PostgreSQL (端口5432) 正在运行"
else
    echo "❌ PostgreSQL未运行，请启动PostgreSQL服务"
    echo "   macOS: brew services start postgresql"
    exit 1
fi

# 检查必要的Python包
echo ""
echo "📦 检查必要的Python包..."
required_packages=("fastapi" "uvicorn" "aiofiles" "sqlalchemy" "psycopg2-binary")
missing_packages=()

for package in "${required_packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "  ✅ $package"
    else
        echo "  ❌ $package (缺失)"
        missing_packages+=("$package")
    fi
done

# 安装缺失的包
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo ""
    echo "📥 安装缺失的包..."
    for package in "${missing_packages[@]}"; do
        # 将包名转换为pip安装格式
        case $package in
            "psycopg2_binary")
                pip_name="psycopg2-binary"
                ;;
            *)
                pip_name=$package
                ;;
        esac
        pip install $pip_name
    done
fi

# 创建必要的目录
echo ""
echo "📁 创建必要的存储目录..."
directories=(
    "storage-system/data/documents/multimodal"
    "storage-system/data/documents/thumbnails"
    "storage-system/data/documents/multimodal/image"
    "storage-system/data/documents/multimodal/document"
    "storage-system/data/documents/multimodal/audio"
    "storage-system/data/documents/multimodal/video"
    "storage-system/data/documents/multimodal/data"
    "storage-system/data/documents/multimodal/code"
    "storage-system/data/documents/multimodal/archive"
    "storage-system/data/documents/multimodal/presentation"
    "storage-system/data/documents/multimodal/unknown"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "  📂 创建: $dir"
    else
        echo "  ✅ 已存在: $dir"
    fi
done

# 检查数据库表是否存在
echo ""
echo "🗄️ 检查数据库表结构..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='athena_business',
        user='postgres',
        password='xj781102'
    )
    cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'multimodal_files'
        );
    \"\"\")
    exists = cur.fetchone()[0]
    if exists:
        print('  ✅ multimodal_files表已存在')
    else:
        print('  ⚠️ multimodal_files表不存在，正在创建...')
        cur.execute(\"\"\"
            CREATE TABLE multimodal_files (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_size BIGINT NOT NULL,
                mime_type VARCHAR(100),
                storage_path TEXT NOT NULL,
                file_hash VARCHAR(64) NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by VARCHAR(100),
                processed BOOLEAN DEFAULT FALSE,
                processing_status VARCHAR(50) DEFAULT 'pending',
                processing_data JSONB,
                metadata JSONB,
                extracted_text TEXT,
                tags TEXT[],
                category VARCHAR(100),
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            );
            CREATE INDEX idx_multimodal_files_type ON multimodal_files(file_type);
            CREATE INDEX idx_multimodal_files_upload_time ON multimodal_files(upload_time);
            CREATE INDEX idx_multimodal_files_hash ON multimodal_files(file_hash);
            CREATE INDEX idx_multimodal_files_tags ON multimodal_files USING GIN(tags);
        \"\"\")
        conn.commit()
        print('  ✅ multimodal_files表创建成功')
    conn.close()
except Exception as e:
    print(f'  ❌ 数据库检查失败: {e}')
"

# 启动服务
echo ""
echo "🚀 启动多模态文件系统服务..."
echo "=================================="

# 切换到服务目录
cd services/multimodal

# 检查端口是否被占用
if lsof -Pi :8088 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 端口8088已被占用，尝试停止现有服务..."
    pkill -f "multimodal_api_server.py" 2>/dev/null || true
    sleep 2
fi

# 启动服务
echo "📍 服务地址: http://localhost:8088"
echo "📊 API文档: http://localhost:8088/docs"
echo "🔍 健康检查: http://localhost:8088/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动Python服务
exec python multimodal_api_server.py