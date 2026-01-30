# 服务发现与配置中心

## 概述

ResearchGO 使用 **Consul + Traefik** 实现完整的微服务治理：

- **Consul**: 服务注册中心 + 配置中心（KV Store）
- **Traefik**: API 网关，从 Consul 获取服务信息
- **服务间动态发现**: 微服务可以动态发现其他服务的地址
- **配置热更新**: 从 Consul KV 读取配置，支持运行时更新

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部请求                                   │
│                            │                                     │
│                            ▼                                     │
│                     ┌─────────────┐                              │
│                     │   Traefik   │◄──── Consul Catalog Provider │
│                     │  (Gateway)  │                              │
│                     │   :8080     │                              │
│                     └──────┬──────┘                              │
│                            │                                     │
│         ┌─────────┬────────┼────────┬─────────┐                  │
│         ▼         ▼        ▼        ▼         ▼                  │
│   ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│   │  Agent   │ │ Auth │ │Paper │ │Vector│ │ ...  │              │
│   │ :8000    │ │:8001 │ │:8003 │ │:8004 │ │      │              │
│   └────┬─────┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘              │
│        │          │        │        │        │                   │
│        └──────────┴────────┴────────┴────────┘                   │
│                            │                                     │
│                            ▼                                     │
│                     ┌─────────────┐                              │
│                     │   Consul    │                              │
│                     │   :8500     │                              │
│                     │  (Registry) │                              │
│                     └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## 服务列表

| 服务 | 端口 | 路由前缀 | 说明 |
|------|------|----------|------|
| agent-service | 8000 | /api/agent | AI 智能体服务 |
| auth-service | 8001 | /api/auth | 认证服务 |
| conversation-service | 8002 | /api/conversations | 对话管理 |
| paper-storage-service | 8003 | /api/papers | 论文存储 |
| vector-search-service | 8004 | /api/vector | 向量搜索/RAG |
| literature-search-service | 8005 | /api/literature | 文献检索 |
| mindmap-service | 8007 | /api/mindmap | 思维导图 |
| analysis-service | 8008 | /api/analysis | 论文分析 |

## 服务注册流程

```
服务启动
    │
    ▼
读取环境变量
(CONSUL_HOST, SERVICE_NAME, SERVICE_PORT)
    │
    ▼
调用 Consul HTTP API
PUT /v1/agent/service/register
    │
    ▼
Consul 记录服务信息
    │
    ▼
Traefik 监听 Consul 变化
自动更新路由表
    │
    ▼
服务可被访问
```

## 健康检查

每个服务都暴露 `/health` 端点，Consul 定期检查：

```json
{
  "Check": {
    "HTTP": "http://service:port/health",
    "Interval": "10s",
    "Timeout": "5s",
    "DeregisterCriticalServiceAfter": "30s"
  }
}
```

- **检查间隔**: 10 秒
- **超时时间**: 5 秒
- **自动注销**: 服务连续失败 30 秒后自动从注册中心移除

## 配置说明

### 环境变量

每个微服务需要配置以下环境变量：

```yaml
environment:
  - CONSUL_HOST=consul          # Consul 地址
  - SERVICE_NAME=agent-service  # 服务名称
  - SERVICE_PORT=8000           # 服务端口
```

### Traefik 配置

`traefik/traefik.yml`:

```yaml
providers:
  # Consul Catalog Provider
  consulCatalog:
    endpoint:
      address: "consul:8500"
    exposedByDefault: false
    watch: true
```

## 使用方式

### 启动所有服务

```bash
docker-compose up -d
```

### 查看 Consul UI

访问 http://localhost:8500

可以看到：
- 所有已注册的服务
- 服务健康状态
- 服务实例详情

### 查看 Traefik Dashboard

访问 http://localhost:8081

可以看到：
- 路由规则
- 服务发现状态
- 请求统计

## 服务间调用

### 方式 1：通过 Docker DNS（当前使用）

```python
# 直接使用服务名
AUTH_SERVICE_URL = "http://auth-service:8001"
```

### 方式 2：通过 Consul DNS

```python
# 使用 Consul DNS 解析
AUTH_SERVICE_URL = "http://auth-service.service.consul:8001"
```

