#!/usr/bin/env python3
"""
BERT模型下载脚本
Download BERT Models for Athena Platform

从魔搭社区下载推荐的BERT模型

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent.parent))

def setup_mirrors():
    """设置下载镜像"""
    # 设置魔搭社区镜像
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

    # 设置pip镜像
    pip_config = """
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
"""

    pip_config_path = Path.home() / ".pip" / "pip.conf"
    pip_config_path.parent.mkdir(exist_ok=True)

    with open(pip_config_path, 'w') as f:
        f.write(pip_config)

    print("✅ 已设置下载镜像源")

def download_model(model_name, model_id):
    """下载指定模型"""
    print(f"\n🔄 开始下载 {model_name}...")
    print(f"   模型ID: {model_id}")

    try:
        # 使用transformers-cli下载
        cmd = [
            "transformers-cli", "download",
            model_id,
            "--cache-dir", "/Users/xujian/Athena工作平台/models/bert_cache"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {model_name} 下载成功！")
            return True
        else:
            print(f"❌ {model_name} 下载失败:")
            print(f"   错误信息: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 下载 {model_name} 时出错: {e}")
        return False

def main():
    """主函数"""
    print("🤖 BERT模型下载器")
    print("=" * 50)

    # 设置镜像源
    setup_mirrors()

    # 安装依赖
    print("\n📦 检查并安装依赖...")
    try:
        subprocess.run([
            "pip", "install",
            "transformers>=4.21.0",
            "torch>=1.12.0",
            "tokenizers>=0.13.0",
            "modelscope>=1.4.0"
        ], check=True)
        print("✅ 依赖检查完成")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 依赖安装可能失败: {e}")
        print("   请手动安装: pip install transformers torch tokenizers modelscope")

    # 需要下载的模型列表（优先使用魔搭社区）
    models_to_download = [
        {
            "name": "Lawformer (法律BERT)",
            "id": "THUDM/Lawformer",
            "priority": 1,
            "description": "法律领域专用BERT模型"
        },
        {
            "name": "Chinese-RoBERTa-WWM-Ext (通用BERT)",
            "id": "hfl/chinese-roberta-wwm-ext-ext",
            "priority": 1,
            "description": "增强版中文RoBERTa模型"
        },
        {
            "name": "Chinese-DeBERTa-V3",
            "id": "hfl/chinese-deberta-v3-base",
            "priority": 2,
            "description": "中文DeBERTa模型，理解能力更强"
        },
        {
            "name": "Chinese-BERT-wwm-ext",
            "id": "hfl/chinese-bert-wwm-ext",
            "priority": 3,
            "description": "中文BERT扩展版本"
        }
    ]

    # 按优先级排序
    models_to_download.sort(key=lambda x: x["priority"])

    # 创建下载报告
    download_report = {
        "start_time": str(datetime.now()),
        "models": {},
        "success_count": 0,
        "total_count": len(models_to_download)
    }

    print(f"\n📋 准备下载 {len(models_to_download)} 个模型：")
    for i, model in enumerate(models_to_download, 1):
        print(f"{i}. {model['name']} - {model['description']}")

    # 开始下载
    success_count = 0

    for model in models_to_download:
        if download_model(model["name"], model["id"]):
            success_count += 1
            download_report["models"][model["id"]] = {
                "name": model["name"],
                "status": "success",
                "priority": model["priority"]
            }
        else:
            download_report["models"][model["id"]] = {
                "name": model["name"],
                "status": "failed",
                "priority": model["priority"]
            }

    download_report["success_count"] = success_count

    # 保存下载报告
    report_path = "/Users/xujian/Athena工作平台/models/bert_download_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(download_report, f, ensure_ascii=False, indent=2)

    # 输出结果
    print("\n" + "=" * 50)
    print(f"📊 下载完成统计:")
    print(f"   - 成功: {success_count}/{len(models_to_download)}")
    print(f"   - 失败: {len(models_to_download) - success_count}/{len(models_to_download)}")
    print(f"   - 报告已保存: {report_path}")

    if success_count > 0:
        print("\n✅ 模型下载完成！")
        print("   可以运行: python3 test_bert_integration.py")
        print("   来测试模型集成效果。")
    else:
        print("\n⚠️ 所有模型下载失败")
        print("   请检查网络连接或手动下载。")

    return success_count > 0

if __name__ == "__main__":
    from datetime import datetime
    main()