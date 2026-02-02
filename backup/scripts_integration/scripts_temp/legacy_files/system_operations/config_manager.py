#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台统一配置管理器
Unified Configuration Manager for Athena Work Platform

提供配置文件的统一管理、验证、同步和部署功能

使用方法:
python3 config_manager.py --validate
python3 config_manager.py --sync
python3 config_manager.py --generate --env development
python3 config_manager.py --compare --env1 development --env2 production

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import argparse
import difflib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class ConfigManager:
    """统一配置管理器"""

    def __init__(self):
        self.config_dir = project_root / 'config'
        self.environments_dir = self.config_dir / 'environments'
        self.services_dir = self.config_dir / 'services'
        self.unified_config_file = self.config_dir / 'unified_config.yaml'

        # 确保目录存在
        self.services_dir.mkdir(exist_ok=True)

        # 配置文件模式定义
        self.config_schema = self._load_config_schema()

    def _load_config_schema(self) -> Dict[str, Any]:
        """加载配置文件模式定义"""
        return {
            'environments': {
                'development': {
                    'required': True,
                    'description': '开发环境配置'
                },
                'production': {
                    'required': True,
                    'description': '生产环境配置'
                },
                'staging': {
                    'required': False,
                    'description': '预发布环境配置'
                }
            },
            'services': {
                'required_sections': [
                    'app', 'ports', 'database', 'redis', 'cache',
                    'api', 'monitoring', 'logging', 'security'
                ],
                'optional_sections': [
                    'testing', 'dev_tools', 'performance', 'backup'
                ]
            },
            'validation_rules': {
                'ports': {
                    'min': 1000,
                    'max': 65535,
                    'required_port_names': ['athena_main', 'athena_memory', 'xiaonuo_memory', 'athena_identity', 'memory_integration']
                },
                'database': {
                    'required_fields': ['host', 'port', 'name', 'user', 'password']
                },
                'redis': {
                    'required_fields': ['host', 'port']
                }
            }
        }

    def load_config(self, env: str) -> Dict[str, Any]:
        """加载指定环境的配置"""
        config_file = self.environments_dir / env / 'config.yaml'

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 添加环境信息
            config['_environment'] = env
            config['_config_file'] = str(config_file)
            config['_loaded_at'] = datetime.now().isoformat()

            return config

        except yaml.YAMLError as e:
            raise ValueError(f"YAML格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载配置失败: {e}")

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证配置文件的完整性和正确性"""
        errors = []
        warnings = []

        # 验证必需的配置段
        required_sections = self.config_schema['services']['required_sections']
        for section in required_sections:
            if section not in config:
                errors.append(f"缺少必需的配置段: {section}")

        # 验证端口配置
        if 'ports' in config:
            ports = config['ports']

            # 检查必需端口
            required_port_names = self.config_schema['validation_rules']['ports']['required_port_names']
            for port_name in required_port_names:
                if port_name not in ports:
                    errors.append(f"缺少必需的端口配置: {port_name}")
                else:
                    port_value = ports[port_name]
                    # 处理环境变量格式的端口值
                    if isinstance(port_value, str) and '${' in port_value:
                        # 提取默认端口值，如 "${ATHENA_PORT:8000}" -> 8000
                        try:
                            default_port = int(port_value.split(':')[-1].rstrip('}'))
                            min_port = self.config_schema['validation_rules']['ports']['min']
                            max_port = self.config_schema['validation_rules']['ports']['max']
                            if not (min_port <= default_port <= max_port):
                                errors.append(f"端口 {port_name} 默认值 {default_port} 超出范围 {min_port}-{max_port}")
                        except ValueError:
                            errors.append(f"端口 {port_name} 配置格式错误: {port_value}")
                    elif isinstance(port_value, int):
                        min_port = self.config_schema['validation_rules']['ports']['min']
                        max_port = self.config_schema['validation_rules']['ports']['max']
                        if not (min_port <= port_value <= max_port):
                            errors.append(f"端口 {port_name} 值 {port_value} 超出范围 {min_port}-{max_port}")

        # 验证数据库配置
        if 'database' in config:
            db_config = config['database']
            required_fields = self.config_schema['validation_rules']['database']['required_fields']
            for field in required_fields:
                if field not in db_config:
                    errors.append(f"数据库配置缺少必需字段: {field}")

        # 验证Redis配置
        if 'redis' in config:
            redis_config = config['redis']
            required_fields = self.config_schema['validation_rules']['redis']['required_fields']
            for field in required_fields:
                if field not in redis_config:
                    errors.append(f"Redis配置缺少必需字段: {field}")

        # 验证日志级别
        if 'logging' in config and 'level' in config['logging']:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            level = config['logging']['level']
            if level not in valid_levels:
                errors.append(f"无效的日志级别: {level}，有效值: {valid_levels}")

        # 生成警告
        if 'app' not in config:
            warnings.append('建议添加应用配置段 (app)')

        if 'monitoring' in config and not config['monitoring'].get('health_check', {}).get('enabled', False):
            warnings.append('建议启用健康检查功能')

        is_valid = len(errors) == 0
        return is_valid, errors + warnings

    def validate_all_configs(self) -> Dict[str, Any]:
        """验证所有环境的配置文件"""
        logger.info('🔍 验证所有配置文件...')

        results = {
            'validation_time': datetime.now().isoformat(),
            'environments': {},
            'total_errors': 0,
            'total_warnings': 0,
            'overall_status': 'valid'
        }

        # 检查所有环境
        environments = []
        for env_dir in self.environments_dir.iterdir():
            if env_dir.is_dir() and (env_dir / 'config.yaml').exists():
                environments.append(env_dir.name)

        for env in environments:
            logger.info(f"  检查 {env} 环境...")

            try:
                config = self.load_config(env)
                is_valid, issues = self.validate_config(config)

                env_result = {
                    'status': 'valid' if is_valid else 'invalid',
                    'errors': [issue for issue in issues if not issue.startswith('建议')],
                    'warnings': [issue for issue in issues if issue.startswith('建议')],
                    'config_file': str(self.environments_dir / env / 'config.yaml')
                }

                results['environments'][env] = env_result
                results['total_errors'] += len(env_result['errors'])
                results['total_warnings'] += len(env_result['warnings'])

                if not is_valid:
                    results['overall_status'] = 'invalid'

                # 显示结果
                if is_valid:
                    logger.info(f"    ✅ {env} 配置有效")
                else:
                    logger.info(f"    ❌ {env} 配置存在问题")

                for issue in issues:
                    status = '  ⚠️' if issue.startswith('建议') else '  ❌'
                    logger.info(f"    {status} {issue}")

            except Exception as e:
                logger.info(f"    💥 {env} 配置加载失败: {e}")
                results['environments'][env] = {
                    'status': 'error',
                    'error': str(e),
                    'errors': [f"配置加载失败: {e}"],
                    'warnings': []
                }
                results['total_errors'] += 1
                results['overall_status'] = 'error'

        return results

    def compare_configs(self, env1: str, env2: str) -> Dict[str, Any]:
        """比较两个环境的配置差异"""
        logger.info(f"🔍 比较 {env1} 和 {env2} 环境配置...")

        try:
            config1 = self.load_config(env1)
            config2 = self.load_config(env2)

            comparison = {
                'comparison_time': datetime.now().isoformat(),
                'environment_1': env1,
                'environment_2': env2,
                'differences': {},
                'only_in_env1': {},
                'only_in_env2': {},
                'summary': {}
            }

            # 递归比较配置
            def deep_compare(obj1, obj2, path=''):
                differences = []

                if isinstance(obj1, dict) and isinstance(obj2, dict):
                    # 检查只在obj1中的键
                    for key in obj1:
                        if key.startswith('_'):  # 跳过元数据
                            continue
                        if key not in obj2:
                            comparison['only_in_env1'][f"{path}.{key}" if path else key] = obj1[key]

                    # 检查只在obj2中的键
                    for key in obj2:
                        if key.startswith('_'):  # 跳过元数据
                            continue
                        if key not in obj1:
                            comparison['only_in_env2'][f"{path}.{key}" if path else key] = obj2[key]

                    # 检查共同的键
                    for key in obj1:
                        if key.startswith('_') or key not in obj2:
                            continue

                        new_path = f"{path}.{key}" if path else key
                        sub_diffs = deep_compare(obj1[key], obj2[key], new_path)
                        differences.extend(sub_diffs)

                elif obj1 != obj2:
                    differences.append({
                        'path': path,
                        'env1_value': obj1,
                        'env2_value': obj2
                    })

                return differences

            # 执行比较
            differences = deep_compare(config1, config2)
            comparison['differences'] = differences

            # 生成摘要
            comparison['summary'] = {
                'total_differences': len(differences),
                'only_in_env1_count': len(comparison['only_in_env1']),
                'only_in_env2_count': len(comparison['only_in_env2']),
                'similarity_score': max(0, 100 - len(differences) * 5)  # 简单的相似度计算
            }

            # 显示比较结果
            logger.info(f"📊 配置比较结果:")
            logger.info(f"  🔄 差异数量: {len(differences)}")
            logger.info(f"  📂 仅在 {env1} 中: {len(comparison['only_in_env1'])} 项")
            logger.info(f"  📂 仅在 {env2} 中: {len(comparison['only_in_env2'])} 项")
            logger.info(f"  📈 相似度: {comparison['summary']['similarity_score']}%")

            # 显示主要差异
            if differences:
                logger.info(f"\n🔍 主要差异:")
                for diff in differences[:10]:  # 只显示前10个差异
                    logger.info(f"  📝 {diff['path']}: {diff['env1_value']} → {diff['env2_value']}")

            return comparison

        except Exception as e:
            raise RuntimeError(f"配置比较失败: {e}")

    def sync_configs(self, source_env: str, target_env: str) -> bool:
        """同步配置（将源环境配置同步到目标环境）"""
        logger.info(f"🔄 同步配置: {source_env} → {target_env}")

        try:
            source_config = self.load_config(source_env)
            target_file = self.environments_dir / target_env / 'config.yaml'

            # 移除元数据
            config_copy = {k: v for k, v in source_config.items() if not k.startswith('_')}

            # 确保目标目录存在
            target_file.parent.mkdir(exist_ok=True)

            # 备份现有配置
            if target_file.exists():
                backup_file = target_file.with_suffix(f".yaml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                target_file.rename(backup_file)
                logger.info(f"  📦 已备份原配置到: {backup_file}")

            # 写入新配置
            with open(target_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_copy, f, default_flow_style=False, allow_unicode=True, indent=2)

            logger.info(f"  ✅ 配置同步完成: {target_file}")
            return True

        except Exception as e:
            logger.info(f"  ❌ 配置同步失败: {e}")
            return False

    def generate_unified_config(self) -> Dict[str, Any]:
        """生成统一配置文件"""
        logger.info('📋 生成统一配置文件...')

        unified_config = {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'description': 'Athena工作平台统一配置文件'
            },
            'environments': {}
        }

        # 加载所有环境配置
        environments = []
        for env_dir in self.environments_dir.iterdir():
            if env_dir.is_dir() and (env_dir / 'config.yaml').exists():
                environments.append(env_dir.name)

        for env in environments:
            try:
                config = self.load_config(env)
                unified_config['environments'][env] = config
                logger.info(f"  ✅ 已加载 {env} 环境配置")
            except Exception as e:
                logger.info(f"  ❌ 加载 {env} 环境配置失败: {e}")

        # 添加通用配置模板
        unified_config['common_template'] = {
            'app': {
                'name': 'athena-work-platform',
                'version': '2.0.0'
            },
            'ports': {
                'athena_main': 8000,
                'athena_memory': 8008,
                'xiaonuo_memory': 8083,
                'athena_identity': 8010,
                'memory_integration': 8011
            }
        }

        # 保存统一配置文件
        with open(self.unified_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(unified_config, f, default_flow_style=False, allow_unicode=True, indent=2)

        logger.info(f"  📄 统一配置文件已生成: {self.unified_config_file}")
        return unified_config

    def standardize_json_configs(self) -> int:
        """将JSON配置文件转换为YAML格式"""
        logger.info('📝 标准化JSON配置文件...')

        converted_count = 0

        # 查找所有JSON配置文件
        json_configs = list(self.config_dir.rglob('*.json'))

        for json_file in json_configs:
            if 'unified_config' in str(json_file):
                continue  # 跳过统一配置文件

            try:
                # 读取JSON配置
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_config = json.load(f)

                # 生成对应的YAML文件路径
                yaml_file = json_file.with_suffix('.yaml')

                # 转换为YAML格式
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(json_config, f, default_flow_style=False, allow_unicode=True, indent=2)

                # 备份原JSON文件
                backup_file = json_file.with_suffix(f'.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}')
                json_file.rename(backup_file)

                logger.info(f"  ✅ 已转换: {json_file} → {yaml_file}")
                converted_count += 1

            except Exception as e:
                logger.info(f"  ❌ 转换失败 {json_file}: {e}")

        logger.info(f"📊 总共转换了 {converted_count} 个配置文件")
        return converted_count

    def print_config_summary(self) -> None:
        """打印配置文件摘要"""
        logger.info('📊 Athena工作平台配置文件摘要')
        logger.info(str('=' * 50))

        # 环境配置
        logger.info(f"\n🏗️ 环境配置:")
        environments = []
        for env_dir in self.environments_dir.iterdir():
            if env_dir.is_dir() and (env_dir / 'config.yaml').exists():
                environments.append(env_dir.name)

        for env in sorted(environments):
            config_file = self.environments_dir / env / 'config.yaml'
            file_size = config_file.stat().st_size
            modified_time = datetime.fromtimestamp(config_file.stat().st_mtime)
            logger.info(f"  📁 {env}: {config_file} ({file_size} bytes, 更新于 {modified_time.strftime('%Y-%m-%d %H:%M')})")

        # 服务配置
        logger.info(f"\n🛠️ 服务配置:")
        if self.services_dir.exists():
            service_configs = list(self.services_dir.rglob('*.yaml'))
            for config in service_configs:
                rel_path = config.relative_to(self.services_dir)
                logger.info(f"  📄 {rel_path}")

        # 其他配置文件
        logger.info(f"\n📋 其他配置文件:")
        other_configs = []
        for pattern in ['*.json', '*.yaml', '*.yml']:
            other_configs.extend(self.config_dir.glob(pattern))

        for config in sorted(other_configs):
            if 'environments' not in str(config) and 'services' not in str(config):
                rel_path = config.relative_to(self.config_dir)
                logger.info(f"  📄 {rel_path}")

        logger.info(f"\n📈 配置统计:")
        logger.info(f"  🏗️ 环境配置: {len(environments)} 个")
        logger.info(f"  🛠️ 服务配置: {len(service_configs) if self.services_dir.exists() else 0} 个")
        logger.info(f"  📋 其他配置: {len(other_configs)} 个")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena工作平台配置管理器')
    parser.add_argument('--validate', action='store_true', help='验证所有配置文件')
    parser.add_argument('--compare', nargs=2, metavar=('ENV1', 'ENV2'), help='比较两个环境的配置')
    parser.add_argument('--sync', nargs=2, metavar=('SOURCE', 'TARGET'), help='同步配置')
    parser.add_argument('--generate', help='生成指定环境的配置')
    parser.add_argument('--unified', action='store_true', help='生成统一配置文件')
    parser.add_argument('--standardize', action='store_true', help='标准化JSON配置文件')
    parser.add_argument('--summary', action='store_true', help='显示配置文件摘要')

    args = parser.parse_args()

    manager = ConfigManager()

    if args.validate or not any(vars(args).values()):
        # 默认执行验证
        results = manager.validate_all_configs()

        logger.info(f"\n📊 验证总结:")
        logger.info(f"  ✅ 有效环境: {len([env for env, info in results['environments'].items() if info['status'] == 'valid'])}")
        logger.info(f"  ❌ 无效环境: {len([env for env, info in results['environments'].items() if info['status'] != 'valid'])}")
        logger.info(f"  🚨 总错误: {results['total_errors']}")
        logger.info(f"  ⚠️ 总警告: {results['total_warnings']}")
        logger.info(f"  📊 整体状态: {results['overall_status']}")

    elif args.compare:
        env1, env2 = args.compare
        comparison = manager.compare_configs(env1, env2)

    elif args.sync:
        source_env, target_env = args.sync
        success = manager.sync_configs(source_env, target_env)
        if success:
            logger.info('✅ 配置同步成功')
        else:
            logger.info('❌ 配置同步失败')

    elif args.generate:
        logger.info(f"🔧 生成 {args.generate} 环境配置...")
        # 这里可以实现配置生成逻辑
        logger.info('⚠️ 配置生成功能待实现')

    elif args.unified:
        manager.generate_unified_config()

    elif args.standardize:
        converted_count = manager.standardize_json_configs()
        logger.info(f"✅ 标准化完成，转换了 {converted_count} 个文件")

    elif args.summary:
        manager.print_config_summary()

if __name__ == '__main__':
    main()