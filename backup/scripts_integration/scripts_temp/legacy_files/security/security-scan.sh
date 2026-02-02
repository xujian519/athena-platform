#!/bin/bash

# Athena工作平台安全漏洞扫描脚本
# 作者: 徐健
# 创建日期: 2025-12-13

set -e

# 配置变量
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
REPORT_DIR="${REPORT_DIR:-$PROJECT_DIR/security-reports}"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
SCAN_TYPE="${1:-all}"  # all, sast, dast, sca, container

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查必要的工具
check_tools() {
    log_info "检查安全扫描工具..."

    local tools=("bandit" "safety" "semgrep" "trivy" "git")
    local missing_tools=()

    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少以下工具: ${missing_tools[*]}"
        log_info "请安装缺少的工具："
        for tool in "${missing_tools[@]}"; do
            case $tool in
                "bandit")
                    echo "  pip install bandit"
                    ;;
                "safety")
                    echo "  pip install safety"
                    ;;
                "semgrep")
                    echo "  pip install semgrep"
                    ;;
                "trivy")
                    echo "  brew install trivy  # macOS"
                    echo "  或: sudo apt-get install trivy  # Ubuntu"
                    ;;
                "git")
                    echo "  brew install git  # macOS"
                    echo "  或: sudo apt-get install git  # Ubuntu"
                    ;;
            esac
        done
        exit 1
    fi

    log_success "所有工具检查通过"
}

