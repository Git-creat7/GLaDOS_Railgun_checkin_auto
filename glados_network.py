import requests, json, os, re

# -------------------------------------------------------------------------------------------
# 配置部分
# -------------------------------------------------------------------------------------------
sckey = os.environ.get("PUSHPLUS_TOKEN", "")
sendContent = ''
all_get_points = []

# glados.network 账号 cookie，多个账号用 & 分隔
cookies = os.environ.get("GLADOS_NETWORK_COOKIE", "").split("&")

if not cookies or cookies[0] == "":
    print('未获取到 GLADOS_NETWORK_COOKIE 变量')
    exit(0)

def start():
    global sendContent, all_get_points

    url = "https://glados.network/api/user/checkin"
    url2 = "https://glados.network/api/user/status"
    referer = 'https://glados.network/console/checkin'
    origin = "https://glados.network"

    # 更新了 User-Agent，防止被识别为旧脚本
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # 【关键修改】这里必须对应当前的域名后缀
    payload = {'token': 'glados.network'}

    for cookie in cookies:
        cookie = cookie.strip()
        if not cookie:
            continue
        try:
            checkin = requests.post(
                url,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent,
                    'content-type': 'application/json;charset=UTF-8'
                },
                data=json.dumps(payload),
                timeout=20
            )
            state = requests.get(
                url2,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent
                },
                timeout=20
            )

            # 调试输出：如果报错，取消下面这行的注释查看服务器返回的具体内容
            # print(f"Checkin Response: {checkin.text}")

            if checkin.status_code != 200:
                print(f"请求失败，状态码: {checkin.status_code}")
                continue

            state_json = state.json()
            checkin_json = checkin.json()

            # 容错处理：防止 state 接口获取失败导致报错
            if 'data' in state_json:
                email = state_json['data']['email']
                time_str = state_json['data']['leftDays'].split('.')[0]
            else:
                email = "未知账号"
                time_str = "未知"

            if 'message' in checkin_json:
                mess = checkin_json['message']

                # --- 提取今日点数 ---
                point_get = "0"
                # 优先尝试从 list 中读取（新版 API）
                if 'list' in checkin_json and len(checkin_json['list']) > 0:
                    try:
                        change = checkin_json['list'][0]['change']
                        point_get = str(int(float(change)))
                    except:
                        pass

                # 如果上面失败，尝试从 message 正则匹配
                if point_get == "0":
                    # 兼容中文和英文的 "Get 10 Points" 或 "获得 10 点"
                    current_get = re.findall(r"(?:Get|获得)\s*(\d+)", mess)
                    if current_get:
                        point_get = current_get[0]

                all_get_points.append(f"{point_get}点")

                # --- 获取总余额 ---
                balance_str = "----总点数(未知)"
                if 'list' in checkin_json and len(checkin_json['list']) > 0:
                    try:
                        balance = str(checkin_json['list'][0]['balance']).split('.')[0]
                        balance_str = f"----总点数({balance})"
                    except:
                        pass

                info = f"{email}----{mess}--本次获得:{point_get}点{balance_str}--剩余({time_str})天"
                print(info)
                sendContent += info + '\n'
            else:
                sendContent += f" 签到失败，返回内容异常: {checkin_json}\n"

        except Exception as e:
            print(f"账号处理出错: {e}")
            continue

    # --- 推送逻辑部分 ---
    push_title = "glados.network签到通知"
    if all_get_points:
        push_title = f"glados.network签到获得: {', '.join(all_get_points)}"

    if sckey != "":
        push_url = 'http://www.pushplus.plus/send'
        data = {"token": sckey, "title": push_title, "content": sendContent, "template": "txt"}
        try:
            requests.post(push_url, data=json.dumps(data), headers={'Content-Type':'application/json'}, timeout=20)
            print("推送已发出")
        except Exception as e:
            print(f"推送失败: {e}")
    else:
        print("未配置 PUSHPLUS_TOKEN，跳过推送")

if __name__ == '__main__':
    start()
