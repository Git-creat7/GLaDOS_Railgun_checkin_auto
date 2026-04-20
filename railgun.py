import requests, json, os, re

# pushplus秘钥（可与原任务共用）
sckey = os.environ.get("PUSHPLUS_TOKEN", "")
sendContent = ''
all_get_points = []

# railgun 账号 cookie，多个账号用 & 分隔
cookies = os.environ.get("RAILGUN_COOKIE", "").split("&")

if not cookies or cookies[0] == "":
    print('未获取到 RAILGUN_COOKIE 变量')
    exit(0)

def start():
    global sendContent, all_get_points

    # railgun 域名与接口
    # 如果后续发现接口路径不同，只需要改这两行
    url = "https://railgun.info/api/user/checkin"
    url2 = "https://railgun.info/api/user/status"

    referer = "https://railgun.info/console/checkin"
    origin = "https://railgun.info"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    payload = {"token": "glados.one"}

    push_title = "Railgun签到结果"

    for cookie in cookies:
        cookie = cookie.strip()
        if not cookie:
            continue
        try:
            checkin = requests.post(
                url,
                headers={
                    "cookie": cookie,
                    "referer": referer,
                    "origin": origin,
                    "user-agent": useragent,
                    "content-type": "application/json;charset=UTF-8",
                },
                data=json.dumps(payload),
                timeout=20
            )
            state = requests.get(
                url2,
                headers={
                    "cookie": cookie,
                    "referer": referer,
                    "origin": origin,
                    "user-agent": useragent
                },
                timeout=20
            )

            if checkin.status_code != 200 or state.status_code != 200:
                msg = f"请求失败 checkin={{checkin.status_code}}, status={{state.status_code}}"
                print(msg)
                sendContent += msg + "\n"
                continue

            state_json = state.json()
            checkin_json = checkin.json()

            email = state_json.get("data", {}).get("email", "未知账号")
            time_str = str(state_json.get("data", {}).get("leftDays", "未知")).split(".")[0]

            mess = checkin_json.get("message", f"签到返回: {{checkin_json}}")

            # 尝试提取本次获得点数
            point_get = "0"
            if isinstance(checkin_json.get("list"), list) and len(checkin_json["list"]) > 0:
                try:
                    point_get = str(int(float(checkin_json["list"][0].get("change", 0))))
                except:
                    pass

            if point_get == "0":
                m = re.findall(r"(?:Get|获得)\s*(\d+)", str(mess))
                if m:
                    point_get = m[0]

            # 尝试提取总余额
            balance_str = "总点数(未知)"
            if isinstance(checkin_json.get("list"), list) and len(checkin_json["list"]) > 0:
                try:
                    balance = str(checkin_json["list"][0].get("balance", "未知")).split(".")[0]
                    balance_str = f"总点数({balance})"
                except:
                    pass

            all_get_points.append(f"{point_get}点")
            info = f"{email}----{mess}--本次获得:{point_get}点--{balance_str}--剩余({time_str})天"
            print(info)
            sendContent += info + "\n"

        except Exception as e:
            err = f"账号处理出错: {{e}}"
            print(err)
            sendContent += err + "\n"
            continue

    if all_get_points:
        push_title = f"Railgun签到获得: {{', '.join(all_get_points)}}"

    if sckey:
        push_url = "http://www.pushplus.plus/send"
        data = {"token": sckey, "title": push_title, "content": sendContent, "template": "txt"}
        try:
            requests.post(push_url, data=json.dumps(data), headers={"Content-Type": "application/json"}, timeout=20)
            print("推送已发出")
        except Exception as e:
            print(f"推送失败: {{e}}")
    else:
        print("未配置 PUSHPLUS_TOKEN，跳过推送")

if __name__ == "__main__":
    start()