+++
title = "05.Web开发实践"
date = 2026-01-19
description = "Go Web开发：框架选型、RESTful API、数据库操作、认证授权、部署"
[taxonomies]
tags = ["Go", "Web", "API"]
+++

## 框架选型

### 主流框架对比

| 框架 | 特点 | 适用场景 |
|------|------|----------|
| net/http | 标准库，无依赖 | 简单API |
| Gin | 高性能，轻量 | 生产环境首选 |
| Echo | 性能好，功能全 | RESTful API |
| Chi | 轻量，兼容标准库 | 微服务 |
| Fiber | 类Express语法 | Node.js转Go |

### Gin快速开始

```go
package main

import "github.com/gin-gonic/gin"

func main() {
    r := gin.Default()
    
    r.GET("/ping", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "pong"})
    })
    
    r.Run(":8080")
}
```

---

## RESTful API设计

### 路由设计

```go
r := gin.Default()

// 用户资源
users := r.Group("/api/v1/users")
{
    users.GET("", listUsers)         // 列表
    users.POST("", createUser)       // 创建
    users.GET("/:id", getUser)       // 详情
    users.PUT("/:id", updateUser)    // 更新
    users.DELETE("/:id", deleteUser) // 删除
}
```

### 请求处理

```go
// 路径参数
func getUser(c *gin.Context) {
    id := c.Param("id")
}

// 查询参数
func listUsers(c *gin.Context) {
    page := c.DefaultQuery("page", "1")
    limit := c.Query("limit")
}

// 请求体绑定
type CreateUserReq struct {
    Name  string `json:"name" binding:"required"`
    Email string `json:"email" binding:"required,email"`
    Age   int    `json:"age" binding:"gte=0,lte=150"`
}

func createUser(c *gin.Context) {
    var req CreateUserReq
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    // 处理
}
```

### 响应格式

```go
// 统一响应结构
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}

func Success(c *gin.Context, data interface{}) {
    c.JSON(200, Response{
        Code:    0,
        Message: "success",
        Data:    data,
    })
}

func Error(c *gin.Context, code int, message string) {
    c.JSON(code, Response{
        Code:    code,
        Message: message,
    })
}
```

---

## 中间件

### 内置中间件

```go
// 日志
r.Use(gin.Logger())

// 恢复
r.Use(gin.Recovery())

// CORS
r.Use(cors.Default())
```

### 自定义中间件

```go
// 认证中间件
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "unauthorized"})
            return
        }
        
        // 验证token
        claims, err := validateToken(token)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
            return
        }
        
        c.Set("user_id", claims.UserID)
        c.Next()
    }
}

// 使用
r.Use(AuthMiddleware())
// 或只对特定路由
protected := r.Group("/api", AuthMiddleware())
```

### 请求限流

```go
func RateLimitMiddleware(limit int) gin.HandlerFunc {
    limiter := rate.NewLimiter(rate.Limit(limit), limit)
    
    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.AbortWithStatusJSON(429, gin.H{"error": "too many requests"})
            return
        }
        c.Next()
    }
}
```

---

## 数据库操作

### GORM基础

```go
import "gorm.io/gorm"
import "gorm.io/driver/mysql"

// 连接
dsn := "user:pass@tcp(127.0.0.1:3306)/dbname?charset=utf8mb4&parseTime=True"
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})

// 模型
type User struct {
    gorm.Model
    Name  string `gorm:"size:100"`
    Email string `gorm:"uniqueIndex"`
    Age   int
}

// 自动迁移
db.AutoMigrate(&User{})
```

### CRUD操作

```go
// 创建
user := User{Name: "Alice", Email: "alice@example.com"}
result := db.Create(&user)

// 查询
var user User
db.First(&user, 1)                    // 主键查询
db.First(&user, "email = ?", email)   // 条件查询
db.Find(&users)                       // 全部

// 更新
db.Model(&user).Update("Name", "Bob")
db.Model(&user).Updates(User{Name: "Bob", Age: 18})

// 删除
db.Delete(&user)          // 软删除
db.Unscoped().Delete(&user) // 永久删除
```

