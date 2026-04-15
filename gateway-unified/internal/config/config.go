package config

// Config 网关配置
type Config struct {
	Server     ServerConfig     `yaml:"server" json:"server"`
	TLS        TLSConfig        `yaml:"tls" json:"tls"`
	Logging    LoggingConfig    `yaml:"logging" json:"logging"`
	Monitoring MonitoringConfig `yaml:"monitoring" json:"monitoring"`
	Tailscale  TailscaleConfig  `yaml:"tailscale" json:"tailscale"`
	Auth       AuthConfig       `yaml:"auth" json:"auth"`
}

// TailscaleConfig Tailscale配置
// 支持Serve模式（Tailnet内部访问）和Funnel模式（公共互联网访问）
type TailscaleConfig struct {
	// 模式: off, serve, funnel
	// - off: 默认，不使用Tailscale
	// - serve: Tailnet内部访问，通过tailscale serve
	// - funnel: 公共HTTPS访问，通过tailscale funnel
	Mode string `yaml:"mode" json:"mode"`

	// 退出时重置Tailscale配置
	ResetOnExit bool `yaml:"reset_on_exit" json:"reset_on_exit"`

	// 是否启用Tailscale身份认证（仅serve模式）
	// 当启用时，可以通过Tailscale身份头进行无密码认证
	AllowTailscaleAuth bool `yaml:"allow_tailscale_auth" json:"allow_tailscale_auth"`
}

// AuthConfig 认证配置
type AuthConfig struct {
	// 认证模式: token, password
	Mode string `yaml:"mode" json:"mode"`

	// Token（可从环境变量OPENCLAW_GATEWAY_TOKEN获取）
	Token string `yaml:"token" json:"token"`

	// 密码（可从环境变量OPENCLAW_GATEWAY_PASSWORD获取）
	Password string `yaml:"password" json:"password"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Port         int  `yaml:"port" json:"port"`
	Production   bool `yaml:"production" json:"production"`
	ReadTimeout  int  `yaml:"read_timeout" json:"read_timeout"`
	WriteTimeout int  `yaml:"write_timeout" json:"write_timeout"`
	IdleTimeout  int  `yaml:"idle_timeout" json:"idle_timeout"`
}

// TLSConfig TLS配置
type TLSConfig struct {
	Enabled  bool   `yaml:"enabled" json:"enabled"`
	CertFile string `yaml:"cert_file" json:"cert_file"`
	KeyFile  string `yaml:"key_file" json:"key_file"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level  string `yaml:"level" json:"level"`
	Format string `yaml:"format" json:"format"`
	Output string `yaml:"output" json:"output"`
}

// MonitoringConfig 监控配置
type MonitoringConfig struct {
	Enabled bool   `yaml:"enabled" json:"enabled"`
	Port    int    `yaml:"port" json:"port"`
	Path    string `yaml:"path" json:"path"`
}

// IsProduction 判断是否为生产环境
func (c *Config) IsProduction() bool {
	return c.Server.Production
}

// IsTailscaleEnabled 判断是否启用Tailscale
func (c *Config) IsTailscaleEnabled() bool {
	return c.Tailscale.Mode != "" && c.Tailscale.Mode != "off"
}

// IsTailscaleServe 判断是否为Serve模式
func (c *Config) IsTailscaleServe() bool {
	return c.Tailscale.Mode == "serve"
}

// IsTailscaleFunnel 判断是否为Funnel模式
func (c *Config) IsTailscaleFunnel() bool {
	return c.Tailscale.Mode == "funnel"
}

// IsAuthRequired 判断是否需要认证
func (c *Config) IsAuthRequired() bool {
	// Funnel模式强制要求认证
	if c.IsTailscaleFunnel() {
		return true
	}
	// 其他模式根据配置决定
	return c.Auth.Mode != ""
}
