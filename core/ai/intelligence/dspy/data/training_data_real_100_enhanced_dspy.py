
# DSPy Training Data - Enhanced Real Patent Cases
# Source: Qdrant patent_decisions collection (308,888 records)
# Generated: 100 cases
import dspy

training_data = [
    # Case 1: 通用领域CN6315124X专利新颖性争议案(决定书)
    # Decision: 584053, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 584053',
        context='[决定书信息]\n决定文号: 584053\n决定类型: 决定书\n决定日期: 2024-07-05\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='维持202130860727.8号外观设计专利权有效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定,自.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 2: 通用领域CN9496807X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 567344, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 567344',
        context='[决定书信息]\n决定文号: 567344\n决定类型: 无效宣告请求审查决定\n决定日期: 2016-06-08\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第567344号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 3: 通用领域CN8171382X专利新颖性争议案(决定书)
    # Decision: 582417, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 582417',
        context='[决定书信息]\n决定文号: 582417\n决定类型: 决定书\n决定日期: 2020-10-15\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='维持第202030612330.2号外观设计专利权有效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定,.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 4: 通信技术领域CN7370341X专利新颖性争议案(决定书)
    # Decision: 567069, Type: novelty
    # Field: 通信技术, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 567069',
        context='[决定书信息]\n决定文号: 567069\n决定类型: 决定书\n决定日期: 2020-04-03\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='对于证据5公开的上述内容,双方当事人的主要争议焦点在于:证据5中的导线体2是否公开了本专利中的硬针件。请求人主张,二者.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 5: 通用领域CN3899125X专利新颖性争议案(决定书)
    # Decision: 580134, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 580134',
        context='[决定书信息]\n决定文号: 580134\n决定类型: 决定书\n决定日期: 2018-11-02\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告第201620106181.0号实用新型专利权全部无效。\n当事人对本决定不服的,根据专利法第46条第2款的规定,.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 6: 通用领域CN5765962X专利新颖性争议案(决定书)
    # Decision: 568922, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 568922',
        context='[决定书信息]\n决定文号: 568922\n决定类型: 决定书\n决定日期: 2019-06-14\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='理由不能成立。\n决定\n维持201830495211.6号外观设计专利权有效。',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 7: 通用领域CN8628350X专利新颖性争议案(决定书)
    # Decision: 566671, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 566671',
        context='[决定书信息]\n决定文号: 566671\n决定类型: 决定书\n决定日期: 2013-12-09\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告201320807274.2号实用新型专利权全部无效。\n当事人对本决定不服的,根据专利法第46条第2款的规定,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 8: 通用领域CN4662361X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 583144, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 583144',
        context='[决定书信息]\n决定文号: 583144\n决定类型: 无效宣告请求审查决定\n决定日期: 2018-09-10\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 9: 通用领域CN4225779X专利新颖性争议案(决定书)
    # Decision: 442001, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 442001',
        context='[决定书信息]\n决定文号: 442001\n决定类型: 决定书\n决定日期: 2014-03-20\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='本专利的专利号为201510063688.2,优先权日为2014年03月20日,申请日为2015年02月06日,授权公.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 10: 通用领域CN201630582439.专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566538, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566538',
        context='[决定书信息]\n决定文号: 566538\n决定类型: 无效宣告请求审查决定\n决定日期: 2018-06-05\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由是涉案专利不符合专利法第27条第2款,第23条第1款和第23条第2款的规定,并提交了如下证据:\n证据1:专利号为.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 11: 通用领域CN7124524X专利充分公开争议案(决定书)
    # Decision: 560761, Type: disclosure
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560761',
        context='[决定书信息]\n决定文号: 560761\n决定类型: 决定书\n决定日期: 2022-08-28\n决定结果: 未.',
        task_type='capability_2_disclosure',
        analysis_summary='对于说明书中仅给出一个具体实施方式,权利要求采用相应的功能予以限定的情形,不能因此直接认定该功能性特征导致权利要求得不.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 12: 通用领域CN7432528X专利程序问题争议案(无效宣告请求审查决定)
    # Decision: 580299, Type: procedural
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 580299',
        context='[决定书信息]\n决定文号: 580299\n决定类型: 无效宣告请求审查决定\n决定日期: 2024-01-10\n.',
        task_type='capability_2_procedural',
        analysis_summary='理由是涉案专利不符合专利法第23条第2款的规定,并提交了如下证据:\n证据1:201530236553.2号中国外观设.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 13: 通用领域CN2091079X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560491, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560491',
        context='[决定书信息]\n决定文号: 560491\n决定类型: 无效宣告请求审查决定\n决定日期: 2019-08-27\n.',
        task_type='capability_2_novelty',
        analysis_summary='本无效宣告请求涉及国家知识产权局于2019年8月27日授权公告的201920143687.2号、名称为“一种卷布灯”的.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 14: 通用领域CN7925079X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 582332, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 582332',
        context='[决定书信息]\n决定文号: 582332\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-07-25\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第582332号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 15: 通用领域CN5476190X专利新颖性争议案(决定书)
    # Decision: 582991, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 582991',
        context='[决定书信息]\n决定文号: 582991\n决定类型: 决定书\n决定日期: 2019-03-14\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1、法律依据\n专利法第23条第1款规定:授予专利权的外观设计,应当不属于现有设计;也没有任何单位或者个人就同样的外观.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 16: 通信技术领域CN6484018X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560537, Type: novelty
    # Field: 通信技术, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560537',
        context='[决定书信息]\n决定文号: 560537\n决定类型: 无效宣告请求审查决定\n决定日期: 2019-07-16\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由是:相对于证据1,涉案专利不符合专利法第23条第1款的规定;相对于证据1或者证据1和证据5的组合,涉案专利不符合专.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 17: 通用领域CN4307782X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 582042, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 582042',
        context='[决定书信息]\n决定文号: 582042\n决定类型: 无效宣告请求审查决定\n决定日期: 2014-08-13\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第582042号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 18: 新能源领域CN7181453X专利新颖性争议案(决定书)
    # Decision: 569183, Type: novelty
    # Field: 新能源, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 569183',
        context='[决定书信息]\n决定文号: 569183\n决定类型: 决定书\n决定日期: 2024-01-29\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1、法律依据\n专利法第23条第2款规定:授予专利权的外观设计与现有设计或者现有设计特征的组合相比,应当具有明显区别。.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 19: 通用领域CN6947025X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 580326, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 580326',
        context='[决定书信息]\n决定文号: 580326\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-12-20\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第580326号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 20: 通用领域CN2755552X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 580643, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 580643',
        context='[决定书信息]\n决定文号: 580643\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-12-15\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第580643号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 21: 通用领域CN8263479X专利新颖性争议案(决定书)
    # Decision: 564405, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 564405',
        context='[决定书信息]\n决定文号: 564405\n决定类型: 决定书\n决定日期: 2020-11-17\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告202010695365.6号发明专利权全部无效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定,自.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 22: 通用领域CN6821391X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560639, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560639',
        context='[决定书信息]\n决定文号: 560639\n决定类型: 无效宣告请求审查决定\n决定日期: 2014-12-29\n.',
        task_type='capability_2_novelty',
        analysis_summary='在第56487号无效宣告请求审查决定维持有效的权利要求2-9的基础上,维持201510155566.6号发明专利权有效.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 23: 通用领域CN6553089X专利主体资格争议案(决定书)
    # Decision: 581633, Type: subject
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 581633',
        context='[决定书信息]\n决定文号: 581633\n决定类型: 决定书\n决定日期: 2024-05-21\n决定结果: 未.',
        task_type='capability_2_subject',
        analysis_summary='理由不充分,故合议组不予支持;证据4公证书原件与复印件一致,且形式上无明显瑕疵,故合议组对证据4公证书的真实性予以确认.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 24: 通用领域CN4545037X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566836, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566836',
        context='[决定书信息]\n决定文号: 566836\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-09-22\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由不成立。',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 25: 通用领域CN304863319S专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 581915, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 581915',
        context='[决定书信息]\n决定文号: 581915\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-01-06\n.',
        task_type='capability_2_novelty',
        analysis_summary='如下证据:\n证据1:KR300290782S,公告日为2002年02月01日,及其中文译文;\n证据2:CN3048.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 26: 通用领域CN1216208X专利新颖性争议案(决定书)
    # Decision: 580388, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 580388',
        context='[决定书信息]\n决定文号: 580388\n决定类型: 决定书\n决定日期: 2005-01-22\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='请求人主张,证据1已经公开了连接板10与板式颊板15转动连接,即公开了“悬挂装置通过一个连接板与浮动支承侧板铰接连接”.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 27: 通用领域CN7850115X专利新颖性争议案(决定书)
    # Decision: 566412, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 566412',
        context='[决定书信息]\n决定文号: 566412\n决定类型: 决定书\n决定日期: 2020-12-07\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告2020225944057.0号实用新型专利权全部无效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 28: 通用领域CN1967495X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566697, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566697',
        context='[决定书信息]\n决定文号: 566697\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-08-11\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由为涉案专利不符合专利法第23条第2款的规定,同时提交了如下证据:\n证据1:中国发明专利201811269840..',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 29: 生物医药领域CN6530992X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566283, Type: novelty
    # Field: 生物医药, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566283',
        context='[决定书信息]\n决定文号: 566283\n决定类型: 无效宣告请求审查决定\n决定日期: 2015-10-21\n.',
        task_type='capability_2_novelty',
        analysis_summary='本无效宣告请求涉及国家知识产权局于2015年10月21日授权公告的、名称为“瓶盖及具有该瓶盖的饮料包装”的发明专利权(.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 30: 通用领域CN6980632X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 569107, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 569107',
        context='[决定书信息]\n决定文号: 569107\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-11-23\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由不再评述。',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 31: 通用领域CN4541018X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566312, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566312',
        context='[决定书信息]\n决定文号: 566312\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-07-01\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第566312号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 32: 通用领域CN8422622X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 583863, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 583863',
        context='[决定书信息]\n决定文号: 583863\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-10-11\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 33: 通用领域CN3184261X专利新颖性争议案(决定书)
    # Decision: 560352, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560352',
        context='[决定书信息]\n决定文号: 560352\n决定类型: 决定书\n决定日期: 2013-03-15\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='宣告201480024198.5号发明专利的权利要求1-11、13-28、30-32、34-43无效,在权利要求12、.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 34: 通用领域CN9557640X专利充分公开争议案(决定书)
    # Decision: 583064, Type: disclosure
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 583064',
        context='[决定书信息]\n决定文号: 583064\n决定类型: 决定书\n决定日期: 2021-09-01\n决定结果: 未.',
        task_type='capability_2_disclosure',
        analysis_summary='关于平行姿态中气液分离器的位置,本专利说明书以及原从属权利要求18中的相关记载均为“在所述平行姿态中,所述气液分离器在.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 35: 通用领域CN4833136X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 581929, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 581929',
        context='[决定书信息]\n决定文号: 581929\n决定类型: 无效宣告请求审查决定\n决定日期: 2016-01-13\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 36: 机器人领域CN9852544X专利清楚性争议案(决定书)
    # Decision: 581835, Type: clarity
    # Field: 机器人, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 581835',
        context='[决定书信息]\n决定文号: 581835\n决定类型: 决定书\n决定日期: 2021-06-11\n决定结果: 未.',
        task_type='capability_2_clarity',
        analysis_summary='(一)审查基础\n本案中,专利权人于2024年07月24日修改了权利要求书,将权利要求3中的技术特征“所述清洁机器人具.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 37: 通用领域CN4020306X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560531, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560531',
        context='[决定书信息]\n决定文号: 560531\n决定类型: 无效宣告请求审查决定\n决定日期: 2021-04-02\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第560531号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 38: 通用领域CN7679242X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560791, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560791',
        context='[决定书信息]\n决定文号: 560791\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-10-31\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第560791号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 39: 通用领域CN4464355X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560895, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560895',
        context='[决定书信息]\n决定文号: 560895\n决定类型: 无效宣告请求审查决定\n决定日期: 2016-03-16\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 40: 通用领域CN1018341X专利新颖性争议案(决定书)
    # Decision: 522001, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 522001',
        context='[决定书信息]\n决定文号: 522001\n决定类型: 决定书\n决定日期: 2014-04-23\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1．法律依据\n专利法第23条第1款规定:授予专利权的外观设计,应当不属于现有设计;也没有任何单位或者个人就同样的外观.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 41: 通用领域CN8584150X专利新颖性争议案(决定书)
    # Decision: 580558, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 580558',
        context='[决定书信息]\n决定文号: 580558\n决定类型: 决定书\n决定日期: 2024-03-13\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1、法律依据\n专利法第23条第2款规定:授予专利权的外观设计与现有设计或者现有设计特征的组合相比,应当具有明显区别。.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 42: 通用领域CN5507286X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 561795, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 561795',
        context='[决定书信息]\n决定文号: 561795\n决定类型: 无效宣告请求审查决定\n决定日期: 2012-11-22\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 43: 通用领域CN5203327X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 580300, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 580300',
        context='[决定书信息]\n决定文号: 580300\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-12-18\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第580300号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 44: 通用领域CN3336919X专利新颖性争议案(决定书)
    # Decision: 560924, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 560924',
        context='[决定书信息]\n决定文号: 560924\n决定类型: 决定书\n决定日期: 2018-01-09\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告201730223885.6号外观设计专利权全部无效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 45: 通用领域CN1701652X专利新颖性争议案(决定书)
    # Decision: 583493, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 583493',
        context='[决定书信息]\n决定文号: 583493\n决定类型: 决定书\n决定日期: 2021-11-28\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='理由证明在现有设计中存在将证据5的玩具鲸鱼产品作为连接件在特定位置进行组合的组合手法的启示。由于缺少组合的启示,证据5.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 46: 通用领域CN5303002X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 569172, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 569172',
        context='[决定书信息]\n决定文号: 569172\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-12-21\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 47: 通用领域CN5190841X专利新颖性争议案(决定书)
    # Decision: 581410, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 581410',
        context='[决定书信息]\n决定文号: 581410\n决定类型: 决定书\n决定日期: 2020-09-16\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='维持第202022032659.9号实用新型专利权有效。\n当事人对本决定不服的,根据专利法第46条第2款的规定,可以.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 48: 通用领域CN3382113X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 569125, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 569125',
        context='[决定书信息]\n决定文号: 569125\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-07-14\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第569125号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 49: 通用领域CN7954494X专利新颖性争议案(决定书)
    # Decision: 562215, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 562215',
        context='[决定书信息]\n决定文号: 562215\n决定类型: 决定书\n决定日期: 2019-01-03\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='合议组认为,本专利权利要求1限定了各个部件的连接及安装位置关系,说明书仅在第0020段记载了本专利的工作原理:本专利的.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 50: 通用领域CN8009197X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560366, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560366',
        context='[决定书信息]\n决定文号: 560366\n决定类型: 无效宣告请求审查决定\n决定日期: 2020-01-10\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 51: 通用领域CN2550194X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 582145, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 582145',
        context='[决定书信息]\n决定文号: 582145\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-04-07\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第582145号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 52: 通用领域CN4241189X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566996, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566996',
        context='[决定书信息]\n决定文号: 566996\n决定类型: 无效宣告请求审查决定\n决定日期: 2021-04-30\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 53: 通用领域CN3212576X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560228, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560228',
        context='[决定书信息]\n决定文号: 560228\n决定类型: 无效宣告请求审查决定\n决定日期: 2020-06-16\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由是:本专利权利要求1不符合中华人民共和国专利法(下称专利法)第22条第3款的规定。同时,请求人提交了如下证据:\n.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 54: 通用领域CN6931047X专利新颖性争议案(决定书)
    # Decision: 560061, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560061',
        context='[决定书信息]\n决定文号: 560061\n决定类型: 决定书\n决定日期: 2022-09-09\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1．法律依据\n专利法第23条第2款规定:授予专利权的外观设计与现有设计或者现有设计特征的组合相比,应当具有明显区别。.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 55: 通用领域CN6169311X专利创造性争议案(决定书)
    # Decision: 515001, Type: creative
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 515001',
        context='[决定书信息]\n决定文号: 515001\n决定类型: 决定书\n决定日期: 2019-05-24\n决定结果: 未.',
        task_type='capability_2_creative',
        analysis_summary='理由和相应的证据表明其为本领域的公知常识或常规技术手段,并且该区别技术特征可以为该技术方案能够带来有益的技术效果,则认.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 56: 通用领域CN1350977X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 569464, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 569464',
        context='[决定书信息]\n决定文号: 569464\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-03-15\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 57: 通用领域CN1631698X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 567612, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 567612',
        context='[决定书信息]\n决定文号: 567612\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-04-01\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由不再作评述。\n基于以上事实和理由,本案合议组作出如下审查决定。\n\n如下审查决定。',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 58: 通用领域CN1153815X专利主体资格争议案(决定书)
    # Decision: 583892, Type: subject
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 583892',
        context='[决定书信息]\n决定文号: 583892\n决定类型: 决定书\n决定日期: 2021-07-06\n决定结果: 未.',
        task_type='capability_2_subject',
        analysis_summary='1.审查基础\n在本案审查过程中,专利权人在2024年05月30日提交的意见陈述中指出修改权利要求5,将权利要求5的技.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 59: 通用领域CN4179082X专利新颖性争议案(决定书)
    # Decision: 580300, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 580300',
        context='[决定书信息]\n决定文号: 580300\n决定类型: 决定书\n决定日期: 2023-12-18\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='证据 1 是(2022)浙永证内字第 3350 号公证书,其内容涉及微信账号的朋友圈证据保全,其通过浏览微信账号为“一.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 60: 通用领域CN2201849X专利创造性争议案(无效宣告请求审查决定)
    # Decision: 568449, Type: creative
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 568449',
        context='[决定书信息]\n决定文号: 568449\n决定类型: 无效宣告请求审查决定\n决定日期: 2014-06-03\n.',
        task_type='capability_2_creative',
        analysis_summary='1. 审查基础\n本无效宣告请求审查决定的基础为本专利的授权公告文本。\n2. 证据认定\n请求人提交的证据1-5均为.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 61: 通用领域CN8469471X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 567453, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 567453',
        context='[决定书信息]\n决定文号: 567453\n决定类型: 无效宣告请求审查决定\n决定日期: 2020-09-15\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 62: 通用领域CN1059183X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 566541, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 566541',
        context='[决定书信息]\n决定文号: 566541\n决定类型: 无效宣告请求审查决定\n决定日期: 2020-11-10\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 63: 新能源领域CN8844137X专利新颖性争议案(决定书)
    # Decision: 560575, Type: novelty
    # Field: 新能源, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560575',
        context='[决定书信息]\n决定文号: 560575\n决定类型: 决定书\n决定日期: 2010-09-28\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='本专利的专利号为201180046489.0 ,优先权日为2010年09月28日,申请日为2011年06月08日,授权.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 64: 通用领域CN1079703X专利新颖性争议案(决定书)
    # Decision: 566594, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 566594',
        context='[决定书信息]\n决定文号: 566594\n决定类型: 决定书\n决定日期: 2015-07-01\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告201410036804.7号发明专利权全部无效。\n当事人对本决定不服的,根据专利法第46条第2款的规定,可以自.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 65: 通用领域CN5433304X专利新颖性争议案(决定书)
    # Decision: 568524, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 568524',
        context='[决定书信息]\n决定文号: 568524\n决定类型: 决定书\n决定日期: 2023-11-28\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告 202230170796.0 号外观设计专利权全部无效。\n当事人对本决定不服的,可以根据专利法第46条第2款的.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 66: 通用领域CN2007149X专利新颖性争议案(决定书)
    # Decision: 560947, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 560947',
        context='[决定书信息]\n决定文号: 560947\n决定类型: 决定书\n决定日期: 2018-04-16\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告201820538770.5号实用新型专利权全部无效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 67: 通信技术领域CN7180167X专利新颖性争议案(决定书)
    # Decision: 582306, Type: novelty
    # Field: 通信技术, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 582306',
        context='[决定书信息]\n决定文号: 582306\n决定类型: 决定书\n决定日期: 2004-09-27\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='本专利的专利号为200410080936.6,申请日为2004年09月27日,授权公告日为2008年01月02日,专利.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 68: 通用领域CN3687990X专利主体资格争议案(决定书)
    # Decision: 580344, Type: subject
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 580344',
        context='[决定书信息]\n决定文号: 580344\n决定类型: 决定书\n决定日期: 2022-02-01\n决定结果: 未.',
        task_type='capability_2_subject',
        analysis_summary='将本专利权利要求1的方案与证据1公开的内容相比可知,证据1中的蒸烤装置相当于本专利中的“带蒸汽功能的烹饪器具”;证据1.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 69: 通用领域CN9783484X专利新颖性争议案(决定书)
    # Decision: 580321, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 580321',
        context='[决定书信息]\n决定文号: 580321\n决定类型: 决定书\n决定日期: 2023-09-22\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='经对比可知,证据1与本专利权利要求1限定的方法基本相同,结合证据1图4-29也可确定证据1公开了权利要求1限定的涉及三.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 70: 通用领域CN3379267X专利新颖性争议案(决定书)
    # Decision: 560746, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560746',
        context='[决定书信息]\n决定文号: 560746\n决定类型: 决定书\n决定日期: 2020-12-31\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='本专利的专利号为202011623656.0,申请日为2020年12月31日,授权公告日为2021年08月27日,专利.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 71: 通用领域CN6268265X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 565782, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 565782',
        context='[决定书信息]\n决定文号: 565782\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-05-25\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 72: 通用领域CN202030045182.专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 567326, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 567326',
        context='[决定书信息]\n决定文号: 567326\n决定类型: 无效宣告请求审查决定\n决定日期: 2020-01-11\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由是涉案专利不符合专利法第9条第1款和第23条2款的规定,并提交了如下证据:\n证据1:专利号为CN20203004.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 73: 通用领域CN1071713X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 465001, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 465001',
        context='[决定书信息]\n决定文号: 465001\n决定类型: 无效宣告请求审查决定\n决定日期: 2016-11-11\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 74: 通用领域CN1075753X专利新颖性争议案(决定书)
    # Decision: 245001, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 245001',
        context='[决定书信息]\n决定文号: 245001\n决定类型: 决定书\n决定日期: 2020-07-10\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1、法律依据\n专利法第23条第2款规定:授予专利权的外观设计与现有设计或者现有设计特征的组合相比,应当具有明显区别。.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 75: 通用领域CN3046699X专利新颖性争议案(决定书)
    # Decision: 560852, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560852',
        context='[决定书信息]\n决定文号: 560852\n决定类型: 决定书\n决定日期: 2020-05-15\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='维持2020208075844号实用新型专利权有效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定,自收.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 76: 通用领域CN4065979X专利程序问题争议案(无效宣告请求审查决定)
    # Decision: 560445, Type: procedural
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560445',
        context='[决定书信息]\n决定文号: 560445\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-09-27\n.',
        task_type='capability_2_procedural',
        analysis_summary='理由是涉案专利不符合专利法第23条第2款的规定,并提交了下列证据:\n证据1:专利号为002772798-0001的欧.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 77: 通用领域CN6108892X专利新颖性争议案(决定书)
    # Decision: 584150, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 584150',
        context='[决定书信息]\n决定文号: 584150\n决定类型: 决定书\n决定日期: 2020-11-03\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='宣告202030208105.2号外观设计专利权无效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定,自.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 78: 通用领域CN306954229S专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 582153, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 582153',
        context='[决定书信息]\n决定文号: 582153\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-04-14\n.',
        task_type='capability_2_novelty',
        analysis_summary='理由是涉案专利不符合专利法第23条第2款的规定,请求宣告涉案专利全部无效,同时提交了如下证据1-8:\n证据1:授权公.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 79: 通用领域CN1137292X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 560681, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 560681',
        context='[决定书信息]\n决定文号: 560681\n决定类型: 无效宣告请求审查决定\n决定日期: 2022-12-21\n.',
        task_type='capability_2_novelty',
        analysis_summary='宣告专利权全部无效。\n宣告专利权部分无效。\n维持专利权有效。\n根据专利法第46条第2款的规定,对本决定不服的,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 80: 通用领域CN9637416X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 581885, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 581885',
        context='[决定书信息]\n决定文号: 581885\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-01-10\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第581885号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 81: 通用领域CN4723547X专利新颖性争议案(决定书)
    # Decision: 582965, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 582965',
        context='[决定书信息]\n决定文号: 582965\n决定类型: 决定书\n决定日期: 2019-02-26\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='(5)随后合议组进行了充分调查,双方当事人充分发表了意见。\n在此基础上,合议组认为本案事实已经清楚,可以依法作出审查.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 82: 通用领域CN9532462X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 582197, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 582197',
        context='[决定书信息]\n决定文号: 582197\n决定类型: 无效宣告请求审查决定\n决定日期: 2020-01-21\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第582197号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 83: 通用领域CN7884089X专利创造性争议案(决定书)
    # Decision: 560491, Type: creative
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560491',
        context='[决定书信息]\n决定文号: 560491\n决定类型: 决定书\n决定日期: 2019-08-27\n决定结果: 未.',
        task_type='capability_2_creative',
        analysis_summary='1.证据认定\n证据1-7为专利文献,专利权人未对其真实性提出异议。经核实,合议组对证据1-7的真实性予以确认。证据1.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 84: 通用领域CN7136415X专利新颖性争议案(决定书)
    # Decision: 560074, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560074',
        context='[决定书信息]\n决定文号: 560074\n决定类型: 决定书\n决定日期: 2022-07-12\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1、法律依据\n专利法第23条第2款规定:授予专利权的外观设计与现有设计或者现有设计特征的组合相比,应当具有明显区别。.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 85: 通用领域CN6338251X专利新颖性争议案(决定书)
    # Decision: 561275, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 561275',
        context='[决定书信息]\n决定文号: 561275\n决定类型: 决定书\n决定日期: 2022-09-29\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='请求人提交的证据1是意大利外观设计专利文献及中文译文,对其真实性以及翻译的准确性,专利权人没有提出异议。经核实,合议组.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 86: 通用领域CN6905212X专利新颖性争议案(决定书)
    # Decision: 560306, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 560306',
        context='[决定书信息]\n决定文号: 560306\n决定类型: 决定书\n决定日期: 2013-04-17\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='在专利权人于2022年07月15日提交的权利要求第1-9项的基础上,宣告201220434418.X号实用新型专利权全.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 87: 通用领域CN1337275X专利创造性争议案(无效宣告请求审查决定)
    # Decision: 567626, Type: creative
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 567626',
        context='[决定书信息]\n决定文号: 567626\n决定类型: 无效宣告请求审查决定\n决定日期: 2021-11-23\n.',
        task_type='capability_2_creative',
        analysis_summary='(一)关于审查基础\n专利权人于2024年01月16日提交了修改的权利要求书,专利权人陈述的修改方式为:将权利要求2、.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 88: 通用领域CN4918707X专利新颖性争议案(决定书)
    # Decision: 566535, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 566535',
        context='[决定书信息]\n决定文号: 566535\n决定类型: 决定书\n决定日期: 2023-01-07\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='关于证据1-3的公开性,基于对抖音短视频管理机制的调查,该平台为用户开放了权限设置功能,包括作品“对所有人可见”、“仅.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 89: 通用领域CN1184375X专利新颖性争议案(决定书)
    # Decision: 580871, Type: novelty
    # Field: 通用, Risk: 高风险
    dspy.Example(
        user_input='分析决定书决定: 580871',
        context='[决定书信息]\n决定文号: 580871\n决定类型: 决定书\n决定日期: 2022-08-13\n决定结果: 专.',
        task_type='capability_2_novelty',
        analysis_summary='宣告202222133201.1号实用新型专利权全部无效。\n当事人对本决定不服的,根据专利法第46条第2款的规定,可.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 90: 通用领域CN2555342X专利新颖性争议案(决定书)
    # Decision: 567662, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 567662',
        context='[决定书信息]\n决定文号: 567662\n决定类型: 决定书\n决定日期: 2018-07-11\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='请求人提交了专利号为ZL201830251564.1的外观设计专利权评价报告及该报告涉及的相关文件,且使用其中的对比设.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 91: 通用领域CN4198109X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 581341, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 581341',
        context='[决定书信息]\n决定文号: 581341\n决定类型: 无效宣告请求审查决定\n决定日期: 2024-01-16\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第581341号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 92: 通用领域CN6443943X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 193001, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 193001',
        context='[决定书信息]\n决定文号: 193001\n决定类型: 无效宣告请求审查决定\n决定日期: 2015-08-19\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第193001号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 93: 通用领域CN9746720X专利新颖性争议案(决定书)
    # Decision: 584023, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 584023',
        context='[决定书信息]\n决定文号: 584023\n决定类型: 决定书\n决定日期: 2024-07-19\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='维持202130032581.8号外观设计专利权有效。\n当事人对本决定不服的,可以根据专利法第46条第2款的规定,自.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 94: 通用领域CN3598398X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 568362, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 568362',
        context='[决定书信息]\n决定文号: 568362\n决定类型: 无效宣告请求审查决定\n决定日期: 2023-10-20\n.',
        task_type='capability_2_novelty',
        analysis_summary='无效宣告请求审查决定书\n(第568362号)\n根据专利法第46条第1款的规定,国家知识产权局对无效宣告请求人就上述.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 95: 通用领域CN4047040X专利新颖性争议案(无效宣告请求审查决定)
    # Decision: 562733, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析无效宣告请求审查决定决定: 562733',
        context='[决定书信息]\n决定文号: 562733\n决定类型: 无效宣告请求审查决定\n决定日期: 2015-03-25\n.',
        task_type='capability_2_novelty',
        analysis_summary='本无效宣告请求涉及中华人民共和国国家知识产权局于2015年03月25日授权公告的专利号为201110041436.1,.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 96: 通信技术领域CN4653615X专利新颖性争议案(决定书)
    # Decision: 568262, Type: novelty
    # Field: 通信技术, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 568262',
        context='[决定书信息]\n决定文号: 568262\n决定类型: 决定书\n决定日期: 2020-07-29\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='本专利的专利号为202221261304.X,优先权日为2020年07月29日,申请日为2021年07月29日,授权公.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 97: 通用领域CN6394730X专利新颖性争议案(决定书)
    # Decision: 582016, Type: novelty
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 582016',
        context='[决定书信息]\n决定文号: 582016\n决定类型: 决定书\n决定日期: 2022-02-11\n决定结果: 未.',
        task_type='capability_2_novelty',
        analysis_summary='1、法律依据\n专利法第23条第2款规定:授予专利权的外观设计与现有设计或者现有设计特征的组合相比,应当具有明显区别。.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 98: 通用领域CN3843980X专利创造性争议案(决定书)
    # Decision: 565667, Type: creative
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 565667',
        context='[决定书信息]\n决定文号: 565667\n决定类型: 决定书\n决定日期: 2021-11-02\n决定结果: 维.',
        task_type='capability_2_creative',
        analysis_summary='1、关于审查基础\n本决定以第52440号决定维持有效的权利要求1-8为审查基础作出。\n关于证据\n请求人Ⅰ提交的证.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 99: 通用领域CN5564602X专利创造性争议案(决定书)
    # Decision: 560135, Type: creative
    # Field: 通用, Risk: 中风险
    dspy.Example(
        user_input='分析决定书决定: 560135',
        context='[决定书信息]\n决定文号: 560135\n决定类型: 决定书\n决定日期: 2021-02-23\n决定结果: 未.',
        task_type='capability_2_creative',
        analysis_summary='综上,本领域技术人员在证据1、证据5和公知常识结合的基础上能够显而易见地获得权利要求1所限定的技术方案,权利要求1不具.',
    ).with_inputs("user_input", "context", "task_type"),

    # Case 100: 关于航空航天领域专利的新颖性争议
    # Decision: WX92650, Type: novelty
    # Field: 航空航天, Risk: 中风险
    dspy.Example(
        user_input='分析复审请求审查决定决定: WX92650',
        context='[决定书信息]\n决定文号: WX92650\n决定类型: 复审请求审查决定\n决定日期: 2016-08-14\n决.',
        task_type='capability_2_novelty',
        analysis_summary='本案复审请求审查决定涉及novelty问题的认定。',
    ).with_inputs("user_input", "context", "task_type"),

]

