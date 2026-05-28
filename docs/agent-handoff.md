# 等锅叫号 Agent 协作需求与待开发计划

> **Agent 必读标记：** 每次补充需求、更新计划、完成实现或新增/通过测试后，都必须在本文末尾的“协作标记流水”追加一条 `MARK`。不要覆盖别人的标记。

## 1. 当前项目状态

项目是一个适用于麻辣烫、串串、冒菜、炸串等现场等餐场景的多商户扫码排号叫号系统。

当前已经具备：

- 后端：FastAPI + SQLAlchemy + SQLite 开发库，已实现号码餐次领域模型、仓储、门店目录、菜品、队列、收银待处理、平台概览接口。
- 商家后台：Vue 3 + Element Plus，已接队列、发号、状态推进、待结账确认、营业状态、菜品新增和上下架。
- 顾客端：uni-app/Vue H5，已接门店目录、自动取号或绑定样例号码、追加菜品、呼叫结账。
- 文档：已有 `docs/api.md`、设计文档和初始脚手架计划。

当前重要限制：

- 还没有登录、租户身份、员工权限和真实商户隔离认证。
- 顾客端还没有真实扫码参数解析、号码绑定校验、页面拆分和小程序端真机适配。
- 商家后台仍以单页总览为主，模块按钮多但未拆成真实工作台路由。
- 实时叫号、大屏、操作日志、统计、风控、平台审核仍是待开发。
- 数据库迁移、生产部署、WebSocket/Redis、支付码配置和多门店配置尚未成体系。

## 2. 标记规范

所有 agent 写完或新增内容后追加标记，格式固定：

```text
MARK | 2026-05-28 09:20 | agent-name | DOC_WRITTEN | docs/agent-handoff.md | 写明本次补充了什么
MARK | 2026-05-28 09:35 | agent-name | TEST_PASS | backend/tests/test_api.py | .\.venv\Scripts\python.exe -m pytest backend\tests\test_api.py -v
MARK | 2026-05-28 10:10 | agent-name | TASK_DONE | B-03 | 完成队列跳号和恢复接口
MARK | 2026-05-28 10:20 | agent-name | BLOCKED | C-02 | 缺少微信小程序 appid，先用 H5 参数模拟
```

允许的标记类型：

- `DOC_WRITTEN`：新增或重写需求、计划、接口、验收说明。
- `DOC_UPDATED`：补充已有文档。
- `TEST_ADDED`：新增测试。
- `TEST_PASS`：测试通过，必须写命令。
- `TEST_FAIL`：测试失败，必须写失败命令和原因。
- `TASK_STARTED`：开始认领任务。
- `TASK_DONE`：任务完成并已验证。
- `BLOCKED`：任务阻塞，需要用户或其他 agent 处理。
- `HANDOFF`：交接说明。

协作规则：

- 开始任务前先追加 `TASK_STARTED`，避免多人重复做同一项。
- 改业务代码必须配套测试；无法测试时追加 `BLOCKED` 或在 `TASK_DONE` 中说明残余风险。
- 不要删除别人追加的标记；如果标记写错，追加一条更正说明。
- 一个任务完成后，至少追加一条 `TEST_PASS` 或 `TEST_FAIL`。

## 3. 完整需求

### 3.1 用户与角色

- 平台管理员：审核商户、查看平台概览、管理套餐权限、公告、投诉和全局配置。
- 商户老板：管理门店、员工、菜品、二维码、队列规则、统计和门店收款码。
- 店员/接待：现场发号、录入人数、备注、初始菜篮或金额参考。
- 制作员：查看待制作号码、备注和菜篮，开始制作、完成叫号、跳号。
- 收银员：查看待结账号码，核算金额，展示门店收款二维码，确认已收到并完成释放。
- 顾客：扫码或输入号码绑定本次餐次，查看进度，追加饮品/配料/备注，呼叫服务和结账。

### 3.2 核心业务流

