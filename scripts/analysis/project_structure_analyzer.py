#!/usr/bin/env python3
"""
项目目录结构分析与优化规划器
Project Structure Analyzer and Optimization Planner

分析当前项目结构，并根据标准化方案提供逐步整理建议
"""

import argparse
import os
from collections import defaultdict
from pathlib import Path


class ProjectStructureAnalyzer:
    """项目结构分析器"""

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.analysis = {
            'total_dirs': 0,
            'total_size': 0,
            'categories': defaultdict(list),
            'issues': [],
            'recommendations': []
        }

    def analyze(self) -> dict:
        """执行完整分析"""
        print("🔍 开始分析项目结构...")

        # 1. 统计根目录文件夹
        self._count_root_directories()

        # 2. 分类所有目录
        self._categorize_directories()

        # 3. 识别问题
        self._identify_issues()

        # 4. 生成建议
        self._generate_recommendations()

        return self.analysis

    def _count_root_directories(self):
        """统计根目录文件夹数量和大小"""
        dirs = [d for d in self.root.iterdir() if d.is_dir() and not d.name.startswith('.')]
        self.analysis['total_dirs'] = len(dirs)

        total_size = 0
        dir_info = []
        for d in dirs:
            size = self._get_dir_size(d)
            total_size += size
            dir_info.append({
                'name': d.name,
                'size': size,
                'size_mb': f"{size / 1024 / 1024:.1f}M"
            })

        self.analysis['total_size'] = total_size
        self.analysis['directories'] = sorted(dir_info, key=lambda x: x['size'], reverse=True)

    def _get_dir_size(self, directory: Path) -> int:
        """获取目录大小（字节）"""
        try:
            total = 0
            for item in directory.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
            return total
        except (PermissionError, OSError):
            return 0

    def _categorize_directories(self):
        """将目录按功能分类"""
        # 定义目录分类规则
        category_rules = {
            'core_business': ['core', 'xiaonuo', 'xiaona-legal-support'],
            'agents': ['agents', 'agent'],
            'ai_ml': ['models', 'athena_env', 'venv', '.venv_opt'],
            'data': ['data', 'knowledge', 'knowledge_graph', 'memory', 'personal_secure_storage'],
            'config': ['config', 'infrastructure', 'security'],
            'api_services': ['api', 'services', 'apps', 'mcp-servers'],
            'testing': ['tests', 'test_coverage_results'],
            'docs': ['docs', 'reports', 'prompts'],
            'deployment': ['deploy', 'docker', 'production', 'backup', 'backups'],
            'development': ['dev', 'scripts', 'tools', 'utils', 'tasks', 'modules'],
            'external': ['claude-code', 'computer-use-ootb', 'athena-client',
                        'patent_hybrid_retrieval', 'patent-platform', 'Dolphin',
                        'domains', 'projects', 'projects', 'var', 'temp'],
            'other': []
        }

        for d in self.root.iterdir():
            if not d.is_dir() or d.name.startswith('.'):
                continue

            categorized = False
            for category, patterns in category_rules.items():
                if any(p in d.name.lower() for p in patterns):
                    self.analysis['categories'][category].append(d.name)
                    categorized = True
                    break

            if not categorized:
                self.analysis['categories']['other'].append(d.name)

    def _identify_issues(self):
        """识别当前结构的问题"""
        issues = self.analysis['issues']

        # 问题1：根目录文件夹过多
        if self.analysis['total_dirs'] > 20:
            issues.append({
                'severity': 'HIGH',
                'type': 'too_many_root_dirs',
                'description': f'根目录有{self.analysis["total_dirs"]}个文件夹，远超建议的10-15个',
                'impact': '降低导航效率，增加维护成本'
            })

        # 问题2：功能重复/分散
        if 'backup' in self.analysis['categories']['deployment'] and \
           'backups' in self.analysis['categories']['deployment']:
            issues.append({
                'severity': 'MEDIUM',
                'type': 'duplicate_functions',
                'description': '存在backup和backups两个备份目录',
                'impact': '可能导致混淆和数据不一致'
            })

        # 问题3：业务逻辑分散
        business_dirs = (self.analysis['categories'].get('core_business', []) +
                        self.analysis['categories'].get('agents', []))
        if len(business_dirs) > 5:
            issues.append({
                'severity': 'MEDIUM',
                'type': 'scattered_business_logic',
                'description': f'业务逻辑分散在{len(business_dirs)}个目录中',
                'impact': '降低代码可维护性和可理解性'
            })

        # 问题4：外部项目混入
        external_count = len(self.analysis['categories'].get('external', []))
        if external_count > 5:
            issues.append({
                'severity': 'MEDIUM',
                'type': 'external_projects_mixed',
                'description': f'{external_count}个外部/独立项目混在根目录',
                'impact': '污染主项目结构，应移至独立目录'
            })

    def _generate_recommendations(self):
        """生成优化建议"""
        recommendations = self.analysis['recommendations']

        # 建议按标准化方案重组
        recommendations.append({
            'phase': 1,
            'priority': 'HIGH',
            'action': 'create_standard_structure',
            'description': '创建标准化目录结构骨架',
            'commands': [
                'mkdir -p src/{agents/{base,orchestrator,planner,executor,reviewer,shared},workflows,tools}',
                'mkdir -p config/{environments,agents,secrets}',
                'mkdir -p data/{raw,processed,outputs,knowledge}',
                'mkdir -p docs/{architecture,api,guides,diagrams}',
                'mkdir -p tests/{unit,integration,e2e,fixtures}',
                'mkdir -p deploy/{docker,kubernetes,scripts}'
            ]
        })

        # 建议整合业务模块
        recommendations.append({
            'phase': 2,
            'priority': 'HIGH',
            'action': 'consolidate_business_modules',
            'description': '整合核心业务模块到src/目录',
            'mapping': {
                'core/': 'src/agents/',
                'xiaonuo/': 'src/agents/xiaonuo/',
                'xiaona-legal-support/': 'src/agents/legal_support/'
            }
        })

        # 建议迁移外部项目
        recommendations.append({
            'phase': 3,
            'priority': 'MEDIUM',
            'action': 'move_external_projects',
            'description': '将外部/独立项目移至独立目录',
            'target': 'external_projects/',
            'projects': [
                'claude-code/',
                'computer-use-ootb/',
                'athena-client/',
                'patent-platform/',
                'Dolphin/',
                'patent_hybrid_retrieval/'
            ]
        })

        # 建议统一配置管理
        recommendations.append({
            'phase': 4,
            'priority': 'HIGH',
            'action': 'centralize_config',
            'description': '统一配置文件管理',
            'mapping': {
                'infrastructure/': 'config/infrastructure/',
                'security/': 'config/security/'
            }
        })

        # 建议整合数据目录
        recommendations.append({
            'phase': 5,
            'priority': 'MEDIUM',
            'action': 'consolidate_data_dirs',
            'description': '整合数据相关目录',
            'mapping': {
                'knowledge/': 'data/knowledge/',
                'knowledge_graph/': 'data/knowledge_graph/',
                'memory/': 'data/memory/',
                'models/': 'data/models/'
            }
        })


