package tailscale

import (
	"context"
	"fmt"
	"os/exec"
	"strings"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/config"
)

// Manager Tailscale管理器
// 负责自动配置Tailscale Serve或Funnel
type Manager struct {
	cfg        *config.TailscaleConfig
	serverPort int
	hostname   string
}

// NewManager 创建Tailscale管理器
func NewManager(cfg *config.TailscaleConfig, serverPort int) *Manager {
	return &Manager{
		cfg:        cfg,
		serverPort: serverPort,
	}
}

// IsAvailable 检查Tailscale CLI是否可用
func (m *Manager) IsAvailable() bool {
	_, err := exec.LookPath("tailscale")
	return err == nil
}

// Status 获取Tailscale状态
func (m *Manager) Status() (string, error) {
	if !m.IsAvailable() {
		return "", fmt.Errorf("tailscale CLI未安装")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "tailscale", "status", "--json")
	outputBytes, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("获取Tailscale状态失败: %w", err)
	}

	return string(outputBytes), nil
}

// GetHostname 获取Tailscale主机名
func (m *Manager) GetHostname() (string, error) {
	if m.hostname != "" {
		return m.hostname, nil
	}

	if !m.IsAvailable() {
		return "", fmt.Errorf("tailscale CLI未安装")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 使用tailscale status获取主机名
	cmd := exec.CommandContext(ctx, "tailscale", "status")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("获取Tailscale状态失败: %w", err)
	}

	// 解析输出获取主机名
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		// 查找包含Tailscale IP的行
		if strings.Contains(line, "100.") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				// 第一列是主机名，第二列是IP
				m.hostname = parts[0]
				return m.hostname, nil
			}
		}
	}

	return "", fmt.Errorf("无法获取主机名")
}

// GetTailnetName 获取Tailnet名称
func (m *Manager) GetTailnetName() (string, error) {
	if !m.IsAvailable() {
		return "", fmt.Errorf("tailscale CLI未安装")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "tailscale", "debug", "prefs")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("获取Tailscale偏好设置失败: %w", err)
	}

	// 从输出中解析Tailnet名称
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "Tailnet") || strings.Contains(line, "tailnet") {
			parts := strings.Split(line, ":")
			if len(parts) >= 2 {
				return strings.TrimSpace(parts[1]), nil
			}
		}
	}

	return "", fmt.Errorf("无法获取Tailnet名称")
}

// SetupServe 配置Tailscale Serve
// 将Gateway暴露给Tailnet内部访问
func (m *Manager) SetupServe() error {
	if !m.IsAvailable() {
		return fmt.Errorf("tailscale CLI未安装")
	}

	if m.cfg.Mode != "serve" {
		return fmt.Errorf("当前模式不是serve: %s", m.cfg.Mode)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 配置tailscale serve
	// tailscale serve --bg https:443 / http://127.0.0.1:8005
	targetURL := fmt.Sprintf("http://127.0.0.1:%d", m.serverPort)

	cmd := exec.CommandContext(ctx, "tailscale", "serve", "--bg", "https:443", "/", targetURL)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("配置Tailscale Serve失败: %w, 输出: %s", err, string(output))
	}

	fmt.Printf("✅ Tailscale Serve配置成功\n")
	fmt.Printf("   目标: %s\n", targetURL)
	return nil
}

// SetupFunnel 配置Tailscale Funnel
// 将Gateway暴露给公共互联网访问
func (m *Manager) SetupFunnel() error {
	if !m.IsAvailable() {
		return fmt.Errorf("tailscale CLI未安装")
	}

	if m.cfg.Mode != "funnel" {
		return fmt.Errorf("当前模式不是funnel: %s", m.cfg.Mode)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 配置tailscale funnel
	// tailscale funnel --bg --https=443 / http://127.0.0.1:8005
	targetURL := fmt.Sprintf("http://127.0.0.1:%d", m.serverPort)

	cmd := exec.CommandContext(ctx, "tailscale", "funnel", "--bg", "--https=443", "/", targetURL)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("配置Tailscale Funnel失败: %w, 输出: %s", err, string(output))
	}

	fmt.Printf("✅ Tailscale Funnel配置成功\n")
	fmt.Printf("   目标: %s\n", targetURL)
	return nil
}

