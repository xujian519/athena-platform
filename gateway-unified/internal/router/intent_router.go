package router

import (
	"regexp"
	"strings"
	"sync"
)

// IntentType 用户意图类型
type IntentType string

const (
	// IntentPatentAnalysis 专利分析意图
	IntentPatentAnalysis IntentType = "patent_analysis"
	// IntentCaseSearch 案例检索意图
	IntentCaseSearch IntentType = "case_search"
	// IntentLegalConsult 法律咨询意图
	IntentLegalConsult IntentType = "legal_consult"
	// IntentPatentSearch 专利检索意图
	IntentPatentSearch IntentType = "patent_search"
	// IntentCreativityAnalysis 创造性分析意图
	IntentCreativityAnalysis IntentType = "creativity_analysis"
	// IntentNoveltyAnalysis 新颖性分析意图
	IntentNoveltyAnalysis IntentType = "novelty_analysis"
	// IntentInfringementAnalysis 侵权分析意图
	IntentInfringementAnalysis IntentType = "infringement_analysis"
	// IntentInvalidationAnalysis 无效宣告意图
	IntentInvalidationAnalysis IntentType = "invalidation_analysis"
	// IntentGeneralQuery 一般查询意图
	IntentGeneralQuery IntentType = "general_query"
	// IntentUnknown 未知意图
	IntentUnknown IntentType = "unknown"
)

// Intent 意图结构
type Intent struct {
	Type        IntentType            `json:"type"`
	Confidence  float64               `json:"confidence"`  // 置信度 0-1
	Entities    map[string]string     `json:"entities"`    // 提取的实体（如专利号、关键词等）
	Metadata    map[string]interface{} `json:"metadata"`    // 额外元数据
	MatchedKeywords []string          `json:"matched_keywords"` // 匹配到的关键词
}

// IntentRouter 意图路由器
type IntentRouter struct {
	mu             sync.RWMutex
	intentPatterns map[IntentType][]*IntentPattern
	fallbackAgents map[IntentType]string // 意图到智能体的映射
	regexCache     map[string]*regexp.Regexp // 预编译正则表达式缓存
}

// IntentPattern 意图匹配模式
type IntentPattern struct {
	Keywords       []string // 关键词列表
	Regex          string   // 正则表达式（可选）
	Weight         float64  // 权重（用于计算置信度）
	RequiredFields []string // 必需字段（如专利号）
}

// NewIntentRouter 创建意图路由器
func NewIntentRouter() *IntentRouter {
	router := &IntentRouter{
		intentPatterns: make(map[IntentType][]*IntentPattern),
		fallbackAgents: make(map[IntentType]string),
		regexCache:     make(map[string]*regexp.Regexp),
	}
	router.initializePatterns()
	return router
}

