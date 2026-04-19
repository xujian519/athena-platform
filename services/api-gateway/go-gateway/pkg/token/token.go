package token

import (
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

// Claims JWT声明结构
type Claims struct {
	UserID   string   `json:"user_id"`
	Username string   `json:"username"`
	Email    string   `json:"email"`
	Roles    []string `json:"roles"`
	jwt.RegisteredClaims
}

// TokenManager Token管理器
type TokenManager struct {
	secretKey      string
	expirationTime time.Duration
	refreshTime    time.Duration
	issuer         string
}

// NewTokenManager 创建Token管理器
func NewTokenManager(secretKey string, expirationTime, refreshTime time.Duration, issuer string) *TokenManager {
	return &TokenManager{
		secretKey:      secretKey,
		expirationTime: expirationTime,
		refreshTime:    refreshTime,
		issuer:         issuer,
	}
}

// GenerateTokens 生成访问令牌和刷新令牌
func (tm *TokenManager) GenerateTokens(userID, username, email string, roles []string) (accessToken, refreshToken string, err error) {
	// 生成访问令牌
	accessToken, err = tm.generateToken(userID, username, email, roles, tm.expirationTime)
	if err != nil {
		return "", "", fmt.Errorf("生成访问令牌失败: %w", err)
	}

	// 生成刷新令牌
	refreshToken, err = tm.generateToken(userID, username, email, roles, tm.refreshTime)
	if err != nil {
		return "", "", fmt.Errorf("生成刷新令牌失败: %w", err)
	}

	return accessToken, refreshToken, nil
}

// generateToken 生成JWT令牌
func (tm *TokenManager) generateToken(userID, username, email string, roles []string, expiration time.Duration) (string, error) {
	now := time.Now()
	claims := Claims{
		UserID:   userID,
		Username: username,
		Email:    email,
		Roles:    roles,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    tm.issuer,
			Subject:   userID,
			Audience:  []string{"athena-gateway"},
			ExpiresAt: jwt.NewNumericDate(now.Add(expiration)),
			NotBefore: jwt.NewNumericDate(now),
			IssuedAt:  jwt.NewNumericDate(now),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(tm.secretKey))
}

// ParseJWT 解析JWT令牌
func ParseJWT(tokenString, secretKey string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("意外的签名方法: %v", token.Header["alg"])
		}
		return []byte(secretKey), nil
	})

	if err != nil {
		return nil, fmt.Errorf("解析令牌失败: %w", err)
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, fmt.Errorf("无效的令牌")
}

// ValidateToken 验证令牌
func (tm *TokenManager) ValidateToken(tokenString string) (*Claims, error) {
	claims, err := ParseJWT(tokenString, tm.secretKey)
	if err != nil {
		return nil, err
	}

	// 检查发行者
	if claims.Issuer != tm.issuer {
		return nil, fmt.Errorf("无效的发行者")
	}

	// 检查受众
	if !contains(claims.Audience, "athena-gateway") {
		return nil, fmt.Errorf("无效的受众")
	}

	return claims, nil
}

// RefreshToken 刷新令牌
func (tm *TokenManager) RefreshToken(refreshTokenString string) (newAccessToken, newRefreshToken string, err error) {
	// 解析刷新令牌
	claims, err := ParseJWT(refreshTokenString, tm.secretKey)
	if err != nil {
		return "", "", fmt.Errorf("解析刷新令牌失败: %w", err)
	}

	// 检查是否过期
	if claims.ExpiresAt != nil && claims.ExpiresAt.Time.Before(time.Now()) {
		return "", "", fmt.Errorf("刷新令牌已过期")
	}

	// 生成新的令牌
	return tm.GenerateTokens(claims.UserID, claims.Username, claims.Email, claims.Roles)
}

// HashPassword 哈希密码
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("密码哈希失败: %w", err)
	}
	return string(bytes), nil
}

// CheckPassword 验证密码
func CheckPassword(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// contains 检查字符串切片是否包含指定字符串
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
