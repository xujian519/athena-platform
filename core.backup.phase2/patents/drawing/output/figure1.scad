// OpenSCAD 公共模块定义
// 自动生成于: 2026-02-26 15:15:59

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
