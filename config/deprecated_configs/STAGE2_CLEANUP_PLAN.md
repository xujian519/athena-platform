# Stage 2配置清理计划

> 日期: 2026-04-21
> 状态: 执行中

## 保留配置（核心配置）

### JSON配置（保留）
- config/service_discovery.json - 服务发现配置
- config/agent_registry.json - Agent注册表
- config/llm_model_registry.json - LLM模型注册表
- config/ports.yaml - 端口分配
- config/permissions.yaml - 权限配置

### Python配置（保留）
- config/database.py - 数据库配置
- config/feature_flags.py - 功能开关
- config/numpy_compatibility.py - NumPy兼容性

### YAML配置（保留）
- config/docker/* - Docker配置（Grafana, Prometheus等）
- config/patent_agents.yaml - 专利Agent配置
- config/elasticsearch.yaml - Elasticsearch配置

## 废弃配置（移动到deprecated_configs）

### JSON配置（废弃）
- config/local_search_engine.json
- config/local_model_registry.json
- config/system_config.json
- config/optimized.json
- config/cache_optimized.json
- 等40+个JSON配置文件

### Python配置（废弃）
- config/configure_*.py - 各种LLM配置脚本
- config/vector_config.py
- config/bge_m3_mps_optimized.py
- config/config_manager.py

## 迁移后配置文件数量

| 类型 | 迁移前 | 迁移后 | 减少 |
|------|--------|--------|------|
| JSON | 52个 | ~5个 | **90%** |
| Python | 13个 | ~3个 | **77%** |
| YAML | 15个 | ~12个 | **20%** |
| **总计** | **80个** | **~20个** | **75%** |

## 清理完成标准

- ✅ 废弃配置已移动
- ✅ 核心配置已保留
- ✅ 配置文档已更新
- ✅ 系统测试通过
