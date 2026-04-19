# ============================================================
# AI伦理框架 - 生产环境Docker镜像
# AI Ethics Framework - Production Docker Image
# ============================================================

# 使用基础镜像，包含所有必要的运行时依赖
FROM python:3.11-slim

# 设置标签
LABEL maintainer="Athena Platform Team <athena@example.com>"
LABEL version="1.0.0"
LABEL description="Athena AI Ethics Framework - Production Environment"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    ETHICS_CONFIG_PATH=/app/config/ethics_config.production.yaml \
    ENVIRONMENT=production \
    # 使用中国镜像源
    PYPI_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PYPI_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 创建非root用户
RUN groupadd -r athena && useradd -r -g athena athena

# 创建必要的目录
RUN mkdir -p /app /app/config /app/logs /var/log/athena /var/run/athena \
    && chown -R athena:athena /app /var/log/athena /var/run/athena

# 设置工作目录
WORKDIR /app

# 先复制pyproject.toml以安装Python依赖
COPY pyproject.toml ./

# 安装Python依赖（分步安装以提高成功率）
RUN pip install --no-cache-dir --timeout=1000 poetry==1.7.1

RUN poetry config virtualenvs.create false && \
    poetry config virtualenvs.in-project false && \
    poetry install --only main --no-interaction --no-ansi

# 复制应用代码 (从项目根目录)
COPY core /app/core/
COPY config /app/config/

# 复制配置文件
COPY core/ethics/config/ethics_config.production.yaml /app/config/

# 健康检查脚本
COPY core/ethics/deployment/healthcheck.py /app/healthcheck.py
RUN chmod +x /app/healthcheck.py

# 启动脚本
COPY core/ethics/deployment/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 切换到非root用户
USER athena

# 暴露端口
# 8080: API服务
# 9091: Prometheus metrics
EXPOSE 8080 9091

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

# 入口点
ENTRYPOINT ["/app/entrypoint.sh"]
