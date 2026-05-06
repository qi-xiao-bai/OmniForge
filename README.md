# OmniForge

**多模态 AI 内容创作引擎** — 基于 Xiaomi MiMo-V2.5 系列大模型的多 Agent 协作编排框架

## 核心特性

- **多 Agent 协作编排**: 5 个专业 Agent（创意理解、内容规划、多模态生成、质量评估）自主协作
- **全模态内容生成**: 支持文本、图像、语音合成三大模态的并行生成
- **智能质量评估**: 判别器机制驱动的迭代优化，确保输出质量
- **DAG 工作流引擎**: 可视化任务编排，支持复杂创作流程的自动化执行
- **上下文感知一致性**: 利用 MiMo 长上下文推理能力，确保跨模态内容在情感、风格上高度统一

## 快速开始

### 前置要求

- Python 3.11+
- Xiaomi MiMo API Key

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/OmniForge.git
cd OmniForge

pip install -r requirements.txt
```

### 配置

```bash
export MIMO_API_KEY="your-api-key-here"
export MIMO_BASE_URL="https://api.mimomimo.com/v1"
```

### 运行

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 文档: http://localhost:8000/docs

### Docker 部署

```bash
docker-compose up --build
```

## 技术架构

```
用户输入 → 创意理解 Agent (MiMo-V2.5 推理模型)
         → 内容规划 Agent (MiMo-V2.5 推理模型)
         → 多模态生成 Agent 集群
           ├─ 文本创作 Agent (MiMo-V2.5 文本模型)
           ├─ 图像生成 Agent (MiMo 多模态模型)
           └─ 语音合成 Agent (MiMo 语音合成模型)
         → 质量评估 Agent (MiMo-V2.5 推理模型)
         → 自动化后处理管道
```

## API 示例

### 创建内容创作任务

```bash
curl -X POST http://localhost:8000/api/v1/creative \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "为一档科技产品评测节目创作一期关于最新折叠屏手机的视频内容",
    "content_type": "short_video",
    "style": "professional"
  }'
```

### 查询任务状态

```bash
curl http://localhost:8000/api/v1/task/{task_id}
```

## 系统要求

| 组件 | 最低要求 |
|------|----------|
| CPU | 2 核 |
| 内存 | 4 GB |
| Python | 3.11+ |
| 网络 | 可访问 MiMo API |

## 项目结构

```
OmniForge/
├── src/
│   ├── main.py                 # FastAPI 应用入口
│   ├── agents/                  # Agent 实现
│   │   ├── base.py              # Agent 基类
│   │   ├── coordinator.py       # 协作编排器
│   │   ├── creative_agent.py    # 创意理解
│   │   ├── planner_agent.py     # 内容规划
│   │   ├── generator_agents.py  # 多模态生成
│   │   └── evaluator_agent.py   # 质量评估
│   ├── core/                    # 核心模块
│   │   ├── mimo_client.py       # MiMo API 客户端
│   │   ├── message_bus.py       # 消息总线
│   │   └── workflow_engine.py   # DAG 工作流
│   ├── api/                     # API 层
│   │   ├── routes.py            # 路由定义
│   │   └── schemas.py           # 数据模型
│   └── services/                # 业务服务
├── tests/                       # 测试套件
├── docs/                        # 架构文档
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT