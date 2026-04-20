// Package llm - LLM智能路由系统
// 根据任务复杂度自动选择最优模型
package llm

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"sync"
	"unicode/utf8"

	"log"
)

// ModelTier 模型层级
type ModelTier string

const (
	// TierEconomy 经济型模型（快速、低成本）
	TierEconomy ModelTier = "economy"
	// TierBalanced 平衡型模型（性能与成本平衡）
	TierBalanced ModelTier = "balanced"
	// TierPremium 高级模型（最佳质量）
	TierPremium ModelTier = "premium"
)

// ModelConfig 模型配置
type ModelConfig struct {
	Tier        ModelTier `json:"tier"`
	ModelName   string    `json:"model_name"`
	MaxTokens   int       `json:"max_tokens"`
	Temperature float64   `json:"temperature"`
	CostPer1K   float64   `json:"cost_per_1k"` // 每1K tokens成本（美元）
	Speed       int       `json:"speed"`       // 相对速度（1-10）
	Quality     int       `json:"quality"`     // 相对质量（1-10）
}

// SmartRouter 智能路由器
type SmartRouter struct {
	models      map[ModelTier]*ModelConfig
	rules       []*RoutingRule
	mu          sync.RWMutex
	stats       *RoutingStats
	defaultTier ModelTier
}

// RoutingRule 路由规则
type RoutingRule struct {
	Name          string    `json:"name"`
	Pattern       string    `json:"pattern"`  // 正则表达式模式
	Keywords      []string  `json:"keywords"` // 关键词列表
	TargetTier    ModelTier `json:"target_tier"`
	Priority      int       `json:"priority"`       // 优先级（数值越大优先级越高）
	MinComplexity float64   `json:"min_complexity"` // 最低复杂度要求
}

// RoutingStats 路由统计
type RoutingStats struct {
	mu               sync.RWMutex
	TotalRequests    uint64
	EconomyCount     uint64
	BalancedCount    uint64
	PremiumCount     uint64
	ManualOverride   uint64
	CostSaved        float64 // 节省的成本（美元）
	AvgComplexity    float64
	ComplexityScores []float64 // 保留最近100个复杂度分数
}

// NewSmartRouter 创建智能路由器
func NewSmartRouter() *SmartRouter {
	router := &SmartRouter{
		models:      make(map[ModelTier]*ModelConfig),
		rules:       make([]*RoutingRule, 0),
		stats:       &RoutingStats{ComplexityScores: make([]float64, 0, 100)},
		defaultTier: TierBalanced,
	}

	// 初始化默认模型配置
	router.initDefaultModels()

	// 初始化默认路由规则
	router.initDefaultRules()

	log.Printf("LLM智能路由器初始化成功 models=%d rules=%d", len(router.models), len(router.rules))

	return router
}

// initDefaultModels 初始化默认模型配置
func (r *SmartRouter) initDefaultModels() {
	// 经济型模型：DeepSeek-V3（高性能、低成本）
	r.models[TierEconomy] = &ModelConfig{
		Tier:        TierEconomy,
		ModelName:   "deepseek-chat",
		MaxTokens:   128000,
		Temperature: 0.7,
		CostPer1K:   0.00014, // ¥1/1M tokens ≈ $0.14/1M
		Speed:       10,
		Quality:     8,
	}

	// 平衡型模型：DeepSeek-V3（统一使用V3版本）
	r.models[TierBalanced] = &ModelConfig{
		Tier:        TierBalanced,
		ModelName:   "deepseek-chat",
		MaxTokens:   128000,
		Temperature: 0.7,
		CostPer1K:   0.00014,
		Speed:       8,
		Quality:     9,
	}

	// 高级模型：DeepSeek-V3（最高质量）
	r.models[TierPremium] = &ModelConfig{
		Tier:        TierPremium,
		ModelName:   "deepseek-reasoner",
		MaxTokens:   128000,
		Temperature: 0.7,
		CostPer1K:   0.00014, // Reasoner版本定价相同
		Speed:       6,
		Quality:     10,
	}
}

