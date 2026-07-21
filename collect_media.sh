#!/bin/bash
# 甲骨文媒体库监控 - 只读采集脚本(不碰任何数据)
OUT=/root/media-dashboard/data/media_stats.json
EMBY_LOG=/mnt/config/logs/embyserver.txt
RCLONE_LOG=/var/log/rclone-gdrive.log

# --- Emby token(只读db) ---
KEY=$(sqlite3 /mnt/config/data/authentication.db "SELECT AccessToken FROM Tokens_2 WHERE IsActive=1 ORDER BY DateLastActivity DESC LIMIT 1" 2>/dev/null)

# --- 系统 ---
UPTIME_D=$(awk '{print int($1/86400)}' /proc/uptime)
LOAD=$(cut -d' ' -f1-3 /proc/loadavg)
MEM=$(free -m | awk '/Mem:/{printf "%d/%d", $3, $2}')
DISK=$(df -h / | awk 'NR==2{print $3"/"$2" "$5}')
DISK_PCT=$(df / | awk 'NR==2{print $5}' | tr -d '%')

# --- Docker容器 ---
EMBY_STATUS=$(docker inspect emby-server --format '{{.State.Status}}' 2>/dev/null)
EMBY_UP=$(docker ps --filter name=emby-server --format '{{.Status}}' 2>/dev/null)
EMBY_CPU=$(docker stats emby-server --no-stream --format '{{.CPUPerc}}' 2>/dev/null)
EMBY_VER=$(curl -sS --max-time 5 "http://127.0.0.1:8096/emby/System/Info/Public" 2>/dev/null | grep -oE '"Version":"[^"]*"' | cut -d'"' -f4)

# --- Emby会话 ---
SESS=$(curl -sS --max-time 6 "http://127.0.0.1:8096/emby/Sessions?api_key=$KEY" 2>/dev/null)
PLAYING=$(echo "$SESS" | python3 -c "import sys,json;d=json.load(sys.stdin);print(len([s for s in d if s.get('NowPlayingItem')]))" 2>/dev/null || echo 0)

# --- rclone ---
RC_MOUNT=$(mount | grep -q fatshare && echo "ok" || echo "DOWN")
RC_ACTIVE=$(systemctl is-active rclone-gdrive 2>/dev/null)
RC_CACHE=$(du -sh /var/cache/rclone 2>/dev/null | cut -f1)
RC_ERR=$(grep -icE "ERROR" "$RCLONE_LOG" 2>/dev/null || echo 0)

# --- STRM统计(按目录,超时保护) ---
strm_count(){ timeout 25 find "$1" -name "*.strm" 2>/dev/null | wc -l | tr -d ' '; }
STRM_DAILY=$(strm_count /home/syncthing/daily_strm_new)
STRM_NEW3=$(timeout 25 find /home/syncthing -name "*.strm" -mtime -3 2>/dev/null | wc -l | tr -d ' ')
STRM_NEW7=$(timeout 25 find /home/syncthing -name "*.strm" -mtime -7 2>/dev/null | wc -l | tr -d ' ')
STRM_TOTAL=$(timeout 60 find /home/syncthing -name "*.strm" 2>/dev/null | wc -l | tr -d ' ')
STRM_DOLBY=$(timeout 40 find /home/syncthing -name "*.strm" -exec grep -l "doVi" {} \; 2>/dev/null | wc -l | tr -d ' ')

# --- 定时任务 - 使用Python解析更可靠 ---
# systemctl list-timers 列: NEXT (1-3 words) LEFT (1) LAST (1-3) PASSED (1) UNIT (1)
# UNIT is at $NF (last column)
python3 -c '
import sys
import json
timers = []
lines = sys.stdin.read().splitlines()
started = False
for line in lines:
    if line.startswith("NEXT "):
        started = True
        continue
    if line.startswith("--") or "loaded units listed" in line or not line.strip():
        continue
    if not started:
        continue
    parts = line.split()
    if len(parts) >= 6:
        next_time = " ".join(parts[0:3])
        unit = parts[-1]
        timers.append({"unit": unit, "next": next_time})
print(json.dumps(timers))
' < <(systemctl list-timers --all 2>/dev/null) > /tmp/timers.json

# --- 证书剩余天数 ---
CERT_DAYS=$(for f in /etc/letsencrypt/live/*/cert.pem; do [ -f "$f" ] && echo "$(basename $(dirname $f)):$(( ($(date -d "$(openssl x509 -enddate -noout -in $f|cut -d= -f2)" +%s) - $(date +%s))/86400 ))d"; done 2>/dev/null | tr '\n' ' ')

# --- 输出JSON ---
python3 - <<END_PYTHON
import json
import time
import os

with open('/tmp/timers.json', 'r') as f:
    timers = json.load(f)

data = {
    "ts": int(time.time()),
    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "sys": {
        "uptime_days": "$UPTIME_D",
        "load": "$LOAD",
        "mem_mb": "$MEM",
        "disk": "$DISK",
        "disk_pct": int("$DISK_PCT")
    },
    "emby": {
        "status": "$EMBY_STATUS",
        "up": "$EMBY_UP",
        "cpu": "$EMBY_CPU",
        "version": "$EMBY_VER",
        "playing": int("$PLAYING")
    },
    "rclone": {
        "mount": "$RC_MOUNT",
        "active": "$RC_ACTIVE",
        "cache": "$RC_CACHE",
        "errors": int("$RC_ERR")
    },
    "strm": {
        "daily_new": int("$STRM_DAILY"),
        "new_3d": int("$STRM_NEW3"),
        "new_7d": int("$STRM_NEW7"),
        "total": int("$STRM_TOTAL"),
        "dolby": int("$STRM_DOLBY")
    },
    "timers": timers,
    "cert": "$CERT_DAYS"
}

with open("$OUT", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(json.dumps(data, ensure_ascii=False, indent=2))
END_PYTHON
