#!/usr/bin/env python3
"""
Agentic Design Patterns 一键启动阅读体验
One-Click Reading Experience Launcher for Agentic Design Patterns
"""

import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any


def check_content_exists() -> bool:
    """检查内容是否存在"""
    base_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")

    if not base_dir.exists():
        return False, "知识库目录不存在"

    original_dir = base_dir / "original"
    if not original_dir.exists():
        return False, "原始内容目录不存在，请先下载内容"

    # 检查是否有Markdown文件
    md_files = list(original_dir.rglob("*.md"))
    if not md_files:
        return False, "没有找到Markdown文件"

    return True, f"找到 {len(md_files)} 个Markdown文件"

def prepare_optimized_content() -> Any:
    """准备优化内容"""
    Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")
    optimizer_script = Path("/Users/xujian/Athena工作平台/scripts/optimize_reading_experience.py")

    print("🔧 准备优化内容...")

    if optimizer_script.exists():
        try:
            subprocess.run([sys.executable, str(optimizer_script)], check=True)
            print("✅ 内容优化完成")
            return True
        except subprocess.CalledProcessError:
            print("⚠️ 优化脚本执行失败，将使用基础界面")
            return False
    else:
        print("⚠️ 优化脚本不存在，将使用基础界面")
        return False

def create_basic_interface() -> Any:
    """创建基础阅读界面"""
    base_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")
    optimized_dir = base_dir / "optimized"
    optimized_dir.mkdir(exist_ok=True)

    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic Design Patterns - 阅读界面</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
            color: white;
            padding: 3rem;
            text-align: center;
        }

        .header h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.3rem;
            opacity: 0.9;
        }

        .content {
            padding: 3rem;
        }

        .file-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }

        .file-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .file-card:hover {
            transform: translate_y(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-color: #3498db;
        }

        .file-card h3 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        }

        .file-card h3 .icon {
            margin-right: 0.5rem;
        }

        .file-card p {
            color: #6c757d;
            font-size: 0.9rem;
        }

        .info-box {
            background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
            border-left: 4px solid #3498db;
            padding: 2rem;
            border-radius: 8px;
            margin: 2rem 0;
        }

        .info-box h2 {
            color: #2c3e50;
            margin-bottom: 1rem;
        }

        .info-box ul {
            list-style-position: inside;
            color: #495057;
        }

        .info-box li {
            margin-bottom: 0.5rem;
        }

        .button {
            display: inline-block;
            background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 6px;
            text-decoration: none;
            margin: 0.5rem;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 1rem;
        }

        .button:hover {
            transform: translate_y(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .stat-card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 0.5rem;
        }

        .stat-label {
            color: #6c757d;
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }

            .header {
                padding: 2rem;
            }

            .header h1 {
                font-size: 2rem;
            }

            .content {
                padding: 2rem;
            }

            .file-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Agentic Design Patterns</h1>
            <p>智能体设计模式 - 中英文对照版 (424页)</p>
        </div>

        <div class="content">
            <div class="info-box">
                <h2>🎯 欢迎阅读智能体设计模式</h2>
                <p>本项目是《Agentic Design Patterns》的中文翻译版本，包含21个核心智能体设计模式，配有完整的代码示例和实践指导。</p>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">424</div>
                    <div class="stat-label">总页数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">21</div>
                    <div class="stat-label">核心模式</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">2</div>
                    <div class="stat-label">语言版本</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">100%</div>
                    <div class="stat-label">中英对照</div>
                </div>
            </div>

            <h2>📖 开始阅读</h2>
            <div id="file-list" class="file-grid">
                <!-- 文件列表将通过JavaScript动态生成 -->
            </div>

            <div class="info-box" style="margin-top: 3rem;">
                <h2>💡 使用说明</h2>
                <ul>
                    <li>📖 点击上方卡片开始阅读对应章节</li>
                    <li>🎯 建议按章节顺序学习，从基础到高级</li>
                    <li>💻 每个模式都配有完整的代码示例</li>
                    <li>🔄 支持中英文对照阅读，便于理解</li>
                    <li>📝 建议结合实际项目进行实践</li>
                </ul>
            </div>

            <div style="text-align: center; margin-top: 2rem;">
                <button class="button" onclick="window.open('https://github.com/ginobefun/agentic-design-patterns-cn')">
                    🌐 访问原项目
                </button>
                <button class="button" onclick="show_download_guide()">
                    📥 下载指南
                </button>
            </div>
        </div>
    </div>

    <script>
        // 获取所有Markdown文件
        async function load_file_list() {
            try {
                // 模拟文件列表（实际应用中需要从服务器获取）
                const files = [
                    { name: 'README.md', title: '项目介绍', desc: '了解项目概况和使用方法', icon: '📘' },
                    { name: 'chapters/', title: '章节内容', desc: '21个核心设计模式详解', icon: '📖' },
                    { name: 'examples/', title: '代码示例', desc: '完整的实践代码示例', icon: '💻' },
                    { name: 'docs/', title: '补充文档', desc: '详细的参考资料和说明', icon: '📚' }
                ];

                const file_list = document.get_element_by_id('file-list');
                file_list.inner_html = '';

                files.for_each(file => {
                    const card = document.create_element('div');
                    card.class_name = 'file-card';
                    card.inner_html = `
                        <h3><span class="icon">${file.icon}</span>${file.title}</h3>
                        <p>${file.desc}</p>
                    `;
                    card.onclick = () => open_file(file.name);
                    file_list.append_child(card);
                });

            } catch (error) {
                console.error('加载文件列表失败:', error);
            }
        }

        function open_file(filename) {
            // 这里应该打开对应的文件
            alert(`即将打开: ${filename}\\n\\n请确保文件存在于 original 目录中`);
        }

        function show_download_guide() {
            const guide = `
📥 手动下载指南：

1. 访问GitHub仓库：
   https://github.com/ginobefun/agentic-design-patterns-cn

2. 点击 "Code" → "Download ZIP"

3. 解压到：
   /Users/xujian/Athena工作平台/knowledge/agentic_design_patterns/original/

4. 重新打开此页面
            `;
            alert(guide);
        }

        // 页面加载完成后执行
        document.add_event_listener('DOMContentLoaded', load_file_list);
    </script>
</body>
</html>
"""

    with open(optimized_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("✅ 基础阅读界面创建完成")

def launch_reading_interface() -> Any:
    """启动阅读界面"""
    base_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")
    optimized_dir = base_dir / "optimized"
    index_file = optimized_dir / "index.html"

    if index_file.exists():
        # 打开浏览器
        webbrowser.open(f'file://{index_file.absolute()}')
        return True
    else:
        print("❌ 阅读界面文件不存在")
        return False

def main() -> None:
    """主函数"""
    print("🚀 Agentic Design Patterns 阅读体验启动器")
    print("=" * 50)

    # 检查内容
    exists, message = check_content_exists()
    if not exists:
        print(f"❌ {message}")
        print("\n📥 请先下载内容：")
        print("1. 访问: https://github.com/ginobefun/agentic-design-patterns-cn")
        print("2. 点击 'Code' → 'Download ZIP'")
        print("3. 解压到: /Users/xujian/Athena工作平台/knowledge/agentic_design_patterns/original/")
        print("4. 重新运行此脚本")
        return

    print(f"✅ {message}")

    # 准备优化内容
    if prepare_optimized_content():
        print("✅ 高级阅读界面已准备")
    else:
        print("⚠️ 创建基础阅读界面")
        create_basic_interface()

    # 启动阅读界面
    if launch_reading_interface():
        print("🌐 阅读界面已在浏览器中打开")
        print("\n📁 内容位置:")
        print("   原始内容: /Users/xujian/Athena工作平台/knowledge/agentic_design_patterns/original/")
        print("   优化界面: /Users/xujian/Athena工作平台/knowledge/agentic_design_patterns/optimized/")

        print("\n💡 使用提示:")
        print("   - 建议使用Chrome或Safari浏览器")
        print("   - 支持本地搜索功能")
        print("   - 可以添加书签和笔记")

    else:
        print("❌ 无法启动阅读界面")
        print("请检查文件是否存在，或手动打开:")
        print("file:///Users/xujian/Athena工作平台/knowledge/agentic_design_patterns/optimized/index.html")

if __name__ == "__main__":
    main()
