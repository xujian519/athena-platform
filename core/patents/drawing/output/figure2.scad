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
        text("输入\nVin", size=10, halign="center", valign="center");
    translate([0, 35])
        color("black")
        text("来自分布式\n采集模块", size=8, halign="center");

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
        text("输出\nVout", size=10, halign="center", valign="center");
}

main();