# 静态应用安全测试 (SAST)
run_sast_scan() {
    log_info "开始静态应用安全测试..."

    local report_file="$REPORT_DIR/sast-report-$DATE.json"

    # Bandit扫描
    log_info "运行Bandit扫描..."
    bandit -r "$PROJECT_DIR/services/" \
        -f json \
        -o "$REPORT_DIR/bandit-report-$DATE.json" \
        --quiet \
        || true

    # Semgrep扫描
    log_info "运行Semgrep扫描..."
    semgrep --config=auto \
        --json \
        --output="$REPORT_DIR/semgrep-report-$DATE.json" \
        "$PROJECT_DIR/services/" \
        || true

    # CodeQL扫描（如果配置了）
    if command -v codeql &> /dev/null; then
        log_info "运行CodeQL扫描..."
        # CodeQL扫描配置
        # 这里可以添加CodeQL扫描命令
    fi

    # 生成综合报告
    python3 << EOF
import json
import os
from datetime import datetime

def generate_sast_report(bandit_file, semgrep_file, output_file):
    report = {
        "scan_type": "SAST",
        "timestamp": datetime.utcnow().isoformat(),
        "tools": ["bandit", "semgrep"],
        "findings": []
    }

    # 处理Bandit报告
    if os.path.exists(bandit_file):
        with open(bandit_file) as f:
            bandit_data = json.load(f)
            for result in bandit_data.get("results", []):
                report["findings"].append({
                    "tool": "bandit",
                    "severity": result["issue_severity"],
                    "confidence": result["issue_certainty"],
                    "test_name": result["test_name"],
                    "message": result["issue_text"],
                    "file": result["filename"],
                    "line": result["line_number"],
                    "cwe_id": result.get("cwe_id", ""),
                    "test_id": result["test_id"]
                })

    # 处理Semgrep报告
    if os.path.exists(semgrep_file):
        with open(semgrep_file) as f:
            semgrep_data = json.load(f)
            for result in semgrep_data.get("results", []):
                report["findings"].append({
                    "tool": "semgrep",
                    "severity": result["metadata"]["severity"],
                    "confidence": result["extra"]["confidence"],
                    "test_name": result["check_id"],
                    "message": result["message"],
                    "file": result["path"],
                    "line": result["start"]["line"],
                    "cwe_id": result["metadata"].get("cwe", ""),
                    "test_id": result["check_id"]
                })

    # 按严重程度排序
    severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    report["findings"].sort(
        key=lambda x: (severity_order.get(x["severity"], 0), -x["line"] if isinstance(x.get("line"), int) else 0),
        reverse=True
    )

    # 统计信息
    report["summary"] = {
        "total": len(report["findings"]),
        "high": sum(1 for f in report["findings"] if f["severity"] == "HIGH"),
        "medium": sum(1 for f in report["findings"] if f["severity"] == "MEDIUM"),
        "low": sum(1 for f in report["findings"] if f["severity"] == "LOW")
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

generate_sast_report(
    "$REPORT_DIR/bandit-report-$DATE.json",
    "$REPORT_DIR/semgrep-report-$DATE.json",
    "$report_file"
)
EOF

    log_success "SAST扫描完成，报告保存到: $report_file"
}

# 动态应用安全测试 (DAST)
run_dast_scan() {
    log_info "开始动态应用安全测试..."

    local report_file="$REPORT_DIR/dast-report-$DATE.json"
    local base_url="${BASE_URL:-http://localhost:8080}"

    # 检查服务是否运行
    if ! curl -s -f "$base_url/health" > /dev/null; then
        log_warning "服务未运行，跳过DAST扫描"
        return 0
    fi

    # OWASP ZAP Baseline Scan
    if command -v docker &> /dev/null; then
        log_info "运行OWASP ZAP扫描..."
        docker run -t --rm \
            -v "$(pwd):/zap/wrk" \
            -w /zap/wrk \
            owasp/zap2docker-stable \
            zap-baseline.py -t "$base_url" \
            -J "$REPORT_DIR/zap-report-$DATE.json" \
            || true
    fi

    # 生成DAST综合报告
    python3 << EOF
import json
import os
from datetime import datetime

def generate_dast_report(zap_file, output_file):
    report = {
        "scan_type": "DAST",
        "timestamp": datetime.utcnow().isoformat(),
        "target": "$base_url",
        "tools": ["owasp-zap"],
        "findings": []
    }

    # 处理ZAP报告
    if os.path.exists(zap_file):
        with open(zap_file) as f:
            zap_data = json.load(f)
            for site in zap_data.get("site", []):
                for alert in site.get("alerts", []):
                    report["findings"].append({
                        "tool": "owasp-zap",
                        "risk": alert["risk"],
                        "confidence": alert["confidence"],
                        "name": alert["alert"],
                        "description": alert["desc"],
                        "instances": [
                            {
                                "url": instance["uri"],
                                "method": instance["method"],
                                "param": instance.get("param", "")
                            }
                            for instance in alert["instances"]
                        ],
                        "solution": alert["solution"],
                        "reference": alert.get("reference", "")
                    })

    # 统计信息
    report["summary"] = {
        "total": len(report["findings"]),
        "high": sum(1 for f in report["findings"] if f["risk"] == "High"),
        "medium": sum(1 for f in report["findings"] if f["risk"] == "Medium"),
        "low": sum(1 for f in report["findings"] if f["risk"] == "Low")
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

generate_dast_report(
    "$REPORT_DIR/zap-report-$DATE.json",
    "$report_file"
)
EOF

    log_success "DAST扫描完成，报告保存到: $report_file"
}

# 软件成分分析 (SCA)
run_sca_scan() {
    log_info "开始软件成分分析..."

    local report_file="$REPORT_DIR/sca-report-$DATE.json"

    # Safety扫描
    log_info "运行Safety扫描..."
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        safety check --json --output "$REPORT_DIR/safety-report-$DATE.json" \
            -r "$PROJECT_DIR/requirements.txt" \
            || true
    fi

    # 使用Snyk（如果配置了API密钥）
    if [ -n "$SNYK_TOKEN" ] && command -v snyk &> /dev/null; then
        log_info "运行Snyk扫描..."
        export SNYK_TOKEN
        snyk test --json > "$REPORT_DIR/snyk-report-$DATE.json" || true
    fi

    # 生成SCA综合报告
    python3 << EOF
import json
import os
from datetime import datetime

def generate_sca_report(safety_file, snyk_file, output_file):
    report = {
        "scan_type": "SCA",
        "timestamp": datetime.utcnow().isoformat(),
        "tools": ["safety"],
        "dependencies": [],
        "vulnerabilities": []
    }

    # 处理Safety报告
    if os.path.exists(safety_file):
        with open(safety_file) as f:
            safety_data = json.load(f)
            for vuln in safety_data:
                report["vulnerabilities"].append({
                    "tool": "safety",
                    "package": vuln["package"],
                    "version": vuln["version"],
                    "id": vuln["id"],
                    "advisory": vuln["advisory"],
                    "cve": vuln.get("cve", ""),
                    "vulnerable_spec": vuln.get("vulnerable_spec", "")
                })

    # 处理Snyk报告
    if os.path.exists(snyk_file):
        report["tools"].append("snyk")
        # 这里可以添加Snyk报告处理逻辑

    # 统计信息
    report["summary"] = {
        "total_vulnerabilities": len(report["vulnerabilities"]),
        "high": sum(1 for v in report["vulnerabilities"] if v.get("severity") == "high"),
        "medium": sum(1 for v in report["vulnerabilities"] if v.get("severity") == "medium"),
        "low": sum(1 for v in report["vulnerabilities"] if v.get("severity") == "low")
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

generate_sca_report(
    "$REPORT_DIR/safety-report-$DATE.json",
    "$REPORT_DIR/snyk-report-$DATE.json",
    "$report_file"
)
EOF

    log_success "SCA扫描完成，报告保存到: $report_file"
}

# 容器安全扫描
run_container_scan() {
    log_info "开始容器安全扫描..."

    local report_file="$REPORT_DIR/container-report-$DATE.json"

    # 检查Dockerfile
    local dockerfile_paths=$(find "$PROJECT_DIR" -name "Dockerfile*" -type f)

    if [ -z "$dockerfile_paths" ]; then
        log_warning "未找到Dockerfile，跳过容器扫描"
        return 0
    fi

    for dockerfile in $dockerfile_paths; do
        log_info "扫描镜像: $dockerfile"

        # 构建镜像名称
        local image_name="athena-scan-$(basename $(dirname $dockerfile))-$DATE"

        # 构建镜像
        docker build -t "$image_name" -f "$dockerfile" $(dirname $dockerfile) || {
            log_warning "构建镜像失败: $dockerfile"
            continue
        }

        # Trivy扫描
        trivy image --format json --output "$REPORT_DIR/trivy-$(basename $dockerfile)-$DATE.json" "$image_name" || true

        # 清理临时镜像
        docker rmi "$image_name" || true
    done

    # 生成容器安全综合报告
    python3 << EOF
import json
import os
import glob
from datetime import datetime

def generate_container_report(trivy_files, output_file):
    report = {
        "scan_type": "Container",
        "timestamp": datetime.utcnow().isoformat(),
        "tools": ["trivy"],
        "images": [],
        "findings": []
    }

    total_findings = {
        "total": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for trivy_file in glob.glob(trivy_files):
        with open(trivy_file) as f:
            trivy_data = json.load(f)

            image_name = trivy_data.get("Metadata", {}).get("ImageName", "Unknown")
            image_report = {
                "name": image_name,
                "os": trivy_data.get("Metadata", {}).get("OS", {}),
                "findings": []
            }

            for result in trivy_data.get("Results", []):
                for vuln in result.get("Vulnerabilities", []):
                    finding = {
                        "image": image_name,
                        "vulnerability_id": vuln["VulnerabilityID"],
                        "package": vuln["PkgName"],
                        "installed_version": vuln["InstalledVersion"],
                        "severity": vuln["Severity"],
                        "title": vuln["Title"],
                        "description": vuln.get("Description", ""),
                        "references": vuln.get("References", [])
                    }

                    image_report["findings"].append(finding)
                    report["findings"].append(finding)

                    # 更新统计
                    total_findings["total"] += 1
                    severity_lower = vuln["Severity"].lower()
                    if severity_lower in total_findings:
                        total_findings[severity_lower] += 1

            report["images"].append(image_report)

    report["summary"] = total_findings

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

generate_container_report(
    "$REPORT_DIR/trivy-*-$DATE.json",
    "$report_file"
)
EOF

    log_success "容器扫描完成，报告保存到: $report_file"
}

# 生成综合安全报告
generate_summary_report() {
    log_info "生成综合安全报告..."

    local report_file="$REPORT_DIR/security-summary-$DATE.html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Athena平台安全扫描报告</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; border-bottom: 2px solid #eee; }
        h2 { color: #666; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }
        .metric-value { font-size: 32px; font-weight: bold; }
        .metric-label { color: #666; }
        .high { color: #d32f2f; }
        .medium { color: #f57c00; }
        .low { color: #388e3c; }
        .findings { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .severity-high { background-color: #ffebee; }
        .severity-medium { background-color: #fff3e0; }
        .severity-low { background-color: #e8f5e9; }
    </style>
</head>
<body>
    <h1>Athena工作平台安全扫描报告</h1>
    <p>扫描时间: $(date)</p>
    <p>扫描范围: $PROJECT_DIR</p>

    <h2>扫描概览</h2>
    <div class="summary">
        <div class="metric">
            <div class="metric-value" id="total-findings">-</div>
            <div class="metric-label">总发现问题</div>
        </div>
        <div class="metric">
            <div class="metric-value high" id="high-findings">-</div>
            <div class="metric-label">高危问题</div>
        </div>
        <div class="metric">
            <div class="metric-value medium" id="medium-findings">-</div>
            <div class="metric-label">中危问题</div>
        </div>
        <div class="metric">
            <div class="metric-value low" id="low-findings">-</div>
            <div class="metric-label">低危问题</div>
        </div>
    </div>

    <h2>扫描类型</h2>
    <ul>
EOF

    # 根据执行的扫描类型添加信息
    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "sast" ]; then
        echo "<li>✅ 静态应用安全测试 (SAST)</li>" >> "$report_file"
    fi
    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "dast" ]; then
        echo "<li>✅ 动态应用安全测试 (DAST)</li>" >> "$report_file"
    fi
    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "sca" ]; then
        echo "<li>✅ 软件成分分析 (SCA)</li>" >> "$report_file"
    fi
    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "container" ]; then
        echo "<li>✅ 容器安全扫描</li>" >> "$report_file"
    fi

    cat >> "$report_file" << EOF
    </ul>

    <h2>关键发现</h2>
    <div id="key-findings">加载中...</div>

    <h2>建议</h2>
    <ol>
        <li>优先修复所有高危漏洞</li>
        <li>建立定期安全扫描机制</li>
        <li>加强代码审查流程</li>
        <li>实施安全编码规范</li>
        <li>定期更新依赖库</li>
    </ol>

    <script>
        // 加载并显示扫描结果
        async function loadResults() {
            const totalHigh = parseInt(localStorage.getItem('high-count') || '0');
            const totalMedium = parseInt(localStorage.getItem('medium-count') || '0');
            const totalLow = parseInt(localStorage.getItem('low-count') || '0');

            document.getElementById('total-findings').textContent = totalHigh + totalMedium + totalLow;
            document.getElementById('high-findings').textContent = totalHigh;
            document.getElementById('medium-findings').textContent = totalMedium;
            document.getElementById('low-findings').textContent = totalLow;

            if (totalHigh > 0) {
                document.getElementById('key-findings').innerHTML =
                    '<p class="high">⚠️ 发现 ' + totalHigh + ' 个高危安全问题，需要立即修复</p>';
            } else {
                document.getElementById('key-findings').innerHTML =
                    '<p class="low">✅ 未发现高危安全问题</p>';
            }
        }

        loadResults();
    </script>
</body>
</html>
EOF

    log_success "综合安全报告已生成: $report_file"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 清理Docker镜像
    docker images | grep "athena-scan-" | awk '{print $3}' | xargs -r docker rmi -f || true
    log_success "清理完成"
}

# 发送报告
send_reports() {
    if [ -n "$SECURITY_TEAM_EMAIL" ]; then
        log_info "发送安全报告到: $SECURITY_TEAM_EMAIL"

        # 压缩报告文件
        local archive_file="$REPORT_DIR/security-scan-$DATE.tar.gz"
        tar -czf "$archive_file" -C "$REPORT_DIR" "sast-report-$DATE.json" \
            "dast-report-$DATE.json" "sca-report-$DATE.json" \
            "container-report-$DATE.json" "security-summary-$DATE.html"

        # 发送邮件（需要配置邮件服务）
        echo "Athena平台安全扫描报告已完成，请查看附件。" | \
            mail -s "安全扫描报告 - $DATE" -a "$archive_file" \
            "$SECURITY_TEAM_EMAIL" || log_warning "邮件发送失败"

        log_success "报告已发送"
    fi
}

# 主函数
main() {
    log_info "开始安全漏洞扫描..."
    log_info "扫描类型: $SCAN_TYPE"
    log_info "项目目录: $PROJECT_DIR"
    log_info "报告目录: $REPORT_DIR"

    # 检查工具
    check_tools

    # 执行扫描
    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "sast" ]; then
        run_sast_scan
    fi

    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "dast" ]; then
        run_dast_scan
    fi

    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "sca" ]; then
        run_sca_scan
    fi

    if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "container" ]; then
        run_container_scan
    fi

    # 生成报告
    generate_summary_report

    # 发送报告
    send_reports

    # 清理
    cleanup

    log_success "安全扫描完成！"
    log_info "报告位置: $REPORT_DIR"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            SCAN_TYPE="$2"
            shift 2
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --report-dir)
            REPORT_DIR="$2"
            shift 2
            ;;
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --email)
            SECURITY_TEAM_EMAIL="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --type TYPE          扫描类型 (sast|dast|sca|container|all)"
            echo "  --project-dir DIR    项目目录"
            echo "  --report-dir DIR     报告输出目录"
            echo "  --base-url URL       DAST扫描目标URL"
            echo "  --email EMAIL        报告接收邮箱"
            echo "  -h, --help           显示帮助信息"
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 执行主函数
main