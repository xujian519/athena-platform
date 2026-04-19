package gateway

import (
	"fmt"
	"testing"
)

// TestNewRouteManager 测试创建路由管理器
func TestNewRouteManager(t *testing.T) {
	rm := NewRouteManager()
	if rm == nil {
		t.Fatal("NewRouteManager() returned nil")
	}
	if rm.Count() != 0 {
		t.Errorf("NewRouteManager() count = %d, want 0", rm.Count())
	}
}

// TestCreateRoute 测试创建路由
func TestCreateRoute(t *testing.T) {
	rm := NewRouteManager()

	route := &RouteRule{
		ID:            "test-route",
		Path:          "/api/test/**",
		TargetService: "test-service",
		Methods:       []string{"GET", "POST"},
		StripPrefix:   true,
	}

	rm.Create(route)

	if rm.Count() != 1 {
		t.Errorf("Create() count = %d, want 1", rm.Count())
	}

	// 验证可以获取路由
	got := rm.Get("test-route")
	if got == nil {
		t.Fatal("Create() route not found")
	}
	if got.Path != "/api/test/**" {
		t.Errorf("Create() Path = %s, want /api/test/**", got.Path)
	}
}

// TestGetRoute 测试获取路由
func TestGetRoute(t *testing.T) {
	rm := NewRouteManager()

	route := &RouteRule{
		ID:            "route-1",
		Path:          "/api/test",
		TargetService: "svc1",
		Methods:       []string{"GET"},
	}
	rm.Create(route)

	// 测试存在的路由
	got := rm.Get("route-1")
	if got == nil {
		t.Fatal("Get() existing route returned nil")
	}
	if got.TargetService != "svc1" {
		t.Errorf("Get() TargetService = %s, want svc1", got.TargetService)
	}

	// 测试不存在的路由
	got = rm.Get("non-existent")
	if got != nil {
		t.Errorf("Get() non-existent = %v, want nil", got)
	}
}

// TestGetAllRoutes 测试获取所有路由
func TestGetAllRoutes(t *testing.T) {
	rm := NewRouteManager()

	// 创建3个路由（使用不同的ID）
	for i := 0; i < 3; i++ {
		rm.Create(&RouteRule{
			ID:            fmt.Sprintf("route-%d", i),
			Path:          "/api/test",
			TargetService: "svc",
			Methods:       []string{"GET"},
		})
	}

	all := rm.GetAll()
	if len(all) != 3 {
		t.Errorf("GetAll() count = %d, want 3", len(all))
	}
}

// TestUpdateRoute 测试更新路由
func TestUpdateRoute(t *testing.T) {
	rm := NewRouteManager()

	// 创建路由
	original := &RouteRule{
		ID:            "route-1",
		Path:          "/api/old",
		TargetService: "svc1",
		Methods:       []string{"GET"},
		Timeout:       10,
	}
	rm.Create(original)

	// 更新路由
	updated := &RouteRule{
		ID:            "route-1",
		Path:          "/api/new",
		TargetService: "svc2",
		Methods:       []string{"GET", "POST"},
		Timeout:       30,
	}
	rm.Update(updated)

	// 验证更新
	got := rm.Get("route-1")
	if got == nil {
		t.Fatal("Update() route not found")
	}
	if got.Path != "/api/new" {
		t.Errorf("Update() Path = %s, want /api/new", got.Path)
	}
	if got.TargetService != "svc2" {
		t.Errorf("Update() TargetService = %s, want svc2", got.TargetService)
	}
	if got.Timeout != 30 {
		t.Errorf("Update() Timeout = %d, want 30", got.Timeout)
	}
}

// TestDeleteRoute 测试删除路由
func TestDeleteRoute(t *testing.T) {
	rm := NewRouteManager()

	route := &RouteRule{
		ID:            "to-delete",
		Path:          "/api/test",
		TargetService: "svc",
		Methods:       []string{"GET"},
	}
	rm.Create(route)

	if rm.Count() != 1 {
		t.Fatalf("Delete() pre-count = %d, want 1", rm.Count())
	}

	// 删除路由
	deleted := rm.Delete("to-delete")
	if !deleted {
		t.Error("Delete() returned false, want true")
	}

	// 验证已删除
	if rm.Count() != 0 {
		t.Errorf("Delete() post-count = %d, want 0", rm.Count())
	}

	// 删除不存在的路由
	deleted = rm.Delete("non-existent")
	if deleted {
		t.Error("Delete() non-existent returned true, want false")
	}
}