class ProjectOptimizer:
    """项目结构优化器 - 生成迁移脚本"""

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.migration_plan = {
            'phase1_preparation': [],
            'phase2_core_business': [],
            'phase3_external_projects': [],
            'phase4_data_config': [],
            'phase5_cleanup': []
        }

    def generate_migration_plan(self) -> dict:
        """生成完整的迁移计划"""
        # 阶段1：准备工作
        self._phase1_preparation()

        # 阶段2：核心业务迁移
        self._phase2_core_business()

        # 阶段3：外部项目迁移
        self._phase3_external_projects()

        # 阶段4：数据和配置迁移
        self._phase4_data_config()

        # 阶段5：清理工作
        self._phase5_cleanup()

        return self.migration_plan

    def _phase1_preparation(self):
        """阶段1：准备工作"""
        self.migration_plan['phase1_preparation'] = [
            {
                'step': 1,
                'action': 'create_backup',
                'description': '创建项目完整备份',
                'command': 'tar -czf ../athena_backup_$(date +%Y%m%d_%H%M%S).tar.gz .'
            },
            {
                'step': 2,
                'action': 'create_standard_structure',
                'description': '创建标准化目录结构',
                'commands': [
                    'mkdir -p src/agents/{base,orchestrator,planner,executor,shared}',
                    'mkdir -p src/workflows',
                    'mkdir -p src/tools',
                    'mkdir -p config/{environments,agents,secrets,infrastructure,security}',
                    'mkdir -p data/{raw,processed,outputs/{logs,artifacts},knowledge}',
                    'mkdir -p docs/{architecture,api,guides,diagrams,reports}',
                    'mkdir -p tests/{unit/{agents,tools},integration,e2e,fixtures}',
                    'mkdir -p deploy/{docker,kubernetes,scripts}',
                    'mkdir -p external_projects',
                    'mkdir -p archive/{old_configs,old_scripts}'
                ]
            },
            {
                'step': 3,
                'action': 'create_migration_tracking',
                'description': '创建迁移跟踪文件',
                'output': '.migration_tracking.json'
            }
        ]

    def _phase2_core_business(self):
        """阶段2：核心业务迁移"""
        self.migration_plan['phase2_core_business'] = [
            {
                'phase': '2.1',
                'action': 'migrate_core_module',
                'description': '迁移core模块到src/agents/',
                'source': 'core/',
                'target': 'src/agents/core/',
                'notes': '这是核心业务逻辑，需要仔细处理导入路径'
            },
            {
                'phase': '2.2',
                'action': 'migrate_xiaonuo',
                'description': '迁移xiaonuo智能体',
                'source': 'xiaonuo/',
                'target': 'src/agents/xiaonuo/'
            },
            {
                'phase': '2.3',
                'action': 'consolidate_agents',
                'description': '整合智能体相关代码',
                'operations': [
                    {
                        'source': 'agent_collaboration/',
                        'target': 'src/agents/shared/collaboration/'
                    },
                    {
                        'source': 'cognition/',
                        'target': 'src/agents/shared/cognition/'
                    },
                    {
                        'source': 'autonomous_control/',
                        'target': 'src/agents/orchestrator/'
                    }
                ]
            },
            {
                'phase': '2.4',
                'action': 'migrate_tools',
                'description': '迁移和整合工具',
                'operations': [
                    {'source': 'tools/', 'target': 'src/tools/'},
                    {'source': 'utils/', 'target': 'src/utils/'},
                    {'source': 'tasks/', 'target': 'src/tasks/'}
                ]
            }
        ]

    def _phase3_external_projects(self):
        """阶段3：外部项目迁移"""
        self.migration_plan['phase3_external_projects'] = [
            {
                'action': 'move_external_projects',
                'description': '将外部项目移至external_projects/',
                'projects': [
                    {'from': 'claude-code/', 'to': 'external_projects/claude-code/'},
                    {'from': 'computer-use-ootb/', 'to': 'external_projects/computer-use-ootb/'},
                    {'from': 'athena-client/', 'to': 'external_projects/athena-client/'},
                    {'from': 'patent-platform/', 'to': 'external_projects/patent-platform/'},
                    {'from': 'Dolphin/', 'to': 'external_projects/Dolphin/'},
                    {'from': 'patent_hybrid_retrieval/', 'to': 'external_projects/patent_hybrid_retrieval/'},
                    {'from': '人物调查报告/', 'to': 'external_projects/人物调查报告/'}
                ]
            }
        ]

    def _phase4_data_config(self):
        """阶段4：数据和配置迁移"""
        self.migration_plan['phase4_data_config'] = [
            {
                'action': 'consolidate_data_directories',
                'description': '整合数据相关目录',
                'operations': [
                    {'from': 'models/', 'to': 'data/models/', 'note': 'AI模型文件'},
                    {'from': 'knowledge/', 'to': 'data/knowledge/', 'note': '知识库'},
                    {'from': 'knowledge_graph/', 'to': 'data/knowledge_graph/', 'note': '知识图谱'},
                    {'from': 'memory/', 'to': 'data/memory/', 'note': '记忆系统'},
                    {'from': 'personal_secure_storage/', 'to': 'data/secure_storage/', 'note': '安全存储'}
                ]
            },
            {
                'action': 'consolidate_config_directories',
                'description': '整合配置目录',
                'operations': [
                    {'from': 'infrastructure/', 'to': 'config/infrastructure/'},
                    {'from': 'security/', 'to': 'config/security/'}
                ]
            },
            {
                'action': 'consolidate_deployment',
                'description': '整合部署相关',
                'operations': [
                    {'from': 'deploy/', 'to': 'deploy/'},
                    {'from': 'docker/', 'to': 'deploy/docker/'},
                    {'from': 'production/', 'to': 'deploy/production/'},
                    {'from': 'backup/', 'to': 'deploy/backups/'},
                    {'from': 'backups/', 'to': 'deploy/backups/', 'note': '合并两个backup目录'}
                ]
            }
        ]

    def _phase5_cleanup(self):
        """阶段5：清理工作"""
        self.migration_plan['phase5_cleanup'] = [
            {
                'action': 'archive_old_configs',
                'description': '归档旧的配置文件',
                'operations': [
                    {'from': '.benchmarks', 'to': 'archive/benchmarks'},
                    {'from': '.specify', 'to': 'archive/specify'},
                    {'from': '.system', 'to': 'archive/system'}
                ]
            },
            {
                'action': 'cleanup_empty_dirs',
                'description': '清理空目录',
                'command': 'find . -type d -empty -delete'
            },
            {
                'action': 'update_imports',
                'description': '更新所有Python导入路径',
                'script': 'scripts/migration/update_imports.py'
            },
            {
                'action': 'run_tests',
                'description': '运行测试验证迁移',
                'command': 'pytest tests/ -v --tb=short'
            }
        ]

    def generate_migration_script(self, output_file: str = 'migrate_project_structure.sh'):
        """生成可执行的迁移脚本"""
        script_lines = [
            '#!/bin/bash',
            '#',
            '# Athena项目结构迁移脚本',
            '# 生成时间: ' + str(__import__('datetime').datetime.now()),
            '#',
            '# ⚠️  警告: 执行前请确保已备份项目！',
            '#',
            '',
            'set -e  # 遇到错误立即退出',
            '',
            '# 颜色输出',
            'RED="\\033[0;31m"',
            'GREEN="\\033[0;32m"',
            'YELLOW="\\033[1;33m"',
            'NC="\\033[0m" # No Color',
            '',
            'log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }',
            'log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }',
            'log_error() { echo -e "${RED}[ERROR]${NC} $1"; }',
            '',
            '# 确认提示',
            'echo "⚠️  即将开始项目结构迁移"',
            'echo "此操作将移动大量文件和目录"',
            'read -p "是否继续? (yes/no): " confirm',
            'if [ "$confirm" != "yes" ]; then',
            '    echo "操作已取消"',
            '    exit 0',
            'fi',
            ''
        ]

        # 添加各阶段的迁移命令
        for phase_name, steps in self.migration_plan.items():
            script_lines.append(f'\n# ============ {phase_name.upper()} ============\n')

            for step in steps:
                if 'command' in step:
                    script_lines.append(f'# {step.get("description", "")}')
                    script_lines.append(step['command'])
                elif 'commands' in step:
                    script_lines.append(f'# {step.get("description", "")}')
                    script_lines.extend(step['commands'])
                elif 'operations' in step:
                    script_lines.append(f'# {step.get("description", "")}')
                    for op in step['operations']:
                        if isinstance(op, dict):
                            src = op.get('from', op.get('source', ''))
                            tgt = op.get('to', op.get('target', ''))
                            if src and tgt:
                                script_lines.append(f'log_info "移动 {src} -> {tgt}"')
                                script_lines.append(f'mv {src} {tgt} 2>/dev/null || log_warn "{src} 不存在或移动失败"')

        script_lines.extend([
            '',
            'log_info "✅ 迁移完成！"',
            'log_info "请运行测试验证: pytest tests/ -v"',
            ''
        ])

        script_content = '\n'.join(script_lines)
        script_path = self.root / output_file

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)
        return script_path


