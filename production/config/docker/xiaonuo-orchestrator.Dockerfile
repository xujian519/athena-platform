# XiaoNuo统一编排器 - Docker镜像
# 多阶段构建，优化镜像大小

# ============================================================================
# 构建阶段
# ============================================================================
FROM python:3.14-slim AS builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY config/pyproject.toml config/poetry.lock* ./

# 安装Poetry
RUN pip install --no-cache-dir poetry==1.8.0

# 配置Poetry
RUN poetry config virtualenvs.create false \
    && poetry config virtualenvs.in-project false

# 安装依赖（包括开发依赖用于类型检查）
RUN poetry install --no-root --no-interaction --no-ansi --all-extras

# ============================================================================
# 运行阶段
# ============================================================================
FROM python:3.14-slim AS runtime

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # 应用目录
    APP_HOME=/app/xiaonuo \
    # 日志目录
    LOG_HOME=/var/log/xiaonuo \
    # 配置目录
    CONFIG_HOME=/etc/xiaonuo

# 创建非root用户
RUN groupadd -r xiaonuo && useradd -r -g xiaonuo xiaonuo

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 创建目录结构
RUN mkdir -p ${APP_HOME} ${LOG_HOME} ${CONFIG_HOME} \
    && chown -R xiaonuo:xiaonuo ${APP_HOME} ${LOG_HOME} ${CONFIG_HOME}

# 设置工作目录
WORKDIR ${APP_HOME}

# 从构建阶段复制Python依赖
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

# 复制应用程序代码
COPY apps/xiaonuo/orchestrator/ ${APP_HOME}/

# 复制配置文件
COPY config/services/ ${CONFIG_HOME}/services/

# 创建日志目录
RUN mkdir -p ${LOG_HOME} \
    && chown -R xiaonuo:xiaonuo ${LOG_HOME}

# 切换到非root用户
USER xiaonuo

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 默认命令
CMD ["python", "-m", "apps.xiaonuo.orchestrator.main"]

# ============================================================================
# 开发阶段（用于本地开发）
# ============================================================================
FROM runtime AS development

# 切换回root用户安装开发工具
USER root

# 安装开发工具
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    mypy \
    ruff \
    black \
    ipython \
    ipdb

# 切换回非root用户
USER xiaonuo

# 开发模式入口点
ENTRYPOINT ["python", "-m", "pytest", "tests/orchestrator/", "-v"]

# ============================================================================
# 测试阶段（用于CI/CD）
# ============================================================================
FROM development AS test

# 切换回root用户
USER root

# 复制测试文件
COPY tests/ ${APP_HOME}/tests/

# 运行测试
RUN python -m pytest tests/orchestrator/unit/ -v --cov=apps/xiaonuo/orchestrator --cov-report=xml

# 切换回非root用户
USER xiaonuo
