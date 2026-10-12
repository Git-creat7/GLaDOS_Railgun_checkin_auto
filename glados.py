#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import time
from urllib.parse import urlparse
import requests

# 修复 Windows 控制台中文编码
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -------------------------------------------------------------------------------------------
# 常量与配置
# -------------------------------------------------------------------------------------------
DOMAINS = [
    "https://glados.cloud",
    "https://glados.rocks",
    "https://glados.network",
]

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

BASE_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

NORMAL_CHECKIN_MESSAGES = (
    "checkin! got",
    "checkin repeats! please try tomorrow",
    "today's observation logged",
)

CURRENT_SESSION_COOKIES = ("gld:sess", "gld:sess.sig")
LEGACY_SESSION_COOKIES = ("koa:sess", "koa:sess.sig")

EXCHANGE_PLANS = {
    "plan100": {"points": 100, "days": 10},
    "plan200": {"points": 200, "days": 30},
    "plan500": {"points": 500, "days": 100},
}
EXCHANGE_DISABLED_VALUES = ("", "off", "no", "none", "false", "0", "disabled")


# -------------------------------------------------------------------------------------------
# Cookie 与 Header 工具函数
# -------------------------------------------------------------------------------------------
def extract_cookie(raw: str):
    """提取并清洗 Cookie，支持原始字符串、带 Cookie: 前缀及 Cookie-Editor JSON 格式"""
    if not raw:
        return None
    raw = raw.strip()
    raw = re.sub(r'^(?:cookie|Cookie)\s*:\s*', '', raw)

    # 包含已知 session key 的常规 header 字符串
    if any(f"{name}=" in raw for name in CURRENT_SESSION_COOKIES + LEGACY_SESSION_COOKIES):
        return raw

    # Cookie-Editor 导出的 JSON 格式
    if raw.startswith(("[", "{")):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                pairs = []
                for item in parsed:
                    if isinstance(item, dict):
                        name = item.get("name")
                        val = item.get("value")
                        if name and val is not None:
                            pairs.append(f"{name}={val}")
                return "; ".join(pairs) if pairs else None
            elif isinstance(parsed, dict) and "token" in parsed:
                return f"koa:sess={parsed['token']}"
        except Exception:
            return None

    return raw


def get_cookie_names(cookie_str: str):
    """获取 Cookie 所有的 key 集合"""
    names = set()
    for item in cookie_str.split(";"):
        k, sep, _ = item.strip().partition("=")
        if sep and k:
            names.add(k)
    return names


def get_session_cookie_kind(cookie_str: str):
    """判断 Cookie 会话格式：新版 gld 或旧版 koa"""
    names = get_cookie_names(cookie_str)
    if set(CURRENT_SESSION_COOKIES).issubset(names):
        return "gld"
    if set(LEGACY_SESSION_COOKIES).issubset(names):
        return "koa"
    return None


def get_browser_headers(user_agent: str = None):
    """生成包含 Client Hints 的浏览器请求头，防止被识别为机器人"""
    ua = (user_agent or os.environ.get("GLADOS_USER_AGENT", "").strip() or DEFAULT_USER_AGENT).strip()
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = ua

    chrome = re.search(r'(?:Chrome|Chromium)/(\d+)', ua)
    if chrome:
        major = chrome.group(1)
        platform = "Windows"
        if "Macintosh" in ua:
            platform = "macOS"
        elif "Android" in ua:
            platform = "Android"
        elif "Linux" in ua:
            platform = "Linux"

        headers.update({
            "Sec-CH-UA": f'"Chromium";v="{major}", "Google Chrome";v="{major}", "Not_A Brand";v="99"',
            "Sec-CH-UA-Mobile": "?1" if "Mobile" in ua else "?0",
            "Sec-CH-UA-Platform": f'"{platform}"',
        })
    return headers


