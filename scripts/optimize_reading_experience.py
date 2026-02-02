#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agentic Design Patterns 阅读体验优化工具
Reading Experience Optimizer for Agentic Design Patterns
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
import shutil
from pathlib import Path
from datetime import datetime

class ReadingOptimizer:
    """阅读体验优化器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")
        self.original_dir = self.base_dir / "original"
        self.optimized_dir = self.base_dir / "optimized"

    def optimize_all_content(self) -> Any:
        """优化所有内容"""
        print("🎨 开始优化阅读体验...")

        # 创建优化目录
        self.optimized_dir.mkdir(exist_ok=True)

        # 优化Markdown文件
        self.optimize_markdown_files()

        # 复制静态资源
        self.copy_static_resources()

        # 创建导航文件
        self.create_navigation_system()

        # 生成阅读配置
        self.create_reading_config()

        # 创建阅读界面
        self.create_reading_interface()

        print("✅ 优化完成！")

    def optimize_markdown_files(self) -> Any:
        """优化Markdown文件"""
        print("📝 优化Markdown文件...")

        if not self.original_dir.exists():
            print("❌ 原始目录不存在，请先下载内容")
            return

        # 遍历所有Markdown文件
        for root, dirs, files in os.walk(self.original_dir):
            for file in files:
                if file.endswith('.md'):
                    self.optimize_single_markdown_file(root, file)

    def optimize_single_markdown_file(self, root, filename) -> Any:
        """优化单个Markdown文件"""
        source_file = Path(root) / filename
        rel_path = source_file.relative_to(self.original_dir)
        target_file = self.optimized_dir / rel_path

        # 创建目标目录
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # 读取原文件
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️ 读取文件失败: {source_file} - {e}")
            return

        # 优化内容
        optimized_content = self.add_reading_enhancements(content, str(rel_path))

        # 写入优化后的内容
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(optimized_content)
            print(f"✅ 优化完成: {rel_path}")
        except Exception as e:
            print(f"⚠️ 写入文件失败: {target_file} - {e}")

    def add_reading_enhancements(self, content, file_path) -> None:
        """添加阅读增强功能"""

        # 添加阅读头部信息
        header = f"""
# 📚 {Path(file_path).stem.replace('-', ' ').title()}

> **文件路径**: `{file_path}`
> **优化时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **阅读模式**: 优化版本

---

"""

        # 添加目录导航
        toc = self.generate_table_of_contents(content)

        # 优化中文显示
        content = self.optimize_chinese_formatting(content)

        # 添加导航按钮
        navigation = """

---

## 🧭 页面导航

- [📖 返回首页](./README.md)
- [📊 查看目录](javascript:show_toc())
- [🔍 搜索内容](javascript:show_search())
- [⬆️ 返回顶部](javascript:scroll_to_top())

## 📚 阅读工具

- 🌙 [深色模式](javascript:toggle_dark_mode())
- 📏 [字体大小](javascript:adjust_font_size())
- 🔖 [添加书签](javascript:add_bookmark())
- 📤 [导出PDF](javascript:export_pdf())

---

*优化阅读体验 • 专注于中文内容理解*
"""

        return header + toc + content + navigation

    def generate_table_of_contents(self, content) -> Any:
        """生成目录"""
        import re

        # 提取标题
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

        if not headings:
            return ""

        toc = "## 📋 本页目录\n\n"

        for level, title in headings:
            # 跳过已经添加的标题
            if any(keyword in title for keyword in ["📚", "📋", "🧭", "📚"]):
                continue

            indent = "  " * (len(level) - 2)
            if len(level) - 2 < 0:
                continue

            # 创建锚点
            anchor = title.lower().replace(' ', '-').replace('（', '').replace('）', '').replace('：', '').replace('、', '').replace('，', '')
            anchor = ''.join(c for c in anchor if c.isalnum() or c == '-')

            toc += f"{indent}- [{title.strip()}](#{anchor})\n"

        return toc + "\n"

    def optimize_chinese_formatting(self, content) -> Any:
        """优化中文格式"""
        # 改善中文排版
        content = content.replace('（', ' （').replace('）', '） ')
        content = content.replace('：', '： ').replace('；', '；\n')
        content = content.replace('，', '， ').replace('。', '。\n')

        # 优化代码块前后的间距
        content = content.replace('\n```', '\n\n```').replace('```\n', '```\n\n')

        # 优化列表格式
        content = content.replace('\n- ', '\n\n- ')

        return content

    def copy_static_resources(self) -> Any:
        """复制静态资源"""
        print("🖼️ 复制图片和资源文件...")

        resource_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf', '.zip']

        for root, dirs, files in os.walk(self.original_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in resource_extensions):
                    source_file = Path(root) / file
                    rel_path = source_file.relative_to(self.original_dir)
                    target_file = self.optimized_dir / rel_path

                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)

    def create_navigation_system(self) -> Any:
        """创建导航系统"""
        print("🗺️ 创建导航系统...")

        # 生成主导航文件
        nav_content = f"""# 📚 Agentic Design Patterns 导航中心

