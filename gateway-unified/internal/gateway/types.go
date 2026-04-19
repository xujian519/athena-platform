package gateway

// BatchRegisterRequest 批量注册服务请求
type BatchRegisterRequest struct {
	Services []ServiceSpec `json:"services" binding:"required,dive"`
}

// ServiceSpec 服务规格
type ServiceSpec struct {
	Name     string                 `json:"name" binding:"required"`
	Host     string                 `json:"host" binding:"required"`
	Port     int                    `json:"port" binding:"required,min=1,max=65535"`
	Weight   int                    `json:"weight"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// UpdateServiceInstanceRequest 更新服务实例请求
type UpdateServiceInstanceRequest struct {
	Weight   int                    `json:"weight" binding:"min=0,max=100"`
	Host     string                 `json:"hostname" binding:"omitempty"`
	Port     int                    `json:"port" binding:"omitempty,min=1,max=65535"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
	Status   string                 `json:"status" binding:"omitempty,oneof=UP DOWN"`
}

// DependencySpec 依赖规格
type DependencySpec struct {
	Service   string   `json:"service" binding:"required"`
	DependsOn []string `json:"depends_on" binding:"required"`
}