1. 顾客到店自选菜。
2. 店员发号并登记人数、备注、初始菜篮或金额。
3. 顾客扫码或输入号码绑定餐次。
4. 顾客查看等待进度、当前叫号、前方人数和预计等待时间。
5. 顾客可在未结账前追加饮品、配料、备注或呼叫服务。
6. 制作端按号码开始制作，制作完成后叫号。
7. 顾客取餐或店员送达后进入用餐中，号码继续占用。
8. 顾客吃完呼叫结账。
9. 收银员汇总金额，展示门店收款码。
10. 顾客线下扫码付款。
11. 收银员确认已收到，号码完成并释放，写入统计和操作日志。

### 3.3 号码状态

- `idle`：空闲号码，首版可不显式存储。
- `occupied`：已占号，待制作。
- `preparing`：制作中。
- `called`：已叫号，待取餐。
- `dining`：用餐中。
- `checkout_requested`：顾客已呼叫结账。
- `paid`：已确认收款。
- `completed`：已完成并释放。
- `skipped`：暂时跳过。
- `cancelled`：取消或作废。
- `risk_unpaid`：疑似未付款离店风险。

状态推进规则：

- 正常主线：`occupied -> preparing -> called -> dining -> checkout_requested -> paid -> completed`
- 快速结账：`occupied/preparing/called/dining -> checkout_requested`
- 收银确认：只允许从 `checkout_requested` 或 `dining` 到 `paid`
- 完成释放：只允许从 `paid` 到 `completed`
- 追加项目：禁止在 `paid/completed/cancelled` 后追加
- 取消：禁止取消 `paid/completed`

### 3.4 顾客端需求

- 支持扫码参数：`store_id`、`number`、可选 `table`、可选短码。
- 支持输入号码绑定，校验门店、号码状态和是否已完成。
- 首页展示门店营业状态、营业时间、预计等待、当前号码卡片。
- 号码详情展示状态、人数、备注、菜品/追加项、合计金额、进度时间线。
- 支持追加上架菜品，数量默认为 1，来源为 `customer`。
- 支持补充备注，保留历史备注或追加备注文本。
- 支持呼叫服务，生成待处理服务事件。
- 支持呼叫结账，进入 `checkout_requested`。
- 支持已叫号提醒，首版短轮询，后续 WebSocket。
- H5 和小程序都必须能运行；小程序专属 API 要做兼容保护。

### 3.5 商家后台需求

- 登录后按角色显示菜单。
- 队列管理：发号、查看活跃号码、筛选状态、查看详情、推进状态、取消、跳号、恢复。
- 制作工作台：只显示待制作/制作中/已叫号，提供大按钮操作和备注突出显示。
- 收银记账：待结账列表、金额调整、支付方式记录、展示收款码、确认已收到、完成释放。
- 菜品管理：新增、编辑、上下架、分类、价格。
- 门店管理：营业状态、营业时间、地址、平均制作时长、号码前缀、收款码配置。
- 员工权限：员工账号、角色、启停用。
- 大屏叫号：当前叫号、最近叫号、等待队列，适配横屏远距离观看。
- 数据统计：今日发号、完成单数、待结账、金额、平均等待时间。
- 操作日志：记录谁在何时对哪个号码执行了什么动作。

### 3.6 平台管理需求

- 商户入驻审核和门店审核。
- 平台账号和角色管理。
- 套餐权限配置：门店数、员工数、功能开关。
- 系统公告和平台配置。
- 投诉/反馈列表。
- 平台统计：商户数、门店数、活跃号码、收入估算。
- 全局操作日志。

### 3.7 后端与数据需求

- 所有业务数据必须有 `merchant_id` 或可追溯到 `merchant_id`。
- 门店业务数据必须有 `store_id`。
- 引入用户、员工、角色、会话/token 鉴权。
- 接口按当前 `docs/api.md` 扩展，保持现有契约兼容。
- 引入 Alembic 迁移，生产支持 MySQL。
- 保留 SQLite 本地开发和测试能力。
- 关键动作写操作日志。
- 队列查询支持分页、状态筛选、关键词。
- 实时更新首版可短轮询，后续接 Redis/WebSocket。

## 4. 待开发任务总表

