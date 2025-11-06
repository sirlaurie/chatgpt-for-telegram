# Caddy 快速部署指南

使用 Caddy 部署 Telegram Bot Webhook 服务器的最简单方法！

---

## 为什么选择 Caddy？

✅ **自动 HTTPS** - 无需手动配置证书
✅ **自动续期** - Let's Encrypt 证书自动更新
✅ **配置简单** - 只需几行配置
✅ **开箱即用** - 无需安装额外工具

---

## 快速开始（5 分钟）

### 步骤 1: 安装 Caddy

**Ubuntu/Debian:**
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

**CentOS/RHEL:**
```bash
dnf install 'dnf-command(copr)'
dnf copr enable @caddy/caddy
dnf install caddy
```

**其他系统**: 访问 https://caddyserver.com/docs/install

### 步骤 2: 配置 Caddy

```bash
# 复制示例配置
sudo cp Caddyfile.example /etc/caddy/Caddyfile

# 编辑配置，替换域名
sudo nano /etc/caddy/Caddyfile
# 将 yourdomain.com 替换为你的实际域名
```

**最小配置**（`/etc/caddy/Caddyfile`）：
```caddy
yourdomain.com {
    reverse_proxy /stripe/webhook localhost:8000
    reverse_proxy /payment/* localhost:8000
    reverse_proxy /health localhost:8000
}
```

### 步骤 3: 启动 Caddy

```bash
# 启动并设置开机自启
sudo systemctl enable caddy
sudo systemctl start caddy

# 检查状态
sudo systemctl status caddy
```

### 步骤 4: 验证配置

```bash
# 1. 检查 Caddy 日志
sudo journalctl -u caddy -f

# 2. 测试 HTTPS 访问
curl https://yourdomain.com/health

# 应该返回：
# {"status":"healthy"}
```

### 步骤 5: 配置 Stripe Webhook

1. 登录 Stripe Dashboard: https://dashboard.stripe.com/
2. 进入 **Developers** → **Webhooks**
3. 点击 **Add endpoint**
4. 输入 URL: `https://yourdomain.com/stripe/webhook`
5. 选择事件类型（见下方）
6. 保存并复制 Webhook Secret

**需要的事件类型**:
- ✅ `checkout.session.completed`
- ✅ `invoice.payment_succeeded`
- ✅ `invoice.payment_failed`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`

---

## 常见问题

### Q: Caddy 自动申请证书需要什么条件？

**A:** 需要满足：
1. ✅ 域名已正确解析到服务器 IP
2. ✅ 防火墙开放 80 和 443 端口
3. ✅ 服务器可公网访问

Caddy 会通过 HTTP-01 challenge 自动申请证书。

### Q: 如何查看 Caddy 日志？

```bash
# 实时查看日志
sudo journalctl -u caddy -f

# 查看最近的错误
sudo journalctl -u caddy -p err
```

### Q: 如何重新加载配置？

```bash
# 方法 1: 重启 Caddy（会中断连接）
sudo systemctl restart caddy

# 方法 2: 优雅重载（推荐，不中断连接）
sudo systemctl reload caddy
```

### Q: 证书申请失败怎么办？

**检查项**:
```bash
# 1. 检查域名解析
dig yourdomain.com