// initializePatterns 初始化意图模式
func (r *IntentRouter) initializePatterns() {
	// 专利分析意图
	r.addPattern(IntentPatentAnalysis, &IntentPattern{
		Keywords: []string{"分析", "专利", "创造", "新颖", "技术方案", "权利要求"},
		Regex:    "(分析|评估).{0,10}(专利|技术方案|创造性|新颖性)",
		Weight:   0.9,
	})

	// 案例检索意图
	r.addPattern(IntentCaseSearch, &IntentPattern{
		Keywords: []string{"案例", "判例", "先例", "类似案件", "裁判", "判决"},
		Regex:    "检索.{0,5}(案例|判例|类似案件)",
		Weight:   0.85,
	})

	// 法律咨询意图
	r.addPattern(IntentLegalConsult, &IntentPattern{
		Keywords: []string{"法律", "法规", "法条", "咨询", "如何", "怎样"},
		Regex:    "(法律|法规).{0,10}(咨询|问题|解释)",
		Weight:   0.8,
	})

	// 专利检索意图
	r.addPattern(IntentPatentSearch, &IntentPattern{
		Keywords: []string{"检索", "搜索", "查询", "找", "现有技术"},
		Regex:    "(检索|搜索|查询).{0,5}(专利|文献|技术)",
		Weight:   0.85,
	})

	// 创造性分析意图
	r.addPattern(IntentCreativityAnalysis, &IntentPattern{
		Keywords: []string{"创造性", "非显而易见", "突出实质性特点", "显著进步"},
		Regex:    "(分析|评估).{0,5}创造性",
		Weight:   0.95,
	})

	// 新颖性分析意图
	r.addPattern(IntentNoveltyAnalysis, &IntentPattern{
		Keywords: []string{"新颖性", "相同", "等同", "现有技术", "抵触申请"},
		Regex:    "(分析|评估).{0,5}新颖性",
		Weight:   0.95,
	})

	// 侵权分析意图
	r.addPattern(IntentInfringementAnalysis, &IntentPattern{
		Keywords: []string{"侵权", "落入", "保护范围", "等同特征", "字面侵权"},
		Regex:    "(是否|分析).{0,5}侵权",
		Weight:   0.9,
	})

	// 无效宣告意图
	r.addPattern(IntentInvalidationAnalysis, &IntentPattern{
		Keywords: []string{"无效", "宣告无效", "无效请求", "权利要求无效"},
		Regex:    "(请求|申请|发起).{0,5}无效",
		Weight:   0.9,
	})

	// 设置默认智能体映射
	r.fallbackAgents[IntentPatentAnalysis] = "xiaona"
	r.fallbackAgents[IntentCaseSearch] = "xiaona"
	r.fallbackAgents[IntentLegalConsult] = "xiaona"
	r.fallbackAgents[IntentPatentSearch] = "xiaonuo"
	r.fallbackAgents[IntentCreativityAnalysis] = "xiaona"
	r.fallbackAgents[IntentNoveltyAnalysis] = "xiaona"
	r.fallbackAgents[IntentInfringementAnalysis] = "xiaona"
	r.fallbackAgents[IntentInvalidationAnalysis] = "xiaona"
	r.fallbackAgents[IntentGeneralQuery] = "xiaonuo"
}

// addPattern 添加意图模式
func (r *IntentRouter) addPattern(intentType IntentType, pattern *IntentPattern) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.intentPatterns[intentType] = append(r.intentPatterns[intentType], pattern)
}

// Route 路由：分析用户输入并返回意图
func (r *IntentRouter) Route(input string) *Intent {
	if input == "" {
		return &Intent{
			Type:       IntentUnknown,
			Confidence: 0.0,
		}
	}

	// 标准化输入
	input = strings.TrimSpace(input)
	input = strings.ToLower(input)

	// 尝试匹配所有意图
	bestIntent := &Intent{
		Type:       IntentUnknown,
		Confidence: 0.0,
		Entities:   make(map[string]string),
		Metadata:   make(map[string]interface{}),
		MatchedKeywords: []string{},
	}

	r.mu.RLock()
	defer r.mu.RUnlock()

	for intentType, patterns := range r.intentPatterns {
		intent := r.matchIntent(input, intentType, patterns)
		if intent.Confidence > bestIntent.Confidence {
			bestIntent = intent
		}
	}

	// 如果置信度太低，归类为一般查询
	if bestIntent.Confidence < 0.3 {
		bestIntent.Type = IntentGeneralQuery
		bestIntent.Confidence = 0.5
	}

	return bestIntent
}

// matchIntent 匹配特定意图
func (r *IntentRouter) matchIntent(input string, intentType IntentType, patterns []*IntentPattern) *Intent {
	intent := &Intent{
		Type:       intentType,
		Confidence: 0.0,
		Entities:   make(map[string]string),
		Metadata:   make(map[string]interface{}),
		MatchedKeywords: []string{},
	}

	totalWeight := 0.0
	matchedCount := 0

	for _, pattern := range patterns {
		// 关键词匹配
		for _, keyword := range pattern.Keywords {
			if strings.Contains(input, strings.ToLower(keyword)) {
				intent.MatchedKeywords = append(intent.MatchedKeywords, keyword)
				totalWeight += pattern.Weight
				matchedCount++
			}
		}

		// 正则表达式匹配
		if pattern.Regex != "" {
			// 使用预编译的正则表达式
			regex, err := r.getOrCreateRegex(pattern.Regex)
			if err == nil && regex.MatchString(input) {
				totalWeight += pattern.Weight * 1.2 // 正则匹配权重更高
				if !contains(intent.MatchedKeywords, "regex") {
					intent.MatchedKeywords = append(intent.MatchedKeywords, "regex:"+pattern.Regex)
				}
			}
		}
	}

	// 计算置信度
	if matchedCount > 0 {
		// 基于匹配数量和权重计算置信度
		intent.Confidence = min(totalWeight/float64(len(patterns)), 1.0)
	}

	// 提取实体
	intent.Entities = r.extractEntities(input, intentType)

	return intent
}