### 方式 3：通过 Consul HTTP API 动态发现

```python
from app.utils.consul_registry import get_consul_registry

registry = get_consul_registry()
auth_info = await registry.discover_service("auth-service")
# auth_info = {"address": "...", "port": 8001, "url": "http://..."}
```

## 故障处理

### 服务无法注册

1. 检查 Consul 是否运行：
   ```bash
   docker ps | grep consul
   ```

2. 检查网络连通性：
   ```bash
   docker exec <service-container> curl http://consul:8500/v1/status/leader
   ```

3. 查看服务日志：
   ```bash
   docker logs <service-container>
   ```

### 服务注册但 Traefik 不路由

1. 检查服务是否健康：
   - Consul UI → Services → 点击服务 → 查看健康检查状态

2. 检查 Traefik 是否发现服务：
   - Traefik Dashboard → HTTP → Services

3. 检查路由规则：
   - Traefik Dashboard → HTTP → Routers

## 配置中心 (Consul KV)

### 配置结构

```
config/
├── openai/
│   ├── model          = gpt-4o
│   ├── embedding_model= text-embedding-3-small
│   ├── max_tokens     = 4096
│   └── temperature    = 0.7
├── agent/
│   ├── max_iterations = 10
│   ├── timeout        = 120
│   └── enable_tools   = true
├── memory/
│   ├── sliding_window_size = 10
│   ├── enable_summary      = true
│   └── enable_semantic     = true
├── rag/
│   ├── chunk_size     = 1000
│   ├── top_k          = 5
│   ├── enable_reranker= false
│   └── enable_hybrid_search = true
└── services/
    ├── auth/port      = 8001
    ├── vector-search/port = 8004
    └── ...
```

### 初始化配置

```bash
# 初始化默认配置
python backend/scripts/init_consul_config.py init

# 强制覆盖已有配置
python backend/scripts/init_consul_config.py force-init

# 列出所有配置
python backend/scripts/init_consul_config.py list
```

### 在代码中使用配置中心

```python
from app.utils.config_center import get_config_center

# 获取配置
config = get_config_center()
model = await config.get("config/openai/model", "gpt-4o")
timeout = await config.get("config/agent/timeout", 120)

# 设置配置
await config.set("config/openai/model", "gpt-4o-mini")

# 监听配置变更
def on_model_change(key, new_value):
    print(f"Model changed to: {new_value}")

config.watch("config/openai/model", on_model_change)
await config.start_watching(["config/openai/model"])
```

### 通过 API 修改配置

```bash
# 修改配置
curl -X PUT http://localhost:8500/v1/kv/config/openai/model \
  -d "gpt-4o-mini"

# 读取配置
curl http://localhost:8500/v1/kv/config/openai/model?raw=true
```

### 配置热更新

配置中心支持热更新，无需重启服务：

1. 修改 Consul KV 中的配置
2. 配置中心定期检测变更
3. 触发注册的回调函数
4. 应用新配置

---

## 服务间动态发现

### 使用方式

```python
from app.utils.service_discovery import get_service_discovery

# 获取服务发现实例
sd = get_service_discovery()

# 动态获取服务 URL
auth_url = await sd.auth_service()
vector_url = await sd.vector_search_service()

# 或者使用通用方法
url = await sd.get_url("auth-service")
```

### 发现优先级

1. **Consul 动态发现** - 从 Consul 获取健康的服务实例
2. **环境变量** - 如 `AUTH_SERVICE_URL`
3. **Docker DNS** - 使用服务名称 `http://auth-service:8001`

### 与静态配置的对比

| 方面 | 静态配置 | 动态发现 |
|------|---------|---------|
| 配置方式 | 环境变量硬编码 | 从 Consul 获取 |
| 扩缩容 | 需要修改配置 | 自动发现新实例 |
| 故障转移 | 需要手动切换 | 自动剔除不健康实例 |
| 负载均衡 | 无 | 可扩展支持 |

---

## 扩展阅读

- [Consul 官方文档](https://developer.hashicorp.com/consul/docs)
- [Traefik Consul Provider](https://doc.traefik.io/traefik/providers/consul-catalog/)
- [Consul KV Store](https://developer.hashicorp.com/consul/docs/dynamic-app-config/kv)

