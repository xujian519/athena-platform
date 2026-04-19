// Package logging - 日志轮转写入器实现
// 提供基于大小和时间的日志轮转功能
package logging

import (
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// RotateWriter 日志轮转写入器
type RotateWriter struct {
	filename string
	config   *RotationConfig
	mu       sync.Mutex
	file     *os.File
	size     int64
}

// NewRotateWriter 创建日志轮转写入器
func NewRotateWriter(filename string, config *RotationConfig) (*RotateWriter, error) {
	if config == nil {
		config = DefaultRotationConfig()
	}

	w := &RotateWriter{
		filename: filename,
		config:   config,
	}

	// 确保日志目录存在
	if err := os.MkdirAll(filepath.Dir(filename), 0755); err != nil {
		return nil, fmt.Errorf("创建日志目录失败: %w", err)
	}

	// 打开或创建日志文件
	if err := w.openFile(); err != nil {
		return nil, err
	}

	return w, nil
}

// Write 实现io.Writer接口
func (w *RotateWriter) Write(p []byte) (n int, err error) {
	w.mu.Lock()
	defer w.mu.Unlock()

	writeLen := int64(len(p))

	// 检查是否需要轮转
	if w.size+writeLen > int64(w.config.MaxSize*1024*1024) {
		if err := w.rotate(); err != nil {
			return 0, err
		}
	}

	// 写入日志
	n, err = w.file.Write(p)
	if err != nil {
		return n, err
	}

	w.size += int64(n)
	return n, nil
}

// rotate 执行日志轮转
func (w *RotateWriter) rotate() error {
	// 关闭当前文件
	if err := w.file.Close(); err != nil {
		return fmt.Errorf("关闭日志文件失败: %w", err)
	}

	// 重命名当前文件为备份
	basename := filepath.Base(w.filename)
	ext := filepath.Ext(w.filename)
	nameWithoutExt := strings.TrimSuffix(basename, ext)

	// 找到下一个可用的备份编号
	backupNum := 1
	for {
		backupName := fmt.Sprintf("%s.%d%s", nameWithoutExt, backupNum, ext)
		if _, err := os.Stat(filepath.Join(filepath.Dir(w.filename), backupName)); os.IsNotExist(err) {
			break
		}
		backupNum++
	}

	// 重命名当前文件
	backupPath := filepath.Join(filepath.Dir(w.filename), fmt.Sprintf("%s.%d%s", nameWithoutExt, 1, ext))
	if err := os.Rename(w.filename, backupPath); err != nil {
		return fmt.Errorf("重命名日志文件失败: %w", err)
	}

	// 压缩备份文件（如果启用）
	if w.config.Compress {
		go w.compressBackup(backupPath)
	}

	// 清理旧备份
	go w.cleanupOldBackups()

	// 打开新的日志文件
	return w.openFile()
}

// openFile 打开日志文件
func (w *RotateWriter) openFile() error {
	file, err := os.OpenFile(w.filename, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return fmt.Errorf("打开日志文件失败: %w", err)
	}

	w.file = file

	// 获取当前文件大小
	info, err := file.Stat()
	if err != nil {
		return fmt.Errorf("获取文件信息失败: %w", err)
	}

	w.size = info.Size()
	return nil
}

// compressBackup 压缩备份文件
func (w *RotateWriter) compressBackup(backupPath string) {
	// 打开源文件
	src, err := os.Open(backupPath)
	if err != nil {
		return
	}
	defer src.Close()

	// 创建压缩文件
	gzPath := backupPath + ".gz"
	gz, err := os.Create(gzPath)
	if err != nil {
		return
	}
	defer gz.Close()

	// 创建gzip写入器
	gzw := gzip.NewWriter(gz)
	defer gzw.Close()

	// 复制数据
	if _, err := io.Copy(gzw, src); err != nil {
		os.Remove(gzPath)
		return
	}

	// 删除原始文件
	os.Remove(backupPath)
}

// cleanupOldBackups 清理旧备份文件
func (w *RotateWriter) cleanupOldBackups() {
	dir := filepath.Dir(w.filename)
	basename := filepath.Base(w.filename)
	ext := filepath.Ext(basename)
	nameWithoutExt := strings.TrimSuffix(basename, ext)

	// 查找所有备份文件
	files, err := filepath.Glob(filepath.Join(dir, nameWithoutExt+".*"))
	if err != nil {
		return
	}

	// 按修改时间排序
	type fileInfo struct {
		name    string
		modTime time.Time
	}

	var fileInfos []fileInfo
	for _, f := range files {
		if f == w.filename {
			continue // 跳过当前文件
		}

		info, err := os.Stat(f)
		if err != nil {
			continue
		}

		fileInfos = append(fileInfos, fileInfo{
			name:    f,
			modTime: info.ModTime(),
		})
	}

	// 按修改时间降序排序（最新的在前）
	sort.Slice(fileInfos, func(i, j int) bool {
		return fileInfos[i].modTime.After(fileInfos[j].modTime)
	})

	// 删除超过数量的备份
	if w.config.MaxBackups > 0 {
		for i := w.config.MaxBackups; i < len(fileInfos); i++ {
			os.Remove(fileInfos[i].name)
		}
		fileInfos = fileInfos[:min(len(fileInfos), w.config.MaxBackups)]
	}

	// 删除超过天数的备份
	if w.config.MaxAge > 0 {
		cutoff := time.Now().Add(-time.Duration(w.config.MaxAge) * 24 * time.Hour)
		for _, f := range fileInfos {
			if f.modTime.Before(cutoff) {
				os.Remove(f.name)
			}
		}
	}
}

// Close 关闭写入器
func (w *RotateWriter) Close() error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.file != nil {
		return w.file.Close()
	}
	return nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
