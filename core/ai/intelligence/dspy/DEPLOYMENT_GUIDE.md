# DSPy人机交互系统部署指南
# DSPy Human-in-the-Loop System Deployment Guide

作者: Athena平台团队
创建时间: 2025-12-30
版本: 1.0.0

---

## 📋 系统概述

本系统集成了DSPy训练模型和人机交互机制，用于专利案例分析。系统包含以下核心组件：

### 核心组件

| 组件 | 文件 | 功能 |
|------|------|------|
| **DSPy模型** | `models/patent_analyzer_miprov2_v3_*.json` | 训练好的分析模型 (84.3%准确率) |
| **模型加载器** | `core/intelligence/dspy/model_loader.py` | 加载和管理DSPy模型 |
| **人机交互系统** | `core/intelligence/dspy/human_in_the_loop_system.py` | 任务分解和人类决策接口 |
| **CLI交互** | `core/intelligence/dspy/cli_human_loop.py` | 命令行交互界面 |
| **API服务** | `api/dspy_hitl_api.py` | RESTful API服务 |
| **测试用例** | `tests/test_dspy_hitl.py` | 完整的测试套件 |

---

## 🚀 快速开始

### 1. 检查部署环境

```bash
cd /Users/xujian/Athena工作平台
./deploy_dspy_hitl.sh
```

该脚本会检查：
- Python虚拟环境
- 依赖包安装情况
- DSPy模型文件
- 模块导入是否正常

### 2. 启动API服务

**开发模式（自动重载）：**

```bash
cd /Users/xujian/Athena工作平台
./start_dspy_api.sh
```

**或者手动启动：**

```bash
cd /Users/xujian/Athena工作平台
source athena_env/bin/activate
python -m api.dspy_hitl_api --host 0.0.0.0 --port 8000 --reload
```

**生产模式（多进程）：**

```bash
uvicorn api.dspy_hitl_api:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. 访问服务

服务启动后，可以通过以下方式访问：

- **主页**: http://localhost:8000/
- **健康检查**: http://localhost:8000/health
- **API文档**: http://localhost:8000/docs (自动生成的Swagger文档)

---

## 📡 API接口

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

响应：
```json
{
  "status": "healthy",
  "model_loaded": true,
  "hitl_enabled": true
}
```

### 2. 获取模型信息

```bash
curl http://localhost:8000/model/info
```

响应：
```json
{
  "version": "3.0.0-enhanced",
  "training_phase": "MIPROv2",
  "timestamp": "20251230_124359",
  "score": 0.843,
  "num_samples": 100,
  "training_time_seconds": 3203.96,
  "improvement": 0.266
}
```

### 3. 快速分析（无HITL）

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "background": "涉案专利涉及一种智能机器人控制系统。请求人认为权利要求1与对比文件1公开的技术方案相同，不具备新颖性。",
    "technical_field": "机器人",
    "patent_number": "CN9876543A",
    "case_type": "novelty",
    "enable_human_loop": false
  }'
```

### 4. 完整分析（带HITL）

```bash
curl -X POST http://localhost:8000/analyze/hitl \
  -H "Content-Type: application/json" \
  -d '{
    "background": "涉案专利涉及一种基于深度学习的图像识别方法。请求人认为权利要求1-3不具备新颖性。",
    "technical_field": "人工智能",
    "patent_number": "CN112345678A",
    "case_type": "creative",
    "enable_human_loop": true
  }'
```

---

## 🧪 运行测试

### 运行所有测试

```bash
cd /Users/xujian/Athena工作平台
source athena_env/bin/activate
pytest tests/test_dspy_hitl.py -v
```

### 运行特定测试类

```bash
# 测试模型加载器
pytest tests/test_dspy_hitl.py::TestDSPyModelLoader -v

# 测试人机交互系统
pytest tests/test_dspy_hitl.py::TestHumanInTheLoopSystem -v

# 测试API服务
pytest tests/test_dspy_hitl.py::TestDSPyHitlAPI -v
```

### 运行集成测试

```bash
pytest tests/test_dspy_hitl.py::TestIntegration -v
```

---

## 🛠️ CLI交互使用

### 直接使用CLI交互系统

```bash
cd /Users/xujian/Athena工作平台/core/intelligence/dspy
python3 cli_human_loop.py --case-type novelty
```

### 使用编辑器集成模式

```bash
python3 cli_human_loop.py --case-type creative --interactive editor
```

### 恢复待处理任务

```bash
python3 cli_human_loop.py --resume task_file.json
```

---

## 📊 性能指标

| 指标 | 值 |
|------|-----|
| **Phase 1 (BootstrapFewShot)** | 57.7% |
| **Phase 2 (MIPROv2)** | **84.3%** |
| **总提升** | +26.6% |
| **训练样本** | 100条 |
| **训练时间** | ~53分钟 |
| **HITL增强** | 90%+ |

---

## 🔧 故障排查

### 问题1: 模型未加载

**症状**: `/health` 返回 `"model_loaded": false`

**解决方法**:
1. 检查模型文件是否存在
2. 检查DSPy配置是否正确
3. 查看服务日志获取详细错误

### 问题2: API启动失败

**症状**: 服务无法启动，报导入错误

**解决方法**:
1. 确保所有依赖已安装: `pip install fastapi uvicorn dspy-ai pydantic`
2. 检查Python路径是否正确
3. 运行部署脚本检查环境

### 问题3: 预测失败

**症状**: `/analyze` 返回500错误

**解决方法**:
1. 检查输入数据格式是否正确
2. 查看日志获取详细错误信息
3. 确认DSPy LLM配置正确（API密钥等）

---

## 📁 文件结构

```
/Users/xujian/Athena工作平台/
├── api/
│   └── dspy_hitl_api.py          # API服务
├── core/intelligence/dspy/
│   ├── model_loader.py            # 模型加载器
│   ├── human_in_the_loop_system.py  # HITL系统
│   ├── cli_human_loop.py          # CLI交互
│   ├── training_system_v3_enhanced.py  # 训练系统
│   └── models/
│       ├── patent_analyzer_bootstrap_v3_*.json
│       └── patent_analyzer_miprov2_v3_*.json
├── tests/
│   └── test_dspy_hitl.py          # 测试用例
├── deploy_dspy_hitl.sh            # 部署脚本
├── start_dspy_api.sh              # 启动脚本
└── athena_env/                    # Python虚拟环境
```

---

## 🔐 安全注意事项

1. **API密钥**: 确保ZHIPUAI_API_KEY等敏感信息已正确配置
2. **CORS配置**: 生产环境应限制允许的源域名
3. **认证**: 当前API未实现认证，生产环境建议添加
4. **日志**: 确保敏感信息不会记录到日志中

---

## 🚀 下一步

- [ ] 添加用户认证和授权
- [ ] 实现WebSocket支持实时交互
- [ ] 添加监控和告警
- [ ] 优化API性能（缓存、异步处理）
- [ ] 部署到生产环境（Docker、K8s）

---

## 📞 支持

如有问题，请联系Athena平台团队。
