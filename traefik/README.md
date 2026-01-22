# Traefik API 网关

ResearchGO 使用 Traefik 作为 API 网关，统一管理所有微服务的入口。

## 架构

```
                    ┌─────────────────┐
                    │   Frontend      │
                    │  (Vue.js)       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Traefik       │
                    │   API Gateway   │
                    │   :8080         │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ auth-service  │  │ chat-service  │  │ paper-service │
│    :8001      │  │    :8006      │  │    :8003      │
└───────────────┘  └───────────────┘  └───────────────┘
        ...（其他微服务）
```

## 启动

```bash
# 启动 Traefik（和其他基础设施）
docker-compose up -d traefik

# 或启动所有服务
docker-compose up -d
```

## 访问

| 地址 | 说明 |
|------|------|
| http://localhost:8080 | API 网关入口 |
| http://localhost:8081 | Traefik Dashboard |

## 路由规则

| 路径 | 目标服务 | 端口 |
|------|----------|------|
| `/api/auth/*` | auth-service | 8001 |
| `/api/conversations/*` | conversation-service | 8002 |
| `/api/papers/*` | paper-service | 8003 |
| `/api/vector/*` | vector-service | 8004 |
| `/api/literature/*` | literature-service | 8005 |
| `/api/chat/*` | chat-service | 8006 |
| `/api/mindmap/*` | mindmap-service | 8007 |
| `/api/analysis/*` | analysis-service | 8008 |

## 前端配置

在 `.env` 文件中启用网关模式：

```env
# 启用 API 网关
VITE_USE_GATEWAY=true
VITE_GATEWAY_URL=http://localhost:8080
```

不使用网关（直接连接各微服务）：

```env
# 禁用 API 网关（默认）
VITE_USE_GATEWAY=false
```

## 配置文件说明

```
traefik/
├── traefik.yml              # 静态配置（入口点、提供者）
├── dynamic/
│   └── services.yml         # 动态配置（路由、服务、中间件）
└── README.md
```

## 添加新服务

在 `dynamic/services.yml` 中添加：

```yaml
http:
  routers:
    new-service-router:
      rule: "PathPrefix(`/api/new-service`)"
      service: new-service
      entryPoints:
        - web

  services:
    new-service:
      loadBalancer:
        servers:
          - url: "http://host.docker.internal:8009"
```

## 中间件

### CORS（已配置）
```yaml
middlewares:
  cors-headers:
    headers:
      accessControlAllowOriginList:
        - "*"
```

### 限流（可选）
```yaml
middlewares:
  rate-limit:
    rateLimit:
      average: 100
      burst: 50
```

要启用中间件，在路由中添加：

```yaml
routers:
  auth-router:
    rule: "PathPrefix(`/api/auth`)"
    service: auth-service
    middlewares:
      - cors-headers
      - rate-limit
    entryPoints:
      - web
```

## 注意事项

1. **host.docker.internal**: Windows/Mac Docker 自动支持，Linux 需要在 docker-compose.yml 中添加 `extra_hosts`
2. **微服务必须运行**: Traefik 只做转发，各微服务需要单独启动
3. **热更新**: 修改 `dynamic/` 目录下的配置会自动生效，无需重启 Traefik

