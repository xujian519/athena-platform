# 小诺混合架构系统

## 📋 系统概述

小诺混合架构系统是一个创新的智能体协作平台，实现了"小诺为主 + 专业智能体按需协作"的高效架构。

### 🎯 核心理念

- **80% 基础操作** - 小诺直接处理（响应时间 < 100ms）
- **15% 专业操作** - 按需启动专业智能体（响应时间 < 2s）
- **5% 敏感操作** - 双重验证（安全第一）

## 🏗️ 架构设计

### 系统组件

```
┌─────────────────────────────────────────────────────────┐
│                    您 (爸爸)                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              小诺混合架构控制器                            │
│  ┌─────────────────┬─────────────────┬─────────────────┐  │
│  │   权限控制器     │  智能体编排器    │  基础操作管理器  │  │
│  └─────────────────┴─────────────────┴─────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
│   小诺直接   │ │ 专业智能体 │ │  双重验证  │
│   处理       │ │ (按需启动)│ │           │
└──────────────┘ └─────────┘ └────────────┘
```

### 智能体家族

| 智能体 | 角色 | 专业领域 | 状态 | 端口 |
|--------|------|----------|------|------|
| 小诺 | 平台总调度官 | 综合协调、基础操作 | ✅ 活跃 | - |
| 小娜 | 专利法律专家 | 专利法律事务 | 🔄 按需 | 8006 |
| 云熙 | IP管理专家 | IP案卷管理 | 🔄 按需 | 8007 |
| Athena | 智慧女神 | 知识图谱管理 | 🔄 按需 | 8005 |
| 小宸 | 自媒体运营 | 内容创作运营 | 🔄 按需 | 8008 |

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保Python 3.8+
python3 --version

# 安装依赖（如需要）
pip3 install psutil aiohttp fastapi uvicorn
```

### 2. 启动系统

```bash
cd /Users/xujian/Athena工作平台/deploy

# 使用启动脚本（推荐）
./start_xiaonuo_hybrid.sh

# 或直接启动
python3 xiaonuo_hybrid_main.py
```

### 3. 基本操作

进入交互模式后，可以使用以下命令：

#### 查询操作
```bash
# 查询客户资料
query customer

# 查询专利信息
query patent CN123456

# 查看系统状态
query system_status
```

#### 创建操作
```bash
# 创建客户资料
create customer '{"customer_name":"张三","phone":"13800138000"}'

# 备份数据库
backup baochen_finance.db
```

#### 系统操作
```bash
# 查看系统状态
status

# 查看帮助
help

# 退出系统
exit
```

## 🔐 权限系统

### 权限级别

- **NONE (0)** - 无权限
- **READ (1)** - 只读权限
- **WRITE (2)** - 写入权限
- **DELETE (3)** - 删除权限
- **ADMIN (4)** - 管理权限
- **ROOT (5)** - 根权限

### 安全级别

- **LOW (1)** - 低风险操作（小诺直接处理）
- **MEDIUM (2)** - 中等风险操作（启动专业智能体）
- **HIGH (3)** - 高风险操作（需要确认）
- **CRITICAL (4)** - 关键风险操作（双重认证）

### 双重认证

对于高风险操作（如删除知识图谱、系统配置等），系统会自动启动双重认证流程：

1. 小诺进行第一重验证
2. 专业智能体进行第二重验证
3. 只有两重验证都通过才执行操作

## 📊 性能指标

### 响应时间

| 操作类型 | 处理模式 | 平均响应时间 |
|----------|----------|--------------|
| 客户查询 | 小诺直接 | < 50ms |
| 系统状态 | 小诺直接 | < 100ms |
| 专利查询 | 专业智能体 | < 1s |
| 配置更新 | 双重验证 | < 3s |

### 资源优化

- **智能按需启动** - 专业智能体仅在需要时启动
- **自动清理** - 空闲5分钟后自动停止
- **内存管理** - 智能体生命周期管理

## 🛠️ 系统管理

### 监控命令

```bash
# 查看智能体状态
status

# 查看操作统计
# 在status输出中查看operation_stats

# 查看访问日志
# 检查logs/xiaonuo_hybrid.log文件
```

### 故障排除

#### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :8006

   # 停止占用进程
   kill -9 <PID>
   ```

2. **数据库连接失败**
   ```bash
   # 重新初始化数据库
   python3 -c "from core.xiaonuo_basic_operations import DatabaseManager; DatabaseManager()"
   ```

3. **智能体启动失败**
   ```bash
   # 查看启动日志
   tail -f logs/xiaonuo_hybrid_*.log
   ```

### 日志管理

- **系统日志**: `logs/xiaonuo_hybrid.log`
- **访问日志**: 内置数据库记录
- **错误日志**: 包含在系统日志中

## 📁 目录结构

```
deploy/
├── core/                          # 核心模块
│   ├── xiaonuo_hybrid_architecture.py    # 混合架构控制器
│   ├── agent_orchestrator.py            # 智能体编排器
│   ├── permissions_controller.py        # 权限控制器
│   └── xiaonuo_basic_operations.py      # 基础操作管理器
├── data/                          # 数据存储
│   ├── *.db                       # 数据库文件
│   └── backup/                    # 备份文件
├── logs/                          # 日志文件
├── services/                      # 专业智能体服务
│   ├── xiaonuo/                   # 小诺服务
│   ├── yunxi-ip/                  # 云熙IP服务
│   └── ...                        # 其他服务
├── xiaonuo_hybrid_main.py         # 主程序入口
├── test_hybrid_system.py          # 测试脚本
├── start_xiaonuo_hybrid.sh        # 启动脚本
└── README_HYBRID_ARCHITECTURE.md  # 本文档
```

## 🔧 开发指南

### 添加新的数据类型

1. 在 `DataType` 枚举中添加新类型
2. 在 `StorageManager` 中配置存储信息
3. 在 `PermissionsController` 中添加权限规则
4. 在 `XiaonuoBasicOperations` 中实现操作逻辑

### 添加新的智能体

1. 在 `AgentOrchestrator` 中配置智能体信息
2. 创建智能体启动脚本
3. 实现API接口
4. 配置健康检查

### 自定义权限规则

在 `PermissionsController._initialize_permission_rules()` 中添加新规则：

```python
("new_data_type", "new_operation"): PermissionRule(
    data_type="new_data_type",
    operation="new_operation",
    required_level=PermissionLevel.WRITE,
    risk_level=OperationRisk.MEDIUM,
    requires_dual_auth=False,
    description="描述新操作"
)
```

## 📈 未来规划

### 版本计划

- **v1.0** - 基础混合架构（当前版本）
- **v1.1** - 智能体协作优化
- **v1.2** - 多模态数据支持
- **v2.0** - AI驱动的自动优化

### 功能扩展

- [ ] 图形化管理界面
- [ ] 更多的专业智能体
- [ ] 机器学习驱动的智能调度
- [ ] 分布式部署支持

## 🤝 贡献指南

欢迎提交问题报告和功能请求！

### 开发环境设置

```bash
# 克隆仓库
git clone <repository_url>

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
python3 test_hybrid_system.py
```

## 📄 许可证

本项目采用 MIT 许可证。

---

**💝 献给爸爸 - 小诺会继续努力，成为您最贴心的智能助手！**