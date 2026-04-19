// Package logging - 结构化日志字段定义
// 提供多种类型的日志字段，支持结构化日志输出
package logging

import (
	"fmt"
	"runtime"
	"time"
)

// ==================== 字段接口和基础类型 ====================

// Field 日志字段接口
type Field interface {
	Key() string
	Value() interface{}
}

// ==================== 基础类型字段 ====================

// stringField 字符串字段
type stringField struct {
	key   string
	value string
}

func (f *stringField) Key() string          { return f.key }
func (f *stringField) Value() interface{} { return f.value }

// String 创建字符串字段
func String(key, value string) Field {
	return &stringField{key: key, value: value}
}

// intField 整数字段
type intField struct {
	key   string
	value int64
}

func (f *intField) Key() string          { return f.key }
func (f *intField) Value() interface{} { return f.value }

// Int 创建整数字段
func Int(key string, value int) Field {
	return &intField{key: key, value: int64(value)}
}

// Int64 创建64位整数字段
func Int64(key string, value int64) Field {
	return &intField{key: key, value: value}
}

// uintField 无符号整数字段
type uintField struct {
	key   string
	value uint64
}

func (f *uintField) Key() string          { return f.key }
func (f *uintField) Value() interface{} { return f.value }

// Uint 创建无符号整数字段
func Uint(key string, value uint) Field {
	return &uintField{key: key, value: uint64(value)}
}

// Uint64 创建64位无符号整数字段
func Uint64(key string, value uint64) Field {
	return &uintField{key: key, value: value}
}

// floatField 浮点数字段
type floatField struct {
	key   string
	value float64
}

func (f *floatField) Key() string          { return f.key }
func (f *floatField) Value() interface{} { return f.value }

// Float64 创建64位浮点数字段
func Float64(key string, value float64) Field {
	return &floatField{key: key, value: value}
}

// Float32 创建32位浮点数字段
func Float32(key string, value float32) Field {
	return &floatField{key: key, value: float64(value)}
}

// boolField 布尔字段
type boolField struct {
	key   string
	value bool
}

func (f *boolField) Key() string          { return f.key }
func (f *boolField) Value() interface{} { return f.value }

// Bool 创建布尔字段
func Bool(key string, value bool) Field {
	return &boolField{key: key, value: value}
}

// errorField 错误字段
type errorField struct {
	key   string
	value error
}

func (f *errorField) Key() string          { return f.key }
func (f *errorField) Value() interface{} { return f.value }

// Err 创建错误字段（使用"error"作为key）
func Err(err error) Field {
	return &errorField{key: "error", value: err}
}

// NamedErr 创建命名错误字段
func NamedErr(key string, err error) Field {
	return &errorField{key: key, value: err}
}

// ==================== 复杂类型字段 ====================

// durationField 时间段字段
type durationField struct {
	key   string
	value time.Duration
}

func (f *durationField) Key() string          { return f.key }
func (f *durationField) Value() interface{} { return f.value }

// Duration 创建时间段字段
func Duration(key string, value time.Duration) Field {
	return &durationField{key: key, value: value}
}

// timeField 时间字段
type timeField struct {
	key   string
	value time.Time
}

func (f *timeField) Key() string          { return f.key }
func (f *timeField) Value() interface{} { return f.value }

// Time 创建时间字段
func Time(key string, value time.Time) Field {
	return &timeField{key: key, value: value}
}

// ==================== 容器类型字段 ====================

// stringSlice 字符串切片字段
type stringSlice struct {
	key   string
	value []string
}

func (f *stringSlice) Key() string          { return f.key }
func (f *stringSlice) Value() interface{} { return f.value }

// Strings 创建字符串切片字段
func Strings(key string, value []string) Field {
	return &stringSlice{key: key, value: value}
}

// anyField 任意类型字段
type anyField struct {
	key   string
	value interface{}
}

func (f *anyField) Key() string          { return f.key }
func (f *anyField) Value() interface{} { return f.value }

// Any 创建任意类型字段
func Any(key string, value interface{}) Field {
	return &anyField{key: key, value: value}
}

// ==================== 辅助函数 ====================

// Errf 格式化错误字段
func Errf(format string, args ...interface{}) Field {
	return &errorField{key: "error", value: fmt.Errorf(format, args...)}
}

// callers 获取调用栈
func callers() []uintptr {
	const depth = 32
	var pcs [depth]uintptr
	n := runtime.Callers(1, pcs[:])
	return pcs[0:n]
}
