#!/usr/bin/env python3
"""
Agentic Design Patterns 简化下载工具 - 专注中文和英文备份
Agentic Design Patterns Simple Downloader - Focus on Chinese and English Backup
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def download_with_git() -> Any:
    """使用Git克隆仓库"""
    base_dir = Path("/Users/xujian/Athena工作平台")
    target_dir = base_dir / "knowledge" / "agentic_design_patterns"

    # 创建目录
    target_dir.mkdir(parents=True, exist_ok=True)

    # GitHub仓库地址
    repo_url = "https://github.com/ginobefun/agentic-design-patterns-cn.git"

    print("🔄 开始下载 Agentic Design Patterns...")
    print(f"📁 目标目录: {target_dir}")
    print(f"🌐 仓库地址: {repo_url}")

    try:
        # 克隆仓库
        cmd = ['git', 'clone', repo_url, str(target_dir / "original")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(target_dir))

        if result.returncode == 0:
            print("✅ 下载成功！")

            # 分析下载内容
            original_dir = target_dir / "original"
            if original_dir.exists():
                print("\n📊 下载内容分析:")

                # 统计文件
                total_files = 0
                md_files = 0
                folders = 0

                for root, dirs, files in os.walk(original_dir):
                    folders += len(dirs)
                    for file in files:
                        total_files += 1
                        if file.endswith('.md'):
                            md_files += 1

                print(f"   📁 目录数量: {folders}")
                print(f"   📄 总文件数: {total_files}")
                print(f"   📝 Markdown文件: {md_files}")

                # 检查关键文件
                key_files = ['README.md', 'docs/', 'content/', 'chapters/']
                print("\n🔍 检查关键文件:")

                for key_file in key_files:
                    key_path = original_dir / key_file
                    if key_path.exists():
                        print(f"   ✅ {key_file}")
                    else:
                        print(f"   ❌ {key_file} (未找到)")

                # 列出所有Markdown文件
                print("\n📚 Markdown文件列表:")
                for root, dirs, files in os.walk(original_dir):
                    for file in files:
                        if file.endswith('.md'):
                            rel_path = os.path.relpath(os.path.join(root, file), original_dir)
                            print(f"   📖 {rel_path}")

            return True

        else:
            print(f"❌ Git克隆失败: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ Git未安装，请先安装Git")
        return False
    except Exception as e:
        print(f"❌ 下载过程出错: {e}")
        return False

def create_reading_index(target_dir) -> Any:
    """创建阅读索引"""
    index_content = f"""# 📚 Agentic Design Patterns 阅读索引

> **下载时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **来源**: https://github.com/ginobefun/agentic-design-patterns-cn
> **内容**: 中文翻译版 + 英文原文

## 📁 目录结构

```
knowledge/agentic_design_patterns/
├── original/          # 原始GitHub仓库内容
│   ├── README.md     # 项目说明
│   ├── docs/         # 文档目录
│   ├── chapters/     # 章节内容
│   └── assets/       # 资源文件
├── reading_index.md  # 本索引文件
└── usage_notes.md    # 使用说明
```

## 🎯 快速开始

### 1. 阅读项目介绍
打开 `original/README.md` 了解项目概况

### 2. 浏览章节内容
查看 `original/` 目录下的Markdown文件

### 3. 使用代码示例
检查 `examples/` 或 `code/` 目录（如果有）

## 📖 推荐阅读顺序

1. **项目概述** → README.md
2. **基础章节** → 从第1章开始
3. **实践示例** → examples目录
4. **参考资料** → docs目录

## 🔍 搜索和定位

- 使用文件名搜索特定章节
- 通过目录结构快速定位内容
- 利用Markdown编辑器的全文搜索功能

## 💡 阅读提示

- 该项目提供中英文对照版本
- 中文内容通常会有特殊标记或高亮
- 建议使用支持Markdown的阅读器

## 📞 如有问题

如果下载不完整，可以：
1. 重新运行下载脚本
2. 检查网络连接
3. 手动访问GitHub仓库查看

---

*最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    with open(target_dir / "reading_index.md", 'w', encoding='utf-8') as f:
        f.write(index_content)

