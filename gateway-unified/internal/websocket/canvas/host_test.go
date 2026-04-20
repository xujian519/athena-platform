package canvas

import (
	"testing"
	"time"
)

// TestNewCanvasHost 测试创建Canvas Host
func TestNewCanvasHost(t *testing.T) {
	host := NewCanvasHost()

	if host == nil {
		t.Fatal("NewCanvasHost返回nil")
	}

	if host.canvases == nil {
		t.Error("canvases映射未初始化")
	}

	if host.ctx == nil {
		t.Error("context未初始化")
	}

	if host.cancel == nil {
		t.Error("cancel函数未初始化")
	}

	// 清理
	host.Close()
}

// TestCreateCanvas 测试创建Canvas
func TestCreateCanvas(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	sessionID := "test_session_001"
	title := "测试Canvas"

	canvas := host.CreateCanvas(sessionID, title)

	if canvas == nil {
		t.Fatal("CreateCanvas返回nil")
	}

	if canvas.ID == "" {
		t.Error("Canvas ID为空")
	}

	if canvas.SessionID != sessionID {
		t.Errorf("期望SessionID %s, 得到 %s", sessionID, canvas.SessionID)
	}

	if canvas.Title != title {
		t.Errorf("期望Title %s, 得到 %s", title, canvas.Title)
	}

	if canvas.HTML == "" {
		t.Error("默认HTML为空")
	}

	if canvas.CSS == "" {
		t.Error("默认CSS为空")
	}

	if canvas.JS == "" {
		t.Error("默认JS为空")
	}

	if canvas.Data == nil {
		t.Error("Data映射未初始化")
	}

	if canvas.CreatedAt.IsZero() {
		t.Error("CreatedAt未设置")
	}

	if canvas.UpdatedAt.IsZero() {
		t.Error("UpdatedAt未设置")
	}

	// 验证Canvas已存储
	stored, exists := host.GetCanvas(canvas.ID)
	if !exists {
		t.Error("Canvas未存储在Host中")
	}

	if stored.ID != canvas.ID {
		t.Error("存储的Canvas ID不匹配")
	}
}

// TestCreateCanvasMultiple 测试创建多个Canvas
func TestCreateCanvasMultiple(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	// 创建多个Canvas
	canvas1 := host.CreateCanvas("session_1", "Canvas 1")
	time.Sleep(10 * time.Millisecond) // 确保时间戳不同
	canvas2 := host.CreateCanvas("session_2", "Canvas 2")
	time.Sleep(10 * time.Millisecond)
	canvas3 := host.CreateCanvas("session_1", "Canvas 3")

	// 验证ID唯一性
	if canvas1.ID == canvas2.ID || canvas1.ID == canvas3.ID || canvas2.ID == canvas3.ID {
		t.Error("Canvas ID不唯一")
	}

	// 验证session_1有2个Canvas
	canvases := host.GetCanvasesBySession("session_1")
	if len(canvases) != 2 {
		t.Errorf("期望session_1有2个Canvas, 得到 %d", len(canvases))
	}

	// 验证session_2有1个Canvas
	canvases = host.GetCanvasesBySession("session_2")
	if len(canvases) != 1 {
		t.Errorf("期望session_2有1个Canvas, 得到 %d", len(canvases))
	}
}

// TestGetCanvas 测试获取Canvas
func TestGetCanvas(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	// 创建Canvas
	canvas := host.CreateCanvas("session_1", "Test Canvas")

	// 测试获取存在的Canvas
	retrieved, exists := host.GetCanvas(canvas.ID)
	if !exists {
		t.Error("Canvas不存在")
	}

	if retrieved.ID != canvas.ID {
		t.Error("获取的Canvas ID不匹配")
	}

	// 测试获取不存在的Canvas
	_, exists = host.GetCanvas("non_existent_id")
	if exists {
		t.Error("不存在的Canvas应该返回false")
	}
}

