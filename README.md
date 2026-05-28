# 等锅叫号

适用于麻辣烫、串串、冒菜、炸串等现场等餐场景的多商户扫码排号叫号系统。

## 核心主流程

号码代表一次现场消费篮/餐次。顾客到店自选菜，店员发号并登记初始菜篮；顾客绑定号码后等待制作、追加备注或饮料、呼叫服务；制作端按号码制作并叫号；顾客取餐后继续占号；吃完呼叫结账；收银员汇总金额并展示门店收款二维码；确认已收到后号码完成释放。

## 项目结构

- `backend/`：Python 3.8 + FastAPI 后端。
- `merchant-admin/`：Vue 3 + Element Plus 商家/平台管理 Web。
- `customer-miniapp/`：uni-app 顾客端小程序/H5。
- `docs/superpowers/specs/`：设计文档。
- `docs/superpowers/plans/`：实施计划。

## 后端开发

```powershell
cd D:\3d\fh
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pytest backend\tests -v
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

开发默认使用 SQLite：`queue_calling.db`。生产环境可通过 `DATABASE_URL` 切换到 MySQL，表结构由 SQLAlchemy 模型和 Alembic 迁移管理。

```powershell
cd D:\3d\fh\backend
..\.venv\Scripts\python.exe -m alembic upgrade head
$env:DATABASE_URL="mysql+pymysql://queue:secret@127.0.0.1:3306/queue_calling?charset=utf8mb4"
..\.venv\Scripts\python.exe -m alembic upgrade head
```

当前后端已经包含：

- 号码餐次领域模型和状态校验。
- SQLAlchemy 持久化仓储。
- 门店队列、号码动作、门店目录、营业状态、菜品管理、平台概览接口。
- 自动发号、顾客追加、呼叫结账、待收银列表、确认收款完成释放。
- 跳号、恢复、取消、疑似未付款风险标记。
- 员工登录、Bearer token、角色拒绝和跨门店拒绝。
- 备注追加、服务呼叫、操作日志和 Alembic 初始迁移。
- 30+ 个后端测试覆盖主流程、仓储和接口契约。

## 商家后台

```powershell
cd D:\3d\fh\merchant-admin
npm install
npm run dev
npm run test:unit
```

后台会读取 `/api/stores/1/catalog` 和 `/api/stores/1/queue`，接口不可用时保留样例数据展示。

当前后台已接入：

- 新增号码。
- 队列状态推进。
- 队列详情抽屉，展示人数、备注、登记内容、金额和收款信息。
- 跳号、恢复、取消、疑似未付款风险标记。
- 制作工作台（`/production`）：按待制作、制作中、已叫号、已跳号分列，备注高亮，大按钮推进厨房动作。
- 待结账收银确认。
- 营业状态切换。
- 门店/员工/规则配置。
- 平台管理后台。
- 大屏叫号。
- 数据统计。
- 菜品新增和上下架切换。

## 顾客端

```powershell
cd D:\3d\fh\customer-miniapp
npm install
npm run dev:h5
```

顾客端会读取门店目录，并支持通过 H5 query 或小程序页面参数绑定号码，例如：

```text
http://localhost:5173/?store_id=1&number=A001
```

也可以在页面内输入店员给出的号码绑定。绑定时会校验门店、号码和已完成/已取消状态。

当前顾客端已接入：

- 扫码参数或输入号码绑定。
- 展示已登记内容和可追加菜品。
- 点击菜品追加到当前号码。
- 追加口味备注，并在已收款、已完成、已取消等状态下阻止继续追加。
- 呼叫服务生成待处理服务事件。
- 呼叫结账进入待收银，重复呼叫时显示等待店员核算。

## 平台管理与展示

```powershell
cd D:\3d\fh\merchant-admin
npm install
npm run dev
```

后台当前已包含：

- 首页经营概览
- 队列管理和详情抽屉
- 制作工作台
- 收银工作台
- 门店/员工/规则配置
- 平台管理后台
- 大屏叫号
- 数据统计

## 部署与环境

### 本地一键启动顺序

1. 启动后端：

```powershell
cd D:\3d\fh
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

2. 启动商家后台：

```powershell
cd D:\3d\fh\merchant-admin
npm run dev
```

3. 启动顾客端：

```powershell
cd D:\3d\fh\customer-miniapp
npm run dev:h5
```

### 环境变量

- `DATABASE_URL`：生产数据库连接串，默认本地 SQLite。
- `API_BASE`：前端请求前缀，当前默认空字符串直连同域 API。
- `VITE_*`：如果后续前端拆成多环境，可继续扩展。

### 上线前检查

- 后端迁移已执行到最新版本。
- `backend/tests` 通过。
- `merchant-admin` 和 `customer-miniapp` 构建通过。
- 门店、员工、平台、统计和大屏页面已在路由中可达。

## API 文档

见 [docs/api.md](docs/api.md)。
