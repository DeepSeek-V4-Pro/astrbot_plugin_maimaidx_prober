# MaiMai DX 查分器（AstrBot 适配 · v1.0.0）

AstrBot 版的舞萌 DX 双源查分插件，连接
[diving-fish（水鱼）](https://www.diving-fish.com) 与
[lxns（落雪）](https://maimai.lxns.net) 两个查分平台。

提供 B50 成绩图（AWMC/Yuzu 原版版式）、个人成绩、曲目搜索、Maidle 猜歌、
谱面统计、今日运势、热门歌曲、Rating 排行榜、按版本查成绩，以及落雪独有的
热力图、趋势、单曲历史/排行、年度回顾、收藏品、双向成绩同步等能力。

## 功能一览

- **B50 成绩图**：AWMC/Yuzu 原版版式（固定 1400x1600 画布、难度贴图成绩卡、
  评级/FC/FS/DX 星、头像、段位/阶级徽章）；BEST 35 / BEST 15 不足时保持空白
  槽位。水鱼 5 位新歌 ID 会自动映射本地曲绘，缺失时按「水鱼 → 落雪」顺序在线回退。
- **个人成绩摘要**：Rating、段位、曲目数、难度分布、Top 成绩。
- **曲目搜索与详情**：名称/作者/ID/别称搜索，封面 + 落雪补全（分类/版本/谱师/定数）。
- **猜歌（Maidle）**：水鱼猜歌游戏，图片线索反馈。
- **谱面统计 / 运势 / 选一 / 服务器状态**：难度分布、今日宜忌、随机选择、双服健康检查。
- **水鱼公共数据**：热门歌曲、DX Rating 排行榜、按版本查询成绩。
- **水鱼账号 OAuth**：设备码绑定，每用户独立 refresh token，旧 Import-Token 自动回退。
- **落雪账号能力**：OAuth / 个人密钥绑定后解锁热力图、趋势、历史、排行、年度回顾、
  收藏品、玩家资料卡、AP50、按 QQ 查玩家。
- **成绩双向同步**：水鱼 → 落雪（`/mai lxns upload`）、落雪 → 水鱼（`/mai df upload`），
  均采用**只升不降**策略。

## 安装

1. 把整个 `astrbot_plugin_maimaidx_prober` 目录放到
   `<ASTRBOT_ROOT>\data\plugins\`；
2. 在 WebUI「插件管理」中加载 / 重载插件（pip 依赖会按 `requirements.txt`
   自动安装到插件隔离目录）；
3. 图片类命令需要浏览器：插件会优先自动使用系统已装的 Chrome / Edge，
   只有都找不到时才需要安装一次 Playwright Chromium：

   ```bash
   python -m playwright install chromium
   ```

4. 发送 `/mai help`，收到命令总览图片即安装成功。

> 容器 / 无交互环境可在配置面板「渲染 → 浏览器路径」手动指定浏览器，
> 或参考 `install_deps.py` 自行构建镜像。

## 配置

全部配置在 WebUI 插件设置面板中完成（由 `_conf_schema.json` 生成），落盘到
`<ASTRBOT_ROOT>\data\config\astrbot_plugin_maimaidx_prober_config.json`。

| 分组 | 关键项 | 说明 |
| --- | --- | --- |
| 插件 | `developer_qq` | 允许使用开发者凭证（落雪/水鱼）的 QQ 列表，为空则关闭全部开发者功能 |
| 插件 | `game_version` | 落雪趋势接口默认版本号（25500 = 舞萌DX 2026） |
| 水鱼 | `developer_token` | 水鱼开发者密钥（`/mai plate` 按版本查成绩用） |
| 水鱼 | `enable_oauth` 等 | 水鱼账号 OAuth（设备码绑定，需填 `oauth_client_id`） |
| 落雪 | `enable_oauth` 等 | 落雪 OAuth 绑定（需应用 ID/密钥） |
| 落雪 | `enable_developer_api` + `developer_api_key` | 好友码查询 / AP50 / 按 QQ 查玩家 |
| 渲染 | `device_scale_factor` / `browser_executable` / `no_sandbox` | 渲染参数与浏览器路径 |

### 落雪接入方式

| 方式 | 配置 | 绑定命令 | 可用能力 |
| --- | --- | --- | --- |
| OAuth（推荐） | `enable_oauth` + 应用 ID/密钥 | `/mai lxns bind`（OOB 授权码） | 全量账号能力 |
| 个人 API 密钥 | 无需配置 | `/mai lxns bind token <密钥>` | 全量账号能力（不含评论） |
| 开发者 API | `enable_developer_api` + `developer_api_key` | 无需绑定，好友码直查 | 好友码 / AP50 / 按 QQ 查玩家 |

开发者密钥是全局凭证，只有 `developer_qq` 白名单内的 QQ 才能触发开发者功能；
列表为空时这些功能全部关闭。

## 命令速查

### 基础命令（`/mai`）

| 命令 | 说明 | 输出 |
|------|------|------|
| `/mai help` | 命令总览 | 图片 |
| `/mai song <关键词/ID>` | 搜索曲目；ID 直接查看详情 | 图片 |
| `/mai today` | 今日运势 — 宜忌与推荐歌曲 | 图片 |
| `/mai maidle` | 开始 Maidle 猜歌游戏 | 图片 |
| `/mai maidle guess <ID/名称>` | 猜歌 — 提交猜测 | 图片 |
| `/mai maidle answer` | 猜歌 — 查看答案 | 图片 |
| `/mai maidle help` | 猜歌规则说明 | 图片 |
| `/mai charts` | 全谱面难度分布统计 | 图片 |
| `/mai hot [N]` | 热门歌曲 TOP N | 图片 |
| `/mai ranking [N]` | DX Rating 排行榜 TOP N | 图片 |
| `/mai status` | 双服状态检测（水鱼 + 落雪） | 图片 |
| `/mai pick <A> <B> [C] [D]` | 随机帮你选一个 | 图片 |
| `/mai plate <版本代号>` | 按版本查询成绩（OAuth / Developer-Token） | 图片 |
| `/mai alias add <ID> <名称>` | 添加本地别称 | 文本 |
| `/mai alias del <ID> <名称>` | 删除本地别称 | 文本 |
| `/mai alias list <ID>` | 查看别称 | 图片 |
| `/mai alias import` | 从 lxns 导入社区别名 | 文本 |
| `/mai df bind` | 发起水鱼 OAuth 绑定（设备码） | 文本 |
| `/mai df bind confirm` | 确认水鱼 OAuth 绑定结果 | 文本 |
| `/mai df unbind` | 解除水鱼 OAuth 绑定 | 文本 |
| `/mai df status` | 查看水鱼 OAuth 绑定状态 | 文本 |

### 成绩查询（`/mai`）

| 命令 | 说明 | 输出 |
|------|------|------|
| `/mai b50 [用户] [--lxns\|--df]` | Best 50 成绩图；可强制指定数据源 | 图片 |
| `/mai my [--lxns\|--df]` | 个人成绩摘要（需绑定 Token / 账号） | 图片 |
| `/mai bind <Token>` | 绑定水鱼成绩导入 Token | — |
| `/mai unbind` | 解除绑定 | — |

> 强制数据源：默认自动选源（绑定落雪 → 开发者好友码 → 水鱼兜底）。
> `--lxns` 强制落雪，`--df` 强制水鱼。好友码查询走落雪开发者 API，
> 需配置 `developer_api_key` 并把 QQ 加入 `developer_qq` 白名单。

### 落雪账号（`/mai lxns`）

| 命令 | 说明 | 输出 |
|------|------|------|
| `/mai lxns bind` | OAuth 授权绑定（私聊流程） | — |
| `/mai lxns bind token <个人API密钥>` | 个人 API 密钥绑定 | — |
| `/mai lxns bind code <授权码>` | 用授权码完成 OAuth 绑定 | — |
| `/mai lxns unbind` | 解除绑定 | — |
| `/mai lxns status` | 查看绑定状态与开发者权限 | 图片 |
| `/mai lxns player [好友码]` | 玩家资料卡 | 图片 |
| `/mai lxns heatmap` | 成绩上传热力图 | 图片 |
| `/mai lxns trend [版本号]` | DX Rating 趋势 | 图片 |
| `/mai lxns history <曲名/ID>` | 单曲游玩历史 | 图片 |
| `/mai lxns rank <曲名/ID>` | 单曲分数排行 | 图片 |
| `/mai lxns year [年份]` | 年度回顾 | 图片 |
| `/mai lxns collections` | 收藏品（称号/头像/姓名框/背景） | 图片 |
| `/mai lxns best [好友码] <曲名>` | 单曲所有谱面最佳成绩 | 图片 |
| `/mai lxns upload` | 水鱼成绩同步到落雪（只升不降） | 文本 |
| `/mai df upload` | 落雪成绩同步到水鱼（反向，只升不降） | 文本 |
| `/mai lxns ap50 <好友码>` | All Perfect 50（开发者模式） | 图片 |
| `/mai lxns qq <QQ号>` | 按 QQ 查玩家资料（开发者模式） | 图片 |
| `/mai lxns comment list/post/like` | 曲目评论（落雪服务端暂未开放） | 文本 |

### AI 工具

| 工具名 | 功能 |
|--------|------|
| `search_mai_songs` | 按名称/艺术家/ID/别称搜索舞萌 DX 曲库 |

## 数据存储

插件私有数据放在
`<ASTRBOT_ROOT>\data\plugin_data\astrbot_plugin_maimaidx_prober\`：

| 文件 | 内容 |
|------|------|
| `bindings.json` | 水鱼 Import-Token 绑定（明文） |
| `lxns_bindings.json` | 落雪绑定（OAuth 令牌 / 个人密钥，明文） |
| `df_oauth_bindings.json` | 水鱼 OAuth 绑定（access/refresh token，明文） |
| `aliases.json` | 本地别称 |

曲库使用内存 TTL 缓存（水鱼/落雪，ETag/304 增量）；Maidle 会话 15 分钟过期，
后台定时清理。

## 目录与体积说明

- `core/`：业务模块（命令 / 服务 / 渲染 / 客户端 / 存储）；
- `core/compat.py`：命令层与 AstrBot 之间的轻量适配基座；
- `assets/awmc_core`（约 19MB）：B50 版式的 UI 贴图与字体，**必需**；
- `assets/awmc/mai/cover`（约 388MB）：B50 曲绘离线缓存，**可选，不随仓库分发**。
  未放置时 B50 会从水鱼 / lxns 在线拉取曲绘，首次渲染稍慢；需要离线时自行把
  曲绘包放到该目录即可（已被 `.gitignore` 忽略）。
- `scripts/quick_command_test.py`：只读回归脚本（服务层 + 渲染器）。

## 常见问题 FAQ

### Q1: `/mai today` 图片里没有曲绘

封面按图片内容校验，lxns CDN 被反爬时自动回退水鱼。若仍缺失，多为两个 CDN
都没有该曲封面，卡片显示「曲绘缺失」占位。

### Q2: `/mai b50` 长时间无响应

多为曲库未缓存、浏览器首次启动或目标用户隐私设置导致。稍等 30 秒重试。

### Q3: 图片模糊

确认配置面板「渲染」里 `device_scale_factor = 2.0`。

### Q4: 容器里图片渲染失败

优先在配置面板指定浏览器路径，或执行 `python -m playwright install chromium`，
并保持 `no_sandbox = true`。

### Q5: Token 提示失效

在 diving-fish 网站重新生成 Token 后执行 `/mai bind <新Token>`。

### Q6: 提示「开发者功能仅限授权 QQ 使用」

开发者功能受 `developer_qq` 白名单限制；列表为空时全部关闭。

### Q7: B50 的 BEST 15 为什么少一行

B50 使用固定 1400x1600 画布：BEST 35 恒为 7 行、BEST 15 恒为 3 行；
成绩不足时对应槽位留空。

### Q8: 落雪 / 水鱼数据不一样，以哪个为准

自动选源时优先落雪（已绑定）→ 开发者好友码 → 水鱼兜底；可用 `--lxns` /
`--df` 固定数据源。

### Q9: 新歌曲绘显示成同一张占位图

已修复：本地曲绘按去掉 10000 偏移的 ID 命名查找，远端优先水鱼官方曲绘源。
如仍出现，确认插件已重载到最新版本。

## 已知问题

1. **落雪评论接口未开放**：`/mai lxns comment *` 实测服务端 404，命令保留并友好提示。
2. **水鱼无头像/段位数据**：水鱼来源的 B50 显示默认图标，不显示阶级/段位徽章。
3. **lxns 资源 CDN 反爬**：封面/头像/收藏品图已改用 `!webp` 后缀规避 WAF，
   极小概率仍可能缺图并回退水鱼。
4. **首次渲染较慢**：内置浏览器首次启动需 10-30 秒。

## 卸载

1. 在 WebUI「插件管理」中停用插件；
2. 删除插件目录与
   `<ASTRBOT_ROOT>\data\plugin_data\astrbot_plugin_maimaidx_prober\`
   （含绑定密钥，先备份）；
3. 可选：`python -m playwright uninstall chromium`。

## 安全说明

本插件会在**本机保存以下密钥**（均为主动提供，用于查询/同步成绩）：

| 密钥 | 存放位置 | 用途 | 吊销方式 |
| --- | --- | --- | --- |
| 水鱼 Import-Token | `bindings.json` | 读取 / 上传水鱼成绩 | 水鱼「编辑个人资料」重新生成 |
| 水鱼 OAuth 令牌 | `df_oauth_bindings.json` | 以账号身份访问水鱼 | 水鱼「已授权应用」撤销；`/mai df unbind` |
| 落雪个人 API 密钥 | `lxns_bindings.json` | 读取 / 上传落雪成绩 | 落雪「账号详情页」重新生成 |
| 落雪 OAuth 令牌 | `lxns_bindings.json` | 以账号身份访问落雪 | 落雪「已授权应用」撤销 |
| 落雪开发者密钥（全局） | 插件配置 | 好友码 / AP50 / 按 QQ 查询 | 落雪开发者面板重置 |
| 水鱼 Developer-Token（全局） | 插件配置 | `/mai plate` 按版本查询 | 水鱼开发者面板重置 |

要点：

1. 上述密钥**明文**保存在本机，请严格限制 AstrBot 数据目录的文件权限；
2. 绑定类命令请在私聊执行，完成后立即撤回含密钥/授权码的消息；
3. 插件不会把令牌写入日志或错误回执；若在日志中看到密钥，请立即吊销并重新绑定；
4. `developer_qq` 白名单只拦截命令入口，密钥文件本身仍依赖文件权限；
5. 所有 API 通信均为 HTTPS，建议定期轮换密钥、仅在需要时绑定；
6. `/mai lxns upload`、`/mai df upload` 会修改绑定账号的成绩（只升不降），
   执行前确认账号正确；
7. 删除插件数据目录会同时删除密钥文件，卸载前先备份。

## 免责声明

1. 本插件按「现状」提供，不提供任何明示或暗示的担保；
2. 为查询成绩，插件会在使用者本机保存主动提供的密钥（见「安全说明」），
   密钥不会上传到插件作者服务器；使用者对密钥的保管与泄露风险自行负责；
3. 因使用本插件产生的任何后果（成绩数据错误、账号异常、密钥泄露等）由使用者承担；
4. 插件连接第三方维护的水鱼 / lxns 服务，不对其可用性、数据准确性、隐私与安全负责；
5. 图片渲染依赖浏览器环境，在精简容器、受限沙盒中可能无法正常输出；
6. 使用者应遵守所在地区法律法规以及所接入平台的服务条款。

---

开发说明见 [DEVELOPMENT.md](DEVELOPMENT.md)，更新日志见
[CHANGELOG.md](CHANGELOG.md)，第三方素材与许可见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
