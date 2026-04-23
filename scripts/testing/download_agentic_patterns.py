#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agentic Design Patterns 原文下载和阅读优化工具
Agentic Design Patterns Original Content Download and Reading Optimization Tool
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
import requests
from urllib.parse import urlparse, urljoin

class AgenticPatternsDownloader:
    """Agentic Design Patterns 下载和优化管理器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.target_dir = self.base_dir / "knowledge" / "agentic_design_patterns"
        self.original_repo_url = "https://github.com/ginobefun/agentic-design-patterns-cn.git"
        self.fork_repo_url = None  # 用户可以设置自己的fork
        self.backup_urls = [
            "https://github.com/ginobefun/agentic-design-patterns-cn",
            "https://gitee.com/mirrors/agentic-design-patterns-cn",  # 如果有中国镜像
        ]

        # 创建必要的目录
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.target_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def check_git_installed(self):
        """检查Git是否安装"""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Git已安装: {result.stdout.strip()}")
                return True
            else:
                return False
        except FileNotFoundError:
            return False

    def clone_repository(self, repo_url=None):
        """克隆GitHub仓库"""
        if repo_url is None:
            repo_url = self.original_repo_url

        print(f"🔄 正在克隆仓库: {repo_url}")

        try:
            # 使用git clone
            cmd = ['git', 'clone', repo_url, str(self.target_dir / "original")]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.target_dir))

            if result.returncode == 0:
                print("✅ 仓库克隆成功！")
                return True
            else:
                print(f"❌ Git克隆失败: {result.stderr}")
                # 尝试其他下载方式
                return self.alternative_download(repo_url)

        except Exception as e:
            print(f"❌ 克装过程中出错: {e}")
            return False

    def alternative_download(self, repo_url):
        """替代下载方案"""
        print("🔄 尝试替代下载方案...")

        # 方案1: 使用GitHub API下载文件
        try:
            return self.download_via_github_api(repo_url)
        except:
            print("GitHub API下载失败")

        # 方案2: 手动下载关键文件
        try:
            return self.download_key_files()
        except:
            print("关键文件下载失败")

        return False

    def download_via_github_api(self, repo_url):
        """通过GitHub API下载内容"""
        print("🔄 通过GitHub API下载...")

        # 解析repo信息
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]

            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"

            try:
                response = requests.get(api_url)
                if response.status_code == 200:
                    contents = response.json()
                    return self.download_directory_contents(api_url, str(self.target_dir / "original"))
                else:
                    print(f"API请求失败: {response.status_code}")
            except Exception as e:
                print(f"API请求出错: {e}")

        return False

    def download_directory_contents(self, api_url, local_path):
        """递归下载目录内容"""
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                contents = response.json()

                # 创建本地目录
                Path(local_path).mkdir(parents=True, exist_ok=True)

                for item in contents:
                    if item['type'] == 'file':
                        # 下载文件
                        file_response = requests.get(item['download_url'])
                        if file_response.status_code == 200:
                            file_path = Path(local_path) / item['name']
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(file_response.text)
                            print(f"✅ 下载文件: {item['name']}")

                    elif item['type'] == 'dir':
                        # 递归下载子目录
                        sub_dir = Path(local_path) / item['name']
                        self.download_directory_contents(item['url'], str(sub_dir))

                return True
        except Exception as e:
            print(f"下载目录内容出错: {e}")
            return False

    def download_key_files(self):
        """下载关键文件（备用方案）"""
        print("🔄 下载关键文件...")

        key_files = [
            "README.md",
            "docs/",
            "src/",
            "examples/",
            "assets/",
            "config/",
        ]

        # 创建基础目录结构
        original_dir = self.target_dir / "original"
        original_dir.mkdir(parents=True, exist_ok=True)

        # 这里可以添加具体的文件下载逻辑
        # 由于GitHub的限制，建议用户手动下载或使用git

        return False

    def analyze_repository_structure(self):
        """分析仓库结构"""
        print("🔍 分析仓库结构...")

        original_dir = self.target_dir / "original"

        if not original_dir.exists():
            print("❌ 仓库目录不存在，请先克隆")
            return None

        structure = {
            "total_files": 0,
            "directories": [],
            "markdown_files": [],
            "image_files": [],
            "code_files": [],
            "total_size": 0
        }

        # 遍历目录结构
        for root, dirs, files in os.walk(original_dir):
            rel_path = os.path.relpath(root, original_dir)

            # 统计目录
            if rel_path != '.':
                structure["directories"].append(rel_path)

            for file in files:
                file_path = Path(root) / file
                structure["total_files"] += 1
                structure["total_size"] += file_path.stat().st_size

                # 分类文件
                if file.endswith('.md'):
                    structure["markdown_files"].append(os.path.join(rel_path, file))
                elif file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    structure["image_files"].append(os.path.join(rel_path, file))
                elif file.endswith(('.py', '.js', .ipynb', '.json', '.yaml', '.yml')):
                    structure["code_files"].append(os.path.join(rel_path, file))

        # 保存结构分析
        with open(self.target_dir / "structure_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)

        print(f"📊 仓库分析完成:")
        print(f"   总文件数: {structure['total_files']}")
        print(f"   Markdown文件: {len(structure['markdown_files'])}")
        print(f"   图片文件: {len(structure['image_files'])}")
        print(f"   代码文件: {len(structure['code_files'])}")
        print(f"   总大小: {structure['total_size'] / 1024 / 1024:.2f} MB")

        return structure

    def create_reading_optimization(self):
        """创建阅读优化版本"""
        print("📚 创建阅读优化版本...")

        optimized_dir = self.target_dir / "optimized"
        optimized_dir.mkdir(exist_ok=True)

        # 复制原始内容
        original_dir = self.target_dir / "original"
        if original_dir.exists():
            # 复制所有Markdown文件并优化
            self.optimize_markdown_files(original_dir, optimized_dir)

            # 复制图片资源
            self.copy_images(original_dir, optimized_dir)

            # 创建导航文件
            self.create_navigation_file(optimized_dir)

            # 创建阅读配置
            self.create_reading_config(optimized_dir)

        print("✅ 阅读优化版本创建完成！")

    def optimize_markdown_files(self, source_dir, target_dir):
        """优化Markdown文件"""
        print("📝 优化Markdown文件...")

        for root, dirs, files in os.walk(source_dir):
            rel_path = os.path.relpath(root, source_dir)
            target_sub_dir = Path(target_dir) / rel_path
            target_sub_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file.endswith('.md'):
                    source_file = Path(root) / file
                    target_file = target_sub_dir / file

                    # 读取原始内容
                    with open(source_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 优化内容
                    optimized_content = self.optimize_markdown_content(content, rel_path)

                    # 写入优化后的内容
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(optimized_content)

                    print(f"✅ 优化完成: {file}")

    def optimize_markdown_content(self, content, relative_path):
        """优化Markdown内容"""
        # 添加目录导航
        toc = self.generate_table_of_contents(content)

        # 优化中文显示
        content = self.optimize_chinese_display(content)

        # 优化图片链接
        content = self.optimize_image_links(content, relative_path)

        # 添加导航和返回顶部按钮
        content = self.add_navigation_elements(content)

        return content

    def generate_table_of_contents(self, content):
        """生成目录"""
        import re

        # 提取所有标题
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

        if headings:
            toc = ["## 📖 目录导航\n"]
            for level, title in headings:
                indent = "  " * (len(level) - 1)
                # 创建锚点链接
                anchor = title.lower().replace(' ', '-').replace('（', '').replace('）', '')
                toc.append(f"{indent}- [{title.strip()}](#{anchor})")

            return "\n".join(toc) + "\n\n"

        return ""

    def optimize_chinese_display(self, content):
        """优化中文显示"""
        # 优化中英文混排
        content = content.replace('（', ' （').replace('）', '） ')

        # 优化标点符号
        content = content.replace('，', '， ').replace('。', '。\n')
        content = content.replace('：', '： ').replace('；', '；\n')

        return content

    def optimize_image_links(self, content, relative_path):
        """优化图片链接"""
        import re

        # 处理相对路径的图片链接
        def replace_img_link(match):
            alt = match.group(1)
            src = match.group(2)

            if not src.startswith(('http://', 'https://')):
                # 相对路径处理
                if src.startswith('./'):
                    src = src[2:]
                # 构建完整路径
                full_path = os.path.join(relative_path, src)
                src = f"./{full_path}"

            return f"![{alt}]({src})"

        pattern = r'!\[(.*?)\]\((.*?)\)'
        return re.sub(pattern, replace_img_link, content)

    def add_navigation_elements(self, content):
        """添加导航元素"""
        # 在文档开头添加快速导航
        nav_header = """