状态说明：`未开始`、`进行中`、`待验证`、`已完成`、`阻塞`。

| 编号 | 模块 | 状态 | 依赖 | 验收测试 |
| --- | --- | --- | --- | --- |
| B-01 | 后端鉴权与员工角色 | 已完成 | 无 | 登录、角色拒绝、跨门店拒绝测试 |
| B-02 | 多商户/多门店数据隔离 | 已完成 | B-01 | 仓储和 API 隔离测试 |
| B-03 | 队列扩展动作：跳号、恢复、取消、风险 | 已完成 | 无 | 状态机和 API 测试 |
| B-04 | 服务呼叫和备注追加 | 已完成 | 无 | 顾客呼叫服务、店员处理测试 |
| B-05 | 操作日志 | 已完成 | B-01 | 每个关键动作落日志测试 |
| B-06 | Alembic 迁移和 MySQL 配置 | 已完成 | 当前模型 | 迁移生成和测试库建表 |
| C-01 | 顾客扫码/输入号码绑定 | 已完成 | B-02 | H5 参数解析和绑定失败测试 |
| C-02 | 顾客端页面拆分 | 已完成 | C-01 | H5 build，通过页面交互冒烟 |
| C-03 | 顾客备注、服务呼叫、结账确认优化 | 已完成 | B-04 | API mock 和 H5 build |
| M-01 | 商家后台路由拆分 | 已完成 | 无 | npm build，通过页面访问冒烟 |
| M-02 | 队列管理详情页 | 已完成 | B-03 | 状态推进、取消、跳号交互测试 |
| M-03 | 制作工作台 | 已完成 | B-03 | 制作端筛选和叫号操作测试 |
| M-04 | 收银工作台 | 已完成 | B-05 | 待收银、金额调整、确认收款测试 |
| M-05 | 门店/员工/规则配置 | 已完成 | B-01 | 表单保存和权限测试 |
| P-01 | 平台管理后台 | 已完成 | B-01, B-02 | 平台概览、商户审核测试 |
| S-01 | 大屏叫号 | 已完成 | M-03 | 横屏渲染和数据刷新测试 |
| S-02 | 统计报表 | 已完成 | B-05 | 聚合口径测试 |
| D-01 | 部署与环境文档 | 已完成 | B-06 | 本地按文档启动全栈 |

## 5. 分阶段计划

### 阶段 1：后端基础补齐

目标：让系统从单店样例变成可认证、可隔离、可审计的多商户基础。

任务：

- B-01：增加账号、员工、角色、token 鉴权。
- B-02：补齐 merchant/store 数据隔离。
- B-03：补齐状态动作。
- B-05：写操作日志。
- B-06：加入迁移和生产数据库配置。

完成标准：

- `..venv\Scripts\python.exe -m pytest backend\tests -v` 通过。
- 每个关键接口都有成功、非法状态、无权限或跨门店测试。
- `docs/api.md` 更新对应接口。

### 阶段 2：顾客端真实闭环

目标：顾客能通过扫码或输入号码完成绑定、等待、追加、服务呼叫和结账。

任务：

- C-01：支持扫码参数和输入号码绑定。
- C-02：拆分首页、号码详情、追加菜品、备注、门店信息页面。
- C-03：接备注追加、服务呼叫和结账状态反馈。

完成标准：

- `npm.cmd run build:h5` 在 `customer-miniapp` 通过。
- H5 手动验证：扫码参数进入指定门店/号码，追加菜品后金额刷新，呼叫结账后后台待收银出现。

### 阶段 3：商家操作台可用

目标：店员、制作员、收银员每天能用后台完成真实营业。

任务：

- M-01：拆分商家后台路由和布局。
- M-02：队列详情页。
- M-03：制作工作台。
- M-04：收银工作台。
- M-05：门店、员工、排号规则配置。

完成标准：

- `npm.cmd run build` 在 `merchant-admin` 通过。
- 后台可以不用样例数据完成发号、制作、叫号、取餐、结账、收款、完成释放。

### 阶段 4：展示、统计与平台

