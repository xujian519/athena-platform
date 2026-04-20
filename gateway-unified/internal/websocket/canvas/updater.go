package canvas

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// UpdateType 更新类型
type UpdateType string

const (
	UpdateTypeReplace  UpdateType = "replace"  // 替换整个内容
	UpdateTypeAppend   UpdateType = "append"   // 追加内容
	UpdateTypePrepend  UpdateType = "prepend"  // 前置内容
	UpdateTypePatch    UpdateType = "patch"    // 补丁更新
	UpdateTypeIncrement UpdateType = "increment" // 增量更新
)

// Update 更新指令
type Update struct {
	ID        string                 `json:"id"`        // 更新ID
	Type      UpdateType             `json:"type"`      // 更新类型
	Target    string                 `json:"target"`    // 目标元素ID
	Data      map[string]interface{} `json:"data"`      // 更新数据
	Timestamp int64                  `json:"timestamp"` // 时间戳
}

// IncrementalUpdater 增量更新器
type IncrementalUpdater struct {
	updates    chan *Update
	buffer     map[string][]*Update
	bufferSize int
	mu         sync.RWMutex
	flushInterval time.Duration
	ctx        context.Context
	cancel     context.CancelFunc
}

// NewIncrementalUpdater 创建增量更新器
func NewIncrementalUpdater() *IncrementalUpdater {
	ctx, cancel := context.WithCancel(context.Background())

	updater := &IncrementalUpdater{
		updates:       make(chan *Update, 1000),
		buffer:        make(map[string][]*Update),
		bufferSize:    50,
		flushInterval: 100 * time.Millisecond,
		ctx:           ctx,
		cancel:        cancel,
	}

	// 启动后台处理
	go updater.processUpdates()
	go updater.flushPeriodically()

	return updater
}

// QueueUpdate 队列更新
func (iu *IncrementalUpdater) QueueUpdate(update *Update) error {
	select {
	case iu.updates <- update:
		return nil
	case <-iu.ctx.Done():
		return fmt.Errorf("更新器已关闭")
	default:
		return fmt.Errorf("更新队列已满")
	}
}

// QueueUpdateTarget 队列目标更新
func (iu *IncrementalUpdater) QueueUpdateTarget(target string, updateType UpdateType, data map[string]interface{}) error {
	update := &Update{
		ID:        generateUpdateID(),
		Type:      updateType,
		Target:    target,
		Data:      data,
		Timestamp: time.Now().UnixNano(),
	}

	return iu.QueueUpdate(update)
}

// processUpdates 处理更新
func (iu *IncrementalUpdater) processUpdates() {
	for {
		select {
		case update := <-iu.updates:
			iu.bufferUpdate(update)
		case <-iu.ctx.Done():
			return
		}
	}
}

// bufferUpdate 缓存更新
func (iu *IncrementalUpdater) bufferUpdate(update *Update) {
	iu.mu.Lock()
	defer iu.mu.Unlock()

	target := update.Target
	iu.buffer[target] = append(iu.buffer[target], update)

	// 如果缓冲区满了，立即刷新
	if len(iu.buffer[target]) >= iu.bufferSize {
		iu.flushTarget(target)
	}
}

// flushPeriodically 定期刷新缓冲区
func (iu *IncrementalUpdater) flushPeriodically() {
	ticker := time.NewTicker(iu.flushInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			iu.flushAll()
		case <-iu.ctx.Done():
			iu.flushAll()
			return
		}
	}
}

// flushAll 刷新所有缓冲区
func (iu *IncrementalUpdater) flushAll() {
	iu.mu.Lock()
	defer iu.mu.Unlock()

	for target := range iu.buffer {
		iu.flushTarget(target)
	}
}

// flushTarget 刷新目标缓冲区
func (iu *IncrementalUpdater) flushTarget(target string) {
	updates := iu.buffer[target]
	if len(updates) == 0 {
		return
	}

	// 合并更新
	merged := iu.mergeUpdates(updates)

	// 发送更新（这里需要WebSocket连接）
	// 实际实现中会通过WebSocket发送给客户端
	logging.LogInfo("刷新增量更新",
		logging.String("target", target),
		logging.Int("count", len(updates)),
		logging.Int("merged_count", len(merged)),
	)

	// 清空缓冲区
	delete(iu.buffer, target)
}