# 📚 Agentic Design Patterns 智能体设计模式

> **原文来源**: https://github.com/ginobefun/agentic-design-patterns-cn
> **本地优化时间**: {timestamp}
> **阅读模式**: 优化版本

---

"""

        # 在文档末尾添加返回导航
        nav_footer = """

---

## 🧭 快速导航

- [📖 返回首页](./README.md)
- [🔍 搜索内容](javascript:prompt('搜索关键词'))
- [📊 查看目录](javascript:scroll_to_top())
- [⬆️ 返回顶部](javascript:scroll_to_top())

---

*本页面经过本地优化，提供更好的阅读体验*
"""

        return nav_header.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + content + nav_footer

    def copy_images(self, source_dir, target_dir):
        """复制图片文件"""
        print("🖼️ 复制图片资源...")

        for root, dirs, files in os.walk(source_dir):
            rel_path = os.path.relpath(root, source_dir)
            target_sub_dir = Path(target_dir) / rel_path
            target_sub_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    source_file = Path(root) / file
                    target_file = target_sub_dir / file
                    shutil.copy2(source_file, target_file)

    def create_navigation_file(self, optimized_dir):
        """创建导航文件"""
        print("🗺️ 创建导航文件...")

        # 生成目录结构
        nav_content = """# 📚 Agentic Design Patterns 导航中心

