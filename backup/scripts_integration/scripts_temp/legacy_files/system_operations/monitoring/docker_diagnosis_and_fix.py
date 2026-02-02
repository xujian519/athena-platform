#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker问题诊断和修复工具
Docker Issue Diagnosis and Fix Tool

诊断Docker Desktop崩溃问题，提供修复建议
"""

import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)

class DockerDiagnosisAndFixer:
    """Docker诊断和修复器"""

    def __init__(self):
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.project_root = PROJECT_ROOT
        self.diagnosis_results = {
            'timestamp': datetime.now().isoformat(),
            'docker_status': {},
            'container_status': {},
            'volume_status': {},
            'network_status': {},
            'fixes_applied': [],
            'recommendations': []
        }

    def check_docker_desktop_status(self):
        """检查Docker Desktop状态"""
        logger.info('🔍 检查Docker Desktop状态...')

        # 检查Docker应用是否在运行
        try:
            result = subprocess.run(
                ['ps', '-ax'],
                capture_output=True,
                text=True,
                timeout=10
            )

            docker_running = False
            docker_desktop_running = False

            for line in result.stdout.split('\n'):
                if 'Docker Desktop' in line and '/Applications/Docker Desktop.app' in line:
                    docker_desktop_running = True
                elif 'Docker' in line and 'dockerd' not in line:
                    docker_running = True

            self.diagnosis_results['docker_status']['docker_desktop'] = docker_desktop_running
            self.diagnosis_results['docker_status']['docker_daemon'] = docker_running

            logger.info(f"  Docker Desktop: {'✅ 运行中' if docker_desktop_running else '❌ 未运行'}")
            logger.info(f"  Docker守护进程: {'✅ 运行中' if docker_running else '❌ 未运行'}")

        except Exception as e:
            logger.info(f"  ❌ 检查失败: {str(e)}")
            self.diagnosis_results['docker_status']['check_error'] = str(e)

        # 检查Docker守护进程状态
        try:
            result = subprocess.run(
                ['docker', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.diagnosis_results['docker_status']['docker_cli'] = True
                logger.info(f"  Docker CLI: ✅ 可用")
            else:
                self.diagnosis_results['docker_status']['docker_cli'] = False
                logger.info(f"  Docker CLI: ❌ 不可用")

        except Exception as e:
            logger.info(f"  Docker CLI: ❌ 不可用 ({str(e)})")
            self.diagnosis_results['docker_status']['docker_cli'] = False

        return self.diagnosis_results['docker_status']

    def check_container_status(self):
        """检查容器状态"""
        logger.info('📦 检查容器状态...')

        try:
            result = subprocess.run(
                ['docker', 'ps', '-a'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                containers = []

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            container_id = parts[0]
                            container_image = parts[1]
                            container_status = parts[4] if len(parts) > 4 else 'unknown'
                            containers.append({
                                'id': container_id,
                                'image': container_image,
                                'status': container_status
                            })

                self.diagnosis_results['container_status']['containers'] = containers
                self.diagnosis_status['container_status']['total'] = len(containers)
                self.diagnosis_status['container_status']['running'] = len([c for c in containers if c['status'] == 'Up'])

                logger.info(f"  容器总数: {len(containers)}")
                logger.info(f"  运行中: {len([c for c in containers if c['status'] == 'Up'])}")

                # 检查Athena相关容器
                athena_containers = [c for c in containers if 'athena' in c['image'].lower()]
                if athena_containers:
                    logger.info(f"  Athena相关容器: {len(athena_containers)}")
                    for container in athena_containers:
                        status_icon = '✅' if container['status'] == 'Up' else '❌'
                        logger.info(f"    {status_icon} {container['image']} ({container['status']})")
                else:
                    logger.info('  Athena相关容器: 0')

            else:
                logger.info('  ❌ 无法获取容器列表')
                self.diagnosis_results['container_status']['error'] = result.stderr

        except Exception as e:
            logger.info(f"  ❌ 检查失败: {str(e)}")
            self.diagnosis_results['container_status']['error'] = str(e)

        return self.diagnosis_results['container_status']

    def check_volume_status(self):
        """检查Docker卷状态"""
        logger.info('💾 检查Docker卷状态...')

        try:
            result = subprocess.run(
                ['docker', 'volume', 'ls'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                volumes = []

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            volume_name = parts[1]
                            volume_driver = parts[6] if len(parts) > 6 else 'unknown'
                            volumes.append({
                                'name': volume_name,
                                'driver': volume_driver
                            })

                self.diagnosis_results['volume_status']['volumes'] = volumes
                logger.info(f"  Docker卷总数: {len(volumes)}")

                # 检查Athena相关卷
                athena_volumes = [v for v in volumes if 'athena' in v['name'].lower() or 'tugraph' in v['name'].lower()]
                if athena_volumes:
                    logger.info(f"  Athena相关卷: {len(athena_volumes)}")
                    for volume in athena_volumes:
                        logger.info(f"    📁 {volume['name']} (驱动: {volume['driver']})")

            else:
                logger.info('  ❌ 无法获取卷列表')
                self.diagnosis_results['volume_status']['error'] = result.stderr

        except Exception as e:
            logger.info(f"  ❌ 检查失败: {str(e)}")
            self.diagnosis_results['volume_status']['error'] = str(e)

        return self.diagnosis_results['volume_status']

    def check_network_status(self):
        """检查Docker网络状态"""
        logger.info('🌐 检查Docker网络状态...')

        try:
            result = subprocess.run(
                ['docker', 'network', 'ls'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                networks = []

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            network_name = parts[1]
                            network_driver = parts[3] if len(parts) > 3 else 'unknown'
                            networks.append({
                                'name': network_name,
                                'driver': network_driver
                            })

                self.diagnosis_results['network_status']['networks'] = networks
                logger.info(f"  Docker网络总数: {len(networks)}")

            else:
                logger.info('  ❌ 无法获取网络列表')
                self.diagnosis_results['network_status']['error'] = result.stderr

        except Exception as e:
            logger.info(f"  ❌ 检查失败: {str(e)}")
            self.diagnosis_results['network_status']['error'] = str(e)

        return self.diagnosis_results['network_status']

    def attempt_docker_fixes(self):
        """尝试Docker修复操作"""
        logger.info('🔧 尝试Docker修复操作...')

        fixes_applied = []

        # 1. 尝试重启Docker Desktop
        if not self.diagnosis_results['docker_status'].get('docker_desktop', False):
            logger.info('  📱 尝试重启Docker Desktop...')
            try:
                # 尝试使用AppleScript重启Docker Desktop
                restart_script = '''
                tell application 'Docker Desktop' to quit
                delay 5
                tell application 'Docker Desktop' to activate
                '''

                subprocess.run(['osascript', '-e', restart_script], timeout=30)
                fixes_applied.append('重启Docker Desktop')
                logger.info('    ✅ 已发送重启命令')
                time.sleep(10)  # 等待重启

            except Exception as e:
                logger.info(f"    ❌ 重启失败: {str(e)}")

        # 2. 尝试启动Docker守护进程
        if not self.diagnosis_results['docker_status'].get('docker_daemon', False):
            logger.info('  🛠️ 尝试启动Docker守护进程...')
            try:
                subprocess.run(['open', '-a', '/Applications/Docker Desktop.app'], timeout=10)
                fixes_applied.append('启动Docker Desktop应用')
                logger.info('    ✅ 已尝试启动Docker Desktop')
                time.sleep(15)  # 等待启动

            except Exception as e:
                logger.info(f"    ❌ 启动失败: {str(e)}")

        # 3. 检查并清理Docker资源
        try:
            logger.info('  🧹 清理Docker资源...')
            # 清理未使用的容器
            subprocess.run(['docker', 'container', 'prune', '-f'], timeout=30)
            logger.info('    ✅ 清理未使用的容器')

            # 清理未使用的镜像
            subprocess.run(['docker', 'image', 'prune', '-f'], timeout=30)
            logger.info('    ✅ 清理未使用的镜像')

            # 清理未使用的卷
            subprocess.run(['docker', 'volume', 'prune', '-f'], timeout=30)
            logger.info('    ✅ 清理未使用的卷')

            fixes_applied.append('清理Docker资源')

        except Exception as e:
            logger.info(f"    ⚠️ 清理部分失败: {str(e)}")

        self.diagnosis_results['fixes_applied'] = fixes_applied
        return fixes_applied

    def check_tugraph_data_integrity(self):
        """检查TuGraph数据完整性"""
        logger.info('🔍 检查TuGraph数据完整性...')

        try:
            # 检查统一法律知识图谱数据文件
            kg_file = self.project_root / 'data' / 'unified_legal_knowledge_graph.json'
            if kg_file.exists():
                import json
                with open(kg_file, 'r', encoding='utf-8') as f:
                    kg_data = json.load(f)

                entities = kg_data.get('entities', [])
                relations = kg_data.get('relations', [])

                logger.info(f"  📊 统一知识图谱文件: {kg_file}")
                logger.info(f"    - 实体数量: {len(entities)}")
                logger.info(f"    - 关系数量: {len(relations)}")
                logger.info(f"    - 文件大小: {kg_file.stat().st_size / 1024 / 1024:.2f} MB")

                self.diagnosis_results['tugraph_data'] = {
                    'file_exists': True,
                    'entities_count': len(entities),
                    'relations_count': len(relations),
                    'file_size_mb': round(kg_file.stat().st_size / 1024 / 1024, 2),
                    'metadata': kg_data.get('metadata', {}),
                    'statistics': kg_data.get('statistics', {})
                }
            else:
                logger.info('  ❌ 统一知识图谱文件不存在')
                self.diagnosis_results['tugraph_data']['file_exists'] = False

        except Exception as e:
            logger.info(f"  ❌ 检查失败: {str(e)}")
            self.diagnosis_results['tugraph_data']['error'] = str(e)

        return self.diagnosis_results.get('tugraph_data', {})

    def generate_recommendations(self):
        """生成修复建议"""
        logger.info('💡 生成修复建议...')

        recommendations = []

        # 基于Docker状态的建议
        docker_status = self.diagnosis_results['docker_status']

        if not docker_status.get('docker_desktop', False):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Docker Desktop未运行',
                'solution': [
                    '1. 手动启动Docker Desktop应用',
                    '2. 检查Docker Desktop是否需要更新',
                    '3. 如果崩溃持续，考虑重新安装Docker Desktop'
                ],
                'steps': [
                    '打开Applications文件夹',
                    '双击Docker Desktop应用',
                    '等待启动完成（可能需要几分钟）'
                ]
            })

        if not docker_status.get('docker_daemon', False):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Docker守护进程未运行',
                'solution': [
                    '1. 重启Docker Desktop',
                    '2. 检查系统虚拟化支持',
                    '3. 尝试在终端手动启动dockerd'
                ],
                'steps': [
                    'sudo systemctl restart docker (Linux)',
                    '或在Docker Desktop中点击重启按钮'
                ]
            })

        # 基于容器状态的建议
        container_status = self.diagnosis_results.get('container_status', {})
        if 'containers' in container_status:
            athena_containers = [c for c in container_status['containers'] if 'athena' in c['image'].lower()]
            if not any(c['status'] == 'Up' for c in athena_containers):
                recommendations.append({
                    'priority': 'MEDIUM',
                    'issue': 'Athena相关容器未运行',
                    'solution': [
                        '1. 重启Docker服务',
                        '2. 检查容器日志找出失败原因',
                        '3. 重新创建容器'
                    ],
                    'container_info': athena_containers
                })

        # 数据保护建议
        tugraph_data = self.diagnosis_results.get('tugraph_data', {})
        if tugraph_data.get('file_exists', False):
            recommendations.append({
                'priority': 'LOW',
                'issue': 'TuGraph数据文件不存在',
                'solution': [
                    '1. 检查备份目录',
                    '2. 重新运行知识图谱整合脚本',
                    '3. 从备份恢复数据'
                ]
            })
        else:
            if tugraph_data.get('entities_count', 0) == 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'issue': 'TuGraph数据为空',
                    'solution': [
                        '1. 检查数据整合脚本输出',
                        '2. 重新执行TuGraph导入',
                        '3. 验证Cypher脚本语法'
                    ]
                })

        # 通用建议
        recommendations.extend([
            {
                'priority': 'LOW',
                'issue': '预防措施',
                'solution': [
                    '1. 定期备份重要容器和数据',
                    '2. 监控Docker资源使用情况',
                    '3. 及时更新Docker版本',
                    '4. 设置资源限制避免内存溢出'
                ]
            }
        ])

        self.diagnosis_results['recommendations'] = recommendations
        return recommendations

    def generate_report(self):
        """生成诊断报告"""
        logger.info('📄 生成诊断报告...')

        report_content = f"""# Docker问题诊断报告

