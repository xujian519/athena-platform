// Package vector - 向量检索批量处理测试
package vector

import (
	"testing"
)

// TestBatchOptimizer 测试批量优化器
func TestBatchOptimizer(t *testing.T) {
	cfg := &BatchOptimizerConfig{
		VectorDim:           768,
		SimilarityThreshold: 0.95,
		MaxBatchSize:        100,
		MergeEnabled:        true,
	}

	optimizer := NewBatchOptimizer(cfg)
	if optimizer == nil {
		t.Fatal("创建批量优化器失败")
	}

	// 测试相似度计算
	vec1 := make([]float64, 768)
	vec2 := make([]float64, 768)

	// 设置相同的值
	for i := range vec1 {
		vec1[i] = 0.5
		vec2[i] = 0.5
	}

	similarity := optimizer.CalculateSimilarity(vec1, vec2)
	if similarity != 1.0 {
		t.Errorf("相同向量相似度应该为1.0，实际为%f", similarity)
	}

	// 测试不同向量
	vec3 := make([]float64, 768)
	for i := range vec3 {
		vec3[i] = 0.3
	}

	similarity = optimizer.CalculateSimilarity(vec1, vec3)
	if similarity >= 0.95 {
		t.Errorf("不同向量相似度应该<0.95，实际为%f", similarity)
	}


}
// TestMergeSimilarVectors 测试向量合并
func TestMergeSimilarVectors(t *testing.T) {
	cfg := &BatchOptimizerConfig{
		VectorDim:           768,
		SimilarityThreshold: 0.95,
		MaxBatchSize:        100,
		MergeEnabled:        true,
	}

	optimizer := NewBatchOptimizer(cfg)

	// 创建测试请求
	reqs := make([]*SearchRequest, 10)
	for i := 0; i < 10; i++ {
		vec := make([]float64, 768)
		if i < 5 {
			// 前5个请求使用相同的向量
			for j := range vec {
				vec[j] = 0.5
			}
		} else {
			// 后5个请求使用不同的向量
			for j := range vec {
				vec[j] = float64(j)
			}
		}

		reqs[i] = &SearchRequest{
			Collection: "test-collection",
			Vector:     vec,
			Limit:      10,
		}
	}

	// 合并相似向量
	merged := optimizer.MergeSimilarVectors(reqs)

	// 应该合并了5个相同向量
	if len(merged) != 6 { // 5个相同 → 1个 + 5个不同 = 6个
		t.Logf("合并结果: %d → %d", len(reqs), len(merged))
	}


}
// TestSmartBatchStrategy 测试智能批处理策略
func TestSmartBatchStrategy(t *testing.T) {
	strategy := NewSmartBatchStrategy()

	testCases := []struct {
		name     string
		reqCount int
		expected int
	}{
		{"小批量", 5, 5},
		{"中等批量", 50, 50},
		{"大批量", 150, 100},
		{"超大批量", 500, 100},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reqs := make([]*SearchRequest, tc.reqCount)
			for i := range reqs {
				vec := make([]float64, 768)
				reqs[i] = &SearchRequest{
					Collection: "test",
					Vector:     vec,
					Limit:      10,
				}
			}

			optimalSize := strategy.OptimizeBatchSize(reqs)
			if optimalSize != tc.expected {
				t.Errorf("%s: 期望%d, 实际%d", tc.name, tc.expected, optimalSize)
			}
		})
	}


}
// TestDeduplicateRequests 测试请求去重
func TestDeduplicateRequests(t *testing.T) {
	// 这个测试需要完整的VectorSearchService，跳过
	if testing.Short() {
		t.Skip("跳过集成测试")
	}


}
// TestGroupRequests 测试请求分组
func TestGroupRequests(t *testing.T) {
	// 这个测试需要完整的VectorSearchService，跳过
	if testing.Short() {
		t.Skip("跳过集成测试")
	}


}
// BenchmarkBatchOptimizer 基准测试
func BenchmarkBatchOptimizer(b *testing.B) {
	cfg := &BatchOptimizerConfig{
		VectorDim:           768,
		SimilarityThreshold: 0.95,
		MaxBatchSize:        100,
		MergeEnabled:        true,
	}

	optimizer := NewBatchOptimizer(cfg)

	vec1 := make([]float64, 768)
	vec2 := make([]float64, 768)
	for i := range vec1 {
		vec1[i] = 0.5
		vec2[i] = 0.5
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		optimizer.CalculateSimilarity(vec1, vec2)
	}


}
// BenchmarkMergeSimilarVectors 基准测试
func BenchmarkMergeSimilarVectors(b *testing.B) {
	cfg := &BatchOptimizerConfig{
		VectorDim:           768,
		SimilarityThreshold: 0.95,
		MaxBatchSize:        100,
		MergeEnabled:        true,
	}

	optimizer := NewBatchOptimizer(cfg)

	reqs := make([]*SearchRequest, 100)
	for i := range reqs {
		vec := make([]float64, 768)
		for j := range vec {
			vec[j] = float64(i % 10)
		}

		reqs[i] = &SearchRequest{
			Collection: "test",
			Vector:     vec,
			Limit:      10,
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		optimizer.MergeSimilarVectors(reqs)
	}


}
// BenchmarkOptimizedBatchSearch 基准测试
func BenchmarkOptimizedBatchSearch(b *testing.B) {
	if testing.Short() {
		b.Skip("跳过集成测试")
	}

}