> **更新时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **总页面数**: 424页
> **包含内容**: 中英文对照 + 完整示例

---

## 🎯 快速导航

### 📖 基础阅读
- [📘 项目介绍](./README.md)
- [📋 目录总览](./table_of_contents.md)
- [🔖 书签收藏](./bookmarks.md)

### 🎯 按章节浏览
"""

        # 扫描并添加所有Markdown文件
        md_files = []
        for root, dirs, files in os.walk(self.original_dir):
            for file in files:
                if file.endswith('.md'):
                    rel_path = Path(root).relative_to(self.original_dir) / file
                    md_files.append(rel_path)

        # 按章节排序
        md_files.sort(key=lambda x: x.name)

        # 添加到导航
        current_section = ""
        for file_path in md_files:
            # 检测章节
            chapter_num = ""
            if file_path.name.startswith(('ch', 'chapter', '0', '1', '2')):
                chapter_num = file_path.name.split('-')[0].replace('ch', '').replace('chapter', '')

            if chapter_num and chapter_num != current_section:
                current_section = chapter_num
                nav_content += f"\n### 📖 第{chapter_num}章\n"

            # 添加文件链接
            display_name = file_path.stem.replace('-', ' ').replace('_', ' ').title()
            nav_content += f"- [{display_name}]({file_path})\n"

        # 添加工具和设置
        nav_content += f"""

## 🔧 阅读工具

- 🔍 **全文搜索**: [搜索页面](./search.html)
- 📊 **统计信息**: [页面统计](./stats.html)
- 🎨 **主题设置**: [外观配置](./settings.html)
- 📤 **导出功能**: [导出页面](./export.html)

## 📚 学习路径

### 🌟 初学者路径 (第1-7章)
1. [提示链](./ch01-prompt-chaining.md) - 任务分解基础
2. [路由](./ch02-routing.md) - 智能决策分发
3. [并行化](./ch03-parallelization.md) - 并发处理
4. [反思](./ch04-reflection.md) - 质量优化
5. [工具使用](./ch05-tool-use.md) - 功能扩展
6. [规划](./ch06-planning.md) - 任务管理
7. [多智能体协作](./ch07-multi-agent-collaboration.md) - 协作架构

### 🚀 进阶路径 (第8-14章)
8. [记忆管理](./ch08-memory-management.md) - 上下文管理
9. [学习适应](./ch09-learning-adaptation.md) - 持续优化
10. [模型上下文协议](./ch10-model-context-protocol.md) - 通信标准
11. [目标设定监控](./ch11-goal-setting-monitoring.md) - 目标管理

### 🏭 生产路径 (第12-21章)
12. [异常处理恢复](./ch12-error-handling-recovery.md) - 稳定性
13. [人机协作](./ch13-human-ai-collaboration.md) - 协作决策
14. [知识检索RAG](./ch14-rag.md) - 知识增强
15. [智能体通信A2A](./ch15-a2a-communication.md) - 通信协议
16. [资源感知优化](./ch16-resource-aware-optimization.md) - 性能优化
17. [推理技术](./ch17-reasoning.md) - 智能推理
18. [护栏安全](./ch18-guardrails-safety.md) - 安全防护
19. [评估监控](./ch19-evaluation-monitoring.md) - 质量评估
20. [优先级排序](./ch20-prioritization.md) - 任务调度
21. [探索发现](./ch21-exploration-discovery.md) - 创新能力

