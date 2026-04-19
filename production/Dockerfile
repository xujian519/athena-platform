# 专利智能检索API Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制production目录的文件（因为context是父目录）
COPY production/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（只复制production目录需要的文件）
COPY production/config.py .
COPY production/patent_retrieval_api.py .
COPY production/core ./core
COPY production/scripts ./scripts
COPY production/services ./services
COPY production/utils ./utils
COPY production/data ./data

# 创建日志目录
RUN mkdir -p logs

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "patent_retrieval_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