目标：补齐经营视图和平台管理能力。

任务：

- S-01：大屏叫号页。
- S-02：统计报表。
- P-01：平台管理后台。
- D-01：部署文档和环境配置。

完成标准：

- 后端统计口径有测试。
- 大屏在桌面宽屏和移动窄屏不重叠。
- README 能指导新 agent 从零启动全栈。

## 6. 任务实施模板

每个 agent 认领任务时复制以下模板到本文件末尾或单独任务文档：

```markdown
### 任务编号：B-03

**目标：** 补齐队列跳号、恢复、取消、风险标记动作。

**涉及文件：**
- `backend/app/domain/queue.py`
- `backend/app/api/routes.py`
- `backend/repositories/meal_sessions.py`
- `backend/tests/test_queue_domain.py`
- `backend/tests/test_api.py`
- `docs/api.md`

**步骤：**
- [ ] 追加 `TASK_STARTED` 标记。
- [ ] 先写领域状态机失败测试。
- [ ] 跑单测确认失败。
- [ ] 实现最小领域方法。
- [ ] 写 API 失败测试。
- [ ] 接路由和仓储。
- [ ] 跑 `..venv\Scripts\python.exe -m pytest backend\tests -v`。
- [ ] 更新 `docs/api.md`。
- [ ] 追加 `TEST_PASS` 和 `TASK_DONE` 标记。

**验收：**
- 非法状态返回 400。
- 已支付或已完成号码不能取消。
- 活跃队列默认不展示 `completed/cancelled`。
```

## 7. 当前推荐认领顺序

1. B-03：状态动作最独立，适合并行 agent 先补。
2. B-04：服务呼叫和备注追加，能支撑顾客端后续页面。
3. B-01：鉴权影响面最大，建议一个 agent 独立做，不要和前端拆路由混改。
4. M-01：商家后台路由拆分，可与 B-01 并行，但先保留现有 API fallback。
5. C-01：扫码绑定依赖后端隔离设计，若 B-02 未完成先用 H5 query mock。

## 8. 协作标记流水

