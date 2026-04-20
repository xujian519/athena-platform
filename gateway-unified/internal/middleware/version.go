// Package middleware - API版本管理中间件
package middleware

import (
	"net/http"
	"regexp"
	"strings"
	"sync"

	"github.com/gin-gonic/gin"
)

// APIVersion API版本信息
type APIVersion struct {
	Version       string `json:"version"`       // 版本号 (v1, v2, etc.)
	Deprecated    bool   `json:"deprecated"`    // 是否废弃
	SunsetDate    string `json:"sunset_date"`   // 废弃日期 (可选)
	RemovedDate   string `json:"removed_date"`  // 移除日期 (可选)
	MigrationGuide string `json:"migration_guide"` // 迁移指南URL (可选)
}

// VersionConfig 版本管理配置
type VersionConfig struct {
	// 版本映射表: version -> APIVersion
	versions map[string]*APIVersion
	versionsMu sync.RWMutex

	// 默认版本
	DefaultVersion string

	// 是否启用版本检测
	EnableVersionDetection bool

	// 是否在响应头中返回版本信息
	IncludeVersionHeader bool
}

// NewVersionConfig 创建版本配置
func NewVersionConfig() *VersionConfig {
	return &VersionConfig{
		versions:               make(map[string]*APIVersion),
		DefaultVersion:         "v1",
		EnableVersionDetection: true,
		IncludeVersionHeader:   true,
	}
}

// RegisterVersion 注册API版本
func (v *VersionConfig) RegisterVersion(version string, info *APIVersion) {
	v.versionsMu.Lock()
	defer v.versionsMu.Unlock()

	info.Version = version
	v.versions[version] = info
}

// UnregisterVersion 注销API版本
func (v *VersionConfig) UnregisterVersion(version string) {
	v.versionsMu.Lock()
	defer v.versionsMu.Unlock()
	delete(v.versions, version)
}

// GetVersion 获取版本信息
func (v *VersionConfig) GetVersion(version string) (*APIVersion, bool) {
	v.versionsMu.RLock()
	defer v.versionsMu.RUnlock()

	info, exists := v.versions[version]
	return info, exists
}

// ListVersions 列出所有版本
func (v *VersionConfig) ListVersions() []*APIVersion {
	v.versionsMu.RLock()
	defer v.versionsMu.RUnlock()

	versions := make([]*APIVersion, 0, len(v.versions))
	for _, info := range v.versions {
		versions = append(versions, info)
	}
	return versions
}

// SetDefaultVersion 设置默认版本
func (v *VersionConfig) SetDefaultVersion(version string) {
	v.versionsMu.Lock()
	defer v.versionsMu.Unlock()
	v.DefaultVersion = version
}

// GetDefaultVersion 获取默认版本
func (v *VersionConfig) GetDefaultVersion() string {
	v.versionsMu.RLock()
	defer v.versionsMu.RUnlock()
	return v.DefaultVersion
}

// extractVersionFromPath 从URL路径中提取版本号
// 支持格式: /api/v1/..., /api/v2/..., /v1/..., etc.
func extractVersionFromPath(path string) string {
	// 匹配 /api/v{数字}/ 或 /v{数字}/ 模式
	re := regexp.MustCompile(`^/api/v(\d+)/|^/v(\d+)/`)
	matches := re.FindStringSubmatch(path)

	if len(matches) >= 2 {
		if matches[1] != "" {
			return "v" + matches[1]
		}
		if len(matches) >= 3 && matches[2] != "" {
			return "v" + matches[2]
		}
	}

	return ""
}

// extractVersionFromHeader 从请求头中提取版本号
// 支持的Header: X-API-Version, Accept-Version, API-Version
func extractVersionFromHeader(c *gin.Context) string {
	// 尝试从不同的Header中获取版本
	headers := []string{"X-API-Version", "Accept-Version", "API-Version"}

	for _, header := range headers {
		if version := c.GetHeader(header); version != "" {
			// 标准化版本号 (确保以v开头)
			if !strings.HasPrefix(version, "v") {
				return "v" + version
			}
			return version
		}
	}

	return ""
}

// extractVersionFromQuery 从查询参数中提取版本号
func extractVersionFromQuery(c *gin.Context) string {
	if version := c.Query("version"); version != "" {
		// 标准化版本号
		if !strings.HasPrefix(version, "v") {
			return "v" + version
		}
		return version
	}
	return ""
}