# -------------------------------------------------------------------------------------------
# GLaDOS 客户端
# -------------------------------------------------------------------------------------------
class GLaDOSClient:
    def __init__(self, cookie: str, domains=None):
        self.cookie = cookie
        self.domains = domains or DOMAINS
        self.working_domain = self.domains[0]
        self.email = "未知账号"
        self.left_days = "未知"
        self.points = "0"
        self.points_change = "0"
        self.session_kind = get_session_cookie_kind(cookie)

    def _request(self, method: str, path: str, payload=None, form=False, timeout=15):
        for domain in self.domains:
            try:
                url = f"{domain}{path}"
                headers = get_browser_headers()
                headers["Cookie"] = self.cookie
                headers["Origin"] = domain
                headers["Referer"] = f"{domain}/console/checkin"

                if form:
                    headers.pop("Content-Type", None)
                    resp = requests.post(url, headers=headers, data=payload, timeout=timeout)
                elif method.upper() == "GET":
                    resp = requests.get(url, headers=headers, timeout=timeout)
                else:
                    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

                if resp.status_code == 200:
                    self.working_domain = domain
                    try:
                        return resp.json()
                    except Exception:
                        return {"code": -1, "message": f"返回非JSON数据: {resp.text[:100]}"}
                elif resp.status_code in (401, 403):
                    try:
                        return resp.json()
                    except Exception:
                        return {"code": -2, "message": f"HTTP {resp.status_code} 权限拒绝"}
            except Exception as e:
                # 尝试下一个镜像域名
                continue
        return None

    def checkin(self):
        """执行签到，动态使用当前域名的 token"""
        for domain in self.domains:
            token = urlparse(domain).netloc or "glados.cloud"
            res = self._request("POST", "/api/user/checkin", payload={"token": token})
            if res is not None:
                return res
        return {"code": -1, "message": "所有镜像域名网络请求失败"}

    def get_status(self):
        """获取账号状态（邮箱、剩余天数）"""
        res = self._request("GET", "/api/user/status")
        if res and isinstance(res.get("data"), dict):
            data = res["data"]
            self.email = str(data.get("email", "未知账号"))
            self.left_days = str(data.get("leftDays", "未知")).split(".")[0]
            return True
        return False

    def get_points(self):
        """获取当前积分及最近变动"""
        res = self._request("GET", "/api/user/points")
        if res and "points" in res:
            self.points = str(res.get("points", "0")).split(".")[0]
            history = res.get("history", [])
            if history and isinstance(history[0], dict):
                change = str(history[0].get("change", "0")).split(".")[0]
                self.points_change = ("+" + change) if not change.startswith("-") else change
            return True
        return False

    def exchange(self, plan_type: str):
        """积分兑换会员天数"""
        return self._request("POST", "/api/user/exchange", payload={"planType": plan_type}, form=True)


