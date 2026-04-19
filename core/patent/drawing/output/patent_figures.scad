// 专利附图完整生成脚本
// 自动从专利说明书解析并生成
// 生成日期: 2026-02-26 14:56:46.720101

// 模块化附图生成
include <builtins.scad>

// ============ 附图生成配置 ============
// 颜色主题
color_primary = [33, 150, 243]/255;
color_success = [76, 175, 80]/255;
color_warning = [255, 193, 7]/255;
color_danger = [211, 47, 47]/255;

// 全局设置
$fn = 40;
$fs = 0.5;
$fa = 5;

// ============ 图1：整体结构示意图 ============
// 图1: 整体结构示意图 - OpenSCAD脚本
// 自动生成自专利说明书

$fn=40;  // 细节精度

// 颜色定义
color_pipe = [139, 69, 83]/255;      // 棕色 #8B4513
color_green = [76, 175, 80]/255;     // 绿色 #4CAF50
color_blue = [33, 150, 243]/255;     // 蓝色 #2196F3
color_orange = [255, 193, 7]/255;    // 橙色 #FFC107
color_purple = [156, 39, 176]/255;    // 紫色 #9C27B0
color_teal = [0, 150, 136]/255;      // 青色 #009688
color_red = [211, 47, 47]/255;       // 红色 #F44336
color_gray = [96, 125, 139]/255;     // 灰色 #607D8B
color_light_blue = [227, 242, 253]/255; // 浅蓝 #E3F2FD

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

// 信号调理电路模块
module signal_circuit() {
    color(color_orange)
    cube([10, 8, 3], center=true);
}

// 分布式采集模块
module distributed_collection() {
    box_size = [60, 25, 15];
    color(color_light_blue)
        translate([0, 0, 0])
        rounded_box(box_size, radius=2, center=false);
    // 标签
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
module arrow_3d(length=30, arrow_size=5) {
    cylinder(h=length, r1=arrow_size/2, r2=arrow_size, center=false);
    translate([0, length, 0])
        sphere(r=arrow_size);
}

module connection_arrow(from, to, label="") {
    direction = to - from;
    length = norm(direction);
    arrow_size = 3;

    color([85, 85, 85]/255)
        rotate([0, 0, atan2(direction.y, direction.x)])
        cylinder(h=length-arrow_size, r=1, center=false);
    translate(to)
        sphere(r=arrow_size);
}

// ============ 主组装 ============

module Figure1_Structure() {
    echo("生成图1: 整体结构示意图...");

    // 供热管道（底部）
    translate([0, 0, 0])
        pipe_module(length=200);

    // 采集点（沿管道分布）
    for (x = [20, 40, 60, 80, 100, 120, 140, 160]) {
        translate([x, 6, 4])
            collection_point(id_num=x/20);
        // 连接线
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

// 生成图1
Figure1_Structure();


// ============ 图2：噪声滤波电路原理图 ============
// 图2: 噪声滤波电路原理图 - OpenSCAD脚本
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
    // 标签
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
    // 符号
    translate([3, 5, 0.1])
        color("black")
        text("-", size=10);
    translate([3, 10, 0.1])
        color("black")
        text("+", size=10);
}

// 连接线
module wire(from, to, label="") {
    color("black")
        hull() {
            translate(from)
                cylinder(r=0.3, h=0.1, center=false);
            translate(to)
                cylinder(r=0.3, h=0.1, center=false);
        }
}

// ============ 主电路 ============

module Figure2_Circuit() {
    echo("生成图2: 噪声滤波电路原理图...");

    // 位置定义
    pos_input = [0, 50];
    pos_stage1_out = [40, 50];
    pos_stage2_out = [90, 50];
    pos_output = [140, 50];

    // 输入端
    translate(pos_input)
        color([179, 229, 252]/255)
        circle(r=8);
    translate(pos_input)
        color("black")
        text("输入\nVin", size=10, halign="center", valign="center");
    translate(pos_input + [0, -15, 0])
        color("black")
        text("来自分布式\n采集模块", size=8, halign="center");

    // 第一级：高阻抗输入缓冲级
    translate(pos_stage1_out)
        module_box(width=50, height=40, color_val=[200, 230, 201]/255,
                   label1="高阻抗输入", label2="缓冲级21");

