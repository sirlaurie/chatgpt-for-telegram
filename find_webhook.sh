#!/bin/bash
# 查找 webhook_server 的运行状态和日志位置

echo "=========================================="
echo "查找 webhook_server 运行状态"
echo "=========================================="
echo ""

# 1. 检查进程
echo "1. 检查 webhook_server 进程："
if ps aux | grep -v grep | grep -q "webhook_server"; then
    echo "   ✅ webhook_server 正在运行"
    echo ""
    ps aux | grep -v grep | grep "webhook_server" | while read line; do
        echo "   $line"
        pid=$(echo $line | awk '{print $2}')
        echo "   PID: $pid"

        # 检查进程的工作目录
        if [ -d "/proc/$pid" ]; then
            echo "   工作目录: $(readlink /proc/$pid/cwd 2>/dev/null || echo '无法读取')"
            echo "   命令行: $(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' || echo '无法读取')"

            # 检查文件描述符（日志可能输出到哪里）
            echo "   输出重定向到:"
            ls -l /proc/$pid/fd/ 2>/dev/null | grep -E "1|2" | head -5 || echo "   无法读取文件描述符"
        fi
    done
else
    echo "   ❌ webhook_server 未运行！"
fi
echo ""

# 2. 检查可能的日志文件位置
echo "2. 查找可能的日志文件："
possible_logs=(
    "./webhook.log"
    "./webhook_server.log"
    "/var/log/webhook.log"
    "/var/log/webhook_server.log"
    "/tmp/webhook.log"
    "~/webhook.log"
    "./logs/webhook.log"
    "./nohup.out"
)

for log in "${possible_logs[@]}"; do
    if [ -f "$log" ]; then
        echo "   ✅ 找到: $log"
        echo "      最后修改: $(stat -c %y "$log" 2>/dev/null || stat -f %Sm "$log" 2>/dev/null)"
        echo "      大小: $(du -h "$log" | cut -f1)"
    fi
done
echo ""

# 3. 检查是否用 systemd 运行
echo "3. 检查 systemd 服务："
if systemctl list-units --type=service 2>/dev/null | grep -q webhook; then
    echo "   ✅ 找到 systemd 服务"
    systemctl status webhook* 2>/dev/null | head -20
    echo ""
    echo "   查看日志使用: sudo journalctl -u webhook -f"
else
    echo "   ❌ 没有找到 systemd 服务"
fi
echo ""

# 4. 检查最近的 nohup.out 文件
echo "4. 查找 nohup.out 文件："
find . -name "nohup.out" -mtime -1 2>/dev/null | while read file; do
    echo "   ✅ 找到: $file"
    echo "      最后修改: $(stat -c %y "$file" 2>/dev/null || stat -f %Sm "$file" 2>/dev/null)"
done
echo ""

# 5. 检查当前目录的所有日志文件
echo "5. 当前目录的日志文件："
ls -lht *.log 2>/dev/null | head -10 || echo "   没有找到 .log 文件"
echo ""

# 6. 检查端口 8000
echo "6. 检查端口 8000 使用情况："
if command -v lsof &> /dev/null; then
    lsof -i :8000 2>/dev/null || echo "   端口 8000 未被使用"
elif command -v netstat &> /dev/null; then
    netstat -tuln | grep :8000 || echo "   端口 8000 未被使用"
elif command -v ss &> /dev/null; then
    ss -tuln | grep :8000 || echo "   端口 8000 未被使用"
else
    echo "   无法检查端口状态"
fi
echo ""

echo "=========================================="
echo "建议："
echo "=========================================="
echo ""
echo "如果 webhook_server 正在运行但没有日志文件："
echo "1. 可能用 systemd 运行 → 使用 journalctl 查看日志"
echo "2. 可能输出到 stdout/stderr → 重新启动并重定向到文件"
echo "3. 可能在其他目录运行 → 检查工作目录"
echo ""
echo "正确的启动方式："
echo "  cd /path/to/chatgpt-for-telegram"
echo "  source .env"
echo "  pkill -f webhook_server.py"
echo "  nohup python webhook_server.py > webhook.log 2>&1 &"
echo "  tail -f webhook.log"
echo ""
