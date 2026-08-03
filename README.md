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
| tok:Xk+Yk | 会话累计输入 + 输出 token |
| cache:XX% | 本轮请求的缓存命中率（越高越省） |
| cost:¥X.XX | 会话累计花费（按 DeepSeek 定价估算） |

- 纯 Python 实现，无需 jq / bc，Windows / macOS / Linux 通用
- 自动识别模型（deepseek-v4-pro / deepseek-v4-flash）切换定价
- 自动识别 DeepSeek 高峰时段（北京时间 9:00-12:00、14:00-18:00，价格 ×2）
- 数据全部本地计算，不上传任何信息

## 安装

1. 将 `statusline.py` 放到 `~/.claude/` 目录
2. 编辑 `~/.claude/settings.json`，添加：

```json
"statusLine": {
  "type": "command",
  "command": "python C:/Users/你的用户名/.claude/statusline.py"
}
```

> macOS / Linux 使用 `python3 ~/.claude/statusline.py`，路径按实际环境修改

3. 重启 Claude Code 生效

## 定价说明

脚本内置 DeepSeek V4 定价（2026-07 峰谷定价机制，元/百万 token）：

| 模型 | 输入（缓存未命中） | 输出 | 高峰 ×2 |
|---|---|---|---|
| deepseek-v4-pro | 3 | 6 | 是 |
| deepseek-v4-flash | 1 | 2 | 是 |

> 缓存命中部分的费用极低（约 0.02-0.025 元/百万 token），且会话累计的缓存 token 数无法从状态栏 JSON 获取，故忽略不计（误差 <1%）。
> 官方调价后，请更新脚本中的 `PRICES` 字典。

## 安全提示

- **切勿提交 `~/.claude/settings.json`** —— 其中包含明文 API key，泄露后他人可消费你的账户额度
- 本项目只包含 `statusline.py`：它不读取任何配置文件、不发起网络请求，可安全使用
- 配置示例中的 API key 请使用占位符（如 `sk-你的key`）

## License

MIT