def print_analysis_report(analysis: dict):
    """打印分析报告"""
    print("\n" + "="*80)
    print("📊 Athena项目目录结构分析报告".center(80))
    print("="*80 + "\n")

    # 总体统计
    print(f"📁 根目录文件夹总数: {analysis['total_dirs']}")
    print(f"💾 总大小: {analysis['total_size'] / 1024 / 1024 / 1024:.2f} GB")
    print()

    # 目录分类
    print("📂 目录分类统计:")
    print("-" * 40)
    for category, dirs in analysis['categories'].items():
        if dirs:
            print(f"  {category:20s}: {len(dirs):2d} 个目录")
            for d in dirs[:5]:  # 只显示前5个
                print(f"    - {d}")
            if len(dirs) > 5:
                print(f"    ... 还有 {len(dirs) - 5} 个")
    print()

    # 问题列表
    if analysis['issues']:
        print("⚠️  识别到的问题:")
        print("-" * 40)
        for i, issue in enumerate(analysis['issues'], 1):
            severity_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(issue['severity'], '⚪')
            print(f"{severity_icon} 问题 {i}: [{issue['severity']}]")
            print(f"   描述: {issue['description']}")
            print(f"   影响: {issue['impact']}")
            print()


def print_recommendations(recommendations: list[dict]):
    """打印优化建议"""
    print("💡 优化建议:")
    print("=" * 80)

    for rec in recommendations:
        phase_icon = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣'}.get(rec.get('phase', 1), '📌')
        priority_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(rec.get('priority', 'LOW'), '⚪')

        print(f"\n{phase_icon} 阶段 {rec.get('phase', '?')}: {rec['description']}")
        print(f"   优先级: {priority_icon} {rec.get('priority', 'UNKNOWN')}")

        if 'commands' in rec:
            print("   执行命令:")
            for cmd in rec['commands']:
                print(f"     $ {cmd}")

        if 'mapping' in rec:
            print("   迁移映射:")
            for src, tgt in rec['mapping'].items():
                print(f"     {src:30s} -> {tgt}")

        if 'projects' in rec:
            print("   涉及项目:")
            for proj in rec['projects']:
                print(f"     - {proj}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Athena项目目录结构分析与优化工具'
    )
    parser.add_argument(
        'project_root',
        nargs='?',
        default=os.getcwd(),
        help='项目根目录路径（默认为当前目录）'
    )
    parser.add_argument(
        '--generate-script',
        action='store_true',
        help='生成迁移脚本'
    )
    parser.add_argument(
        '--output',
        default='migrate_project_structure.sh',
        help='迁移脚本输出文件名'
    )

    args = parser.parse_args()

    # 执行分析
    analyzer = ProjectStructureAnalyzer(args.project_root)
    analysis = analyzer.analyze()

    # 打印报告
    print_analysis_report(analysis)
    print_recommendations(analysis['recommendations'])

    # 生成迁移脚本
    if args.generate_script:
        print("\n🔧 生成迁移脚本...")
        optimizer = ProjectOptimizer(args.project_root)
        optimizer.generate_migration_plan()
        script_path = optimizer.generate_migration_script(args.output)
        print(f"✅ 迁移脚本已生成: {script_path}")
        print(f"   执行前请仔细检查: bash {script_path}")


if __name__ == '__main__':
    main()
