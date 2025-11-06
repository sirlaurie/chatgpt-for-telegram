#!/bin/bash
# 诊断 403 错误的脚本

echo "=========================================="
echo "诊断 stripe.autheai.com 的 403 错误"
echo "=========================================="
echo ""

# 1. DNS 解析
echo "1. DNS 解析："
if command -v dig &> /dev/null; then
    dig +short stripe.autheai.com
elif command -v nslookup &> /dev/null; then
    nslookup stripe.autheai.com | grep -A1 "Name:"
else
    echo "   DNS 工具不可用，请手动检查"
fi
echo ""

# 2. 测试不同路径
echo "2. 测试不同端点："
for path in "/health" "/payment/success" "/"; do
    echo "   Testing: https://stripe.autheai.com$path"
    response=$(curl -s -o /dev/null -w "%{http_code}" -m 5 https://stripe.autheai.com$path 2>&1)
    echo "   → HTTP $response"
done
echo ""

# 3. 检查响应头
echo "3. 检查服务器响应头："
curl -I -m 5 https://stripe.autheai.com/health 2>&1 | grep -i "server\|cf-ray\|x-powered-by\|via" || echo "   无法获取响应头"
echo ""

# 4. 测试直接访问本地服务
echo "4. 测试本地 webhook server："
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1 | grep -q "200"; then
    echo "   ✅ 本地服务器运行正常 (localhost:8000)"
else
    echo "   ❌ 本地服务器未运行或无响应"
fi
echo ""

# 5. 检查 Caddy 状态
echo "5. 检查 Caddy 状态："
if systemctl is-active --quiet caddy 2>/dev/null; then
    echo "   ✅ Caddy 正在运行"
    echo "   配置文件："
    sudo caddy validate --config /etc/caddy/Caddyfile 2>&1 | head -3 || echo "   无法验证配置"
else
    echo "   ❌ Caddy 未运行或不是 systemd 服务"
fi
echo ""

# 6. 检查防火墙
echo "6. 防火墙规则："
if command -v ufw &> /dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "   UFW 状态："
    sudo ufw status | grep -E "443|8000"
elif command -v iptables &> /dev/null; then
    echo "   检查 iptables..."
    sudo iptables -L -n | grep -E "443|8000" | head -5 || echo "   无 443/8000 端口规则"
else
    echo "   未检测到防火墙或无权限查看"
fi
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果看到 'server: envoy'，说明有外部代理在拦截请求。"
echo "常见原因："
echo "  - CloudFlare WAF 规则"
echo "  - VPS 提供商的 DDoS 保护"
echo "  - 反向代理配置错误"
echo ""
echo "请检查："
echo "  1. CloudFlare 安全设置（如果使用）"
echo "  2. VPS 控制面板的防火墙规则"
echo "  3. DNS 是否指向正确的 IP"
