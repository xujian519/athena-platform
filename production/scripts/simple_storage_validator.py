#!/usr/bin/env python3
"""
Athena工作平台存储系统简化验证器
Simple Storage System Validator for Athena Platform
"""

from __future__ import annotations
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

class SimpleStorageValidator:
    """简化存储系统验证器"""

    def __init__(self):
        self.session_id = f"storage_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.validation_results = {}

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"✅ {message}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"ℹ️ {message}")

    def print_warning(self, message: str) -> Any:
        """打印警告消息"""
        print(f"⚠️  {message}")

    def print_error(self, message: str) -> Any:
        """打印错误消息"""
        print(f"❌ {message}")

    def validate_postgresql(self) -> bool:
        """验证PostgreSQL"""
        self.print_info("🔍 验证PostgreSQL数据库...")

        try:
            # 检查PostgreSQL服务状态
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_success("✅ PostgreSQL服务运行正常")

                # 获取版本信息
                result = subprocess.run(['psql', '-V'], capture_output=True, text=True)
                version = result.stdout.strip()
                self.print_info(f"📊 {version}")

                # 尝试连接数据库
                try:
                    result = subprocess.run([
                        'psql', '-h', 'localhost', '-U', 'postgres',
                        '-c', 'SELECT version();', 'athena'
                    ], capture_output=True, text=True, timeout=10)

                    if result.returncode == 0:
                        self.print_success("✅ 数据库连接成功")
                        self.validation_results['postgresql'] = {
                            'status': 'healthy',
                            'details': '连接正常，可执行查询'
                        }
                    else:
                        self.print_warning("⚠️  数据库连接需要配置")
                        self.validation_results['postgresql'] = {
                            'status': 'warning',
                            'details': '服务运行但连接需要配置'
                        }
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    self.print_warning("⚠️  需要数据库认证信息")
                    self.validation_results['postgresql'] = {
                        'status': 'warning',
                        'details': '服务运行但需要认证'
                    }
            else:
                self.print_error("❌ PostgreSQL服务未运行")
                self.validation_results['postgresql'] = {
                    'status': 'error',
                    'details': '服务未运行'
                }
        except Exception as e:
            self.print_error(f"❌ PostgreSQL验证失败: {e}")
            self.validation_results['postgresql'] = {
                'status': 'error',
                'details': str(e)
            }

    def validate_redis(self) -> bool:
        """验证Redis"""
        self.print_info("🔍 验证Redis缓存...")

        try:
            # 检查Redis服务
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            if 'PONG' in result.stdout:
                self.print_success("✅ Redis服务运行正常")

                # 获取Redis信息
                result = subprocess.run(['redis-cli', 'info', 'modules/modules/memory/modules/memory/modules/memory/memory'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'used_memory_human:' in line:
                            memory = line.split(':')[1]
                            self.print_info(f"💾 内存使用: {memory}")
                            break

                # 测试基本操作
                test_key = f"test_{int(time.time())}"
                subprocess.run(['redis-cli', 'set', test_key, 'test_value'], capture_output=True)
                result = subprocess.run(['redis-cli', 'get', test_key], capture_output=True, text=True)
                subprocess.run(['redis-cli', 'del', test_key], capture_output=True)

                if 'test_value' in result.stdout:
                    self.print_success("✅ Redis读写测试通过")
                    self.validation_results['redis'] = {
                        'status': 'healthy',
                        'details': '读写功能正常'
                    }
                else:
                    self.print_warning("⚠️  Redis读写测试失败")
                    self.validation_results['redis'] = {
                        'status': 'warning',
                        'details': '服务运行但读写异常'
                    }
            else:
                self.print_error("❌ Redis服务未响应")
                self.validation_results['redis'] = {
                    'status': 'error',
                    'details': '服务未运行'
                }
        except Exception as e:
            self.print_error(f"❌ Redis验证失败: {e}")
            self.validation_results['redis'] = {
                'status': 'error',
                'details': str(e)
            }

    def validate_elasticsearch(self) -> bool:
        """验证Elasticsearch"""
        self.print_info("🔍 验证Elasticsearch...")

        try:
            import requests

            response = requests.get('http://localhost:9200/_cluster/health', timeout=10)
            if response.status_code == 200:
                health = response.json()
                status = health['status']
                nodes = health['number_of_nodes']

                self.print_success(f"✅ Elasticsearch集群状态: {status}")
                self.print_info(f"📊 节点数量: {nodes}")

                if status in ['green', 'yellow']:
                    self.validation_results['elasticsearch'] = {
                        'status': 'healthy',
                        'details': f'集群状态: {status}, 节点数: {nodes}'
                    }
                else:
                    self.validation_results['elasticsearch'] = {
                        'status': 'warning',
                        'details': f'集群状态: {status}, 需要关注'
                    }
            else:
                self.print_error("❌ Elasticsearch连接失败")
                self.validation_results['elasticsearch'] = {
                    'status': 'error',
                    'details': '连接失败'
                }
        except Exception as e:
            self.print_warning(f"⚠️  Elasticsearch验证跳过: {e}")
            self.validation_results['elasticsearch'] = {
                'status': 'unknown',
                'details': '服务未安装或未运行'
            }

    def validate_qdrant(self) -> bool:
        """验证Qdrant"""
        self.print_info("🔍 验证Qdrant向量数据库...")

        try:
            import requests

            response = requests.get('http://localhost:6333/health', timeout=10)
            if response.status_code == 200:
                self.print_success("✅ Qdrant服务运行正常")

                # 获取集合信息
                response = requests.get('http://localhost:6333/collections', timeout=10)
                if response.status_code == 200:
                    collections = response.json()
                    count = len(collections.get('result', {}).get('collections', []))
                    self.print_info(f"📊 当前集合数量: {count}")

                self.validation_results['qdrant'] = {
                    'status': 'healthy',
                    'details': '向量数据库运行正常'
                }
            else:
                self.print_error("❌ Qdrant服务未响应")
                self.validation_results['qdrant'] = {
                    'status': 'error',
                    'details': '服务未运行'
                }
        except Exception as e:
            self.print_warning(f"⚠️  Qdrant验证跳过: {e}")
            self.validation_results['qdrant'] = {
                'status': 'unknown',
                'details': '服务未安装或未运行'
            }

    def validate_memory_system(self) -> bool:
        """验证四层记忆系统"""
        self.print_info("🔍 验证四层记忆系统...")

        try:
            memory_base = project_root / "core" / "modules/modules/memory/modules/memory/modules/memory/memory"
            layers = ["hot_memories", "warm_memories", "cold_memories", "eternal_memories"]
            total_files = 0
            existing_layers = 0

            for layer in layers:
                layer_path = memory_base / layer
                if layer_path.exists():
                    files = list(layer_path.glob("*.json"))
                    if files:
                        existing_layers += 1
                        total_files += len(files)
                        size_mb = sum(f.stat().st_size for f in files) / 1024 / 1024
                        self.print_success(f"✅ {layer}: {len(files)} 个文件 ({size_mb:.2f}MB)")
                    else:
                        self.print_warning(f"⚠️  {layer}: 目录存在但无文件")
                else:
                    self.print_error(f"❌ {layer}: 目录不存在")

            # 检查记忆网络
            network_file = memory_base / "memory_network.json"
            if network_file.exists():
                self.print_success("✅ 记忆连接网络存在")
            else:
                self.print_warning("⚠️  记忆连接网络未找到")

            health_percent = (existing_layers / len(layers)) * 100
            self.validation_results['memory_system'] = {
                'status': 'healthy' if health_percent >= 75 else 'warning',
                'details': f'{existing_layers}/{len(layers)} 层完整, {total_files} 个记忆文件'
            }

        except Exception as e:
            self.print_error(f"❌ 记忆系统验证失败: {e}")
            self.validation_results['memory_system'] = {
                'status': 'error',
                'details': str(e)
            }

    def validate_file_system(self) -> bool:
        """验证文件系统"""
        self.print_info("🔍 验证文件系统...")

        try:
            production_path = project_root / "production"

            # 检查关键目录
            critical_dirs = ["logs", "config", "dev/scripts", "data"]
            existing_dirs = 0

            for dir_name in critical_dirs:
                dir_path = production_path / dir_name
                if dir_path.exists() and dir_path.is_dir():
                    existing_dirs += 1
                    self.print_success(f"✅ {dir_name} 目录存在")
                else:
                    self.print_warning(f"⚠️  {dir_name} 目录不存在")

            # 检查磁盘空间
            try:
                import psutil
                disk = psutil.disk_usage(str(project_root))
                free_gb = disk.free / 1024 / 1024 / 1024
                total_gb = disk.total / 1024 / 1024 / 1024
                usage_percent = (disk.used / disk.total) * 100

                self.print_info(f"💿 磁盘使用: {usage_percent:.1f}% (剩余 {free_gb:.1f}GB)")

                if usage_percent < 90:
                    self.validation_results['file_system'] = {
                        'status': 'healthy',
                        'details': f'{existing_dirs}/{len(critical_dirs)} 目录完整, 磁盘空间充足'
                    }
                else:
                    self.validation_results['file_system'] = {
                        'status': 'warning',
                        'details': '磁盘空间不足'
                    }
            except ImportError:
                self.print_warning("⚠️  无法检查磁盘空间 (psutil未安装)")
                self.validation_results['file_system'] = {
                    'status': 'warning',
                    'details': f'{existing_dirs}/{len(critical_dirs)} 目录完整'
                }

        except Exception as e:
            self.print_error(f"❌ 文件系统验证失败: {e}")
            self.validation_results['file_system'] = {
                'status': 'error',
                'details': str(e)
            }

    def run_validation(self) -> Any:
        """运行所有验证"""
        print("🌸🐟 Athena工作平台存储系统验证器")
        print("=" * 60)
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        # 运行各项验证
        self.validate_postgresql()
        print("")

        self.validate_redis()
        print("")

        self.validate_elasticsearch()
        print("")

        self.validate_qdrant()
        print("")

        self.validate_memory_system()
        print("")

        self.validate_file_system()

        # 生成报告
        self.generate_report()

    def generate_report(self) -> Any:
        """生成验证报告"""
        print("\n" + "=" * 60)
        print("📊 存储系统验证结果摘要")
        print("=" * 60)

        # 统计结果
        total = len(self.validation_results)
        healthy = sum(1 for r in self.validation_results.values() if r['status'] == 'healthy')
        warning = sum(1 for r in self.validation_results.values() if r['status'] == 'warning')
        error = sum(1 for r in self.validation_results.values() if r['status'] == 'error')
        unknown = sum(1 for r in self.validation_results.values() if r['status'] == 'unknown')

        score = (healthy / total * 100) if total > 0 else 0

        print(f"🎯 总体评分: {score:.1f}%")
        print(f"✅ 健康: {healthy}")
        print(f"⚠️  警告: {warning}")
        print(f"❌ 错误: {error}")
        print(f"❓ 未知: {unknown}")

        print("\n📋 详细结果:")
        for system, result in self.validation_results.items():
            icon = {
                'healthy': '✅',
                'warning': '⚠️ ',
                'error': '❌',
                'unknown': '❓'
            }.get(result['status'], '❓')

            print(f"   {icon} {system}: {result['status']}")
            print(f"      📄 {result['details']}")

        # 保存报告
        report = {
            'validation_time': datetime.now().isoformat(),
            'session_id': self.session_id,
            'overall_score': score,
            'summary': {
                'total': total,
                'healthy': healthy,
                'warning': warning,
                'error': error,
                'unknown': unknown
            },
            'details': self.validation_results
        }

        logs_dir = project_root / "production" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        report_file = logs_dir / f"storage_validation_{self.session_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 报告已保存: {report_file.name}")

        # 最终评估
        if score >= 90:
            self.print_pink("🎉 存储系统验证优秀！完全可用！")
        elif score >= 75:
            self.print_success("👍 存储系统验证良好！基本可用！")
        elif score >= 50:
            self.print_warning("⚠️  存储系统验证一般，需要关注！")
        else:
            self.print_error("❌ 存储系统验证失败，需要修复！")

def main() -> None:
    """主函数"""
    validator = SimpleStorageValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()
