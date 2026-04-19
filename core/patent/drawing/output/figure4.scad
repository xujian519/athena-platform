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
