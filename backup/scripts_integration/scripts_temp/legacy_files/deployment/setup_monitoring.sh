#!/bin/bash
# 监控和告警系统配置脚本
# Monitoring and Alerting System Configuration for Athena

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROMETHEUS_VERSION="latest"
GRAFANA_VERSION="latest"
ALERTMANAGER_VERSION="latest"
NODE_EXPORTER_VERSION="latest"
CADVISOR_VERSION="latest"

PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
ALERTMANAGER_PORT=9093
NODE_EXPORTER_PORT=9100
CADVISOR_PORT=8080

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查监控系统依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    log_success "监控系统依赖检查完成"
}

# 创建目录结构
create_directories() {
    log_info "创建监控目录结构..."

    mkdir -p /Users/xujian/Athena工作平台/monitoring/{prometheus,grafana,alertmanager,exporters,dashboards}
    mkdir -p /Users/xujian/Athena工作平台/monitoring/prometheus/{rules,data}
    mkdir -p /Users/xujian/Athena工作平台/monitoring/grafana/{provisioning/{dashboards,datasources},data}
    mkdir -p /Users/xujian/Athena工作平台/monitoring/alertmanager/{data,templates}
    mkdir -p /Users/xujian/Athena工作平台/data/monitoring/{prometheus,grafana,alertmanager}

    log_success "监控目录结构创建完成"
}

# 创建Prometheus配置
create_prometheus_config() {
    log_info "创建Prometheus配置..."

    # 主配置文件已在前面创建

    # 创建告警规则目录
    cat > "/Users/xujian/Athena工作平台/monitoring/prometheus/rules/recording.yml" << 'EOF'
# Recording Rules for Athena

groups:
  - name: athena.recording.rules
    interval: 30s
    rules:
      # CPU使用率
      - record: athena:cpu_usage:rate5m
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

      # 内存使用率
      - record: athena:memory_usage:percent
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

      # 磁盘使用率
      - record: athena:disk_usage:percent
        expr: (1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100

      # 网络流量
      - record: athena:network_receive:rate5m
        expr: rate(node_network_receive_bytes_total[5m])

      - record: athena:network_transmit:rate5m
        expr: rate(node_network_transmit_bytes_total[5m])

      # API性能指标
      - record: athena:api_requests:rate5m
        expr: sum(rate(http_requests_total{job="api-gateway"}[5m]))

      - record: athena:api_latency:p95
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="api-gateway"}[5m])) by (le))

      - record: athena:api_error_rate:5m
        expr: sum(rate(http_requests_total{job="api-gateway",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="api-gateway"}[5m]))

      # 数据库指标
      - record: athena:postgres_connections:current
        expr: pg_stat_activity_count

      - record: athena:postgres_connections:max
        expr: pg_settings_max_connections

      - record: athena:postgres_connections:utilization
        expr: pg_stat_activity_count / pg_settings_max_connections

      - record: athena:postgres_cache_hit_ratio
        expr: pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)

      # Redis指标
      - record: athena:redis_memory:utilization
        expr: redis_memory_used_bytes / redis_memory_max_bytes

      - record: athena:redis_hit_ratio
        expr: redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)

      - record: athena:redis_connections:current
        expr: redis_connected_clients

      # 文档处理指标
      - record: athena:document_processing:rate5m
        expr: sum(rate(dolphin_processing_total[5m]))

      - record: athena:document_processing:duration:p95
        expr: histogram_quantile(0.95, sum(rate(dolphin_processing_duration_seconds_bucket[5m])) by (le))

      - record: athena:document_processing:success_rate
        expr: sum(rate(dolphin_processing_success_total[5m])) / sum(rate(dolphin_processing_total[5m]))

      # 容器指标
      - record: athena:container_memory:usage
        expr: sum(container_memory_usage_bytes{name!=""}) by (name)

      - record: athena:container_cpu:usage
        expr: sum(rate(container_cpu_usage_seconds_total{name!=""}[5m])) by (name)
