# 公开 Bot 模式说明

## ✅ 已实施方案 A：完全公开模式

你的 Telegram Bot 现在运行在**公开模式**下，任何人都可以注册并使用。

---

## 🎯 工作流程

### 新用户首次使用

```
新用户发送消息
  ↓
自动创建账户（allow=1）
  ↓
获得 5 次免费对话
  ↓
第 6 次对话被拦截
  ↓
显示订阅付费提示
  ↓
用户订阅后无限使用
```

**特点：**
- ✅ 无需等待审批
- ✅ 立即可用
- ✅ 5 次免费试用
- ✅ 用户体验流畅

---

## 👨‍💼 管理员权限

### 管理员自动识别

通过环境变量 `DEVELOPER_CHAT_ID` 识别管理员：

```bash
# .env
export DEVELOPER_CHAT_ID=123456789  # 你的 Telegram ID
```

### 管理员特权

- ✅ **无限免费使用**（绕过订阅检查）
- ✅ **永不被封禁**（即使设置 allow=0 也无效）
- ✅ **接收封禁用户的尝试通知**

---

## 🔨 管理员操作

### 封禁用户

使用 `/admin` 命令：

1. 选择用户列表（permitted/premium）
2. 选择要封禁的用户
3. 点击 [Decline] 或 [Downgrade]

**效果：**
- 用户的 `allow` 字段设为 0
- 即使用户已付费，也无法使用 bot
- 用户收到封禁提示

### 查看用户列表

`/admin` 命令提供以下列表：
- **Waiting**: 等待列表（在公开模式下应该为空）
- **Permitted**: 普通用户列表
- **Premium**: 高级用户列表（已订阅）

---

## 🔄 权限检查层级

Bot 使用**双层权限检查**：

### 第 1 层：硬性权限（check_permission）

```python
@check_permission
async def handler():
    # 检查用户是否被封禁（allow=0）
    # 管理员永远通过
    # 新用户自动创建 allow=1
```

**拦截条件：**
- ❌ 用户被管理员封禁（allow=0）

**通过条件：**
- ✅ 管理员（DEVELOPER_CHAT_ID）
- ✅ 普通用户（allow=1）
- ✅ 新用户（自动创建）

### 第 2 层：软性权限（check_subscription）

```python
@check_subscription
async def handler():
    # 检查订阅状态和免费额度
    # 管理员永远通过
```

**拦截条件：**
- ❌ 免费额度用完（free_messages_used >= 5）
- ❌ 且无活跃订阅

**通过条件：**
- ✅ 管理员
- ✅ 有活跃订阅
- ✅ 免费额度未用完

---

## 📊 用户状态示例

### 状态 1: 新用户

```
数据库记录：
- allow: 1              ✅ 自动允许
- free_messages_used: 0
- subscription_status: 'free'

行为：
- 可以发送 5 条消息
```

### 状态 2: 免费额度用完

```
数据库记录：
- allow: 1
- free_messages_used: 5
- subscription_status: 'free'

行为：
- 被拦截，显示订阅提示
```

### 状态 3: 已订阅用户

```
数据库记录：
- allow: 1
- subscription_status: 'active'
- subscription_end_date: 1234567890

行为：
- 无限使用
```

### 状态 4: 被封禁用户

```
数据库记录：
- allow: 0              ❌ 被封禁
- subscription_status: 'active'  # 即使有订阅

行为：
- 完全无法使用
- 显示封禁提示
```

### 状态 5: 管理员

```
环境变量：
DEVELOPER_CHAT_ID=123456789

行为：
- 绕过所有检查
- 无限免费使用
```

---

## 🔧 数据库字段说明

### User 表关键字段

| 字段 | 作用 | 公开模式默认值 |
|------|------|---------------|
| `allow` | 硬性权限（封禁控制） | 1（新用户自动允许） |
| `premium` | 遗留字段（已弃用） | 0 |
| `waiting` | 遗留字段（已弃用） | 0 |
| `free_messages_used` | 已使用免费次数 | 0 |
| `subscription_status` | 订阅状态 | 'free' |
| `subscription_type` | 订阅类型 | None |
| `subscription_end_date` | 订阅到期时间 | None |

---

## ⚠️ 重要注意事项

### 1. 不再有审批流程

- ❌ 删除了 `warning()` 审批函数
- ❌ 删除了 `approval_callback()` 处理器
- ✅ 新用户自动 `allow=1`

### 2. 管理员封禁仍然有效

- ✅ `/admin` 命令仍可用
- ✅ 可以设置 `allow=0` 封禁用户
- ✅ 被封禁用户无法使用（即使已付费）

### 3. Premium 字段已弃用

- 不再使用 `premium` 字段控制权限
- 改用 `subscription_status` 控制
- `/admin` 中的 Upgrade/Downgrade 仍可用，但不影响订阅

### 4. 全新数据库

- 你说不考虑现有数据库
- 首次运行会创建完整的表结构
- 包含所有订阅相关字段

---

## 🧪 测试流程

### 测试 1: 新用户自动注册

```
1. 使用一个新的 Telegram 账号
2. 向 bot 发送任意消息
3. ✅ 应该立即收到回复（无需等待审批）
```

### 测试 2: 免费额度限制

```
1. 继续发送消息（共 5 条）
2. 第 6 条消息应该被拦截
3. ✅ 显示订阅付费提示和按钮
```

### 测试 3: 管理员权限

```
1. 使用管理员账号（DEVELOPER_CHAT_ID）
2. 发送任意数量的消息
3. ✅ 永远不会被拦截
```

### 测试 4: 封禁功能

```
1. 管理员使用 /admin 命令
2. 选择一个用户并 Decline
3. 该用户尝试发送消息
4. ✅ 应该收到封禁提示
```

---

## 🚀 快速开始

### 1. 配置环境变量

```bash
# .env
export DEVELOPER_CHAT_ID=your_telegram_id
export bot_token=your_bot_token

# Stripe 配置
export STRIPE_SECRET_KEY=sk_test_xxx
export STRIPE_WEBHOOK_SECRET=whsec_xxx
export WEBHOOK_BASE_URL=https://yourdomain.com
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 终端 1: Telegram Bot
source .env && python start.py

# 终端 2: Webhook Server
source .env && python webhook_server.py
```

### 4. 配置 Stripe Webhook

在 Stripe Dashboard 设置：
```
https://yourdomain.com/stripe/webhook
```

---

## 📖 相关文档

- **完整部署指南**: `SUBSCRIPTION_SETUP.md`
- **Caddy 配置**: `CADDY_QUICKSTART.md`
- **权限系统分析**: `PERMISSION_SYSTEM_ANALYSIS.md`

---

## ❓ 常见问题

### Q: 如何将 bot 改回私有模式？

需要修改代码，重新实施方案 B 或 C。见 `PERMISSION_SYSTEM_ANALYSIS.md`。

### Q: 封禁用户后能解封吗？

可以。使用 `/admin` 命令，选择用户，点击 [Approve]，将 `allow` 设为 1。

### Q: 管理员能被封禁吗？

不能。代码中管理员（DEVELOPER_CHAT_ID）永远 `allow=1`，即使数据库中设为 0 也无效。

### Q: Premium 字段还有用吗？

基本没用了。订阅由 `subscription_status` 控制。但 `/admin` 中的 Upgrade/Downgrade 仍会修改这个字段（兼容性保留）。

---

**欢迎使用公开 Bot 模式！** 🎉
