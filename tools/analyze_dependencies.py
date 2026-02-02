#!/usr/bin/env python3
"""
依赖关系分析工具
检测Python模块之间的循环依赖
"""

import ast
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """依赖关系分析器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies: Dict[str, Set[str]] = {}
        self.circular_deps: Set[Tuple[str, str]] = set()
        
    def is_python_file(self, file_path: Path) -> bool:
        """检查是否为Python文件"""
        return file_path.suffix == '.py'
    
    def get_module_name(self, file_path: Path) -> str:
        """获取模块名"""
        # 移除项目根目录前缀
        relative_path = file_path.relative_to(self.project_root)
        # 移除.py后缀
        module_path = str(relative_path.with_suffix(''))
        # 将路径转换为模块名
        return module_path.replace(os.sep, '.')
    
    def extract_imports(self, file_path: Path) -> Set[str]:
        """提取文件中的导入语句"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            logger.info(f"解析文件失败 {file_path}: {e}")
            
        return imports
    
    def filter_project_imports(self, imports: Set[str], module_name: str) -> Set[str]:
        """过滤出项目内部的导入"""
        project_imports = set()
        
        # 项目根模块名（从项目根目录名获取）
        project_root_name = self.project_root.name
        
        for imp in imports:
            # 检查是否是项目内的模块
            if (imp.startswith('core.') or 
                imp.startswith('services.') or 
                imp.startswith('tools.') or
                imp.startswith('utils.') or
                imp.startswith(project_root_name + '.')):
                project_imports.add(imp)
                
        return project_imports
    
    def analyze_file(self, file_path: Path):
        """分析单个Python文件"""
        if not self.is_python_file(file_path):
            return
            
        module_name = self.get_module_name(file_path)
        imports = self.extract_imports(file_path)
        project_imports = self.filter_project_imports(imports, module_name)
        
        self.dependencies[module_name] = project_imports
    
    def find_circular_dependencies(self):
        """查找循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: list):
            if node in rec_stack:
                # 找到循环，提取循环路径
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                for i in range(len(cycle) - 1):
                    self.circular_deps.add((cycle[i], cycle[i + 1]))
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            
            # 访问依赖
            for dep in self.dependencies.get(node, []):
                if dep in self.dependencies:  # 只分析项目内模块
                    dfs(dep, path + [node])
            
            rec_stack.remove(node)
        
        # 对每个模块执行DFS
        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])
    
    def generate_report(self) -> Dict:
        """生成分析报告"""
        # 统计信息
        total_modules = len(self.dependencies)
        total_dependencies = sum(len(deps) for deps in self.dependencies.values())
        
        # 找出依赖最多的模块
        most_depended = {}
        for module, deps in self.dependencies.items():
            for dep in deps:
                if dep in most_depended:
                    most_depended[dep] += 1
                else:
                    most_depended[dep] = 1
        
        # 排序
        top_modules = sorted(most_depended.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report = {
            'summary': {
                'total_modules': total_modules,
                'total_dependencies': total_dependencies,
                'circular_dependencies': len(self.circular_deps),
                'status': '发现问题' if self.circular_deps else '正常'
            },
            'circular_dependencies': list(self.circular_deps),
            'most_depended_modules': top_modules,
            'dependencies': {k: list(v) for k, v in self.dependencies.items() if v}
        }
        
        return report
    
    def analyze(self):
        """执行分析"""
        logger.info('开始分析Python模块依赖...')
        
        # 遍历所有Python文件
        for root, dirs, files in os.walk(self.project_root):
            # 跳过特定目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                file_path = Path(root) / file
                self.analyze_file(file_path)
        
        logger.info(f"已分析 {len(self.dependencies)} 个Python模块")
        
        # 查找循环依赖
        logger.info('检查循环依赖...')
        self.find_circular_dependencies()
        
        if self.circular_deps:
            logger.info(f"发现 {len(self.circular_deps)} 个循环依赖!")
            for dep in self.circular_deps:
                logger.info(f"  {dep[0]} -> {dep[1]}")
        else:
            logger.info('未发现循环依赖')
        
        return self.generate_report()

def main():
    """主函数"""
    project_root = '/Users/xujian/Athena工作平台'
    
    # 创建分析器
    analyzer = DependencyAnalyzer(project_root)
    
    # 执行分析
    report = analyzer.analyze()
    
    # 保存报告
    report_path = os.path.join(project_root, 'reports', 'dependency_analysis_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n分析报告已保存到: {report_path}")
    
    # 打印摘要
    logger.info("\n=== 依赖分析摘要 ===")
    logger.info(f"总模块数: {report['summary']['total_modules']}")
    logger.info(f"总依赖数: {report['summary']['total_dependencies']}")
    logger.info(f"循环依赖: {report['summary']['circular_dependencies']}")
    logger.info(f"状态: {report['summary']['status']}")
    
    if report['circular_dependencies']:
        logger.info("\n循环依赖详情:")
        for dep in report['circular_dependencies']:
            logger.info(f"  {dep[0]} 依赖 {dep[1]}")

if __name__ == '__main__':
    main()