#!/usr/bin/env python3
"""
MCP服务自动注册系统
"""

import json
from pathlib import Path

PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
MCP_SERVERS_DIR = PROJECT_ROOT / "mcp-servers"
CONFIG_DIR = PROJECT_ROOT / "config"
SERVICE_DISCOVERY_FILE = CONFIG_DIR / "service_discovery.json"

MCP_SERVICES_BASE = {
    "gaode-mcp-server": {
        "name": "gaode-mcp-server",
        "type": "mcp",
        "provider": "mlx",
        "protocol": "stdio",
        "protocol": "http",
        "port": 8080,
        "description": "高德地图API服务"
    },
    "jina-ai-mcp-server": {
        "name": "jina-ai-mcp-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "http",
        "port": 8080,
        "description": "Jina AI搜索和嵌入服务"
    },
    "academic-search-mcp-server": {
        "name": "academic-search-mcp-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "http",
        "port": 8080,
        "description": "学术搜索服务"
    },
    "chrome-mcp-server": {
        "name": "chrome-mcp-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "stdio",
        "enabled": False,
        "description": "浏览器自动化服务"
    },
    "github-mcp-server": {
        "name": "github-mcp-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "stdio",
        "enabled": False,
        "description": "GitHub API集成服务"
    },
    "google-patents-meta-server": {
        "name": "google-patents-meta-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "stdio",
        "enabled": False,
        "description": "Google专利元数据服务"
    },
    "imsg-mcp-server": {
        "name": "imsg-mcp-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "stdio",
        "enabled": False,
        "description": "iMessage集成服务"
    },
    "patent_downloader": {
        "name": "patent_downloader",
        "type": "script",
        "enabled": False,
        "description": "专利PDF下载服务"
    },
    "patent-search-mcp-server": {
        "name": "patent-search-mcp-server",
        "type": "mcp",
        "provider": "nodejs",
        "protocol": "stdio",
        "enabled": False,
        "description": "专利搜索服务"
    },
    "xiaonuo-calendar-assistant": {
        "name": "xiaonuo-calendar-assistant",
        "type": "mcp",
        "provider": "python",
        "protocol": "stdio",
        "enabled": False,
        "description": "小诺日历助手服务"
    }
}


def scan_mcp_servers() -> dict:
    """扫描mcp-servers目录，返回服务配置字典"""
    services_to_register = {}
    print("🔍 扫描MCP服务器目录...")

    for server_dir in MCP_SERVERS_DIR.iterdir():
        if not server_dir.is_dir():
            continue

        server_name = server_dir.name

        if server_name in MCP_SERVICES_BASE:
            services_to_register[server_name] = MCP_SERVICES_BASE[server_name]
            print(f"✅ {server_name}: 已知服务，使用预定义配置")
            continue

        config_file = server_dir / "config.yaml"
        env_file = server_dir / ".env"

        service_info = {
            "name": server_name,
            "type": "mcp",
            "provider": "unknown",
            "protocol": "stdio",
            "enabled": True,
            "description": f"{server_name} MCP服务",
            "path": str(server_dir),
            "config": str(config_file) if config_file.exists() else None,
            "env": str(env_file) if env_file.exists() else None,
            "health_check": "/health"
        }

        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    config_data = json.load(f)
                    service_info.update(config_data)
                    print(f"📄 从 {config_file.name} 读取配置")
            except Exception as e:
                print(f"⚠️  读取配置文件失败: {str(e)}")

        services_to_register[server_name] = service_info

    return services_to_register


def update_service_discovery(services: dict) -> None:
    """更新service_discovery.json文件"""
    print("📝 更新service_discovery.json...")

    try:
        with open(SERVICE_DISCOVERY_FILE, encoding="utf-8") as f:
            discovery_config = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取service_discovery.json失败: {str(e)}")
        return

    discovery_config["services"] = list(services.values())

    total_services = len(services)
    enabled_services = len([s for s in services.values() if s.get("enabled", True)])

    discovery_config["statistics"] = {
        "total": total_services,
        "enabled": enabled_services,
        "last_scan": discovery_config.get("last_scan", ""),
        "scan_timestamp": None
    }

    try:
        with open(SERVICE_DISCOVERY_FILE, "w", encoding="utf-8") as f:
            json.dump(discovery_config, f, indent=2, ensure_ascii=False)
        print("✅ 已更新service发现配置")
        print(f"   - 总服务数: {total_services}")
        print(f"   - 已启用: {enabled_services}")
    except Exception as e:
        print(f"❌ 更新service_discovery.json失败: {str(e)}")


def main():
    """主函数"""
    print("=== MCP服务自动注册系统 ===")

    services = scan_mcp_servers()

    update_service_discovery(services)

    print("\n✅ 完成！")
    print(f"📊 注册了 {len(services)} 个MCP服务到服务发现系统")


if __name__ == "__main__":
    main()