// VersionMiddleware 版本管理中间件
// 检测API版本并设置到上下文中，同时处理废弃版本警告
func (v *VersionConfig) VersionMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !v.EnableVersionDetection {
			c.Next()
			return
		}

		// 按优先级提取版本号: URL路径 > 请求头 > 查询参数 > 默认版本
		var version string

		// 1. 从URL路径提取
		if pathVersion := extractVersionFromPath(c.Request.URL.Path); pathVersion != "" {
			version = pathVersion
		}

		// 2. 从请求头提取
		if version == "" {
			version = extractVersionFromHeader(c)
		}

		// 3. 从查询参数提取
		if version == "" {
			version = extractVersionFromQuery(c)
		}

		// 4. 使用默认版本
		if version == "" {
			version = v.GetDefaultVersion()
		}

		// 标准化版本号
		if !strings.HasPrefix(version, "v") {
			version = "v" + version
		}

		// 验证版本是否存在
		versionInfo, exists := v.GetVersion(version)
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "不支持的API版本",
				"version": version,
				"valid_versions": func() []string {
					versions := v.ListVersions()
					result := make([]string, len(versions))
					for i, v := range versions {
						result[i] = v.Version
					}
					return result
				}(),
			})
			c.Abort()
			return
		}

		// 设置版本到上下文
		c.Set("api_version", version)
		c.Set("api_version_info", versionInfo)

		// 如果版本已废弃，添加警告Header
		if versionInfo.Deprecated {
			c.Header("X-API-Deprecated", "true")
			c.Header("X-API-Deprecation-Version", version)

			if versionInfo.SunsetDate != "" {
				c.Header("Sunset", versionInfo.SunsetDate)
			}

			if versionInfo.RemovedDate != "" {
				c.Header("X-API-Removal-Date", versionInfo.RemovedDate)
			}

			if versionInfo.MigrationGuide != "" {
				c.Header("X-API-Migration-Guide", versionInfo.MigrationGuide)
			}

			// 在响应体中添加警告
			c.Header("Warning", `299 - "API version `+version+` is deprecated"`)
		}

		// 如果启用，在响应头中返回当前版本
		if v.IncludeVersionHeader {
			c.Header("X-API-Version", version)
		}

		c.Next()
	}
}

// RequireVersionMiddleware 要求特定版本的中间件
// 用于强制要求特定版本的API
func (v *VersionConfig) RequireVersionMiddleware(requiredVersion string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 标准化版本号
		if !strings.HasPrefix(requiredVersion, "v") {
			requiredVersion = "v" + requiredVersion
		}

		// 获取当前请求的版本
		currentVersion, exists := c.Get("api_version")
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "未指定API版本",
			})
			c.Abort()
			return
		}

		// 检查版本是否匹配
		if currentVersion != requiredVersion {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "API版本不匹配",
				"required": requiredVersion,
				"provided": currentVersion,
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// MinVersionMiddleware 要求最低版本的中间件
func (v *VersionConfig) MinVersionMiddleware(minVersion string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 标准化版本号
		if !strings.HasPrefix(minVersion, "v") {
			minVersion = "v" + minVersion
		}

		// 获取当前请求的版本
		currentVersion, exists := c.Get("api_version")
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "未指定API版本",
			})
			c.Abort()
			return
		}

		// 比较版本号
		if compareVersions(currentVersion.(string), minVersion) < 0 {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "API版本过低",
				"min_required": minVersion,
				"provided": currentVersion,
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// compareVersions 比较两个版本号
// 返回: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
func compareVersions(v1, v2 string) int {
	// 移除v前缀
	v1 = strings.TrimPrefix(v1, "v")
	v2 = strings.TrimPrefix(v2, "v")

	// 简单比较版本号
	if v1 < v2 {
		return -1
	} else if v1 > v2 {
		return 1
	}
	return 0
}

// LoadVersionsFromConfig 从配置加载版本信息
// 配置格式:
// {
//   "versions": [
//     {"version": "v1", "deprecated": false},
//     {"version": "v2", "deprecated": false},
//     {"version": "v3", "deprecated": true, "sunset_date": "2026-12-31", "removed_date": "2027-01-01"}
//   ],
//   "default_version": "v2"
// }
func (v *VersionConfig) LoadVersionsFromConfig(config map[string]interface{}) {
	// 加载版本列表
	if versions, ok := config["versions"].([]interface{}); ok {
		for _, ver := range versions {
			if verMap, ok := ver.(map[string]interface{}); ok {
				versionStr := ""
				info := &APIVersion{}

				if ver, ok := verMap["version"].(string); ok {
					versionStr = ver
				}

				if deprecated, ok := verMap["deprecated"].(bool); ok {
					info.Deprecated = deprecated
				}

				if sunsetDate, ok := verMap["sunset_date"].(string); ok {
					info.SunsetDate = sunsetDate
				}

				if removedDate, ok := verMap["removed_date"].(string); ok {
					info.RemovedDate = removedDate
				}

				if migrationGuide, ok := verMap["migration_guide"].(string); ok {
					info.MigrationGuide = migrationGuide
				}

				if versionStr != "" {
					v.RegisterVersion(versionStr, info)
				}
			}
		}
	}

	// 加载默认版本
	if defaultVer, ok := config["default_version"].(string); ok {
		v.SetDefaultVersion(defaultVer)
	}
}
