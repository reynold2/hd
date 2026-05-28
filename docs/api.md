# 等锅叫号 API 草案

## 健康检查

- `GET /health`

返回：

```json
{"status": "ok"}
```

## 门店目录

- `GET /api/stores/{store_id}/catalog`

返回门店基础信息、菜品展示、员工、排号规则。开发库为空时会自动生成默认门店、菜品和员工。

## 鉴权

- `POST /api/auth/login`

员工 PIN 登录。当前开发种子员工默认 PIN 为 `0000`，返回 Bearer token 和员工上下文。

```json
{
  "store_id": 1,
  "staff_name": "李店长",
  "pin": "0000"
}
```

返回：

```json
{
  "token": "base64payload.signature",
  "staff": {
    "id": 2,
    "store_id": 1,
    "name": "李店长",
    "role": "manager",
    "status": "active"
  }
}
```

商家后台写操作需要请求头：

```http
Authorization: Bearer <token>
```

当前已校验：

- 发号：`boss`、`manager`，且只能访问员工所属门店。
- 制作、叫号、取餐、跳号、恢复：`boss`、`manager`、`cook`，且只能操作员工所属门店号码。
- 取消号码：`boss`、`manager`，且只能操作员工所属门店号码。
- 标记未付款风险：`boss`、`manager`、`cashier`，且只能操作员工所属门店号码。
- 营业状态、菜品新增和编辑：`boss`、`manager`，且只能访问或编辑员工所属门店数据。
- 收银确认、完成释放：`boss`、`manager`、`cashier`，且只能访问员工所属门店。
- 服务呼叫处理：`boss`、`manager`、`cashier`、`cook`，且只能处理员工所属门店呼叫。

- `PATCH /api/stores/{store_id}/business-status`

```json
{
  "business_status": "paused"
}
```

`business_status` 可选：`open`、`paused`、`closed`。

## 菜品

- `POST /api/stores/{store_id}/dishes`

```json
{
  "name": "酸梅汤",
  "category": "饮品",
  "price": "8.00",
  "available": true
}
```

- `PATCH /api/dishes/{dish_id}`

```json
{
  "available": false,
  "price": "7.00"
}
```

## 队列

- `GET /api/stores/{store_id}/queue`

返回门店未完成号码餐次，不包含已完成和已取消。

- `POST /api/stores/{store_id}/queue/issue`

店员或接待现场发号。号码按门店前缀自动生成，如 `A001`。

```json
{
  "people_count": 2,
  "remark": "少辣，不要葱"
}
```

## 收银

- `GET /api/stores/{store_id}/cashier/pending`

返回已呼叫结账、等待收银确认的号码餐次。

## 号码餐次

- `POST /api/meal-sessions`

```json
{
  "store_id": 1,
  "number": "A018",
  "people_count": 2,
  "remark": "少辣，不要葱"
}
```

- `GET /api/meal-sessions/{number}`
- `POST /api/meal-sessions/{number}/items`

```json
{
  "name": "可乐",
  "amount": "5.00",
  "source": "customer",
  "quantity": 2,
  "note": ""
}
```

- `POST /api/meal-sessions/{number}/remarks`

顾客、店员或收银员在未关闭号码上追加备注。追加后会保留原备注，并按 `source: 内容` 换行追加。

```json
{
  "remark": "加麻加汤",
  "source": "customer"
}
```

- `POST /api/meal-sessions/{number}/service-calls`

顾客或店员在未关闭号码上发起服务呼叫。

```json
{
  "message": "麻烦加一份蘸料",
  "source": "customer"
}
```

## 状态动作

- `POST /api/meal-sessions/{number}/actions/start-preparing`
- `POST /api/meal-sessions/{number}/actions/call`
- `POST /api/meal-sessions/{number}/actions/mark-dining`
- `POST /api/meal-sessions/{number}/actions/request-checkout`
- `POST /api/meal-sessions/{number}/actions/confirm-payment`

```json
{
  "payment_method": "store_qr",
  "cashier_id": 7
}
```

- `POST /api/meal-sessions/{number}/actions/complete`
- `POST /api/meal-sessions/{number}/actions/skip`
- `POST /api/meal-sessions/{number}/actions/resume`
- `POST /api/meal-sessions/{number}/actions/cancel`
- `POST /api/meal-sessions/{number}/actions/mark-unpaid-risk`

典型现场主流程：

`issue → add item → start-preparing → call → mark-dining → customer add item → request-checkout → confirm-payment → complete`

异常和风控流程：

- `skip`：从 `occupied`、`preparing`、`called` 暂时跳过号码，状态变为 `skipped`。
- `resume`：只允许从 `skipped` 恢复，状态回到 `preparing`。
- `cancel`：取消未支付号码，状态变为 `cancelled`；已支付或已完成号码不可取消。
- `mark-unpaid-risk`：将未关闭号码标记为疑似未付款风险，状态变为 `risk_unpaid`；已支付、已完成、已取消号码不可标记。

## 服务呼叫

- `GET /api/stores/{store_id}/service-calls/pending`

返回门店待处理服务呼叫，按创建顺序排列。

- `POST /api/service-calls/{call_id}/handle`

```json
{
  "staff_id": 2,
  "resolution": "已加蘸料"
}
```

处理成功后服务呼叫状态变为 `handled`，并记录处理员工和处理说明。

## 操作日志

- `GET /api/stores/{store_id}/operation-logs`

需要 `boss` 或 `manager` 角色，并且只能查看员工所属门店。

返回门店关键员工动作日志，当前已记录：

- `queue.issue`：店长或老板现场发号。
- `payment.confirm`：老板、店长或收银员确认收款。

## 平台概览

- `GET /api/platform/overview`

返回平台招商审核、套餐和公告的基础概览数据。当前为种子数据服务。
