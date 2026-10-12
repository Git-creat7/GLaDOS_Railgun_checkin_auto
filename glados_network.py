#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLaDOS Network 专用签到脚本 (优先请求 glados.network 域名)
"""
from glados import run_checkin

# glados.network 域名优先列表
NETWORK_DOMAINS = [
    "https://glados.network",
    "https://glados.cloud",
    "https://glados.rocks",
]

def start():
    # 优先读取 GLADOS_NETWORK_COOKIE，未配置时自动回退读取 GLADOS_COOKIE
    run_checkin(domains=NETWORK_DOMAINS, cookie_env_priority="network")

if __name__ == '__main__':
    start()