# -------------------------------------------------------------------------------------------
# 主流程
# -------------------------------------------------------------------------------------------
def run_checkin(domains=None, cookie_env_priority=None):
    if cookie_env_priority == "network":
        raw_cookie = os.environ.get("GLADOS_NETWORK_COOKIE", "").strip() or os.environ.get("GLADOS_COOKIE", "").strip()
    else:
        raw_cookie = os.environ.get("GLADOS_COOKIE", "").strip() or os.environ.get("GLADOS_NETWORK_COOKIE", "").strip()

    if not raw_cookie:
        print("未获取到 GLADOS_COOKIE (或 GLADOS_NETWORK_COOKIE) 环境变量")
        return "未获取到环境变量"

    # 分割多账号（支持换行符或 &）
    if "&" in raw_cookie:
        raw_list = raw_cookie.split("&")
    else:
        raw_list = raw_cookie.split("\n")

    cookies = [extract_cookie(item) for item in raw_list if extract_cookie(item)]
    if not cookies:
        print("未解析到有效的 Cookie，请检查配置")
        return "未解析到有效Cookie"

    sckey = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    exchange_plan_env = os.environ.get("EXCHANGE_PLAN", "off").strip().lower()
    auto_exchange_enabled = exchange_plan_env not in EXCHANGE_DISABLED_VALUES and exchange_plan_env in EXCHANGE_PLANS

    send_lines = []
    all_points_gained = []
    success_count = 0

    print(f"=== 开始 GLaDOS 签到，共检测到 {len(cookies)} 个账号 ===")

    for idx, cookie in enumerate(cookies, 1):
        client = GLaDOSClient(cookie, domains=domains)

        # 检查 Cookie 是否包含新版认证凭证
        if client.session_kind != "gld":
            warning_msg = (
                f"【账号{idx}警告】Cookie 未包含完整的 gld:sess 与 gld:sess.sig！\n"
                f"GLaDOS 2026年9月更新后，旧版 koa:sess 或残缺 Cookie 会被服务器拒绝并返回“没有权限”。\n"
                f"若本次签到失败，请在浏览器重新登录 GLaDOS，重新获取完整 Cookie 并更新 GitHub Secrets。"
            )
            print(warning_msg)

        # 执行签到重试逻辑 (最多3次)
        checkin_res = None
        for attempt in range(1, 4):
            checkin_res = client.checkin()
            if not checkin_res:
                time.sleep(2)
                continue

            msg = str(checkin_res.get("message", ""))
            code = checkin_res.get("code")

            # 正常签到成功或当日已签到
            if code == 0 or any(norm in msg.lower() for norm in NORMAL_CHECKIN_MESSAGES):
                break

            # 致命认证错误不重试
            if code == -2 or "没有权限" in msg or "device-mismatch" in str(checkin_res.get("reason", "")):
                break

            time.sleep(2)

        # 获取状态与积分详情
        client.get_status()
        client.get_points()

        # 解析签到结果
        msg = checkin_res.get("message", "签到请求失败") if checkin_res else "网络连接失败"
        code = checkin_res.get("code") if checkin_res else -1
        reason = checkin_res.get("reason", "") if checkin_res else ""

        is_success = (code == 0) or any(norm in str(msg).lower() for norm in NORMAL_CHECKIN_MESSAGES)

        # 提取本次获得点数
        point_get = "0"
        if checkin_res and isinstance(checkin_res.get("list"), list) and len(checkin_res["list"]) > 0:
            try:
                change = checkin_res["list"][0].get("change", 0)
                point_get = str(int(float(change)))
            except Exception:
                pass

        if point_get == "0":
            m = re.findall(r"(?:Get|获得)\s*(\d+)", str(msg))
            if m:
                point_get = m[0]

        # 提取总点数
        balance_str = client.points if client.points != "0" else "未知"
        if checkin_res and isinstance(checkin_res.get("list"), list) and len(checkin_res["list"]) > 0:
            try:
                b = checkin_res["list"][0].get("balance")
                if b is not None:
                    balance_str = str(b).split(".")[0]
            except Exception:
                pass

        # 错误诊断信息
        diag = ""
        if not is_success:
            if "没有权限" in str(msg) or code == -2:
                diag = " [诊断: Cookie无效或过期，未包含2026新版 gld:sess 签名，请重新登录官网抓取最新完整Cookie]"
            elif reason == "device-mismatch" or "device" in str(msg).lower():
                diag = " [诊断: 设备指纹不匹配，请在Secrets添加 GLADOS_USER_AGENT 填入您浏览器的真实User-Agent]"

        # 自动兑换积分 (如果开启)
        exchange_info = ""
        if is_success and auto_exchange_enabled:
            plan = EXCHANGE_PLANS[exchange_plan_env]
            try:
                cur_pts = int(float(client.points))
                if cur_pts >= plan["points"]:
                    ex_res = client.exchange(exchange_plan_env)
                    if ex_res and ex_res.get("code") == 0:
                        client.get_status()
                        client.get_points()
                        exchange_info = f" [自动兑换成功: 消耗{plan['points']}点兑换{plan['days']}天]"
                        print(f"账号 {client.email}{exchange_info}")
            except Exception as e:
                print(f"自动兑换出错: {e}")

        # 格式化输出
        if is_success:
            success_count += 1
            all_points_gained.append(f"{point_get}点")
            line = f"{client.email}----{msg}--本次获得:{point_get}点----总点数({balance_str})--剩余({client.left_days})天{exchange_info}"
        else:
            line = f"{client.email}----签到失败: {msg}{diag}--剩余({client.left_days})天"

        print(line)
        send_lines.append(line)

    # 微信 PushPlus 推送
    send_content = "\n".join(send_lines)
    push_title = ", ".join(all_points_gained) if all_points_gained else "0点"

    if sckey:
        try:
            push_url = "http://www.pushplus.plus/send"
            push_data = {
                "token": sckey,
                "title": push_title,
                "content": send_content,
                "template": "txt"
            }
            res = requests.post(push_url, json=push_data, headers={"Content-Type": "application/json"}, timeout=15)
            print(f"推送状态: {res.status_code}")
        except Exception as e:
            print(f"推送异常: {e}")
    else:
        print("未配置 PUSHPLUS_TOKEN，跳过推送")

    return send_content


def start():
    run_checkin()


if __name__ == "__main__":
    start()
