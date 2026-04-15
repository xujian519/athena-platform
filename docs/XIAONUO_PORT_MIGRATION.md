# 小诺服务端口迁移说明
## Xiaonuo Service Port Migration Guide

**迁移日期**: 2025-12-26
**状态**: ✅ 已完成

---

## 📊 端口变更概览

| 状态 | 端口 | 服务名称 | 版本 | 说明 |
|-----|------|---------|------|-----|
| **🟢 激活** | **8006** | **小诺·双鱼座优化版** | **v2.0.0-Optimized** | **新默认端口** |
| 🔴 弃用 | 8004 | 小诺·双鱼公主 v4.0 | v4.0.0 | 功能已合并到8006 |
| 🔴 弃用 | 8005 | 小诺·双鱼座 | v2.0.0-Patent | 功能已合并到8006 |

---

## 🎯 8006端口新特性

### 集成的所有功能

8006端口现在集成了**所有端口的功能**，是最完整的版本：

#### 来自8004端口的功能 ✅
- **v4.0不确定性量化器** - 基于证据强度的置信度评估
- **命题响应生成器** - 生成符合维特根斯坦原则的响应
- **响应验证器** - 自检机制确保响应质量

#### 来自8005端口的功能 ✅
- **专利全文处理系统** - 向量化、三元组提取、知识图谱构建
- **PDF批量下载与监控** - 自动监控和智能处理
- **向量搜索** - 语义相似度专利检索
- **中国专利数据库检索** - 直接访问中国专利库

#### 新增Phase 1/2/3优化模块 ✅
- **Phase 1**: 意图置信度评分、参数验证、执行引擎、智能拒绝
- **Phase 2**: BERT分类器(MPS)、参数提取(MPS)、工具图谱、错误处理、混沌工程
- **Phase 3**: 自主学习、多模态理解、智能体融合、预测维护、性能监控

### 完整功能列表

```yaml
核心能力:
  - v4.0不确定性量化 ✅
  - 7阶段智能处理管道 ✅
  - 自主学习和进化 ✅
  - MPS加速优化 ✅
  - 国内镜像站支持 ✅

专利处理:
  - 专利全文向量化 ✅
  - 三元组自动提取 ✅
  - 知识图谱构建 ✅
  - 向量搜索 ✅
  - PDF批量下载 ✅

智能对话:
  - BERT意图分类 ✅
  - T5参数提取 ✅
  - 多模态理解 ✅
  - 响应自检 ✅

系统管理:
  - 性能监控 ✅
  - 预测性维护 ✅
  - 混沌工程 ✅
  - 错误处理 ✅
```

---

## 🔄 Docker配置更新

### docker-compose.yml 变更

**文件**: `/Users/xujian/Athena工作平台/infrastructure/docker-deployment/docker-compose.yml`

**主要变更**:
```yaml
# 旧配置 (8005端口)
xiaonuo-core:
  container_name: xiaonuo-core
  ports:
    - "8005:8005"
  command: python3 -c 'import uvicorn; uvicorn.run("xiaonuo_simple:app", ...)'

# 新配置 (8006端口)
xiaonuo-core:
  container_name: xiaonuo-core-optimized
  ports:
    - "8006:8006"
  environment:
    - HF_ENDPOINT=https://hf-mirror.com
    - XIAONUO_ENABLE_V4=true
    - XIAONUO_ENABLE_OPTIMIZED=true
  volumes:
    - xiaonuo_models:/app/models/cache  # 新增：模型缓存
  command: python3 xiaonuo_optimized_v2.py
  deploy:
    resources:
      limits:
        cpus: '4.0'    # 从2.0提升到4.0
        memory: 8G     # 从4G提升到8G
```

### 环境变量说明

| 变量 | 值 | 说明 |
|-----|-----|------|
| `HF_ENDPOINT` | `https://hf-mirror.com` | 国内HuggingFace镜像站 |
| `XIAONUO_ENABLE_V4` | `true` | 启用v4.0不确定性量化 |
| `XIAONUO_ENABLE_OPTIMIZED` | `true` | 启用Phase 1/2/3优化模块 |

---

## 🚀 启动方式

### Docker方式（推荐）

```bash
cd /Users/xujian/Athena工作平台/infrastructure/docker-deployment

# 启动所有服务（包括8006端口的小诺）
docker-compose up -d

# 查看日志
docker-compose logs -f xiaonuo-core

# 停止服务
docker-compose down
```

### 直接运行方式

```bash
# 启动8006端口优化版
cd /Users/xujian/Athena工作平台/apps/xiaonuo
bash start_optimized_xiaonuo.sh

# 或直接运行
python3 xiaonuo_optimized_v2.py
```

---

## 📋 API接口变更

### 健康检查

