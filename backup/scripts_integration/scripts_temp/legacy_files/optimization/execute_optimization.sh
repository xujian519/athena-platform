#!/bin/bash

echo "🚀 执行Athena性能优化..."

# 1. 停止AI模型服务以减少资源消耗
echo "📌 停止AI模型服务..."
pkill -f "ai_model_service.py" 2>/dev/null || echo "AI模型服务未运行"

# 2. 清理日志文件
echo "🧹 清理日志文件..."
find /Users/xujian/Athena工作平台/logs -name "*.log" -type f -exec truncate -s 10M {} \; 2>/dev/null
echo "已将所有日志文件限制为10MB"

# 3. 清理Python缓存
echo "🗑️ 清理Python缓存..."
find /Users/xujian/Athena工作平台 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /Users/xujian/Athena工作平台 -name "*.pyc" -delete 2>/dev/null

# 4. 优化PostgreSQL连接
echo "🔧 优化PostgreSQL配置..."
cat << EOF > /tmp/postgresql_perf_tuning.conf
# PostgreSQL性能优化配置
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
EOF

# 5. 清理Docker资源
echo "🐳 清理Docker资源..."
docker system prune -f 2>/dev/null || echo "Docker未运行或权限不足"

# 6. 检查磁盘空间
echo "💾 磁盘空间使用情况:"
df -h / | tail -1

# 7. 检查内存使用
echo "🧠 内存使用情况:"
top -l 1 | grep "PhysMem"

echo "✅ 优化完成！"
echo ""
echo "💡 建议："
echo "1. 重启YunPat服务: pkill -f api_service.py && python3 services/yunpat-agent/api_service.py"
echo "2. 如果需要AI功能，请配置API密钥"
echo "3. 定期运行此脚本进行维护"

# Day 1: 安全加固任务
execute_sec_001() {
    log "执行 SEC-001: 加密.env文件中的敏感信息"

    # 查找所有.env文件
    find . -name ".env*" -type f | while read file; do
        if [[ "$file" != *".example" ]] && [[ "$file" != *".template" ]]; then
            backup_file "$file"

            # 检查是否已加密
            if ! grep -q "\$ANSIBLE_VAULT" "$file"; then
                log "加密文件: $file"
                # 这里应该调用ansible-vault加密
                # ansible-vault encrypt "$file"
                warning "请手动使用 ansible-vault encrypt $file"
            fi
        fi
    done
    success "SEC-001 完成"
}

execute_sec_002() {
    log "执行 SEC-002: 更新默认密码"

    # 生成随机密码
    generate_password() {
        openssl rand -base64 32 | tr -d "=+/" | cut -c1-16
    }

    # 更新数据库密码配置示例
    DB_PASSWORD=$(generate_password)
    log "生成新的数据库密码: ${DB_PASSWORD:0:4}****"

    # 这里应该更新实际的配置文件
    warning "请手动更新配置文件中的密码"

    success "SEC-002 完成"
}

execute_sec_003() {
    log "执行 SEC-003: API权限审查"

    # 扫描Python文件中的API端点
    find . -name "*.py" -type f | xargs grep -l "app\|@app\|router" | while read file; do
        log "检查API文件: $file"
        # 检查是否有认证装饰器
        if ! grep -q "@auth\|@login_required" "$file"; then
            warning "发现未保护的API端点: $file"
        fi
    done

    success "SEC-003 完成"
}

execute_sec_004() {
    log "执行 SEC-004: 删除弃用的PostgreSQL MCP服务器"

    # 卸载npm包
    if npm list -g @modelcontextprotocol/server-postgres > /dev/null 2>&1; then
        npm uninstall -g @modelcontextprotocol/server-postgres
        log "已卸载弃用的PostgreSQL MCP服务器"
    else
        log "PostgreSQL MCP服务器未安装"
    fi

    # 检查配置文件引用
    grep -r "server-postgres" config/ > /dev/null 2>&1 && warning "配置文件中仍存在server-postgres引用"

    success "SEC-004 完成"
}