// initDefaultRules 初始化默认路由规则
func (r *SmartRouter) initDefaultRules() {
	// 规则1：简单问答 → 经济型
	r.rules = append(r.rules, &RoutingRule{
		Name:          "simple_qa",
		Keywords:      []string{"什么是", "如何", "怎么", "定义", "解释"},
		TargetTier:    TierEconomy,
		Priority:      10,
		MinComplexity: 0.0,
	})

	// 规则2：代码生成 → 平衡型
	r.rules = append(r.rules, &RoutingRule{
		Name:          "code_generation",
		Pattern:       `(代码|编程|写函数|实现|function|class)`,
		TargetTier:    TierBalanced,
		Priority:      20,
		MinComplexity: 0.3,
	})

	// 规则3：专利分析 → 高级
	r.rules = append(r.rules, &RoutingRule{
		Name:          "patent_analysis",
		Keywords:      []string{"专利", "创造性", "新颖性", "侵权", "权利要求", "审查意见"},
		TargetTier:    TierPremium,
		Priority:      100,
		MinComplexity: 0.7,
	})

	// 规则4：法律分析 → 高级
	r.rules = append(r.rules, &RoutingRule{
		Name:          "legal_analysis",
		Pattern:       `(法律|法条|案例|判决|合同|协议)`,
		TargetTier:    TierPremium,
		Priority:      90,
		MinComplexity: 0.7,
	})

	// 规则5：数据转换 → 经济型
	r.rules = append(r.rules, &RoutingRule{
		Name:          "data_transformation",
		Keywords:      []string{"转换", "格式", "解析", "提取"},
		TargetTier:    TierEconomy,
		Priority:      15,
		MinComplexity: 0.2,
	})
}

// CalculateComplexity 计算任务复杂度（0.0-1.0）
func (r *SmartRouter) CalculateComplexity(ctx context.Context, prompt string) float64 {
	complexity := 0.0

	// 1. 文本长度因子（0-0.2）
	length := utf8.RuneCountInString(prompt)
	if length > 5000 {
		complexity += 0.2
	} else if length > 2000 {
		complexity += 0.1
	}

	// 2. 关键词复杂度（0-0.3）
	complexKeywords := map[string]float64{
		"分析":   0.1,
		"评估":   0.1,
		"推理":   0.15,
		"综合":   0.15,
		"判断":   0.1,
		"策略":   0.15,
		"优化":   0.1,
		"设计":   0.15,
		"专利":   0.2,
		"法律":   0.2,
		"侵权":   0.2,
		"创造性":  0.2,
		"权利要求": 0.15,
		"审查意见": 0.2,
	}

	for keyword, score := range complexKeywords {
		if strings.Contains(prompt, keyword) {
			complexity += score
		}
	}

	// 限制最大值
	if complexity > 0.3 {
		complexity = 0.3
	}

	// 3. 任务类型因子（0-0.3）
	if r.containsAny(prompt, []string{"比较", "对比", "差异", "优缺点"}) {
		complexity += 0.1
	}
	if r.containsAny(prompt, []string{"生成", "编写", "创建", "设计"}) {
		complexity += 0.15
	}
	if r.containsAny(prompt, []string{"多步骤", "流程", "工作流", "管道"}) {
		complexity += 0.2
	}

	// 4. 专业领域因子（0-0.2）
	if r.containsAny(prompt, []string{"专利", "法律", "医学", "金融", "工程"}) {
		complexity += 0.2
	}

	// 限制在0-1范围内
	if complexity > 1.0 {
		complexity = 1.0
	}
	if complexity < 0.0 {
		complexity = 0.0
	}

	// 更新统计
	r.stats.mu.Lock()
	r.stats.ComplexityScores = append(r.stats.ComplexityScores, complexity)
	if len(r.stats.ComplexityScores) > 100 {
		r.stats.ComplexityScores = r.stats.ComplexityScores[1:]
	}
	r.stats.AvgComplexity = r.calculateAvgComplexity()
	r.stats.mu.Unlock()

	return complexity
}

// SelectModel 选择模型
func (r *SmartRouter) SelectModel(ctx context.Context, prompt string, requestedTier ModelTier) (*ModelConfig, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// 1. 用户指定了模型层级
	if requestedTier != "" {
		if config, ok := r.models[requestedTier]; ok {
			r.stats.ManualOverride++
			return config, nil
		}
		return nil, fmt.Errorf("未知的模型层级: %s", requestedTier)
	}

	// 2. 计算复杂度
	complexity := r.CalculateComplexity(ctx, prompt)

	// 3. 匹配路由规则
	matchedTier := r.matchRules(ctx, prompt, complexity)
	if matchedTier == "" {
		matchedTier = r.defaultTier
	}

	// 4. 获取模型配置
	config, ok := r.models[matchedTier]
	if !ok {
		return nil, fmt.Errorf("模型配置不存在: %s", matchedTier)
	}

	// 5. 更新统计
	r.stats.mu.Lock()
	r.stats.TotalRequests++
	switch matchedTier {
	case TierEconomy:
		r.stats.EconomyCount++
	case TierBalanced:
		r.stats.BalancedCount++
	case TierPremium:
		r.stats.PremiumCount++
	}
	r.stats.mu.Unlock()

	log.Printf("模型路由选择 tier=%s model=%s complexity=%.2f", string(matchedTier), config.ModelName, complexity)

	return config, nil
}