// TestUpdateCanvasHTML 测试更新Canvas HTML
func TestUpdateCanvasHTML(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")
	newHTML := "<div>New HTML Content</div>"

	err := host.UpdateCanvas(canvas.ID, map[string]interface{}{
		"html": newHTML,
	})

	if err != nil {
		t.Errorf("UpdateCanvas失败: %v", err)
	}

	retrieved, _ := host.GetCanvas(canvas.ID)
	if retrieved.HTML != newHTML {
		t.Errorf("期望HTML '%s', 得到 '%s'", newHTML, retrieved.HTML)
	}
}

// TestUpdateCanvasCSS 测试更新Canvas CSS
func TestUpdateCanvasCSS(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")
	newCSS := ".test { color: red; }"

	err := host.UpdateCanvas(canvas.ID, map[string]interface{}{
		"css": newCSS,
	})

	if err != nil {
		t.Errorf("UpdateCanvas失败: %v", err)
	}

	retrieved, _ := host.GetCanvas(canvas.ID)
	if retrieved.CSS != newCSS {
		t.Errorf("期望CSS '%s', 得到 '%s'", newCSS, retrieved.CSS)
	}
}

// TestUpdateCanvasJS 测试更新Canvas JavaScript
func TestUpdateCanvasJS(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")
	newJS := "console.log('test');"

	err := host.UpdateCanvas(canvas.ID, map[string]interface{}{
		"js": newJS,
	})

	if err != nil {
		t.Errorf("UpdateCanvas失败: %v", err)
	}

	retrieved, _ := host.GetCanvas(canvas.ID)
	if retrieved.JS != newJS {
		t.Errorf("期望JS '%s', 得到 '%s'", newJS, retrieved.JS)
	}
}

// TestUpdateCanvasData 测试更新Canvas Data
func TestUpdateCanvasData(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")
	newData := map[string]interface{}{
		"key1": "value1",
		"key2": 123,
	}

	err := host.UpdateCanvas(canvas.ID, map[string]interface{}{
		"data": newData,
	})

	if err != nil {
		t.Errorf("UpdateCanvas失败: %v", err)
	}

	retrieved, _ := host.GetCanvas(canvas.ID)
	if retrieved.Data["key1"] != "value1" {
		t.Errorf("期望Data['key1'] = 'value1', 得到 %v", retrieved.Data["key1"])
	}

	if retrieved.Data["key2"] != 123 {
		t.Errorf("期望Data['key2'] = 123, 得到 %v", retrieved.Data["key2"])
	}
}

// TestUpdateCanvasMultipleFields 测试同时更新多个字段
func TestUpdateCanvasMultipleFields(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")
	newHTML := "<div>New HTML</div>"
	newCSS := ".new { color: blue; }"

	err := host.UpdateCanvas(canvas.ID, map[string]interface{}{
		"html": newHTML,
		"css":  newCSS,
	})

	if err != nil {
		t.Errorf("UpdateCanvas失败: %v", err)
	}

	retrieved, _ := host.GetCanvas(canvas.ID)
	if retrieved.HTML != newHTML {
		t.Error("HTML未更新")
	}

	if retrieved.CSS != newCSS {
		t.Error("CSS未更新")
	}
}

// TestUpdateCanvasNonExistent 测试更新不存在的Canvas
func TestUpdateCanvasNonExistent(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	err := host.UpdateCanvas("non_existent_id", map[string]interface{}{
		"html": "<div>Test</div>",
	})

	if err == nil {
		t.Error("期望更新不存在的Canvas返回错误")
	}
}

// TestDeleteCanvas 测试删除Canvas
func TestDeleteCanvas(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")

	// 删除Canvas
	host.DeleteCanvas(canvas.ID)

	// 验证Canvas已删除
	_, exists := host.GetCanvas(canvas.ID)
	if exists {
		t.Error("Canvas应该已被删除")
	}
}

// TestDeleteCanvasNonExistent 测试删除不存在的Canvas
func TestDeleteCanvasNonExistent(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	// 删除不存在的Canvas不应该panic
	host.DeleteCanvas("non_existent_id")
}

