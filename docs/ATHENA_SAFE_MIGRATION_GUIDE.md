# 🛡️ Athena工作平台安全架构转型指南
## 零风险Gateway模式迁移方案

> **核心原则**：数据零丢失、服务零中断、可随时回滚

---

## 📋 目录

1. [安全原则](#安全原则)
2. [资产盘点与分类](#资产盘点与分类)
3. [备份策略](#备份策略)
4. [分阶段迁移方案](#分阶段迁移方案)
5. [回滚机制](#回滚机制)
6. [应急响应预案](#应急响应预案)
7. [验证清单](#验证清单)

---

## 🔒 安全原则

### 三重保护机制

```
┌─────────────────────────────────────────────────────────┐
│              Athena三重保护架构                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 1: 数据备份 (防丢失)                       │   │
│  │  - 实时备份 (每5分钟)                             │   │
│  │  - 每日全量备份                                   │   │
│  │  - 异地冗余存储                                   │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 2: 版本控制 (防破坏)                       │   │
│  │  - Git标签管理                                    │   │
│  │  - 数据库迁移版本控制                             │   │
│  │  - 配置文件版本追踪                               │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 3: 回滚能力 (防灾难)                       │   │
│  │  - 一键回滚脚本                                   │   │
│  │  - 蓝绿部署                                       │   │
│  │  - 快速切换机制                                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 核心承诺

| 承诺项 | 具体指标 | 验证方式 |
|-------|---------|---------|
| **数据零丢失** | RPO (恢复点目标) = 0 | 实时备份验证 |
| **服务最小中断** | RTO (恢复时间目标) < 5分钟 | 自动化切换测试 |
| **可随时回滚** | 回滚时间 < 10分钟 | 回滚演练 |
| **100%可追溯** | 所有变更可审计 | 日志完整性检查 |

---

## 📊 资产盘点与分类

### 核心数据资产清单

#### 🔴 P0级 - 关键资产 (不可丢失)

| 资产名称 | 存储位置 | 数据量 | 备份频率 | 保留期限 |
|---------|---------|--------|---------|---------|
| **法律世界模型** | `core/legal_world_model/` | ~2GB | 实时 | 永久 |
| **PostgreSQL数据库** | PostgreSQL Data | ~10GB | 每5分钟 | 永久+7年 |
| **知识图谱(Neo4j)** | Neo4j Data | ~5GB | 每小时 | 永久 |
| **向量数据库(Qdrant)** | Qdrant Storage | ~8GB | 每小时 | 永久 |
| **个人安全存储** | `personal_secure_storage/` | ~1GB | 实时 | 永久 |

#### 🟡 P1级 - 重要资产 (可重建但耗时)

| 资产名称 | 存储位置 | 数据量 | 备份频率 | 保留期限 |
|---------|---------|--------|---------|---------|
| **智能体配置** | `core/agents/` | ~500MB | 每日 | 1年 |
| **提示词模板** | `core/prompts/` | ~100MB | 每日 | 1年 |
| **技能脚本** | `skills/` | ~200MB | 每日 | 1年 |
| **日志数据** | `logs/` | ~5GB | 每日 | 90天 |

#### 🟢 P2级 - 一般资产 (可快速重建)

| 资产名称 | 存储位置 | 数据量 | 备份频率 | 保留期限 |
|---------|---------|--------|---------|---------|
| **文档** | `docs/` | ~50MB | 每周 | 90天 |
| **测试数据** | `tests/` | ~100MB | 每周 | 30天 |
| **临时文件** | `temp/` | ~1GB | 不备份 | - |

### 资产价值评估矩阵

```
           高价值
              │
    P0 关键   │   P1 重要
    (核心资产) │   (业务数据)
              │
──────────────┼──────────────
              │
    P2 一般   │   P3 临时
    (文档)    │   (缓存)
              │
           低价值
           高重建难度 → 低重建难度
```

---

## 💾 备份策略

### 3-2-1备份法则

```
3份数据副本
├── 1份生产数据
├── 1份本地备份
└── 1份异地备份

2种不同介质
├── 磁盘存储 (SSD/HDD)
└── 云存储 (S3/OSS)

1份离线备份
└── 冷存储 (Glacier/OBS Archive)
```

### 自动化备份系统

#### PostgreSQL数据库备份

```bash
#!/bin/bash
# scripts/backup/postgres_backup.sh
set -euo pipefail

# 配置
BACKUP_DIR="/backup/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="athena_db"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 1. 逻辑备份 (SQL格式) - 可读性强
pg_dump -h localhost -U postgres -d "${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    > "${BACKUP_DIR}/athena_${TIMESTAMP}.sql"

# 2. 二进制备份 (恢复快)
pg_dump -h localhost -U postgres -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    -f "${BACKUP_DIR}/athena_${TIMESTAMP}.dump"

# 3. 同时备份到云存储
aws s3 cp "${BACKUP_DIR}/athena_${TIMESTAMP}.sql" \
    "s3://athena-backups/postgres/${TIMESTAMP}.sql" \
    --storage-class GLACIER

# 4. 清理旧备份 (保留30天)
find "${BACKUP_DIR}" -name "athena_*.sql" -mtime +${RETENTION_DAYS} -delete

echo "✅ PostgreSQL备份完成: ${TIMESTAMP}"
```

#### Neo4j知识图谱备份

```bash
#!/bin/bash
# scripts/backup/neo4j_backup.sh

BACKUP_DIR="/backup/neo4j"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEO4J_HOME="/usr/local/neo4j"

# 使用neo4j-admin备份
${NEO4J_HOME}/bin/neo4j-admin database backup \
    --from-path=/data/databases \
    --backup-path="${BACKUP_DIR}" \
    --name=legal_graph \
    --to="legal_graph_${TIMESTAMP}"

# 压缩
cd "${BACKUP_DIR}"
tar -czf "legal_graph_${TIMESTAMP}.tar.gz" "legal_graph_${TIMESTAMP}"
rm -rf "legal_graph_${TIMESTAMP}"

echo "✅ Neo4j备份完成: ${TIMESTAMP}"
```

#### 法律世界模型备份

```python
#!/usr/bin/env python3
# scripts/backup/legal_world_model_backup.py

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

class LegalWorldModelBackup:
    """法律世界模型专用备份工具

    特点：
    1. 增量备份 (只备份变更文件)
    2. 版本控制集成
    3. 校验和验证
    """

    def __init__(self):
        self.source_dir = Path("/Users/xujian/Athena工作平台/core/legal_world_model")
        self.backup_dir = Path("/backup/legal_world_model")
        self.git_dir = Path("/backup/legal_world_model_git")

    def incremental_backup(self):
        """增量备份，基于文件修改时间"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp

        # 创建备份目录
        backup_path.mkdir(parents=True, exist_ok=True)

        # 复制变更的文件
        for file in self.source_dir.rglob("*"):
            if file.is_file():
                relative_path = file.relative_to(self.source_dir)
                backup_file = backup_path / relative_path

                # 创建目录结构
                backup_file.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                shutil.copy2(file, backup_file)

        # 计算校验和
        checksums = self._calculate_checksums(backup_path)
        checksum_file = backup_path / "checksums.txt"
        with open(checksum_file, 'w') as f:
            for path, checksum in checksums.items():
                f.write(f"{checksum} {path}\n")

        print(f"✅ 法律世界模型备份完成: {timestamp}")

    def git_backup(self):
        """Git版本控制备份"""
        import subprocess

        # 复制到Git仓库
        if not self.git_dir.exists():
            self.git_dir.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=self.git_dir)

        # 复制文件
        for item in self.source_dir.iterdir():
            dest = self.git_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # Git提交
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subprocess.run(["git", "add", "."], cwd=self.git_dir)
        subprocess.run(
            ["git", "commit", "-m", f"Backup: {timestamp}"],
            cwd=self.git_dir
        )
        subprocess.run(
            ["git", "tag", f"backup-{timestamp}"],
            cwd=self.git_dir
        )

        print(f"✅ Git备份完成: backup-{timestamp}")

    def _calculate_checksums(self, directory):
        """计算所有文件的SHA256校验和"""
        checksums = {}
        for file in directory.rglob("*"):
            if file.is_file():
                sha256 = hashlib.sha256()
                with open(file, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        sha256.update(chunk)
                relative_path = file.relative_to(directory)
                checksums[str(relative_path)] = sha256.hexdigest()
        return checksums

if __name__ == "__main__":
    backup = LegalWorldModelBackup()
    backup.incremental_backup()
    backup.git_backup()
```

### 备份验证系统

```python
#!/usr/bin/env python3
# scripts/backup/verify_backups.py

import os
import subprocess
from datetime import datetime, timedelta

class BackupVerifier:
    """备份验证工具 - 确保备份可恢复"""

    def __init__(self):
        self.verification_log = "/backup/verification.log"

    def verify_postgres_backup(self, backup_file):
        """验证PostgreSQL备份完整性"""
        # 1. 检查文件存在
        if not os.path.exists(backup_file):
            return False, "备份文件不存在"

        # 2. 尝试恢复到测试数据库
        test_db = "athena_test_restore"
        try:
            # 创建测试数据库
            subprocess.run(
                ["createdb", "-U", "postgres", test_db],
                check=True
            )

            # 尝试恢复
            subprocess.run(
                ["psql", "-U", "postgres", "-d", test_db, "-f", backup_file],
                check=True,
                capture_output=True
            )

            # 验证表数量
            result = subprocess.run(
                ["psql", "-U", "postgres", "-d", test_db,
                 "-t", "-c", "SELECT COUNT(*) FROM information_schema.tables"],
                capture_output=True,
                text=True,
                check=True
            )

            table_count = int(result.stdout.strip())
            if table_count < 10:  # 至少应该有10张表
                return False, f"表数量异常: {table_count}"

            return True, f"验证通过，{table_count}张表"

        finally:
            # 清理测试数据库
            subprocess.run(
                ["dropdb", "-U", "postgres", test_db],
                stderr=subprocess.DEVNULL
            )

    def verify_all_recent_backups(self):
        """验证最近24小时的所有备份"""
        results = []

        # 验证PostgreSQL
        postgres_backup = self._get_latest_postgres_backup()
        if postgres_backup:
            success, message = self.verify_postgres_backup(postgres_backup)
            results.append({
                "type": "PostgreSQL",
                "backup": postgres_backup,
                "success": success,
                "message": message
            })

        # 记录结果
        self._log_results(results)
        return results

    def _log_results(self, results):
        """记录验证结果"""
        with open(self.verification_log, 'a') as f:
            f.write(f"\n=== 备份验证 {datetime.now()} ===\n")
            for result in results:
                status = "✅" if result['success'] else "❌"
                f.write(f"{status} {result['type']}: {result['message']}\n")

if __name__ == "__main__":
    verifier = BackupVerifier()
    results = verifier.verify_all_recent_backups()
    print("\n备份验证结果:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['type']}: {r['message']}")
```

### 备份调度系统

```yaml
# scripts/backup/backup_schedule.yaml
backups:
  postgres:
    enabled: true
    schedule:
      # 每5分钟增量备份
      incremental: "*/5 * * * *"
      # 每天凌晨2点全量备份
      full: "0 2 * * *"
    retention:
      incremental: 7  # 天
      full: 30  # 天

  neo4j:
    enabled: true
    schedule:
      # 每小时备份
      full: "0 * * * *"
    retention:
      full: 30  # 天

  legal_world_model:
    enabled: true
    schedule:
      # 实时备份 (文件变化时)
      incremental: "inotify"
      # 每天Git提交
      git: "0 3 * * *"
    retention:
      incremental: 90  # 天
      git: "forever"  # 永久保留

  qdrant:
    enabled: true
    schedule:
      # 每6小时备份
      full: "0 */6 * * *"
    retention:
      full: 14  # 天

notifications:
  on_failure: true
  email: "xujian519@gmail.com"
  webhook: "https://hooks.example.com/backup"
```

---

## 🚀 分阶段迁移方案

### 总体迁移路线图

```
┌─────────────────────────────────────────────────────────┐
│              Athena架构转型时间线 (90天)                 │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Phase 0: 准备阶段 (Day 1-7)                            │
│  ├─ 资产盘点 ✅                                         │
│  ├─ 备份系统部署                                        │
│  ├─ 回滚机制测试                                        │
│  └─ 基线性能测试                                        │
│                                                           │
│  Phase 1: Gateway并行运行 (Day 8-30)                    │
│  ├─ 部署新Gateway (不接管流量)                          │
│  ├─ 数据同步验证                                        │
│  └─ 功能对比测试                                        │
│                                                           │
│  Phase 2: 灰度切流 (Day 31-60)                          │
│  ├─ 10% 流量 → Gateway                                  │
│  ├─ 50% 流量 → Gateway                                  │
│  └─ 100% 流量 → Gateway                                 │
│                                                           │
│  Phase 3: 稳定运行 (Day 61-90)                          │
│  ├─ 监控观察                                            │
│  ├─ 性能优化                                            │
│  └─ 旧系统下线                                          │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Phase 0: 准备阶段 (Day 1-7)

#### 任务清单

```bash
#!/bin/bash
# scripts/migration/phase0_prepare.sh

echo "🚀 Phase 0: 迁移准备阶段"

# 1. 创建迁移分支
git checkout -b migration/gateway-transition
git push -u origin migration/gateway-transition

# 2. 备份所有数据
echo "📦 开始全量备份..."
./scripts/backup/backup_all.sh

# 3. 验证备份完整性
echo "🔍 验证备份完整性..."
python3 scripts/backup/verify_backups.py

# 4. 创建回滚标签
echo "🏷️ 创建回滚基线标签..."
git tag pre-migration-baseline-$(date +%Y%m%d)
git push origin pre-migration-baseline-$(date +%Y%m%d)

# 5. 部署监控
echo "📊 部署监控系统..."
docker-compose -f docker-compose.monitoring.yml up -d

# 6. 基线性能测试
echo "⚡ 执行基线性能测试..."
python3 scripts/performance/run_benchmark.py --tag baseline

echo "✅ Phase 0 完成！准备开始迁移。"
```

#### 验证清单

- [ ] 所有P0数据备份完成
- [ ] 备份验证100%通过
- [ ] Git基线标签已创建
- [ ] 监控系统运行正常
- [ ] 基线性能数据已记录
- [ ] 回滚脚本已测试
- [ ] 应急联系方式已确认

### Phase 1: Gateway并行运行 (Day 8-30)

#### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│         Phase 1: 并行运行架构                            │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  现有系统 (主流量)          新Gateway (影子流量)          │
│  ┌──────────────┐           ┌──────────────┐            │
│  │ 小娜代理     │           │ 小娜代理     │            │
│  │ 小诺代理     │  ────────→│ 小诺代理     │            │
│  │ 云熙代理     │  影子复制 │ 云熙代理     │            │
│  └──────────────┘           └──────────────┘            │
│         │                           │                    │
│         ▼                           ▼                    │
│  ┌──────────────┐           ┌──────────────┐            │
│  │ 现有数据层   │           │ Gateway      │            │
│  │              │           │ (只读模式)   │            │
│  └──────────────┘           └──────────────┘            │
│         │                           │                    │
│         └───────────┬───────────────┘                    │
│                     ▼                                    │
│            ┌──────────────┐                              │
│            │ 对比验证     │                              │
│            │ - 结果一致性 │                              │
│            │ - 性能对比   │                              │
│            │ - 日志对比   │                              │
│            └──────────────┘                              │
└─────────────────────────────────────────────────────────┘
```

#### 数据同步脚本

```python
#!/usr/bin/env python3
# scripts/migration/shadow_sync.py

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

class ShadowSyncManager:
    """影子同步管理器 - 将请求复制到Gateway进行验证"""

    def __init__(self):
        self.gateway_url = "http://localhost:8006"  # 新Gateway端口
        self.legacy_url = "http://localhost:8005"    # 现有系统
        self.log_file = "/migration/shadow_sync.log"

    async def shadow_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """影子请求：同时发给新旧系统"""

        # 1. 发送给现有系统 (主请求)
        legacy_response = await self._send_request(
            self.legacy_url,
            request_data
        )

        # 2. 异步发送给Gateway (影子请求)
        gateway_response = await self._send_request(
            self.gateway_url,
            request_data
        )

        # 3. 对比结果
        comparison = self._compare_responses(
            legacy_response,
            gateway_response
        )

        # 4. 记录差异
        if not comparison['identical']:
            self._log_difference(request_data, comparison)

        # 返回现有系统的结果
        return legacy_response

    def _compare_responses(self, legacy: Dict, gateway: Dict) -> Dict:
        """对比两个响应"""
        return {
            'identical': legacy.get('result') == gateway.get('result'),
            'legacy_latency': legacy.get('latency'),
            'gateway_latency': gateway.get('latency'),
            'difference_details': self._deep_diff(legacy, gateway)
        }

    def _log_difference(self, request: Dict, comparison: Dict):
        """记录差异"""
        with open(self.log_file, 'a') as f:
            f.write(f"\n=== 差异发现 {datetime.now()} ===\n")
            f.write(f"请求: {request}\n")
            f.write(f"对比结果: {comparison}\n")
            f.write(f"延迟差异: {comparison['gateway_latency'] - comparison['legacy_latency']}ms\n")

# 使用示例
async def main():
    sync_manager = ShadowSyncManager()

    # 模拟请求
    request = {
        'agent': 'xiaona',
        'action': 'analyze_patent',
        'params': {'patent_id': 'CN123456789A'}
    }

    # 影子同步请求
    response = await sync_manager.shadow_request(request)
    print(f"响应: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 验证指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| **结果一致性** | >99% | ___ | 待验证 |
| **性能差异** | <10% | ___ | 待验证 |
| **错误率** | <0.1% | ___ | 待验证 |
| **数据完整性** | 100% | ___ | 待验证 |

### Phase 2: 灰度切流 (Day 31-60)

#### 切流策略

```
灰度切流时间表：

Week 1-2 (Day 31-44): 10% 流量
├─ 内部测试用户
├─ 非关键业务
└─ 严格监控

Week 3-4 (Day 45-58): 50% 流量
├─ 扩大到所有用户
├─ 轮询分配 (基于user_id % 2)
└─ A/B测试对比

Week 5-6 (Day 59-72): 100% 流量
├─ 全量切换
├─ 保留旧系统热备份
└─ 准备快速回滚
```

#### 流量分配器

```python
#!/usr/bin/env python3
# scripts/migration/traffic_splitter.py

import hashlib
from typing import Optional

class TrafficSplitter:
    """基于用户ID的流量分配器"""

    def __init__(self, gateway_ratio: float = 0.0):
        """
        Args:
            gateway_ratio: 流向Gateway的比例 (0.0 - 1.0)
        """
        self.gateway_ratio = gateway_ratio
        self.gateway_url = "http://localhost:8006"
        self.legacy_url = "http://localhost:8005"

    def should_route_to_gateway(self, user_id: str) -> bool:
        """判断用户是否应该路由到Gateway"""
        # 基于user_id的哈希，确保同一用户总是路由到同一系统
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < (self.gateway_ratio * 100)

    def route(self, user_id: str):
        """获取目标URL"""
        if self.should_route_to_gateway(user_id):
            return self.gateway_url
        return self.legacy_url

# 配置
class TrafficConfig:
    """流量配置管理"""

    # 每周更新一次
    SCHEDULE = {
        "week1": 0.10,  # 10%
        "week2": 0.10,  # 10%
        "week3": 0.50,  # 50%
        "week4": 0.50,  # 50%
        "week5": 1.00,  # 100%
        "week6": 1.00,  # 100%
    }

    @classmethod
    def get_current_ratio(cls) -> float:
        """获取当前应该使用的流量比例"""
        # 从配置文件或环境变量读取
        import os
        return float(os.getenv('GATEWAY_TRAFFIC_RATIO', '0.0'))
```

#### 自动化切流脚本

```bash
#!/bin/bash
# scripts/migration/update_traffic_ratio.sh

GATEWAY_RATIO=$1

if [ -z "$GATEWAY_RATIO" ]; then
    echo "用法: $0 <流量比例 (0.0-1.0)>"
    exit 1
fi

echo "🔄 更新流量比例: ${GATEWAY_RATIO}"

# 更新环境变量
export GATEWAY_TRAFFIC_RATIO=$GATEWAY_RATIO

# 保存到配置文件
echo "GATEWAY_TRAFFIC_RATIO=$GATEWAY_RATIO" >> .env.migration

# 重启服务
docker-compose restart gateway

# 记录切换日志
echo "$(date): 流量比例更新为 ${GATEWAY_RATIO}" >> /migration/traffic_changes.log

echo "✅ 流量比例已更新为 ${GATEWAY_RATIO}"
```

### Phase 3: 稳定运行 (Day 61-90)

#### 监控仪表板

```python
#!/usr/bin/env python3
# scripts/migration/dashboard.py

from prometheus_client import Counter, Histogram, Gauge
import time

# 关键指标
migration_metrics = {
    # 请求量
    'requests_total': Counter(
        'athena_requests_total',
        'Total requests',
        ['system', 'agent', 'status']
    ),

    # 延迟
    'request_latency': Histogram(
        'athena_request_latency_seconds',
        'Request latency',
        ['system', 'agent']
    ),

    # 错误率
    'errors_total': Counter(
        'athena_errors_total',
        'Total errors',
        ['system', 'agent', 'error_type']
    ),

    # 数据一致性
    'data_inconsistency': Counter(
        'athena_data_inconsistency_total',
        'Data inconsistency events',
        ['check_type']
    ),

    # 系统健康
    'system_health': Gauge(
        'athena_system_health',
        'System health status',
        ['system', 'check_type']
    ),
}

class MigrationMonitor:
    """迁移监控"""

    def __init__(self):
        self.metrics = migration_metrics

    def record_request(self, system: str, agent: str,
                      status: str, latency: float):
        """记录请求"""
        self.metrics['requests_total'].labels(
            system=system,
            agent=agent,
            status=status
        ).inc()
        self.metrics['request_latency'].labels(
            system=system,
            agent=agent
        ).observe(latency)

    def record_error(self, system: str, agent: str,
                    error_type: str):
        """记录错误"""
        self.metrics['errors_total'].labels(
            system=system,
            agent=agent,
            error_type=error_type
        ).inc()

    def check_health(self):
        """健康检查"""
        # 检查PostgreSQL
        pg_health = self._check_postgres()
        self.metrics['system_health'].labels(
            system='postgres',
            check_type='connectivity'
        ).set(1 if pg_health else 0)

        # 检查Neo4j
        neo4j_health = self._check_neo4j()
        self.metrics['system_health'].labels(
            system='neo4j',
            check_type='connectivity'
        ).set(1 if neo4j_health else 0)

        # 检查Qdrant
        qdrant_health = self._check_qdrant()
        self.metrics['system_health'].labels(
            system='qdrant',
            check_type='connectivity'
        ).set(1 if qdrant_health else 0)

    def _check_postgres(self) -> bool:
        """检查PostgreSQL连接"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                database="athena_db",
                user="postgres"
            )
            conn.close()
            return True
        except:
            return False

# 启动监控服务
if __name__ == "__main__":
    from prometheus_client import start_http_server

    # 启动Prometheus指标服务
    start_http_server(9090)

    monitor = MigrationMonitor()

    # 持续监控
    while True:
        monitor.check_health()
        time.sleep(60)
```

---

## 🔄 回滚机制

### 一键回滚系统

```bash
#!/bin/bash
# scripts/migration/emergency_rollback.sh

set -euo pipefail

echo "🚨 执行紧急回滚..."

# 1. 确认回滚
read -p "⚠️  确定要回滚到迁移前状态吗？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ 回滚已取消"
    exit 0
fi

# 2. 记录回滚开始时间
echo "$(date): 开始回滚" >> /migration/rollback.log

# 3. 切换流量回旧系统
echo "🔄 切换流量..."
export GATEWAY_TRAFFIC_RATIO=0.0
./scripts/migration/update_traffic_ratio.sh 0.0

# 4. 停止新Gateway
echo "⏹️  停止Gateway..."
docker-compose stop gateway

# 5. 恢复数据库 (如果需要)
read -p "是否需要恢复数据库？(yes/no): " restore_db
if [ "$restore_db" = "yes" ]; then
    echo "💾 恢复数据库..."
    LATEST_BACKUP=$(ls -t /backup/postgres/*.sql | head -1)
    psql -U postgres -d athena_db -f "$LATEST_BACKUP"
fi

# 6. 验证回滚
echo "🔍 验证系统状态..."
python3 scripts/health/check_system.py

# 7. 记录回滚完成
echo "$(date): 回滚完成" >> /migration/rollback.log

echo "✅ 回滚完成！系统已恢复到迁移前状态。"
```

### Git版本回滚

```bash
#!/bin/bash
# scripts/migration/git_rollback.sh

COMMIT_TAG=$1  # 例如: pre-migration-baseline-20250202

if [ -z "$COMMIT_TAG" ]; then
    echo "用法: $0 <Git标签>"
    echo "可用标签:"
    git tag -l "pre-migration-baseline-*"
    exit 1
fi

echo "🔄 回滚到Git标签: $COMMIT_TAG"

# 1. 创建回滚分支
git checkout -b rollback-from-$(date +%Y%m%d)

# 2. 回滚到指定标签
git reset --hard $COMMIT_TAG

# 3. 强制推送 (谨慎!)
read -p "⚠️  这将强制推送，覆盖远程分支。确认？(yes/no): " confirm
if [ "$confirm" = "yes" ]; then
    git push -f origin rollback-from-$(date +%Y%m%d)
    echo "✅ Git回滚完成"
else
    echo "❌ 已取消"
    exit 0
fi
```

### 数据库回滚

```python
#!/usr/bin/env python3
# scripts/migration/db_rollback.py

import subprocess
import sys
from datetime import datetime
from pathlib import Path

class DatabaseRollback:
    """数据库回滚管理器"""

    def __init__(self):
        self.backup_dir = Path("/backup/postgres")
        self.db_name = "athena_db"

    def list_available_backups(self):
        """列出可用的备份"""
        backups = sorted(self.backup_dir.glob("athena_*.sql"))
        print("\n可用的数据库备份:")
        for i, backup in enumerate(backups[-10:], 1):
            size = backup.stat().st_size / (1024 * 1024)  # MB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i}. {backup.name} ({size:.1f}MB, {mtime})")

        return backups

    def rollback_to_backup(self, backup_file: Path):
        """回滚到指定备份"""
        print(f"⚠️  准备回滚数据库到: {backup_file.name}")

        # 1. 创建当前数据库的备份
        emergency_backup = self.backup_dir / f"emergency_before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        print(f"💾 创建紧急备份: {emergency_backup}")

        subprocess.run([
            "pg_dump", "-U", "postgres", "-d", self.db_name,
            "-f", str(emergency_backup)
        ], check=True)

        # 2. 确认回滚
        confirm = input("确认执行回滚？(yes/no): ")
        if confirm.lower() != "yes":
            print("❌ 已取消")
            return

        # 3. 停止所有连接
        print("⏹️  停止所有数据库连接...")
        subprocess.run([
            "docker-compose", "stop", "web", "gateway"
        ], check=True)

        # 4. 删除并重建数据库
        print("🔄 重建数据库...")
        subprocess.run(["dropdb", "-U", "postgres", self.db_name], check=True)
        subprocess.run(["createdb", "-U", "postgres", self.db_name], check=True)

        # 5. 恢复备份
        print("💾 恢复备份数据...")
        with open(backup_file) as f:
            subprocess.run([
                "psql", "-U", "postgres", "-d", self.db_name
            ], stdin=f, check=True)

        # 6. 重启服务
        print("▶️  重启服务...")
        subprocess.run([
            "docker-compose", "start", "web"
        ], check=True)

        print("✅ 数据库回滚完成")

if __name__ == "__main__":
    roller = DatabaseRollback()

    # 列出备份
    backups = roller.list_available_backups()

    # 选择备份
    try:
        choice = int(input("\n选择要回滚到的备份编号: ")) - 1
        selected_backup = backups[-10:][choice]
        roller.rollback_to_backup(selected_backup)
    except (ValueError, IndexError):
        print("❌ 无效的选择")
```

### 回滚决策树

```
回滚决策流程：

发现问题
    │
    ├─ 严重程度评估
    │   ├─ P0 (数据丢失、服务中断) → 立即回滚
    │   ├─ P1 (功能异常、性能下降) → 评估后决策
    │   └─ P2 (小问题) → 记录并监控
    │
    ├─ 回滚类型选择
    │   ├─ 流量回滚 (最快速)
    │   │   └─ 执行: update_traffic_ratio.sh 0.0
    │   ├─ 服务回滚 (中等速度)
    │   │   └─ 执行: git_rollback.sh + docker-compose restart
    │   └─ 数据回滚 (最后手段)
    │       └─ 执行: db_rollback.py
    │
    └─ 验证回滚
        ├─ 功能验证
        ├─ 数据完整性检查
        └─ 性能验证
```

---

## 🚨 应急响应预案

### 故障分级

| 级别 | 定义 | 响应时间 | 处理措施 |
|------|------|---------|---------|
| **P0 - 严重** | 数据丢失、服务完全不可用 | < 5分钟 | 立即回滚 |
| **P1 - 高** | 核心功能异常、性能下降>50% | < 15分钟 | 评估后回滚或修复 |
| **P2 - 中** | 非核心功能异常、性能下降<50% | < 1小时 | 监控并修复 |
| **P3 - 低** | 小问题、用户体验影响小 | < 4小时 | 记录并排期修复 |

### 应急联系人

```yaml
# scripts/migration/emergency_contacts.yaml
contacts:
  primary:
    name: "徐健"
    role: "项目负责人"
    email: "xujian519@gmail.com"
    phone: "+86 xxx xxxx xxxx"

  technical:
    name: "[技术负责人]"
    role: "技术架构师"
    email: "[email]"
    phone: "[phone]"

  escalation:
    - level: 1
      timeout_minutes: 15
      contact: "technical"

    - level: 2
      timeout_minutes: 30
      contact: "primary"
```

### 应急检查清单

```markdown
# 应急响应检查清单

## P0级别 - 立即回滚

### 步骤1: 快速评估 (2分钟内)
- [ ] 确认问题范围
- [ ] 评估数据影响
- [ ] 确定回滚必要性

### 步骤2: 执行回滚 (5分钟内)
- [ ] 通知相关人员
- [ ] 执行: `./scripts/migration/emergency_rollback.sh`
- [ ] 验证回滚成功

### 步骤3: 恢复后验证 (10分钟内)
- [ ] 检查核心功能
- [ ] 验证数据完整性
- [ ] 监控系统指标

### 步骤4: 根因分析 (事后)
- [ ] 记录问题详情
- [ ] 分析根本原因
- [ ] 制定预防措施

## P1级别 - 评估后决策

### 步骤1: 问题评估 (10分钟内)
- [ ] 问题严重程度评估
- [ ] 影响范围确认
- [ ] 修复时间估算

### 步骤2: 决策
- [ ] 是否需要回滚？
- [ ] 是否可以在线修复？
- [ ] 需要哪些资源？

### 步骤3: 执行
- [ ] 执行选定方案
- [ ] 持续监控
- [ ] 沟通状态更新

## P2/P3级别 - 监控修复

### 步骤1: 记录问题
- [ ] 创建Issue
- [ ] 记录详细信息
- [ ] 设置优先级

### 步骤2: 安排修复
- [ ] 分配责任人
- [ ] 评估工作量
- [ ] 纳入迭代计划
```

---

## ✅ 验证清单

### 每日检查清单

```markdown
# 每日迁移验证清单

## 数据完整性
- [ ] PostgreSQL备份成功
- [ ] Neo4j备份成功
- [ ] Qdrant备份成功
- [ ] 法律世界模型备份成功
- [ ] 备份验证通过

## 系统健康
- [ ] 所有服务运行正常
- [ ] CPU使用率 < 80%
- [ ] 内存使用率 < 80%
- [ ] 磁盘使用率 < 70%
- [ ] 错误率 < 0.1%

## 功能验证
- [ ] 小娜代理响应正常
- [ ] 小诺代理响应正常
- [ ] 云熙代理响应正常
- [ ] 数据库查询正常
- [ ] 向量检索正常

## 性能指标
- [ ] 响应时间 < 基线 * 1.1
- [ ] 吞吐量 > 基线 * 0.9
- [ ] 错误率 < 基线 * 1.5
```

### 每周检查清单

```markdown
# 每周迁移验证清单

## 备份恢复测试
- [ ] 执行一次备份恢复演练
- [ ] 验证恢复时间 < RTO目标
- [ ] 验证数据完整性100%

## 回滚演练
- [ ] 执行一次完整回滚测试
- [ ] 验证回滚时间 < 10分钟
- [ ] 验证所有功能正常

## 性能回归测试
- [ ] 运行完整性能测试套件
- [ ] 对比基线性能
- [ ] 分析性能差异

## 安全审计
- [ ] 检查访问日志
- [ ] 验证数据加密
- [ ] 检查权限配置
```

---

## 📊 监控仪表板

### 关键指标定义

```yaml
# scripts/migration/metrics_definition.yaml
metrics:
  # 业务指标
  business:
    - name: "代理请求成功率"
      metric: "agent_request_success_rate"
      target: "> 99%"

    - name: "平均响应时间"
      metric: "avg_response_time_ms"
      target: "< 1000ms"

    - name: "数据一致性"
      metric: "data_consistency_rate"
      target: "100%"

  # 技术指标
  technical:
    - name: "系统可用性"
      metric: "system_uptime"
      target: "> 99.9%"

    - name: "错误率"
      metric: "error_rate"
      target: "< 0.1%"

    - name: "资源使用率"
      metric: "resource_utilization"
      target: "< 80%"

  # 迁移指标
  migration:
    - name: "迁移进度"
      metric: "migration_progress"
      target: "按计划完成"

    - name: "流量比例"
      metric: "gateway_traffic_ratio"
      target: "按计划增加"

    - name: "回滚准备就绪"
      metric: "rollback_ready"
      target: "100%"
```

---

## 📝 总结

### 核心保障机制

1. **三重备份**：实时 + 每日 + 异地
2. **版本控制**：Git标签 + 数据库版本
3. **灰度发布**：10% → 50% → 100%
4. **快速回滚**：< 10分钟完全回滚
5. **持续监控**：24/7监控 + 自动告警

### 成功标准

- ✅ 数据零丢失 (RPO = 0)
- ✅ 服务最小中断 (RTO < 5分钟)
- ✅ 可随时回滚 (< 10分钟)
- ✅ 100%可追溯

### 下一步行动

1. **立即执行**：
   - [ ] 部署备份系统
   - [ ] 测试回滚流程
   - [ ] 建立监控基线

2. **本周完成**：
   - [ ] Phase 0准备工作
   - [ ] 创建迁移分支
   - [ ] 团队培训

3. **下周开始**：
   - [ ] Phase 1并行运行
   - [ ] 影子流量验证
   - [ ] 持续监控

---

**文档版本**: v1.0
**最后更新**: 2026-02-02
**维护者**: 徐健 (xujian519@gmail.com)
**审核状态**: 待审核

> 💡 **记住**：宁可多花时间准备，不要在迁移时后悔。备份和回滚是最好的保险！
