#!/bin/bash
# Webhook 诊断脚本

echo "=========================================="
echo "Stripe Webhook 诊断"
echo "=========================================="
echo ""

# 1. 检查 webhook server 是否运行
echo "1. 检查 webhook server 状态："
if ps aux | grep -v grep | grep -q "webhook_server"; then
    echo "   ✅ webhook_server.py 正在运行"
    ps aux | grep -v grep | grep "webhook_server" | awk '{print "   PID: " $2 ", 启动时间: " $9}'
else
    echo "   ❌ webhook_server.py 未运行！"
    echo "   请启动: python webhook_server.py"
fi
echo ""

# 2. 检查端口监听
echo "2. 检查端口 8000 监听状态："
if command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":8000 "; then
        echo "   ✅ 端口 8000 正在监听"
    else
        echo "   ❌ 端口 8000 未监听"
    fi
elif command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":8000 "; then
        echo "   ✅ 端口 8000 正在监听"
    else
        echo "   ❌ 端口 8000 未监听"
    fi
else
    echo "   ⚠️  无法检查端口状态（netstat/ss 不可用）"
fi
echo ""

# 3. 测试本地 webhook endpoint
echo "3. 测试本地 webhook endpoint："
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)
if [ "$response" = "200" ]; then
    echo "   ✅ webhook server 可访问 (localhost:8000/health)"
else
    echo "   ❌ webhook server 无响应 (HTTP $response)"
fi
echo ""

# 4. 测试公网 webhook endpoint
echo "4. 测试公网 webhook URL："
webhook_url="https://stripe.autheai.com/stripe/webhook"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$webhook_url" 2>&1)
echo "   URL: $webhook_url"
echo "   响应: HTTP $response"
if [ "$response" = "400" ]; then
    echo "   ✅ 端点可访问（400 是预期的，因为没有正确的签名）"
elif [ "$response" = "200" ]; then
    echo "   ⚠️  返回 200，可能有问题"
else
    echo "   ❌ 无法访问 webhook endpoint"
fi
echo ""

# 5. 检查环境变量
echo "5. 检查 Stripe 环境变量："
if [ -n "$STRIPE_SECRET_KEY" ]; then
    echo "   ✅ STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY:0:10}..."
else
    echo "   ❌ STRIPE_SECRET_KEY 未设置"
fi

if [ -n "$STRIPE_WEBHOOK_SECRET" ]; then
    echo "   ✅ STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET:0:10}..."
else
    echo "   ❌ STRIPE_WEBHOOK_SECRET 未设置！这会导致 webhook 验证失败！"
fi

if [ -n "$WEBHOOK_BASE_URL" ]; then
    echo "   ✅ WEBHOOK_BASE_URL: $WEBHOOK_BASE_URL"
else
    echo "   ⚠️  WEBHOOK_BASE_URL 未设置"
fi
echo ""

# 6. 检查最近的 webhook 日志
echo "6. 检查最近的 webhook 日志："
if [ -f "webhook.log" ]; then
    echo "   最近 10 行日志："
    tail -10 webhook.log | sed 's/^/   /'
else
    echo "   ❌ webhook.log 文件不存在"
    echo "   日志可能输出到其他地方"
fi
echo ""

# 7. 检查数据库
echo "7. 检查数据库表："
if [ -f "bot.db" ]; then
    echo "   ✅ 数据库文件存在: bot.db"
    if command -v sqlite3 &> /dev/null; then
        echo "   数据库表："
        sqlite3 bot.db ".tables" | sed 's/^/   /'
    else
        echo "   ⚠️  sqlite3 命令不可用，无法检查表结构"
    fi
else
    echo "   ❌ 数据库文件不存在: bot.db"
fi
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "常见问题和解决方案："
echo ""
echo "1. webhook_server 未运行："
echo "   → 启动: nohup python webhook_server.py > webhook.log 2>&1 &"
echo ""
echo "2. STRIPE_WEBHOOK_SECRET 未设置："
echo "   → 在 Stripe Dashboard 创建 webhook 并获取 secret"
echo "   → 将 secret 添加到 .env 文件"
echo "   → 重启 webhook_server"
echo ""
echo "3. Stripe Dashboard 中未配置 webhook："
echo "   → 访问 https://dashboard.stripe.com/webhooks"
echo "   → 添加端点: https://stripe.autheai.com/stripe/webhook"
echo "   → 选择事件: checkout.session.completed, invoice.*, customer.subscription.*"
echo ""
echo "4. 端口 8000 被占用或防火墙阻止："
echo "   → 检查防火墙: sudo ufw allow 8000"
echo "   → 检查 Caddy 是否正确转发到 localhost:8000"
echo ""