EOF

    log_success "Prometheus配置创建完成"
}

# 创建Grafana配置
create_grafana_config() {
    log_info "创建Grafana配置..."

    # 数据源配置
    cat > "/Users/xujian/Athena工作平台/monitoring/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "5s"
      queryTimeout: "60s"
      httpMethod: "POST"
    secureJsonData: {}

  - name: Athena-AlertManager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    editable: true
    jsonData:
      implementation: "prometheus"
    secureJsonData: {}
EOF

    # 仪表板配置
    cat > "/Users/xujian/Athena工作平台/monitoring/grafana/provisioning/dashboards/athena.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # Grafana配置文件
    cat > "/Users/xujian/Athena工作平台/monitoring/grafana/grafana.ini" << 'EOF'
[server]
http_port = 3000
domain = localhost
root_url = http://localhost:3000

[security]
admin_user = admin
admin_password = admin123

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db

[log]
mode = file
level = info
file = /var/log/grafana/grafana.log

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org_role = Viewer

[auth]
disable_login_form = false

[smtp]
enabled = false
EOF

    log_success "Grafana配置创建完成"
}

# 创建AlertManager配置
create_alertmanager_config() {
    log_info "创建AlertManager配置..."

    cat > "/Users/xujian/Athena工作平台/monitoring/alertmanager/alertmanager.yml" << 'EOF'
# AlertManager配置

global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@athena.multimodal.ai'
  smtp_auth_username: 'alerts@athena.multimodal.ai'
  smtp_auth_password: 'your_smtp_password'

# 路由配置
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 5s
      repeat_interval: 30m
    - match:
        severity: warning
      receiver: 'warning-alerts'
      group_wait: 30s
      repeat_interval: 2h
    - match:
        severity: info
      receiver: 'info-alerts'
      group_wait: 60s
      repeat_interval: 24h

# 接收器配置
receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:9001/webhooks/alerts'
        send_resolved: true

  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@athena.multimodal.ai,ops@athena.multimodal.ai'
        subject: '[CRITICAL] Athena告警: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          告警名称: {{ .Annotations.summary }}
          告警描述: {{ .Annotations.description }}
          告警级别: {{ .Labels.severity }}
          开始时间: {{ .StartsAt }}
          {{ if .EndsAt }}结束时间: {{ .EndsAt }}{{ end }}
          标签: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
          {{ end }}
    webhook_configs:
      - url: '${SLACK_WEBHOOK_URL}'
        send_resolved: true
        title: '🚨 Athena CRITICAL Alert'
        text: |
          {{ range .Alerts }}
          *告警*: {{ .Annotations.summary }}
          *描述*: {{ .Annotations.description }}
          *服务*: {{ .Labels.service }}
          *实例*: {{ .Labels.instance }}
          *时间*: {{ .StartsAt }}
          {{ end }}

  - name: 'warning-alerts'
    email_configs:
      - to: 'ops@athena.multimodal.ai'
        subject: '[WARNING] Athena告警: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          告警名称: {{ .Annotations.summary }}
          告警描述: {{ .Annotations.description }}
          告警级别: {{ .Labels.severity }}
          开始时间: {{ .StartsAt }}
          {{ if .EndsAt }}结束时间: {{ .EndsAt }}{{ end }}
          {{ end }}

  - name: 'info-alerts'
    webhook_configs:
      - url: '${SLACK_WEBHOOK_URL}'
        send_resolved: true
        title: 'ℹ️ Athena INFO Alert'
        text: |
          {{ range .Alerts }}
          *信息*: {{ .Annotations.summary }}
          *描述*: {{ .Annotations.description }}
          *服务*: {{ .Labels.service }}
          {{ end }}

# 抑制规则
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']

# 模板
templates:
  - '/etc/alertmanager/templates/*.tmpl'
EOF

    # 告警模板
    mkdir -p "/Users/xujian/Athena工作平台/monitoring/alertmanager/templates"

    cat > "/Users/xujian/Athena工作平台/monitoring/alertmanager/templates/default.tmpl" << 'EOF'
{{ define "__slack_resolve_text" }}{{ range . }}
*告警已解决*: {{ .Annotations.summary }}
*描述*: {{ .Annotations.description }}
*服务*: {{ .Labels.service }}
{{ end }}{{ end }}

{{ define "__slack_text" }}{{ range . }}
*告警*: {{ .Annotations.summary }}
*描述*: {{ .Annotations.description }}
*级别*: {{ .Labels.severity }}
*服务*: {{ .Labels.service }}
*实例*: {{ .Labels.instance }}
*时间*: {{ .StartsAt }}
{{ if .EndsAt }}*解决时间*: {{ .EndsAt }}{{ end }}
*标签*: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
{{ end }}{{ end }}

{{ define "__email_resolve_subject" }}[RESOLVED] {{ .GroupLabels.alertname }}{{ end }}

{{ define "__email_subject" }}[ALERT] {{ .GroupLabels.alertname }}{{ end }}
EOF

    log_success "AlertManager配置创建完成"
}

