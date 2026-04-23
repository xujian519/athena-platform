#!/usr/bin/env python3
"""
专利分类向量集合初始化脚本
Initialize Patent Classification Vector Collections

功能:
1. 创建CPC/IPC分类向量集合
2. 预加载分类代码向量
3. 验证向量索引

基于论文#16 PatentSBERTa实现

作者: 小娜·天秤女神
创建时间: 2026-03-20
"""

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# CPC分类代码 (示例)
CPC_CODES = [
    # A部 - 人类生活需要
    {"code": "A01B", "description": "农业或林业的整地；一般的农业用机械或农具的部件、零件或附件", "main_class": "A"},
    {"code": "A01C", "description": "种植；播种；施肥", "main_class": "A"},
    {"code": "A01D", "description": "收获；割草", "main_class": "A"},
    {"code": "A01F", "description": "脱粒；禾草的加工；农业产品的加工；割下材料的堆积", "main_class": "A"},
    {"code": "A01G", "description": "园艺；蔬菜、花卉、稻、果树的栽培", "main_class": "A"},
    {"code": "A01J", "description": "乳品的加工", "main_class": "A"},
    {"code": "A01K", "description": "畜牧业；养鸟业；养蜂业；养鱼业", "main_class": "A"},
    {"code": "A01M", "description": "动物的捕捉、诱捕或惊吓；消灭有害动物或有害植物用的装置", "main_class": "A"},
    {"code": "A01N", "description": "人体、动植物体或其局部的保存；杀生剂", "main_class": "A"},
    {"code": "A21B", "description": "食品烤炉；焙烤用的机械或设备", "main_class": "A"},
    {"code": "A21C", "description": "制作或加工面团的机械或设备；处理由面团制作的焙烤产品", "main_class": "A"},
    {"code": "A21D", "description": "焙烤用面粉或面团的方法；焙烤用添加物", "main_class": "A"},
    {"code": "A22B", "description": "屠宰", "main_class": "A"},
    {"code": "A22C", "description": "肉类、家禽或鱼类的加工", "main_class": "A"},
    {"code": "A23B", "description": "除去冷藏外的食品的保存", "main_class": "A"},
    {"code": "A23C", "description": "乳制品，如奶、黄油、干酪", "main_class": "A"},
    {"code": "A23D", "description": "食用油或脂肪，如人造黄油", "main_class": "A"},
    {"code": "A23F", "description": "咖啡；茶；其代用品；它们的制造、配制或泡制", "main_class": "A"},
    {"code": "A23G", "description": "可可；巧克力；糖果；冰淇淋", "main_class": "A"},
    {"code": "A23K", "description": "饲料", "main_class": "A"},
    {"code": "A23L", "description": "食品、食料或非酒精饮料", "main_class": "A"},
    {"code": "A23N", "description": "其他类不包括的处理大量收获的水果、蔬菜或花球的机械", "main_class": "A"},
    {"code": "A23P", "description": "食品的成形或加工", "main_class": "A"},
    {"code": "A24B", "description": "烟草的制备或加工", "main_class": "A"},
    {"code": "A24C", "description": "雪茄烟；纸烟；烟油滤芯", "main_class": "A"},
    {"code": "A24D", "description": "雪茄或纸烟的烟嘴", "main_class": "A"},
    {"code": "A24F", "description": "吸烟者用品", "main_class": "A"},

    # B部 - 作业；运输
    {"code": "B01B", "description": "沸水的蒸发；蒸发设备", "main_class": "B"},
    {"code": "B01D", "description": "分离", "main_class": "B"},
    {"code": "B01F", "description": "混合，例如，溶解、乳化、分散", "main_class": "B"},
    {"code": "B01J", "description": "化学或物理方法，例如，催化作用或胶体化学", "main_class": "B"},
    {"code": "B01L", "description": "化学或物理实验室用装置", "main_class": "B"},
    {"code": "B02B", "description": "加工谷物", "main_class": "B"},
    {"code": "B02C", "description": "一般的破碎，研磨或粉碎", "main_class": "B"},
    {"code": "B03B", "description": "用液体或用风力摇床或风力跳汰机分离固体物料", "main_class": "B"},
    {"code": "B03C", "description": "从固体物料或流体中分离固体物料的磁或静电分离", "main_class": "B"},
    {"code": "B03D", "description": "浮选", "main_class": "B"},
    {"code": "B04B", "description": "离心机", "main_class": "B"},
    {"code": "B04C", "description": "应用自由旋流的装置，如旋流器", "main_class": "B"},
    {"code": "B05B", "description": "喷射装置；雾化装置；喷嘴", "main_class": "B"},
    {"code": "B05C", "description": "一般对表面涂布液体或其他流体的装置", "main_class": "B"},
    {"code": "B05D", "description": "对表面涂布液体或其他流体的工艺", "main_class": "B"},
    {"code": "B06B", "description": "一般的声学或振动的利用", "main_class": "B"},
    {"code": "B07B", "description": "分离；分级", "main_class": "B"},
    {"code": "B07C", "description": "邮资的盖销或分拣", "main_class": "B"},
    {"code": "B08B", "description": "一般清洁；一般污垢的清除", "main_class": "B"},
    {"code": "B09B", "description": "固体废物的处理", "main_class": "B"},
    {"code": "B09C", "description": "污染的土壤的再生", "main_class": "B"},
    {"code": "B21B", "description": "金属的轧制", "main_class": "B"},
    {"code": "B21C", "description": "用非轧制方式生产金属板、线、棒、管或型材", "main_class": "B"},
    {"code": "B21D", "description": "金属板或管或型材的基本无切削加工或处理", "main_class": "B"},
    {"code": "B21F", "description": "金属丝或金属丝网的加工或处理", "main_class": "B"},

    # C部 - 化学；冶金
    {"code": "C01B", "description": "非金属元素；其化合物", "main_class": "C"},
    {"code": "C01C", "description": "氨；氰；其化合物", "main_class": "C"},
    {"code": "C01D", "description": "碱金属即锂、钠、钾、铷、铯或钫的化合物", "main_class": "C"},
    {"code": "C01F", "description": "金属铍、镁、铝、钙、锶、钡、镭的化合物", "main_class": "C"},
    {"code": "C01G", "description": "含有不包含在C01D或C01F小类中之金属的化合物", "main_class": "C"},
    {"code": "C02F", "description": "水、废水或污水的处理", "main_class": "C"},
    {"code": "C03B", "description": "玻璃、矿棉或渣棉的制造或成型", "main_class": "C"},
    {"code": "C03C", "description": "玻璃、釉或搪瓷釉的化学成分", "main_class": "C"},
    {"code": "C04B", "description": "石灰；氧化镁；矿渣；水泥", "main_class": "C"},
    {"code": "C05B", "description": "磷肥", "main_class": "C"},
    {"code": "C05C", "description": "氮肥", "main_class": "C"},
    {"code": "C05D", "description": "不包含在C05B、C05C小类中的肥料", "main_class": "C"},
    {"code": "C05F", "description": "不包含在C05B、C05C小类中的有机肥料", "main_class": "C"},
    {"code": "C05G", "description": "分属于C05大类下各小类中肥料的混合物", "main_class": "C"},
    {"code": "C06B", "description": "炸药；火柴", "main_class": "C"},
    {"code": "C06C", "description": "起爆或点火装置", "main_class": "C"},
    {"code": "C06D", "description": "烟火；爆竹", "main_class": "C"},
    {"code": "C06F", "description": "火柴的制造", "main_class": "C"},
    {"code": "C07B", "description": "无环或碳环化合物的一般制备方法", "main_class": "C"},
    {"code": "C07C", "description": "无环或碳环化合物", "main_class": "C"},
    {"code": "C07D", "description": "杂环化合物", "main_class": "C"},
    {"code": "C07F", "description": "含除碳、氢、卤素、氧、氮、硫、硒或碲以外的其他元素的无环、碳环或杂环化合物", "main_class": "C"},
    {"code": "C07G", "description": "未知结构的化合物", "main_class": "C"},
    {"code": "C07H", "description": "糖类及其衍生物；核苷；核苷酸；核酸", "main_class": "C"},
    {"code": "C07J", "description": "甾族化合物", "main_class": "C"},
    {"code": "C07K", "description": "肽", "main_class": "C"},

    # G部 - 物理
    {"code": "G01B", "description": "长度、厚度或类似线性尺寸的测量；角度的测量；面积的测量", "main_class": "G"},
    {"code": "G01C", "description": "测量距离、水准或者方位；勘测；导航", "main_class": "G"},
    {"code": "G01D", "description": "非专用于特定变量的测量；不包括在其他单独小类中的测量装置", "main_class": "G"},
    {"code": "G01F", "description": "容积、流量、质量流量或液位的测量", "main_class": "G"},
    {"code": "G01H", "description": "机械振动或超声波、声波或亚声波的测量", "main_class": "G"},
    {"code": "G01J", "description": "红外光、可见光或紫外光的强度、速度、光谱成份，偏振或相位的测量", "main_class": "G"},
    {"code": "G01K", "description": "温度测量；热量测量", "main_class": "G"},
    {"code": "G01L", "description": "测量流体压力；测量流体的粘度", "main_class": "G"},
    {"code": "G01M", "description": "机器或结构部件的静态或动态平衡的测试", "main_class": "G"},
    {"code": "G01N", "description": "借助于测定材料的化学或物理性质来测试或分析材料", "main_class": "G"},
    {"code": "G01P", "description": "线速度或角速度、加速度、减速度或冲击的测量", "main_class": "G"},
    {"code": "G01R", "description": "测量电变量；测量磁变量", "main_class": "G"},
    {"code": "G01S", "description": "无线电定向；无线电导航", "main_class": "G"},
    {"code": "G01T", "description": "核辐射或X射线辐射的测量", "main_class": "G"},
    {"code": "G01V", "description": "地球物理；重力测量；物质或物体的探测", "main_class": "G"},
    {"code": "G01W", "description": "气象学", "main_class": "G"},
    {"code": "G02B", "description": "光学元件、系统或仪器", "main_class": "G"},
    {"code": "G02C", "description": "眼镜；太阳镜或与眼镜有同样特性的护目镜", "main_class": "G"},
    {"code": "G02F", "description": "光学器件或装置", "main_class": "G"},
    {"code": "G03B", "description": "摄影术或电影术用的附件", "main_class": "G"},
    {"code": "G03C", "description": "摄影用的感光材料", "main_class": "G"},
    {"code": "G03D", "description": "摄影术或电影术用的辅助工艺", "main_class": "G"},
    {"code": "G03F", "description": "图纹面的照相制版工艺", "main_class": "G"},
    {"code": "G03G", "description": "电摄影术；电照相；磁记录", "main_class": "G"},
    {"code": "G03H", "description": "全息摄影的工艺", "main_class": "G"},
    {"code": "G04B", "description": "机械驱动的钟或表；机械日历钟或表", "main_class": "G"},
    {"code": "G04C", "description": "电动机械钟或表", "main_class": "G"},
    {"code": "G04D", "description": "时钟或表的修理", "main_class": "G"},
    {"code": "G04F", "description": "测量时间间隔", "main_class": "G"},
    {"code": "G04G", "description": "电子钟或表", "main_class": "G"},
    {"code": "G05B", "description": "一般的控制或调节系统；这种系统的功能单元", "main_class": "G"},
    {"code": "G05D", "description": "非电变量的控制或调节系统", "main_class": "G"},
    {"code": "G05F", "description": "电变量或磁变量的调节系统", "main_class": "G"},
    {"code": "G05G", "description": "控制装置或系统", "main_class": "G"},
    {"code": "G06B", "description": "应用液体的计算设备", "main_class": "G"},
    {"code": "G06C", "description": "应用机械机构的计算设备", "main_class": "G"},
    {"code": "G06D", "description": "应用流体装置的数字计算设备", "main_class": "G"},
    {"code": "G06E", "description": "光学计算设备", "main_class": "G"},
    {"code": "G06F", "description": "电数字数据处理", "main_class": "G"},
    {"code": "G06G", "description": "模拟计算机", "main_class": "G"},
    {"code": "G06J", "description": "混合计算装置", "main_class": "G"},
    {"code": "G06K", "description": "数据识别；数据表示；记录载体", "main_class": "G"},
    {"code": "G06M", "description": "计数机构", "main_class": "G"},
    {"code": "G06N", "description": "基于特定计算模型的计算机系统", "main_class": "G"},
    {"code": "G06Q", "description": "专门适用于行政、商业、金融、管理、监督或预测目的的数据处理系统或方法", "main_class": "G"},
    {"code": "G06T", "description": "图像数据处理或产生", "main_class": "G"},
    {"code": "G06V", "description": "图像或视频识别或理解", "main_class": "G"},
    {"code": "G07B", "description": "售票设备", "main_class": "G"},
    {"code": "G07C", "description": "时间登记器或出勤登记器", "main_class": "G"},
    {"code": "G07D", "description": "处理钱币或纸币", "main_class": "G"},
    {"code": "G07F", "description": "投币式设备", "main_class": "G"},
    {"code": "G07G", "description": "登记收款机", "main_class": "G"},
    {"code": "G08B", "description": "信号装置或呼叫装置；报警系统", "main_class": "G"},
    {"code": "G08C", "description": "测量值、控制信号或类似信号的传输系统", "main_class": "G"},
    {"code": "G08G", "description": "交通控制系统", "main_class": "G"},
    {"code": "G09B", "description": "教育或演示用具；用于教学或与盲人、聋人或哑人通信的用具", "main_class": "G"},
    {"code": "G09C", "description": "密码术或密码装置", "main_class": "G"},
    {"code": "G09D", "description": "铁路用或类似用途的时间表或计费装置", "main_class": "G"},
    {"code": "G09F", "description": "显示；广告；标记；标签或名牌；印鉴", "main_class": "G"},
    {"code": "G09G", "description": "对用静态方法显示可变信息的指示装置进行控制的装置或电路", "main_class": "G"},
    {"code": "G10B", "description": "风琴；簧风琴", "main_class": "G"},
    {"code": "G10C", "description": "钢琴", "main_class": "G"},
    {"code": "G10D", "description": "未列入其他类组的乐器", "main_class": "G"},
    {"code": "G10F", "description": "自动乐器", "main_class": "G"},
    {"code": "G10G", "description": "音乐的辅助设备", "main_class": "G"},
    {"code": "G10H", "description": "电声乐器", "main_class": "G"},
    {"code": "G10K", "description": "发声器械", "main_class": "G"},
    {"code": "G10L", "description": "语音分析或合成；语音识别；音频分析或处理", "main_class": "G"},
    {"code": "G11B", "description": "基于记录载体和换能器之间的相对运动而实现的信息存储", "main_class": "G"},
    {"code": "G11C", "description": "静态存储器", "main_class": "G"},
    {"code": "G12B", "description": "仪器的零部件", "main_class": "G"},
    {"code": "G16B", "description": "生物化学，例如生物信息学或chemoinformatics", "main_class": "G"},
    {"code": "G16C", "description": "计算化学，即信息通信技术(ICT)专门适用于理论或计算化学", "main_class": "G"},
    {"code": "G16H", "description": "医疗保健信息学，即专门适用于处置或处理医疗或健康数据的信息和通信技术(ICT)", "main_class": "G"},
    {"code": "G16Z", "description": "未列入其他类组的数据处理或计算的特别领域", "main_class": "G"},
    {"code": "G21B", "description": "核反应堆", "main_class": "G"},
    {"code": "G21C", "description": "核反应堆", "main_class": "G"},
    {"code": "G21D", "description": "核发电厂", "main_class": "G"},
    {"code": "G21F", "description": "X射线，γ射线，微粒射线或离子射线的防护", "main_class": "G"},
    {"code": "G21G", "description": "化学元素的转变", "main_class": "G"},
    {"code": "G21H", "description": "从放射源取得能量", "main_class": "G"},
    {"code": "G21J", "description": "核爆炸", "main_class": "G"},
    {"code": "G21K", "description": "未列入其他类组的粒子或电磁辐射的处理技术；辐射室装置", "main_class": "G"},

    # H部 - 电学
    {"code": "H01B", "description": "电缆；导体；绝缘体；导电、绝缘或介电材料的选择", "main_class": "H"},
    {"code": "H01C", "description": "电阻器", "main_class": "H"},
    {"code": "H01F", "description": "磁体；电感；变压器；磁性材料的选择", "main_class": "H"},
    {"code": "H01G", "description": "电容器；电解型的电容器、整流器、检波器、开关器件、光敏器件或热敏器件", "main_class": "H"},
    {"code": "H01H", "description": "电开关；继电器；选择器；紧急保护装置", "main_class": "H"},
    {"code": "H01J", "description": "放电管或放电灯", "main_class": "H"},
    {"code": "H01K", "description": "白炽灯", "main_class": "H"},
    {"code": "H01L", "description": "半导体器件；其他类目中不包括的电固体器件", "main_class": "H"},
    {"code": "H01M", "description": "用于直接转变化学能为电能的方法或装置", "main_class": "H"},
    {"code": "H01P", "description": "波导；谐振器、传输线或其他波导型器件", "main_class": "H"},
    {"code": "H01Q", "description": "天线，即无线电天线", "main_class": "H"},
    {"code": "H01R", "description": "导电连接；一组相互绝缘的电连接元件的结构组合；连接装置；集电器", "main_class": "H"},
    {"code": "H01S", "description": "利用受激发射的器件", "main_class": "H"},
    {"code": "H01T", "description": "火花隙；应用火花隙的过压避雷器；火花塞；电子发射器；离子发射器", "main_class": "H"},
    {"code": "H02B", "description": "供电或配电用的配电盘、变电站或开关装置", "main_class": "H"},
    {"code": "H02G", "description": "电缆或电线的或光缆和电缆或电线组合的安装", "main_class": "H"},
    {"code": "H02H", "description": "紧急保护电路装置", "main_class": "H"},
    {"code": "H02J", "description": "供电或配电的电路装置或系统；电能存储系统", "main_class": "H"},
    {"code": "H02K", "description": "电机", "main_class": "H"},
    {"code": "H02M", "description": "用于交流和交流之间、交流和直流之间或直流和直流之间的转换", "main_class": "H"},
    {"code": "H02N", "description": "其他类目中不包括的电机", "main_class": "H"},
    {"code": "H02P", "description": "电机、机电变流器或整流器的控制或调节", "main_class": "H"},
    {"code": "H03B", "description": "使用工作于非开关状态的主动元件的振荡发生", "main_class": "H"},
    {"code": "H03C", "description": "调制", "main_class": "H"},
    {"code": "H03D", "description": "解调或检波；调制载波频率到调制信号频率的变频", "main_class": "H"},
    {"code": "H03F", "description": "放大器", "main_class": "H"},
    {"code": "H03G", "description": "放大的控制", "main_class": "H"},
    {"code": "H03H", "description": "阻抗网络，例如谐振电路；谐振器", "main_class": "H"},
    {"code": "H03J", "description": "谐振电路的调谐；谐振电路的选择", "main_class": "H"},
    {"code": "H03K", "description": "脉冲技术", "main_class": "H"},
    {"code": "H03L", "description": "电子振荡器或脉冲发生器的自动控制、起振或同步", "main_class": "H"},
    {"code": "H03M", "description": "一般编码、译码或代码转换", "main_class": "H"},
    {"code": "H04B", "description": "传输", "main_class": "H"},
    {"code": "H04H", "description": "广播通信", "main_class": "H"},
    {"code": "H04J", "description": "多路复用通信", "main_class": "H"},
    {"code": "H04K", "description": "保密通信；对保密通信的干扰", "main_class": "H"},
    {"code": "H04L", "description": "数字信息的传输，例如电报通信", "main_class": "H"},
    {"code": "H04M", "description": "电话通信", "main_class": "H"},
    {"code": "H04N", "description": "图像通信，例如电视", "main_class": "H"},
    {"code": "H04Q", "description": "电通信技术领域中未列入其他类目的选择方法或装置", "main_class": "H"},
    {"code": "H04R", "description": "扬声器、传声器、唱机拾音器或其他声—机电换能器；助听器；扩音系统", "main_class": "H"},
    {"code": "H04S", "description": "立体声系统", "main_class": "H"},
    {"code": "H04W", "description": "无线通信网络", "main_class": "H"},
    {"code": "H05B", "description": "电照明；其他类目中不包括的电加热", "main_class": "H"},
    {"code": "H05C", "description": "为杀伤或击昏生物体用的电装置", "main_class": "H"},
    {"code": "H05F", "description": "静电；自然发生的静电", "main_class": "H"},
    {"code": "H05G", "description": "X射线技术", "main_class": "H"},
    {"code": "H05H", "description": "等离子体技术；加速的带电粒子或中子的产生", "main_class": "H"},
    {"code": "H05K", "description": "印刷电路；电设备的外壳或结构零部件；电气元件组件的制造", "main_class": "H"},
]


