"""
Diagnostic tool to measure active disk I/O, identify top disk consumers,
and verify autocorrect process resource usage.
"""

import os
import sys
import time
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def sample_io():
    proc_map = {}
    for p in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info', 'io_counters']):
        try:
            info = p.info
            io = info.get('io_counters')
            read_bytes = io.read_bytes if io else 0
            write_bytes = io.write_bytes if io else 0
            mem = info.get('memory_info')
            ram_mb = mem.rss / (1024 * 1024) if mem else 0.0
            cpu = info.get('cpu_percent') or 0.0
            exe = info.get('exe') or ""
            proc_map[info['pid']] = {
                'name': info['name'],
                'read': read_bytes,
                'write': write_bytes,
                'ram_mb': ram_mb,
                'cpu': cpu,
                'exe': exe,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return proc_map

def main():
    print("\n" + "=" * 75)
    print("           🔍 REAL-TIME SYSTEM DISK I/O & PROCESS AUDIT")
    print("=" * 75)

    s1 = sample_io()
    time.sleep(2.0)
    s2 = sample_io()

    rates = []
    for pid, p2 in s2.items():
        p1 = s1.get(pid)
        if p1:
            diff_r = p2['read'] - p1['read']
            diff_w = p2['write'] - p1['write']
            total_kb_sec = (diff_r + diff_w) / (2.0 * 1024.0)
            rates.append({
                'pid': pid,
                'name': p2['name'],
                'rate_kb_sec': total_kb_sec,
                'read_kb_sec': diff_r / (2.0 * 1024.0),
                'write_kb_sec': diff_w / (2.0 * 1024.0),
                'ram_mb': p2['ram_mb'],
                'cpu': p2['cpu'],
                'exe': p2['exe'],
            })

    rates.sort(key=lambda x: x['rate_kb_sec'], reverse=True)

    print("\n--- TOP 10 ACTIVE DISK I/O PROCESSES (Last 2.0s) ---")
    print(f"{'PID':>7} | {'PROCESS NAME':<24} | {'DISK I/O (KB/s)':>15} | {'RAM (MB)':>10} | {'PATH'}")
    print("-" * 75)
    for r in rates[:10]:
        print(f"{r['pid']:>7} | {r['name']:<24} | {r['rate_kb_sec']:>15.1f} | {r['ram_mb']:>10.1f} | {r['exe'][:40]}")

    print("\n--- AUTOCORRECT PYTHON PROCESSES ---")
    found_any = False
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'io_counters', 'cpu_percent', 'memory_info']):
        try:
            if 'python' in p.name().lower():
                cmd = " ".join(p.cmdline())
                if 'AI powered autocorrect' in cmd or 'web_app.py' in cmd or 'sandbox_gui.py' in cmd:
                    found_any = True
                    # Find matching rate
                    match_rate = next((x['rate_kb_sec'] for x in rates if x['pid'] == p.pid), 0.0)
                    print(f"PID {p.pid:>6} | Cmd: {cmd[:45]:<45} | Disk I/O: {match_rate:.2f} KB/s | CPU: {p.cpu_percent():.1f}% | RAM: {p.memory_info().rss/(1024*1024):.1f} MB")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not found_any:
        print("  No autocorrect Python processes found actively running.")

    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