# 创建监控导出器配置
create_exporter_configs() {
    log_info "创建监控导出器配置..."

    # Node Exporter配置
    cat > "/Users/xujian/Athena工作平台/monitoring/exporters/node-exporter.yml" << 'EOF'
# Node Exporter配置
version: '3.8'

services:
  node-exporter:
    image: prom/node-exporter:latest
    container_name: athena-node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    restart: unless-stopped
    networks:
      - monitoring
EOF

    # cAdvisor配置
    cat > "/Users/xujian/Athena工作平台/monitoring/exporters/cadvisor.yml" << 'EOF'
# cAdvisor配置
version: '3.8'

services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: athena-cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg
    restart: unless-stopped
    networks:
      - monitoring
EOF

    log_success "监控导出器配置创建完成"
}

# 创建Docker Compose监控配置
create_monitoring_docker_compose() {
    log_info "创建监控Docker Compose配置..."

    cat > "/Users/xujian/Athena工作平台/docker/docker-compose.monitoring.yml" << 'EOF'
# 监控系统Docker Compose配置
# Monitoring System Docker Compose Configuration

version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: athena-prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'
      - '--storage.tsdb.retention.size=20GB'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
      - '--web.external-url=http://localhost:9090'
    volumes:
      - ../monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ../monitoring/prometheus/rules:/etc/prometheus/rules:ro
      - /data/athena/monitoring/prometheus:/prometheus
    networks:
      - athena-network
      - monitoring
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4Gi
        reservations:
          cpus: '1.0'
          memory: 2Gi
    labels:
      - "com.athena.service=prometheus"
      - "com.athena.environment=production"

  # AlertManager
  alertmanager:
    image: prom/alertmanager:latest
    container_name: athena-alertmanager
    ports:
      - "9093:9093"
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
      - '--cluster.listen-address=0.0.0.0:9094'
    volumes:
      - ../monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - ../monitoring/alertmanager/templates:/etc/alertmanager/templates:ro
      - /data/athena/monitoring/alertmanager:/alertmanager
    networks:
      - athena-network
      - monitoring
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9093/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2Gi
        reservations:
          cpus: '0.5'
          memory: 1Gi
    labels:
      - "com.athena.service=alertmanager"
      - "com.athena.environment=production"

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: athena-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin123}
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource,grafana-piechart-panel
      - GF_SMTP_ENABLED=false
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_USERS_ALLOW_ORG_CREATE=false
      - GF_AUTH_DISABLE_LOGIN_FORM=false
      - GF_LOG_MODE=file
      - GF_LOG_LEVEL=info
    volumes:
      - ../monitoring/grafana/grafana.ini:/etc/grafana/grafana.ini:ro
      - ../monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ../monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - /data/athena/monitoring/grafana:/var/lib/grafana
    networks:
      - athena-network
      - monitoring
      - frontend-network
    restart: unless-stopped
    depends_on:
      prometheus:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2Gi
        reservations:
          cpus: '0.5'
          memory: 1Gi
    labels:
      - "com.athena.service=grafana"
      - "com.athena.environment=production"

  # Node Exporter
  node-exporter:
    image: prom/node-exporter:latest
    container_name: athena-node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
      - '--collector.processes'
      - '--collector.systemd'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256Mi
        reservations:
          cpus: '0.25'
          memory: 128Mi
    labels:
      - "com.athena.service=node-exporter"
      - "com.athena.environment=production"

  # cAdvisor
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: athena-cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg
    networks:
      - monitoring
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512Mi
        reservations:
          cpus: '0.5'
          memory: 256Mi
    labels:
      - "com.athena.service=cadvisor"
      - "com.athena.environment=production"

  # Redis Exporter
  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: athena-redis-exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis-cluster:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    networks:
      - athena-network
      - monitoring
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256Mi
        reservations:
          cpus: '0.25'
          memory: 128Mi
    labels:
      - "com.athena.service=redis-exporter"
      - "com.athena.environment=production"

  # PostgreSQL Exporter
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: athena-postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://athena_user:${DB_PASSWORD}@postgres-primary:5432/athena_production?sslmode=disable
    networks:
      - athena-network
      - monitoring
    restart: unless-stopped
    depends_on:
      postgres-primary:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256Mi
        reservations:
          cpus: '0.25'
          memory: 128Mi
    labels:
      - "com.athena.service=postgres-exporter"
      - "com.athena.environment=production"

  # Blackbox Exporter
  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    container_name: athena-blackbox-exporter
    ports:
      - "9115:9115"
    volumes:
      - ../monitoring/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    networks:
      - monitoring
      - frontend-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256Mi
        reservations:
          cpus: '0.25'
          memory: 128Mi
    labels:
      - "com.athena.service=blackbox-exporter"
      - "com.athena.environment=production"