// extractEntities 从输入中提取实体
func (r *IntentRouter) extractEntities(input string, intentType IntentType) map[string]string {
	entities := make(map[string]string)

	// 提取专利号（CN开头，数字和字母）
	patentRegex := regexp.MustCompile(`(?i)(CN|CZ|US|EP|JP|WO)\s*\d{6,}[A-Z]?`)
	if matches := patentRegex.FindStringSubmatch(input); len(matches) > 0 {
		entities["patent_number"] = matches[0]
	}

	// 提取数字（可能是年份、金额等）
	numberRegex := regexp.MustCompile(`\d+`)
	if numbers := numberRegex.FindAllString(input, -1); len(numbers) > 0 {
		entities["numbers"] = strings.Join(numbers, ",")
	}

	// 根据意图类型提取特定实体
	switch intentType {
	case IntentPatentSearch:
		// 提取检索关键词（去除停用词）
		keywords := r.extractKeywords(input)
		if len(keywords) > 0 {
			entities["search_keywords"] = strings.Join(keywords, ",")
		}
	case IntentLegalConsult:
		// 提取法律条文引用
		articleRegex := regexp.MustCompile(`第.{1,5}条`)
		if articles := articleRegex.FindAllString(input, -1); len(articles) > 0 {
			entities["articles"] = strings.Join(articles, ",")
		}
	}

	return entities
}

// extractKeywords 提取关键词
func (r *IntentRouter) extractKeywords(input string) []string {
	// 停用词列表
	stopWords := map[string]bool{
		"的": true, "了": true, "是": true, "在": true, "有": true,
		"和": true, "与": true, "或": true, "及": true, "等": true,
		"检索": true, "搜索": true, "查询": true, "找": true,
	}

	words := strings.Fields(input)
	keywords := make([]string, 0)

	for _, word := range words {
		word = strings.TrimSpace(word)
		if len(word) > 1 && !stopWords[word] {
			keywords = append(keywords, word)
		}
	}

	return keywords
}

// GetAgentForIntent 根据意图获取推荐的智能体
func (r *IntentRouter) GetAgentForIntent(intent *Intent) string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if agent, exists := r.fallbackAgents[intent.Type]; exists {
		return agent
	}

	return "xiaonuo" // 默认返回小诺
}

// AddCustomPattern 添加自定义模式
func (r *IntentRouter) AddCustomPattern(intentType IntentType, pattern *IntentPattern) {
	r.addPattern(intentType, pattern)
}

// SetAgentMapping 设置意图到智能体的映射
func (r *IntentRouter) SetAgentMapping(intentType IntentType, agentName string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.fallbackAgents[intentType] = agentName
}

// contains 检查字符串切片是否包含某元素
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// getOrCreateRegex 获取或创建预编译的正则表达式
func (r *IntentRouter) getOrCreateRegex(pattern string) (*regexp.Regexp, error) {
	r.mu.RLock()
	regex, exists := r.regexCache[pattern]
	r.mu.RUnlock()

	if exists {
		return regex, nil
	}

	// 编译并缓存正则表达式
	regex, err := regexp.Compile(pattern)
	if err != nil {
		return nil, err
	}

	r.mu.Lock()
	r.regexCache[pattern] = regex
	r.mu.Unlock()

	return regex, nil
}

// min 返回两个float64中的较小值
func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
