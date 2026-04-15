#!/usr/bin/env python3
from __future__ import annotations
"""
专利制图系统 - OpenSCAD脚本生成器 V2
修复版：添加rounded_box模块定义，避免变量冲突
"""

import os
import re
from datetime import datetime
from typing import Any


class OpenSCADGeneratorV2:
    """OpenSCAD脚本生成器 V2 - 修复版"""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(self.base_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)

    def get_common_header(self) -> str:
        """获取通用头部，包含rounded_box定义"""
        return '''// OpenSCAD 公共模块定义
// 自动生成于: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''

$fn = 40;  // 细节精度

// 圆角长方体模块
module rounded_box(size, radius=2, center=false) {
    if (center) {
        translate([-size.x/2, -size.y/2, -size.z/2])
            rounded_box_centered(size, radius);
    } else {
        rounded_box_centered(size, radius);
    }
}

module rounded_box_centered(size, radius) {
    x = size.x;
    y = size.y;
    z = size.z;
    r = min(radius, min(x, y, z) / 2);

    hull() {
        translate([r, r, r]) sphere(r=r);
        translate([x-r, r, r]) sphere(r=r);
        translate([r, y-r, r]) sphere(r=r);
        translate([x-r, y-r, r]) sphere(r=r);
        translate([r, r, z-r]) sphere(r=r);
        translate([x-r, r, z-r]) sphere(r=r);
        translate([r, y-r, z-r]) sphere(r=r);
        translate([x-r, y-r, z-r]) sphere(r=r);
    }
}

'''

    def parse_specification(self, spec_file: str) -> dict[str, Any]:
        """解析说明书文件，提取附图信息"""
        with open(spec_file, encoding='utf-8') as f:
            content = f.read()

        figures_info = {
            'title': '',
            'figures': []
        }

        # 提取发明名称
        for line in content.split('\n'):
            if '发明名称' in line and line.startswith('##'):
                idx = content.index(line)
                for next_line in content.split('\n')[idx+1:idx+5]:
                    if next_line.strip():
                        figures_info['title'] = next_line.strip().replace('**', '')
                        break
                break

        # 提取附图说明
        in_figure_section = False
        current_figure = None

        for line in content.split('\n'):
            if '附图说明' in line and line.startswith('##'):
                in_figure_section = True
                continue

            if in_figure_section:
                # 检测附图编号
                if line.startswith('图') and '本实用新型' in line:
                    match = re.match(r'图(\d+)[（\(](.*?)[）)]', line)
                    if match:
                        fig_num = match.group(1)
                        fig_desc = match.group(2)
                        current_figure = {
                            'number': fig_num,
                            'description': fig_desc,
                            'details': []
                        }
                        figures_info['figures'].append(current_figure)

        return figures_info

    def generate_figure1_structure(self) -> str:
        """生成图1：整体结构示意图"""
        script = self.get_common_header() + '''
// ============ 图1：整体结构示意图 ============
// 专利: 供热管道阴极保护系统用电位采集优化装置

$fn=40;  // 细节精度

// 颜色定义
color_pipe = [139, 69, 83]/255;      // 棕色
color_green = [76, 175, 80]/255;     // 绿色
color_blue = [33, 150, 243]/255;     // 蓝色
color_orange = [255, 193, 7]/255;    // 橙色
color_purple = [156, 39, 176]/255;   // 紫色
color_teal = [0, 150, 136]/255;      // 青色
color_red = [211, 47, 47]/255;       // 红色
color_gray = [96, 125, 139]/255;     // 灰色
color_light_blue = [227, 242, 253]/255; // 浅蓝

// 管道模块
module pipe_module(length=200, diameter=8) {
    color(color_pipe)
    cylinder(h=length, d=diameter, center=true);
}

// 采集点模块
module collection_point(id_num=1) {
    color(color_green)
    sphere(r=6);
    // ID标签
    translate([0, 12, 0])
        color("black")
        text(str(id_num), size=8, halign="center", valign="center");
}

// 分布式采集模块
module distributed_collection() {
    box_size = [60, 25, 15];
    color(color_light_blue)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 15, 7])
        color("black")
        text("分布式采集模块1", size=10, halign="center", valign="center");
    translate([0, 10, 7])
        color("black")
        text("4-16个采集点", size=6, halign="center", valign="center");
}

// 噪声滤波电路模块
module noise_filter_circuit() {
    box_size = [60, 25, 15];
    color([255, 243, 224]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 15, 7])
        color("black")
        text("噪声滤波电路2", size=10, halign="center", valign="center");
    translate([0, 10, 7])
        color("black")
        text("三级滤波", size=6, halign="center", valign="center");
}

// 自动校准模块
module auto_calibration() {
    box_size = [50, 25, 15];
    color([243, 229, 245]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 15, 7])
        color("black")
        text("自动校准3", size=10, halign="center", valign="center");
    translate([0, 10, 7])
        color("black")
        text("1小时周期", size=6, halign="center", valign="center");
}

// 温度补偿模块
module temperature_compensation() {
    box_size = [50, 25, 15];
    color([232, 245, 233]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 15, 7])
        color("black")
        text("温度补偿4", size=10, halign="center", valign="center");
    translate([0, 10, 7])
        color("black")
        text("-20~60℃", size=6, halign="center", valign="center");
}

// 数据处理模块
module data_processing() {
    box_size = [50, 25, 15];
    color([225, 241, 254]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 15, 7])
        color("black")
        text("数据处理5", size=10, halign="center", valign="center");
    translate([0, 10, 7])
        color("black")
        text("数字滤波", size=6, halign="center", valign="center");
}

// 数据传输模块
module data_transmission() {
    box_size = [50, 25, 15];
    color([254, 235, 238]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 15, 7])
        color("black")
        text("数据传输6", size=10, halign="center", valign="center");
    translate([0, 10, 7])
        color("black")
        text("RS485/LoRa", size=6, halign="center", valign="center");
}

// 云平台模块
module cloud_platform() {
    box_size = [80, 30, 20];
    color([236, 239, 241]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=3, center=false);
    translate([0, 18, 10])
        color("black")
        text("上位机/云平台8", size=12, halign="center", valign="center");
}

// 连接箭头
module connection_arrow(from, to) {
    direction = to - from;
    length = norm(direction);
    arrow_size = 3;
    color([85, 85, 85]/255)
        rotate([0, 0, atan2(direction.y, direction.x)])
        cylinder(h=length-arrow_size, r=1, center=false);
    translate(to)
        sphere(r=arrow_size);
}

// 主组装
module main() {
    // 供热管道（底部）
    translate([0, 0, 0])
        pipe_module(length=200);

    // 采集点（沿管道分布）
    for (x = [20, 40, 60, 80, 100, 120, 140, 160]) {
        translate([x, 6, 4])
            collection_point(id_num=x/20);
        color([100, 100, 100]/255, 0.3)
            translate([x, 0, 0])
            cylinder(h=6, r=0.3);
    }

    // 功能模块层
    z_level = 20;

    // 第一层：采集和滤波
    translate([25, 30, z_level])
        distributed_collection();
    translate([85, 30, z_level])
        noise_filter_circuit();
    translate([145, 30, z_level])
        auto_calibration();

    // 第二层：补偿和处理
    translate([25, 70, z_level])
        temperature_compensation();
    translate([75, 70, z_level])
        data_processing();
    translate([125, 70, z_level])
        data_transmission();

    // 第三层：云平台
    translate([75, 110, z_level+10])
        cloud_platform();
}

main();
'''
        return script

    def generate_figure2_circuit(self) -> str:
        """生成图2：噪声滤波电路原理图"""
        script = self.get_common_header() + '''
// ============ 图2：噪声滤波电路原理图 ============
// 展示三级滤波结构的电路框图

$fn=40;

// 颜色定义
color_green = [76, 175, 80]/255;
color_orange = [255, 193, 7]/255;
color_purple = [156, 39, 176]/255;
color_gray = [96, 125, 139]/255;
color_blue = [33, 150, 243]/255;

// 模块框
module module_box(width, height, color_val, label1, label2="") {
    color(color_val)
        translate([0, 0, 0])
        rounded_box([width, height, 8], radius=1, center=false);
    translate([0, height/2+2, 4])
        color("black")
        text(label1, size=9, halign="center", valign="center");
    if (label2 != "") {
        translate([0, height/2-2, 4])
            color("black")
            text(label2, size=6, halign="center", valign="center");
    }
}

// 运放符号
module opamp_symbol() {
    color("white")
        polygon([[0, 0], [0, 15], [12, 7.5]]);
    translate([3, 5, 0.1])
        color("black")
        text("-", size=10);
    translate([3, 10, 0.1])
        color("black")
        text("+", size=10);
}

// 连接线
module wire(from, to) {
    color("black")
        hull() {
            translate(from)
                cylinder(r=0.3, h=0.1, center=false);
            translate(to)
                cylinder(r=0.3, h=0.1, center=false);
        }
}

// 主电路
module main() {
    // 输入端
    translate([0, 50])
        color([179, 229, 252]/255)
        circle(r=8);
    translate([0, 50])
        color("black")
        text("输入\\nVin", size=10, halign="center", valign="center");
    translate([0, 35])
        color("black")
        text("来自分布式\\n采集模块", size=8, halign="center");

    // 第一级：高阻抗输入缓冲级
    translate([40, 30])
        module_box(width=50, height=40, color_val=[200, 230, 201]/255,
                   label1="高阻抗输入", label2="缓冲级");

    // 运放符号
    translate([60, 40, 0])
        opamp_symbol();

    // 第二级：工频陷波级
    translate([90, 30])
        module_box(width=50, height=40, color_val=[255, 224, 178]/255,
                   label1="工频陷波", label2="级");

    // 双T符号
    translate([110, 50, 0]) {
        for (i = [0:3]) {
            translate([0, 6-i*4, 0])
                cube([6, 4, 2], center=false);
        }
    }

    // 第三级：低通滤波级
    translate([140, 30])
        module_box(width=50, height=40, color_val=[225, 179, 229]/255,
                   label1="低通滤波", label2="级");

    // 输出端
    translate([180, 50])
        color([200, 230, 201]/255)
        circle(r=8);
    translate([180, 50])
        color("black")
        text("输出\\nVout", size=10, halign="center", valign="center");
}

main();
'''
        return script

    def generate_figure3_flowchart(self) -> str:
        """生成图3：自动校准流程图"""
        script = self.get_common_header() + '''
// ============ 图3：自动校准流程图 ============
// 使用方块流程图展示自动校准过程

$fn=40;

// 颜色定义
color_blue = [33, 150, 243]/255;
color_green = [76, 175, 80]/255;
color_orange = [255, 193, 7]/255;

// 流程节点
module flow_node(type, label) {
    if (type == "start" || type == "end") {
        color(color_blue)
            translate([0, 0, 0])
            circle(r=12);
    } else if (type == "decision") {
        color([255, 235, 238]/255)
            translate([0, 0, 0])
            polygon([[0, 15], [15, 7.5], [0, 0]]);
    } else {
        color(color_green)
            translate([0, 0, 0])
            rounded_box([30, 20, 5], radius=3, center=false);
    }
    translate([0, 0, 0.1])
        color("black")
        text(label, size=8, halign="center", valign="center");
}

// 箭头
module flow_arrow(from, to) {
    direction = to - from;
    length = norm(direction);
    color([85, 85, 85]/255)
        rotate([0, 0, atan2(direction.y, direction.x)])
        cylinder(h=length-3, r=0.8, center=false);
    translate(to)
        sphere(r=1.5);
}

// 主流程图
module main() {
    // 节点位置
    pos_start = [75, 100];
    pos_decision = [75, 80];
    pos_zero = [75, 55];
    pos_offset = [75, 40];
    pos_gain = [75, 25];
    pos_end = [75, 10];

    // 开始
    translate(pos_start)
        flow_node("start", "开始");

    // 判断
    translate(pos_decision)
        flow_node("decision", "是否\\n触发?");

    // 零点校准
    translate(pos_zero)
        flow_node("process", "零点校准");

    // 计算偏移
    translate(pos_offset)
        flow_node("process", "计算零点偏移");

    // 增益校准
    translate(pos_gain)
        flow_node("process", "增益校准");

    // 结束
    translate(pos_end)
        flow_node("end", "结束");

    // 连接箭头
    flow_arrow([pos_start[0], pos_start[1]-12], [pos_decision[0], pos_decision[1]+7.5]);
    flow_arrow([pos_decision[0], pos_decision[1]-7.5], [pos_zero[0], pos_zero[1]+10]);
    flow_arrow([pos_zero[0], pos_zero[1]-10], [pos_offset[0], pos_offset[1]+10]);
    flow_arrow([pos_offset[0], pos_offset[1]-10], [pos_gain[0], pos_gain[1]+10]);
    flow_arrow([pos_gain[0], pos_gain[1]-10], [pos_end[0], pos_end[1]+12]);
}

main();
'''
        return script

    def generate_figure4_layout(self) -> str:
        """生成图4：分布式采集布置示意图"""
        script = self.get_common_header() + '''
// ============ 图4：分布式采集布置示意图 ============
// 展示管道沿线采集点的空间布置

$fn=40;

// 颜色定义
color_pipe = [139, 69, 83]/255;      // 棕色
color_green = [76, 175, 80]/255;     // 绿色
color_soil = [215, 204, 200]/255;    // 土壤色
color_grass = [76, 175, 80]/255;     // 草地色
color_blue = [33, 150, 243]/255;     // 蓝色
color_gray = [96, 125, 139]/255;     // 灰色

// 地面模块
module ground_plane() {
    color(color_grass)
        translate([0, 0, -1])
            cube([200, 200, 1], center=false);
}

// 浅土层
module soil_layer() {
    color(color_soil)
        translate([0, 0, -0.5])
            cube([200, 2, 1], center=false);
}

// 供热管道
module heat_pipe(length=180) {
    color(color_pipe)
        rotate([0, 90, 0])
        cylinder(h=length, d=6, center=true);
}

// 采集点模块（含连接）
module collection_point_full(id_num=1) {
    // 地面标记
    color([100, 100, 100]/255)
        translate([0, 0, 0])
            cylinder(h=0.5, r=8, center=false);
    // 参比电极
    color(color_gray)
        translate([0, 0, 0])
            cylinder(h=5, r=1.5);
    // 采集点圆圈
    color(color_green)
        translate([0, 0, 2])
            sphere(r=3);
    // ID标签
    translate([0, 0, 6])
        color("black")
        text(str(id_num), size=8, halign="center", valign="center");
}

// 数据汇聚节点
module data_aggregation() {
    box_size = [30, 20, 12];
    color([255, 249, 196]/255)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    translate([0, 12, 6])
        color("black")
        text("数据汇聚节点", size=9, halign="center", valign="center");
}

// 总线
module data_bus() {
    color(color_blue)
        translate([0, 15, 5])
            cube([180, 2, 1], center=false);
}

// 主布局
module main() {
    // 地面
    ground_plane();
    // 浅土层
    soil_layer();
    // 供热管道
    translate([10, 8, 0])
        heat_pipe();
    // 采集点（8个，沿管道分布）
    positions = [20, 40, 60, 80, 100, 120, 140, 160];
    for (i = [0:7]) {
        translate([positions[i], 8, 0])
            collection_point_full(id_num=i+1);
    }
    // 数据总线
    data_bus();
    // 数据汇聚节点
    translate([90, 50, 0])
        data_aggregation();
    // 覆盖率标注
    translate([90, 80, 1])
        color([46, 125, 50]/255)
            text("管道沿线覆盖率 ≥95%", size=14, halign="center");
}

main();
'''
        return script

    def generate_all_figures(self, spec_file: str) -> dict[str, str]:
        """生成所有附图的独立脚本"""
        print("专利制图系统 V2 - OpenSCAD脚本生成器")
        print("=" * 50)
        print()

        figures = {
            'figure1': self.generate_figure1_structure(),
            'figure2': self.generate_figure2_circuit(),
            'figure3': self.generate_figure3_flowchart(),
            'figure4': self.generate_figure4_layout(),
        }

        # 保存每个图到独立文件
        output_files = {}
        for fig_name, script in figures.items():
            output_file = os.path.join(self.output_dir, f'{fig_name}.scad')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(script)
            output_files[fig_name] = output_file
            print(f"✅ {fig_name}.scad 已生成")

        print()
        print("=" * 50)
        print("所有附图脚本生成完成！")
        print(f"输出目录: {self.output_dir}")
        print()
        print("使用方法:")
        print("1. 在OpenSCAD中打开对应的 .scad 文件")
        print("2. 按F5预览3D模型")
        print("3. 导出为STL/OFF/PNG等格式")
        print()
        print("或者使用命令行渲染:")
        for fig_name, file_path in output_files.items():
            print(f"  openscad {file_path} -o {fig_name}.png --imgsize=1920,1080")

        return output_files

    def render_with_openscad(self, scad_file: str, output_file: str, width=1920, height=1080) -> bool:
        """使用OpenSCAD命令行工具渲染图片"""
        openscad_path = "/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD"

        if not os.path.exists(openscad_path):
            print(f"OpenSCAD未找到: {openscad_path}")
            return False

        cmd = f'{openscad_path} "{scad_file}" -o "{output_file}" --imgsize={width},{height} --autocenter --viewall'
        print(f"执行命令: {cmd}")

        result = os.system(cmd)
        return result == 0

if __name__ == "__main__":
    generator = OpenSCADGeneratorV2()
    spec_file = "/Users/xujian/工作/01_客户管理/01_正式客户/济南东盛热电有限公司/02_专利管理/专利撰写/供热管道阴极保护系统用电位采集优化装置/说明书.md"

    # 生成所有图
    output_files = generator.generate_all_figures(spec_file)

    # 可选：自动渲染PNG
    print()
    print("是否自动渲染PNG图像？(y/n)")
    # 注意：这里需要交互式输入，为了自动化，我们直接渲染

    print()
    print("自动渲染PNG图像...")
    for fig_name, scad_file in output_files.items():
        png_file = os.path.join(generator.output_dir, f'{fig_name}.png')
        print(f"渲染 {fig_name}...")
        if generator.render_with_openscad(scad_file, png_file):
            print(f"  ✅ {fig_name}.png 已生成")
        else:
            print(f"  ❌ {fig_name}.png 渲染失败")
