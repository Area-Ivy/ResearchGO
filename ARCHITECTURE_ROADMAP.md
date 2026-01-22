# ResearchGO 架构演进路线图

## 目录

- [当前架构](#当前架构)
- [与工业级项目的差距](#与工业级项目的差距)
- [架构优化方向](#架构优化方向)
- [演进路线图](#演进路线图)

---

## 当前架构

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue.js)                        │
│                          localhost:5173                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Traefik API Gateway                           │
│                       localhost:8080                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ auth-service  │   │ chat-service  │   │ paper-service │
│    :8001      │   │    :8006      │   │    :8003      │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    MySQL      │   │    MinIO      │   │    Milvus     │
│    :3306      │   │    :9000      │   │    :19530     │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 当前服务清单

| 服务 | 端口 | 职责 | 依赖 |
|------|------|------|------|
| auth-service | 8001 | 用户认证、JWT 签发 | MySQL |
| conversation-service | 8002 | 对话历史管理 | MySQL |
| paper-storage-service | 8003 | 论文上传、存储、管理 | MySQL, MinIO |
| vector-search-service | 8004 | 语义搜索、RAG | Milvus, OpenAI |
| literature-search-service | 8005 | 学术文献检索 | OpenAlex API |
| chat-service | 8006 | AI 对话 | OpenAI |
| mindmap-service | 8007 | 思维导图生成 | MinIO, OpenAI |
| analysis-service | 8008 | 论文分析报告 | MinIO, OpenAI |

### 已完成

- [x] 微服务拆分（8 个服务）
- [x] API 网关（Traefik）
- [x] JWT 认证
- [x] 基础设施容器化（MySQL, MinIO, Milvus, RabbitMQ, Redis）
- [x] 前端适配微服务

---

## 与工业级项目的差距

### 🔴 核心差距（生产必备）

#### 1. 可观测性 (Observability)

**当前状态**：无

**工业标准**：

| 组件 | 作用 | 推荐工具 |
|------|------|----------|
| 日志聚合 | 统一收集、检索所有服务日志 | ELK Stack / Loki + Grafana |
| 分布式追踪 | 追踪请求在各服务间的调用链 | Jaeger / Zipkin / SkyWalking |
| 指标监控 | QPS、延迟、错误率、资源使用 | Prometheus + Grafana |
| 告警系统 | 异常自动通知 | AlertManager / PagerDuty |

**影响**：
- 服务故障无法及时发现
- 性能问题难以定位
- 无法进行容量规划

#### 2. 服务治理

**当前状态**：服务地址硬编码，无容错机制

**工业标准**：

| 组件 | 当前 | 目标 |
|------|------|------|
| 服务发现 | URL 硬编码 | Consul / Nacos 动态发现 |
| 配置中心 | 分散的 .env 文件 | Apollo / Nacos 统一配置 |
| 熔断器 | 无 | Hystrix / Sentinel / resilience4j |
| 限流 | 无 | Sentinel / Traefik 插件 |
| 重试机制 | 无 | 指数退避重试 |
| 负载均衡 | Traefik 轮询 | 加权轮询、最少连接 |

**影响**：
- 单点故障导致级联失败
- 配置变更需要重启服务
- 突发流量可能打垮服务

#### 3. 数据一致性

**当前状态**：无分布式事务处理

**工业标准**：

| 问题 | 解决方案 |
|------|----------|
| 分布式事务 | Saga 模式 / TCC / 本地消息表 |
| 消息可靠性 | 消息确认、死信队列、重试 |
| 幂等性 | 唯一请求 ID、去重表 |
| 最终一致性 | 事件溯源、补偿机制 |

**影响**：
- 跨服务操作可能产生不一致数据
- 网络抖动导致数据丢失

### 🟡 重要差距（生产推荐）

#### 4. CI/CD 流水线

**当前状态**：手动启动

**工业标准**：

```
代码提交
    │
    ▼
┌─────────────┐
│  代码检查   │  ESLint, Black, SonarQube
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  单元测试   │  pytest, Jest (覆盖率 > 80%)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  构建镜像   │  Docker Build
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  集成测试   │  E2E 测试
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  自动部署   │  蓝绿/金丝雀发布
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  自动回滚   │  健康检查失败时
└─────────────┘
```

#### 5. 安全加固

| 缺失项 | 风险 | 解决方案 |
|--------|------|----------|
| 服务间认证 | 内部服务可被任意调用 | mTLS / 服务网格 |
| 密钥管理 | API Key 明文存储 | HashiCorp Vault |
| 审计日志 | 无操作记录 | 审计中间件 |
| HTTPS | 当前 HTTP 明文传输 | Let's Encrypt 证书 |
| 输入验证 | SQL 注入、XSS 风险 | 参数校验、WAF |

#### 6. 测试体系

**当前状态**：手动测试脚本

**工业标准**：

| 测试类型 | 覆盖范围 | 工具 |
|----------|----------|------|
| 单元测试 | 函数/方法级别 | pytest, Jest |
| 集成测试 | 服务内部模块 | pytest + testcontainers |
| 契约测试 | 服务间 API 兼容性 | Pact |
| E2E 测试 | 完整用户流程 | Playwright, Cypress |
| 性能测试 | 压力、负载测试 | Locust, k6 |
| 混沌测试 | 故障注入 | Chaos Monkey |

### 🟢 锦上添花

| 项目 | 说明 | 优先级 |
|------|------|--------|
| API 版本管理 | `/api/v1/`, `/api/v2/` 共存 | 低 |
| 数据库迁移 | Alembic 版本管理 | 中 |
| 灰度发布 | 新版本只给部分用户 | 低 |
| 多环境管理 | dev / staging / prod | 中 |
| 文档自动化 | API 文档自动生成 | 低（FastAPI 已有） |

---

## 架构优化方向

### 1. 分层架构 (Layered Architecture)

**当前问题**：服务内部代码组织较扁平

**优化方向**：

```
service/
├── api/                 # 接口层 (Interface Layer)
│   ├── routes.py        # HTTP 路由
│   └── schemas.py       # 请求/响应模型
│
├── application/         # 应用层 (Application Layer)
│   ├── services.py      # 业务编排、用例实现
│   └── dto.py           # 数据传输对象
│
├── domain/              # 领域层 (Domain Layer)
│   ├── entities.py      # 领域实体
│   ├── value_objects.py # 值对象
│   ├── repositories.py  # 仓储接口（抽象）
│   └── services.py      # 领域服务
│
├── infrastructure/      # 基础设施层 (Infrastructure Layer)
│   ├── database.py      # 数据库连接
│   ├── repositories.py  # 仓储实现
│   ├── external_api.py  # 外部 API 调用
│   └── messaging.py     # 消息队列
│
└── main.py              # 启动入口
```

**依赖方向**：

```
API → Application → Domain ← Infrastructure
                      ↑
              依赖倒置原则
```

### 2. 六边形架构 (Hexagonal Architecture)

**核心思想**：业务逻辑与外部系统解耦

```
                    ┌─────────────────┐
                    │   HTTP API      │  ← 主适配器 (Driving Adapter)
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        │                    ▼                    │
        │           ┌─────────────────┐           │
        │           │                 │           │
 CLI ───┼──────────▶│   Application   │◀──────────┼─── gRPC
        │           │      Core       │           │
        │           │                 │           │
        │           └────────┬────────┘           │
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Database    │   │  Message Queue │   │  External API │
└───────────────┘   └───────────────┘   └───────────────┘
                    ↑ 次适配器 (Driven Adapter)
```

**好处**：
- 可以轻松替换数据库、消息队列
- 方便单元测试（Mock 外部依赖）
- 业务逻辑不受技术选型影响

### 3. 领域驱动设计 (DDD)

**适用场景**：业务复杂的服务（如 paper-storage-service）

**划分边界上下文**：

```
┌─────────────────────────────────────────────────────────────┐
│                    ResearchGO 领域                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│  用户上下文     │  论文上下文      │  对话上下文             │
│  (User Context) │  (Paper Context) │  (Conversation Context) │
├─────────────────┼─────────────────┼─────────────────────────┤
│ - User          │ - Paper         │ - Conversation          │
│ - Credential    │ - PaperMetadata │ - Message               │
│ - Session       │ - Citation      │ - Context               │
│                 │ - Vector        │ - Summary               │
└─────────────────┴─────────────────┴─────────────────────────┘
```

**聚合根设计示例**：

```python
# domain/aggregates/paper.py

class Paper:
    """论文聚合根"""
    
    def __init__(self, paper_id: PaperId, title: str, owner: UserId):
        self.id = paper_id
        self.title = title
        self.owner = owner
        self.metadata = PaperMetadata()
        self.vectors = []
        self._events = []
    
    def upload_content(self, content: bytes) -> None:
        """上传论文内容"""
        self.metadata.update_size(len(content))
        self._events.append(PaperUploadedEvent(self.id))
    
    def index_vectors(self, vectors: List[Vector]) -> None:
        """索引向量"""
        self.vectors = vectors
        self._events.append(PaperIndexedEvent(self.id))
    
    @property
    def domain_events(self) -> List[DomainEvent]:
        return self._events
```

### 4. 事件驱动架构 (EDA)

**当前问题**：服务间同步调用，耦合度高

**优化方向**：

```
┌─────────────────┐         ┌─────────────────┐
│ paper-service   │         │ vector-service  │
│                 │         │                 │
│  上传论文       │         │  索引向量       │
│       │         │         │       ▲         │
│       ▼         │         │       │         │
│  发布事件 ──────┼────────▶│  订阅事件       │
│ PaperUploaded   │         │                 │
└─────────────────┘         └─────────────────┘
                  │
                  ▼
           ┌─────────────┐
           │  RabbitMQ   │
           │  Event Bus  │
           └─────────────┘
```

**事件定义**：

```python
# 领域事件
class PaperUploadedEvent:
    paper_id: str
    user_id: str
    object_name: str
    timestamp: datetime

class PaperIndexedEvent:
    paper_id: str
    vector_count: int
    timestamp: datetime

class PaperAnalyzedEvent:
    paper_id: str
    summary: str
    timestamp: datetime
```

**好处**：
- 服务解耦，独立部署
- 异步处理，提高响应速度
- 天然支持事件溯源

### 5. CQRS 模式

**适用场景**：读写负载不均衡的服务

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌─────────────────┐           ┌─────────────────┐
     │  Command Side   │           │   Query Side    │
     │  (写操作)        │           │   (读操作)       │
     ├─────────────────┤           ├─────────────────┤
     │ - 上传论文       │           │ - 搜索论文       │
     │ - 更新元数据     │           │ - 获取列表       │
     │ - 删除论文       │           │ - 获取详情       │
     └────────┬────────┘           └────────┬────────┘
              │                             │
              ▼                             ▼
     ┌─────────────────┐           ┌─────────────────┐
     │  Write Model    │           │   Read Model    │
     │  (MySQL)        │──同步───▶│  (Elasticsearch) │
     └─────────────────┘           └─────────────────┘
```

### 6. 服务网格 (Service Mesh)

**适用场景**：服务数量多，需要统一管理服务间通信

```
┌─────────────────────────────────────────────────────────────┐
│                      Control Plane                          │
│                        (Istio)                              │
└─────────────────────────────┬───────────────────────────────┘
                              │ 配置下发
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│┌─────────────┐│   │┌─────────────┐│   │┌─────────────┐│
││   Sidecar   ││   ││   Sidecar   ││   ││   Sidecar   ││
││   (Envoy)   ││   ││   (Envoy)   ││   ││   (Envoy)   ││
│└──────┬──────┘│   │└──────┬──────┘│   │└──────┬──────┘│
│       │       │   │       │       │   │       │       │
│┌──────▼──────┐│   │┌──────▼──────┐│   │┌──────▼──────┐│
││ auth-service││   ││ chat-service││   ││paper-service││
│└─────────────┘│   │└─────────────┘│   │└─────────────┘│
└───────────────┘   └───────────────┘   └───────────────┘
```

**提供能力**：
- mTLS（服务间加密通信）
- 流量管理（灰度发布、故障注入）
- 可观测性（自动追踪、指标采集）

**注意**：Service Mesh 复杂度高，建议服务数量 > 20 时再考虑

---

## 演进路线图

### Phase 1：可观测性基础（1-2 周）

```
优先级：P0
目标：服务状态可感知
```

| 任务 | 工具 | 产出 |
|------|------|------|
| 统一日志格式 | structlog | JSON 格式日志 |
| 日志收集 | Loki + Promtail | 集中式日志查询 |
| 指标暴露 | prometheus-fastapi-instrumentator | /metrics 端点 |
| 监控面板 | Grafana | 服务健康大盘 |
| 基础告警 | AlertManager | 服务不可用告警 |

### Phase 2：服务韧性（2-3 周）

```
优先级：P1
目标：服务故障不影响整体
```

| 任务 | 工具 | 产出 |
|------|------|------|
| 熔断器 | circuitbreaker | 故障隔离 |
| 重试机制 | tenacity | 瞬时故障自动恢复 |
| 超时控制 | httpx timeout | 避免无限等待 |
| 限流 | Traefik RateLimit | 流量保护 |
| 健康检查 | /health, /ready | 自动故障发现 |

### Phase 3：CI/CD（2-3 周）

```
优先级：P2
目标：自动化交付
```

| 任务 | 工具 | 产出 |
|------|------|------|
| 代码检查 | pre-commit, ruff | 代码质量保障 |
| 单元测试 | pytest | 覆盖率 > 70% |
| 镜像构建 | GitHub Actions | 自动构建 |
| 部署流水线 | GitHub Actions | 一键部署 |
| 服务 Dockerfile | Docker | 服务容器化 |

### Phase 4：架构优化（4-6 周）

```
优先级：P3
目标：代码质量、可维护性
```

| 任务 | 范围 | 产出 |
|------|------|------|
| 分层架构重构 | 全部服务 | 清晰的代码结构 |
| 领域建模 | paper-service | DDD 实践 |
| 事件驱动改造 | paper → vector | 异步解耦 |
| 配置中心 | 全部服务 | 统一配置管理 |

### Phase 5：高级特性（长期）

```
优先级：P4
目标：生产级能力
```

| 任务 | 说明 |
|------|------|
| 分布式追踪 | 请求链路追踪 |
| 服务发现 | 动态服务注册 |
| 契约测试 | API 兼容性保障 |
| 灰度发布 | 渐进式发布 |
| 服务网格 | Istio（可选） |

---

## 完成度评估

```
当前完成度：50%

基础设施     [████████████████████] 100%
服务拆分     [████████████████████] 100%
API 网关     [████████████████████] 100%
可观测性     [░░░░░░░░░░░░░░░░░░░░]   0%
服务治理     [████░░░░░░░░░░░░░░░░]  20%
CI/CD        [░░░░░░░░░░░░░░░░░░░░]   0%
安全加固     [████░░░░░░░░░░░░░░░░]  20%
架构优化     [██░░░░░░░░░░░░░░░░░░]  10%

综合评估     [██████████░░░░░░░░░░]  50%
```

---

## 参考资源

### 书籍
- 《微服务架构设计模式》- Chris Richardson
- 《领域驱动设计》- Eric Evans
- 《凤凰架构》- 周志明

### 工具文档
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Jaeger](https://www.jaegertracing.io/docs/)
- [Traefik](https://doc.traefik.io/traefik/)

### 实践指南
- [12-Factor App](https://12factor.net/zh_cn/)
- [Microsoft 微服务指南](https://docs.microsoft.com/zh-cn/azure/architecture/microservices/)
- [Martin Fowler - Microservices](https://martinfowler.com/articles/microservices.html)

