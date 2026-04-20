// Package middleware - 安全头中间件
package middleware

import (
	"strings"

	"github.com/gin-gonic/gin"
)

// SecurityHeadersConfigExtended 扩展的安全头配置
type SecurityHeadersConfigExtended struct {
	// X-Content-Type-Options
	// 值: nosniff
	// 防止浏览器MIME类型嗅探
	XContentTypeOptions string

	// X-Frame-Options
	// 值: DENY, SAMEORIGIN, ALLOW-FROM uri
	// 防止点击劫持攻击
	XFrameOptions string

	// X-XSS-Protection
	// 值: 1; mode=block
	// 启用浏览器XSS保护
	XXSSProtection string

	// Strict-Transport-Security
	// 值: max-age=31536000; includeSubDomains; preload
	// 强制使用HTTPS
	StrictTransportSecurity string

	// Content-Security-Policy
	// 值: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'
	// 控制资源加载策略
	ContentSecurityPolicy string

	// Referrer-Policy
	// 值: no-referrer, no-referrer-when-downgrade, origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
	// 控制Referer头信息发送
	ReferrerPolicy string

	// Permissions-Policy
	// 值: geolocation=(), microphone=(), camera=()
	// 控制浏览器功能和API
	PermissionsPolicy string

	// Cross-Origin-Opener-Policy
	// 值: same-origin, same-origin-allow-popups, unsafe-none
	// 控制跨域窗口行为
	CrossOriginOpenerPolicy string

	// Cross-Origin-Resource-Policy
	// 值: same-site, same-origin, cross-origin
	// 控制跨域资源访问
	CrossOriginResourcePolicy string

	// Cross-Origin-Embedder-Policy
	// 值: require-corp, credentialless
	// 控制跨域嵌入策略
	CrossOriginEmbedderPolicy string

	// 是否移除Server头
	RemoveServerHeader bool

	// 自定义Server头值
	ServerHeaderValue string
}

// DefaultSecurityHeadersConfigExtended 默认安全头配置
func DefaultSecurityHeadersConfigExtended() *SecurityHeadersConfigExtended {
	return &SecurityHeadersConfigExtended{
		XContentTypeOptions:       "nosniff",
		XFrameOptions:             "DENY",
		XXSSProtection:            "1; mode=block",
		StrictTransportSecurity:   "max-age=31536000; includeSubDomains",
		ContentSecurityPolicy:     "default-src 'self'",
		ReferrerPolicy:            "strict-origin-when-cross-origin",
		PermissionsPolicy:         "geolocation=(), microphone=(), camera=()",
		CrossOriginOpenerPolicy:   "same-origin",
		CrossOriginResourcePolicy: "same-site",
		CrossOriginEmbedderPolicy: "",
		RemoveServerHeader:        true,
		ServerHeaderValue:         "",
	}
}

// DevelopmentSecurityHeadersConfigExtended 开发环境安全头配置
func DevelopmentSecurityHeadersConfigExtended() *SecurityHeadersConfigExtended {
	return &SecurityHeadersConfigExtended{
		XContentTypeOptions:       "nosniff",
		XFrameOptions:             "SAMEORIGIN", // 开发环境允许同源嵌入
		XXSSProtection:            "1; mode=block",
		StrictTransportSecurity:   "", // 开发环境不使用HTTPS
		ContentSecurityPolicy:     "default-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*",
		ReferrerPolicy:            "strict-origin-when-cross-origin",
		PermissionsPolicy:         "geolocation=(self), microphone=(self), camera=(self)",
		CrossOriginOpenerPolicy:   "same-origin-allow-popups", // 允许弹出窗口
		CrossOriginResourcePolicy: "same-site",
		CrossOriginEmbedderPolicy: "",
		RemoveServerHeader:        false,
		ServerHeaderValue:         "Athena-Gateway/Dev",
	}
}

// ProductionSecurityHeadersConfigExtended 生产环境安全头配置
func ProductionSecurityHeadersConfigExtended() *SecurityHeadersConfigExtended {
	return &SecurityHeadersConfigExtended{
		XContentTypeOptions:       "nosniff",
		XFrameOptions:             "DENY",
		XXSSProtection:            "1; mode=block",
		StrictTransportSecurity:   "max-age=31536000; includeSubDomains; preload",
		ContentSecurityPolicy:     "default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'",
		ReferrerPolicy:            "no-referrer",
		PermissionsPolicy:         "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
		CrossOriginOpenerPolicy:   "same-origin",
		CrossOriginResourcePolicy: "same-origin",
		CrossOriginEmbedderPolicy: "require-corp",
		RemoveServerHeader:        true,
		ServerHeaderValue:         "",
	}
}

