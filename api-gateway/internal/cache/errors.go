package cache

import "fmt"

var (
	ErrCacheNotFound = fmt.Errorf("缓存项不存在")
	ErrCacheExpired  = fmt.Errorf("缓存项已过期")
)
