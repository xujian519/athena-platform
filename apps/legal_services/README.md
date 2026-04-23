# Legal Services - 历史存档目录

> **⚠️ 已废弃 - 此目录仅用于历史记录参考**

---

## 📜 目录状态

- **状态**: 🗄️ **已废弃/存档**
- **最后更新**: 2025-12-21
- **迁移状态**: ✅ 核心功能已迁移至 `core/` 和 `services/`

---

## 🔄 迁移历史

### 原始位置
```
apps/apps/legal_services/  (双重路径，目录结构异常)
```

### 迁移目标 (2025年12月)

| 原始模块 | 迁移位置 | 状态 |
|---------|---------|------|
| `apple_silicon_legal_intelligence.py` | `core/legal_world_model/` | ✅ 已迁移 |
| `unified_legal_intelligence_hub.py` | `services/legal-support/` | ✅ 已迁移 |
| `enhanced_bge_embedding_service.py` | `core/embedding/` | ✅ 已迁移 |
| `api/legal_qa/xiaonuo_legal_qa.py` | `core/agents/xiaona/` | ✅ 已迁移 |
| `api/legal_analysis/xiaona_legal_processor.py` | `core/agents/xiaona/` | ✅ 已迁移 |

---

## 📁 当前内容

### system_check_report_20251221_100547.json
- **用途**: 2025年12月21日的系统检查报告
- **内容**: 记录了迁移前的文件系统状态和组件完整性
- **价值**: 历史参考，用于验证迁移完整性

---

## ⚠️ 重要说明

1. **不要在此目录添加新代码** - 所有新法律智能功能应在 `core/legal_world_model/` 或 `services/legal-support/` 中开发

2. **PID文件已迁移** - 原本存储的进程ID文件现在统一管理在:
   - `logs/` - 服务日志和PID
   - `data/` - 运行时数据PID

3. **API端点已整合** - 法律相关的API现在通过Gateway统一路由:
   - Gateway: `http://localhost:8005`
   - 小娜API: `/api/xiaona/*`
   - 法律问答: `/api/legal/qa/*`

---

## 🔗 相关文档

- [法律世界模型](../../core/legal_world_model/README.md)
- [小娜智能体](../../core/agents/xiaona/README.md)
- [Gateway配置](../../gateway-unified/README.md)

---

## 🗑️ 清理计划

**建议保留时间**: 2026年6月（6个月存档期）

到期后可选择：
1. 删除整个目录
2. 移至 `archive/` 目录长期保存
3. 提取有价值的历史数据后删除

---

**维护者**: 徐健 (xujian519@gmail.com)
**文档创建**: 2026-04-22
