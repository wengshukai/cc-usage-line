# cc-usage-line

Claude Code 状态栏（statusline）小工具：在 CLI 底部实时显示**模型、上下文使用率、token 用量、缓存命中率、花费金额**。

> **适用场景**：本工具面向**通过 DeepSeek API（Anthropic 兼容端点）驱动 Claude Code** 的用户——`cost` 字段按 DeepSeek 官方定价折算（含峰谷时段），只有在这套组合下金额才准确。若使用其他端点或非 DeepSeek 模型，模型名 / `ctx` / token / `cache` 仍可正常显示，但 `cost` 会按 DeepSeek 价格误算，请忽略或自行修改脚本中的 `PRICES`。

```
[deepseek-flash[1m] ctx:23.2% ↑249.8k ↓193.5k cache:98.6% cost:¥1.37]
```

## 字段说明

| 字段 | 含义 |
|---|---|
| 模型名 | 当前使用的模型 |
| ctx:XX.X% | 上下文占用，与 `/context` 命令同口径（分母为 auto-compact 窗口：1M 模型 = 786432，即 `/context` 里显示的 "786.4k"），精确到 0.1% |
| ↑Xk ↓Xk | 当前对话累计输入（↑，不含缓存读取）/ 输出（↓）token |
| cache:XX.X% | 当前对话累计缓存命中率（越高越省） |
| cost:¥X.XX | 当前对话累计花费（缓存命中按低价计费） |

- 纯 Python 实现，无需 jq / bc，Windows / macOS / Linux 通用
- 自动识别模型（deepseek-flash / deepseek-v4-pro）切换定价
- 自动识别 DeepSeek 峰谷时段：**周一至周五**（不含法定节假日）北京时间 9:00-12:00、14:00-18:00 价格 ×2，**周末全天按空闲价**
- 数据全部本地计算，不上传任何信息

## 安装

### 方式 A：一键安装脚本（Windows，推荐）

下载 / clone 本仓库后双击 `install.bat`，自动完成「复制脚本到 `~/.claude/`」+「写入 settings.json」（原配置自动备份为 `settings.json.bak`），重启 Claude Code 即生效。

### 方式 B：手动安装（三步）

**第 1 步：下载脚本**

```bash
git clone https://github.com/wengshukai/cc-usage-line.git
cp cc-usage-line/statusline.py ~/.claude/
```

（或打开仓库页面点 `statusline.py` → Raw，另存到 `~/.claude/` 目录。）

**第 2 步：配置 settings.json**

编辑 `~/.claude/settings.json`，加入：

```json
"statusLine": {
  "type": "command",
  "command": "python C:/Users/你的用户名/.claude/statusline.py"
}
```

| 系统 | command 写法 |
|---|---|
| Windows | `python C:/Users/你的用户名/.claude/statusline.py` |
| macOS / Linux | `python3 ~/.claude/statusline.py` |

**第 3 步：重启 Claude Code**

底部状态栏即生效。

## 验证安装

```bash
echo '{}' | python ~/.claude/statusline.py
```

- 输出 `[Unknown]` → 安装成功（正式使用时显示真实数据）
- 输出红色报错 → 检查 Python 是否在 PATH 中

## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| 不显示 `cache:` 字段 | 模型端点没返回缓存数据（非 DeepSeek 端点常见） | 换官方 DeepSeek Anthropic 端点，或忽略 |
| 显示 `Unknown` 模型名 | Claude Code 版本旧，状态栏数据不完整 | 升级 Claude Code |
| 金额显示 `¥0.000` | 会话刚开始 token 少，或用的非 DeepSeek 模型 | 正常，多聊几轮再看 |
| `ctx` 与 `/context` 差 0~1 个百分点 | 状态栏用 API 实测 token（最近一轮调用），`/context` 用本地估算（敲命令那一刻），两边天然有微小出入 | 正常现象（口径已一致：同除 auto-compact 窗口） |
| 想自定义模型 / 定价 | 编辑脚本里的 `PRICES` 字典 | 见下方定价说明 |

> **Q：`cost` 为什么不是从我的第一条消息开始算？**
>
> 脚本的累计从启用状态栏那一刻开始（每次响应后按 `session_id` 累加到 `~/.claude/statusline-state.json`），之前的历史账单不会自动包含。
>
> 如果想回算历史对话的完整账单：读取 `~/.claude/projects/<项目目录>/<session_id>.jsonl`，累加每条 assistant 消息的 `usage` 字段（`input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens`），再按 `PRICES` 定价换算即可。注意 transcript 中 resume 重放的记录会出现重复 usage，需按消息 ID 去重。

## 定价说明

脚本内置 DeepSeek 官方定价（元/百万 token，**空闲时段**；高峰时段价格 ×2）：

| 模型 | 输入·缓存命中 | 输入·未命中 | 输出 |
|---|---|---|---|
| deepseek-flash | 0.02 | 1 | 4 |
| deepseek-v4-pro | 0.15 | 4.5 | 13.5 |

> 高峰时段为**周一至周五**（不含中国法定节假日）北京时间 9:00-12:00、14:00-18:00；其余时间（含周末及法定节假日全天）为空闲时段。
> 来源：https://api-docs.deepseek.com/zh-cn/quick_start/pricing（2026-10 核对）。官方调价后，请更新脚本中的 `PRICES` 字典。

**统计口径**（当前对话累计）：脚本每次被调用时把本轮用量按 `session_id` 累加到本地状态文件（`~/.claude/statusline-state.json`），新开对话自动从零累计。状态栏 JSON 的会话累计输入 `total_input_tokens` 包含缓存读取，会严重高估，故不使用；缓存命中部分按官方低价单独计费。

**ctx 口径**：用最近一次 API 调用的输入侧 token 除以 auto-compact 窗口（1M 模型 = 786432，约为名义窗口的 75%，这正是 `/context` 显示的分母；Claude Code 官方对状态栏的 `used_percentage` 是除以名义窗口 1M 且取整，故此处自行重算以对齐 `/context` 并保留 0.1% 精度）。如需跟随自定义的 auto-compact 设置，可通过环境变量 `CLAUDE_CODE_AUTO_COMPACT_WINDOW` 覆盖。

## 文件说明

| 文件 | 作用 |
|---|---|
| `statusline.py` | 状态栏脚本本体 |
| `install.py` | 安装脚本（复制 + 写配置，自动备份原 settings.json） |
| `install.bat` | Windows 双击运行安装 |
| `README.md` | 本文档 |

## 卸载

从 `settings.json` 删掉 `statusLine` 字段，再删除 `~/.claude/statusline.py`（及 `~/.claude/statusline-state.json`）即可。

## 安全提示

- **切勿提交 `~/.claude/settings.json`** —— 其中包含明文 API key，泄露后他人可消费你的账户额度
- 本项目只包含 `statusline.py`：它不读取任何配置文件、不发起网络请求，可安全使用
- 配置示例中的 API key 请使用占位符（如 `sk-你的key`）

## License

MIT