def create_usage_notes(target_dir) -> Any:
    """创建使用说明"""
    notes_content = f"""# 📖 Agentic Design Patterns 使用说明

## 🚀 如何访问

### 方法1: 使用Markdown阅读器
推荐使用Typora、Mark Text等专业的Markdown阅读器

### 方法2: 使用VS Code
1. 安装Markdown All in One插件
2. 打开文件夹: `{target_dir}/original`
3. 使用预览功能阅读

### 方法3: 使用在线工具
将文件上传到在线Markdown预览网站

## 📚 内容特色

### 🇨🇳 中文优化
- 中英文对照显示
- 中文黄色高亮（在原始版本中）
- 专业术语统一翻译

### 📖 结构清晰
- 按章节组织内容
- 代码示例完整
- 配图和说明丰富

### 🎯 实用导向
- 理论与实践结合
- 提供完整代码示例
- 适合开发者学习

## 🔧 最佳实践

### 阅读建议
1. **按顺序阅读**: 从基础到高级循序渐进
2. **理论实践结合**: 阅读理论的同时尝试代码示例
3. **笔记记录**: 重要概念和实现方法做好笔记
4. **定期回顾**: 复习已学内容加深理解

### 学习路径
```
第1-7章: 核心模式 (基础)
    ↓
第8-14章: 高级模式 (进阶)
    ↓
第15-21章: 生产模式 (实战)
    ↓
实践项目: 应用所学模式
```

## 📊 424页内容概览

根据之前的分析，该书包含：

### 🎯 第一部分：核心设计模式 (103页)
1. 提示链 (Prompt Chaining)
2. 路由 (Routing)
3. 并行化 (Parallelization)
4. 反思 (Reflection)
5. 工具使用 (Tool Use)
6. 规划 (Planning)
7. 多智能体协作 (Multi-Agent Collaboration)

### 🚀 第二部分：高级设计模式 (61页)
8. 记忆管理 (Memory Management)
9. 学习与适应 (Learning and Adaptation)
10. 模型上下文协议 (Model Context Protocol)
11. 目标设定与监控 (Goal Setting and Monitoring)

### 🔗 第三部分：集成设计模式 (34页)
12. 异常处理与恢复 (Error Handling and Recovery)
13. 人机协作 (Human-AI Collaboration)
14. 知识检索 (RAG)

### 🏭 第四部分：生产设计模式 (114页)
15. 智能体间通信 (A2A)
16. 资源感知优化 (Resource-Aware Optimization)
17. 推理技术 (Reasoning)
18. 护栏/安全模式 (Guardrails/Safety)
19. 评估与监控 (Evaluation and Monitoring)
20. 优先级排序 (Prioritization)
21. 探索与发现 (Exploration and Discovery)

## 💻 代码示例说明

书中包含丰富的代码示例，涵盖：
- Python实现
- JavaScript/Node.js版本
- 实际项目应用案例
- 性能优化技巧

## 🔄 持续更新

该项目是活跃的开源项目，建议：
- 定期检查GitHub更新
- 关注Issue和讨论
- 参与社区贡献

---

*祝您学习愉快！如有问题，请参考项目的GitHub页面*
"""

    with open(target_dir / "usage_notes.md", 'w', encoding='utf-8') as f:
        f.write(notes_content)

def main() -> None:
    """主函数"""
    print("=" * 60)
    print("📚 Agentic Design Patterns 下载工具")
    print("🎯 专注中文 + 英文备份")
    print("=" * 60)

    # 执行下载
    if download_with_git():
        target_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")

        # 创建辅助文件
        create_reading_index(target_dir)
        create_usage_notes(target_dir)

        print("\n🎉 下载和配置完成！")
        print(f"\n📁 内容位置: {target_dir}")
        print(f"📖 阅读索引: {target_dir}/reading_index.md")
        print(f"📝 使用说明: {target_dir}/usage_notes.md")

        print("\n🚀 快速开始:")
        print(f"   cd {target_dir}/original")
        print("   # 使用你喜欢的Markdown阅读器打开README.md")

    else:
        print("\n❌ 下载失败")
        print("\n🔧 备选方案:")
        print("1. 手动访问GitHub下载")
        print("2. 检查网络连接")
        print("3. 确保Git已正确安装")

if __name__ == "__main__":
    main()
