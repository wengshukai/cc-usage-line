#!/usr/bin/env python3
"""Claude Code status line: model / context / tokens / cache hit rate.
读取 Claude Code 传入的 JSON，显示模型名、上下文使用率、会话 token 用量、缓存命中率。
"""
import json
import sys
from datetime import datetime, timedelta, timezone

# Windows 下强制 UTF-8 输出，避免 ¥ 等符号因 GBK 报错
sys.stdout.reconfigure(encoding="utf-8")

try:
    data = json.load(sys.stdin)
except Exception:
    print("[cache:--%]")
    sys.exit(0)

model = (data.get("model") or {}).get("display_name") or "Unknown"

cw = data.get("context_window") or {}
used_pct = cw.get("used_percentage")
total_in = cw.get("total_input_tokens") or 0
total_out = cw.get("total_output_tokens") or 0

# 当前轮次的缓存数据（DeepSeek 自动上下文缓存会映射到这里）
cu = cw.get("current_usage") or {}
cur_in = cu.get("input_tokens") or 0
cache_read = cu.get("cache_read_input_tokens") or 0
cache_create = cu.get("cache_creation_input_tokens") or 0


def fmt_k(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


# DeepSeek V4 定价（元 / 百万 token），2026-07 起施行峰谷定价
PRICES = {
    "pro":   {"in": 3.0, "out": 6.0},
    "flash": {"in": 1.0, "out": 2.0},
}


def is_peak_hour():
    """高峰时段（北京时间 9:00-12:00、14:00-18:00）价格为平时 2 倍"""
    now = datetime.now(timezone(timedelta(hours=8)))
    return now.hour in (9, 10, 11, 14, 15, 16, 17)


def calc_cost(model_name, total_in, total_out):
    key = "flash" if "flash" in model_name.lower() else "pro"
    price = PRICES[key]
    mult = 2.0 if is_peak_hour() else 1.0
    return (total_in * price["in"] + total_out * price["out"]) * mult / 1_000_000


parts = []
if used_pct is not None:
    parts.append(f"ctx:{used_pct:.0f}%")
if total_in + total_out > 0:
    parts.append(f"tok:{fmt_k(total_in)}+{fmt_k(total_out)}")

# 缓存命中率 = 缓存读取 / (本次输入 + 缓存读取 + 缓存写入)
total_cur = cur_in + cache_read + cache_create
if total_cur > 0:
    rate = cache_read * 100 / total_cur
    parts.append(f"cache:{rate:.0f}%")

cost = calc_cost(model, total_in, total_out)
if cost > 0:
    parts.append(f"cost:¥{cost:.3f}" if cost < 1 else f"cost:¥{cost:.2f}")

print(f"[{model} {' '.join(parts)}]".replace(" ]", "]"))
