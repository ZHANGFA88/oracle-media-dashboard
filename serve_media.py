#!/usr/bin/env python3
import os, json, subprocess, urllib.parse, urllib.request, time, random
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("MEDIA_PORT", "8771"))
HOST = "0.0.0.0"
BASE = "/root/media-dashboard"
STATS = BASE + "/data/media_stats.json"
EMBY_LOG = "/mnt/config/logs/embyserver.txt"
RCLONE_LOG = "/var/log/rclone-gdrive.log"
EMBY_KEY = "a9f314e11d5a4b06a7120617bfe04589"
EMBY_HOST = "127.0.0.1:8096"

def tail_log(path, n=60, grep=None):
    try:
        if grep:
            out = subprocess.run(['bash','-c',"grep -iE '%s' '%s' 2>/dev/null | tail -%d" % (grep, path, n)],
                                 capture_output=True, text=True, timeout=10)
        else:
            out = subprocess.run(['tail','-n',str(n),path], capture_output=True, text=True, timeout=10)
        return out.stdout.splitlines()
    except Exception as e:
        return ["(读取失败: %s)" % e]

def classify(line):
    l = line.lower()
    if 'error' in l or 'fail' in l or 'exception' in l or 'denied' in l:
        return 'error'
    if 'warn' in l:
        return 'warn'
    return 'info'

def fetch_emby(url):
    try:
        api_key = EMBY_KEY
        if '?' in url:
            full_url = 'http://' + EMBY_HOST + url + '&api_key=' + api_key
        else:
            full_url = 'http://' + EMBY_HOST + url + '?api_key=' + api_key
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok':False,'error':str(e)}

def get_ip_location(ip):
    """通过IP获取经纬度，使用免费IP定位API"""
    try:
        if ip.startswith('10.') or ip.startswith('172.16.') or ip.startswith('192.168.') or ip.startswith('127.'):
            return (31.23, 121.47)
        if ':' in ip:
            return (31.23, 121.47)
        req = urllib.request.Request('http://ip-api.com/json/%s?fields=status,country,regionName,city,lat,lon' % ip)
        with urllib.request.urlopen(req, timeout=3) as r:
            d = json.loads(r.read().decode('utf-8'))
            if d.get('status') == 'success':
                return (d.get('lat'), d.get('lon'))
            else:
                return (31.23, 121.47)
    except Exception as e:
        return (31.23, 121.47)

class Handler(SimpleHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        try:
            if path == '/api/media/stats':
                try:
                    age = time.time() - os.path.getmtime(STATS)
                except:
                    age = 9999
                if age > 55:
                    subprocess.run(['bash', BASE+'/collect_media.sh'], capture_output=True, timeout=90)
                try:
                    with open(STATS, 'r') as f:
                        return self._json(200, json.load(f))
                except Exception as e:
                    return self._json(500, {'ok':False,'error':str(e)})
            if path == '/api/media/logs':
                src = q.get('src', ['emby'])[0]
                n = int(q.get('n', ['60'])[0])
                path_map = {
                    'emby': EMBY_LOG,
                    'rclone': RCLONE_LOG,
                }
                p = path_map.get(src, EMBY_LOG)
                lines = tail_log(p, n=n, grep=None)
                out = [{'t': classify(line), 'l': line} for line in lines]
                return self._json(200, {'lines':out})
            if path == '/api/media/poster':
                mid = q.get('id', [None])[0]
                if not mid:
                    self.send_response(404)
                    self.end_headers()
                    return
                url = 'http://' + EMBY_HOST + '/emby/Items/' + mid + '/Images/Primary?api_key=' + EMBY_KEY
                req = urllib.request.Request(url)
                try:
                    with urllib.request.urlopen(req, timeout=10) as r:
                        data = r.read()
                        self.send_response(200)
                        self.send_header('Content-Type', 'image/jpeg')
                        self.end_headers()
                        self.wfile.write(data)
                except Exception as e:
                    self.send_response(404)
                    self.end_headers()
                return
            if path == '/api/media/movies':
                # 查询电影 + 电视剧，所有视频类型，保留最多 22 个
                d = fetch_emby('/emby/Items?SortBy=DateCreated&SortOrder=Descending&Limit=36&Recursive=true&Fields=PrimaryImageAspectRatio,ImageTags&IncludeItemTypes=Movie,Series')
                if isinstance(d,dict):
                    d = d.get('Items', d.get('Data', []))
                if not isinstance(d, list):
                    d = []
                out = []
                for i in d:
                    # 放宽条件：只要有 ImageTags 或者 PrimaryImageTag 就显示
                    has_poster = i.get('PrimaryImageTag') is not None or 'Primary' in (i.get('ImageTags') or {})
                    if has_poster:
                        out.append({'name':i.get('Name'),'year':i.get('ProductionYear'),'id':i.get('Id')})
                # 打乱顺序，电影电视剧随机排列
                random.shuffle(out)
                # 只保留前 22 个，避免重叠太挤
                return self._json(200, out[:22])
            if path == '/api/media/access':
                d = fetch_emby('/emby/Sessions')
                if isinstance(d,dict):
                    d = d.get('Items', d.get('Data', []))
                if not isinstance(d, list):
                    d = []
                out = []
                seen = set()
                for s in d:
                    # 只显示正在播放：当 NowPlayingItem 存在且非空就是正在播放
                    if not s.get('NowPlayingItem'):
                        continue
                    ip = s.get('RemoteEndPoint','')
                    if not ip:
                        continue
                    if ip not in seen:
                        seen.add(ip)
                        # 获取IP位置
                        lat, lon = get_ip_location(ip)
                        # 区域标记
                        if ':' in ip:
                            loc = 'HK' if ip.startswith('2408') or ip.startswith('200') else 'CN'
                        else:
                            loc = 'CN'
                        # 获取当前播放的itemId和名称
                        now_playing = s.get('NowPlayingItem', {})
                        item_id = now_playing.get('Id') if now_playing else None
                        item_name = now_playing.get('Name') if now_playing else 'Unknown'
                        out.append({
                            'user': s.get('UserName'),
                            'client': s.get('Client'),
                            'device': s.get('DeviceName'),
                            'ip': ip,
                            'loc': loc,
                            'lat': lat,
                            'lon': lon,
                            'itemId': item_id,
                            'itemName': item_name
                        })
                return self._json(200, out[:12])
            if path == '/' or path == '':
                self.path = '/public/media.html'
            return super().do_GET()
        except Exception as e:
            return self._json(500, {'ok':False,'error':str(e)})

    def log_message(self, *a):
        pass

if __name__ == '__main__':
    os.chdir(BASE)
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print('MediaMonitor at http://%s:%d' % (HOST, PORT))
    srv.serve_forever()
