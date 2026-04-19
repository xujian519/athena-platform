package gateway

import (
	"testing"
)

// TestMatchPath 精确匹配
func TestMatchPath_ExactMatch(t *testing.T) {
	tests := []struct {
		name      string
		routePath string
		reqPath   string
		want      bool
	}{
		{
			name:      "完全相同路径",
			routePath: "/api/legal",
			reqPath:   "/api/legal",
			want:      true,
		},
		{
			name:      "根路径",
			routePath: "/",
			reqPath:   "/",
			want:      true,
		},
		{
			name:      "不同路径",
			routePath: "/api/legal",
			reqPath:   "/api/patent",
			want:      false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := matchPath(tt.routePath, tt.reqPath); got != tt.want {
				t.Errorf("matchPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestMatchPath_SingleWildcard 单层通配符 (*)
func TestMatchPath_SingleWildcard(t *testing.T) {
	tests := []struct {
		name      string
		routePath string
		reqPath   string
		want      bool
	}{
		{
			name:      "单层匹配",
			routePath: "/api/*",
			reqPath:   "/api/legal",
			want:      true,
		},
		{
			name:      "单层匹配-嵌套",
			routePath: "/api/legal/*",
			reqPath:   "/api/legal/patents",
			want:      true,
		},
		{
			name:      "单层不匹配-多层",
			routePath: "/api/*",
			reqPath:   "/api/legal/patents",
			want:      false, // * 只匹配单层
		},
		{
			name:      "前缀相同但无子路径",
			routePath: "/api/*",
			reqPath:   "/api",
			want:      true, // /api 等价于 /api/
		},
		{
			name:      "尾随斜杠",
			routePath: "/api/*",
			reqPath:   "/api/",
			want:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := matchPath(tt.routePath, tt.reqPath); got != tt.want {
				t.Errorf("matchPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestMatchPath_DoubleWildcard 多层通配符 (**)
func TestMatchPath_DoubleWildcard(t *testing.T) {
	tests := []struct {
		name      string
		routePath string
		reqPath   string
		want      bool
	}{
		{
			name:      "多层匹配-两层",
			routePath: "/api/**",
			reqPath:   "/api/legal/patents",
			want:      true,
		},
		{
			name:      "多层匹配-三层",
			routePath: "/api/**",
			reqPath:   "/api/legal/patents/search",
			want:      true,
		},
		{
			name:      "多层匹配-根",
			routePath: "/api/**",
			reqPath:   "/api",
			want:      true,
		},
		{
			name:      "多层匹配-直接子路径",
			routePath: "/api/**",
			reqPath:   "/api/legal",
			want:      true,
		},
		{
			name:      "多层不匹配-不同前缀",
			routePath: "/api/**",
			reqPath:   "/legal/patents",
			want:      false,
		},
		{
			name:      "嵌套路径多层匹配",
			routePath: "/api/svc/**",
			reqPath:   "/api/svc/a/b/c/d",
			want:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := matchPath(tt.routePath, tt.reqPath); got != tt.want {
				t.Errorf("matchPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestMatchPath_FilePathPattern 文件路径风格通配符
func TestMatchPath_FilePathPattern(t *testing.T) {
	tests := []struct {
		name      string
		routePath string
		reqPath   string
		want      bool
	}{
		{
			name:      "JSON扩展名",
			routePath: "/api/*.json",
			reqPath:   "/api/test.json",
			want:      true,
		},
		{
			name:      "JSON扩展名不匹配",
			routePath: "/api/*.json",
			reqPath:   "/api/test.xml",
			want:      false,
		},
		{
			name:      "复杂通配符",
			routePath: "/api/patents/*.json",
			reqPath:   "/api/patents/CN123456.json",
			want:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := matchPath(tt.routePath, tt.reqPath); got != tt.want {
				t.Errorf("matchPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestMatchPath_RealWorld 真实场景测试
func TestMatchPath_RealWorld(t *testing.T) {
	tests := []struct {
		name      string
		routePath string
		reqPath   string
		want      bool
	}{
		// Athena平台真实场景
		{
			name:      "小娜法律服务-精确",
			routePath: "/api/legal/search",
			reqPath:   "/api/legal/search",
			want:      true,
		},
		{
			name:      "小娜法律服务-单层通配",
			routePath: "/api/legal/*",
			reqPath:   "/api/legal/patents",
			want:      true,
		},
		{
			name:      "小娜法律服务-多层通配",
			routePath: "/api/legal/**",
			reqPath:   "/api/legal/patents/cn/123456",
			want:      true,
		},
		{
			name:      "服务级通配",
			routePath: "/api/**",
			reqPath:   "/api/svc/xiaona/patents/search",
			want:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := matchPath(tt.routePath, tt.reqPath); got != tt.want {
				t.Errorf("matchPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

// TestContains 辅助函数测试
func TestContains(t *testing.T) {
	tests := []struct {
		name   string
		slice  []string
		item   string
		want   bool
	}{
		{
			name:  "包含",
			slice: []string{"GET", "POST", "PUT"},
			item:  "GET",
			want:  true,
		},
		{
			name:  "不包含",
			slice: []string{"GET", "POST", "PUT"},
			item:  "DELETE",
			want:  false,
		},
		{
			name:  "空切片",
			slice: []string{},
			item:  "GET",
			want:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := contains(tt.slice, tt.item); got != tt.want {
				t.Errorf("contains() = %v, want %v", got, tt.want)
			}
		})
	}
}
