# 开发说明（AstrBot 适配）

## 目录结构

```text
astrbot_plugin_maimaidx_prober/
├─ main.py                # AstrBot Star 入口：命令分发、ctx 适配、LLM 工具注册
├─ metadata.yaml          # 插件元数据
├─ _conf_schema.json      # 配置面板声明
├─ core/
│  ├─ compat.py           # 命令层轻量适配基座（Command/Tool/PluginConfigBase/PluginBase）
│  ├─ plugin.py           # 插件主类：组装各层与生命周期
│  ├─ config.py           # 强类型配置（pydantic）
│  ├─ commands/           # 命令 mixin：@Command(正则) / @Tool
│  ├─ services/           # 业务服务：查分、音乐、渲染、OAuth
│  ├─ clients/            # diving-fish / lxns API 客户端
│  ├─ stores/             # JSON 存储：绑定、别名
│  └─ renderers/          # HTML 面板渲染 + B50 / 信息卡 PIL 渲染
├─ assets/                # 本地素材（B50 版式、字体、曲绘）
└─ scripts/
   ├─ quick_command_test.py   # 只读回归脚本
   └─ download_font.py        # 可选：下载 AWMC 中文字体
```

## 分层约定

- 命令写在 `core/commands/*.py` 的 mixin 里，用 `@Command(name, description,
  pattern)` 声明正则；`main.py` 启动时扫描 MRO 收集并绑定到插件实例，消息到达
  时按「字面前缀长度」从具体到宽泛依次匹配，命中后 `stop_event()`；
- 命令通过 `self.ctx.send.text/image/forward` 发送，`main.py` 的 `AstrBotCtx`
  把它们映射到当前 `AstrMessageEvent`；
- 配置由 `_conf_schema.json` 生成面板，`main.py` 把落盘 JSON 解析成
  `core/config.py` 的 pydantic 模型后注入插件主类；
- 持久化数据一律放在 AstrBot 插件数据目录（`StarTools.get_data_dir`），
  不写入插件目录。

## 新增 / 修改命令

1. 在对应 mixin 中新增 `@Command(...)` 方法，签名约定：

   ```python
   async def handler(self, stream_id: str = "", matched_groups: dict = None, **kwargs):
       ...
       return ok, "描述", True   # 第三项 True 表示已处理，终止事件传播
   ```

2. 正则统一以 `^/mai` 开头（AstrBot 会把 `wake_prefix` 剥掉，`main.py` 会补回
   开头的 `/` 再匹配）；
3. 图片类结果用 `_render_and_send`（内部走 `HtmlRenderer`），文本用
   `self.ctx.send.text`。

## 渲染

`core/services/renderer.py` 的 `HtmlRenderer` 懒加载 Playwright 单例浏览器，
按以下顺序选择可执行文件：

1. 配置 `render.browser_executable`；
2. 自动探测系统 Chrome / Edge；
3. Playwright 托管 Chromium（需 `python -m playwright install chromium`）。

B50 / AP50 不走 HTML，而是 `core/renderers/b50_awmc_pillow.py` 的 PIL 版式，
素材在 `assets/awmc_core`，曲绘优先本地 `assets/awmc/mai/cover`，缺失时在线回退。
中文字体优先读取 `assets/awmc_core/font/ResourceHanRoundedCN-Bold.ttf`
（可通过 `python scripts/download_font.py` 单独下载）；未放入时按平台顺序
回退到系统中文字体，最后回退到 `VarelaRound-Regular.ttf`。下载后的字体已
被 `.gitignore` 忽略，确认本地渲染效果后不会被误提交。

单曲详情与落雪单曲最佳走 `core/renderers/awmc_info_pillow.py`：直接按
`chart_info.png` / `play_info.png` AWMC 模板拼版，同样优先本地曲绘、远程兜底。
帮助页由 `core/renderers/help.py` 统一生成总览、`df help` 与 `lxns help`。

## 回归测试

```bash
# Windows PowerShell（在 AstrBot 后端同环境 Python 下）
$env:ASTRBOT_PLUGIN_ROOT = "插件目录路径"
$env:ASTRBOT_PLUGIN_DATA = "<ASTRBOT_ROOT>\data\plugin_data\astrbot_plugin_maimaidx_prober"
$env:ASTRBOT_PLUGIN_CONFIG = "<ASTRBOT_ROOT>\data\config\astrbot_plugin_maimaidx_prober_config.json"
$env:ASTRBOT_TEST_QQ = "测试 QQ 号"
$env:ASTRBOT_TEST_OUT = "输出目录"
python scripts\quick_command_test.py
```

脚本只做只读调用，上传命令走 dry_run；输出 PASS/FAIL 摘要与渲染样本。

## 注意事项

- 网络请求一律用 `aiohttp`，不要在命令层引入同步阻塞；
- 密钥不要写入日志；绑定数据文件权限要收紧；
- 依赖声明只放 `requirements.txt`，Playwright Chromium 不要写进依赖。
