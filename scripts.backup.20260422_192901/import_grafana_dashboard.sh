#!/bin/bash
###############################################################################
# Grafana仪表板导入脚本
# Grafana Dashboard Import Script
#
# 用途: 将Athena执行模块的仪表板导入到Grafana
# 使用: ./import_grafana_dashboard.sh [--url <grafana_url>] [--api-key <key>]
#
# 作者: Athena AI系统
# 版本: 2.0.0
# 创建时间: 2026-01-27
###############################################################################

set -e

# 配置变量
ATHENA_HOME=${ATHENA_HOME:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
DASHBOARD_FILE="$ATHENA_HOME/config/monitoring/grafana_dashboard.json"
GRAFANA_URL=${GRAFANA_URL:-"http://localhost:3000"}
GRAFANA_API_KEY=${GRAFANA_API_KEY:-""}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# 检查仪表板文件
check_dashboard_file() {
    if [ ! -f "$DASHBOARD_FILE" ]; then
        log_error "仪表板文件不存在: $DASHBOARD_FILE"
        exit 1
    fi
    
    log_info "仪表板文件: $DASHBOARD_FILE"
    
    # 验证JSON格式
    if ! jq empty "$DASHBOARD_FILE" 2>/dev/null; then
        log_error "仪表板文件不是有效的JSON格式"
        exit 1
    fi
    
    log_info "仪表板文件格式验证通过"
}

# 检查Grafana连接
check_grafana_connection() {
    log_info "检查Grafana连接..."
    
    if ! curl -sf "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        log_warn "无法连接到Grafana: $GRAFANA_URL"
        log_warn "请确保Grafana正在运行"
        return 1
    fi
    
    log_info "Grafana连接成功"
    
    # 获取Grafana版本
    local version=$(curl -sf "$GRAFANA_URL/api/health" | jq -r '.version' 2>/dev/null || echo "unknown")
    log_info "Grafana版本: $version"
    
    return 0
}

# 通过API导入仪表板
import_dashboard_via_api() {
    log_info "通过API导入仪表板..."
    
    # 准备导入负载
    local payload=$(jq -n \
        --slurpfile dashboard "$DASHBOARD_FILE" \
        --overwrite \
        '{
            dashboard: $dashboard[0],
            overwrite: true,
            message: "Imported by Athena deployment script"
        }' 2>/dev/null)
    
    if [ -z "$payload" ]; then
        log_error "准备导入负载失败"
        return 1
    fi
    
    # 发送导入请求
    local response=$(curl -sf -X POST \
        "$GRAFANA_URL/api/dashboards/db" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        -u "admin:admin" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
        local url=$(echo "$response" | jq -r '.url' 2>/dev/null || echo "unknown")
        
        log_info "导入状态: $status"
        log_info "仪表板URL: $GRAFANA_URL$url"
        return 0
    else
        log_error "导入失败"
        return 1
    fi
}

# 通过API密钥导入仪表板
import_dashboard_with_api_key() {
    log_info "使用API密钥导入仪表板..."
    
    # 准备导入负载
    local payload=$(jq -n \
        --slurpfile dashboard "$DASHBOARD_FILE" \
        --overwrite \
        '{
            dashboard: $dashboard[0],
            overwrite: true,
            message: "Imported by Athena deployment script"
        }' 2>/dev/null)
    
    if [ -z "$payload" ]; then
        log_error "准备导入负载失败"
        return 1
    fi
    
    # 发送导入请求
    local response=$(curl -sf -X POST \
        "$GRAFANA_URL/api/dashboards/db" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $GRAFANA_API_KEY" \
        -d "$payload" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
        local url=$(echo "$response" | jq -r '.url' 2>/dev/null || echo "unknown")
        
        log_info "导入状态: $status"
        log_info "仪表板URL: $GRAFANA_URL$url"
        return 0
    else
        log_error "导入失败"
        return 1
    fi
}

# 显示手动导入说明
show_manual_import_instructions() {
    cat << 'EOF'

========================================
  手动导入步骤
========================================

由于无法自动连接到Grafana，请按照以下步骤手动导入：

1. 访问 Grafana Web UI
   URL: http://localhost:3000
   默认用户名: admin
   默认密码: admin

2. 登录后，点击左侧菜单的 "+" 图标
   选择 "Import dashboard"

3. 选择上传方式：
   
   方式A: 上传JSON文件
   - 点击 "Upload JSON file"
   - 选择文件: config/monitoring/grafana_dashboard.json
   
   方式B: 粘贴JSON内容
   - 点击 "Import via panel json"
   - 复制并粘贴 grafana_dashboard.json 的内容

4. 配置数据源
   - 选择 Prometheus 作为数据源
   - 数据源名称: Prometheus
   - URL: http://localhost:9090
   - 点击 "Import" 按钮

5. 仪表板导入成功！
   - 你应该能看到"Athena执行模块监控仪表板"
   - 包含队列状态、任务速率、性能指标等面板

EOF
}

# 显示配置Prometheus数据源的说明
show_datasource_setup_instructions() {
    cat << 'EOF'

========================================
  配置Prometheus数据源
========================================

如果这是第一次使用Grafana，需要先配置Prometheus数据源：

1. 在Grafana中，点击左侧菜单的 "Configuration" (齿轮图标)
   选择 "Data sources"

2. 点击 "Add data source"

3. 选择 "Prometheus"

4. 配置数据源：
   - Name: Prometheus
   - URL: http://localhost:9090
   - Access: Server (default)
   
5. 点击 "Save & Test"

6. 确认显示 "Data source is working"

然后就可以导入仪表板了。

EOF
}

# 主函数
main() {
    echo "========================================"
    echo " Grafana仪表板导入"
    echo "========================================"
    echo ""
    
    # 检查仪表板文件
    check_dashboard_file
    
    echo ""
    
    # 检查Grafana连接
    if check_grafana_connection; then
        echo ""
        
        # 尝试导入
        if [ -n "$GRAFANA_API_KEY" ]; then
            if import_dashboard_with_api_key; then
                echo ""
                echo -e "${GREEN}仪表板导入成功！${NC}"
                echo ""
                echo "访问地址: $GRAFANA_URL/d/athena-execution-monitoring"
            else
                log_error "API密钥导入失败，请尝试手动导入"
                show_manual_import_instructions
            fi
        else
            if import_dashboard_via_api; then
                echo ""
                echo -e "${GREEN}仪表板导入成功！${NC}"
                echo ""
                echo "访问地址: $GRAFANA_URL/d/athena-execution-monitoring"
            else
                log_error "自动导入失败，请尝试手动导入"
                show_datasource_setup_instructions
                show_manual_import_instructions
            fi
        fi
    else
        log_warn "无法连接到Grafana，显示手动导入说明"
        echo ""
        show_datasource_setup_instructions
        show_manual_import_instructions
    fi
    
    echo ""
    echo "========================================"
    echo " 导入说明汇总"
    echo "========================================"
    echo ""
    echo "仪表板文件: $DASHBOARD_FILE"
    echo "Grafana URL: $GRAFANA_URL"
    echo ""
    echo "快速导入命令（使用API密钥）:"
    echo "  GRAFANA_API_KEY=your_key $0"
    echo ""
    echo "或者使用自定义URL:"
    echo "  GRAFANA_URL=http://your-grafana:3000 $0"
    echo ""
}

# 执行主函数
main "$@"
