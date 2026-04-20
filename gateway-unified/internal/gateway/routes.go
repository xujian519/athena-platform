package gateway

import (
	"path/filepath"
	"strings"
	"sync"
)

// RouteRule 路由规则
type RouteRule struct {
	ID             string                 `json:"id"`
	Path           string                 `json:"path"`
	TargetService  string                 `json:"target_service"`
	Methods        []string               `json:"methods"`
	StripPrefix    bool                   `json:"strip_prefix"`
	Timeout        int                    `json:"timeout"`
	Retries        int                    `json:"retries"`
	AuthRequired   bool                   `json:"auth_required"`
	Priority       int                    `json:"priority"`
	Weight         int                    `json:"weight"`
	Enabled        bool                   `json:"enabled"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

// RouteManager 路由管理器
type RouteManager struct {
	mu     sync.RWMutex
	routes map[string]*RouteRule  // id -> route
}

// NewRouteManager 创建路由管理器
func NewRouteManager() *RouteManager {
	return &RouteManager{
		routes: make(map[string]*RouteRule),
	}
}

// Create 创建路由
func (m *RouteManager) Create(route *RouteRule) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.routes[route.ID] = route
}

// Get 根据ID获取路由
func (m *RouteManager) Get(id string) *RouteRule {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.routes[id]
}

// GetAll 获取所有路由
func (m *RouteManager) GetAll() []*RouteRule {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*RouteRule, 0, len(m.routes))
	for _, route := range m.routes {
		result = append(result, route)
	}
	return result
}

// Update 更新路由
func (m *RouteManager) Update(route *RouteRule) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.routes[route.ID]; exists {
		m.routes[route.ID] = route
	}
}

// Delete 删除路由
func (m *RouteManager) Delete(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.routes[id]; exists {
		delete(m.routes, id)
		return true
	}
	return false
}

// Count 返回路由数量
func (m *RouteManager) Count() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.routes)
}

// FindByPath 根据路径和方法查找路由
// 按优先级匹配：精确匹配 > 单层通配符 > 多层通配符
func (m *RouteManager) FindByPath(path string, method string) *RouteRule {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// 按优先级分三次查找
	// 1. 首先尝试精确匹配
	for _, route := range m.routes {
		if route.Path == path && contains(route.Methods, method) {
			return route
		}
	}

	// 2. 尝试单层通配符匹配 (/*)
	for _, route := range m.routes {
		if strings.HasSuffix(route.Path, "/*") && !strings.HasSuffix(route.Path, "/**") {
			if matchPath(route.Path, path) && contains(route.Methods, method) {
				return route
			}
		}
	}

	// 3. 尝试多层通配符匹配 (/**) 和其他模式
	for _, route := range m.routes {
		if matchPath(route.Path, path) && contains(route.Methods, method) {
			return route
		}
	}

	return nil
}

// matchPath 检查路径是否匹配（支持通配符）
// 支持的通配符模式：
//   1. 精确匹配: /api/legal 匹配 /api/legal
//   2. 后缀通配符: /api/legal/* 匹配 /api/legal/anything
//   3. 双星通配符: /api/** 匹配 /api/anything/deeply/nested
//   4. 参数匹配: /api/:id 匹配 /api/123
func matchPath(routePath, requestPath string) bool {
	// 精确匹配
	if routePath == requestPath {
		return true
	}

	// 处理双星通配符 (**) - 匹配多层路径
	if strings.HasSuffix(routePath, "/**") {
		prefix := strings.TrimSuffix(routePath, "/**")
		if requestPath == prefix {
			return true
		}
		if strings.HasPrefix(requestPath, prefix+"/") {
			return true
		}
		return false
	}

	// 处理单星通配符 (*) - 只匹配单层路径
	// /api/* 匹配 /api/foo，但不匹配 /api/foo/bar
	if strings.HasSuffix(routePath, "/*") {
		prefix := strings.TrimSuffix(routePath, "/*")
		if requestPath == prefix {
			return true
		}
		// 检查是否只有一层子路径
		if strings.HasPrefix(requestPath, prefix+"/") {
			suffix := strings.TrimPrefix(requestPath, prefix+"/")
			// 确保没有额外的斜杠（即只有一层）
			if !strings.Contains(suffix, "/") {
				return true
			}
		}
		return false
	}

	// 使用 filepath.Match 进行通用的通配符匹配
	// 将路径转换为文件系统路径格式进行匹配
	matched, err := filepath.Match(routePath, requestPath)
	if err == nil && matched {
		return true
	}

	return false
}

// contains 检查字符串是否在数组中
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