### 事务

```go
err := db.Transaction(func(tx *gorm.DB) error {
    if err := tx.Create(&user1).Error; err != nil {
        return err
    }
    if err := tx.Create(&user2).Error; err != nil {
        return err
    }
    return nil
})
```

---

## 认证授权

### JWT认证

```go
import "github.com/golang-jwt/jwt/v5"

var jwtSecret = []byte("your-secret-key")

type Claims struct {
    UserID uint   `json:"user_id"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

// 生成Token
func GenerateToken(userID uint, role string) (string, error) {
    claims := Claims{
        UserID: userID,
        Role:   role,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(jwtSecret)
}

// 验证Token
func ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        return jwtSecret, nil
    })
    
    if err != nil {
        return nil, err
    }
    
    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }
    
    return nil, errors.New("invalid token")
}
```

### RBAC权限控制

```go
func RequireRole(roles ...string) gin.HandlerFunc {
    return func(c *gin.Context) {
        userRole := c.GetString("role")
        
        for _, role := range roles {
            if userRole == role {
                c.Next()
                return
            }
        }
        
        c.AbortWithStatusJSON(403, gin.H{"error": "forbidden"})
    }
}

// 使用
admin := r.Group("/admin", AuthMiddleware(), RequireRole("admin"))
```

---

## 配置管理

### Viper

```go
import "github.com/spf13/viper"

func initConfig() {
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath(".")
    
    viper.AutomaticEnv()
    
    if err := viper.ReadInConfig(); err != nil {
        log.Fatal(err)
    }
}

// config.yaml
// server:
//   port: 8080
// database:
//   host: localhost
//   port: 3306

port := viper.GetInt("server.port")
dbHost := viper.GetString("database.host")
```

### 环境变量

```go
type Config struct {
    ServerPort int    `env:"SERVER_PORT" envDefault:"8080"`
    DBHost     string `env:"DB_HOST" envDefault:"localhost"`
    DBPassword string `env:"DB_PASSWORD,required"`
}

import "github.com/caarlos0/env/v6"

var cfg Config
if err := env.Parse(&cfg); err != nil {
    log.Fatal(err)
}
```

---

## 日志

### Zap日志

```go
import "go.uber.org/zap"

logger, _ := zap.NewProduction()
defer logger.Sync()

logger.Info("User logged in",
    zap.String("username", "alice"),
    zap.Int("user_id", 123),
)

// Gin集成
r.Use(ginzap.Ginzap(logger, time.RFC3339, true))
```

---

## 部署

### Docker

```dockerfile
# 多阶段构建
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/main .
EXPOSE 8080
CMD ["./main"]
```

### 优雅关闭

```go
srv := &http.Server{
    Addr:    ":8080",
    Handler: r,
}

go func() {
    if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
        log.Fatalf("listen: %s\n", err)
    }
}()

quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

if err := srv.Shutdown(ctx); err != nil {
    log.Fatal("Server forced to shutdown:", err)
}
```

---

## 项目结构

```
project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handler/      # HTTP处理器
│   ├── service/      # 业务逻辑
│   ├── repository/   # 数据访问
│   ├── model/        # 数据模型
│   └── middleware/   # 中间件
├── pkg/              # 公共库
├── config/           # 配置
├── api/              # API文档
├── go.mod
├── go.sum
├── Dockerfile
└── Makefile
```

---

## 总结

| 组件 | 推荐 |
|------|------|
| 框架 | Gin、Echo |
| ORM | GORM |
| 配置 | Viper |
| 日志 | Zap |
| 认证 | JWT |
| 验证 | go-playground/validator |
| 文档 | Swagger |

Go Web开发生态成熟，标准库强大，第三方库丰富，是构建高性能后端服务的优秀选择。

---

## 相关文章

- [上一篇：标准库精选](/articles/golang/go-04-标准库精选/)
- [下一篇：性能优化](/articles/golang/go-06-性能优化/)
