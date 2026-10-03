#!/usr/bin/env python3
"""安装 Claude Code 状态栏：复制脚本到 ~/.claude/ 并配置 settings.json。"""
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CLAUDE_DIR = os.path.expanduser("~/.claude")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statusline.py")
DST = os.path.join(CLAUDE_DIR, "statusline.py")
SETTINGS = os.path.join(CLAUDE_DIR, "settings.json")


def main():
    if not os.path.isdir(CLAUDE_DIR):
        print(f"[x] 未找到 {CLAUDE_DIR}，请先安装并运行一次 Claude Code")
        return 1

    # 1. 复制脚本
    shutil.copyfile(SRC, DST)
    print(f"[√] 已复制脚本 -> {DST}")

    # 2. 读取现有 settings.json
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}
    except json.JSONDecodeError:
        print(f"[x] {SETTINGS} 不是合法 JSON，请先手动修复后再运行")
        return 1

    # 3. 备份原配置
    if os.path.exists(SETTINGS):
        shutil.copyfile(SETTINGS, SETTINGS + ".bak")
        print(f"[√] 已备份原配置 -> {SETTINGS}.bak")

    # 4. 写入 statusLine 配置（正斜杠路径，与 Claude Code 惯例一致）
    settings["statusLine"] = {
        "type": "command",
        "command": "python " + DST.replace("\\", "/"),
    }
    with open(SETTINGS, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[√] 已更新 {SETTINGS} 的 statusLine 配置")
    print()
    print("安装完成，重启 Claude Code 后生效。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