// Setup 根据配置自动设置
func (m *Manager) Setup() error {
	switch m.cfg.Mode {
	case "serve":
		return m.SetupServe()
	case "funnel":
		return m.SetupFunnel()
	case "off", "":
		return nil
	default:
		return fmt.Errorf("未知的Tailscale模式: %s", m.cfg.Mode)
	}
}

// Reset 重置Tailscale配置
func (m *Manager) Reset() error {
	if !m.IsAvailable() {
		return nil
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// 重置serve和funnel配置
	cmd := exec.CommandContext(ctx, "tailscale", "serve", "--reset")
	_, _ = cmd.CombinedOutput() // 忽略错误

	fmt.Println("🔄 Tailscale配置已重置")
	return nil
}

// GetServeURL 获取Serve的访问URL
func (m *Manager) GetServeURL() (string, error) {
	hostname, err := m.GetHostname()
	if err != nil {
		return "", err
	}

	tailnet, err := m.GetTailnetName()
	if err != nil {
		// 如果获取不到tailnet，使用默认格式
		return fmt.Sprintf("https://%s.ts.net/", hostname), nil
	}

	return fmt.Sprintf("https://%s.%s.ts.net/", hostname, tailnet), nil
}

// Whois 通过IP获取Tailscale用户信息
func (m *Manager) Whois(ip string) (string, error) {
	if !m.IsAvailable() {
		return "", fmt.Errorf("tailscale CLI未安装")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "tailscale", "whois", ip)
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("whois查询失败: %w", err)
	}

	return string(output), nil
}

// VerifyTailscaleAuth 验证Tailscale身份认证
// 检查请求是否来自Tailscale Serve，并验证用户身份
func (m *Manager) VerifyTailscaleAuth(forwardedFor, userLogin string) (bool, string, error) {
	if !m.cfg.AllowTailscaleAuth {
		return false, "", fmt.Errorf("Tailscale身份认证未启用")
	}

	// 验证forwarded_for是否是Tailscale IP
	if forwardedFor == "" {
		return false, "", fmt.Errorf("缺少X-Forwarded-For头")
	}

	// 通过tailscale whois验证IP
	whoisResult, err := m.Whois(forwardedFor)
	if err != nil {
		return false, "", err
	}

	// 检查whois结果中是否包含用户登录名
	if userLogin != "" && strings.Contains(whoisResult, userLogin) {
		return true, userLogin, nil
	}

	// 从whois结果中提取用户信息
	lines := strings.Split(whoisResult, "\n")
	for _, line := range lines {
		if strings.Contains(line, "@") {
			// 找到邮箱，提取用户名
			parts := strings.Fields(line)
			for _, part := range parts {
				if strings.Contains(part, "@") {
					return true, part, nil
				}
			}
		}
	}

	return false, "", fmt.Errorf("无法验证用户身份")
}

// PrintInfo 打印Tailscale配置信息
func (m *Manager) PrintInfo() {
	if m.cfg.Mode == "off" || m.cfg.Mode == "" {
		fmt.Println("📍 Tailscale: 未启用")
		return
	}

	fmt.Println("📍 Tailscale配置:")
	fmt.Printf("   模式: %s\n", m.cfg.Mode)
	fmt.Printf("   退出时重置: %v\n", m.cfg.ResetOnExit)
	fmt.Printf("   允许Tailscale认证: %v\n", m.cfg.AllowTailscaleAuth)

	// 尝试获取访问URL
	if url, err := m.GetServeURL(); err == nil {
		fmt.Printf("   访问地址: %s\n", url)
	}
}
