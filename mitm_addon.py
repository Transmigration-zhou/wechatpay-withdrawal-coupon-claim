"""mitmproxy addon: 自动提取微信小程序「提现笔笔省」请求里的 session-token，写入 .env。

启动方式：
    mitmdump -s mitm_addon.py

mitmproxy 默认监听 8080 端口。Mac 系统代理或微信网络代理指向 127.0.0.1:8080 即可。
"""

import re
from pathlib import Path
from mitmproxy import http, ctx

TARGET_HOST = "discount.wxpapp.wechatpay.cn"
ENV_PATH = Path(__file__).resolve().parent / ".env"
ENV_KEY = "SESSION_TOKEN"

_last_token: str | None = None


def _update_env(token: str) -> None:
    """把 SESSION_TOKEN 写入 .env，保留其它行。"""
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    pattern = re.compile(rf"^\s*{ENV_KEY}\s*=")
    replaced = False
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{ENV_KEY}={token}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{ENV_KEY}={token}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def request(flow: http.HTTPFlow) -> None:
    if flow.request.pretty_host != TARGET_HOST:
        return

    token = flow.request.headers.get("session-token")
    if not token:
        return

    global _last_token
    if token == _last_token:
        return

    _last_token = token
    _update_env(token)
    ctx.log.info(f"[token-capture] 已更新 SESSION_TOKEN ({len(token)} chars) from {flow.request.pretty_url}")