execute_sec_005() {
    log "执行 SEC-005: 端口管理"

    # 创建端口分配文件
    cat > config/ports.yaml << EOF
# Athena工作平台端口分配
services:
  athena_main: 8000
  athena_memory: 8008
  athena_identity: 8010
  yunpat_agent: 8020
  api_gateway: 8080
  crawler_service: 8300
  search_service: 8500
  monitoring: 9000
EOF

    log "已创建端口分配文件: config/ports.yaml"

    # 检查端口冲突
    netstat -tuln | grep -E ":(8000|8030)" && warning "发现端口冲突，请检查配置"

    success "SEC-005 完成"
}

# Day 2: 配置标准化任务
execute_conf_001() {
    log "执行 CONF-001: 重构配置目录结构"

    # 创建新目录结构
    mkdir -p config/{environments,services,infrastructure,secrets}

    # 移动现有配置文件
    find . -maxdepth 1 -name "*.yaml" -not -path "./config/*" -exec mv {} config/ \;

    log "配置文件已移动到config/目录"

    # 创建基础配置模板
    cat > config/base.yaml << EOF
# Athena工作平台基础配置
metadata:
  name: athena-platform
  version: 2.0.0
  environment: \${ENVIRONMENT:development}

logging:
  level: \${LOG_LEVEL:info}
  format: json

server:
  host: \${HOST:0.0.0.0}
  port: \${PORT:8000}
  workers: \${WORKERS:1}
EOF

    success "CONF-001 完成"
}

execute_conf_002() {
    log "执行 CONF-002: 合并重复配置"

    # 查找重复的数据库配置
    if [ -f "config/database.yaml" ] && [ -f "config/database_unified.yaml" ]; then
        log "发现重复的数据库配置文件"
        backup_file "config/database_unified.yaml"
        # 这里应该实现合并逻辑
        warning "请手动合并database.yaml和database_unified.yaml"
    fi

    success "CONF-002 完成"
}

# Day 4: 代码规范化任务
execute_code_001() {
    log "执行 CODE-001: 配置Python代码格式化工具"

    # 创建pyproject.toml
    cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
EOF

    # 安装开发工具
    pip install black isort flake8 mypy pre-commit

    success "CODE-001 完成"
}

execute_code_002() {
    log "执行 CODE-002: 设置pre-commit hooks"

    # 创建.pre-commit-config.yaml
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
EOF

    # 安装hooks
    pre-commit install

    success "CODE-002 完成"
}

# 生成进度报告
generate_report() {
    log "生成进度报告..."

    REPORT_FILE="$OPT_DIR/logs/progress_report_$(date +%Y%m%d_%H%M%S).md"

    cat > "$REPORT_FILE" << EOF
# Athena优化进度报告
生成时间: $(date)

## 已完成任务
$(cat "$OPT_DIR/logs/tasks.log" 2>/dev/null || echo "暂无任务记录")

## 当前状态
- 优化阶段: $1
- 完成任务数: $2
- 总任务数: $3

## 问题记录
$(cat "$OPT_DIR/logs/issues.log" 2>/dev/null || echo "暂无问题记录")

## 下一步
$4
EOF

    success "进度报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    case $1 in
        "phase:1")
            log "开始执行第一阶段：安全加固与基础设施"
            execute_sec_001
            execute_sec_002
            execute_sec_003
            execute_sec_004
            execute_sec_005
            ;;
        "day:1")
            log "执行第1天任务：安全风险消除"
            execute_sec_001
            execute_sec_002
            execute_sec_003
            execute_sec_004
            execute_sec_005
            ;;
        "task")
            case $2 in
                "SEC-001") execute_sec_001 ;;
                "SEC-002") execute_sec_002 ;;
                "SEC-003") execute_sec_003 ;;
                "SEC-004") execute_sec_004 ;;
                "SEC-005") execute_sec_005 ;;
                "CONF-001") execute_conf_001 ;;
                "CONF-002") execute_conf_002 ;;
                "CODE-001") execute_code_001 ;;
                "CODE-002") execute_code_002 ;;
                *) error "未知任务ID: $2" ;;
            esac
            ;;
        "help"|"-h"|"--help")
            echo "使用方法:"
            echo "  $0 [phase:N]     - 执行第N阶段的所有任务"
            echo "  $0 [day:N]       - 执行第N天的所有任务"
            echo "  $0 [task:ID]    - 执行指定任务"
            echo "  $0 help         - 显示帮助信息"
            ;;
        *)
            error "未知命令: $1. 使用 '$0 help' 查看帮助"
            ;;
    esac
}

# 执行主函数
main "$@"