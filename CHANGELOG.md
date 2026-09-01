# 更新日志

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
