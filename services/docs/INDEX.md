# Services 文档索引

**文档更新时间**: 2025-12-13 23:20:00

## 📚 文档导航

### 📊 报告文档
查看所有服务相关的分析报告：

- [清理报告](reports/SERVICES_CLEANUP_REPORT.md)
  - 服务目录清理成果
  - 整理前后对比
  - 清理效果统计

- [一致性检查报告](reports/SERVICES_CONSISTENCY_REPORT.md)
  - 20个服务的详细分析
  - 发现的问题列表
  - 改进建议

- [优化总结报告](reports/SERVICES_OPTIMIZATION_SUMMARY.md)
  - 优化执行成果
  - 关键指标提升
  - 工具和文档创建

### 📝 服务模板
创建新服务的标准和指南：

- [服务标准模板](templates/SERVICE_TEMPLATE.md)
  - Python/Node.js服务结构
  - 最佳实践指南
  - 文件清单

- [服务创建工具](../create_service.py)
  ```bash
  # 创建Python服务
  python3 create_service.py my-service --type python

  # 创建Node.js服务
  python3 create_service.py my-service --type nodejs
  ```

### 📋 工作进度
正在进行的或已完成的计划：

- [优化计划](work-in-progress/SERVICES_OPTIMIZATION_PLAN.md)
  - 分阶段优化策略
  - 任务清单
  - 时间安排

### 🔧 工具和脚本

#### 核心工具
- **create_service.py** - 服务创建器
  - 快速生成标准服务
  - 支持Python和Node.js
  - 包含测试和Docker配置

- **agent_manager.py** - 智能体管理器
  ```bash
  python3 agent_manager.py start    # 启动所有智能体
  python3 agent_manager.py status   # 查看状态
  python3 agent_manager.py comm --from a --to b --message "hello"
  ```

#### 批量脚本
- **core-services/start_all.sh** - 启动所有核心服务
- **data-services/start_all.sh** - 启动所有数据服务

### 📖 服务文档

#### 核心服务
- [api-gateway](../api-gateway/README.md) - API网关（Node.js）
- [athena-platform](../athena-platform/README.md) - Athena平台
- [yunpat-agent](../yunpat-agent/docs/README.md) - 云熙智能体

#### 服务集合
- [agent-services](../agent-services/README.md) - 智能体服务
- [core-services](../core-services/README.md) - 核心基础设施
- [data-services](../data-services/README.md) - 数据服务

#### 新创建的服务
- [browser-automation-standard](../browser-automation-standard/README.md)
- [data-visualization](../data-visualization/README.md)

## 🎯 快速查找

### 按文档类型
- **报告**: reports/
- **模板**: templates/
- **工具**: 根目录和docs/
- **服务文档**: 各服务目录

### 按服务类型
- **AI服务**: ai-models, ai-services
- **智能体**: yunpat-agent, agent-services
- **核心服务**: api-gateway, core-services
- **数据服务**: data-services, crawler
- **工具服务**: utility_services, visualization-tools

## 📌 重要提示

1. **创建新服务**：
   ```bash
   cd services
   python3 create_service.py new-service
   ```

2. **管理服务**：
   - 使用start_all.sh批量启动
   - 使用agent_manager.py管理智能体

3. **查看状态**：
   ```bash
   # 查看服务概览
   cat SERVICES_OVERVIEW.md

   # 查看目录结构
   cat DIRECTORY_STRUCTURE.md
   ```

## 🔗 相关链接

- [Athena工作平台](../README.md)
- [服务标准模板](templates/SERVICE_TEMPLATE.md)
- [云熙智能体](../yunpat-agent/)

---

**维护者**: Athena开发团队
**最后更新**: 2025-12-13 23:20:00