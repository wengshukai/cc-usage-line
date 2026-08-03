# cc-usage-line

Claude Code 状态栏（statusline）小工具：在 CLI 底部实时显示**模型、上下文使用率、token 用量、缓存命中率、花费金额**。

```
[deepseek-v4-pro ctx:12% tok:8.3k+1.2k cache:83% cost:¥0.032]
```

## 功能

| 字段 | 含义 |
|---|---|
| 模型名 | 当前使用的模型 |
| ctx:XX% | 上下文窗口使用率 |
| tok:Xk+Yk | 当前对话累计新增输入 + 输出 token（不含缓存读取） |
| cache:XX% | 当前对话累计缓存命中率（越高越省） |
| cost:¥X.XX | 当前对话累计花费（缓存命中按低价计费） |

- 纯 Python 实现，无需 jq / bc，Windows / macOS / Linux 通用
- 自动识别模型（deepseek-v4-pro / deepseek-v4-flash）切换定价
- 自动识别 DeepSeek 高峰时段（北京时间 9:00-12:00、14:00-18:00，价格 ×2）
- 数据全部本地计算，不上传任何信息

## 安装（三步）

### 第 1 步：下载脚本

方式 A（推荐，以后升级直接 `git pull`）：

```bash
git clone https://github.com/wengshukai/cc-usage-line.git
cp cc-usage-line/statusline.py ~/.claude/
```

方式 B（懒得 clone，直接下载文件）：打开仓库页面点 `statusline.py` → Raw，另存到 `~/.claude/` 目录。

### 第 2 步：配置 settings.json

编辑 `~/.claude/settings.json`，加入：

```json
"statusLine": {
  "type": "command",
  "command": "python C:/Users/你的用户名/.claude/statusline.py"
}
```

不同系统对应写法：

| 系统 | command 写法 |
|---|---|
| Windows | `python C:/Users/你的用户名/.claude/statusline.py` |
| macOS / Linux | `python3 ~/.claude/statusline.py` |

### 第 3 步：重启 Claude Code

底部状态栏即生效，显示效果：

```
[deepseek-v4-pro ctx:12% tok:8.3k+1.2k cache:83% cost:¥0.032]
```

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
| 想自定义模型 / 定价 | 编辑脚本里的 `PRICES` 字典 | 见下方定价说明 |

## 定价说明

脚本内置 DeepSeek V4 定价（2026-07 峰谷定价机制，元/百万 token）：

| 模型 | 输入（缓存未命中） | 输出 | 高峰 ×2 |
|---|---|---|---|
| deepseek-v4-pro | 3 | 6 | 是 |
| deepseek-v4-flash | 1 | 2 | 是 |

> 统计口径为**当前对话累计**：脚本每次被调用时把本轮用量按 `session_id` 累加到本地状态文件（`~/.claude/statusline-state.json`），新开对话自动从零累计。
> 状态栏 JSON 的会话累计输入 `total_input_tokens` 包含缓存读取，会严重高估，故不使用；缓存命中部分按官方低价（0.02-0.025 元/百万 token）单独计费。
> 官方调价后，请更新脚本中的 `PRICES` 字典。

## 安全提示

- **切勿提交 `~/.claude/settings.json`** —— 其中包含明文 API key，泄露后他人可消费你的账户额度
- 本项目只包含 `statusline.py`：它不读取任何配置文件、不发起网络请求，可安全使用
- 配置示例中的 API key 请使用占位符（如 `sk-你的key`）

## License

MIT
