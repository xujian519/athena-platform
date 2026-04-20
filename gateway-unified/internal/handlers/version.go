// Package handlers - API版本管理处理器
package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/middleware"
)

// VersionHandler API版本管理处理器
type VersionHandler struct {
	versionConfig *middleware.VersionConfig
}

// NewVersionHandler 创建版本管理处理器
func NewVersionHandler(versionConfig *middleware.VersionConfig) *VersionHandler {
	return &VersionHandler{
		versionConfig: versionConfig,
	}
}

// ListVersions 列出所有API版本
// @Summary 列出所有API版本
// @Tags version
// @Produce json
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/versions [get]
func (h *VersionHandler) ListVersions(c *gin.Context) {
	versions := h.versionConfig.ListVersions()

	// 获取当前请求的版本
	currentVersion, _ := c.Get("api_version")

	c.JSON(http.StatusOK, gin.H{
		"success":        true,
		"current_version": currentVersion,
		"default_version": h.versionConfig.GetDefaultVersion(),
		"versions":       versions,
	})
}

// GetVersion 获取特定版本信息
// @Summary 获取特定版本信息
// @Tags version
// @Produce json
// @Param version path string true "版本号 (v1, v2, etc.)"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "版本不存在"
// @Router /api/v1/versions/{version} [get]
func (h *VersionHandler) GetVersion(c *gin.Context) {
	version := c.Param("version")

	// 标准化版本号
	if len(version) > 0 && version[0] != 'v' {
		version = "v" + version
	}

	versionInfo, exists := h.versionConfig.GetVersion(version)
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "版本不存在",
			"version": version,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    versionInfo,
	})
}

// RegisterVersion 注册新API版本
// @Summary 注册新API版本
// @Tags version
// @Accept json
// @Produce json
// @Param request body middleware.APIVersion true "版本信息"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 400 {object} map[string]interface{} "错误响应"
// @Router /api/v1/versions [post]
func (h *VersionHandler) RegisterVersion(c *gin.Context) {
	var req struct {
		Version       string `json:"version" binding:"required"`
		Deprecated    bool   `json:"deprecated"`
		SunsetDate    string `json:"sunset_date"`
		RemovedDate   string `json:"removed_date"`
		MigrationGuide string `json:"migration_guide"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// 标准化版本号
	if len(req.Version) > 0 && req.Version[0] != 'v' {
		req.Version = "v" + req.Version
	}

	// 检查版本是否已存在
	if _, exists := h.versionConfig.GetVersion(req.Version); exists {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "版本已存在",
			"version": req.Version,
		})
		return
	}

	// 创建版本信息
	info := &middleware.APIVersion{
		Deprecated:     req.Deprecated,
		SunsetDate:     req.SunsetDate,
		RemovedDate:    req.RemovedDate,
		MigrationGuide: req.MigrationGuide,
	}

	h.versionConfig.RegisterVersion(req.Version, info)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"version": req.Version,
			"info":    info,
		},
	})
}

// UpdateVersion 更新API版本信息
// @Summary 更新API版本信息
// @Tags version
// @Accept json
// @Produce json
// @Param version path string true "版本号"
// @Param request body middleware.APIVersion true "版本信息"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "版本不存在"
// @Router /api/v1/versions/{version} [put]
func (h *VersionHandler) UpdateVersion(c *gin.Context) {
	version := c.Param("version")

	// 标准化版本号
	if len(version) > 0 && version[0] != 'v' {
		version = "v" + version
	}

	// 检查版本是否存在
	if _, exists := h.versionConfig.GetVersion(version); !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "版本不存在",
			"version": version,
		})
		return
	}

	var req struct {
		Deprecated     *bool   `json:"deprecated"`
		SunsetDate     *string `json:"sunset_date"`
		RemovedDate    *string `json:"removed_date"`
		MigrationGuide *string `json:"migration_guide"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// 获取现有版本信息
	existingInfo, _ := h.versionConfig.GetVersion(version)

	// 更新字段
	if req.Deprecated != nil {
		existingInfo.Deprecated = *req.Deprecated
	}
	if req.SunsetDate != nil {
		existingInfo.SunsetDate = *req.SunsetDate
	}
	if req.RemovedDate != nil {
		existingInfo.RemovedDate = *req.RemovedDate
	}
	if req.MigrationGuide != nil {
		existingInfo.MigrationGuide = *req.MigrationGuide
	}

	// 重新注册（更新）
	h.versionConfig.RegisterVersion(version, existingInfo)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    existingInfo,
	})
}

// DeprecateVersion 废弃API版本
// @Summary 废弃API版本
// @Tags version
// @Accept json
// @Produce json
// @Param version path string true "版本号"
// @Param request body object {sunset_date:string,removed_date:string,migration_guide:string} true "废弃信息"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "版本不存在"
// @Router /api/v1/versions/{version}/deprecate [post]
func (h *VersionHandler) DeprecateVersion(c *gin.Context) {
	version := c.Param("version")

	// 标准化版本号
	if len(version) > 0 && version[0] != 'v' {
		version = "v" + version
	}

	// 检查版本是否存在
	versionInfo, exists := h.versionConfig.GetVersion(version)
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "版本不存在",
			"version": version,
		})
		return
	}

	var req struct {
		SunsetDate     string `json:"sunset_date"`
		RemovedDate    string `json:"removed_date"`
		MigrationGuide string `json:"migration_guide"`
	}

	c.ShouldBindJSON(&req)

	// 更新废弃信息
	versionInfo.Deprecated = true
	if req.SunsetDate != "" {
		versionInfo.SunsetDate = req.SunsetDate
	}
	if req.RemovedDate != "" {
		versionInfo.RemovedDate = req.RemovedDate
	}
	if req.MigrationGuide != "" {
		versionInfo.MigrationGuide = req.MigrationGuide
	}

	// 重新注册
	h.versionConfig.RegisterVersion(version, versionInfo)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    versionInfo,
		"message": "版本已标记为废弃",
	})
}

// SetDefaultVersion 设置默认API版本
// @Summary 设置默认API版本
// @Tags version
// @Accept json
// @Produce json
// @Param request body object {version:string} true "版本号"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 400 {object} map[string]interface{} "错误响应"
// @Router /api/v1/versions/default [put]
func (h *VersionHandler) SetDefaultVersion(c *gin.Context) {
	var req struct {
		Version string `json:"version" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// 标准化版本号
	if len(req.Version) > 0 && req.Version[0] != 'v' {
		req.Version = "v" + req.Version
	}

	// 检查版本是否存在
	if _, exists := h.versionConfig.GetVersion(req.Version); !exists {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "版本不存在",
			"version": req.Version,
		})
		return
	}

	h.versionConfig.SetDefaultVersion(req.Version)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"default_version": req.Version,
		},
	})
}
