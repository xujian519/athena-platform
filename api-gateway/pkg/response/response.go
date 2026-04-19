package response

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// Response 统一响应结构
type Response struct {
	Success   bool        `json:"success"`
	Code      int         `json:"code"`
	Message   string      `json:"message"`
	Data      interface{} `json:"data,omitempty"`
	Timestamp int64       `json:"timestamp"`
	RequestID string      `json:"request_id,omitempty"`
}

// ErrorResponse 错误响应结构
type ErrorResponse struct {
	Success   bool   `json:"success"`
	Code      int    `json:"code"`
	Message   string `json:"message"`
	Error     string `json:"error,omitempty"`
	Timestamp int64  `json:"timestamp"`
	RequestID string `json:"request_id,omitempty"`
}

// PagedResponse 分页响应结构
type PagedResponse struct {
	Success    bool        `json:"success"`
	Code       int         `json:"code"`
	Message    string      `json:"message"`
	Data       interface{} `json:"data"`
	Pagination Pagination  `json:"pagination"`
	Timestamp  int64       `json:"timestamp"`
	RequestID  string      `json:"request_id,omitempty"`
}

// Pagination 分页信息
type Pagination struct {
	Page       int  `json:"page"`
	PageSize   int  `json:"page_size"`
	Total      int  `json:"total"`
	TotalPages int  `json:"total_pages"`
	HasNext    bool `json:"has_next"`
	HasPrev    bool `json:"has_prev"`
}

// Success 成功响应
func Success(c *gin.Context, data interface{}) {
	response := Response{
		Success:   true,
		Code:      http.StatusOK,
		Message:   "操作成功",
		Data:      data,
		Timestamp: time.Now().Unix(),
	}

	// 添加请求ID（如果存在）
	if requestID, exists := c.Get("request_id"); exists {
		response.RequestID = requestID.(string)
	}

	c.JSON(http.StatusOK, response)
}

// SuccessWithMessage 带自定义消息的成功响应
func SuccessWithMessage(c *gin.Context, message string, data interface{}) {
	response := Response{
		Success:   true,
		Code:      http.StatusOK,
		Message:   message,
		Data:      data,
		Timestamp: time.Now().Unix(),
	}

	// 添加请求ID（如果存在）
	if requestID, exists := c.Get("request_id"); exists {
		response.RequestID = requestID.(string)
	}

	c.JSON(http.StatusOK, response)
}

// Error 错误响应
func Error(c *gin.Context, httpCode int, message string, errDetail string) {
	response := ErrorResponse{
		Success:   false,
		Code:      httpCode,
		Message:   message,
		Error:     errDetail,
		Timestamp: time.Now().Unix(),
	}

	// 添加请求ID（如果存在）
	if requestID, exists := c.Get("request_id"); exists {
		response.RequestID = requestID.(string)
	}

	c.JSON(httpCode, response)
}

// BadRequest 400错误响应
func BadRequest(c *gin.Context, message string) {
	Error(c, http.StatusBadRequest, message, "")
}

// Unauthorized 401错误响应
func Unauthorized(c *gin.Context, message string) {
	Error(c, http.StatusUnauthorized, message, "")
}

// Forbidden 403错误响应
func Forbidden(c *gin.Context, message string) {
	Error(c, http.StatusForbidden, message, "")
}

// NotFound 404错误响应
func NotFound(c *gin.Context, message string) {
	Error(c, http.StatusNotFound, message, "")
}

// MethodNotAllowed 405错误响应
func MethodNotAllowed(c *gin.Context, message string) {
	Error(c, http.StatusMethodNotAllowed, message, "")
}

// InternalServerError 500错误响应
func InternalServerError(c *gin.Context, message string) {
	Error(c, http.StatusInternalServerError, message, "")
}

// ServiceUnavailable 503错误响应
func ServiceUnavailable(c *gin.Context, message string) {
	Error(c, http.StatusServiceUnavailable, message, "")
}

// TooManyRequests 429错误响应
func TooManyRequests(c *gin.Context, message string) {
	Error(c, http.StatusTooManyRequests, message, "")
}

// Paged 分页响应
func Paged(c *gin.Context, data interface{}, pagination Pagination) {
	response := PagedResponse{
		Success:    true,
		Code:       http.StatusOK,
		Message:    "操作成功",
		Data:       data,
		Pagination: pagination,
		Timestamp:  time.Now().Unix(),
	}

	// 添加请求ID（如果存在）
	if requestID, exists := c.Get("request_id"); exists {
		response.RequestID = requestID.(string)
	}

	c.JSON(http.StatusOK, response)
}

// Created 201创建成功响应
func Created(c *gin.Context, message string, data interface{}) {
	response := Response{
		Success:   true,
		Code:      http.StatusCreated,
		Message:   message,
		Data:      data,
		Timestamp: time.Now().Unix(),
	}

	// 添加请求ID（如果存在）
	if requestID, exists := c.Get("request_id"); exists {
		response.RequestID = requestID.(string)
	}

	c.JSON(http.StatusCreated, response)
}

// NoContent 204无内容响应
func NoContent(c *gin.Context) {
	c.Status(http.StatusNoContent)
}

// NewPagination 创建分页信息
func NewPagination(page, pageSize, total int) Pagination {
	if page <= 0 {
		page = 1
	}
	if pageSize <= 0 {
		pageSize = 10
	}

	totalPages := (total + pageSize - 1) / pageSize
	hasNext := page < totalPages
	hasPrev := page > 1

	return Pagination{
		Page:       page,
		PageSize:   pageSize,
		Total:      total,
		TotalPages: totalPages,
		HasNext:    hasNext,
		HasPrev:    hasPrev,
	}
}

// ValidationError 验证错误响应
func ValidationError(c *gin.Context, errors interface{}) {
	Error(c, http.StatusUnprocessableEntity, "请求参数验证失败", "")
	c.JSON(http.StatusUnprocessableEntity, gin.H{
		"success":   false,
		"code":      http.StatusUnprocessableEntity,
		"message":   "请求参数验证失败",
		"errors":    errors,
		"timestamp": time.Now().Unix(),
	})
}
