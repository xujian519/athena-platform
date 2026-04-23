#!/usr/bin/env python3
"""
专利申请管理系统启动脚本
Patent Application Management System Startup Script

启动小娜的专利申请信息管理系统，提供完整的信息录入、查询、统计功能

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_dependencies() -> bool:
    """检查依赖包"""
    required_packages = [
        'streamlit',
        'pandas',
        'openpyxl',
        'python-docx'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("🔧 正在安装依赖包...")

        for package in missing_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                             check=True, capture_output=True)
                print(f"✅ 成功安装 {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 安装 {package} 失败: {e}")
                return False

        print("🎉 所有依赖包安装完成!")
    else:
        print("✅ 所有依赖包已安装")

    return True

def init_database() -> Any:
    """初始化数据库"""
    try:
        from core.data.patent_application_management_system import PatentApplicationDatabase

        print("🔧 正在初始化专利申请数据库...")
        db = PatentApplicationDatabase()

        # 生成统计信息
        stats = db.generate_statistics()

        print("✅ 数据库初始化完成")
        print(f"📊 当前申请总数: {stats['total_applications']}")
        print(f"📈 数据库路径: {db.db_path}")

        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def process_sunjunxia_application() -> Any | None:
    """处理孙俊霞的专利申请"""
    try:
        from core.data.patent_application_management_system import (
            ApplicantInfo,
            FeeDetails,
            InventorInfo,
            PatentApplication,
            PatentApplicationDatabase,
        )

        print("🔍 正在处理孙俊霞的专利申请...")

        db = PatentApplicationDatabase()

        # 检查是否已有申请记录
        existing_apps = db.search_applications(patent_name="农作物幼苗培育保护罩")

        if existing_apps:
            print("✅ 找到现有申请记录")
            for app in existing_apps:
                print(f"  - 申请ID: {app.patent_id}")
                print(f"  - 专利名称: {app.patent_name}")
                print(f"  - 申请状态: {app.application_status}")
                return True
        else:
            print("📝 创建新的申请记录...")

            # 创建基础申请记录（信息待补充）
            application = PatentApplication(
                patent_name="农作物幼苗培育保护罩",
                patent_type="实用新型",
                application_date="2025-12-17",
                contact_person="孙俊霞",
                contact_phone="待补充",
                application_status="准备中",
                technical_field="农业种植技术",
                created_by="小娜系统",
                notes="需要从确认书中提取关键信息：申请人身份证号、地址、电话、费用明细等"
            )

            # 添加基础申请人信息
            application.applicants.append(ApplicantInfo(
                name="孙俊霞",
                id_type="身份证",
                id_number="待从确认书提取",
                address="待从确认书提取",
                postal_code="待从确认书提取",
                phone="待从确认书提取",
                organization_type="个人"
            ))

            # 添加发明人信息
            application.inventors.append(InventorInfo(
                name="孙俊霞",
                id_number="待从确认书提取",
                sequence=1,
                professional_title="基层农业技术推广专家"
            ))

            # 设置基础费用信息
            application.fee_details = FeeDetails(
                application_fee=500.0,
                examination_fee=0.0,
                printing_fee=50.0,
                certificate_fee=200.0,
                agency_fee=0.0,  # 待确认
                total_amount=750.0,  # 待更新
                payment_status="未支付"
            )

            # 保存到数据库
            patent_id = db.save_patent_application(application)

            print(f"✅ 申请记录已创建: {patent_id}")

            # 添加文档记录
            confirmation_form_path = "/Users/xujian/Nutstore Files/工作/孙俊霞1件/专利申请确认表(2).doc"
            if Path(confirmation_form_path).exists():
                db.add_document(
                    patent_id=patent_id,
                    document_type="专利申请确认书",
                    document_name="专利申请确认表(2).doc",
                    file_path=confirmation_form_path,
                    uploaded_by="小娜系统",
                    notes="需要提取关键信息：申请人身份信息、联系方式、费用明细"
                )
                print("✅ 确认书文档已添加到档案")

            return True

    except Exception as e:
        print(f"❌ 处理孙俊霞申请失败: {e}")
        return False

def start_web_interface() -> Any:
    """启动Web界面"""
    try:
        print("🌐 正在启动专利申请管理系统Web界面...")

        # 设置Streamlit配置
        os.environ['STREAMLIT_SERVER_PORT'] = '8502'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'

        # 启动Streamlit应用
        script_path = project_root / "core/data/patent_application_ui.py"

        print(f"📍 启动路径: {script_path}")
        print("🚀 Web界面启动中...")
        print("📱 访问地址: http://localhost:8502")
        print("⏹️  按 Ctrl+C 停止服务")

        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(script_path)
        ])

    except KeyboardInterrupt:
        print("\n👋 系统已停止")
    except Exception as e:
        print(f"❌ 启动Web界面失败: {e}")

def main() -> None:
    """主函数"""
    print("=" * 80)
    print("📋" + " " * 25 + "小娜专利申请管理系统" + " " * 25 + "📋")
    print("=" * 80)
    print(f"🕐 启动时间: {sys.modules['datetime'].datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👩‍⚖️ 操作者: 小娜·天秤女神 (专利法律专家)")
    print("🎯 功能目标: 统一管理专利申请信息，支持信息录入、查询、统计")
    print("=" * 80)

    # 检查依赖
    print("\n🔧 步骤1: 检查系统依赖")
    if not check_dependencies():
        print("❌ 依赖检查失败，请手动安装缺失的包")
        return

    # 初始化数据库
    print("\n💾 步骤2: 初始化数据库")
    if not init_database():
        print("❌ 数据库初始化失败")
        return

    # 处理孙俊霞的申请
    print("\n📝 步骤3: 处理孙俊霞专利申请")
    if not process_sunjunxia_application():
        print("❌ 处理申请失败")
        return

    # 显示系统使用说明
    print("\n📖 系统使用说明:")
    print("1. 🆕 新建申请: 录入新的专利申请信息")
    print("2. 🔍 申请查询: 搜索和查看现有申请记录")
    print("3. 📊 统计分析: 查看申请统计数据和趋势")
    print("4. 📁 文档管理: 上传和管理申请相关文档")
    print("5. 📤 数据导出: 导出申请数据到Excel/CSV/JSON")

    print("\n⚠️  特别提醒:")
    print("- 孙俊霞的确认书文档已存储，但需要手动录入关键信息")
    print("- 请访问Web界面完善申请人身份信息、联系方式和费用明细")
    print("- 系统会自动保存所有录入的信息")

    # 启动Web界面
    print("\n🚀 步骤4: 启动Web管理界面")
    start_web_interface()

if __name__ == "__main__":
    main()
