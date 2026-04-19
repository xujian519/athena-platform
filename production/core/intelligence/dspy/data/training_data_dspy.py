from __future__ import annotations
# DSPy Training Data

import dspy

training_data = [
    # Case 1: 材料科学领域组合创新新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种材料科学领域的装置\n专利号: CN2015900654X\n发明人: 张某\n申请日: 2018-04-20\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种材料科学领.',
        context='现有技术: 对比文件D1:\n文献类型: 外国专利\n公开号: WO3743675A\n公开日: 2011-05-15\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n披露了相关的方法步.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征2: 涉案专利采用方法B,提高了效率\n\n3. 判断结论\n涉案.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 2: 新能源领域组合创新新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种新能源领域的装置\n专利号: CN2020525458X\n发明人: 赵某\n申请日: 2023-09-05\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种新能源领域的.',
        context='现有技术: 对比文件D1:\n文献类型: 技术标准\n公开号: US1570053B1\n公开日: 2015-02-04\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n公开了类似的.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了相似的技术手段,但具体实现方式存在差异\n\n2. 区别技术特征\n区别特征3: 涉案专利优化了参数C,改善了性能\n\n3. 判断结论\n涉案专利.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 3: 通信技术领域结构改进新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种通信技术领域的系统\n专利号: CN2016452699X\n发明人: 刘某\n申请日: 2021-05-07\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种通信技术领.',
        context='现有技术: 对比文件D2:\n文献类型: 中国发明专利\n公开号: WO4926451B2\n公开日: 2015-02-05\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n揭示了.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征3: 涉案专利优化了参数C,改善了性能\n\n3. 判断结论\n需.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 4: 医疗器械领域组合创新新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种医疗器械领域的方法\n专利号: CN2017791313X\n发明人: 赵某\n申请日: 2018-10-13\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种医疗器械领.',
        context='现有技术: 对比文件D3:\n文献类型: 外国专利\n公开号: WO7187237B2\n公开日: 2016-12-15\n\n公开内容:\n披露了相关的方法步骤,包括数据采集和处理\n披露了相关的.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\\.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 5: 人工智能领域功能增强新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种人工智能领域的方法\n专利号: CN2015671301X\n发明人: 张某\n申请日: 2022-02-06\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种人工智能领.',
        context='现有技术: 对比文件D1:\n文献类型: 技术标准\n公开号: EP9289216A\n公开日: 2021-12-03\n\n公开内容:\n披露了相关的方法步骤,包括数据采集和处理\n揭示了相关的技.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征3: 涉案专利优化了参数C,改善了性能\n\n3. 判断结论\n涉.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 6: 通信技术领域功能增强新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种通信技术领域的方法\n专利号: CN2022945047X\n发明人: 赵某\n申请日: 2021-05-17\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种通信技术领.',
        context='现有技术: 对比文件D1:\n文献类型: 中国发明专利\n公开号: CN6992749B2\n公开日: 2012-05-18\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n披露了相关的.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\\.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 7: 医疗器械领域应用拓展新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种医疗器械领域的装置\n专利号: CN2022675479X\n发明人: 李某\n申请日: 2015-05-25\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种医疗器械领.',
        context='现有技术: 对比文件D1:\n文献类型: 科技论文\n公开号: WO2091603A\n公开日: 2012-03-19\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n展示了相近的应.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征2: 涉案专利采用方法B,提高了效率\n\n3. 判断结论\n需要.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 8: 医疗器械领域组合创新新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种医疗器械领域的装置\n专利号: CN2020763351X\n发明人: 李某\n申请日: 2020-03-06\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种医疗器械领.',
        context='现有技术: 对比文件D1:\n文献类型: 科技论文\n公开号: CN7335564A\n公开日: 2011-02-03\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n披露了相关的.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了相似的技术手段,但具体实现方式存在差异\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\n涉案.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 9: 智能汽车领域应用拓展新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种智能汽车领域的系统\n专利号: CN2015604606X\n发明人: 赵某\n申请日: 2019-12-28\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种智能汽车领.',
        context='现有技术: 对比文件D3:\n文献类型: 中国发明专利\n公开号: CN4414919A\n公开日: 2022-06-09\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n展示了相近的应.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了相似的技术手段,但具体实现方式存在差异\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\n需要.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 10: 新能源领域结构改进新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种新能源领域的系统\n专利号: CN2016503226X\n发明人: 李某\n申请日: 2017-02-27\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种新能源领域的.',
        context='现有技术: 对比文件D2:\n文献类型: 外国专利\n公开号: WO2241626B1\n公开日: 2022-01-06\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n揭示了相关的技术.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了相似的技术手段,但具体实现方式存在差异\n\n2. 区别技术特征\n区别特征3: 涉案专利优化了参数C,改善了性能\n\n3. 判断结论\n涉案专利.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 11: 通信技术领域结构改进新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种通信技术领域的设备\n专利号: CN2016114072X\n发明人: 刘某\n申请日: 2021-12-11\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种通信技术领.',
        context='现有技术: 对比文件D3:\n文献类型: 外国专利\n公开号: US5910739A\n公开日: 2016-10-28\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n披露了相关的方.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了相似的技术手段,但具体实现方式存在差异\n\n2. 区别技术特征\n区别特征2: 涉案专利采用方法B,提高了效率\n\n3. 判断结论\n涉案专利具.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 12: 半导体领域方法创新新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种半导体领域的系统\n专利号: CN2018905646X\n发明人: 李某\n申请日: 2018-08-15\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种半导体领域的.',
        context='现有技术: 对比文件D2:\n文献类型: 科技论文\n公开号: CN9791887B1\n公开日: 2019-05-11\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n描述了相似.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1公开了涉案专利的大部分技术特征,但未公开区别特征X\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\\.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 13: 材料科学领域功能增强新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种材料科学领域的设备\n专利号: CN2021538114X\n发明人: 张某\n申请日: 2022-10-19\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种材料科学领.',
        context='现有技术: 对比文件D3:\n文献类型: 中国发明专利\n公开号: US6790387B2\n公开日: 2021-11-13\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n披露了相.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1与涉案专利的技术领域、所要解决的技术问题基本相同\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 14: 人工智能领域应用拓展新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种人工智能领域的装置\n专利号: CN2021162224X\n发明人: 张某\n申请日: 2016-01-21\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种人工智能领.',
        context='现有技术: 对比文件D2:\n文献类型: 中国实用新型专利\n公开号: WO7071246B2\n公开日: 2013-04-01\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n披露.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1与涉案专利的技术领域、所要解决的技术问题基本相同\n\n2. 区别技术特征\n区别特征3: 涉案专利优化了参数C,改善了性能\n\n3. 判断结论\n需要.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 15: 材料科学领域组合创新新颖性争议案
    dspy.Example(
        user_input='涉案专利: 一种材料科学领域的方法\n专利号: CN2017181496X\n发明人: 李某\n申请日: 2016-09-21\n\n[技术方案]\n\n[技术方案]\n涉案专利提供了一种材料科学领.',
        context='现有技术: 对比文件D1:\n文献类型: 中国实用新型专利\n公开号: US2433418A\n公开日: 2010-05-14\n\n公开内容:\n披露了相关的方法步骤,包括数据采集和处理\n披露了.',
        task_type='capability_2_novelty',
        analysis_result='[新颖性分析]\n1. 对比文件分析\nD1与涉案专利的技术领域、所要解决的技术问题基本相同\n\n2. 区别技术特征\n区别特征1: 涉案专利增加了模块A,实现了功能增强\n\n3. 判断结论\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 16: 通信技术领域集成系统创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种通信技术领域的集成系统\n专利号: CN2022424950X\n发明人: 李某\n\n[技术背景]\n\n通信技术领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D3:\n文献类型: 外国专利\n公开号: WO7185444A\n公开日: 2020-01-18\n\n公开内容:\n披露了相关的方法步骤,包括数据采集和处理\n公开了类似的技.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1是最接近的现有技术,公开了基本的技术框架\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技术效.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 17: 材料科学领域协同方案创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种材料科学领域的优化方法\n专利号: CN2015795875X\n发明人: 赵某\n\n[技术背景]\n\n材料科学领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D2:\n文献类型: 中国实用新型专利\n公开号: US6216495B1\n公开日: 2022-06-10\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n披露.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于优化了参数C,降低了能耗\n\n3. 技术效果分析\n显著提升了系统性.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 18: 生物医药领域复合物创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种生物医药领域的集成系统\n专利号: CN2020324930X\n发明人: 李某\n\n[技术背景]\n\n生物医药领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D2:\n文献类型: 技术标准\n公开号: CN3249268A\n公开日: 2015-06-10\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n展示了相近的应.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1与涉案专利属于相同技术领域,解决类似技术问题\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 19: 航空航天领域优化算法创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种航空航天领域的集成系统\n专利号: CN2021825739X\n发明人: 刘某\n\n[技术背景]\n\n航空航天领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D2:\n文献类型: 技术标准\n公开号: WO2609469B1\n公开日: 2021-05-07\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n披露了相关.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1与涉案专利属于相同技术领域,解决类似技术问题\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 20: 智能汽车领域复合物创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种智能汽车领域的集成系统\n专利号: CN2022107833X\n发明人: 刘某\n\n[技术背景]\n\n智能汽车领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D2:\n文献类型: 技术标准\n公开号: WO8775144A\n公开日: 2014-11-01\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n描述了相似的功.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1与涉案专利属于相同技术领域,解决类似技术问题\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 21: 医疗器械领域协同方案创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种医疗器械领域的优化方法\n专利号: CN2018830123X\n发明人: 赵某\n\n[技术背景]\n\n医疗器械领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D2:\n文献类型: 科技论文\n公开号: EP5478339B2\n公开日: 2011-11-24\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n披露了相关的方法.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1与涉案专利属于相同技术领域,解决类似技术问题\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 22: 生物医药领域协同方案创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种生物医药领域的新工艺\n专利号: CN2017151613X\n发明人: 李某\n\n[技术背景]\n\n生物医药领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题.',
        context='现有技术: 对比文件D3:\n文献类型: 技术标准\n公开号: CN2900091A\n公开日: 2022-01-16\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n展示了相近的应.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技术效果分析\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 23: 材料科学领域集成系统创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种材料科学领域的复合物\n专利号: CN2016307718X\n发明人: 张某\n\n[技术背景]\n\n材料科学领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题.',
        context='现有技术: 对比文件D3:\n文献类型: 中国实用新型专利\n公开号: WO8745314B2\n公开日: 2011-05-24\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n展示.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1与涉案专利属于相同技术领域,解决类似技术问题\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 24: 医疗器械领域优化算法创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种医疗器械领域的优化方法\n专利号: CN2022857604X\n发明人: 张某\n\n[技术背景]\n\n医疗器械领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D1:\n文献类型: 中国发明专利\n公开号: CN4967743B1\n公开日: 2012-09-27\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n展示了相.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析\n改善了用户.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 25: 新能源领域集成系统创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种新能源领域的集成系统\n专利号: CN2016453916X\n发明人: 刘某\n\n[技术背景]\n\n新能源领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题1.',
        context='现有技术: 对比文件D1:\n文献类型: 中国发明专利\n公开号: WO2776283B2\n公开日: 2019-05-13\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n公开了类.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技术效果分析\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 26: 航空航天领域集成系统创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种航空航天领域的优化方法\n专利号: CN2017949437X\n发明人: 赵某\n\n[技术背景]\n\n航空航天领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问.',
        context='现有技术: 对比文件D1:\n文献类型: 外国专利\n公开号: WO6159701B2\n公开日: 2010-05-26\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n披露了相关的方法.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1是最接近的现有技术,公开了基本的技术框架\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 27: 航空航天领域协同方案创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种航空航天领域的复合物\n专利号: CN2017735846X\n发明人: 张某\n\n[技术背景]\n\n航空航天领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题.',
        context='现有技术: 对比文件D1:\n文献类型: 中国发明专利\n公开号: CN3508827A\n公开日: 2019-10-23\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n公开了类似.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技术效果分析\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 28: 新能源领域集成系统创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种新能源领域的新工艺\n专利号: CN2016713255X\n发明人: 张某\n\n[技术背景]\n\n新能源领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题1:.',
        context='现有技术: 对比文件D1:\n文献类型: 中国发明专利\n公开号: EP4891866B1\n公开日: 2010-11-11\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n公开了.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1是最接近的现有技术,公开了基本的技术框架\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 29: 人工智能领域集成系统创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种人工智能领域的复合物\n专利号: CN2017340420X\n发明人: 刘某\n\n[技术背景]\n\n人工智能领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题.',
        context='现有技术: 对比文件D1:\n文献类型: 中国实用新型专利\n公开号: US4499487A\n公开日: 2013-12-07\n\n公开内容:\n披露了相关的方法步骤,包括数据采集和处理\n披露了.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于增加了功能模块A,解决了响应速度慢的问题\n\n3. 技术效果分析\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 30: 机器人领域复合物创造性争议案
    dspy.Example(
        user_input='涉案专利: 一种机器人领域的集成系统\n专利号: CN2023716065X\n发明人: 李某\n\n[技术背景]\n\n机器人领域是当前技术发展的热点方向。\n现有技术存在以下问题:\n- 问题1.',
        context='现有技术: 对比文件D3:\n文献类型: 科技论文\n公开号: CN1769238B1\n公开日: 2020-06-09\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n公开了类似的.',
        task_type='capability_2_creative',
        analysis_result='[创造性分析]\n1. 最接近现有技术确定\nD1公开了涉案专利的大部分技术特征\n\n2. 区别特征与技术问题\n区别特征在于采用了工艺B,提高了产品合格率\n\n3. 技术效果分析\n降低了生产.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 31: 通信技术领域控制系统充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及通信技术领域,专利号: CN2017777860X\n\n\n[技术方案]\n涉案专利提供了一种通信技术领域的新装置,包括以下技术特征:\n- 接收模块\n- 发射模块\n- 处理单元\\.',
        context='现有技术: 对比文件D2:\n文献类型: 中国发明专利\n公开号: WO6187151B2\n公开日: 2022-07-06\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n公开了类.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书公开了关键技术参数和实施步骤\n\n2. 实施例描述\n提供了3个具体实施例,涵盖不同应用场景\n\n3. 技术效果验证\n仅描述性说明,缺乏实验.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 32: 智能汽车领域生物材料充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及智能汽车领域,专利号: CN2017153084X\n\n\n[技术方案]\n涉案专利提供了一种智能汽车领域的新方法,包括以下技术特征:\n- 通信模块\n- 执行机构\n- 传感器模块.',
        context='现有技术: 对比文件D2:\n文献类型: 中国实用新型专利\n公开号: US4812925B2\n公开日: 2012-03-15\n\n公开内容:\n披露了相关的方法步骤,包括数据采集和处理\n揭示.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书公开了完整的技术方案,包括各组成部分\n\n2. 实施例描述\n提供了3个具体实施例,涵盖不同应用场景\n\n3. 技术效果验证\n仅描述性说明,.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 33: 通信技术领域生物材料充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及通信技术领域,专利号: CN2019317071X\n\n\n[技术方案]\n涉案专利提供了一种通信技术领域的新系统,包括以下技术特征:\n- 处理单元\n- 接收模块\n- 控制接口\\.',
        context='现有技术: 对比文件D1:\n文献类型: 中国实用新型专利\n公开号: WO5490090B1\n公开日: 2018-06-28\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n公开.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书公开了关键技术参数和实施步骤\n\n2. 实施例描述\n提供了3个具体实施例,涵盖不同应用场景\n\n3. 技术效果验证\n仅描述性说明,缺乏实验.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 34: 材料科学领域制备方法充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及材料科学领域,专利号: CN2020503278X\n\n\n[技术方案]\n涉案专利提供了一种材料科学领域的新装置,包括以下技术特征:\n- 添加剂\n- 增强相\n- 涂层\n- 基.',
        context='现有技术: 对比文件D2:\n文献类型: 技术标准\n公开号: EP5284326B2\n公开日: 2018-02-02\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n揭示了相关的.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书描述了基本原理,但缺少具体实施细节\n\n2. 实施例描述\n仅提供1个实施例,公开不充分\n\n3. 技术效果验证\n提供了对比实验,效果显著\\.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 35: 材料科学领域控制系统充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及材料科学领域,专利号: CN2022748396X\n\n\n[技术方案]\n涉案专利提供了一种材料科学领域的新装置,包括以下技术特征:\n- 基体材料\n- 添加剂\n- 涂层\n- .',
        context='现有技术: 对比文件D2:\n文献类型: 中国实用新型专利\n公开号: WO8092853B2\n公开日: 2020-03-25\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n揭示了相.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书描述了基本原理,但缺少具体实施细节\n\n2. 实施例描述\n仅提供1个实施例,公开不充分\n\n3. 技术效果验证\n通过实验数据验证了技术效果.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 36: 通信技术领域数据处理充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及通信技术领域,专利号: CN2018373428X\n\n\n[技术方案]\n涉案专利提供了一种通信技术领域的新装置,包括以下技术特征:\n- 处理单元\n- 发射模块\n- 接收模块\\.',
        context='现有技术: 对比文件D3:\n文献类型: 中国发明专利\n公开号: WO1875725A\n公开日: 2018-10-04\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n披露了相.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书公开了完整的技术方案,包括各组成部分\n\n2. 实施例描述\n提供了3个具体实施例,涵盖不同应用场景\n\n3. 技术效果验证\n通过实验数据验.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 37: 智能汽车领域制备方法充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及智能汽车领域,专利号: CN2019575988X\n\n\n[技术方案]\n涉案专利提供了一种智能汽车领域的新方法,包括以下技术特征:\n- 人机界面\n- 控制器\n- 执行机构\n.',
        context='现有技术: 对比文件D3:\n文献类型: 科技论文\n公开号: CN1244829B2\n公开日: 2013-05-20\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n公开了类似.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书公开了关键技术参数和实施步骤\n\n2. 实施例描述\n提供了多个实施例,但关键参数未明确\n\n3. 技术效果验证\n仅描述性说明,缺乏实验支持.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 38: 通信技术领域数据处理充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及通信技术领域,专利号: CN2023523049X\n\n\n[技术方案]\n涉案专利提供了一种通信技术领域的新工艺,包括以下技术特征:\n- 发射模块\n- 天线系统\n- 处理单元\\.',
        context='现有技术: 对比文件D1:\n文献类型: 中国实用新型专利\n公开号: US5171589B1\n公开日: 2014-11-11\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n展示.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书描述了基本原理,但缺少具体实施细节\n\n2. 实施例描述\n仅提供1个实施例,公开不充分\n\n3. 技术效果验证\n仅描述性说明,缺乏实验支持.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 39: 人工智能领域控制系统充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及人工智能领域,专利号: CN2023751801X\n\n\n[技术方案]\n涉案专利提供了一种人工智能领域的新系统,包括以下技术特征:\n- 数据采集层\n- 输出接口\n- 存储单元.',
        context='现有技术: 对比文件D3:\n文献类型: 科技论文\n公开号: CN4260431B2\n公开日: 2018-01-12\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n披露了相关的.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书描述了基本原理,但缺少具体实施细节\n\n2. 实施例描述\n提供了多个实施例,但关键参数未明确\n\n3. 技术效果验证\n通过实验数据验证了技.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 40: 新能源领域检测技术充分公开争议案
    dspy.Example(
        user_input='涉案专利涉及新能源领域,专利号: CN2017885491X\n\n\n[技术方案]\n涉案专利提供了一种新能源领域的新装置,包括以下技术特征:\n- 充电接口\n- 散热结构\n- 保护电路\n-.',
        context='现有技术: 对比文件D3:\n文献类型: 技术标准\n公开号: US9052541A\n公开日: 2011-09-07\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n公开了类似的技.',
        task_type='capability_2_disclosure',
        analysis_result='[充分公开分析]\n1. 技术方案公开程度\n说明书描述了基本原理,但缺少具体实施细节\n\n2. 实施例描述\n提供了多个实施例,但关键参数未明确\n\n3. 技术效果验证\n仅描述性说明,缺乏实.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 41: 材料科学领域工艺参数新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及材料科学领域,专利号: CN2022453424X\n\n\n[技术方案]\n涉案专利提供了一种材料科学领域的新工艺,包括以下技术特征:\n- 基体材料\n- 涂层\n- 界面层\n- .',
        context='现有技术: 对比文件D3:\n文献类型: 中国发明专利\n公开号: EP9713661B1\n公开日: 2014-11-25\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n揭示了.',
        task_type='capability_2_clarity',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 42: 机器人领域成分配比新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及机器人领域,专利号: CN2019583298X\n\n\n[技术方案]\n涉案专利提供了一种机器人领域的新方法,包括以下技术特征:\n- 机械臂\n- 执行末端\n- 驱动单元\n- .',
        context='现有技术: 对比文件D2:\n文献类型: 中国实用新型专利\n公开号: US7443095B2\n公开日: 2020-10-02\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n披露.',
        task_type='capability_2_clarity',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 43: 航空航天领域使用方法新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及航空航天领域,专利号: CN2016628448X\n\n\n[技术方案]\n涉案专利提供了一种航空航天领域的新工艺,包括以下技术特征:\n- 控制单元\n- 机身结构\n- 动力系统\\.',
        context='现有技术: 对比文件D2:\n文献类型: 中国发明专利\n公开号: WO7907266B2\n公开日: 2017-06-17\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n披露了.',
        task_type='capability_2_clarity',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 44: 半导体领域应用领域新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及半导体领域,专利号: CN2022131075X\n\n\n[技术方案]\n涉案专利提供了一种半导体领域的新装置,包括以下技术特征:\n- 衬底材料\n- 互连结构\n- 介质层\n- .',
        context='现有技术: 对比文件D2:\n文献类型: 外国专利\n公开号: US7886355B1\n公开日: 2019-02-02\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n展示了相近的.',
        task_type='capability_2_clarity',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 45: 人工智能领域装置结构新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及人工智能领域,专利号: CN2021486395X\n\n\n[技术方案]\n涉案专利提供了一种人工智能领域的新方法,包括以下技术特征:\n- 存储单元\n- 算法模型\n- 输出接口\\.',
        context='现有技术: 对比文件D1:\n文献类型: 科技论文\n公开号: US2621453A\n公开日: 2011-10-24\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n揭示了相关的技.',
        task_type='capability_2_clarity',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 46: 机器人领域平台架构新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及机器人领域,专利号: CN2020219646X\n\n\n[技术方案]\n涉案专利提供了一种机器人领域的新系统,包括以下技术特征:\n- 控制系统\n- 传感器阵列\n- 驱动单元\n.',
        context='现有技术: 对比文件D2:\n文献类型: 外国专利\n公开号: CN1881213B1\n公开日: 2021-05-16\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n描述了相似的.',
        task_type='capability_2_complex',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 47: 半导体领域生态方案新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及半导体领域,专利号: CN2016426679X\n\n\n[技术方案]\n涉案专利提供了一种半导体领域的新装置,包括以下技术特征:\n- 介质层\n- 外延层\n- 互连结构\n- 电.',
        context='现有技术: 对比文件D3:\n文献类型: 中国发明专利\n公开号: CN4463648A\n公开日: 2013-01-12\n\n公开内容:\n描述了相似的功能模块,实现基本的控制功能\n描述了相似.',
        task_type='capability_2_complex',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 48: 新能源领域生态方案新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及新能源领域,专利号: CN2021572241X\n\n\n[技术方案]\n涉案专利提供了一种新能源领域的新系统,包括以下技术特征:\n- 散热结构\n- 充电接口\n- 保护电路\n-.',
        context='现有技术: 对比文件D2:\n文献类型: 科技论文\n公开号: US2696111B1\n公开日: 2019-02-07\n\n公开内容:\n公开了类似的技术结构,包含传感器和处理单元\n披露了相关.',
        task_type='capability_2_complex',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 49: 航空航天领域生态方案新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及航空航天领域,专利号: CN2019647844X\n\n\n[技术方案]\n涉案专利提供了一种航空航天领域的新系统,包括以下技术特征:\n- 动力系统\n- 通信系统\n- 控制单元\\.',
        context='现有技术: 对比文件D1:\n文献类型: 科技论文\n公开号: EP8053113B1\n公开日: 2015-11-14\n\n公开内容:\n揭示了相关的技术原理,采用类似的算法\n披露了相关的方法.',
        task_type='capability_2_complex',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 50: 材料科学领域生态方案新颖性争议案
    dspy.Example(
        user_input='涉案专利涉及材料科学领域,专利号: CN2022187794X\n\n\n[技术方案]\n涉案专利提供了一种材料科学领域的新装置,包括以下技术特征:\n- 基体材料\n- 增强相\n- 涂层\n- .',
        context='现有技术: 对比文件D3:\n文献类型: 中国发明专利\n公开号: EP1716157B2\n公开日: 2011-08-23\n\n公开内容:\n展示了相近的应用场景,解决类似的技术问题\n展示了相.',
        task_type='capability_2_complex',
        analysis_result='[综合分析]\n本案例涉及多个法律问题,需要综合考虑:\n1. 新颖性评估\n2. 创造性评估\n3. 其他法律问题\n\n结论: 需要进一步分析',
    ).with_inputs("user_input", "context", "task_type"),

]