@dataclass
class CollectionConfig:
    """向量集合配置"""
    name: str
    vector_size: int
    distance: str
    description: str


class PatentClassificationVectorInitializer:
    """
    专利分类向量集合初始化器

    功能:
    1. 创建Qdrant向量集合
    2. 生成分类代码的嵌入向量
    3. 批量索引分类向量
    """

    COLLECTIONS = [
        CollectionConfig(
            name="cpc_vectors",
            vector_size=768,
            distance="Cosine",
            description="CPC分类代码向量索引",
        ),
        CollectionConfig(
            name="ipc_vectors",
            vector_size=768,
            distance="Cosine",
            description="IPC分类代码向量索引",
        ),
    ]

    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """初始化"""
        self.host = qdrant_host
        self.port = qdrant_port
        self.client = None
        self.embedding_service = None

        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self):
        """初始化连接和服务"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models

            self.client = QdrantClient(host=self.host, port=self.port)
            self.models = models
            self.logger.info(f"✅ Qdrant客户端已连接: {self.host}:{self.port}")

        except ImportError:
            self.logger.warning("⚠️ qdrant-client未安装，使用模拟模式")
            self.client = None

        try:
            from core.embedding.unified_embedding_service import (
                ModuleType,
                get_unified_embedding_service,
            )

            self.embedding_service = get_unified_embedding_service()
            self.module_type = ModuleType.PATENT_SEARCH
            self.logger.info("✅ 嵌入服务已加载")

        except ImportError:
            self.logger.warning("⚠️ 嵌入服务未找到，使用模拟向量")

    async def create_collections(self):
        """创建向量集合"""
        if self.client is None:
            self.logger.warning("模拟模式：跳过集合创建")
            return

        for config in self.COLLECTIONS:
            try:
                # 检查集合是否存在
                collections = self.client.get_collections().collections
                existing_names = [c.name for c in collections]

                if config.name in existing_names:
                    self.logger.info(f"📦 集合 {config.name} 已存在")
                    continue

                # 创建新集合
                from qdrant_client.http.models import Distance, VectorParams

                self.client.create_collection(
                    collection_name=config.name,
                    vectors_config=VectorParams(
                        size=config.vector_size,
                        distance=Distance.COSINE,
                    ),
                )

                self.logger.info(f"✅ 创建集合: {config.name}")

            except Exception as e:
                self.logger.error(f"❌ 创建集合 {config.name} 失败: {e}")

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """生成嵌入向量"""
        if self.embedding_service is None:
            # 模拟向量
            import random
            return [[random.gauss(0, 0.1) for _ in range(768)] for _ in texts]

        try:
            result = await self.embedding_service.encode(
                texts=texts,
                module_type=self.module_type,
            )

            embeddings = result.get("embeddings", [])
            return embeddings if isinstance(embeddings[0], list) else [embeddings]

        except Exception as e:
            self.logger.error(f"生成嵌入失败: {e}")
            # 返回模拟向量
            import random
            return [[random.gauss(0, 0.1) for _ in range(768)] for _ in texts]

    async def index_classification_codes(self):
        """索引分类代码"""
        self.logger.info(f"📊 开始索引 {len(CPC_CODES)} 个CPC分类代码...")

        if self.client is None:
            self.logger.warning("模拟模式：跳过索引")
            return

        # 批量处理
        batch_size = 50
        for i in range(0, len(CPC_CODES), batch_size):
            batch = CPC_CODES[i : i + batch_size]

            # 生成描述文本
            texts = [f"{code['code']}: {code['description']}" for code in batch]

            # 生成嵌入向量
            embeddings = await self.generate_embeddings(texts)

            # 构建点
            from qdrant_client.http.models import PointStruct

            points = []
            for j, (code, embedding) in enumerate(zip(batch, embeddings, strict=False)):
                points.append(
                    PointStruct(
                        id=i + j,
                        vector=embedding,
                        payload={
                            "code": code["code"],
                            "description": code["description"],
                            "main_class": code["main_class"],
                        },
                    )
                )

            # 批量插入
            try:
                self.client.upsert(
                    collection_name="cpc_vectors",
                    points=points,
                )
                self.logger.info(f"  ✅ 索引 {len(points)} 个分类代码 ({i + len(points)}/{len(CPC_CODES)})")

            except Exception as e:
                self.logger.error(f"  ❌ 索引失败: {e}")

        self.logger.info("✅ CPC分类代码索引完成")

    async def verify_collections(self):
        """验证集合"""
        if self.client is None:
            self.logger.warning("模拟模式：跳过验证")
            return

        for config in self.COLLECTIONS:
            try:
                info = self.client.get_collection(config.name)
                self.logger.info(
                    f"📊 {config.name}: "
                    f"向量数={info.points_count}, "
                    f"状态={info.status}"
                )
            except Exception as e:
                self.logger.error(f"❌ 验证 {config.name} 失败: {e}")

    async def run(self):
        """执行初始化"""
        self.logger.info("🚀 开始初始化专利分类向量集合...")

        await self.initialize()
        await self.create_collections()
        await self.index_classification_codes()
        await self.verify_collections()

        self.logger.info("✅ 专利分类向量集合初始化完成")


async def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    initializer = PatentClassificationVectorInitializer()
    await initializer.run()


if __name__ == "__main__":
    asyncio.run(main())
