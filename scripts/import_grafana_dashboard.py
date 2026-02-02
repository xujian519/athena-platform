#!/usr/bin/env python3
"""
Grafana仪表板导入脚本
Grafana Dashboard Importer

自动导入认知与决策模块的监控仪表板到Grafana

作者: Athena Platform Team
版本: v1.0
"""

import json
import argparse
import requests
from pathlib import Path
from typing import Optional


def import_dashboard_via_api(
    grafana_url: str,
    api_key: str,
    dashboard_file: str,
    folder: str = "Athena",
    overwrite: bool = True
) -> bool:
    """
    通过Grafana API导入仪表板

    Args:
        grafana_url: Grafana服务URL (如 http://localhost:3000)
        api_key: Grafana API密钥
        dashboard_file: 仪表板JSON文件路径
        folder: 目标文件夹名称
        overwrite: 是否覆盖已存在的仪表板

    Returns:
        bool: 导入是否成功
    """
    # 读取仪表板配置
    dashboard_path = Path(dashboard_file)
    if not dashboard_path.exists():
        print(f"❌ 仪表板文件不存在: {dashboard_file}")
        return False

    with open(dashboard_path, 'r', encoding='utf-8') as f:
        dashboard_json = json.load(f)

    # 准备导入payload
    payload = {
        "dashboard": dashboard_json,
        "overwrite": overwrite,
        "message": "通过API自动导入 - Athena认知决策模块监控"
    }

    # 如果指定了文件夹，获取或创建文件夹
    folder_id = None
    if folder:
        # 查找文件夹
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"{grafana_url}/api/folders",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            folders = response.json()
            target_folder = next((f for f in folders if f["title"] == folder), None)

            if target_folder:
                folder_id = target_folder["id"]
            else:
                # 创建新文件夹
                create_response = requests.post(
                    f"{grafana_url}/api/folders",
                    headers=headers,
                    json={"title": folder},
                    timeout=10
                )
                if create_response.status_code == 200:
                    folder_id = create_response.json()["id"]
                    print(f"✅ 创建文件夹: {folder}")

        if folder_id:
            payload["folderId"] = folder_id

    # 导入仪表板
    import_response = requests.post(
        f"{grafana_url}/api/dashboards/db",
        headers=headers,
        json=payload,
        timeout=10
    )

    if import_response.status_code == 200:
        result = import_response.json()
        print(f"✅ 仪表板导入成功!")
        print(f"   URL: {grafana_url}{result['url']}")
        print(f"   UID: {result['uid']}")
        print(f"   版本: {result['version']}")
        return True
    else:
        print(f"❌ 仪表板导入失败: {import_response.status_code}")
        print(f"   错误: {import_response.text}")
        return False


def print_manual_import_instructions(
    dashboard_file: str,
    grafana_url: str = "http://localhost:3000"
):
    """
    打印手动导入说明
    """
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║          Grafana 仪表板手动导入指南                            ║
╚════════════════════════════════════════════════════════════════╝

📁 仪表板文件位置:
   {dashboard_file}

🌐 Grafana访问地址:
   {grafana_url}

📋 手动导入步骤:

   1. 登录Grafana
      - 打开浏览器访问: {grafana_url}
      - 默认用户名: admin
      - 默认密码: admin
      - 首次登录后会提示修改密码

   2. 进入导入页面
      - 点击左侧菜单 "+" → "Import"
      - 或直接访问: {grafana_url}/dashboard/import

   3. 上传仪表板文件
      - 点击 "Upload JSON file"
      - 选择文件: {dashboard_file}
      - 或直接复制粘贴JSON内容

   4. 配置仪表板
      - Name: Athena 认知与决策模块监控仪表板
      - Folder: Athena (或选择其他文件夹)
      - Unique UID: athena-cognitive-decision

   5. 点击 "Import" 完成导入

   6. 验证仪表板
      - 仪表板应显示10个监控面板
      - 包括认知处理延迟、决策队列、内存使用等指标

💡 提示:
   - 如果没有看到数据，请确认Prometheus数据源已配置
   - 默认Prometheus地址: http://localhost:9090
   - 刷新时间默认为30秒，可在右上角调整

🔧 配置Prometheus数据源:

   1. 在Grafana中: Configuration → Data Sources → Add data source
   2. 选择 "Prometheus"
   3. 设置:
      - Name: Prometheus
      - URL: http://localhost:9090
      - Access: Server (default)
   4. 点击 "Save & Test"

═════════════════════════════════════════════════════════════════
""")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Grafana仪表板导入工具")
    parser.add_argument(
        '--grafana-url',
        default='http://localhost:3000',
        help='Grafana服务URL (默认: http://localhost:3000)'
    )
    parser.add_argument(
        '--api-key',
        help='Grafana API密钥 (用于自动导入)'
    )
    parser.add_argument(
        '--dashboard',
        default='config/monitoring/grafana/cognitive_decision_dashboard.json',
        help='仪表板JSON文件路径'
    )
    parser.add_argument(
        '--folder',
        default='Athena',
        help='目标文件夹名称 (默认: Athena)'
    )
    parser.add_argument(
        '--manual',
        action='store_true',
        help='仅显示手动导入说明'
    )
    parser.add_argument(
        '--no-overwrite',
        action='store_true',
        help='不覆盖已存在的仪表板'
    )

    args = parser.parse_args()

    # 如果只是显示手动导入说明
    if args.manual:
        print_manual_import_instructions(args.dashboard, args.grafana_url)
        return

    # 如果提供了API密钥，自动导入
    if args.api_key:
        print("🚀 开始自动导入Grafana仪表板...\n")
        success = import_dashboard_via_api(
            grafana_url=args.grafana_url,
            api_key=args.api_key,
            dashboard_file=args.dashboard,
            folder=args.folder,
            overwrite=not args.no_overwrite
        )

        if success:
            print("\n✅ 导入完成!")
            print(f"📊 访问仪表板: {args.grafana_url}/d/athena-cognitive-decision")
        else:
            print("\n❌ 导入失败，请检查错误信息或使用手动导入方式")
            print("\n使用 --manual 查看手动导入说明")
    else:
        # 没有API密钥，显示手动导入说明
        print("⚠️  未提供API密钥，无法自动导入")
        print("💡 使用 --api-key 参数进行自动导入，或参考以下手动导入说明:\n")
        print_manual_import_instructions(args.dashboard, args.grafana_url)


if __name__ == '__main__':
    main()