**诊断时间**: {self.diagnosis_results['timestamp']}
**诊断工具**: Athena Docker诊断器

---

## 📊 诊断结果概览

### Docker状态
- Docker Desktop: {'✅ 运行中' if self.diagnosis_results['docker_status'].get('docker_desktop') else '❌ 未运行'}
- Docker守护进程: {'✅ 运行中' if self.diagnosis_status.get('docker_daemon') else '❌ 未运行'}
- Docker CLI: {'✅ 可用' if self.diagnosis_results['docker_status'].get('docker_cli') else '❌ 不可用'}

### 容器状态
"""

        container_status = self.diagnosis_results.get('container_status', {})
        if 'containers' in container_status:
            report_content += f"- 容器总数: {len(container_status['containers'])}\n"
            report_content += f"- 运行中容器: {len([c for c in container_status['containers'] if c['status'] == 'Up'])}\n\n"

            athena_containers = [c for c in container_status['containers'] if 'athena' in c['image'].lower()]
            if athena_containers:
                report_content += "### Athena相关容器\n"
                for container in athena_containers:
                    status_icon = '✅' if container['status'] == 'Up' else '❌'
                    report_content += f"- {status_icon} {container['image']} (状态: {container['status']})\n"
                report_content += "\n"

        # TuGraph数据状态
        tugraph_data = self.diagnosis_results.get('tugraph_data', {})
        if tugraph_data:
            report_content += "### TuGraph数据状态\n"
            if tugraph_data.get('file_exists'):
                report_content += f"- ✅ 数据文件存在\n"
                report_content += f"- 实体数量: {tugraph_data.get('entities_count', 0)}\n"
                report_content += f"- 关系数量: {tugraph_data.get('relations_count', 0)}\n"
                report_content += f"- 文件大小: {tugraph_data.get('file_size_mb', 0)} MB\n"
            else:
                report_content += "- ❌ 数据文件不存在\n"
            report_content += "\n"

        # 应用的修复
        report_content += "### 应用的修复\n"
        for fix in self.diagnosis_results.get('fixes_applied', []):
            report_content += f"- ✅ {fix}\n"

        report_content += "\n---\n\n## 💡 修复建议\n\n"

        for i, rec in enumerate(self.diagnosis_results['recommendations'], 1):
            priority_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[rec['priority']]
            report_content += f"{i}. {priority_icon} **{rec['issue']}**\n\n"

            for solution in rec['solution']:
                report_content += f"   - {solution}\n"

            if 'steps' in rec:
                report_content += "\n   **操作步骤:**\n"
                for step in rec['steps']:
                    report_content += f"   - {step}\n"

            if 'container_info' in rec:
                report_content += "\n   **涉及容器:**\n"
                for container in rec['container_info']:
                    report_content += f"   - {container['image']}: {container['status']}\n"

            report_content += "\n"

        report_content += """
