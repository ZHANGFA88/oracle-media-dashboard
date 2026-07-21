# 🎬 甲骨文 Emby 媒体库监控大屏

> 一个美观实用的 Emby 媒体库实时监控仪表盘，带 3D 地球在线用户光点，每日更新海报墙，系统状态监控，STRM 健康度统计，定时任务展示。

## ✨ 功能特性

| 功能 | 描述 | 状态 |
|------|------|------|
| 🌍 **3D 地球** | 显示当前在线用户，根据 IP 真实地理位置显示光点，点击光点直接跳转播放 | ✅ 完成 |
| 👥 **Who's Watching** | 列表显示在线用户：区域 + IP + 用户名 + 设备 + 当前正在播放影片 | ✅ 完成 |
| 🎬 **每日更新海报墙** | 显示最近入库的电影/电视剧海报，**限制 22 个避免拥挤**，电影电视剧随机排列 | ✅ 完成 |
| 🔗 **正确跳转 Emby** | 点击海报直接跳转到 `https://tv.embyapp.top` 对应影片播放页 | ✅ 完成 |
| 🩺 **STRM 健康度** | 详细统计 STRM 文件：全库总数、杜比视界数量、日更库数量、近 3 天/7 天新增 | ✅ 完成 |
| ⏱️ **定时任务** | 显示所有 systemd 定时任务和下次运行时间，包括 STRM 自动更新任务 | ✅ 完成 |
| ☁️ **云盘状态** | 显示 Rclone 云盘挂载状态、缓存用量、错误计数 | ✅ 完成 |
| 💻 **系统信息** | CPU、内存、磁盘、负载实时显示 | ✅ 完成 |
| 🔐 **SSL 证书** | 显示 Let's Encrypt 证书剩余天数 | ✅ 完成 |
| 📝 **日志中心** | 实时查看 Emby/Rclone/STRM 日志，支持 tab 切换 | ✅ 完成 |
| 🌓 **深色/浅色主题** | 支持一键切换主题，自动保存偏好 | ✅ 完成 |

## 📐 布局结构

严格三栏布局，每个模块都有合适的尺寸，不会出现长条溢出：

| 📍 位置 | 宽度 | 模块 |
|--------|------|------|
| **左栏** | 280px | 🌍 3D 地球 → 👥 谁在看 Emby → 📊 媒体库总览 |
| **中栏** | 自适应 | 🎬 每日更新海报墙（上） → 📝 日志中心（下） |
| **右栏** | 280px | 🩺 STRM 健康度 → ⏱️ 定时任务 → ☁️ 云盘 → 💻 系统 → 🔐 证书 |

## 📊 STRM 健康度统计

面板现在包含以下详细信息：

| 统计项 | 说明 |
|--------|------|
| **全库总 STRM** | 整个 `/home/syncthing` 目录下所有 `.strm` 文件总数 |
| **杜比视界 STRM** | 包含 `doVi` 标记的杜比视界 STRM 文件数量 |
| **日更库 STRM** | `/home/syncthing/daily_strm_new` 目录下的 STRM 数量 |
| **近 3 天新增** | 最近 3 天新增的 STRM 文件数量 |
| **近 7 天新增** | 最近 7 天新增的 STRM 文件数量 |

## ⏰ 定时任务展示

自动收集所有 systemd 定时任务，显示任务名称和下次运行时间：

常见任务示例：
- `certbot.service` - SSL 证书自动续期
- `daily-strm-weekly.service` - STRM 每日更新同步
- `dolby-strm-weekly.service` - 杜比视界 STRM 处理
- `strm-deadlink-monthly.service` - STRM 死链月度检查
- `apt-daily.service` - 系统自动更新
- `fstrim.service` - SSD 定期trim优化

## 🎬 每日更新海报墙

- ✅ 只包含 **电影 + 电视剧**，不包含演员/导演
- ✅ 限制 **最多 22 个海报**，避免布局拥挤重叠
- ✅ 每次刷新 **随机打乱顺序**，电影电视剧混排
- ✅ 点击海报直接跳转 Emby 正确播放页

## 🚀 快速部署

### 1. 克隆项目到服务器
```bash
git clone https://github.com/ZHANGFA88/oracle-media-dashboard.git
cd oracle-media-dashboard
chmod +x *.sh
```

### 2. 修改配置
编辑 `serve_media.py` 修改：
```python
PORT = 8771              # 监控端口
EMBY_KEY = "你的 API Key"  # Emby API Key
EMBY_HOST = "127.0.0.1:8096" # Emby 地址
```

### 3. 安装 systemd 服务
```bash
cp media-dashboard.service /etc/systemd/system/
# 如果你安装路径不是 /root/media-dashboard，需要编辑 service 文件修改路径
systemctl daemon-reload
systemctl enable media-dashboard
systemctl start media-dashboard
```

### 4. 访问
打开浏览器访问：
```
http://你的服务器IP:8771
```

## 📁 项目结构

```
oracle-media-dashboard/
├── README.md              # 📝 项目说明文档
├── collect_media.sh       # 📊 统计数据采集脚本
├── serve_media.py         # 🚀 Python HTTP 服务端
├── media-dashboard.service # ⚙️ systemd 服务配置文件
└── public/
    ├── media.html         # 🎨 前端大屏页面
    └── cobe.js            # 🌍 3D 地球渲染库
```

## 🔧 依赖

- Python 3.7+
- Linux (systemd)
- **无需额外 Python 依赖**，全部使用标准库
- Emby/Jellyfin 媒体服务器
- 可选：rclone 云盘挂载，STRM 自动同步任务

## 📝 说明

- 💯 **完全只读**：不修改 Emby 任何数据，只做监控展示
- 🔄 **自动刷新**：所有数据每分钟更新一次
- 🖼️ **海报代理**：海报图片通过 Emby API 代理获取，无需本地存储
- 📍 **IP 定位**：使用免费 ip-api.com 服务获取真实地理位置

## 🎨 截图预览

### 🖥️ 完整大屏界面

![完整大屏](https://i.imgur.com/your-screenshot.png)

### 📊 STRM 健康度面板

```
 🩺 STRM 健康度
─────────────────────────────────
全库总 STRM        24,629
杜比视界 STRM            0
日更库 STRM          1,980
近 3 天新增              21
近 7 天新增              53
```

### ⏰ 定时任务面板

```
 ⏱️ 定时任务
─────────────────────────────────
certbot.service             Tue 2026-07-21 14:44:22
daily-strm-weekly.service   Wed 2026-07-22 06:05:20
dolby-strm-weekly.service   Fri 2026-08-07 04:47:51
...
```

## 🎯 特色

- 原生 JavaScript + CSS，不需要 Node.js，不需要打包，直接运行
- 响应式布局，适配不同屏幕
- 美观的毛玻璃效果面板
- 星空渐变背景，现代UI设计
- 代码简洁，易于二次开发

## 🎨 致谢

- [cobe](https://github.com/evanw/cobe) - 优秀的 3D 地球渲染库
- 灵感来自金融可视化大屏

## 📄 许可证

MIT License

---

*项目由 OpenClaw AI 辅助开发 🤖*
