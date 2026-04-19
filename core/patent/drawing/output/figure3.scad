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
        flow_node("decision", "是否\n触发?");

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