// matchRules 匹配路由规则
func (r *SmartRouter) matchRules(ctx context.Context, prompt string, complexity float64) ModelTier {
	// 按优先级排序
	sortedRules := make([]*RoutingRule, len(r.rules))
	copy(sortedRules, r.rules)

	// 简单冒泡排序（按优先级降序）
	for i := 0; i < len(sortedRules)-1; i++ {
		for j := 0; j < len(sortedRules)-i-1; j++ {
			if sortedRules[j].Priority < sortedRules[j+1].Priority {
				sortedRules[j], sortedRules[j+1] = sortedRules[j+1], sortedRules[j]
			}
		}
	}

	// 匹配规则
	for _, rule := range sortedRules {
		// 检查复杂度要求
		if complexity < rule.MinComplexity {
			continue
		}

		// 检查关键词匹配
		if len(rule.Keywords) > 0 {
			if r.containsAny(prompt, rule.Keywords) {
				return rule.TargetTier
			}
		}

		// 检查正则表达式匹配
		if rule.Pattern != "" {
			matched, err := regexp.MatchString(rule.Pattern, prompt)
			if err == nil && matched {
				return rule.TargetTier
			}
		}
	}

	return r.defaultTier
}

// containsAny 检查字符串是否包含任一关键词
func (r *SmartRouter) containsAny(text string, keywords []string) bool {
	for _, keyword := range keywords {
		if strings.Contains(text, keyword) {
			return true
		}
	}
	return false
}

// calculateAvgComplexity 计算平均复杂度
func (r *SmartRouter) calculateAvgComplexity() float64 {
	if len(r.stats.ComplexityScores) == 0 {
		return 0.0
	}

	sum := 0.0
	for _, score := range r.stats.ComplexityScores {
		sum += score
	}
	return sum / float64(len(r.stats.ComplexityScores))
}

// AddRule 添加路由规则
func (r *SmartRouter) AddRule(rule *RoutingRule) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if rule.Name == "" {
		return fmt.Errorf("规则名称不能为空")
	}

	if rule.TargetTier == "" {
		return fmt.Errorf("目标层级不能为空")
	}

	if _, ok := r.models[rule.TargetTier]; !ok {
		return fmt.Errorf("未知的模型层级: %s", rule.TargetTier)
	}

	r.rules = append(r.rules, rule)

	log.Printf("添加路由规则 name=%s target_tier=%s priority=%d", rule.Name, string(rule.TargetTier), rule.Priority)

	return nil
}

// UpdateModelConfig 更新模型配置
func (r *SmartRouter) UpdateModelConfig(tier ModelTier, config *ModelConfig) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if tier == "" {
		return fmt.Errorf("模型层级不能为空")
	}

	if config == nil {
		return fmt.Errorf("配置不能为空")
	}

	r.models[tier] = config

	log.Printf("更新模型配置 tier=%s model=%s", string(tier), config.ModelName)

	return nil
}

// GetStats 获取路由统计
func (r *SmartRouter) GetStats() *RoutingStats {
	r.stats.mu.RLock()
	defer r.stats.mu.RUnlock()

	return &RoutingStats{
		TotalRequests:  r.stats.TotalRequests,
		EconomyCount:   r.stats.EconomyCount,
		BalancedCount:  r.stats.BalancedCount,
		PremiumCount:   r.stats.PremiumCount,
		ManualOverride: r.stats.ManualOverride,
		CostSaved:      r.stats.CostSaved,
		AvgComplexity:  r.stats.AvgComplexity,
	}
}

// GetModelConfig 获取模型配置
func (r *SmartRouter) GetModelConfig(tier ModelTier) (*ModelConfig, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	config, ok := r.models[tier]
	if !ok {
		return nil, fmt.Errorf("未知的模型层级: %s", tier)
	}

	return config, nil
}

// ListModels 列出所有模型
func (r *SmartRouter) ListModels() []*ModelConfig {
	r.mu.RLock()
	defer r.mu.RUnlock()

	models := make([]*ModelConfig, 0, len(r.models))
	for _, config := range r.models {
		models = append(models, config)
	}

	return models
}

// CalculateCostSavings 计算成本节省
func (r *SmartRouter) CalculateCostSavings() float64 {
	stats := r.GetStats()
	if stats.TotalRequests == 0 {
		return 0.0
	}

	// 假设不使用智能路由，全部使用平衡型模型
	balancedConfig, _ := r.GetModelConfig(TierBalanced)
	economyConfig, _ := r.GetModelConfig(TierEconomy)

	// 计算节省：经济型比平衡型节省多少
	economyRequests := float64(stats.EconomyCount)
	costPerRequestEconomy := economyConfig.CostPer1K / 1000.0 * 1000 // 假设平均1000 tokens
	costPerRequestBalanced := balancedConfig.CostPer1K / 1000.0 * 1000

	saved := economyRequests * (costPerRequestBalanced - costPerRequestEconomy)
	return saved
}

// ResetStats 重置统计
func (r *SmartRouter) ResetStats() {
	r.stats.mu.Lock()
	defer r.stats.mu.Unlock()

	r.stats = &RoutingStats{
		ComplexityScores: make([]float64, 0, 100),
	}
}
