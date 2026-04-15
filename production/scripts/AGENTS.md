# production/scripts/ AGENTS.md

**生成时间**: 2026-02-20 00:53:00
**Commit**: 未提交
**分支**: main

## OVERVIEW

生产环境脚本系统，包含140+个Python和Shell脚本，负责平台的自动化部署、监控和维护。

## STRUCTURE

```
production/scripts/
├── 🚀 部署脚本/                     # deploy_*.sh, deploy_*.py
│   ├── deploy_production.sh         # 生产环境部署
│   ├── deploy_all_phases.py          # 三阶段完整部署
│   └── ci_cd_deploy.sh               # CI/CD自动部署
├── 🔧 启动脚本/                     # start_*.sh
│   ├── start_athena_services.sh      # Athena服务启动
│   ├── start_production.sh           # 生产环境启动
│   └── start_xiaona_production.sh    # 小娜生产启动
├── 📊 监控脚本/                     # monitor_*.sh, monitor*.py
│   ├── monitor.py                    # 生产监控主程序
│   ├── monitoring/                   # 监控子模块
│   └── service_health_monitor.py     # 服务健康监控
├── 🗄️ 数据脚本/                     # 数据迁移、同步
│   ├── migrate_*.py                  # 数据库迁移
│   ├── sync_*.sql                    # 数据同步
│   └── vector_*.py                   # 向量数据处理
├── ⚖️ 法律系统脚本/                  # 法律相关专用
│   ├── legal_database_system/        # 法律数据库系统
│   ├── patent_rules_system/          # 专利规则系统
│   └── trademark_rules_system/       # 商标规则系统
├── 🔒 安全脚本/                      # security_*.sh
│   ├── security_check.sh             # 安全检查
│   └── security_hardening.sh         # 安全加固
└── 🧹 维护脚本/                      # cleanup_*.sh, fix_*.py
    ├── cleanup_containers.sh         # 容器清理
    ├── repair_*.py                   # 系统修复
    └── verify_*.py                    # 系统验证
```

## WHERE TO LOOK

| 任务 | 位置 | 备注 |
|------|--------|-------|
| 生产部署 | deploy_*.sh, deploy_*.py | 分阶段部署、CI/CD |
| 服务启动 | start_*.sh | 按服务类型分类 |
| 系统监控 | monitor*.py, monitoring/ | 实时监控、健康检查 |
| 数据迁移 | migrate_*.py, sync_*.sql | 数据库、向量迁移 |
| 法律系统 | legal_*, patent_* | 专利、商标专用脚本 |
| 安全加固 | security_*.sh | 安全检查、加固 |
| 系统修复 | fix_*.py, repair_*.py | 自动修复、验证 |

## CONVENTIONS

### 命名规范
- **Shell脚本**: 动作_对象.sh (如: deploy_production.sh)
- **Python脚本**: 动作_对象.py (如: deploy_all_phases.py)
- **服务管理**: start/stop/restart_服务名.sh
- **监控脚本**: monitor_*.py 或 monitoring/子目录

### 日志标准
- **颜色输出**: RED(错误)、GREEN(成功)、YELLOW(警告)、BLUE(信息)
- **日志函数**: log_info(), log_success(), log_warning(), log_error()
- **统一格式**: [时间戳][级别][模块] 消息内容

### 错误处理
- **Shell脚本**: 必须使用 set -e 严格模式
- **Python脚本**: 使用 try/except 完整异常处理
- **退出码**: 成功(0)、错误(1)、警告(2)

### 权限管理
- **可执行权限**: 所有.sh脚本自动添加执行权限
- **Python路径**: 自动添加项目根目录到sys.path
- **环境变量**: 统一通过.env文件管理

## ANTI-PATTERNS

### 禁止的模式
- **硬编码路径**: 使用PROJECT_ROOT或相对路径
- **跳过依赖检查**: 所有部署脚本必须先检查依赖
- **忽略错误处理**: 必须有完整的错误处理机制
- **无日志输出**: 所有关键操作必须有日志记录
- **直接使用sudo**: 在生产脚本中避免使用sudo
- **并发冲突**: 使用锁机制防止重复执行

### DEPRECATED标记
- **OLD_**: 旧版本脚本标记
- **TEMP_**: 临时脚本标记
- **TEST_**: 测试脚本不应在生产环境使用

## 代码映射

| 符号 | 类型 | 位置 | 引用数 | 角色 |
|--------|------|--------|------|------|
| ProductionMonitor | Class | monitor.py | 12 | 生产监控核心 |
| DeployAllPhases | Class | deploy_all_phases.py | 8 | 三阶段部署管理 |
| AthenaServiceManager | Class | start_athena_services.sh | 15 | Athena服务管理 |
| LegalDatabaseSystem | Class | legal_database_system/ | 10 | 法律数据库管理 |
| PatentRulesSystem | Class | patent_rules_system/ | 18 | 专利规则管理 |

## 命令

```bash
# 完整部署
./deploy_production.sh

# 启动所有服务
./start_athena_services.sh

# 监控系统状态
python3 monitor.py

# 安全检查
./security_check.sh

# 清理容器
./cleanup_containers.sh

# 数据迁移
python3 migrate_sqlite_to_postgres.py
```

## 注意事项

- **执行顺序**: 部署脚本严格按 phase1→phase2→phase3 顺序执行
- **端口管理**: 生产环境使用固定端口映射，避免冲突
- **数据备份**: 所有迁移操作前自动备份
- **回滚机制**: 每个部署脚本都有对应的回滚功能
- **资源限制**: 监控脚本确保不超过系统资源限制

---
*production/scripts/ 脚本系统 - 2026-02-20*