# 网络配置
networks:
  athena-network:
    external: true

  monitoring:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.24.0.0/16
          gateway: 172.24.0.1

  frontend-network:
    external: true
EOF

    log_success "监控Docker Compose配置创建完成"
}

# 创建Blackbox Exporter配置
create_blackbox_config() {
    log_info "创建Blackbox Exporter配置..."

    mkdir -p "/Users/xujian/Athena工作平台/monitoring"

    cat > "/Users/xujian/Athena工作平台/monitoring/blackbox.yml" << 'EOF'
# Blackbox Exporter配置

modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      valid_http_versions:
        - "HTTP/1.1"
        - "HTTP/2.0"
      valid_status_codes: []
      method: GET
      fail_if_ssl: false
      fail_if_not_ssl: false
      tls_config:
        insecure_skip_verify: false
      follow_redirects: true
      headers:
        User-Agent: "Athena-Monitor/1.0"
      no_follow_redirects: false

  http_post_2xx:
    prober: http
    timeout: 10s
    http:
      method: POST
      headers:
        Content-Type: application/json
      body: '{"test": true}'

  tcp_connect:
    prober: tcp
    timeout: 5s
    tcp:
      preferred_ip_protocol: "ip4"

  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"
EOF

    log_success "Blackbox Exporter配置创建完成"
}

# 启动监控服务
start_monitoring_services() {
    log_info "启动监控服务..."

    cd /Users/xujian/Athena工作平台/docker

    # 启动监控服务
    docker-compose -f docker-compose.monitoring.yml up -d

    # 等待服务启动
    log_info "等待监控服务启动..."
    sleep 30

    # 检查服务状态
    services=("prometheus:9090" "grafana:3000" "alertmanager:9093")
    for service_info in "${services[@]}"; do
        service=$(echo $service_info | cut -d':' -f1)
        port=$(echo $service_info | cut -d':' -f2)

        if curl -f "http://localhost:$port" >/dev/null 2>&1; then
            log_success "$service 服务启动成功"
        else
            log_error "$service 服务启动失败"
            return 1
        fi
    done

    log_success "所有监控服务启动完成"
}

