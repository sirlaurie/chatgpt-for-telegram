# 订阅支付系统设置指南

本指南将帮助你配置和部署 Telegram Bot 的 Stripe 订阅支付系统。

---

## 📋 目录

1. [系统概览](#系统概览)
2. [前置要求](#前置要求)
3. [Stripe 配置](#stripe-配置)
4. [环境变量配置](#环境变量配置)
5. [部署步骤](#部署步骤)
6. [测试](#测试)
7. [常见问题](#常见问题)

---

## 系统概览

### 功能特性

- ✅ 新用户 5 次免费对话
- ✅ 超出额度自动拦截并提示付费
- ✅ 月付/年付订阅选项
- ✅ Stripe 安全支付集成
- ✅ 自动续费管理
- ✅ 订阅状态查询
- ✅ 支持退款（自动降级为免费用户）
- ✅ 管理员免费使用
- ✅ 自动过期检查和提醒

### 定价方案

- **月度订阅**: $9.99/月
- **年度订阅**: $99.99/年（节省 17%）

可以在 `src/helpers/stripe_helper.py` 中修改定价。

---

## 前置要求

### 1. Python 环境

- Python 3.10+
- 所有依赖已安装（见 requirements.txt）

### 2. Stripe 账户

1. 注册 Stripe 账户：https://dashboard.stripe.com/register
2. 完成账户验证（用于生产环境）
3. 获取 API 密钥

### 3. 公网服务器

需要一个有公网 IP 和 HTTPS 的服务器来接收 Stripe Webhook。

推荐选项：
- Railway (https://railway.app/)
- Render (https://render.com/)
- DigitalOcean
- AWS EC2
- 其他支持 HTTPS 的云服务

---

## Stripe 配置

### 步骤 1: 获取 API 密钥

1. 登录 Stripe Dashboard: https://dashboard.stripe.com/
2. 点击 **Developers** → **API keys**
3. 复制以下密钥：
   - **Publishable key** (pk_test_xxx 或 pk_live_xxx)
   - **Secret key** (sk_test_xxx 或 sk_live_xxx)

⚠️ **注意**：
- 测试模式密钥以 `_test_` 开头
- 生产模式密钥以 `_live_` 开头
- 永远不要将 Secret key 提交到代码仓库

### 步骤 2: 创建产品（可选）

如果你想在 Stripe Dashboard 中管理产品和价格：

1. 进入 **Products** → **Add Product**
2. 创建两个产品：
   - **Monthly Subscription** - $9.99/month
   - **Yearly Subscription** - $99.99/year
3. 复制 Price ID（price_xxx）并添加到环境变量

**或者**：代码会自动创建产品（默认方式）

### 步骤 3: 配置 Webhook

1. 进入 **Developers** → **Webhooks**
2. 点击 **Add endpoint**
3. 输入 Webhook URL：
   ```
   https://yourdomain.com/stripe/webhook
   ```
   替换 `yourdomain.com` 为你的实际域名

4. 选择以下事件类型：
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

5. 点击 **Add endpoint**

6. 点击新创建的 endpoint，复制 **Signing secret** (whsec_xxx)

---

## 环境变量配置

### 1. 复制示例配置

```bash
cp .env.example .env
```

### 2. 编辑 .env 文件

```bash
# Stripe Configuration
export STRIPE_SECRET_KEY=sk_test_xxx  # 替换为你的 Secret Key
export STRIPE_PUBLISHABLE_KEY=pk_test_xxx  # 替换为你的 Publishable Key
export STRIPE_WEBHOOK_SECRET=whsec_xxx  # 替换为你的 Webhook Secret

# Webhook Server Configuration
export WEBHOOK_BASE_URL=https://yourdomain.com  # 替换为你的域名
export WEBHOOK_HOST=0.0.0.0
export WEBHOOK_PORT=8000

# Telegram Bot (已有配置)
export bot_token=your_bot_token
export DEVELOPER_CHAT_ID=your_telegram_id

# API Keys (已有配置)
export OPENAI_API_KEY=your_openai_key
export GOOGLE_API_KEY=your_google_key
```

### 3. 加载环境变量

```bash
source .env
```

---

## 部署步骤

### 方案 1: 单服务器部署（开发/测试）

适用于开发和小规模测试。

#### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
# 或使用 uv
uv pip install -r requirements.txt
```

#### 步骤 2: 初始化数据库

第一次运行时，数据库会自动创建并迁移。

```bash
python3 start.py
```

停止后继续下一步。

#### 步骤 3: 启动服务

使用 **tmux** 或 **screen** 同时运行两个进程：

**终端 1 - Telegram Bot**:
```bash
source .env && python3 start.py
```

**终端 2 - Webhook Server**:
```bash
source .env && python3 webhook_server.py
```

#### 步骤 4: 使用 ngrok 暴露 Webhook（仅测试）

如果在本地测试，使用 ngrok 暴露端口：

```bash
ngrok http 8000
```

复制 ngrok 提供的 HTTPS URL（如 https://abc123.ngrok.io）并：
1. 更新 Stripe Webhook endpoint URL
2. 更新 .env 中的 WEBHOOK_BASE_URL

---

### 方案 2: 生产环境部署（推荐）

#### 使用 Systemd (Linux)

**1. 创建 Bot 服务**

创建文件 `/etc/systemd/system/telegram-bot.service`：

```ini
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/chatgpt-for-telegram
EnvironmentFile=/path/to/chatgpt-for-telegram/.env
ExecStart=/usr/bin/python3 /path/to/chatgpt-for-telegram/start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**2. 创建 Webhook 服务**

创建文件 `/etc/systemd/system/webhook-server.service`：

```ini
[Unit]
Description=Stripe Webhook Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/chatgpt-for-telegram
EnvironmentFile=/path/to/chatgpt-for-telegram/.env
ExecStart=/usr/bin/python3 /path/to/chatgpt-for-telegram/webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. 启动服务**

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl enable webhook-server
sudo systemctl start telegram-bot
sudo systemctl start webhook-server
```

**4. 检查状态**

```bash
sudo systemctl status telegram-bot
sudo systemctl status webhook-server
```

**5. 查看日志**

```bash
sudo journalctl -u telegram-bot -f
sudo journalctl -u webhook-server -f
```

#### 使用 Caddy 反向代理（推荐）

Caddy 自动管理 HTTPS 证书，配置极其简单！

**1. 安装 Caddy**

```bash
# Ubuntu/Debian
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# CentOS/RHEL
dnf install 'dnf-command(copr)'
dnf copr enable @caddy/caddy
dnf install caddy
```

**2. 创建 Caddyfile**

创建文件 `/etc/caddy/Caddyfile`：

```caddy
yourdomain.com {
    # Webhook endpoint for Stripe
    reverse_proxy /stripe/webhook localhost:8000

    # Payment success/cancel pages
    reverse_proxy /payment/* localhost:8000

    # Optional: Health check endpoint
    reverse_proxy /health localhost:8000
}
```

就这么简单！Caddy 会自动：
- ✅ 申请 Let's Encrypt SSL 证书
- ✅ 自动续期证书
- ✅ 配置 HTTPS
- ✅ HTTP 自动重定向到 HTTPS

**3. 启动 Caddy**

```bash
sudo systemctl enable caddy
sudo systemctl start caddy
sudo systemctl status caddy
```

**4. 查看日志**

```bash
sudo journalctl -u caddy -f
```

**5. 验证配置**

访问 `https://yourdomain.com/health` 应该返回 `{"status":"healthy"}`

---

#### 使用 Nginx 反向代理（备选方案）

如果你更熟悉 Nginx，配置如下：

**1. 安装 Certbot（用于 Let's Encrypt）**

```bash
sudo apt install certbot python3-certbot-nginx
```

**2. 配置 Nginx**

创建文件 `/etc/nginx/sites-available/telegram-bot`：

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /stripe/webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /payment/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location /health {
        proxy_pass http://localhost:8000;
    }
}
```

**3. 启用站点**

```bash
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**4. 获取 SSL 证书**

```bash
sudo certbot --nginx -d yourdomain.com
```

Certbot 会自动配置 SSL 并设置自动续期。

---

### 方案 3: Docker 部署（可选）

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "start.py"]
```

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    env_file: .env
    restart: always
    volumes:
      - ./bot.db:/app/bot.db

  webhook-server:
    build: .
    command: python3 webhook_server.py
    env_file: .env
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./bot.db:/app/bot.db
```

运行：
```bash
docker-compose up -d
```

---

## 测试

### 1. 测试免费额度

1. 与 Bot 发送 5 条消息
2. 第 6 条消息应该被拦截并显示付费提示

### 2. 测试订阅流程

1. 点击付费按钮
2. 选择订阅计划（月付/年付）
3. 使用 Stripe 测试卡号：
   - **成功**: `4242 4242 4242 4242`
   - **失败**: `4000 0000 0000 0002`
   - 任意未来日期 + 任意 CVC

4. 完成支付
5. 检查是否收到订阅成功通知
6. 发送消息测试无限对话

### 3. 测试 Webhook

检查 webhook_server 日志：

```bash
tail -f webhook_server.log
# 或
sudo journalctl -u webhook-server -f
```

应该看到类似：
```
Received webhook event: checkout.session.completed
Subscription created for telegram_id: 123456789
```

### 4. 测试订阅管理

- `/my_subscription` - 查看订阅信息
- `/cancel_subscription` - 取消自动续费
- `/usage` - 查看使用情况

---

## 常见问题

### Q1: Webhook 没有收到事件

**检查项**:
1. Webhook URL 是否正确且可公网访问
2. Webhook 服务器是否运行（`sudo systemctl status webhook-server`）
3. Stripe Dashboard → Webhooks → 点击 endpoint → 查看 "Recent deliveries"
4. 检查防火墙是否开放 8000 端口
5. 确认 HTTPS 证书有效

### Q2: 支付成功但订阅未创建

**检查项**:
1. 查看 webhook 日志：`tail -f webhook_server.log`
2. 检查数据库是否正确创建：`sqlite3 bot.db "SELECT * FROM Subscription;"`
3. 确认 STRIPE_WEBHOOK_SECRET 正确配置
4. 查看 Stripe Dashboard 中的事件日志

### Q3: 数据库迁移失败

**解决方案**:
1. 备份现有数据库：`cp bot.db bot.db.backup`
2. 手动添加新列：
   ```sql
   sqlite3 bot.db
   ALTER TABLE User ADD COLUMN free_messages_used INTEGER DEFAULT 0;
   ALTER TABLE User ADD COLUMN subscription_status TEXT DEFAULT 'free';
   -- ... 其他列
   ```

### Q4: 现有 premium 用户怎么办？

运行迁移脚本将现有 premium 用户设置为免费用户：

```python
python3 -c "
from src.utils._db import DBClient
client = DBClient()
client.cursor.execute('UPDATE User SET subscription_status = \"free\" WHERE premium = 1')
client.cursor.execute('UPDATE User SET premium = 0')
client.connection.commit()
print('Migrated premium users to free tier')
"
```

### Q5: 如何给特定用户免费订阅？

手动更新数据库：

```python
python3 -c "
from src.utils.subscription_operations import create_subscription
import time

telegram_id = 123456789  # 用户的 Telegram ID
create_subscription(
    telegram_id=telegram_id,
    stripe_subscription_id='manual_grant',
    stripe_customer_id='manual',
    plan_type='lifetime',
    current_period_start=int(time.time()),
    current_period_end=int(time.time()) + (365 * 24 * 60 * 60 * 10),  # 10 years
)
print(f'Granted lifetime subscription to {telegram_id}')
"
```

### Q6: 如何修改定价？

编辑 `src/helpers/stripe_helper.py`:

```python
PRICING = {
    "monthly": {
        "price": 19.99,  # 修改这里
        "currency": "usd",
        "interval": "month",
        ...
    },
    ...
}
```

### Q7: 如何处理退款？

1. 在 Stripe Dashboard 中处理退款
2. Webhook 会自动接收 `charge.refunded` 事件（如果配置了）
3. 手动降级用户：
   ```python
   python3 -c "
   from src.utils._db import DBClient
   client = DBClient()
   telegram_id = 123456789
   client.update_record('User', telegram_id, {
       'subscription_status': 'free',
       'free_messages_used': 0
   })
   print('User downgraded to free tier')
   "
   ```

---

## 生产环境清单

部署到生产前检查：

- [ ] 使用 Stripe **生产模式** 密钥（sk_live_xxx）
- [ ] HTTPS 已配置并有效
- [ ] Webhook URL 使用生产域名
- [ ] 所有环境变量已正确设置
- [ ] 数据库已备份
- [ ] 日志记录已配置
- [ ] 定时任务正常运行
- [ ] 测试所有支付流程
- [ ] 设置监控和告警
- [ ] 配置自动备份

---

## 支持

如有问题，请查看：
- Stripe 文档: https://stripe.com/docs
- python-telegram-bot 文档: https://docs.python-telegram-bot.org/

---

**祝你部署顺利！** 🚀