## 💡 使用提示

### 🎯 阅读建议
- 按顺序学习，循序渐进
- 理论与实践结合
- 多做笔记和总结
- 与实际项目结合

### 🔍 搜索技巧
- 使用关键词快速定位
- 按章节号查找内容
- 利用标签分类浏览

### 📖 最佳实践
- 定期复习已学内容
- 参与社区讨论
- 分享学习心得
- 应用到实际项目

---

*最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*页面总数: {len(md_files)}*
*总内容量: 424页*
"""

        # 写入导航文件
        with open(self.optimized_dir / "navigation.md", 'w', encoding='utf-8') as f:
            f.write(nav_content)

        # 创建目录总览文件
        self.create_table_of_contents(md_files)

    def create_table_of_contents(self, md_files) -> Any:
        """创建详细目录"""
        toc_content = f"""# 📋 Agentic Design Patterns 目录总览

> **页数**: 424页
> **章节**: 21个核心模式
> **格式**: 中英文对照
> **特色**: 完整代码示例

---

## 📚 完整章节列表

"""

        # 按类别分组
        chapters = {
            "核心模式": [],
            "高级模式": [],
            "集成模式": [],
            "生产模式": []
        }

        for file_path in md_files:
            chapter_num = ""
            if file_path.name.startswith(('ch', 'chapter', '0', '1', '2')):
                chapter_num = file_path.name.split('-')[0].replace('ch', '').replace('chapter', '')

            # 根据章节号分类
            if chapter_num.isdigit():
                num = int(chapter_num)
                if 1 <= num <= 7:
                    category = "核心模式"
                elif 8 <= num <= 11:
                    category = "高级模式"
                elif 12 <= num <= 14:
                    category = "集成模式"
                elif 15 <= num <= 21:
                    category = "生产模式"
                else:
                    category = "其他"
            else:
                category = "其他"

            display_name = file_path.stem.replace('-', ' ').replace('_', ' ').title()
            chapters[category].append((file_path, display_name))

        # 生成分组目录
        for category, files in chapters.items():
            if files:
                toc_content += f"### {category}\n\n"
                for file_path, display_name in files:
                    toc_content += f"- [{display_name}]({file_path})\n"
                toc_content += "\n"

        # 写入目录文件
        with open(self.optimized_dir / "table_of_contents.md", 'w', encoding='utf-8') as f:
            f.write(toc_content)

    def create_reading_config(self) -> Any:
        """创建阅读配置"""
        config = {
            "theme": {
                "primary_color": "#2c3e50",
                "accent_color": "#3498db",
                "background_color": "#ffffff",
                "text_color": "#2c3e50",
                "code_background": "#f8f9fa"
            },
            "typography": {
                "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
                "font_size": "16px",
                "line_height": 1.8,
                "paragraph_spacing": "1.2em"
            },
            "layout": {
                "max_width": "800px",
                "content_padding": "2rem",
                "sidebar_width": "250px"
            },
            "features": {
                "dark_mode": True,
                "search_enabled": True,
                "bookmarks_enabled": True,
                "export_enabled": True,
                "print_friendly": True
            },
            "chinese_optimization": {
                "punctuation_spacing": True,
                "line_break_optimization": True,
                "character_spacing": True,
                "mixed_language_optimization": True
            }
        }

        with open(self.optimized_dir / "reading_config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def create_reading_interface(self) -> Any:
        """创建阅读界面"""
        # 创建简单的HTML阅读界面
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic Design Patterns - 阅读界面</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Agentic Design Patterns</h1>
            <p>智能体设计模式 - 中英文对照版 (424页)</p>
        </header>

        <nav class="sidebar">
            <h3>🧭 快速导航</h3>
            <ul>
                <li><a href="navigation.md">📖 导航中心</a></li>
                <li><a href="table_of_contents.md">📋 目录总览</a></li>
                <li><a href="README.md">📘 项目介绍</a></li>
            </ul>

            <h3>📚 章节浏览</h3>
            <div id="chapter-list">
                <!-- 动态生成章节列表 -->
            </div>
        </nav>

        <main class="content">
            <div id="reading-area">
                <h2>🎯 欢迎阅读 Agentic Design Patterns</h2>
                <p>请从左侧导航选择要阅读的章节，或使用下面的快速链接：</p>

                <div class="quick-links">
                    <a href="navigation.md" class="link-card">
                        <h3>📖 开始阅读</h3>
                        <p>从导航中心开始系统学习</p>
                    </a>

                    <a href="table_of_contents.md" class="link-card">
                        <h3>📋 查看目录</h3>
                        <p>浏览所有章节和内容</p>
                    </a>
                </div>

                <div class="info-box">
                    <h3>📖 阅读说明</h3>
                    <ul>
                        <li>🎯 本书包含21个核心智能体设计模式</li>
                        <li>📝 提供中英文对照内容</li>
                        <li>💻 包含完整的代码示例</li>
                        <li>🚀 适合各水平开发者学习</li>
                    </ul>
                </div>
            </div>
        </main>
    </div>

    <script src="scripts.js"></script>
</body>
</html>
"""

        # 创建CSS样式
        css_content = """
/* Agentic Design Patterns 阅读界面样式 */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    line-height: 1.8;
    color: #2c3e50;
    background-color: #f8f9fa;
}

.container {
    display: flex;
    min-height: 100vh;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

header p {
    font-size: 1.2rem;
    opacity: 0.9;
}

.sidebar {
    width: 280px;
    background: white;
    padding: 2rem 1.5rem;
    border-right: 1px solid #e1e4e8;
    overflow-y: auto;
    height: calc(100vh - 120px);
}

.sidebar h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
    font-size: 1.1rem;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5rem;
}

.sidebar ul {
    list-style: none;
    margin-bottom: 2rem;
}

.sidebar li {
    margin-bottom: 0.5rem;
}

.sidebar a {
    color: #2c3e50;
    text-decoration: none;
    padding: 0.5rem;
    display: block;
    border-radius: 4px;
    transition: all 0.3s ease;
}

.sidebar a:hover {
    background-color: #f8f9fa;
    color: #3498db;
    transform: translate_x(5px);
}

.content {
    flex: 1;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.reading-area {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.quick-links {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.link-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 1.5rem;
    border-radius: 8px;
    text-decoration: none;
    color: #2c3e50;
    border: 1px solid #dee2e6;
    transition: all 0.3s ease;
}

.link-card:hover {
    transform: translate_y(-5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
}

.link-card h3 {
    margin-bottom: 0.5rem;
    color: #3498db;
}

.info-box {
    background: #e8f4fd;
    border-left: 4px solid #3498db;
    padding: 1.5rem;
    border-radius: 4px;
    margin: 2rem 0;
}

.info-box h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
}

.info-box ul {
    list-style-position: inside;
}

.info-box li {
    margin-bottom: 0.5rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }

    .sidebar {
        width: 100%;
        height: auto;
        border-right: none;
        border-bottom: 1px solid #e1e4e8;
    }

    header h1 {
        font-size: 2rem;
    }

    .content {
        padding: 1rem;
    }
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
    body {
        background-color: #1a1a1a;
        color: #e4e4e4;
    }

    .sidebar,
    .reading-area {
        background: #2d2d2d;
    }

    .link-card {
        background: #3d3d3d;
        border-color: #4d4d4d;
    }
}
"""

        # 创建JavaScript功能
        js_content = """
// Agentic Design Patterns 阅读界面脚本

document.add_event_listener('DOMContentLoaded', function() {
    load_chapter_list();
    setup_event_listeners();
});

function load_chapter_list() {
    const chapter_list = document.get_element_by_id('chapter-list');
    const chapters = [
        { num: 1, title: '提示链 (Prompt Chaining)', file: 'ch01-prompt-chaining.md' },
        { num: 2, title: '路由 (Routing)', file: 'ch02-routing.md' },
        { num: 3, title: '并行化 (Parallelization)', file: 'ch03-parallelization.md' },
        { num: 4, title: '反思 (Reflection)', file: 'ch04-reflection.md' },
        { num: 5, title: '工具使用 (Tool Use)', file: 'ch05-tool-use.md' },
        { num: 6, title: '规划 (Planning)', file: 'ch06-planning.md' },
        { num: 7, title: '多智能体协作 (Multi-Agent)', file: 'ch07-multi-agent-collaboration.md' },
        { num: 8, title: '记忆管理 (Memory Management)', file: 'ch08-memory-management.md' },
        { num: 9, title: '学习适应 (Learning & Adaptation)', file: 'ch09-learning-adaptation.md' },
        { num: 10, title: '模型上下文协议 (MCP)', file: 'ch10-model-context-protocol.md' },
        { num: 11, title: '目标设定监控 (Goal Setting)', file: 'ch11-goal-setting-monitoring.md' },
        { num: 12, title: '异常处理恢复 (Error Handling)', file: 'ch12-error-handling-recovery.md' },
        { num: 13, title: '人机协作 (Human-AI)', file: 'ch13-human-ai-collaboration.md' },
        { num: 14, title: '知识检索 (RAG)', file: 'ch14-rag.md' },
        { num: 15, title: '智能体通信 (A2A)', file: 'ch15-a2a-communication.md' },
        { num: 16, title: '资源感知优化 (Resource Optimization)', file: 'ch16-resource-aware-optimization.md' },
        { num: 17, title: '推理技术 (Reasoning)', file: 'ch17-reasoning.md' },
        { num: 18, title: '护栏安全 (Guardrails)', file: 'ch18-guardrails-safety.md' },
        { num: 19, title: '评估监控 (Evaluation)', file: 'ch19-evaluation-monitoring.md' },
        { num: 20, title: '优先级排序 (Prioritization)', file: 'ch20-prioritization.md' },
        { num: 21, title: '探索发现 (Exploration)', file: 'ch21-exploration-discovery.md' }
    ];

    let html = '';
    chapters.for_each(chapter => {
        html += `<li><a href="${chapter.file}">第${chapter.num}章: ${chapter.title}</a></li>`;
    });

    chapter_list.inner_html = html;
}

function setup_event_listeners() {
    // 添加键盘快捷键
    document.add_event_listener('keydown', function(e) {
        if (e.alt_key) {
            switch(e.key) {
                case 'h': // Alt+H: 返回首页
                    window.location.href = 'index.html';
                    break;
                case 'n': // Alt+N: 打开导航
                    window.location.href = 'navigation.md';
                    break;
                case 's': // Alt+S: 搜索
                    show_search();
                    break;
            }
        }
    });
}

function show_search() {
    const query = prompt('请输入搜索关键词:');
    if (query) {
        // 实现搜索功能
        alert('搜索功能正在开发中...');
    }
}

function toggle_dark_mode() {
    document.body.class_list.toggle('dark-mode');
}

function scroll_to_top() {
    window.scroll_to({ top: 0, behavior: 'smooth' });
}
"""

        # 写入文件
        with open(self.optimized_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(html_content)

        with open(self.optimized_dir / "styles.css", 'w', encoding='utf-8') as f:
            f.write(css_content)

        with open(self.optimized_dir / "scripts.js", 'w', encoding='utf-8') as f:
            f.write(js_content)

        print("✅ 阅读界面创建完成")


def main() -> None:
    """主函数"""
    print("🎨 Agentic Design Patterns 阅读体验优化工具")
    print("=" * 50)

    optimizer = ReadingOptimizer()

    try:
        optimizer.optimize_all_content()
        print("\n🎉 优化完成！")
        print(f"📁 优化后的内容保存在: {optimizer.optimized_dir}")
        print(f"🌐 打开阅读界面: {optimizer.optimized_dir}/index.html")
    except Exception as e:
        print(f"❌ 优化过程中出错: {e}")


if __name__ == "__main__":
    main()