// mergeUpdates 合并更新
func (iu *IncrementalUpdater) mergeUpdates(updates []*Update) map[string]interface{} {
	merged := make(map[string]interface{})

	for _, update := range updates {
		// 根据更新类型合并
		switch update.Type {
		case UpdateTypeReplace:
			// 替换整个数据
			for k, v := range update.Data {
				merged[k] = v
			}
		case UpdateTypePatch:
			// 补丁更新，合并到现有数据
			for k, v := range update.Data {
				if existing, ok := merged[k]; ok {
					if existingMap, ok := existing.(map[string]interface{}); ok {
						if vMap, ok := v.(map[string]interface{}); ok {
							merged[k] = iu.mergeMaps(existingMap, vMap)
						} else {
							merged[k] = v
						}
					} else {
						merged[k] = v
					}
				} else {
					merged[k] = v
				}
			}
		case UpdateTypeIncrement:
			// 增量更新（如进度+1）
			for k, v := range update.Data {
				if existing, ok := merged[k]; ok {
					if existingInt, ok := existing.(int); ok {
						if vInt, ok := v.(int); ok {
							merged[k] = existingInt + vInt
						}
					} else if existingFloat, ok := existing.(float64); ok {
						if vFloat, ok := v.(float64); ok {
							merged[k] = existingFloat + vFloat
						}
					} else {
						merged[k] = v
					}
				} else {
					merged[k] = v
				}
			}
		case UpdateTypeAppend:
			// 追加数据（用于列表）
			for k, v := range update.Data {
				if existing, ok := merged[k]; ok {
					if existingSlice, ok := existing.([]interface{}); ok {
						if vSlice, ok := v.([]interface{}); ok {
							merged[k] = append(existingSlice, vSlice...)
						} else {
							merged[k] = append(existingSlice, v)
						}
					} else {
						merged[k] = []interface{}{existing, v}
					}
				} else {
					merged[k] = v
				}
			}
		}
	}

	return merged
}

// mergeMaps 合并map
func (iu *IncrementalUpdater) mergeMaps(a, b map[string]interface{}) map[string]interface{} {
	merged := make(map[string]interface{})

	for k, v := range a {
		merged[k] = v
	}

	for k, v := range b {
		if existing, ok := merged[k]; ok {
			if existingMap, ok := existing.(map[string]interface{}); ok {
				if vMap, ok := v.(map[string]interface{}); ok {
					merged[k] = iu.mergeMaps(existingMap, vMap)
					continue
				}
			}
		}
		merged[k] = v
	}

	return merged
}

// GenerateUpdateScript 生成更新脚本
func (iu *IncrementalUpdater) GenerateUpdateScript(target string, updates []*Update) string {
	script := fmt.Sprintf(`
// 增量更新脚本 - %s
(function() {
    const target = document.getElementById('%s');
    if (!target) return;

`, time.Now().Format("15:04:05.000"), target)

	for _, update := range updates {
		script += iu.generateUpdateScript(update)
	}

	script += `
})();
`
	return script
}

// generateUpdateScript 生成单个更新脚本
func (iu *IncrementalUpdater) generateUpdateScript(update *Update) string {
	switch update.Type {
	case UpdateTypeReplace:
		return iu.generateReplaceScript(update)
	case UpdateTypePatch:
		return iu.generatePatchScript(update)
	case UpdateTypeIncrement:
		return iu.generateIncrementScript(update)
	case UpdateTypeAppend:
		return iu.generateAppendScript(update)
	default:
		return ""
	}
}

// generateReplaceScript 生成替换脚本
func (iu *IncrementalUpdater) generateReplaceScript(update *Update) string {
	dataJSON, _ := json.Marshal(update.Data)

	return fmt.Sprintf(`
    // 替换内容
    try {
        const data = %s;
        for (const key in data) {
            target[key] = data[key];
        }
    } catch (e) {
        console.error('替换更新失败:', e);
    }
`, string(dataJSON))
}

// generatePatchScript 生成补丁脚本
func (iu *IncrementalUpdater) generatePatchScript(update *Update) string {
	dataJSON, _ := json.Marshal(update.Data)

	return fmt.Sprintf(`
    // 补丁更新
    try {
        const patch = %s;
        for (const key in patch) {
            if (typeof patch[key] === 'object' && typeof target[key] === 'object') {
                Object.assign(target[key], patch[key]);
            } else {
                target[key] = patch[key];
            }
        }
    } catch (e) {
        console.error('补丁更新失败:', e);
    }
`, string(dataJSON))
}

// generateIncrementScript 生成增量脚本
func (iu *IncrementalUpdater) generateIncrementScript(update *Update) string {
	dataJSON, _ := json.Marshal(update.Data)

	return fmt.Sprintf(`
    // 增量更新
    try {
        const inc = %s;
        for (const key in inc) {
            if (typeof target[key] === 'number') {
                target[key] += inc[key];
            }
        }
    } catch (e) {
        console.error('增量更新失败:', e);
    }
`, string(dataJSON))
}

// generateAppendScript 生成追加脚本
func (iu *IncrementalUpdater) generateAppendScript(update *Update) string {
	dataJSON, _ := json.Marshal(update.Data)

	return fmt.Sprintf(`
    // 追加内容
    try {
        const data = %s;
        for (const key in data) {
            if (Array.isArray(target[key])) {
                if (Array.isArray(data[key])) {
                    target[key].push(...data[key]);
                } else {
                    target[key].push(data[key]);
                }
            }
        }
    } catch (e) {
        console.error('追加更新失败:', e);
    }
`, string(dataJSON))
}

// Close 关闭更新器
func (iu *IncrementalUpdater) Close() {
	iu.cancel()
	close(iu.updates)
}

// generateUpdateID 生成更新ID
func generateUpdateID() string {
	return fmt.Sprintf("update_%d", time.Now().UnixNano())
}
