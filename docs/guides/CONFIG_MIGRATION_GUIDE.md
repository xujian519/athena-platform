# 配置迁移指南

> **第2阶段 Week 1 Day 5**
> **任务**: 迁移核心配置

---

## 📋 迁移任务清单

### 1. 数据库配置迁移

**源配置**:
- config/database_config.yaml
- config/database_unified.yaml
- config/database.yaml

**目标配置**:
- config/base/database.yml (已创建)

**迁移方式**: 使用配置适配器自动迁移

**验证**: 连接测试

### 2. Redis配置迁移

**源配置**:
- config/redis.yaml

**目标配置**:
- config/base/redis.yml (已创建)

**迁移方式**: 使用配置适配器自动迁移

**验证**: 连接测试

### 3. LLM配置迁移

**源配置**:
- config/llm_models_env_template.env
- config/domestic_llm_config.json

**目标配置**:
- config/base/llm.yml (已创建)

**迁移方式**: 使用配置适配器自动迁移

**验证**: API调用测试

### 4. 服务配置迁移

**源配置**:
- services/*/config*.yml

**目标配置**:
- config/services/*.yml (已创建: xiaona.yml, xiaonuo.yml, gateway.yml)

**迁移方式**: 手动迁移

**验证**: 服务启动测试

---

## 🔄 迁移步骤

### 自动迁移

```bash
# 运行配置迁移脚本
python3 scripts/migrate_configs.py
```

### 手动验证

```bash
# 验证数据库连接
python3 -c "
from core.config.unified_settings import UnifiedSettings
settings = UnifiedSettings()
print('数据库URL:', settings.database_url)
print('Redis URL:', settings.redis_url)
"

# 验证服务配置
python3 -c "
from core.config.unified_config_loader import create_unified_settings
settings = create_unified_settings('development', 'xiaona')
print('小娜服务配置:', settings.service)
"
```

---

## ✅ 验证标准

- [ ] 数据库配置已迁移
- [ ] Redis配置已迁移
- [ ] LLM配置已迁移
- [ ] 服务配置已迁移
- [ ] 适配器功能正常
- [ ] 旧配置仍可访问（兼容性）
- [ ] 新配置加载正常
- [ ] 系统功能验证通过

---

## ⚠️ 注意事项

1. **备份优先**: 迁移前已备份到移动硬盘
2. **兼容性**: 适配器确保旧配置仍可访问
3. **渐进式**: 新旧配置并存，逐步切换
4. **验证**: 每步迁移后都要验证功能

---

**迁移完成时间**: 2026-04-21
**执行人**: Claude Code (OMC模式)
**团队**: phase2-refactor
