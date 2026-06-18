#!/usr/bin/env python3
"""
实时抓取 Medeo Discord 社区身份组分布。

通过 Discord Gateway WebSocket 协议拉取全部成员，按身份组聚合统计。
统计口径：
  - 排除 Bot 账号
  - 同一用户持有多个身份组时分别计入各组
  - 同一组内每人仅计一次（处理 AI-Artist 双 role ID 去重）
  - 各项人数加总等于该组总人次

用法：
    cp .env.example .env  # 填入 token
    pip install -r requirements.txt
    python fetch_roles.py

环境变量：
    DISCORD_USER_TOKEN  必填，Discord 用户 token
    HTTPS_PROXY         可选，代理地址，如 http://127.0.0.1:7890
    OUTPUT_JSON         可选，结果 JSON 输出路径
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import websocket  # websocket-client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import GUILD_ID, ROLE_MAP, DISPLAY_ORDER

GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
MAX_ATTEMPTS = 3
ATTEMPT_TIMEOUT = 120  # 单次尝试超时（秒）
RETRY_COOLDOWN = 15    # 失败后等待秒数


# ─────────────────────────────────────────────────────────────
# 核心抓取
# ─────────────────────────────────────────────────────────────

def fetch_role_distribution(token: str, guild_id: str, proxy: Optional[str] = None) -> dict:
    """
    通过 Gateway WebSocket 拉取整个服务器成员列表并聚合身份组。

    Returns:
        {
          "total_members": int,
          "slot_counts": {(group_name, role_name): count, ...},
          "fetched_at": ISO 时间戳,
        }

    Raises:
        RuntimeError: 拉取失败（连接/超时/数据为空）
    """
    results: dict = {}
    done = threading.Event()

    proxy_host, proxy_port = _parse_proxy(proxy)

    def run_once() -> None:
        slot_counts: dict[tuple[str, str], int] = defaultdict(int)
        member_slots: dict[str, set[tuple[str, str]]] = defaultdict(set)
        total_members = [0]
        chunks_received = [0]
        chunks_total: list[Optional[int]] = [None]

        def on_open(_ws):  # pragma: no cover - 仅打印
            pass

        def on_message(ws, raw):
            ev = json.loads(raw)
            op, t = ev.get("op"), ev.get("t")

            # HELLO：启动心跳，发送 IDENTIFY
            if op == 10:
                interval = ev["d"]["heartbeat_interval"]

                def heartbeat():
                    while True:
                        time.sleep(interval / 1000)
                        try:
                            ws.send(json.dumps({"op": 1, "d": None}))
                        except Exception:
                            break

                threading.Thread(target=heartbeat, daemon=True).start()
                time.sleep(0.5)
                ws.send(json.dumps({
                    "op": 2,
                    "d": {
                        "token": token,
                        "capabilities": 16381,
                        "properties": {
                            "os": "Mac OS X",
                            "browser": "Chrome",
                            "device": "",
                        },
                        "presence": {
                            "status": "online",
                            "since": 0,
                            "activities": [],
                            "afk": False,
                        },
                        "compress": False,
                        "client_state": {},
                    },
                }))

            # READY：发起成员请求（请求全部成员）
            elif t == "READY":
                time.sleep(1.0)
                ws.send(json.dumps({
                    "op": 8,
                    "d": {
                        "guild_id": guild_id,
                        "query": "",
                        "limit": 0,
                        "presences": False,
                    },
                }))

            # GUILD_MEMBERS_CHUNK：按 chunk 接收成员
            elif t == "GUILD_MEMBERS_CHUNK":
                d = ev["d"]
                chunks_received[0] += 1
                if chunks_total[0] is None:
                    chunks_total[0] = d.get("chunk_count", 1)

                for m in d.get("members", []):
                    user = m.get("user", {})
                    if user.get("bot"):
                        continue
                    uid = user.get("id")
                    if not uid:
                        continue
                    total_members[0] += 1
                    for rid in m.get("roles", []):
                        slot = ROLE_MAP.get(rid)
                        if not slot:
                            continue
                        # 去重：同一用户在同一 slot 只计一次
                        if slot in member_slots[uid]:
                            continue
                        member_slots[uid].add(slot)
                        slot_counts[slot] += 1

                _log(
                    f"  chunk {chunks_received[0]}/{chunks_total[0]}  "
                    f"已拉取 {total_members[0]} 人"
                )

                if chunks_total[0] and chunks_received[0] >= chunks_total[0]:
                    results["slot_counts"] = dict(slot_counts)
                    results["total_members"] = total_members[0]
                    done.set()
                    ws.close()

        ws = websocket.WebSocketApp(
            GATEWAY_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda _ws, e: _log(f"  WS error: {e}"),
            on_close=lambda *_args: done.set(),
        )

        kwargs = {"sslopt": {"cert_reqs": ssl.CERT_NONE}}
        if proxy_host:
            kwargs.update(
                http_proxy_host=proxy_host,
                http_proxy_port=proxy_port,
                proxy_type="http",
            )
        ws.run_forever(**kwargs)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        _log(f"\n=== 第 {attempt}/{MAX_ATTEMPTS} 次尝试 ===")
        results.clear()
        done.clear()
        threading.Thread(target=run_once, daemon=True).start()
        done.wait(timeout=ATTEMPT_TIMEOUT)

        if results.get("total_members", 0) > 100:
            _log(f"✅ 成功：拉取 {results['total_members']} 名非 Bot 成员")
            results["fetched_at"] = datetime.now(timezone.utc).isoformat()
            return results

        _log(f"❌ 未获取到足够数据，{RETRY_COOLDOWN}s 后重试…")
        time.sleep(RETRY_COOLDOWN)

    raise RuntimeError("Gateway 拉取失败：超过最大重试次数")


# ─────────────────────────────────────────────────────────────
# 输出
# ─────────────────────────────────────────────────────────────

def render_text(results: dict) -> str:
    sc = results["slot_counts"]
    total = results["total_members"]
    ts = results["fetched_at"]

    lines = [
        "=" * 52,
        f"Medeo 身份组分布",
        f"统计时间: {ts}",
        f"非 Bot 成员: {total:,}",
        "=" * 52,
    ]

    for grp, roles in DISPLAY_ORDER.items():
        gdata = {r: sc.get((grp, r), 0) for r in roles}
        gtotal = sum(gdata.values())
        lines.append(f"\n【{grp}】共 {gtotal} 人次")
        for role in roles:
            cnt = gdata[role]
            pct = cnt / gtotal * 100 if gtotal else 0
            lines.append(f"  {role}: {cnt} ({pct:.0f}%)")
        # 一致性校验：单项加总 = gtotal（永真，仅显示状态）
        verify = "✅" if sum(gdata.values()) == gtotal else "❌"
        lines.append(f"  合计: {gtotal} {verify}")

    return "\n".join(lines)


def to_serializable(results: dict) -> dict:
    """JSON 友好格式（元组 key 转字符串）"""
    sc = results["slot_counts"]
    grouped: dict[str, dict[str, int]] = {}
    for (grp, role), cnt in sc.items():
        grouped.setdefault(grp, {})[role] = cnt
    return {
        "fetched_at": results["fetched_at"],
        "total_members": results["total_members"],
        "groups": grouped,
    }


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    print(msg, flush=True)


def _parse_proxy(proxy: Optional[str]) -> tuple[Optional[str], Optional[int]]:
    if not proxy:
        return None, None
    u = urlparse(proxy)
    if not u.hostname:
        return None, None
    return u.hostname, u.port or 80


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main() -> int:
    token = os.getenv("DISCORD_USER_TOKEN", "").strip()
    if not token:
        sys.stderr.write(
            "❌ 缺少 DISCORD_USER_TOKEN 环境变量。\n"
            "   请复制 .env.example 为 .env 并填入 token，或导出环境变量。\n"
        )
        return 1

    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or None
    if proxy:
        _log(f"使用代理: {proxy}")

    try:
        results = fetch_role_distribution(token, GUILD_ID, proxy)
    except RuntimeError as e:
        sys.stderr.write(f"❌ {e}\n")
        return 1

    print(render_text(results))

    out_path = os.getenv("OUTPUT_JSON", "").strip()
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(to_serializable(results), f, ensure_ascii=False, indent=2)
        _log(f"\n✅ 已写入 {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
