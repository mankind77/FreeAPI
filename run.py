#!/usr/bin/env python3
"""
FreeAPI Directory - 一键启动脚本

    python run.py           # 仅本地访问 http://localhost:9000
    python run.py --public  # 同时生成公网
"""

import subprocess
import sys
import os
import time
import re
import threading
import socket
import argparse

# 强制关闭输出缓冲，确保实时显示
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data.db")


def check_deps():
    try:
        import fastapi, uvicorn, sqlalchemy, jinja2, httpx, aiosqlite
    except ImportError as e:
        print(f"[!] 缺少依赖: {e}")
        print("[*] 请运行: pip install -r requirements.txt")
        sys.exit(1)


def start_tunnel(port: int):
    """创建 localhost.run SSH 隧道，返回公网 URL。"""
    print("[*] 正在创建公网隧道 (localhost.run)...", flush=True)
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        "-R", f"80:localhost:{port}",
        "nokey@localhost.run",
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    url = [None]
    def read():
        for line in proc.stdout:
            m = re.search(r'(https://[a-z0-9]+\.lhr\.life)', line)
            if m:
                url[0] = m.group(1)
                break

    t = threading.Thread(target=read, daemon=True)
    t.start()

    time.sleep(5)
    try:
        s = socket.create_connection(("localhost.run", 80), timeout=8)
        s.sendall(b"GET / HTTP/1.0\r\nHost: localhost.run\r\n\r\n")
        s.recv(4096)
        s.close()
    except Exception:
        pass

    time.sleep(4)
    if url[0]:
        with open(os.path.join(PROJECT_DIR, "tunnel.pid"), "w") as f:
            f.write(str(proc.pid))
    return url[0], proc


def main():
    parser = argparse.ArgumentParser(description="FreeAPI Directory Server")
    parser.add_argument("--public", action="store_true", help="同时生成公网 URL")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    check_deps()

    # 自动关闭旧进程
    port = args.port
    old_killed = False
    try:
        import psutil
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == "LISTEN":
                psutil.Process(conn.pid).terminate()
                print(f"[*] 已关闭占用端口 {port} 的旧进程 (PID {conn.pid})")
                old_killed = True
                time.sleep(1)
    except ImportError:
        pass
    if not old_killed:
        # Fallback: try pkill
        try:
            subprocess.run(f"pkill -f 'uvicorn.*:{port}'", shell=True, timeout=3)
        except Exception:
            pass

    # 初始化数据库
    if not os.path.exists(DB_PATH):
        print("[*] 数据库不存在，正在初始化...")
        subprocess.run([sys.executable, os.path.join(PROJECT_DIR, "seed.py")], check=True)

    port = args.port
    local_url = f"http://localhost:{port}"

    print()
    print("=" * 50, flush=True)
    print("  FreeAPI Directory", flush=True)
    print("=" * 50, flush=True)
    print(f"  本地访问: {local_url}", flush=True)
    print(f"  AI 搜索:  {local_url}/search", flush=True)

    # 公网隧道
    tunnel_proc = None
    if args.public:
        public_url, tunnel_proc = start_tunnel(port)
        if public_url:
            print(f"  公网访问: {public_url}", flush=True)
            print(f"  公网搜索: {public_url}/search", flush=True)
            print(flush=True)
            print("  >>> 把这个链接分享给任何人即可访问! <<<", flush=True)
        else:
            print("  [!] 公网隧道创建失败，仅本地可用", flush=True)
            print("  [*] 手动创建: ssh -R 80:localhost:9000 nokey@localhost.run", flush=True)

    print("=" * 50, flush=True)
    print("  按 Ctrl+C 停止服务器", flush=True)
    print(flush=True)

    import uvicorn
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
    finally:
        if tunnel_proc:
            tunnel_proc.terminate()


if __name__ == "__main__":
    main()
