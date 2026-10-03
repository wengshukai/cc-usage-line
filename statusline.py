#!/usr/bin/env python3
"""Claude Code status line: model / context / tokens / cache hit rate / cost.
按 session_id 把每轮用量累加到本地状态文件，显示【当前对话】的累计数据；
新开对话（新 session_id）自动从零累计。缓存读取 token 单独计费，不混入输入。
ctx 与 /context 的百分比对齐：分子为最近一次 API 调用的输入侧 token，
分母为其 "Auto-compact window"（见 auto_compact_window()）。
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Windows 下强制 UTF-8 输出，避免 ¥ 等符号因 GBK 报错
sys.stdout.reconfigure(encoding="utf-8")

STATE_FILE = os.path.expanduser("~/.claude/statusline-state.json")

try:
    data = json.load(sys.stdin)
except Exception:
    print("[cache:--%]")
    sys.exit(0)

model = (data.get("model") or {}).get("display_name") or "Unknown"
session_id = data.get("session_id") or "default"

cw = data.get("context_window") or {}
used_pct = cw.get("used_percentage")
cu = cw.get("current_usage") or {}
cur_in = cu.get("input_tokens") or 0
cur_out = cu.get("output_tokens") or 0
cache_read = cu.get("cache_read_input_tokens") or 0
cache_create = cu.get("cache_creation_input_tokens") or 0


def fmt_k(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


# DeepSeek 官方定价（元 / 百万 token，此处为空闲时段价，高峰时段 ×2）
# 来源：https://api-docs.deepseek.com/zh-cn/quick_start/pricing（2026-10 核对）
PRICES = {
    "pro":   {"in": 4.5, "out": 13.5, "cache": 0.15},
    "flash": {"in": 1.0, "out": 4.0,  "cache": 0.02},
}


def is_peak_hour():
    """高峰时段：周一至周五（不含法定节假日）北京时间 9:00-12:00、14:00-18:00，
    价格为空闲时段 2 倍；周末全天按空闲计（法定节假日未处理，一年仅十余天）"""
    now = datetime.now(timezone(timedelta(hours=8)))
    return now.weekday() < 5 and now.hour in (9, 10, 11, 14, 15, 16, 17)


def calc_cost(model_name, cur_in, cache_read, cache_create, cur_out):
    """费用：新输入 + 缓存读取（低价） + 缓存写入 + 输出"""
    key = "flash" if "flash" in model_name.lower() else "pro"
    price = PRICES[key]
    mult = 2.0 if is_peak_hour() else 1.0
    raw = (cur_in + cache_create) * price["in"] + cache_read * price["cache"] + cur_out * price["out"]
    return raw * mult / 1_000_000


# ---- ctx 分母：与 /context 的 "Auto-compact window" 对齐 ----
# 实测 1M 模型为 786432（= 1Mi × 75%，/context 显示 "786.4k"），其他窗口按同比例换算。
# 支持 CLAUDE_CODE_AUTO_COMPACT_WINDOW 环境变量覆盖（与 Claude Code 同名机制）。
def auto_compact_window(size):
    env = (os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW") or "").strip()
    if env.isdigit() and int(env) > 0:
        return int(env)
    return round(size / 1_000_000 * 1_048_576 * 0.75)


# ---- 会话累计：把每轮用量按 session_id 累加到本地状态文件 ----
def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


state = load_state()
if session_id not in state:
    # 新会话：只保留最近 4 个旧会话记录，避免文件无限增长
    state = {k: v for k, v in list(state.items())[-4:]}
s = state.setdefault(session_id, {"in": 0, "out": 0, "cache_read": 0, "cache_create": 0})
s["in"] += cur_in
s["out"] += cur_out
s["cache_read"] += cache_read
s["cache_create"] += cache_create
save_state(state)

# ---- 显示：全部为当前对话累计口径 ----
parts = []
# ctx 用原始 token 数自算（stdin 的 used_percentage 已被 SDK 取整，达不到 0.1% 精度）
ctx_used = cur_in + cache_create + cache_read
size = cw.get("context_window_size")
if size and ctx_used > 0:
    parts.append(f"ctx:{ctx_used / auto_compact_window(size) * 100:.1f}%")
elif used_pct is not None:
    parts.append(f"ctx:{used_pct:.1f}%")

if s["in"] + s["out"] > 0:
    parts.append(f"↑{fmt_k(s['in'])} ↓{fmt_k(s['out'])}")

total_cur = s["in"] + s["cache_read"] + s["cache_create"]
if total_cur > 0:
    rate = s["cache_read"] * 100 / total_cur
    parts.append(f"cache:{rate:.1f}%")

cost = calc_cost(model, s["in"], s["cache_read"], s["cache_create"], s["out"])
if cost > 0:
    parts.append(f"cost:¥{cost:.3f}" if cost < 1 else f"cost:¥{cost:.2f}")

print(f"[{model} {' '.join(parts)}]".replace(" ]", "]"))