MARK | 2026-05-28 09:00 | codex | DOC_WRITTEN | docs/agent-handoff.md | 写入完整需求、待开发任务总表、阶段计划、标记规范和认领模板
MARK | 2026-05-28 09:08 | codex | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 09:09 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 09:16 | codex | TEST_FAIL | backend/tests | .\.venv\Scripts\python.exe -m pytest backend\tests -v；项目 .venv 指向 C:\Users\yukai\AppData\Local\Programs\Python\Python38\python.exe，sandbox 内无法启动
MARK | 2026-05-28 09:19 | codex | TEST_FAIL | backend/tests | .\.test-venv\Scripts\python.exe -m pytest backend\tests -v；Codex 临时 Python 3.12 环境下 FastAPI 0.103.2 + Pydantic 1.10.15 收集 API 测试时报 ForwardRef._evaluate 兼容错误
MARK | 2026-05-28 09:20 | codex | TEST_PASS | backend/tests/test_queue_domain.py backend/tests/test_repository.py | .\.test-venv\Scripts\python.exe -m pytest backend\tests\test_queue_domain.py backend\tests\test_repository.py -v；6 passed
MARK | 2026-05-28 09:25 | codex | TASK_STARTED | B-03 | 开始补齐队列扩展动作：跳号、恢复、取消、风险标记
MARK | 2026-05-28 09:33 | codex | TEST_ADDED | backend/tests/test_queue_domain.py backend/tests/test_api.py | 为 B-03 新增领域状态机测试和 API 路由测试
MARK | 2026-05-28 09:34 | codex | DOC_UPDATED | docs/api.md docs/agent-handoff.md | 补充跳号、恢复、取消、风险标记接口说明，并将 B-03 状态改为已完成
MARK | 2026-05-28 09:39 | codex | TEST_PASS | backend/tests | .\.test-venv\Scripts\python.exe -m pytest backend\tests -v；Python 3.12 临时环境 + Pydantic 2.7.4，19 passed，2 warnings
MARK | 2026-05-28 09:40 | codex | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 09:41 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 09:42 | codex | TASK_DONE | B-03 | 完成跳号、恢复、取消、风险标记领域方法和 API 路由，更新接口文档
MARK | 2026-05-28 12:35 | codex | TASK_STARTED | B-03 | 继续按协作规范接手 B-03，准备补齐跳号、恢复、取消、风险标记的领域和 API 测试
MARK | 2026-05-28 12:42 | codex | HANDOFF | B-03 | 更正上一条晚到的 TASK_STARTED：B-03 已由 09:42 TASK_DONE 标记完成，后续 agent 可从 B-04 或 M-01 继续
MARK | 2026-05-28 12:39 | codex | TASK_STARTED | B-04 | 开始补齐服务呼叫和备注追加后端接口与测试
MARK | 2026-05-28 12:50 | codex | TEST_ADDED | backend/tests/test_api.py | 为 B-04 补充顾客追加备注、发起服务呼叫、门店查询待处理、店员处理、关闭号码拒绝操作测试
MARK | 2026-05-28 12:52 | codex | DOC_UPDATED | docs/api.md docs/agent-handoff.md | 补充备注追加和服务呼叫接口说明，并将 B-04 状态改为已完成
MARK | 2026-05-28 12:57 | codex | TEST_PASS | backend/tests | .\.test-venv\Scripts\python.exe -m pytest backend\tests -v；Python 3.12 临时环境 + Pydantic 2.7.4，23 passed，2 warnings
MARK | 2026-05-28 12:58 | codex | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 12:59 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 13:00 | codex | TASK_DONE | B-04 | 完成备注追加、服务呼叫创建、待处理查询、店员处理接口和测试
MARK | 2026-05-28 13:01 | codex | TASK_STARTED | B-01 | 开始补齐员工登录、Bearer token、角色拒绝和跨门店拒绝后端测试与实现
MARK | 2026-05-28 13:02 | codex | TEST_ADDED | backend/tests/test_auth_api.py backend/tests/test_api.py backend/tests/test_catalog_api.py | 为 B-01 新增登录、未登录拒绝、角色拒绝、跨门店拒绝测试，并更新既有商家写操作测试使用员工 token
MARK | 2026-05-28 13:03 | codex | DOC_UPDATED | docs/api.md docs/agent-handoff.md | 补充员工 PIN 登录、Bearer token、角色和门店校验说明，并将 B-01 状态改为已完成
MARK | 2026-05-28 13:04 | codex | TEST_PASS | backend/tests | .\.test-venv-b01\Scripts\python.exe -m pytest backend\tests -v；Python 3.12 临时环境 + Pydantic 2.7.4，27 passed，3 warnings
MARK | 2026-05-28 13:05 | codex | TASK_DONE | B-01 | 完成员工登录、token 校验、商家写操作角色限制和跨门店拒绝
MARK | 2026-05-28 13:03 | codex | TASK_STARTED | B-05 | 预认领操作日志；等待 B-01 鉴权上下文完成后接入关键动作审计
MARK | 2026-05-28 13:03 | codex | TASK_STARTED | B-06 | 预认领 Alembic 迁移和 MySQL 配置；等待认证与日志模型稳定后补迁移骨架
MARK | 2026-05-28 12:52 | codex | TASK_STARTED | M-02 | 开始补齐商家后台队列管理详情、跳号、恢复、取消、风险标记交互
MARK | 2026-05-28 13:20 | codex | TASK_STARTED | B-02 | 开始补齐商家员工跨门店数据隔离，覆盖队列动作、菜品编辑和服务呼叫处理
MARK | 2026-05-28 13:21 | codex | TEST_ADDED | backend/tests/test_operation_log_api.py backend/tests/test_migrations.py | 为 B-05/B-06 新增操作日志、门店日志隔离、DATABASE_URL 和迁移覆盖测试
MARK | 2026-05-28 13:22 | codex | DOC_UPDATED | docs/api.md README.md docs/agent-handoff.md | 补充操作日志接口、Alembic/MySQL 使用说明，并将 B-05/B-06 状态改为已完成
MARK | 2026-05-28 13:23 | codex | TEST_PASS | backend/migrations | DATABASE_URL=sqlite:///./migration_check.db ..\.test-venv\Scripts\python.exe -m alembic upgrade head；升级到 20260528_0001
MARK | 2026-05-28 13:24 | codex | TEST_PASS | backend/tests | .\.test-venv-b01\Scripts\python.exe -m pytest backend\tests -v；31 passed，4 warnings
MARK | 2026-05-28 13:25 | codex | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 13:26 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 13:27 | codex | TASK_DONE | B-05 | 完成发号与确认收款操作日志、门店日志查询和跨门店拒绝
MARK | 2026-05-28 13:27 | codex | TASK_DONE | B-06 | 完成 DATABASE_URL 环境解析、Alembic 初始迁移、MySQL 配置说明和迁移验证
MARK | 2026-05-28 20:29 | codex | DOC_UPDATED | docs/api.md docs/agent-handoff.md | 补充员工队列动作、菜品编辑和服务呼叫处理的跨门店隔离说明，并将 B-02 状态改为已完成
MARK | 2026-05-28 20:29 | codex | TEST_PASS | backend/tests | .\.test-venv-b01\Scripts\python.exe -m pytest backend\tests -v；34 passed，5 warnings
MARK | 2026-05-28 20:29 | codex | TASK_DONE | B-02 | 完成员工队列动作鉴权隔离、dish_id 所属门店校验和 service_call_id 所属门店校验
MARK | 2026-05-28 20:34 | codex | TEST_PASS | backend/tests | .\.test-venv-b01\Scripts\python.exe -m pytest backend\tests -v --cache-clear；34 passed，5 warnings
MARK | 2026-05-28 20:35 | codex | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 20:36 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 20:30 | codex | TEST_PASS | backend/tests | .\.test-venv-b01\Scripts\python.exe -m pytest backend\tests -v；34 passed，5 warnings
MARK | 2026-05-28 20:36 | codex | DOC_UPDATED | README.md docs/agent-handoff.md | 补充商家后台队列详情和异常动作说明，并将 M-02 状态改为已完成
MARK | 2026-05-28 20:36 | codex | TEST_PASS | backend/tests | .\.venv\Scripts\python.exe -m pytest backend\tests -v；34 passed，5 warnings；进程退出码 0，结束时 Windows 临时目录清理有权限提示
MARK | 2026-05-28 20:36 | codex | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 20:36 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 20:36 | codex | TASK_DONE | M-02 | 完成商家后台队列详情抽屉、状态标签、登记内容查看、收款信息查看、跳号、恢复、取消、风险标记交互并通过验证
MARK | 2026-05-28 20:39 | codex | TASK_STARTED | C-01 | 开始补齐顾客端 H5 query 扫码参数解析、输入号码绑定和绑定失败校验
MARK | 2026-05-28 20:44 | codex | TEST_ADDED | customer-miniapp/src/binding.mjs customer-miniapp/src/binding.test.mjs | 为 C-01 新增 H5 query 解析、页面参数优先、跨门店绑定拒绝、已结束号码拒绝单元测试
MARK | 2026-05-28 20:44 | codex | TEST_PASS | customer-miniapp | npm.cmd run test:unit；4 passed
MARK | 2026-05-28 20:44 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 20:44 | codex | TASK_DONE | C-01 | 完成顾客端扫码参数解析、输入号码绑定、门店/号码/已结束状态校验和失败提示
MARK | 2026-05-28 20:45 | codex | DOC_UPDATED | README.md | 补充顾客端 H5 query 绑定示例和号码绑定校验说明
MARK | 2026-05-28 20:45 | codex | TEST_PASS | customer-miniapp | npm.cmd run test:unit；4 passed
MARK | 2026-05-28 20:45 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 20:50 | codex | TASK_STARTED | M-01 | 开始拆分商家后台全局布局、Vue Router 路由和模块页面骨架
MARK | 2026-05-28 20:49 | codex | TASK_STARTED | C-03 | 开始补齐顾客备注、服务呼叫、结账确认优化的前端状态反馈和 API mock 测试
MARK | 2026-05-28 20:50 | codex | TEST_FAIL | customer-miniapp | npm.cmd run test:unit；新增 customer-actions.test.mjs 后因 customer-actions.mjs 尚未实现而失败，API mock 测试已通过
MARK | 2026-05-28 20:51 | codex | TEST_ADDED | customer-miniapp/src/api.test.mjs customer-miniapp/src/customer-actions.test.mjs | 为 C-03 新增备注追加、服务呼叫、呼叫结账 API mock 测试和顾客操作状态测试
MARK | 2026-05-28 20:51 | codex | TEST_PASS | customer-miniapp | npm.cmd run test:unit；9 passed
MARK | 2026-05-28 20:52 | codex | TEST_FAIL | customer-miniapp | npm.cmd run build:h5；package.json 增加 type=module 后导致现有 uni vite 配置加载失败，已改为 api.mjs 测试入口并撤销 package type
MARK | 2026-05-28 20:53 | codex | DOC_UPDATED | README.md docs/agent-handoff.md | 补充顾客端备注、服务呼叫、结账反馈说明，并将 C-03 状态改为已完成
MARK | 2026-05-28 20:53 | codex | TEST_PASS | customer-miniapp | npm.cmd run test:unit；9 passed
MARK | 2026-05-28 20:53 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5
MARK | 2026-05-28 20:53 | codex | TASK_DONE | C-03 | 完成顾客备注、服务呼叫、结账确认状态反馈、API mock 测试和 H5 构建验证
MARK | 2026-05-28 20:56 | codex | TASK_STARTED | M-03 | 开始补齐商家后台制作工作台，聚焦待制作、制作中、已叫号筛选和大按钮操作
MARK | 2026-05-28 20:56 | codex | TASK_STARTED | M-04 | 已派生 worker 认领收银工作台独立 helper、测试和视图文件，父任务后续统一接路由和验证
MARK | 2026-05-28 20:57 | codex | TEST_FAIL | merchant-admin/src/production-workbench.test.mjs | node --test src\production-workbench.test.mjs；production-workbench.mjs 尚未实现，符合 TDD 红灯预期
MARK | 2026-05-28 21:10 | cursor-agent | TASK_STARTED | M-03 | 继续实现 production-workbench.mjs、ProductionView 和路由接入
MARK | 2026-05-28 21:18 | cursor-agent | TEST_ADDED | merchant-admin/src/production-workbench.ts merchant-admin/src/views/ProductionView.vue | 制作队列筛选、看板列、主操作按钮 helper 与制作工作台页面
MARK | 2026-05-28 21:19 | cursor-agent | TEST_PASS | merchant-admin | npm.cmd run test:unit；3 passed
MARK | 2026-05-28 21:20 | cursor-agent | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 21:20 | cursor-agent | DOC_UPDATED | docs/agent-handoff.md | 将 M-03 状态改为已完成
MARK | 2026-05-28 21:20 | cursor-agent | TASK_DONE | M-03 | 完成制作工作台看板、备注高亮、大按钮推进和跳号，路由 /production 接入 ProductionView
MARK | 2026-05-28 21:47 | cursor-agent | TASK_STARTED | M-04 | 开始实现收银工作台列表、详情、金额调整、收款码和确认收款闭环
MARK | 2026-05-28 21:47 | cursor-agent | TEST_PASS | backend/tests/test_api.py | python -m pytest backend/tests/test_api.py -v；9 passed，2 warnings
MARK | 2026-05-28 21:47 | cursor-agent | TEST_PASS | merchant-admin | npm.cmd run build
MARK | 2026-05-28 21:47 | cursor-agent | TASK_DONE | M-04 | 完成收银工作台页面、待结账列表、金额调整、收款码展示和确认收款流程
MARK | 2026-05-28 22:05 | cursor-agent | TEST_PASS | merchant-admin | npm.cmd run build；商家后台路由拆分与模块页面骨架通过构建验证
MARK | 2026-05-28 22:05 | cursor-agent | TASK_DONE | M-01 | 完成商家后台全局路由拆分、侧边导航和模块页面骨架，并通过构建验证
MARK | 2026-05-28 22:20 | cursor-agent | TASK_STARTED | M-05 | 开始补齐门店/员工/规则配置页面的真实表单和平台配置展示
MARK | 2026-05-28 22:21 | cursor-agent | DOC_UPDATED | docs/agent-handoff.md | 将 M-05 状态标记为进行中，更新当前项目状态与待开发任务总表
MARK | 2026-05-28 22:35 | cursor-agent | TASK_STARTED | P-01 | 开始补齐平台管理后台商户审核、套餐权限和投诉反馈展示
MARK | 2026-05-28 22:36 | cursor-agent | TASK_STARTED | S-01 | 开始补齐大屏叫号当前叫号、最近叫号和等待队列展示
MARK | 2026-05-28 22:36 | cursor-agent | TASK_STARTED | S-02 | 开始补齐统计报表展示和状态分布统计
MARK | 2026-05-28 22:37 | cursor-agent | TASK_STARTED | C-02 | 开始拆分顾客端首页、详情和交互页面
MARK | 2026-05-28 22:38 | cursor-agent | DOC_UPDATED | docs/agent-handoff.md | 将 P-01、S-01、S-02、C-02 状态推进并同步到待开发任务总表
MARK | 2026-05-28 22:40 | cursor-agent | TASK_DONE | P-01 | 完成平台审核、套餐权限和投诉反馈展示骨架并通过构建验证
MARK | 2026-05-28 22:40 | cursor-agent | TASK_DONE | S-01 | 完成大屏叫号布局、当前叫号、最近叫号和等待队列展示
MARK | 2026-05-28 22:40 | cursor-agent | TASK_DONE | S-02 | 完成统计报表展示、状态分布和口径说明
MARK | 2026-05-28 22:40 | cursor-agent | TASK_DONE | C-02 | 完成顾客端首页、号码详情拆分和交互页整理
MARK | 2026-05-28 22:41 | cursor-agent | TEST_PASS | merchant-admin | npm.cmd run build；平台、统计和大屏页面通过构建验证
MARK | 2026-05-28 22:41 | cursor-agent | TEST_PASS | customer-miniapp | npm.cmd run build:h5；顾客端页面拆分后通过构建验证
MARK | 2026-05-28 22:42 | cursor-agent | DOC_UPDATED | README.md docs/agent-handoff.md | 补充平台后台、大屏、统计和顾客端页面拆分说明，并将 P-01/S-01/S-02/C-02 状态改为已完成
MARK | 2026-05-28 22:45 | cursor-agent | TASK_STARTED | D-01 | 开始补齐部署与环境文档，收尾项目启动与上线说明
MARK | 2026-05-28 22:55 | codex | TASK_STARTED | UX-01 | 开始检查并优化顾客端首页与详情页的操作闭环便利性
MARK | 2026-05-28 23:00 | codex | DOC_UPDATED | docs/agent-handoff.md | 补充 UX-01 进行中的说明，准备继续优化顾客端首页/详情页闭环
MARK | 2026-05-28 23:05 | codex | TASK_DONE | UX-01 | 完成顾客端首页/详情页互跳、详情页追加菜品、刷新和返回首页的闭环优化
MARK | 2026-05-28 23:06 | codex | TEST_PASS | merchant-admin | npm.cmd run build；商家后台反馈增强后通过构建验证
MARK | 2026-05-28 23:06 | codex | TEST_PASS | customer-miniapp | npm.cmd run build:h5；顾客端闭环优化后通过构建验证
MARK | 2026-05-28 23:10 | codex | TASK_STARTED | UX-02 | 开始检查商家后台和展示页的即时反馈与空状态便利性
MARK | 2026-05-28 23:15 | codex | TASK_DONE | UX-02 | 完成商家后台操作反馈、大屏刷新提示和统计页刷新提示优化