---

## 🚀 立即操作建议

### 如果Docker Desktop崩溃
1. 强制退出Docker Desktop
2. 清理Docker缓存: `docker system prune -a`
3. 重启Mac电脑
4. 重新启动Docker Desktop

### 如果容器未运行
1. 检查Docker服务状态: `docker ps -a`
2. 查看容器日志: `docker logs <container_id>`
3. 重启容器: `docker restart <container_id>`

### 如果数据丢失
1. 检查备份目录: `ls -la /Users/xujian/Athena工作平台/data/backup*`
2. 从备份恢复: 运行数据恢复脚本
3. 重新构建: 运行知识图谱构建脚本

---

## 📞 技术支持

如果问题持续存在：
- Docker官方支持: https://docs.docker.com/
- Docker Desktop问题: https://docs.docker.com/desktop/troubleshoot/
- 系统兼容性检查: `docker system info`

---

**报告生成时间**: {datetime.now().isoformat()}
**建议操作顺序**: 按优先级从高到低执行修复建议
"""

        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.project_root / 'reports' / f"docker_diagnosis_report_{timestamp}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"✅ 诊断报告已保存: {report_path}")
        return report_path

    def run_diagnosis(self):
        """运行完整诊断流程"""
        logger.info('🔍 开始Docker问题诊断')
        logger.info(str('='*60))

        try:
            # 1. 检查Docker状态
            self.check_docker_desktop_status()

            # 2. 检查容器状态
            self.check_container_status()

            # 3. 检查卷状态
            self.check_volume_status()

            # 4. 检查网络状态
            self.check_network_status()

            # 5. 检查TuGraph数据完整性
            self.check_tugraph_data_integrity()

            # 6. 生成修复建议
            self.generate_recommendations()

            # 7. 尝试修复操作
            if not self.diagnosis_results['docker_status'].get('docker_desktop', False):
                logger.info("\n🔧 Docker Desktop未运行，尝试修复...")
                self.attempt_docker_fixes()

                # 重新检查状态
                logger.info("\n🔄 重新检查Docker状态...")
                time.sleep(5)
                self.check_docker_desktop_status()

            # 8. 生成报告
            report_path = self.generate_report()

            logger.info(str('='*60))
            logger.info('🎉 Docker诊断完成!')

            # 总结状态
            docker_desktop = self.diagnosis_results['docker_status'].get('docker_desktop', False)
            if docker_desktop:
                logger.info('🟢 Docker Desktop: 正常运行')
            else:
                logger.info('🔴 Docker Desktop: 需要修复')

            logger.info(f"📄 详细报告: {report_path}")

            return True

        except Exception as e:
            logger.info(f"❌ 诊断过程异常: {str(e)}")
            return False

def main():
    """主函数"""
    logger.info('🛠️ Docker问题诊断和修复工具')
    logger.info('诊断Docker Desktop崩溃问题，提供修复建议')
    logger.info(str('='*60))

    # 创建诊断器
    fixer = DockerDiagnosisAndFixer()

    # 运行诊断
    success = fixer.run_diagnosis()

    if success:
        logger.info("\n🎯 诊断完成！")
        logger.info('💡 查看详细报告了解具体问题和修复建议')
    else:
        logger.info("\n❌ 诊断失败")

if __name__ == '__main__':
    main()
