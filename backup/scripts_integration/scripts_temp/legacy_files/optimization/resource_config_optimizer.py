#!/usr/bin/env python3
"""
🚀 资源配置优化器
小诺的智能资源配置系统

功能:
1. 分析系统资源使用情况
2. 优化Qdrant容器配置
3. 调整系统参数
4. 资源使用监控和预警

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx
import psutil
import yaml
from loguru import logger

logger = logging.getLogger(__name__)

# 配置日志
logger.add('resource_config.log', rotation='50 MB', level='INFO')

class ResourceConfigOptimizer:
    """资源配置优化器"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333'):
        self.qdrant_url = qdrant_url
        self.client = httpx.AsyncClient(timeout=30.0)

    def get_system_resources(self) -> Dict:
        """获取系统资源信息"""
        try:
            # CPU信息
            cpu_count = psutil.cpu_count(logical=True)
            cpu_physical = psutil.cpu_count(logical=False)
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存信息
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            # 网络信息
            network = psutil.net_io_counters()

            # Docker相关信息
            docker_info = self._get_docker_info()

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'logical_cores': cpu_count,
                    'physical_cores': cpu_physical,
                    'current_freq_mhz': cpu_freq.current if cpu_freq else 0,
                    'min_freq_mhz': cpu_freq.min if cpu_freq else 0,
                    'max_freq_mhz': cpu_freq.max if cpu_freq else 0,
                    'usage_percent': cpu_percent,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'usage_percent': memory.percent,
                    'swap_total_gb': swap.total / (1024**3),
                    'swap_used_gb': swap.used / (1024**3),
                    'swap_usage_percent': swap.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'usage_percent': (disk.used / disk.total) * 100,
                    'read_mb_s': disk_io.read_bytes / (1024**2) if disk_io else 0,
                    'write_mb_s': disk_io.write_bytes / (1024**2) if disk_io else 0
                },
                'network': {
                    'bytes_sent_mb': network.bytes_sent / (1024**2) if network else 0,
                    'bytes_recv_mb': network.bytes_recv / (1024**2) if network else 0,
                    'packets_sent': network.packets_sent if network else 0,
                    'packets_recv': network.packets_recv if network else 0
                },
                'docker': docker_info
            }

        except Exception as e:
            logger.error(f"获取系统资源信息失败: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _get_docker_info(self) -> Dict:
        """获取Docker相关信息"""
        try:
            # 检查Docker是否运行
            import subprocess

            # 获取Qdrant容器信息
            result = subprocess.run(
                ['docker', 'stats', 'qdrant', '--no-stream', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                import json
                stats = json.loads(result.stdout)
                container_info = stats[0] if stats else {}

                return {
                    'container_running': True,
                    'container_name': 'qdrant',
                    'cpu_percent': float(container_info.get('CPUPerc', '0%').rstrip('%')),
                    'memory_usage_mb': self._parse_memory(container_info.get('MemUsage', '0B')),
                    'memory_limit_mb': self._parse_memory(container_info.get('MemLimit', '0B')),
                    'memory_percent': float(container_info.get('MemPerc', '0%').rstrip('%')),
                    'network_io_mb': self._parse_memory(container_info.get('NetIO', '0B')) / (1024**2),
                    'block_io_mb': self._parse_memory(container_info.get('BlockIO', '0B')) / (1024**2)
                }
            else:
                return {'container_running': False}

        except Exception as e:
            logger.warning(f"获取Docker信息失败: {e}")
            return {'container_running': False, 'error': str(e)}

    def _parse_memory(self, memory_str: str) -> float:
        """解析内存字符串为MB"""
        try:
            memory_str = memory_str.strip()
            if memory_str.endswith('B'):
                value = float(memory_str[:-1])
                if memory_str.endswith('KiB'):
                    return value / 1024
                elif memory_str.endswith('MiB'):
                    return value
                elif memory_str.endswith('GiB'):
                    return value * 1024
                else:
                    return value / (1024**2)  # 假设是字节
            return 0
        except:
            return 0

    async def get_qdrant_performance_metrics(self) -> Dict:
        """获取Qdrant性能指标"""
        try:
            # 健康检查
            health_response = await self.client.get(f"{self.qdrant_url}/health")
            health_data = health_response.json() if health_response.status_code == 200 else {}

            # 集合信息
            collections_response = await self.client.get(f"{self.qdrant_url}/collections")
            collections_data = collections_response.json() if collections_response.status_code == 200 else {}

            # 计算总体指标
            total_vectors = 0
            total_ram_usage_mb = 0
            collection_count = 0

            if collections_data.get('result'):
                for collection in collections_data['result']['collections']:
                    collection_count += 1

                    # 获取详细信息
                    try:
                        detail_response = await self.client.get(
                            f"{self.qdrant_url}/collections/{collection['name']}"
                        )
                        if detail_response.status_code == 200:
                            detail = detail_response.json()['result']
                            total_vectors += detail.get('points_count', 0)

                            # 估算内存使用
                            vector_size = detail['config']['params']['vectors']['size']
                            estimated_ram = detail.get('points_count', 0) * vector_size * 4 / (1024**2)  # 估算
                            total_ram_usage_mb += estimated_ram
                    except:
                        pass

            return {
                'health': health_data,
                'collections': {
                    'total_count': collection_count,
                    'total_vectors': total_vectors,
                    'estimated_ram_usage_mb': round(total_ram_usage_mb, 2)
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取Qdrant性能指标失败: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def analyze_resource_usage(self, system_resources: Dict, qdrant_metrics: Dict) -> Dict:
        """分析资源使用情况"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'recommendations': [],
            'resource_pressure': {
                'cpu': 'low',
                'memory': 'low',
                'disk': 'low'
            },
            'optimization_opportunities': []
        }

        try:
            # CPU分析
            cpu_usage = system_resources['cpu']['usage_percent']
            if cpu_usage > 80:
                analysis['resource_pressure']['cpu'] = 'high'
                analysis['overall_status'] = 'warning'
                analysis['recommendations'].append('CPU使用率过高，考虑增加CPU核心或优化查询')
            elif cpu_usage > 60:
                analysis['resource_pressure']['cpu'] = 'medium'
                analysis['recommendations'].append('CPU使用率中等，监控系统负载')

            # 内存分析
            memory_usage = system_resources['memory']['usage_percent']
            if memory_usage > 85:
                analysis['resource_pressure']['memory'] = 'high'
                analysis['overall_status'] = 'warning'
                analysis['recommendations'].append('内存使用率过高，考虑增加内存或优化缓存')
            elif memory_usage > 70:
                analysis['resource_pressure']['memory'] = 'medium'
                analysis['recommendations'].append('内存使用率较高，监控系统内存使用')

            # Docker容器资源分析
            if system_resources['docker'].get('container_running', False):
                docker_cpu = system_resources['docker']['cpu_percent']
                docker_memory = system_resources['docker']['memory_percent']

                if docker_memory > 80:
                    analysis['recommendations'].append('Qdrant容器内存使用过高，考虑增加容器内存限制')
                    analysis['optimization_opportunities'].append({
                        'type': 'docker_memory',
                        'current_limit': system_resources['docker']['memory_limit_mb'],
                        'suggested_limit': int(system_resources['docker']['memory_limit_mb'] * 1.5),
                        'description': '增加Qdrant容器内存限制'
                    })

            # Qdrant性能分析
            if 'collections' in qdrant_metrics:
                total_vectors = qdrant_metrics['collections']['total_vectors']
                if total_vectors > 100000:
                    analysis['recommendations'].append(f"大规模向量集合({total_vectors}个向量)，建议启用分片")
                    analysis['optimization_opportunities'].append({
                        'type': 'sharding',
                        'vectors': total_vectors,
                        'suggested_shards': max(2, total_vectors // 150000),
                        'description': '实施向量分片以提高性能'
                    })

            # 磁盘空间分析
            disk_usage = system_resources['disk']['usage_percent']
            if disk_usage > 80:
                analysis['resource_pressure']['disk'] = 'high'
                analysis['recommendations'].append('磁盘空间不足，需要清理或扩容')
            elif disk_usage > 70:
                analysis['resource_pressure']['disk'] = 'medium'
                analysis['recommendations'].append('磁盘空间使用率较高，监控系统空间')

        except Exception as e:
            logger.error(f"分析资源使用失败: {e}")
            analysis['error'] = str(e)

        return analysis

    def generate_docker_compose_optimization(self, analysis: Dict) -> Dict:
        """生成Docker Compose优化配置"""
        try:
            # 获取当前系统资源
            system_memory = psutil.virtual_memory().total / (1024**3)  # GB
            system_cores = psutil.cpu_count(logical=True)

            # 基于分析结果计算优化配置
            docker_config = {
                'version': '3.8',
                'services': {
                    'qdrant': {
                        'image': 'qdrant/qdrant:latest',
                        'container_name': 'qdrant_optimized',
                        'ports': ['6333:6333', '6334:6334'],
                        'restart': 'unless-stopped',
                        'environment': {
                            'QDRANT__SERVICE__HTTP_PORT': '6333',
                            'QDRANT__SERVICE__GRPC_PORT': '6334'
                        },
                        'volumes': [
                            './qdrant_storage:/qdrant/storage'
                        ],
                        'deploy': {
                            'resources': {
                                'limits': {
                                    'cpus': str(system_cores * 0.8),  # 使用80%的CPU
                                    'memory': f"{int(system_memory * 0.7)}G"  # 使用70%的内存
                                },
                                'reservations': {
                                    'cpus': str(system_cores * 0.3),  # 预留30%的CPU
                                    'memory': f"{int(system_memory * 0.3)}G"  # 预留30%的内存
                                }
                            }
                        }
                    }
                },
                'volumes': {
                    'qdrant_storage': {}
                },
                'networks': {
                    'qdrant_network': {
                        'driver': 'bridge'
                    }
                }
            }

            # 根据优化建议调整配置
            for opportunity in analysis.get('optimization_opportunities', []):
                if opportunity['type'] == 'docker_memory':
                    suggested_memory = opportunity['suggested_limit']
                    docker_config['services']['qdrant']['deploy']['resources']['limits']['memory'] = f"{suggested_memory}M"

                elif opportunity['type'] == 'cpu_scaling':
                    suggested_cpus = opportunity.get('suggested_cores', system_cores)
                    docker_config['services']['qdrant']['deploy']['resources']['limits']['cpus'] = str(suggested_cpus)

            return docker_config

        except Exception as e:
            logger.error(f"生成Docker Compose配置失败: {e}")
            return {'error': str(e)}

    def generate_qdrant_config_optimization(self, analysis: Dict) -> Dict:
        """生成Qdrant配置优化"""
        try:
            qdrant_config = {
                'storage': {
                    'performance': {
                        'max_search_threads': psutil.cpu_count(logical=True),
                        'max_optimization_threads': max(2, psutil.cpu_count(logical=True) // 2),
                        'update_queue_size': 1000,
                        'optimizers_map_size': 1000
                    },
                    'wal': {
                        'wal_capacity_mb': 64,
                        'wal_segments_ahead': 0
                    }
                },
                'service': {
                    'max_request_size_mb': 32,
                    'timeout_sec': 30
                },
                'cluster': {
                    # 如果启用集群，添加集群配置
                }
            }

            # 根据分析结果调整配置
            if analysis.get('resource_pressure', {}).get('memory') == 'high':
                # 内存压力大，减少缓存
                qdrant_config['storage']['performance']['optimizers_map_size'] = 500
                qdrant_config['storage']['wal']['wal_capacity_mb'] = 32

            if analysis.get('resource_pressure', {}).get('cpu') == 'high':
                # CPU压力大，减少线程数
                qdrant_config['storage']['performance']['max_search_threads'] = max(2, psutil.cpu_count(logical=True) // 2)
                qdrant_config['storage']['performance']['max_optimization_threads'] = 2

            return qdrant_config

        except Exception as e:
            logger.error(f"生成Qdrant配置失败: {e}")
            return {'error': str(e)}

    async def implement_optimizations(self, auto_apply: bool = False) -> Dict:
        """实施资源配置优化"""
        logger.info('🚀 开始资源配置优化分析')

        # 1. 获取系统资源信息
        logger.info('收集系统资源信息...')
        system_resources = self.get_system_resources()

        # 2. 获取Qdrant性能指标
        logger.info('收集Qdrant性能指标...')
        qdrant_metrics = await self.get_qdrant_performance_metrics()

        # 3. 分析资源使用
        logger.info('分析资源使用情况...')
        analysis = self.analyze_resource_usage(system_resources, qdrant_metrics)

        # 4. 生成优化配置
        logger.info('生成优化配置...')
        docker_config = self.generate_docker_compose_optimization(analysis)
        qdrant_config = self.generate_qdrant_config_optimization(analysis)

        results = {
            'optimization_time': datetime.now().isoformat(),
            'system_resources': system_resources,
            'qdrant_metrics': qdrant_metrics,
            'analysis': analysis,
            'docker_compose_config': docker_config,
            'qdrant_config': qdrant_config,
            'applied_changes': [],
            'summary': {
                'overall_status': analysis['overall_status'],
                'recommendations_count': len(analysis['recommendations']),
                'optimization_opportunities_count': len(analysis['optimization_opportunities'])
            }
        }

        # 5. 自动应用优化（如果启用）
        if auto_apply:
            logger.info('自动应用优化配置...')

            # 保存Docker Compose配置
            docker_compose_file = '.runtime/docker-compose.optimized.yml'
            try:
                with open(docker_compose_file, 'w') as f:
                    yaml.dump(docker_config, f, default_flow_style=False)
                results['applied_changes'].append(f"保存优化的Docker Compose配置: {docker_compose_file}")
                logger.info(f"✅ Docker Compose配置已保存: {docker_compose_file}")
            except Exception as e:
                logger.error(f"保存Docker Compose配置失败: {e}")

            # 保存Qdrant配置
            qdrant_config_file = '.runtime/qdrant.optimized.yml'
            try:
                with open(qdrant_config_file, 'w') as f:
                    yaml.dump(qdrant_config, f, default_flow_style=False)
                results['applied_changes'].append(f"保存优化的Qdrant配置: {qdrant_config_file}")
                logger.info(f"✅ Qdrant配置已保存: {qdrant_config_file}")
            except Exception as e:
                logger.error(f"保存Qdrant配置失败: {e}")

        # 6. 保存完整结果
        results_file = '.runtime/resource_optimization_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"资源配置优化分析完成，结果保存到: {results_file}")
        return results

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='资源配置优化器')
    parser.add_argument('--auto-apply', action='store_true',
                       help='自动应用优化配置')
    parser.add_argument('--show-resources', action='store_true',
                       help='显示当前系统资源信息')
    parser.add_argument('--monitor', action='store_true',
                       help='启动资源监控模式')

    args = parser.parse_args()

    optimizer = ResourceConfigOptimizer()

    try:
        if args.show_resources:
            # 显示系统资源信息
            resources = optimizer.get_system_resources()
            qdrant_metrics = await optimizer.get_qdrant_performance_metrics()
            analysis = optimizer.analyze_resource_usage(resources, qdrant_metrics)

            logger.info(f"\n{'='*60}")
            logger.info(f"🖥️ 系统资源信息")
            logger.info(f"{'='*60}")

            # CPU信息
            cpu = resources['cpu']
            logger.info(f"CPU:")
            logger.info(f"  逻辑核心: {cpu['logical_cores']}")
            logger.info(f"  物理核心: {cpu['physical_cores']}")
            logger.info(f"  当前频率: {cpu['current_freq_mhz']:.0f} MHz")
            logger.info(f"  使用率: {cpu['usage_percent']:.1f}%")

            # 内存信息
            memory = resources['memory']
            logger.info(f"\n内存:")
            logger.info(f"  总计: {memory['total_gb']:.1f} GB")
            logger.info(f"  已用: {memory['used_gb']:.1f} GB ({memory['usage_percent']:.1f}%)")
            logger.info(f"  可用: {memory['available_gb']:.1f} GB")

            # Docker信息
            if resources['docker'].get('container_running', False):
                docker = resources['docker']
                logger.info(f"\nQdrant容器:")
                logger.info(f"  CPU使用率: {docker['cpu_percent']:.1f}%")
                logger.info(f"  内存使用: {docker['memory_usage_mb']:.1f} MB / {docker['memory_limit_mb']:.1f} MB ({docker['memory_percent']:.1f}%)")

            # Qdrant指标
            if 'collections' in qdrant_metrics:
                collections = qdrant_metrics['collections']
                logger.info(f"\nQdrant集合:")
                logger.info(f"  集合数量: {collections['total_count']}")
                logger.info(f"  向量总数: {collections['total_vectors']:,}")
                logger.info(f"  估算内存使用: {collections['estimated_ram_usage_mb']:.1f} MB")

            # 分析结果
            logger.info(f"\n📊 资源使用分析:")
            logger.info(f"  整体状态: {analysis['overall_status']}")
            logger.info(f"  CPU压力: {analysis['resource_pressure']['cpu']}")
            logger.info(f"  内存压力: {analysis['resource_pressure']['memory']}")
            logger.info(f"  磁盘压力: {analysis['resource_pressure']['disk']}")

            if analysis['recommendations']:
                logger.info(f"\n💡 优化建议:")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    logger.info(f"  {i}. {rec}")

        elif args.monitor:
            # 启动监控模式
            logger.info('启动资源监控模式...')

            while True:
                resources = optimizer.get_system_resources()
                qdrant_metrics = await optimizer.get_qdrant_performance_metrics()
                analysis = optimizer.analyze_resource_usage(resources, qdrant_metrics)

                logger.info(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 资源监控:")
                logger.info(str(f"CPU: {resources['cpu']['usage_percent']:.1f}% | "
                      f"内存: {resources['memory']['usage_percent']:.1f}% | "
                      f"磁盘: {resources['disk']['usage_percent']:.1f}% | "
                      f"状态: {analysis['overall_status']}"))

                # 检查是否需要告警
                if analysis['overall_status'] != 'healthy':
                    logger.warning(f"资源使用告警: {analysis['overall_status']}")

                await asyncio.sleep(30)  # 30秒监控间隔

        else:
            # 执行完整的优化分析
            results = await optimizer.implement_optimizations(auto_apply=args.auto_apply)

            logger.info(f"\n{'='*60}")
            logger.info(f"🚀 资源配置优化分析结果")
            logger.info(f"{'='*60}")

            summary = results['summary']
            logger.info(f"整体状态: {summary['overall_status']}")
            logger.info(f"优化建议: {summary['recommendations_count']} 项")
            logger.info(f"优化机会: {summary['optimization_opportunities_count']} 项")

            if results['analysis']['recommendations']:
                logger.info(f"\n💡 优化建议:")
                for i, rec in enumerate(results['analysis']['recommendations'], 1):
                    logger.info(f"  {i}. {rec}")

            if results['analysis']['optimization_opportunities']:
                logger.info(f"\n🔧 优化机会:")
                for opp in results['analysis']['optimization_opportunities']:
                    logger.info(f"  - {opp['description']}")

            if args.auto_apply:
                logger.info(f"\n✅ 已应用的变更:")
                for change in results['applied_changes']:
                    logger.info(f"  - {change}")
            else:
                logger.info(f"\n💾 要应用优化配置，请使用 --auto-apply 参数")

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断了资源监控")
    except Exception as e:
        logger.error(f"资源配置优化过程出错: {e}")
    finally:
        await optimizer.close()

if __name__ == '__main__':
    asyncio.run(main())