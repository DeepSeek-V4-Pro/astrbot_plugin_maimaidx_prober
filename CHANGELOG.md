# 更新日志

## 1.1.0（2026-09-03）

同步 MaiBot 上游 `maimaidx_prober` v3.3.0 内容。

### 功能

- `/mai song` 单曲详情改用 AWMC `chart_info` 模板 Pillow 拼版，新增
  `render_song_info`；
- 落雪 `/mai lxns best` 改用 AWMC `play_info` 模板，新增 `render_play_info`，
  展示达成率 / RA / DX 分数与星数 / 评级 / FC / FS；
- B50 渲染补充渐变背景、随机默认头像与落雪年份页脚素材，补齐 `chart_info`
  底部评级预估 RA 卡片，并修正水鱼 notes 的 TOUCH / BREAK 列位；
- `/mai today` 加入 7 套随机角色主题（prism_plus / circle 立绘与 AWMC 前景 logo），
  封面下方补充曲目 ID 与类型，定数改为按难度分色的标签列表，祝福语并入页脚；
- `/mai help` 改为命令总览入口，新增 `/mai df help` 与 `/mai lxns help`，
  落雪页采用双列命令网格；Maidle 说明保留为 `/mai maidle help`。

### 细节修复

- `/mai b50` / `/mai my` 支持 `--水鱼` / `--落雪` 中文来源标志，且可放在用户参数前后；
- 落雪头像改用 `assets2.lxns.net` 原始 PNG，规避 WAF；
- 水鱼旧 Developer-Token 回退标注 2026-10-01 停止服务；
- 快速回归脚本补齐三页帮助与两个 Pillow 渲染器检查。

### AstrBot 适配说明

- 核心逻辑保持 `core/` 分层，命令仍由 `main.py` 统一分发；
- 配置版本统一提升到 `config_version = 3.3.0`，与上游 3.3 发布保持一致；
- 图片署名与 User-Agent 保持 AstrBot 版本：`AstrBot/1.1`。

## 1.0.0（2026-09-02）

首个 AstrBot 适配版。

### 功能

- 舞萌 DX 双源查分：diving-fish（水鱼）+ lxns（落雪）；
- B50 成绩图（AWMC/Yuzu 原版版式）、个人成绩、按版本成绩、曲目搜索与详情、
  Maidle 猜歌、谱面统计、今日运势、热门歌曲、Rating 排行榜、双服状态、
  本地别称管理；
- 水鱼账号 OAuth（设备码 + refresh token）与 Import-Token 绑定；
- 落雪 OAuth / 个人密钥绑定，热力图、趋势、单曲历史/排行、年度回顾、
  收藏品、玩家资料卡、AP50、按 QQ 查玩家；
- 水鱼 ↔ 落雪成绩双向同步（只升不降）；
- LLM 工具 `search_mai_songs`（曲库搜索）。

### AstrBot 适配说明

- 入口为 AstrBot Star 体系：`main.py` 统一做命令正则分发、`ctx.send` /
  插件数据目录映射、LLM 工具注册；
- 配置改为 `_conf_schema.json` 可视化面板，数据落盘到 AstrBot 插件数据目录；
- 图片渲染优先复用系统 Chrome / Edge，其次 Playwright Chromium，避免重复下载；
- 命令匹配兼容 AstrBot 的 `wake_prefix`（如 `/`）剥离行为；
- B50 曲绘兼容水鱼 5 位新歌 ID 的本地映射，远端优先水鱼官方曲绘源。

### 测试

- `scripts/quick_command_test.py` 全量只读回归：49/49 通过；
- B50 渲染器使用真实账号数据 + 本地素材验证（1400x1600 PNG）。