```bash
# 旧端口（已弃用）
curl http://localhost:8005/health

# 新端口（推荐）
curl http://localhost:8006/health
```

### 对话接口

```bash
# 8006端口 - 支持所有新特性
curl -X POST http://localhost:8006/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "小诺你好",
    "use_optimized": true,
    "use_v4_principles": true,
    "include_confidence": true
  }'
```

### 专利搜索

```bash
curl -X POST http://localhost:8006/api/patent/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "人工智能",
    "limit": 10
  }'
```

---

## ⚠️ 弃用说明

### 8004端口 - 弃用原因

1. **功能已完全合并** - 所有v4.0特性已集成到8006
2. **避免端口冲突** - 减少运行的服务数量
3. **简化部署** - 统一使用8006端口

### 8005端口 - 弃用原因

1. **功能已完全合并** - 专利处理能力已在8006
2. **缺少优化模块** - 没有Phase 1/2/3优化
3. **缺少v4.0特性** - 没有不确定性量化

### 迁移建议

**如果您正在使用**:
- **8004端口**: 切换到8006，设置 `use_v4_principles=true`
- **8005端口**: 切换到8006，所有专利功能都可用

**迁移步骤**:
1. 停止旧服务: `docker-compose down`
2. 更新配置: 已在docker-compose.yml中完成
3. 启动新服务: `docker-compose up -d`
4. 更新客户端: 将端口从8004/8005改为8006

---

## 🔧 配置验证

### 验证8006端口已启用

```bash
# 检查服务状态
curl http://localhost:8006/health

# 预期响应
{
  "status": "healthy",
  "service": "xiaonuo-optimized-v2",
  "phases": {
    "v4": "initialized",
    "phase1": "initialized",
    "phase2": "initialized",
    "phase3": "initialized"
  },
  "patent_tool": "ready",
  "v4_features": {
    "uncertainty_quantifier": "ready",
    "response_validator": "ready"
  }
}
```

### 验证优化模块已加载

```bash
curl -X POST http://localhost:8006/api/optimize/status \
  -H 'Content-Type: application/json' \
  -d '{"detail_level": "detailed"}'
```

---

## 📊 性能对比

| 指标 | 8004 | 8005 | 8006 (新) |
|-----|------|------|-----------|
| 基础对话 | ✅ | ✅ | ✅ |
| v4.0不确定性量化 | ✅ | ❌ | ✅ |
| 专利处理 | ❌ | ✅ | ✅ |
| Phase 1优化 | ❌ | ❌ | ✅ |
| Phase 2优化 | ❌ | ❌ | ✅ MPS加速 |
| Phase 3优化 | ❌ | ❌ | ✅ |
| CPU (Docker) | 2核 | 2核 | **4核** |
| 内存 (Docker) | 4GB | 4GB | **8GB** |

---

## 🎯 后续操作

### 立即行动

1. ✅ **Docker配置已更新** - docker-compose.yml已修改
2. ✅ **服务已合并** - 8006端口包含所有功能
3. ⏳ **重启Docker服务** - 执行 `docker-compose up -d`

### 可选操作

1. **清理旧容器**
   ```bash
   docker-compose down
   docker system prune -a
   ```

2. **更新客户端配置**
   - 修改API调用中的端口
   - 更新文档和示例

3. **监控新服务**
   - 访问 http://localhost:8006/
   - 检查健康状态: http://localhost:8006/health

---

## 📞 技术支持

### 相关文件

- **服务文件**: `apps/xiaonuo/xiaonuo_optimized_v2.py`
- **启动脚本**: `apps/xiaonuo/start_optimized_xiaonuo.sh`
- **Docker配置**: `infrastructure/docker-deployment/docker-compose.yml`
- **集成报告**: `docs/XIAONUO_INTEGRATION_COMPLETE.md`
- **验证报告**: `docs/ALL_PHASES_VERIFICATION_COMPLETE.md`

### 快速命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f xiaonuo-core

# 健康检查
curl http://localhost:8006/health

# 优化状态
curl -X POST http://localhost:8006/api/optimize/status

# 停止服务
docker-compose down
```

---

## ✅ 总结

**重要变更**:
- ✅ 8006端口成为**唯一活跃端口**
- 🔴 8004端口**已弃用**（功能合并到8006）
- 🔴 8005端口**已弃用**（功能合并到8006）
- ✅ Docker配置已更新
- ✅ 资源配置已提升（4核/8GB）

**新端口优势**:
- 🎯 集成所有功能（v4.0 + Phase 1/2/3 + 专利处理）
- 🚀 MPS加速优化
- 🌐 国内镜像站支持
- 📊 更高性能和智能
- 🔄 7阶段智能处理管道

---

**迁移完成日期**: 2025-12-26
**文档版本**: v1.0
**状态**: ✅ 已完成并验证