    // 运放符号
    translate([60, 40, 0])
        opamp_symbol();

    // 第二级：工频陷波级
    translate(pos_stage2_out)
        module_box(width=50, height=40, color_val=[255, 224, 178]/255,
                   label1="工频陷波", label2="级22");

    // 双T符号
    translate([110, 50, 0]) {
        for (i = [0:3]) {
            translate([0, 6-i*4, 0])
                cube([6, 4, 2], center=false);
        }
    }

    // 第三级：低通滤波级
    translate([140, 50])
        module_box(width=50, height=40, color_val=[225, 179, 229]/255,
                   label1="低通滤波", label2="级23");

    // 输出端
    translate([180, 50])
        color([200, 230, 201]/255)
        circle(r=8);
    translate([180, 50])
        color("black")
        text("输出\nVout", size=10, halign="center", valign="center");
}

Figure2_Circuit();


// ============ 图3：自动校准流程图 ============
// 图3: 自动校准流程图 - OpenSCAD脚本
// 使用方块流程图展示自动校准过程

$fn=40;

// 颜色定义
color_blue = [33, 150, 243]/255;
color_green = [76, 175, 80]/255;
color_orange = [255, 193, 7]/255;
color_purple = [156, 39, 176]/255;
color_red = [211, 47, 47]/255;

// 流程节点
module flow_node(type, label, detail="") {
    size = [30, 20];
    positions = [
        [0, 80],   // 开始/结束
        [0, 65],   // 判断
        [0, 50],   // 处理
        [0, 35],   // 处理
    ];

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
            rounded_box(size, radius=3, center=false);
    }

    // 标签
    translate([0, 0, 0.1])
        color("black")
        text(label, size=8, halign="center", valign="center", $fn=35);
}

// 箭头
module flow_arrow() {
    color([85, 85, 85]/255)
        cylinder(h=10, r=1, center=false);
    translate([0, 10, 0])
        cylinder(h=3, r1=1, r2=2, center=false);
}

// ============ 流程图组装 ============

module Figure3_Flowchart() {
    echo("生成图3: 自动校准流程图...");

    // 主流程节点
    // 开始
    translate([75, 100])
        flow_node("start", "开始", "系统初始化");

    // 判断
    translate([75, 80])
        flow_node("decision", "是否\n触发?");

    // 零点校准
    translate([75, 55])
        flow_node("process", "零点校准", "输入接地\n采集V_zero");

    // 计算偏移
    translate([75, 40])
        flow_node("process", "计算零点偏移", "offset=V_zero");

    // 增益校准
    translate([75, 25])
        flow_node("process", "增益校准", "输入标准\n采集V_std");

    // 结束
    translate([75, 10])
        flow_node("end", "结束", "等待下次\n校准");

    // 连接箭头（简化）
    flow_arrows = [
        [[75, 88], [75, 80]],  // 开始 -> 判断
        [[75, 72], [75, 65]],  // 判断 -> 零点校准
        [[75, 45], [75, 40]],  // 零点校准 -> 计算偏移
        [[75, 30], [75, 25]],  // 计算偏移 -> 增益校准
        [[75, 15], [75, 10]],  // 增益校准 -> 结束
    ];

    for (arrow = flow_arrows) {
        translate([arrow[0].x, arrow[0].y, 0])
            rotate([0, 0, 90])
            cylinder(h=arrow[1].y-arrow[0].y-3, r=0.8, center=false);
    }
}

Figure3_Flowchart();


// ============ 图4：分布式采集布置示意图 ============
// 图4: 分布式采集布置示意图 - OpenSCAD脚本
// 展示管道沿线采集点的空间布置

$fn=40;

// 颜色定义
color_pipe = [139, 69, 83]/255;      // 棕色
color_green = [76, 175, 80]/255;     // 绿色
color_soil = [215, 204, 200]/255;    // 土壤色
color_grass = [76, 175, 80]/255;     // 草地色
color_blue = [33, 150, 243]/255;     // 蓝色
color_line = [25, 118, 210]/255;     // 线条色

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

// ============ 布局组装 ============

module Figure4_Layout() {
    echo("生成图4: 分布式采集布置示意图...");

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

Figure4_Layout();
