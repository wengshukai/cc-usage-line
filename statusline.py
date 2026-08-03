#!/usr/bin/env python3
"""Claude Code status line: model / context / tokens / cache hit rate / cost.
按 session_id 把每轮用量累加到本地状态文件，显示【当前对话】的累计数据；
新开对话（新 session_id）自动从零累计。缓存读取 token 单独计费，不混入输入。
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


# DeepSeek V4 定价（元 / 百万 token），2026-07 起施行峰谷定价
PRICES = {
    "pro":   {"in": 3.0, "out": 6.0, "cache": 0.025},
    "flash": {"in": 1.0, "out": 2.0, "cache": 0.02},
}


def is_peak_hour():
    """高峰时段（北京时间 9:00-12:00、14:00-18:00）价格为平时 2 倍"""
    now = datetime.now(timezone(timedelta(hours=8)))
    return now.hour in (9, 10, 11, 14, 15, 16, 17)


def calc_cost(model_name, cur_in, cache_read, cache_create, cur_out):
    """费用：新输入 + 缓存读取（低价） + 缓存写入 + 输出"""
    key = "flash" if "flash" in model_name.lower() else "pro"
    price = PRICES[key]
    mult = 2.0 if is_peak_hour() else 1.0
    raw = (cur_in + cache_create) * price["in"] + cache_read * price["cache"] + cur_out * price["out"]
    return raw * mult / 1_000_000


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
if used_pct is not None:
    parts.append(f"ctx:{used_pct:.0f}%")

if s["in"] + s["out"] > 0:
    parts.append(f"tok:{fmt_k(s['in'])}+{fmt_k(s['out'])}")

total_cur = s["in"] + s["cache_read"] + s["cache_create"]
if total_cur > 0:
    rate = s["cache_read"] * 100 / total_cur
    parts.append(f"cache:{rate:.0f}%")

cost = calc_cost(model, s["in"], s["cache_read"], s["cache_create"], s["out"])
if cost > 0:
    parts.append(f"cost:¥{cost:.3f}" if cost < 1 else f"cost:¥{cost:.2f}")

print(f"[{model} {' '.join(parts)}]".replace(" ]", "]"))
