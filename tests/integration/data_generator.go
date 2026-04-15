package integration

import (
	"fmt"
	"math/rand"
	"time"
)

type DataGenerator struct {
	rand *rand.Rand
}

func NewDataGenerator() *DataGenerator {
	return &DataGenerator{
		rand: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

func (dg *DataGenerator) GeneratePatentData(config *PatentDataConfig) map[string]interface{} {
	patent := make(map[string]interface{})

	patent["patent_id"] = fmt.Sprintf("PAT_%d", dg.rand.Intn(999999))
	patent["title"] = dg.generatePatentTitle(config.Technology, config.Complexity)
	patent["abstract"] = dg.generatePatentAbstract(config.Technology, config.Complexity)
	patent["claims"] = dg.generatePatentClaims(config.Technology, config.Complexity)
	patent["description"] = dg.generatePatentDescription(config.Technology, config.Complexity)
	patent["inventors"] = dg.generateInventors()
	patent["assignee"] = dg.generateAssignee()
	patent["filing_date"] = time.Now().AddDate(0, 0, -dg.rand.Intn(365)).Format("2006-01-02")
	patent["country"] = config.Country
	patent["technology_field"] = config.Technology
	patent["complexity"] = config.Complexity

	return patent
}

func (dg *DataGenerator) generatePatentTitle(technology, complexity string) string {
	techPrefixes := map[string][]string{
		"AI": {
			"基于深度学习的", "人工智能驱动的", "机器学习增强的",
			"神经网络优化的", "智能算法的",
		},
		"IoT": {
			"物联网智能", "传感器网络", "边缘计算",
			"互联设备", "无线传感",
		},
		"Blockchain": {
			"区块链技术", "分布式账本", "智能合约",
			"去中心化", "加密货币",
		},
	}

	techSuffixes := map[string][]string{
		"simple":  {"系统", "装置", "方法"},
		"medium":  {"优化系统", "智能平台", "自动化装置"},
		"complex": {"多模态分析系统", "自适应优化平台", "智能决策支持系统"},
	}

	prefixes := techPrefixes[technology]
	suffixes := techSuffixes[complexity]

	prefix := prefixes[dg.rand.Intn(len(prefixes))]
	suffix := suffixes[dg.rand.Intn(len(suffixes))]

	return prefix + suffix
}

func (dg *DataGenerator) generatePatentAbstract(technology, complexity string) string {
	sentences := map[string][]string{
		"AI": {
			"本发明涉及一种基于人工智能技术的数据处理方法。",
			"通过深度学习算法对输入数据进行分析和处理。",
			"系统采用神经网络模型实现智能决策。",
			"该技术能够显著提高数据处理的准确性和效率。",
		},
		"IoT": {
			"本发明提供一种物联网设备的数据采集和处理方法。",
			"通过分布式传感器网络实时收集环境数据。",
			"系统支持多种通信协议和设备类型。",
			"该技术能够实现大规模设备的智能化管理。",
		},
		"Blockchain": {
			"本发明涉及一种基于区块链技术的数据安全存储方法。",
			"采用分布式账本技术确保数据的不可篡改性。",
			"系统支持智能合约的自动执行。",
			"该技术能够提供高度可信的数据交换平台。",
		},
	}

	techSentences := sentences[technology]

	numSentences := 2
	if complexity == "medium" {
		numSentences = 3
	} else if complexity == "complex" {
		numSentences = 4
	}

	abstract := ""
	for i := 0; i < numSentences; i++ {
		if i > 0 {
			abstract += " "
		}
		abstract += techSentences[dg.rand.Intn(len(techSentences))]
	}

	return abstract
}

func (dg *DataGenerator) generatePatentClaims(technology, complexity string) string {
	claims := make([]string, 0)

	numClaims := 1
	if complexity == "medium" {
		numClaims = 3
	} else if complexity == "complex" {
		numClaims = 5
	}

	for i := 0; i < numClaims; i++ {
		claimNum := i + 1
		claim := fmt.Sprintf("%d. 一种%s技术，其特征在于包括：", claimNum, technology)

		steps := 2
		if complexity == "medium" {
			steps = 3
		} else if complexity == "complex" {
			steps = 4
		}

		for j := 0; j < steps; j++ {
			claim += fmt.Sprintf("步骤%d：数据处理；", j+1)
		}

		claims = append(claims, claim)
	}

	claimText := ""
	for i, claim := range claims {
		if i > 0 {
			claimText += "\n"
		}
		claimText += claim
	}

	return claimText
}

func (dg *DataGenerator) generatePatentDescription(technology, complexity string) string {
	sections := make([]string, 0)

	sections = append(sections, "【技术领域】")
	sections = append(sections, fmt.Sprintf("本发明涉及%s技术领域，特别涉及一种智能化数据处理系统。", technology))

	sections = append(sections, "【背景技术】")
	sections = append(sections, "现有的数据处理技术存在效率低、准确性差等问题，需要更加智能化的解决方案。")

	sections = append(sections, "【发明内容】")
	sections = append(sections, "本发明的目的是提供一种高效、准确的数据处理方法和系统。")

	sections = append(sections, "【具体实施方式】")
	sections = append(sections, "下面结合附图对本发明的具体实施方式进行详细说明。")

	if complexity == "complex" {
		sections = append(sections, "【实施例】")
		sections = append(sections, "实施例1：采用本技术进行图像识别处理。")
		sections = append(sections, "实施例2：采用本技术进行自然语言处理。")
	}

	description := ""
	for _, section := range sections {
		if description != "" {
			description += "\n\n"
		}
		description += section
	}

	return description
}

func (dg *DataGenerator) generateInventors() []string {
	firstNames := []string{"张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"}
	lastNames := []string{"伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军"}

	numInventors := 1 + dg.rand.Intn(3)
	inventors := make([]string, 0, numInventors)

	for i := 0; i < numInventors; i++ {
		firstName := firstNames[dg.rand.Intn(len(firstNames))]
		lastName := lastNames[dg.rand.Intn(len(lastNames))]
		inventors = append(inventors, firstName+lastName)
	}

	return inventors
}

func (dg *DataGenerator) generateAssignee() string {
	companies := []string{
		"北京科技创新有限公司",
		"上海智能技术研究院",
		"深圳人工智能科技有限公司",
		"广州未来科技有限公司",
		"杭州云计算有限公司",
	}

	return companies[dg.rand.Intn(len(companies))]
}