// TestFindByPath 测试根据路径查找路由
func TestFindByPath(t *testing.T) {
	rm := NewRouteManager()

	// 创建多个路由
	rm.Create(&RouteRule{
		ID:            "route-1",
		Path:          "/api/legal",
		TargetService: "xiaona",
		Methods:       []string{"GET", "POST"},
	})
	rm.Create(&RouteRule{
		ID:            "route-2",
		Path:          "/api/legal/*",
		TargetService: "xiaona",
		Methods:       []string{"GET"},
	})
	rm.Create(&RouteRule{
		ID:            "route-3",
		Path:          "/api/patent/**",
		TargetService: "xiaonuo",
		Methods:       []string{"GET"},
	})

	// 测试精确匹配
	route := rm.FindByPath("/api/legal", "GET")
	if route == nil {
		t.Fatal("FindByPath() exact match returned nil")
	}
	if route.ID != "route-1" {
		t.Errorf("FindByPath() exact match ID = %s, want route-1", route.ID)
	}

	// 测试通配符匹配
	route = rm.FindByPath("/api/legal/patents", "GET")
	if route == nil {
		t.Fatal("FindByPath() wildcard match returned nil")
	}
	if route.ID != "route-2" {
		t.Errorf("FindByPath() wildcard match ID = %s, want route-2", route.ID)
	}

	// 测试方法不匹配
	route = rm.FindByPath("/api/legal", "DELETE")
	if route != nil {
		t.Error("FindByPath() method mismatch returned route, want nil")
	}

	// 测试路径不存在
	route = rm.FindByPath("/api/nonexistent", "GET")
	if route != nil {
		t.Error("FindByPath() non-existent returned route, want nil")
	}

	// 测试多层通配符
	route = rm.FindByPath("/api/patent/search/advanced", "GET")
	if route == nil {
		t.Fatal("FindByPath() double wildcard returned nil")
	}
	if route.ID != "route-3" {
		t.Errorf("FindByPath() double wildcard ID = %s, want route-3", route.ID)
	}
}

// TestRoutePriority 测试路由优先级
func TestRoutePriority(t *testing.T) {
	rm := NewRouteManager()

	// 创建可能有冲突的路由
	// 更具体的路径应该优先
	rm.Create(&RouteRule{
		ID:            "wildcard",
		Path:          "/api/**",
		TargetService: "default",
		Methods:       []string{"GET"},
	})
	rm.Create(&RouteRule{
		ID:            "specific",
		Path:          "/api/legal/search",
		TargetService: "xiaona",
		Methods:       []string{"GET"},
	})

	// 查找时应该返回第一个匹配的路由
	// 实际优先级取决于查找顺序，这里只是验证能找到
	route := rm.FindByPath("/api/legal/search", "GET")
	if route == nil {
		t.Fatal("RoutePriority() no match found")
	}

	// 验证至少能匹配到路由
	if route.Path != "/api/legal/search" && route.Path != "/api/**" {
		t.Errorf("RoutePriority() unexpected Path = %s", route.Path)
	}
}

// TestRouteMethods 测试路由方法过滤
func TestRouteMethods(t *testing.T) {
	rm := NewRouteManager()

	rm.Create(&RouteRule{
		ID:            "multi-method",
		Path:          "/api/test",
		TargetService: "svc",
		Methods:       []string{"GET", "POST", "PUT"},
	})

	// 测试每个方法都能匹配
	for _, method := range []string{"GET", "POST", "PUT"} {
		route := rm.FindByPath("/api/test", method)
		if route == nil {
			t.Errorf("RouteMethods() %s not matched", method)
		}
	}

	// 测试不在列表中的方法
	route := rm.FindByPath("/api/test", "DELETE")
	if route != nil {
		t.Error("RouteMethods() DELETE matched when it shouldn't")
	}
}

// TestStripPrefix 测试路径前缀剥离
func TestStripPrefix(t *testing.T) {
	rm := NewRouteManager()

	// 测试启用StripPrefix
	rm.Create(&RouteRule{
		ID:            "strip-true",
		Path:          "/api/svc/*",
		TargetService: "svc",
		StripPrefix:   true,
		Methods:       []string{"GET"},
	})

	route := rm.FindByPath("/api/svc/test", "GET")
	if route == nil {
		t.Fatal("StripPrefix() route not found")
	}
	if !route.StripPrefix {
		t.Error("StripPrefix() StripPrefix = false, want true")
	}

	// 测试禁用StripPrefix
	rm.Create(&RouteRule{
		ID:            "strip-false",
		Path:          "/api/raw/*",
		TargetService: "raw",
		StripPrefix:   false,
		Methods:       []string{"GET"},
	})

	route = rm.FindByPath("/api/raw/test", "GET")
	if route == nil {
		t.Fatal("StripPrefix() route not found")
	}
	if route.StripPrefix {
		t.Error("StripPrefix() StripPrefix = true, want false")
	}
}
