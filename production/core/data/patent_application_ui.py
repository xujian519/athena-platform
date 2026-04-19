from __future__ import annotations
from dataclasses import asdict

#!/usr/bin/env python3
"""
专利申请信息管理界面
Patent Application Information Management UI

为专利申请信息管理系统提供Web界面,支持信息录入、查询、编辑等功能

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from core.data.patent_application_management_system import (
    ApplicantInfo,
    FeeDetails,
    InventorInfo,
    PatentApplication,
    PatentApplicationDatabase,
    PatentApplicationExtractor,
)


class PatentApplicationUI:
    """专利申请管理界面"""

    def __init__(self):
        self.db = PatentApplicationDatabase()
        self.extractor = PatentApplicationExtractor(self.db)

    def run(self) -> None:
        """运行主界面"""
        st.set_page_config(page_title="专利申请信息管理系统", page_icon="📋", layout="wide")

        st.title("📋 专利申请信息管理系统")
        st.markdown("---")

        # 侧边栏导航
        with st.sidebar:
            st.title("功能菜单")
            page = st.selectbox(
                "选择功能", ["新建申请", "申请查询", "统计分析", "文档管理", "数据导出"]
            )

        if page == "新建申请":
            self._new_application_page()
        elif page == "申请查询":
            self._search_application_page()
        elif page == "统计分析":
            self._statistics_page()
        elif page == "文档管理":
            self._document_management_page()
        elif page == "数据导出":
            self._export_page()

    def _new_application_page(self) -> Any:
        """新建申请页面"""
        st.header("📝 新建专利申请")

        with st.form("patent_application_form"):
            st.subheader("基本信息")
            col1, col2 = st.columns(2)

            with col1:
                patent_name = st.text_input("专利名称*", value="农作物幼苗培育保护罩")
                patent_type = st.selectbox("专利类型*", ["实用新型", "发明", "外观设计"])
                application_date = st.date_input("申请日期*", datetime.now())
                contact_person = st.text_input("联系人姓名*", value="孙俊霞")

            with col2:
                contact_phone = st.text_input("联系电话*", value="")
                contact_email = st.text_input("联系邮箱")
                technical_field = st.text_input("技术领域", value="农业种植技术")
                priority_date = st.date_input("优先权日期 (可选)")

            st.subheader("申请人信息")
            applicant_name = st.text_input("申请人名称*", value="孙俊霞")
            col3, col4 = st.columns(2)
            with col3:
                applicant_id_type = st.selectbox("证件类型", ["身份证", "统一社会信用代码"])
                applicant_id_number = st.text_input("证件号码*")
                applicant_postal_code = st.text_input("邮编*")
            with col4:
                applicant_phone = st.text_input("申请人电话*")
                applicant_email = st.text_input("申请人邮箱")
                organization_type = st.selectbox("机构类型", ["个人", "企业", "科研机构", "高校"])

            applicant_address = st.text_area("申请地址*", height=100)

            st.subheader("发明人信息")
            inventor_count = st.number_input("发明人数量", min_value=1, max_value=10, value=1)

            inventors = []
            for i in range(inventor_count):
                with st.expander(f"发明人 {i+1}"):
                    col5, col6 = st.columns(2)
                    with col5:
                        inventor_name = st.text_input(f"发明人姓名 {i+1}*")
                        inventor_id = st.text_input(f"身份证号 {i+1}*")
                    with col6:
                        inventor_education = st.selectbox(
                            f"学历 {i+1}", ["本科", "硕士", "博士", "其他"]
                        )
                        inventor_title = st.text_input(f"职称 {i+1}")

                    inventor_workplace = st.text_input(f"工作单位 {i+1}")
                    inventor_contribution = st.text_area(f"主要贡献 {i+1}", height=50)

                    if inventor_name and inventor_id:
                        inventors.append(
                            InventorInfo(
                                name=inventor_name,
                                id_number=inventor_id,
                                sequence=i + 1,
                                education=inventor_education,
                                professional_title=inventor_title,
                                workplace=inventor_workplace,
                                contribution=inventor_contribution,
                            )
                        )

            st.subheader("费用明细")
            col7, col8 = st.columns(2)
            with col7:
                application_fee = st.number_input("申请费", min_value=0.0, value=500.0)
                examination_fee = st.number_input("实质审查费", min_value=0.0, value=0.0)
                printing_fee = st.number_input("印刷费", min_value=0.0, value=50.0)
            with col8:
                certificate_fee = st.number_input("证书费", min_value=0.0, value=200.0)
                maintenance_fee = st.number_input("年费", min_value=0.0, value=0.0)
                agency_fee = st.number_input("代理费", min_value=0.0, value=0.0)

            payment_status = st.selectbox("支付状态", ["未支付", "已支付", "部分支付"])

            # 自动计算总费用
            total_fee = (
                application_fee
                + examination_fee
                + printing_fee
                + certificate_fee
                + maintenance_fee
                + agency_fee
            )
            st.info(f"总费用: ¥{total_fee:.2f}")

            notes = st.text_area("备注信息", height=100)

            submitted = st.form_submit_button("保存申请信息", type="primary")

            if submitted:
                if all(
                    [
                        patent_name,
                        contact_person,
                        contact_phone,
                        applicant_name,
                        applicant_id_number,
                        applicant_phone,
                        applicant_address,
                        applicant_postal_code,
                        inventors,
                    ]
                ):

                    # 创建申请信息
                    application = PatentApplication(
                        patent_name=patent_name,
                        patent_type=patent_type,
                        application_date=application_date.strftime("%Y-%m-%d"),
                        contact_person=contact_person,
                        contact_phone=contact_phone,
                        contact_email=contact_email,
                        technical_field=technical_field,
                        priority_date=priority_date.strftime("%Y-%m-%d") if priority_date else None,
                        inventors=inventors,
                        fee_details=FeeDetails(
                            application_fee=application_fee,
                            examination_fee=examination_fee,
                            printing_fee=printing_fee,
                            certificate_fee=certificate_fee,
                            maintenance_fee=maintenance_fee,
                            agency_fee=agency_fee,
                            total_amount=total_fee,
                            payment_status=payment_status,
                        ),
                        notes=notes,
                        created_by="用户录入",
                    )

                    # 添加申请人信息
                    application.applicants.append(
                        ApplicantInfo(
                            name=applicant_name,
                            id_type=applicant_id_type,
                            id_number=applicant_id_number,
                            address=applicant_address,
                            postal_code=applicant_postal_code,
                            phone=applicant_phone,
                            email=applicant_email,
                            organization_type=organization_type,
                        )
                    )

                    # 保存到数据库
                    patent_id = self.db.save_patent_application(application)
                    st.success(f"申请信息已保存!专利申请ID: {patent_id}")

                    # 显示保存的信息
                    with st.expander("查看保存的信息"):
                        st.json(asdict(application))
                else:
                    st.error("请填写所有必填字段")

    def _search_application_page(self) -> Any:
        """申请查询页面"""
        st.header("🔍 专利申请查询")

        with st.form("search_form"):
            col1, col2 = st.columns(2)
            with col1:
                search_name = st.text_input("专利名称")
                search_type = st.selectbox("专利类型", ["全部", "发明", "实用新型", "外观设计"])
                search_status = st.selectbox(
                    "申请状态", ["全部", "准备中", "已提交", "审查中", "已授权", "已驳回"]
                )
            with col2:
                search_date_from = st.date_input("申请日期从")
                search_date_to = st.date_input("申请日期到")
                search_contact = st.text_input("联系人")

            search_button = st.form_submit_button("搜索", type="primary")

            if search_button:
                search_params = {}
                if search_name:
                    search_params["patent_name"] = search_name
                if search_type != "全部":
                    search_params["patent_type"] = search_type
                if search_status != "全部":
                    search_params["application_status"] = search_status
                if search_contact:
                    search_params["contact_person"] = search_contact
                if search_date_from:
                    search_params["application_date_from"] = search_date_from.strftime("%Y-%m-%d")
                if search_date_to:
                    search_params["application_date_to"] = search_date_to.strftime("%Y-%m-%d")

                applications = self.db.search_applications(**search_params)

                if applications:
                    st.success(f"找到 {len(applications)} 个申请记录")

                    # 创建数据表格
                    data = []
                    for app in applications:
                        data.append(
                            {
                                "专利申请ID": app.patent_id,
                                "专利名称": app.patent_name,
                                "专利类型": app.patent_type,
                                "申请日期": app.application_date,
                                "联系人": app.contact_person,
                                "联系电话": app.contact_phone,
                                "申请状态": app.application_status,
                                "创建时间": app.created_at,
                            }
                        )

                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)

                    # 详细信息查看
                    st.subheader("详细信息")
                    selected_app_id = st.selectbox(
                        "选择申请查看详情",
                        options=[app.patent_id for app in applications],
                        format_func=lambda x: f"{x} - {next(app.patent_name for app in applications if app.patent_id == x)}",
                    )

                    if selected_app_id:
                        selected_app = next(
                            app for app in applications if app.patent_id == selected_app_id
                        )
                        self._display_application_details(selected_app)
                else:
                    st.warning("未找到符合条件的申请记录")

    def _display_application_details(self, application: PatentApplication) -> Any:
        """显示申请详细信息"""
        tabs = st.tabs(["基本信息", "申请人信息", "发明人信息", "费用信息", "文档档案"])

        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**专利申请ID**:", application.patent_id)
                st.write("**专利名称**:", application.patent_name)
                st.write("**专利类型**:", application.patent_type)
                st.write("**申请日期**:", application.application_date)
                st.write("**申请号**:", application.application_number or "未分配")
                st.write("**联系人**:", application.contact_person)
                st.write("**联系电话**:", application.contact_phone)
            with col2:
                st.write("**联系邮箱**:", application.contact_email or "未填写")
                st.write("**申请状态**:", application.application_status)
                st.write("**优先权日期**:", application.priority_date or "无")
                st.write("**技术领域**:", application.technical_field or "未填写")
                st.write("**创建时间**:", application.created_at)
                st.write("**创建人**:", application.created_by)

            if application.abstract:
                st.write("**摘要**:")
                st.write(application.abstract)

            if application.keywords:
                st.write("**关键词**:", ", ".join(application.keywords))

            if application.notes:
                st.write("**备注**:")
                st.write(application.notes)

        with tabs[1]:
            if application.applicants:
                for i, applicant in enumerate(application.applicants, 1):
                    st.subheader(f"申请人 {i}")
                    col3, col4 = st.columns(2)
                    with col3:
                        st.write("**姓名**:", applicant.name)
                        st.write("**证件类型**:", applicant.id_type)
                        st.write("**证件号码**:", applicant.id_number)
                        st.write("**电话**:", applicant.phone)
                    with col4:
                        st.write("**邮箱**:", applicant.email or "未填写")
                        st.write("**邮编**:", applicant.postal_code)
                        st.write("**机构类型**:", applicant.organization_type)
                    st.write("**地址**:", applicant.address)
                    st.markdown("---")
            else:
                st.info("暂无申请人信息")

        with tabs[2]:
            if application.inventors:
                for i, inventor in enumerate(application.inventors, 1):
                    st.subheader(f"发明人 {i}")
                    col5, col6 = st.columns(2)
                    with col5:
                        st.write("**姓名**:", inventor.name)
                        st.write("**身份证号**:", inventor.id_number)
                        st.write("**排序**:", inventor.sequence)
                    with col6:
                        st.write("**学历**:", inventor.education or "未填写")
                        st.write("**职称**:", inventor.professional_title or "未填写")
                        st.write("**工作单位**:", inventor.workplace or "未填写")
                    if inventor.contribution:
                        st.write("**主要贡献**:", inventor.contribution)
                    st.markdown("---")
            else:
                st.info("暂无发明人信息")

        with tabs[3]:
            if application.fee_details:
                fee = application.fee_details
                col7, col8 = st.columns(2)
                with col7:
                    st.metric("申请费", f"¥{fee.application_fee:.2f}")
                    st.metric("实质审查费", f"¥{fee.examination_fee:.2f}")
                    st.metric("印刷费", f"¥{fee.printing_fee:.2f}")
                    st.metric("证书费", f"¥{fee.certificate_fee:.2f}")
                with col8:
                    if fee.maintenance_fee:
                        st.metric("年费", f"¥{fee.maintenance_fee:.2f}")
                    if fee.agency_fee:
                        st.metric("代理费", f"¥{fee.agency_fee:.2f}")
                    st.metric("总费用", f"¥{fee.total_amount:.2f}")
                    st.metric("支付状态", fee.payment_status)

                if fee.other_fees:
                    st.write("**其他费用**:")
                    for name, amount in fee.other_fees.items():
                        st.write(f"- {name}: ¥{amount:.2f}")
            else:
                st.info("暂无费用信息")

        with tabs[4]:
            documents = self.db.get_documents(application.patent_id)
            if documents:
                for doc in documents:
                    st.subheader(doc["document_name"])
                    col9, col10 = st.columns(2)
                    with col9:
                        st.write("**文档类型**:", doc["document_type"])
                        st.write("**文件路径**:", doc["file_path"])
                        if doc["file_size"]:
                            st.write("**文件大小**:", f"{doc['file_size']} bytes")
                    with col10:
                        st.write("**上传时间**:", doc["upload_time"])
                        st.write("**上传人**:", doc["uploaded_by"] or "未知")
                    if doc["notes"]:
                        st.write("**备注**:", doc["notes"])
                    st.markdown("---")
            else:
                st.info("暂无文档档案")

    def _statistics_page(self) -> Any:
        """统计分析页面"""
        st.header("📊 统计分析")

        stats = self.db.generate_statistics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总申请数", stats["total_applications"])
        with col2:
            if stats["type_distribution"]:
                st.metric("发明专利", stats["type_distribution"].get("发明", 0))
        with col3:
            if stats["type_distribution"]:
                st.metric("实用新型", stats["type_distribution"].get("实用新型", 0))
        with col4:
            st.metric("总费用", f"¥{stats['total_fees']:.2f}")

        if stats["type_distribution"]:
            st.subheader("专利类型分布")
            type_df = pd.DataFrame(
                list(stats["type_distribution"].items()), columns=["专利类型", "数量"]
            )
            st.bar_chart(type_df.set_index("专利类型"))

        if stats["status_distribution"]:
            st.subheader("申请状态分布")
            status_df = pd.DataFrame(
                list(stats["status_distribution"].items()), columns=["申请状态", "数量"]
            )
            st.bar_chart(status_df.set_index("申请状态"))

    def _document_management_page(self) -> Any:
        """文档管理页面"""
        st.header("📁 文档管理")

        patent_id = st.text_input("输入专利申请ID")

        if patent_id:
            application = self.db.get_patent_application(patent_id)
            if application:
                st.success(f"找到申请: {application.patent_name}")

                # 文件上传
                uploaded_file = st.file_uploader(
                    "上传申请文档", type=["pdf", "doc", "docx", "jpg", "png"]
                )

                if uploaded_file:
                    document_type = st.selectbox(
                        "文档类型", ["确认书", "技术交底书", "说明书", "附图", "其他"]
                    )
                    document_name = st.text_input("文档名称", value=uploaded_file.name)
                    notes = st.text_area("备注")

                    if st.button("保存文档"):
                        # 保存文件
                        save_path = Path("/tmp") / f"{patent_id}_{uploaded_file.name}"
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        self.db.add_document(
                            patent_id=patent_id,
                            document_type=document_type,
                            document_name=document_name,
                            file_path=str(save_path),
                            uploaded_by="用户上传",
                            notes=notes,
                        )
                        st.success("文档已保存")

                # 显示已有文档
                documents = self.db.get_documents(patent_id)
                if documents:
                    st.subheader("已有文档")
                    for doc in documents:
                        st.write(f"- {doc['document_name']} ({doc['document_type']})")
            else:
                st.error("未找到该专利申请")

    def _export_page(self) -> Any:
        """数据导出页面"""
        st.header("📤 数据导出")

        export_format = st.selectbox("导出格式", ["Excel", "CSV", "JSON"])

        if st.button("导出所有申请数据"):
            # 获取所有申请数据
            applications = self.db.search_applications()

            if applications:
                data = []
                for app in applications:
                    data.append(
                        {
                            "专利申请ID": app.patent_id,
                            "专利名称": app.patent_name,
                            "专利类型": app.patent_type,
                            "申请日期": app.application_date,
                            "申请人": ", ".join([a.name for a in app.applicants]),
                            "发明人": ", ".join([i.name for i in app.inventors]),
                            "联系人": app.contact_person,
                            "联系电话": app.contact_phone,
                            "申请状态": app.application_status,
                            "总费用": app.fee_details.total_amount if app.fee_details else 0,
                            "创建时间": app.created_at,
                        }
                    )

                df = pd.DataFrame(data)

                if export_format == "Excel":
                    excel_data = df.to_excel(index=False, engine="openpyxl")
                    st.download_button(
                        label="下载Excel文件",
                        data=excel_data,
                        file_name=f"patent_applications_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                elif export_format == "CSV":
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="下载CSV文件",
                        data=csv_data,
                        file_name=f"patent_applications_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )
                else:  # JSON
                    json_data = json.dumps(data, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="下载JSON文件",
                        data=json_data,
                        file_name=f"patent_applications_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                    )
            else:
                st.warning("暂无数据可导出")


def main() -> None:
    """主函数"""
    ui = PatentApplicationUI()
    ui.run()


if __name__ == "__main__":
    main()
