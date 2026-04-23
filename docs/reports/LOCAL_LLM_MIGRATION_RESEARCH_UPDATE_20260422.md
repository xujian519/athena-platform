# 本地LLM迁移研究更新报告

**更新时间**: 2026-04-22
**更新原因**: 用户指出Qwen3.5/3.6已发布，不应使用过时的Qwen2.5
**关键更正**: 用户使用oMLX，不是Ollama

---

## 📋 更新内容总结

### 1. 模型推荐更新（Qwen2.5 → Qwen3.5/3.6）

#### 原推荐（已过时）
- ❌ Qwen2.5-7B-Instruct（2024年版本）

#### 新推荐（2026年最新）
- ⭐ **Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit**
  - MLX Community ID: `mlx-community/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit`
  - 80.4k下载，160个like，最受欢迎
  - Claude 4.6 Opus蒸馏版本，推理能力强
  - 文件大小：~16GB
  - 推理速度：30-40 tokens/sec

- ⚡ **Qwen3.5-9B-MLX-4bit**
  - MLX Community ID: `mlx-community/Qwen3.5-9B-MLX-4bit`
  - 73.3k下载，101个like
  - 最轻量选择，快速响应
  - 文件大小：~2GB
  - 推理速度：60-80 tokens/sec

- 🔥 **Qwen3.6-35B-A3B-UD-MLX-4bit**（不推荐）
  - MLX Community ID: `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit`
  - 刚发布2天，仅16.9k下载
  - 稳定性待验证，不推荐生产使用

### 2. 安装方式更新（Ollama → oMLX）

#### 原方案（错误）
```bash
# ❌ 用户不使用Ollama
ollama pull qwen2.5:7b-instruct
ollama serve
```

#### 新方案（正确）
```bash
# ✅ 用户使用oMLX
# 编辑 ~/.omlx/model_settings.json
{
  "models": [
    {
      "id": "qwen3.5-27b-claude",
      "model_path": "mlx-community/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit",
      "type": "llm"
    },
    {
      "id": "qwen3.5-9b",
      "model_path": "mlx-community/Qwen3.5-9B-MLX-4bit",
      "type": "llm"
    }
  ]
}

# 重启oMLX服务
omlx restart
```

### 3. 配置代码更新

#### 更新了以下部分
- ✅ 模型对比表（Qwen2.5 → Qwen3.5/3.6）
- ✅ 推荐方案配置（Ollama → oMLX）
- ✅ 实施路径（Ollama安装 → oMLX配置）
- ✅ 风险评估（添加Qwen3.6稳定性风险）
- ✅ 立即行动项（更新为Qwen3.5安装步骤）

---

## 📊 模型对比（更新后）

| 模型 | 参数 | 文件大小 | 推理速度 | 推荐度 | 用途 |
|------|------|----------|----------|--------|------|
| **Qwen3.5-27B-Claude** | 27B | ~16GB | 30-40 t/s | ⭐⭐⭐⭐⭐ | 复杂推理 |
| **Qwen3.5-9B** | 9B | ~2GB | 60-80 t/s | ⭐⭐⭐⭐⭐ | 快速响应 |
| **Qwen3.6-35B-A3B** | 35B | ~6GB | 25-35 t/s | ⭐⭐⭐ | 尝鲜测试 |
| **Gemma-4-E2B-IT** | 4.7B | ~3GB | 50-70 t/s | ⭐⭐⭐⭐⭐ | 多模态 |

---

## 🎯 关键要点

### 为什么选择Qwen3.5而不是Qwen3.6？

1. **稳定性**: Qwen3.5已成熟，用户反馈多（80.4k下载）
2. **Claude蒸馏**: Qwen3.5-27B有Claude 4.6 Opus蒸馏版本
3. **验证**: Qwen3.6刚发布2天，稳定性待验证

### 为什么使用oMLX而不是Ollama？

1. **用户环境**: 用户已安装oMLX（8009端口）
2. **Apple Silicon优化**: oMLX专为Apple Silicon优化
3. **MLX Community**: 直接从Hugging Face MLX Community下载，无需转换

---

## 📝 更新文件列表

- ✅ `/Users/xujian/Athena工作平台/docs/reports/LOCAL_LLM_MIGRATION_RESEARCH_20260422.md`
  - 模型推荐部分（第111-160行）
  - 配置建议部分（第160-250行）
  - 实施路径部分（第280-360行）
  - 实施建议部分（第475-575行）
  - 风险评估部分（第575-620行）
  - 总结与建议部分（第620-650行）

---

## 🚀 下一步行动

1. 安装Qwen3.5模型到oMLX
2. 修改小娜降级策略（优先使用Qwen3.5-27B-Claude）
3. 更新本地8009适配器支持模型切换
4. 测试和验证

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-22