// SecurityHeadersMiddlewareExtended 安全头中间件
func SecurityHeadersMiddlewareExtended(config *SecurityHeadersConfigExtended) gin.HandlerFunc {
	if config == nil {
		config = DefaultSecurityHeadersConfigExtended()
	}

	return func(c *gin.Context) {
		// X-Content-Type-Options
		if config.XContentTypeOptions != "" {
			c.Header("X-Content-Type-Options", config.XContentTypeOptions)
		}

		// X-Frame-Options
		if config.XFrameOptions != "" {
			c.Header("X-Frame-Options", config.XFrameOptions)
		}

		// X-XSS-Protection
		if config.XXSSProtection != "" {
			c.Header("X-XSS-Protection", config.XXSSProtection)
		}

		// Strict-Transport-Security (仅HTTPS)
		if config.StrictTransportSecurity != "" && c.Request.TLS != nil {
			c.Header("Strict-Transport-Security", config.StrictTransportSecurity)
		}

		// Content-Security-Policy
		if config.ContentSecurityPolicy != "" {
			c.Header("Content-Security-Policy", config.ContentSecurityPolicy)
		}

		// Referrer-Policy
		if config.ReferrerPolicy != "" {
			c.Header("Referrer-Policy", config.ReferrerPolicy)
		}

		// Permissions-Policy
		if config.PermissionsPolicy != "" {
			c.Header("Permissions-Policy", config.PermissionsPolicy)
		}

		// Cross-Origin-Opener-Policy
		if config.CrossOriginOpenerPolicy != "" {
			c.Header("Cross-Origin-Opener-Policy", config.CrossOriginOpenerPolicy)
		}

		// Cross-Origin-Resource-Policy
		if config.CrossOriginResourcePolicy != "" {
			c.Header("Cross-Origin-Resource-Policy", config.CrossOriginResourcePolicy)
		}

		// Cross-Origin-Embedder-Policy
		if config.CrossOriginEmbedderPolicy != "" {
			c.Header("Cross-Origin-Embedder-Policy", config.CrossOriginEmbedderPolicy)
		}

		// Server头
		if config.RemoveServerHeader {
			c.Header("Server", "")
		} else if config.ServerHeaderValue != "" {
			c.Header("Server", config.ServerHeaderValue)
		}

		// 移除敏感信息头
		c.Header("X-Powered-By", "")

		c.Next()
	}
}

// ContentSecurityPolicyBuilder CSP构建器
type ContentSecurityPolicyBuilder struct {
	directives map[string]string
}

// NewContentSecurityPolicyBuilder 创建CSP构建器
func NewContentSecurityPolicyBuilder() *ContentSecurityPolicyBuilder {
	return &ContentSecurityPolicyBuilder{
		directives: make(map[string]string),
	}
}

// DefaultSrc 设置default-src
func (b *ContentSecurityPolicyBuilder) DefaultSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["default-src"] = strings.Join(sources, " ")
	return b
}

// ScriptSrc 设置script-src
func (b *ContentSecurityPolicyBuilder) ScriptSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["script-src"] = strings.Join(sources, " ")
	return b
}

// StyleSrc 设置style-src
func (b *ContentSecurityPolicyBuilder) StyleSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["style-src"] = strings.Join(sources, " ")
	return b
}

// ImgSrc 设置img-src
func (b *ContentSecurityPolicyBuilder) ImgSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["img-src"] = strings.Join(sources, " ")
	return b
}

// ConnectSrc 设置connect-src
func (b *ContentSecurityPolicyBuilder) ConnectSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["connect-src"] = strings.Join(sources, " ")
	return b
}

// FontSrc 设置font-src
func (b *ContentSecurityPolicyBuilder) FontSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["font-src"] = strings.Join(sources, " ")
	return b
}

// ObjectSrc 设置object-src
func (b *ContentSecurityPolicyBuilder) ObjectSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["object-src"] = strings.Join(sources, " ")
	return b
}

