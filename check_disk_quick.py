import sys
import os
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("\n--- GLOBAL DISK I/O METRICS ---")
disk = psutil.disk_io_counters()
print(f"Read Count:  {disk.read_count:,}")
print(f"Write Count: {disk.write_count:,}")
print(f"Read Bytes:  {disk.read_bytes / (1024**3):.2f} GB")
print(f"Write Bytes: {disk.write_bytes / (1024**3):.2f} GB")

print("\n--- RUNNING PYTHON PROCESSES IN OUR DIRECTORY ---")
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'io_counters']):
    try:
        if 'python' in p.info['name'].lower():
            cmd = " ".join(p.info['cmdline'] or [])
            if "AI powered autocorrect" in cmd:
                io = p.info['io_counters']
                r_mb = io.read_bytes / (1024*1024) if io else 0
                w_mb = io.write_bytes / (1024*1024) if io else 0
                ram = p.info['memory_info'].rss / (1024*1024) if p.info['memory_info'] else 0
                print(f"PID: {p.info['pid']} | Name: {p.info['name']} | CPU: {p.cpu_percent():.1f}% | RAM: {ram:.1f} MB | Lifetime Disk Read: {r_mb:.1f} MB | Lifetime Disk Write: {w_mb:.1f} MB | Cmd: {cmd[:60]}")
    except:
        pass
print("-------------------------------------------------\n")