# 2. 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# 3. 查看 Caddy 日志
sudo journalctl -u caddy -n 50
```

**常见原因**:
- ❌ 域名未正确解析
- ❌ 80/443 端口未开放
- ❌ 其他服务占用 80/443 端口

### Q: 如何测试本地开发环境？

使用 Caddy 的本地 HTTPS（自签名证书）：

```bash
# 创建本地 Caddyfile
cat > Caddyfile.local << 'EOF'
localhost:8443 {
    reverse_proxy /stripe/webhook localhost:8000
    reverse_proxy /payment/* localhost:8000
    reverse_proxy /health localhost:8000
    tls internal
}
EOF

# 运行 Caddy
caddy run --config Caddyfile.local
```

访问: https://localhost:8443/health

---

## 高级配置

### 添加访问日志

```caddy
yourdomain.com {
    reverse_proxy /stripe/webhook localhost:8000
    reverse_proxy /payment/* localhost:8000

    log {
        output file /var/log/caddy/telegram-bot.log {
            roll_size 100mb
            roll_keep 10
        }
        format json
    }
}
```

### 添加速率限制

```caddy
yourdomain.com {
    # 防止 DDoS
    rate_limit {
        zone webhook {
            key {remote_host}
            events 100
            window 1m
        }
    }

    reverse_proxy /stripe/webhook localhost:8000 {
        rate_limit webhook
    }

    reverse_proxy /payment/* localhost:8000
}
```

### 添加基本认证（可选）

```caddy
yourdomain.com {
    # Webhook 不需要认证（Stripe 有签名验证）
    reverse_proxy /stripe/webhook localhost:8000

    # Payment 页面添加认证（可选）
    reverse_proxy /payment/* localhost:8000

    # Admin 接口添加认证
    basicauth /admin/* {
        admin $2a$14$Zkx...  # 使用 caddy hash-password 生成
    }

    reverse_proxy /admin/* localhost:8000
}
```

生成密码哈希：
```bash
caddy hash-password
# 输入密码，复制输出的哈希值
```

### 配置多个域名

```caddy
# 主域名
yourdomain.com {
    reverse_proxy /stripe/webhook localhost:8000
    reverse_proxy /payment/* localhost:8000
}

# www 重定向到主域名
www.yourdomain.com {
    redir https://yourdomain.com{uri} permanent
}

# 备用域名
alt.yourdomain.com {
    reverse_proxy localhost:8000
}
```

---

## 完整部署检查清单

部署前确认：

- [ ] Caddy 已安装并运行
- [ ] 域名已解析到服务器 IP
- [ ] 防火墙开放 80 和 443 端口
- [ ] Caddyfile 配置正确
- [ ] Webhook 服务器运行在 8000 端口
- [ ] 访问 `https://yourdomain.com/health` 返回成功
- [ ] Stripe Webhook 已配置
- [ ] 环境变量 `WEBHOOK_BASE_URL` 已设置

---

## 监控和维护

### 查看 SSL 证书信息

```bash
# 查看证书详情
sudo caddy list-modules | grep tls

# 查看证书过期时间
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### 设置日志轮转

```bash
# Caddy 内置日志轮转，但也可以使用 logrotate
sudo nano /etc/logrotate.d/caddy
```

添加：
```
/var/log/caddy/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 caddy caddy
    sharedscripts
    postrotate
        systemctl reload caddy > /dev/null 2>&1 || true
    endscript
}
```

### 监控 Caddy 状态

使用 Caddy 的管理 API：

```bash
# 启用管理 API（添加到 Caddyfile 顶部）
{
    admin localhost:2019
}

# 查看配置
curl localhost:2019/config/

# 查看运行状态
curl localhost:2019/metrics
```

---

## 故障排查

### Caddy 无法启动

```bash
# 检查配置语法
sudo caddy validate --config /etc/caddy/Caddyfile

# 查看详细错误
sudo journalctl -u caddy -n 100 --no-pager
```

### 端口冲突

```bash
# 检查 80/443 端口占用
sudo lsof -i :80
sudo lsof -i :443

# 如果有其他服务占用，停止它们
sudo systemctl stop nginx  # 或 apache2
```

### 证书问题

```bash
# 清除证书缓存（谨慎使用）
sudo rm -rf /var/lib/caddy/.local/share/caddy/certificates

# 重启 Caddy
sudo systemctl restart caddy
```

---

## 性能优化

```caddy
yourdomain.com {
    # 启用 HTTP/2
    protocols h1 h2

    # 启用压缩
    encode gzip zstd

    # 缓存静态文件（如果有）
    @static {
        path *.css *.js *.png *.jpg *.svg
    }
    header @static Cache-Control "public, max-age=31536000"

    reverse_proxy /stripe/webhook localhost:8000
    reverse_proxy /payment/* localhost:8000
}
```

---

## 参考资源

- 📚 Caddy 官方文档: https://caddyserver.com/docs/
- 🔧 Caddyfile 语法: https://caddyserver.com/docs/caddyfile
- 💬 Caddy 社区论坛: https://caddy.community/
- 📖 Caddy GitHub: https://github.com/caddyserver/caddy

---

**完成！** 🎉

你的 Webhook 服务器现在已经通过 HTTPS 安全运行了！
