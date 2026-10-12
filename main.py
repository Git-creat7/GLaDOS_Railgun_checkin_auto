#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚合签到脚本：同时执行 GLaDOS 与 Railgun 签到，合并所有账号结果并通过 PushPlus 统一推送一次。
"""
import os
import sys
import json
import re
import requests
from glados import GLaDOSClient, extract_cookie, NORMAL_CHECKIN_MESSAGES

# 修复 Windows 控制台编码
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def checkin_glados(cookie: str):
    """执行单个 GLaDOS 账号签到"""
    client = GLaDOSClient(cookie)
    checkin_res = client.checkin()

    msg = checkin_res.get("message", "签到请求失败") if checkin_res else "网络连接失败"
    code = checkin_res.get("code") if checkin_res else -1
    is_success = (code == 0) or any(norm in str(msg).lower() for norm in NORMAL_CHECKIN_MESSAGES)

    client.get_status()
    client.get_points()

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

    balance_str = client.points if client.points != "0" else "未知"
    if checkin_res and isinstance(checkin_res.get("list"), list) and len(checkin_res["list"]) > 0:
        try:
            b = checkin_res["list"][0].get("balance")
            if b is not None:
                balance_str = str(b).split(".")[0]
        except Exception:
            pass

    return {
        "site": "GLaDOS",
        "email": client.email,
        "is_success": is_success,
        "msg": msg,
        "point_get": point_get,
        "balance": balance_str,
        "left_days": client.left_days
    }


def checkin_railgun(cookie: str):
    """执行单个 Railgun 账号签到"""
    url = "https://railgun.info/api/user/checkin"
    url2 = "https://railgun.info/api/user/status"
    headers = {
        "cookie": cookie,
        "referer": "https://railgun.info/console/checkin",
        "origin": "https://railgun.info",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "content-type": "application/json;charset=UTF-8",
    }
    payload = {"token": "railgun.one"}

    try:
        checkin_resp = requests.post(url, headers=headers, json=payload, timeout=20)
        state_resp = requests.get(url2, headers=headers, timeout=20)

        if checkin_resp.status_code != 200 or state_resp.status_code != 200:
            return {
                "site": "Railgun",
                "email": "未知账号",
                "is_success": False,
                "msg": f"HTTP失败 checkin={checkin_resp.status_code}, status={state_resp.status_code}",
                "point_get": "0",
                "balance": "未知",
                "left_days": "未知"
            }

        state_json = state_resp.json()
        checkin_json = checkin_resp.json()

        email = state_json.get("data", {}).get("email", "未知账号")
        time_str = str(state_json.get("data", {}).get("leftDays", "未知")).split(".")[0]
        mess = checkin_json.get("message", "签到成功")
        is_success = checkin_json.get("code") in (0, 1) or "checked in" in str(mess).lower() or "logged" in str(mess).lower()

        point_get = "0"
        if isinstance(checkin_json.get("list"), list) and len(checkin_json["list"]) > 0:
            try:
                point_get = str(int(float(checkin_json["list"][0].get("change", 0))))
            except Exception:
                pass
        if point_get == "0":
            m = re.findall(r"(?:Get|获得)\s*(\d+)", str(mess))
            if m:
                point_get = m[0]

        balance_str = "未知"
        if isinstance(checkin_json.get("list"), list) and len(checkin_json["list"]) > 0:
            try:
                balance_str = str(checkin_json["list"][0].get("balance", "未知")).split(".")[0]
            except Exception:
                pass

        return {
            "site": "Railgun",
            "email": email,
            "is_success": is_success,
            "msg": mess,
            "point_get": point_get,
            "balance": balance_str,
            "left_days": time_str
        }
    except Exception as e:
        return {
            "site": "Railgun",
            "email": "未知账号",
            "is_success": False,
            "msg": f"请求异常: {e}",
            "point_get": "0",
            "balance": "未知",
            "left_days": "未知"
        }


def run_all():
    sckey = os.environ.get("PUSHPLUS_TOKEN", "").strip()

    # 1. 获取所有 GLaDOS Cookie
    glados_raw = os.environ.get("GLADOS_COOKIE", "").strip()
    glados_cookies = []
    if glados_raw:
        sep = "&" if "&" in glados_raw else "\n"
        glados_cookies = [extract_cookie(c) for c in glados_raw.split(sep) if extract_cookie(c)]

    # 2. 获取所有 Railgun Cookie
    railgun_raw = os.environ.get("RAILGUN_COOKIE", "").strip()
    railgun_cookies = []
    if railgun_raw:
        sep = "&" if "&" in railgun_raw else "\n"
        railgun_cookies = [extract_cookie(c) for c in railgun_raw.split(sep) if extract_cookie(c)]

    total_accounts = len(glados_cookies) + len(railgun_cookies)
    if total_accounts == 0:
        print("未检测到任何账号 Cookie，请配置 GLADOS_COOKIE 或 RAILGUN_COOKIE")
        return 1

    print(f"=== 聚合签到开始：GLaDOS {len(glados_cookies)} 个账号，Railgun {len(railgun_cookies)} 个账号 ===")

    all_results = []
    success_count = 0

    # 执行 GLaDOS 签到
    for idx, c in enumerate(glados_cookies, 1):
        print(f"--> 执行 GLaDOS 账号 {idx}...")
        res = checkin_glados(c)
        all_results.append(res)
        if res["is_success"]:
            success_count += 1
        print(f"    [{res['site']}] {res['email']} | 结果: {res['msg']} | 获得: {res['point_get']}点 | 剩余: {res['left_days']}天")

    # 执行 Railgun 签到
    for idx, c in enumerate(railgun_cookies, 1):
        print(f"--> 执行 Railgun 账号 {idx}...")
        res = checkin_railgun(c)
        all_results.append(res)
        if res["is_success"]:
            success_count += 1
        print(f"    [{res['site']}] {res['email']} | 结果: {res['msg']} | 获得: {res['point_get']}点 | 剩余: {res['left_days']}天")

    # 格式化聚合推送内容
    content_lines = []
    for r in all_results:
        icon = "✅" if r["is_success"] else "❌"
        content_lines.append(
            f"{icon} [{r['site']}] {r['email']}\n"
            f"   结果: {r['msg']}\n"
            f"   获得: {r['point_get']}点 | 总点数: {r['balance']} | 剩余: {r['left_days']}天\n"
        )

    send_content = "\n".join(content_lines)
    points_summary = [f"{r['point_get']}点" for r in all_results]
    push_title = ", ".join(points_summary) if points_summary else "0点"

    # PushPlus 统一聚合推送
    if sckey:
        try:
            push_url = "http://www.pushplus.plus/send"
            push_data = {
                "token": sckey,
                "title": push_title,
                "content": send_content,
                "template": "txt"
            }
            resp = requests.post(push_url, json=push_data, headers={"Content-Type": "application/json"}, timeout=15)
            print(f"PushPlus 聚合推送状态: {resp.status_code}")
        except Exception as e:
            print(f"PushPlus 聚合推送异常: {e}")
    else:
        print("未配置 PUSHPLUS_TOKEN，跳过推送")

    return 0 if success_count == total_accounts else 1


if __name__ == '__main__':
    sys.exit(run_all())