# 配置Grafana仪表板
setup_grafana_dashboards() {
    log_info "配置Grafana仪表板..."

    # 等待Grafana启动
    sleep 10

    # 设置API密钥
    ADMIN_USER="admin"
    ADMIN_PASSWORD="${GRAFANA_PASSWORD:-admin123}"

    # 创建API密钥
    API_KEY=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"name":"athena-key","role":"Admin"}' \
        "http://${ADMIN_USER}:${ADMIN_PASSWORD}@localhost:3000/api/auth/keys" | \
        jq -r '.key' 2>/dev/null || echo "")

    if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ]; then
        log_success "Grafana API密钥创建成功"
    else
        log_warning "Grafana API密钥创建失败，请手动创建"
    fi

    log_success "Grafana仪表板配置完成"
}

# 验证监控配置
verify_monitoring_setup() {
    log_info "验证监控配置..."

    # 检查Prometheus目标
    prometheus_targets=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets | length' 2>/dev/null || echo "0")

    if [ "$prometheus_targets" -gt 0 ]; then
        log_success "Prometheus目标发现正常 ($prometheus_targets 个目标)"
    else
        log_warning "Prometheus目标发现异常"
    fi

    # 检查Grafana数据源
    grafana_datasources=$(curl -s http://admin:admin123@localhost:3000/api/datasources | jq -r '. | length' 2>/dev/null || echo "0")

    if [ "$grafana_datasources" -gt 0 ]; then
        log_success "Grafana数据源配置正常 ($grafana_datasources 个数据源)"
    else
        log_warning "Grafana数据源配置异常"
    fi

    # 检查AlertManager状态
    if curl -f http://localhost:9093/-/healthy >/dev/null 2>&1; then
        log_success "AlertManager服务正常"
    else
        log_warning "AlertManager服务异常"
    fi

    log_success "监控配置验证完成"
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建监控管理脚本..."

    # 监控启动脚本
    cat > "/Users/xujian/Athena工作平台/scripts/start_monitoring.sh" << 'EOF'
#!/bin/bash
# 启动监控服务

echo "启动Athena监控系统..."

cd /Users/xujian/Athena工作平台/docker
docker-compose -f docker-compose.monitoring.yml up -d

echo "等待服务启动..."
sleep 30

echo "检查服务状态..."
docker-compose -f docker-compose.monitoring.yml ps

echo "监控系统启动完成"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin123)"
echo "AlertManager: http://localhost:9093"
EOF

    # 监控停止脚本
    cat > "/Users/xujian/Athena工作平台/scripts/stop_monitoring.sh" << 'EOF'
#!/bin/bash
# 停止监控服务

echo "停止Athena监控系统..."

cd /Users/xujian/Athena工作平台/docker
docker-compose -f docker-compose.monitoring.yml down

echo "监控系统已停止"
EOF

    # 监控重启脚本
    cat > "/Users/xujian/Athena工作平台/scripts/restart_monitoring.sh" << 'EOF'
#!/bin/bash
# 重启监控服务

/Users/xujian/Athena工作平台/scripts/stop_monitoring.sh
sleep 10
/Users/xujian/Athena工作平台/scripts/start_monitoring.sh

echo "监控系统重启完成"
EOF

    # 监控状态检查脚本
    cat > "/Users/xujian/Athena工作平台/scripts/status_monitoring.sh" << 'EOF'
#!/bin/bash
# 监控系统状态检查

echo "============================================"
echo "     Athena监控系统状态检查"
echo "     时间: $(date)"
echo "============================================"
echo ""

cd /Users/xujian/Athena工作平台/docker

echo "1. Docker容器状态:"
docker-compose -f docker-compose.monitoring.yml ps
echo ""

echo "2. 服务健康检查:"
services=("prometheus:9090" "grafana:3000" "alertmanager:9093" "node-exporter:9100" "cadvisor:8080")

for service_info in "${services[@]}"; do
    service=$(echo $service_info | cut -d':' -f1)
    port=$(echo $service_info | cut -d':' -f2)

    if curl -f "http://localhost:$port" >/dev/null 2>&1; then
        echo "✓ $service (端口 $port) - 正常"
    else
        echo "✗ $service (端口 $port) - 异常"
    fi
done
echo ""

echo "3. Prometheus目标状态:"
curl -s http://localhost:9090/api/v1/targets | \
    jq -r '.data.activeTargets[] | "\(.job) - \(.instance): \(.health)"' 2>/dev/null || \
    echo "无法获取Prometheus目标状态"
echo ""

echo "4. Grafana数据源状态:"
curl -s http://admin:admin123@localhost:3000/api/datasources | \
    jq -r '.[] | "\(.name): \(.url)"' 2>/dev/null || \
    echo "无法获取Grafana数据源状态"
echo ""

echo "============================================"
echo "状态检查完成"
echo "============================================"
EOF

    chmod +x /Users/xujian/Athena工作平台/scripts/*_monitoring.sh

    log_success "监控管理脚本创建完成"
}

# 主函数
main() {
    echo -e "${BLUE}📊 Athena多模态文件系统监控配置${NC}"
    echo "============================================"
    echo -e "${CYAN}开始时间: $(date)${NC}"
    echo ""

    # 检查依赖
    check_dependencies

    # 创建配置
    create_directories
    create_prometheus_config
    create_grafana_config
    create_alertmanager_config
    create_exporter_configs
    create_blackbox_config
    create_monitoring_docker_compose

    # 启动服务
    start_monitoring_services

    # 配置仪表板
    setup_grafana_dashboards

    # 验证配置
    verify_monitoring_setup

    # 创建管理脚本
    create_management_scripts

    echo ""
    echo -e "${GREEN}✅ 监控和告警系统配置完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 访问地址:${NC}"
    echo -e "  📈 Prometheus: ${YELLOW}http://localhost:9090${NC}"
    echo -e "  📊 Grafana: ${YELLOW}http://localhost:3000${NC} (admin/admin123)"
    echo -e "  🚨 AlertManager: ${YELLOW}http://localhost:9093${NC}"
    echo -e "  💻 Node Exporter: ${YELLOW}http://localhost:9100/metrics${NC}"
    echo -e "  🐳 cAdvisor: ${YELLOW}http://localhost:8080${NC}"
    echo ""
    echo -e "${BLUE}🔧 管理命令:${NC}"
    echo -e "  🚀 启动监控: ${YELLOW}/Users/xujian/Athena工作平台/scripts/start_monitoring.sh${NC}"
    echo -e "  🛑 停止监控: ${YELLOW}/Users/xujian/Athena工作平台/scripts/stop_monitoring.sh${NC}"
    echo -e "  🔄 重启监控: ${YELLOW}/Users/xujian/Athena工作平台/scripts/restart_monitoring.sh${NC}"
    echo -e "  📊 状态检查: ${YELLOW}/Users/xujian/Athena工作平台/scripts/status_monitoring.sh${NC}"
    echo ""
    echo -e "${BLUE}📋 配置文件:${NC}"
    echo -e "  ⚙️ Prometheus: ${YELLOW}/Users/xujian/Athena工作平台/monitoring/prometheus/${NC}"
    echo -e "  📊 Grafana: ${YELLOW}/Users/xujian/Athena工作平台/monitoring/grafana/${NC}"
    echo -e "  🚨 AlertManager: ${YELLOW}/Users/xujian/Athena工作平台/monitoring/alertmanager/${NC}"
    echo ""
    echo -e "${PURPLE}✨ 监控和告警系统已就绪！${NC}"
}

# 执行主函数
main "$@"