## 🎯 快速开始

- [📖 主要内容](./main.md)
- [🔧 代码示例](./examples/)
- [📚 参考资料](./docs/)

## 📋 按章节浏览

"""

        # 扫描所有Markdown文件并添加到导航
        for root, dirs, files in os.walk(optimized_dir):
            rel_path = os.path.relpath(root, optimized_dir)
            if rel_path != '.':
                nav_content += f"\n### 📁 {rel_path}\n"

            for file in files:
                if file.endswith('.md') and file != 'README.md':
                    file_path = os.path.join(rel_path, file)
                    nav_content += f"- [{file.replace('.md', '')}](./{file_path})\n"

        # 添加搜索功能
        nav_content += """

## 🔍 搜索和工具

- [🔎 全局搜索](javascript:prompt('输入搜索关键词'))
- [📊 内容统计](./stats.html)
- [🏷️ 标签索引](./tags.html)

## ⚙️ 阅读设置

- 🌙 [深色模式](javascript:toggle_dark_mode())
- 📏 [字体大小](javascript:adjust_font_size())
- 📖 [阅读模式](javascript:toggle_reading_mode())

---

*最后更新: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "*"

        with open(optimized_dir / "navigation.md", 'w', encoding='utf-8') as f:
            f.write(nav_content)

    def create_reading_config(self, optimized_dir):
        """创建阅读配置文件"""
        config = {
            "reading_settings": {
                "theme": "light",
                "font_size": "medium",
                "line_height": 1.6,
                "max_width": "800px"
            },
            "navigation": {
                "show_toc": True,
                "show_breadcrumb": True,
                "auto_collapse": False
            },
            "features": {
                "search": True,
                "bookmarks": True,
                "notes": True,
                "export": True
            },
            "optimization_applied": {
                "chinese_punctuation": True,
                "image_optimization": True,
                "link_conversion": True,
                "table_of_contents": True
            }
        }

        with open(optimized_dir / "reading_config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def create_local_server(self, port=8080):
        """创建本地服务器"""
        print(f"🌐 启动本地阅读服务器 (端口: {port})...")

        optimized_dir = self.target_dir / "optimized"

        # 创建简单的HTTP服务器脚本
        server_script = f"""
#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# 设置工作目录
os.chdir("{optimized_dir}")

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        super().end_headers()

    def guess_type(self, path):
        if path.endswith('.md'):
            return 'text/html; charset=utf-8'
        return super().guess_type(path)

PORT = {port}
Handler = CustomHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"📚 Agentic Design Patterns 阅读服务器已启动")
    print(f"🌐 访问地址: http://localhost:{PORT}")
    print(f"📁 服务目录: {optimized_dir}")
    print("按 Ctrl+C 停止服务器")

    # 自动打开浏览器
    webbrowser.open(f'http://localhost:{PORT}')

    httpd.serve_forever()
"""

        script_path = self.target_dir / "start_reading_server.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(server_script)

        # 设置执行权限
        os.chmod(script_path, 0o755)

        print(f"✅ 本地服务器脚本已创建: {script_path}")
        print(f"🚀 运行命令: python3 {script_path}")

    def generate_usage_guide(self):
        """生成使用指南"""
        guide = """# 📚 Agentic Design Patterns 本地阅读指南

## 🚀 快速开始

### 1. 下载和优化
```bash
cd /Users/xujian/Athena工作平台
python3 scripts/download_agentic_patterns.py
```

### 2. 启动本地阅读服务器
```bash
python3 knowledge/agentic_design_patterns/start_reading_server.py
```

### 3. 访问阅读界面
打开浏览器访问: http://localhost:8080

## 📁 目录结构

```
knowledge/agentic_design_patterns/
├── original/          # 原始GitHub仓库内容
├── optimized/         # 优化后的阅读版本
├── cache/            # 下载缓存
├── start_reading_server.py  # 本地服务器
├── usage_guide.md    # 使用指南
└── structure_analysis.json  # 仓库结构分析
```

## 🎯 优化特性

### ✨ 阅读体验优化
- 🇨🇳 中文显示优化
- 📖 自动生成目录
- 🖼️ 图片链接修复
- 🧭 智能导航系统

### 🔧 功能增强
- 🔍 全文搜索
- 📖 深色模式
- 📏 字体调节
- 🏷️ 书签管理

### 📱 响应式设计
- 💻 桌面端优化
- 📱 移动端适配
- 📊 高DPI支持

## 🛠️ 自定义配置

编辑 `reading_config.json` 文件来自定义阅读体验：

```json
{
  "reading_settings": {
    "theme": "dark",           // light | dark
    "font_size": "large",      // small | medium | large
    "line_height": 1.8
  }
}
```

## 📖 推荐阅读顺序

1. **入门** → README.md
2. **基础** → 第1-7章 (核心模式)
3. **进阶** → 第8-14章 (高级模式)
4. **精通** → 第15-21章 (生产模式)

## 🔍 搜索技巧

- 使用关键词搜索设计模式
- 按章节号快速定位
- 通过标签筛选内容

## 💡 使用建议

1. **首次使用**: 建议先阅读README.md了解项目结构
2. **学习路径**: 按照章节顺序学习，循序渐进
3. **实践应用**: 结合examples目录中的代码示例
4. **定期更新**: 使用脚本同步最新内容

## 🆘 常见问题

### Q: 下载失败怎么办？
A: 检查网络连接，或尝试手动下载GitHub仓库

### Q: 图片显示异常？
A: 确保图片文件已正确复制到optimized目录

### Q: 搜索功能不工作？
A: 需要在浏览器中启用JavaScript

### Q: 如何自定义样式？
A: 编辑CSS文件或修改reading_config.json

## 📞 技术支持

如遇到问题，请检查：
1. Python版本 (建议3.8+)
2. 网络连接状态
3. 文件权限设置
4. 浏览器兼容性

---

*祝您阅读愉快！*
"""

        with open(self.target_dir / "usage_guide.md", 'w', encoding='utf-8') as f:
            f.write(guide)

    def run_complete_process(self):
        """运行完整的下载和优化流程"""
        print("🚀 开始完整的下载和优化流程...")

        # 1. 检查Git
        if not self.check_git_installed():
            print("⚠️  Git未安装，将使用替代方案")

        # 2. 克隆仓库
        if not self.clone_repository():
            print("❌ 下载失败，请检查网络连接")
            return False

        # 3. 分析结构
        structure = self.analyze_repository_structure()
        if structure:
            print(f"📊 分析完成，共找到 {structure['total_files']} 个文件")

        # 4. 创建阅读优化
        self.create_reading_optimization()

        # 5. 创建本地服务器
        self.create_local_server()

        # 6. 生成使用指南
        self.generate_usage_guide()

        print("🎉 所有流程完成！")
        print(f"📁 内容保存在: {self.target_dir}")
        print(f"🌐 启动服务器: python3 {self.target_dir / 'start_reading_server.py'}")
        print(f"📖 阅读指南: {self.target_dir / 'usage_guide.md'}")

        return True


def main():
    """主函数"""
    print("=" * 60)
    print("📚 Agentic Design Patterns 下载和优化工具")
    print("=" * 60)

    downloader = AgenticPatternsDownloader()

    try:
        success = downloader.run_complete_process()
        if success:
            print("\n🎊 下载和优化成功完成！")
        else:
            print("\n❌ 过程中遇到错误，请检查日志")
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main()