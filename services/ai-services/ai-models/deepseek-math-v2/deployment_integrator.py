#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeekMath V2技术集成部署器
将论文技术集成到Athena智能工作平台的统一部署系统

作者: Athena AI团队
版本: 1.0.0
创建时间: 2025-11-28
"""

import importlib.util
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class DeepSeekMathV2Integrator:
    """DeepSeekMath V2技术集成部署器"""

    def __init__(self, athena_root: str = '/Users/xujian/Athena工作平台'):
        self.athena_root = Path(athena_root)
        self.deepseek_root = self.athena_root / 'athena_core' / 'deepseek_math_v2'
        self.integration_status = {
            'grpo_deployed': False,
            'two_stage_deployed': False,
            'data_generator_deployed': False,
            'evaluation_deployed': False,
            'api_endpoints_created': False,
            'timestamp': datetime.now().isoformat()
        }

    def deploy_all_components(self) -> Dict[str, Any]:
        """部署所有组件"""
        logger.info('开始部署DeepSeekMath V2技术组件...')

        deployment_results = {
            'start_time': datetime.now().isoformat(),
            'components_deployed': [],
            'components_failed': [],
            'api_endpoints': [],
            'integration_tests': {}
        }

        # 1. 部署GRPO优化器
        try:
            grpo_result = self._deploy_grpo_optimizer()
            deployment_results['components_deployed'].append('GRPO优化器')
            deployment_results['api_endpoints'].extend(grpo_result['api_endpoints'])
            self.integration_status['grpo_deployed'] = True
            logger.info('✅ GRPO优化器部署成功')
        except Exception as e:
            deployment_results['components_failed'].append({'component': 'GRPO优化器', 'error': str(e)})
            logger.error(f"❌ GRPO优化器部署失败: {e}")

        # 2. 部署两阶段学习系统
        try:
            two_stage_result = self._deploy_two_stage_learning()
            deployment_results['components_deployed'].append('两阶段学习系统')
            deployment_results['api_endpoints'].extend(two_stage_result['api_endpoints'])
            self.integration_status['two_stage_deployed'] = True
            logger.info('✅ 两阶段学习系统部署成功')
        except Exception as e:
            deployment_results['components_failed'].append({'component': '两阶段学习系统', 'error': str(e)})
            logger.error(f"❌ 两阶段学习系统部署失败: {e}")

        # 3. 部署数据生成器
        try:
            data_gen_result = self._deploy_data_generator()
            deployment_results['components_deployed'].append('数据生成器')
            deployment_results['api_endpoints'].extend(data_gen_result['api_endpoints'])
            self.integration_status['data_generator_deployed'] = True
            logger.info('✅ 数据生成器部署成功')
        except Exception as e:
            deployment_results['components_failed'].append({'component': '数据生成器', 'error': str(e)})
            logger.error(f"❌ 数据生成器部署失败: {e}")

        # 4. 部署评估系统
        try:
            eval_result = self._deploy_evaluation_system()
            deployment_results['components_deployed'].append('评估系统')
            deployment_results['api_endpoints'].extend(eval_result['api_endpoints'])
            self.integration_status['evaluation_deployed'] = True
            logger.info('✅ 评估系统部署成功')
        except Exception as e:
            deployment_results['components_failed'].append({'component': '评估系统', 'error': str(e)})
            logger.error(f"❌ 评估系统部署失败: {e}")

        # 5. 创建API端点
        try:
            api_result = self._create_api_endpoints()
            deployment_results['api_endpoints'].extend(api_result['api_endpoints'])
            self.integration_status['api_endpoints_created'] = True
            logger.info('✅ API端点创建成功')
        except Exception as e:
            deployment_results['components_failed'].append({'component': 'API端点', 'error': str(e)})
            logger.error(f"❌ API端点创建失败: {e}")

        # 6. 集成测试
        try:
            test_results = self._run_integration_tests()
            deployment_results['integration_tests'] = test_results
            logger.info('✅ 集成测试完成')
        except Exception as e:
            logger.error(f"❌ 集成测试失败: {e}")

        # 保存部署状态
        self._save_deployment_status(deployment_results)

        deployment_results['end_time'] = datetime.now().isoformat()
        deployment_results['deployment_status'] = self.integration_status

        logger.info('🎉 DeepSeekMath V2技术部署完成!')
        return deployment_results

    def _deploy_grpo_optimizer(self) -> Dict[str, Any]:
        """部署GRPO优化器"""
        # 创建GRPO服务脚本
        grpo_service_path = self.deepseek_root / 'services' / 'grpo_service.py'
        grpo_service_path.parent.mkdir(parents=True, exist_ok=True)

        grpo_service_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRPO优化器服务
基于DeepSeekMath V2的无奖励强化学习专利分析优化服务
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException

# 导入统一认证模块
from shared.auth.auth_middleware import (
    create_auth_middleware,
    setup_cors
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import torch
import json
from datetime import datetime

# 导入GRPO模块
from grpo_optimizer import PatentGRPOOptimizer, GRPOConfig, PatentPolicyNetwork

app = FastAPI(
    title='Athena GRPO专利分析优化器',
    description='基于DeepSeekMath V2的无奖励强化学习专利分析优化服务',
    version='1.0.0'
)


# 服务端点配置
SERVICE_ENDPOINTS = {
    'grpo': 'http://localhost:8020',
    'two_stage': 'http://localhost:8021',
    'data_generator': 'http://localhost:8022',
    'evaluation': 'http://localhost:8023'
}

@app.get('/')
async def root():
    return {
        'service': 'Athena DeepSeekMath V2统一API',
        'status': 'running',
        'version': '1.0.0',
        'description': 'DeepSeekMath V2技术集成统一API服务',
        'integrated_services': list(SERVICE_ENDPOINTS.keys()),
        'features': [
            '🔍 GRPO优化器',
            '🎯 两阶段学习',
            '📊 数据生成器',
            '📈 性能评估',
            '🔗 统一接口'
        ]
    }

@app.get('/health')
async def health_check():
    """统一健康检查"""
    service_status = {}

    for service_name, endpoint in SERVICE_ENDPOINTS.items():
        try:
            response = requests.get(f"{endpoint}/health", timeout=2)
            service_status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'endpoint': endpoint,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            service_status[service_name] = {
                'status': 'error',
                'endpoint': endpoint,
                'error': str(e)
            }

    all_healthy = all(status['status'] == 'healthy' for status in service_status.values())

    return {
        'overall_status': 'healthy' if all_healthy else 'partial',
        'services': service_status,
        'timestamp': datetime.now().isoformat()
    }

@app.post('/patent/optimize')
async def optimize_patent_strategy(request: dict):
    """专利策略优化接口"""
    try:
        response = requests.post(
            f"{SERVICE_ENDPOINTS['grpo']}/optimize",
            json=request,
            timeout=30
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GRPO优化失败: {str(e)}")

@app.post('/patent/analyze')
async def analyze_patent(request: dict):
    """专利分析接口"""
    try:
        response = requests.post(
            f"{SERVICE_ENDPOINTS['two_stage']}/analyze",
            json=request,
            timeout=30
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"专利分析失败: {str(e)}")

@app.post('/patent/generate_data')
async def generate_patent_data(request: dict):
    """专利数据生成接口"""
    try:
        response = requests.post(
            f"{SERVICE_ENDPOINTS['data_generator']}/generate_training_data",
            json=request,
            timeout=60
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据生成失败: {str(e)}")

@app.post('/evaluate')
async def evaluate_performance(request: dict):
    """性能评估接口"""
    try:
        response = requests.post(
            f"{SERVICE_ENDPOINTS['evaluation']}/evaluate",
            json=request,
            timeout=30
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能评估失败: {str(e)}")

@app.get('/metrics')
async def get_metrics():
    """获取性能指标"""
    try:
        response = requests.get(
            f"{SERVICE_ENDPOINTS['evaluation']}/metrics",
            timeout=10
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8025)
'''

        with open(api_router_path, 'w', encoding='utf-8') as f:
            f.write(api_router_code)

        # 创建统一启动脚本
        unified_start_script = self.deepseek_root / 'scripts' / 'start_deepseek_services.sh'
        unified_start_script.parent.mkdir(parents=True, exist_ok=True)

        unified_script_content = '''#!/bin/bash
# DeepSeekMath V2统一服务启动脚本

echo '🚀 启动Athena DeepSeekMath V2技术集成服务...'
echo '=================================================='

# 设置环境
export PYTHONPATH='${PYTHONPATH}:$(pwd)'

# 检查并停止现有服务
echo '🛑 清理现有DeepSeekMath V2服务...'
for port in 8020 8021 8022 8023 8025; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo '  停止端口$port上的服务'
        pkill -f ':$port'
        sleep 1
    fi
done

# 启动各个服务
echo ''
echo '🔧 启动DeepSeekMath V2核心服务...'

# 1. 启动GRPO优化器服务
echo '📊 启动GRPO优化器服务 (端口8020)...'
cd $(dirname '$0')/../services
python3 grpo_service.py &
GRPO_PID=$!
echo 'GRPO服务PID: $GRPO_PID'

# 2. 启动两阶段学习服务
echo '🎯 启动两阶段学习服务 (端口8021)...'
python3 two_stage_service.py &
STAGE_PID=$!
echo '两阶段服务PID: $STAGE_PID'

# 3. 启动数据生成服务
echo '📈 启动专利数据生成服务 (端口8022)...'
python3 data_generator_service.py &
DATA_GEN_PID=$!
echo '数据生成服务PID: $DATA_GEN_PID'

# 4. 启动评估服务
echo '📊 启动技术评估服务 (端口8023)...'
python3 evaluation_service.py &
EVAL_PID=$!
echo '评估服务PID: $EVAL_PID'

# 5. 启动统一API服务
echo '🔗 启动统一API服务 (端口8025)...'
python3 api_router.py &
API_PID=$!
echo '统一API服务PID: $API_PID'

# 保存进程ID
echo $GRPO_PID $STAGE_PID $DATA_GEN_PID $EVAL_PID $API_PID > /tmp/deepseek_pids.txt

# 等待所有服务启动
echo ''
echo '⏳ 等待所有服务启动...'
sleep 5

# 检查服务状态
echo ''
echo '🔍 检查服务状态:'
all_services_healthy=true

for service in 'grpo' 'two_stage' 'data_generator' 'evaluation' 'api'; do
    case $service in
        'grpo')
            port=8020
            name='GRPO优化器'
            ;;
        'two_stage')
            port=8021
            name='两阶段学习'
            ;;
        'data_generator')
            port=8022
            name='数据生成器'
            ;;
        'evaluation')
            port=8023
            name='技术评估'
            ;;
        'api')
            port=8025
            name='统一API'
            ;;
    esac

    if curl -s 'http://localhost:$port/health' > /dev/null; then
        echo '  ✅ $name (端口$port): 健康'
    else
        echo '  ❌ $name (端口$port): 未响应'
        all_services_healthy=false
    fi
done

# 显示服务信息
echo ''
if [ '$all_services_healthy' = true ]; then
    echo '🎉 DeepSeekMath V2技术集成服务启动完成!'
    echo ''
    echo '🌐 服务访问地址:'
    echo '  🔍 GRPO优化器:        http://localhost:8020'
    echo '  🎯 两阶段学习:       http://localhost:8021'
    echo '  📊 数据生成器:        http://localhost:8022'
    echo '  📈 技术评估:          http://localhost:8023'
    echo '  🔗 统一API:           http://localhost:8025'
    echo ''
    echo '📖 健康检查:            http://localhost:8025/health'
    echo '📊 API文档:            http://localhost:8025/docs'
    echo ''
    echo '💡 DeepSeekMath V2技术已完全集成到Athena平台!'
    echo '   - 无奖励强化学习 (GRPO)'
    echo '   - 两阶段渐进学习'
    echo '   - 大规模数据生成'
    echo '   - 综合性能评估'
    echo '   - 统一API接口'
else
    echo '⚠️ 部分服务启动失败，请检查日志'
    echo ''
    echo '🛑 停止所有服务:'
    echo '  ./scripts/stop_deepseek_services.sh'
    exit 1
fi
'''

        with open(unified_start_script, 'w', encoding='utf-8') as f:
            f.write(unified_script_content)

        # 创建停止脚本
        stop_script_content = '''#!/bin/bash
# DeepSeekMath V2服务停止脚本

echo '🛑 停止DeepSeekMath V2技术集成服务...'

# 从文件读取进程ID
if [ -f '/tmp/deepseek_pids.txt' ]; then
    PIDS=$(cat /tmp/deepseek_pids.txt)
    for pid in $PIDS; do
        if kill -0 $pid 2>/dev/null; then
            echo '停止进程: $pid'
            kill $pid
        fi
    done
    rm -f /tmp/deepseek_pids.txt
fi

# 强制停止可能残留的进程
echo '🧹 清理残留进程...'
for port in 8020 8021 8022 8023 8025; do
    pkill -f ':$port' 2>/dev/null
done

echo '✅ 所有DeepSeekMath V2服务已停止'
'''

        stop_script_path = self.deepseek_root / 'scripts' / 'stop_deepseek_services.sh'
        with open(stop_script_path, 'w', encoding='utf-8') as f:
            f.write(stop_script_content)

        os.chmod(unified_start_script, 0o755)
        os.chmod(stop_script_path, 0o755)

        return {
            'api_router_path': str(api_router_path),
            'unified_start_script': str(unified_start_script),
            'stop_script': str(stop_script_path),
            'api_endpoints': [
                'http://localhost:8025/',
                'http://localhost:8025/health',
                'http://localhost:8025/docs'
            ]
        }

    def _run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        test_results = {}

        # 测试GRPO服务
        try:
            import requests
            response = requests.get('http://localhost:8020/health', timeout=5)
            test_results['grpo_service'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            }
        except (ConnectionError, OSError, TimeoutError):
            test_results['grpo_service'] = {'status': 'failed', 'error': 'connection_error'}

        # 测试两阶段学习服务
        try:
            response = requests.get('http://localhost:8021/health', timeout=5)
            test_results['two_stage_service'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            }
        except (ConnectionError, OSError, TimeoutError):
            test_results['two_stage_service'] = {'status': 'failed', 'error': 'connection_error'}

        # 测试数据生成服务
        try:
            response = requests.get('http://localhost:8022/health', timeout=5)
            test_results['data_generator_service'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            }
        except (ConnectionError, OSError, TimeoutError):
            test_results['data_generator_service'] = {'status': 'failed', 'error': 'connection_error'}

        # 测试评估服务
        try:
            response = requests.get('http://localhost:8023/health', timeout=5)
            test_results['evaluation_service'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            }
        except (ConnectionError, OSError, TimeoutError):
            test_results['evaluation_service'] = {'status': 'failed', 'error': 'connection_error'}

        # 测试统一API
        try:
            response = requests.get('http://localhost:8025/health', timeout=5)
            test_results['unified_api'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response.elapsed.total_seconds()
            }
        except (ConnectionError, OSError, TimeoutError):
            test_results['unified_api'] = {'status': 'failed', 'error': 'connection_error'}

        return test_results

    def _save_deployment_status(self, deployment_results: Dict[str, Any]):
        """保存部署状态"""
        status_path = self.deepseek_root / 'deployment_status.json'

        deployment_info = {
            'deployment_timestamp': datetime.now().isoformat(),
            'athena_platform_root': str(self.athena_root),
            'deepseek_v2_root': str(self.deepseek_root),
            'integration_status': self.integration_status,
            'deployment_results': deployment_results,
            'success_summary': {
                'total_components': len(deployment_results.get('components_deployed', [])),
                'failed_components': len(deployment_results.get('components_failed', [])),
                'api_endpoints': len(deployment_results.get('api_endpoints', [])),
                'integration_tests': deployment_results.get('integration_tests', {})
            }
        }

        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(deployment_info, f, indent=2, ensure_ascii=False)

        logger.info(f"部署状态已保存: {status_path}")

# 主程序入口
if __name__ == '__main__':
    # 创建集成器
    integrator = DeepSeekMathV2Integrator()

    # 运行完整部署
    results = integrator.deploy_all_components()

    logger.info('🎉 DeepSeekMath V2技术集成部署完成!')
    logger.info(f"✅ 部署的组件: {len(results['components_deployed'])}")
    logger.info(f"❌ 失败的组件: {len(results['components_failed'])}")
    logger.info(f"🌐 API端点: {len(results['api_endpoints'])}")

    if results['integration_tests']:
        logger.info('📋 集成测试结果:')
        for service, result in results['integration_tests'].items():
            status = '✅' if result['status'] == 'passed' else '❌'
            logger.info(f"  {status} {service}: {result['status']}")

    logger.info(f"\n📄 详细部署报告: {integrator.deepseek_root / 'deployment_status.json'}")
'''

        with write_file_path.open('w', encoding='utf-8') as f:
            f.write(integrator_script_content)

        # 设置执行权限
        os.chmod(integrator_path, 0o755)

        logger.info(f"集成部署器已创建: {integrator_path}")
        logger.info('使用方法: python3 deploy_integrator.py')

        return str(integrator_path)
TodoWrite
<arg_key>todos</arg_key>
<arg_value>[{'content': '深度挖掘论文核心架构设计', 'status': 'completed', 'active_form': '深度挖掘论文核心架构设计'}, {'content': '实现GRPO核心算法模块', 'status': 'completed', 'active_form': '实现GRPO核心算法模块'}, {'content': '部署两阶段学习系统', 'status': 'completed', 'active_form': '部署两阶段学习系统'}, {'content': '集成数据生成和优化器', 'status': 'completed', 'active_form': '集成数据生成和优化器'}, {'content': '测试和性能评估', 'status': 'completed', 'active_form': '测试和性能评估'}]