// TestRender 测试渲染Canvas
func TestRender(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test Canvas")
	canvas.Data = map[string]interface{}{
		"test_key": "test_value",
	}
	host.UpdateCanvas(canvas.ID, map[string]interface{}{"data": canvas.Data})

	html, err := host.Render(canvas.ID)
	if err != nil {
		t.Errorf("Render失败: %v", err)
	}

	if html == "" {
		t.Error("渲染的HTML为空")
	}

	// 验证HTML包含关键元素
	if len(html) < 100 {
		t.Error("渲染的HTML太短")
	}

	// 验证包含DOCTYPE
	if !contains(html, "<!DOCTYPE html>") {
		t.Error("HTML缺少DOCTYPE声明")
	}

	// 验证包含标题
	if !contains(html, canvas.Title) {
		t.Error("HTML不包含Canvas标题")
	}

	// 验证包含CSS
	if !contains(html, "</style>") {
		t.Error("HTML缺少CSS标签")
	}

	// 验证包含JS
	if !contains(html, "<script>") {
		t.Error("HTML缺少Script标签")
	}
}

// TestRenderNonExistent 测试渲染不存在的Canvas
func TestRenderNonExistent(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	_, err := host.Render("non_existent_id")
	if err == nil {
		t.Error("期望渲染不存在的Canvas返回错误")
	}
}

// TestGetCanvasesBySession 测试按Session获取Canvas列表
func TestGetCanvasesBySession(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	// 创建不同Session的Canvas
	canvas1 := host.CreateCanvas("session_a", "Canvas A1")
	_ = host.CreateCanvas("session_b", "Canvas B1")
	canvas3 := host.CreateCanvas("session_a", "Canvas A2")
	_ = host.CreateCanvas("session_b", "Canvas B2")
	_ = host.CreateCanvas("session_c", "Canvas C1")

	// 测试session_a
	canvasesA := host.GetCanvasesBySession("session_a")
	if len(canvasesA) != 2 {
		t.Errorf("期望session_a有2个Canvas, 得到 %d", len(canvasesA))
	}

	// 测试session_b
	canvasesB := host.GetCanvasesBySession("session_b")
	if len(canvasesB) != 2 {
		t.Errorf("期望session_b有2个Canvas, 得到 %d", len(canvasesB))
	}

	// 测试session_c
	canvasesC := host.GetCanvasesBySession("session_c")
	if len(canvasesC) != 1 {
		t.Errorf("期望session_c有1个Canvas, 得到 %d", len(canvasesC))
	}

	// 测试不存在的session
	canvasesD := host.GetCanvasesBySession("session_d")
	if len(canvasesD) != 0 {
		t.Errorf("期望session_d有0个Canvas, 得到 %d", len(canvasesD))
	}

	// 验证ID匹配
	aIDs := make(map[string]bool)
	for _, c := range canvasesA {
		aIDs[c.ID] = true
	}

	if !aIDs[canvas1.ID] || !aIDs[canvas3.ID] {
		t.Error("session_a的Canvas ID不匹配")
	}
}

// TestClose 测试关闭Canvas Host
func TestClose(t *testing.T) {
	host := NewCanvasHost()

	// 创建一些Canvas
	host.CreateCanvas("session_1", "Canvas 1")
	host.CreateCanvas("session_2", "Canvas 2")

	// 关闭Host
	host.Close()

	// 验证context已取消
	select {
	case <-host.ctx.Done():
		// Context已取消,正常
	default:
		t.Error("Context应该已取消")
	}

	// 验证canvases已清空
	if len(host.canvases) != 0 {
		t.Error("Canvases应该已清空")
	}
}