// MediaSrc 设置media-src
func (b *ContentSecurityPolicyBuilder) MediaSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["media-src"] = strings.Join(sources, " ")
	return b
}

// FrameSrc 设置frame-src
func (b *ContentSecurityPolicyBuilder) FrameSrc(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["frame-src"] = strings.Join(sources, " ")
	return b
}

// BaseURI 设置base-uri
func (b *ContentSecurityPolicyBuilder) BaseURI(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["base-uri"] = strings.Join(sources, " ")
	return b
}

// FormAction 设置form-action
func (b *ContentSecurityPolicyBuilder) FormAction(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["form-action"] = strings.Join(sources, " ")
	return b
}

// FrameAncestors 设置frame-ancestors
func (b *ContentSecurityPolicyBuilder) FrameAncestors(sources ...string) *ContentSecurityPolicyBuilder {
	b.directives["frame-ancestors"] = strings.Join(sources, " ")
	return b
}

// ReportURI 设置report-uri
func (b *ContentSecurityPolicyBuilder) ReportURI(uri string) *ContentSecurityPolicyBuilder {
	b.directives["report-uri"] = uri
	return b
}

// ReportTo 设置report-to
func (b *ContentSecurityPolicyBuilder) ReportTo(endpoint string) *ContentSecurityPolicyBuilder {
	b.directives["report-to"] = endpoint
	return b
}

// UpgradeInsecureRequests 升级不安全请求
func (b *ContentSecurityPolicyBuilder) UpgradeInsecureRequests() *ContentSecurityPolicyBuilder {
	b.directives["upgrade-insecure-requests"] = ""
	return b
}

// BlockAllMixedContent 阻止混合内容
func (b *ContentSecurityPolicyBuilder) BlockAllMixedContent() *ContentSecurityPolicyBuilder {
	b.directives["block-all-mixed-content"] = ""
	return b
}

// Build 构建CSP策略
func (b *ContentSecurityPolicyBuilder) Build() string {
	parts := make([]string, 0, len(b.directives))
	for directive, value := range b.directives {
		if value == "" {
			parts = append(parts, directive)
		} else {
			parts = append(parts, directive+" "+value)
		}
	}
	return strings.Join(parts, "; ")
}

// CommonCSPSources 常用CSP源
var CommonCSPSources = struct {
	Self          string
	None          string
	UnsafeInline  string
	UnsafeEval    string
	UnsafeHashes  string
	StrictDynamic string
	ReportSample  string
	Data          string
	Blob          string
	Any           string
	HTTPS         string
	Localhost     string
}{
	Self:         "'self'",
	None:         "'none'",
	UnsafeInline: "'unsafe-inline'",
	UnsafeEval:   "'unsafe-eval'",
	UnsafeHashes: "'unsafe-hashes'",
	StrictDynamic: "'strict-dynamic'",
	ReportSample:  "'report-sample'",
	Data:         "data:",
	Blob:         "blob:",
	Any:          "*",
	HTTPS:        "https:",
	Localhost:    "localhost:",
}

// CSPForDevelopment 开发环境CSP
func CSPForDevelopment() string {
	return NewContentSecurityPolicyBuilder().
		DefaultSrc(CommonCSPSources.Self).
		ScriptSrc(CommonCSPSources.Self, CommonCSPSources.UnsafeInline, CommonCSPSources.UnsafeEval).
		StyleSrc(CommonCSPSources.Self, CommonCSPSources.UnsafeInline).
		ImgSrc(CommonCSPSources.Self, CommonCSPSources.Data, CommonCSPSources.Blob).
		ConnectSrc(CommonCSPSources.Self, "localhost:*", "127.0.0.1:*").
		Build()
}

// CSPForProduction 生产环境CSP
func CSPForProduction(domains ...string) string {
	sources := append([]string{CommonCSPSources.Self}, domains...)

	return NewContentSecurityPolicyBuilder().
		DefaultSrc(CommonCSPSources.Self).
		ScriptSrc(sources...).
		StyleSrc(sources...).
		ImgSrc(append(sources, CommonCSPSources.Data)...).
		ConnectSrc(sources...).
		ObjectSrc(CommonCSPSources.None).
		BaseURI(CommonCSPSources.Self).
		FormAction(CommonCSPSources.Self).
		FrameAncestors(CommonCSPSources.None).
		UpgradeInsecureRequests().
		Build()
}