// TestConcurrentAccess 测试并发访问
func TestConcurrentAccess(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	// 并发创建Canvas
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(index int) {
			sessionID := "session_concurrent_" + string(rune('0'+index%10))
			title := "Canvas Concurrent"
			host.CreateCanvas(sessionID, title)
			done <- true
		}(i)
	}

	// 等待所有goroutine完成
	for i := 0; i < 10; i++ {
		<-done
	}

	// 验证创建了10个不同Session的Canvas
	totalCount := 0
	for i := 0; i < 10; i++ {
		sessionID := "session_concurrent_" + string(rune('0'+i%10))
		canvases := host.GetCanvasesBySession(sessionID)
		totalCount += len(canvases)
	}

	if totalCount != 10 {
		t.Errorf("期望10个Canvas, 得到 %d", totalCount)
	}
}

// TestDefaultHTML 测试默认HTML模板
func TestDefaultHTML(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test")

	// 验证默认HTML包含关键元素
	if !contains(canvas.HTML, "loading") {
		t.Error("默认HTML缺少loading元素")
	}

	if !contains(canvas.HTML, "container") {
		t.Error("默认HTML缺少container元素")
	}

	if !contains(canvas.HTML, "content") {
		t.Error("默认HTML缺少content元素")
	}

	if !contains(canvas.HTML, "progress") {
		t.Error("默认HTML缺少progress元素")
	}

	if !contains(canvas.HTML, "results") {
		t.Error("默认HTML缺少results元素")
	}
}

// TestDefaultCSS 测试默认CSS样式
func TestDefaultCSS(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test")

	// 验证默认CSS包含关键样式
	if !contains(canvas.CSS, "body") {
		t.Error("默认CSS缺少body样式")
	}

	if !contains(canvas.CSS, "loading") {
		t.Error("默认CSS缺少loading样式")
	}

	if !contains(canvas.CSS, "spinner") {
		t.Error("默认CSS缺少spinner样式")
	}

	if !contains(canvas.CSS, "progress-bar") {
		t.Error("默认CSS缺少progress-bar样式")
	}

	if !contains(canvas.CSS, "result-card") {
		t.Error("默认CSS缺少result-card样式")
	}
}

// TestDefaultJS 测试默认JavaScript
func TestDefaultJS(t *testing.T) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("session_1", "Test")

	// 验证默认JS包含关键函数
	if !contains(canvas.JS, "initWebSocket") {
		t.Error("默认JS缺少initWebSocket函数")
	}

	if !contains(canvas.JS, "sendHandshake") {
		t.Error("默认JS缺少sendHandshake函数")
	}

	if !contains(canvas.JS, "handleMessage") {
		t.Error("默认JS缺少handleMessage函数")
	}

	if !contains(canvas.JS, "handleProgress") {
		t.Error("默认JS缺少handleProgress函数")
	}

	if !contains(canvas.JS, "sendTask") {
		t.Error("默认JS缺少sendTask函数")
	}

	if !contains(canvas.JS, "generateClientID") {
		t.Error("默认JS缺少generateClientID函数")
	}

	if !contains(canvas.JS, "generateMessageID") {
		t.Error("默认JS缺少generateMessageID函数")
	}
}

// BenchmarkCreateCanvas 性能测试: 创建Canvas
func BenchmarkCreateCanvas(b *testing.B) {
	host := NewCanvasHost()
	defer host.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		host.CreateCanvas("bench_session", "Benchmark Canvas")
	}
}

// BenchmarkRender 性能测试: 渲染Canvas
func BenchmarkRender(b *testing.B) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("bench_session", "Benchmark Canvas")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		host.Render(canvas.ID)
	}
}

// BenchmarkUpdateCanvas 性能测试: 更新Canvas
func BenchmarkUpdateCanvas(b *testing.B) {
	host := NewCanvasHost()
	defer host.Close()

	canvas := host.CreateCanvas("bench_session", "Benchmark Canvas")
	updates := map[string]interface{}{
		"html": "<div>Updated</div>",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		host.UpdateCanvas(canvas.ID, updates)
	}
}

// === 辅助函数 ===

// contains 检查字符串是否包含子串
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 ||
		(len(s) > 0 && len(substr) > 0 && findSubstring(s, substr)))
}

// findSubstring 查找子串
func findSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
