#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站UP主动态监控脚本 - WBI签名版本
使用WBI签名和buvid cookie绕过反爬虫
"""

import requests
import hashlib
import time
import json
import os
import sys
import random
from functools import reduce
from urllib.parse import urlencode

# ===== WBI签名 =====
MIXIN_KEY_ENC_TAB = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]


def get_mixin_key(orig: str) -> str:
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]


def enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = get_mixin_key(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time
    params = dict(sorted(params.items()))
    params = {
        k: ''.join(filter(lambda ch: ch not in "!'()*", str(v)))
        for k, v in params.items()
    }
    query = urlencode(params)
    wbi_sign = hashlib.md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = wbi_sign
    return params


class BiliMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/126.0.0.0 Safari/537.36',
                'Referer': 'https://space.bilibili.com/',
                'Origin': 'https://space.bilibili.com',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'sec-ch-ua': '"Chromium";v="126", "Google Chrome";v="126", "Not-A.Brand";v="8"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
            }
        )
        self.img_key = ''
        self.sub_key = ''

    def init_cookies(self):
        """获取buvid3/buvid4指纹cookie"""
        try:
            resp = self.session.get(
                'https://api.bilibili.com/x/frontend/finger/spi', timeout=10
            )
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                b_3 = data.get('b_3', '')
                b_4 = data.get('b_4', '')
                self.session.cookies.set('buvid3', b_3, domain='.bilibili.com')
                self.session.cookies.set('buvid4', b_4, domain='.bilibili.com')
                print(f"[OK] buvid3={b_3[:20]}...")
                return True
            else:
                print(f"[WARN] 获取buvid失败: HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] 获取buvid异常: {e}")
            return False

    def load_extra_cookie(self):
        """加载额外的B站cookie（可选，增强反爬能力）"""
        cookie_str = os.environ.get('BILI_COOKIE', '')
        if cookie_str:
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    self.session.cookies.set(
                        key.strip(), value.strip(), domain='.bilibili.com'
                    )
            print("[OK] 已加载额外BILI_COOKIE")

    def get_wbi_keys(self):
        """获取WBI签名密钥"""
        try:
            resp = self.session.get(
                'https://api.bilibili.com/x/web-interface/nav', timeout=10
            )
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                wbi_img = data.get('wbi_img', {})
                img_url = wbi_img.get('img_url', '')
                sub_url = wbi_img.get('sub_url', '')
                if '/' in img_url and '/' in sub_url:
                    self.img_key = img_url.rsplit('/', 1)[1].split('.')[0]
                    self.sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
                    print(f"[OK] WBI keys获取成功")
                    return True
            print(f"[WARN] WBI获取失败: HTTP {resp.status_code}")
            return False
        except Exception as e:
            print(f"[ERROR] WBI获取异常: {e}")
            return False

    def get_dynamics(self, uid: str):
        """获取UP主动态列表"""
        params = {
            'host_mid': uid,
            'timezone_offset': -480,
            'platform': 'web',
            'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote',
        }

        signed_params = enc_wbi(params, self.img_key, self.sub_key)
        url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'

        try:
            resp = self.session.get(url, params=signed_params, timeout=15)
            print(f"  [API] uid={uid} HTTP={resp.status_code}")

            if resp.status_code == 412:
                print("  [!] 412错误 - 被反爬拦截，请配置BILI_COOKIE")
                return []

            if resp.status_code != 200:
                print(f"  [!] 异常响应: {resp.text[:200]}")
                return []

            data = resp.json()
            if data.get('code') != 0:
                print(
                    f"  [!] API错误: code={data.get('code')} msg={data.get('message')}"
                )
                return []

            items = data.get('data', {}).get('items', [])
            return items

        except Exception as e:
            print(f"  [ERROR] 请求异常: {e}")
            return []

    def extract_text_content(self, item):
        """从动态中提取文字内容，无文字返回空字符串"""
        modules = item.get('modules', {})
        dynamic_module = modules.get('module_dynamic', {})
        text_parts = []

        # 1. 从 desc 提取（纯文字动态、图文动态的文字部分）
        desc = dynamic_module.get('desc', {})
        if desc:
            rich_text_nodes = desc.get('rich_text_nodes', [])
            if rich_text_nodes:
                for node in rich_text_nodes:
                    orig_text = node.get('orig_text', '') or node.get('text', '')
                    if orig_text:
                        text_parts.append(orig_text)
            elif desc.get('text'):
                text_parts.append(desc['text'])

        # 2. 从 major.opus 提取（新版opus格式）
        major = dynamic_module.get('major', {})
        if major:
            opus = major.get('opus', {})
            if opus:
                # opus summary
                summary = opus.get('summary', {})
                if summary:
                    rich_text_nodes = summary.get('rich_text_nodes', [])
                    if rich_text_nodes:
                        for node in rich_text_nodes:
                            orig_text = node.get('orig_text', '') or node.get(
                                'text', ''
                            )
                            if orig_text:
                                text_parts.append(orig_text)
                    elif summary.get('text'):
                        text_parts.append(summary['text'])
                # opus title
                title = opus.get('title', '')
                if title:
                    text_parts.insert(0, f"【{title}】")

            # major.article（专栏）
            article = major.get('article', {})
            if article:
                title = article.get('title', '')
                desc_text = article.get('desc', '')
                if title:
                    text_parts.append(f"【专栏】{title}")
                if desc_text:
                    text_parts.append(desc_text)

        # 合并去重
        full_text = '\n'.join(text_parts).strip()
        return full_text

    def process_dynamics(self, items, up_name):
        """处理动态列表，返回有文字的动态"""
        results = []
        for item in items:
            dynamic_id = item.get('id_str', '')
            dynamic_type = item.get('type', '')

            # 跳过视频和直播类型
            if dynamic_type in (
                'DYNAMIC_TYPE_AV',
                'DYNAMIC_TYPE_LIVE_RCMD',
                'DYNAMIC_TYPE_LIVE',
                'DYNAMIC_TYPE_PGC',
            ):
                continue

            text = self.extract_text_content(item)

            if not text:
                continue

            # 获取发布时间
            author_module = item.get('modules', {}).get('module_author', {})
            pub_ts = author_module.get('pub_ts', 0)
            pub_time = ''
            if pub_ts:
                try:
                    pub_ts_int = int(pub_ts)
                    pub_time = time.strftime('%m-%d %H:%M', time.localtime(pub_ts_int))
                except (ValueError, TypeError):
                    pub_time = str(pub_ts)

            results.append(
                {
                    'id': dynamic_id,
                    'type': dynamic_type,
                    'text': text,
                    'pub_time': pub_time,
                    'pub_ts': pub_ts,
                    'up_name': up_name,
                    'url': f'https://www.bilibili.com/opus/{dynamic_id}',
                }
            )

        return results


def send_wechat(send_key, title, content):
    """通过Server酱推送微信消息"""
    url = f'https://sctapi.ftqq.com/{send_key}.send'
    data = {
        'title': title[:100],
        'desp': content,
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        result = resp.json()
        if result.get('code') == 0:
            print(f"  [推送成功] {send_key[:8]}...")
        else:
            print(f"  [推送失败] {send_key[:8]}... msg={result.get('message')}")
        return result.get('code') == 0
    except Exception as e:
        print(f"  [推送异常] {e}")
        return False


def load_sent_ids():
    """加载已发送的动态ID列表"""
    try:
        with open('sent_ids.json', 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def load_last_check_time():
    """加载上次检测时间"""
    try:
        with open('last_check_time.txt', 'r') as f:
            timestamp = float(f.read().strip())
            return timestamp
    except (FileNotFoundError, ValueError):
        # 默认使用2026-06-29 17:00:00 UTC+8 (2026-06-29 09:00:00 UTC)
        return 1751289600  # 2026-06-29 09:00:00 UTC


def save_last_check_time(timestamp):
    """保存上次检测时间"""
    with open('last_check_time.txt', 'w') as f:
        f.write(str(timestamp))


def save_sent_ids(ids):
    """保存已发送的动态ID（保留最新300条）"""
    with open('sent_ids.json', 'w') as f:
        json.dump(ids[-300:], f, ensure_ascii=False)


def main():
    print("=" * 50)
    print(f"[启动] B站动态监控 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 读取配置
    up_list_str = os.environ.get('UP_LIST', '')
    send_keys_str = os.environ.get('SEND_KEYS', '')
    monitor_names_str = os.environ.get(
        'MONITOR_NAMES', ''
    )  # 可选：指定要监控的UP主名称

    if not up_list_str or not send_keys_str:
        print("[ERROR] 环境变量 UP_LIST 或 SEND_KEYS 未配置")
        sys.exit(1)

    up_list = json.loads(up_list_str)
    send_keys = json.loads(send_keys_str)

    # 如果指定了MONITOR_NAMES，只监控指定的UP主
    if monitor_names_str:
        monitor_names = [name.strip() for name in monitor_names_str.split(',')]
        up_list = [up for up in up_list if up['name'] in monitor_names]
        print(f"[过滤] 只监控: {', '.join(monitor_names)}")

    print(f"[配置] 监控UP主: {len(up_list)}个, 推送目标: {len(send_keys)}个")

    # 加载已发送记录和上次检测时间
    sent_ids = load_sent_ids()
    last_check_time = load_last_check_time()
    current_time = time.time()

    print(f"[状态] 已有发送记录: {len(sent_ids)}条")
    print(
        f"[时间] 上次检测: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_check_time))}"
    )
    print(
        f"[时间] 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}"
    )

    # 初始化监控器
    monitor = BiliMonitor()
    monitor.load_extra_cookie()

    if not monitor.init_cookies():
        print("[WARN] buvid获取失败，继续尝试...")
    time.sleep(1)

    if not monitor.get_wbi_keys():
        print("[ERROR] WBI密钥获取失败，无法继续")
        sys.exit(1)
    time.sleep(1)

    # 检查每个UP主
    all_new = []

    for up in up_list:
        uid = up['uid']
        name = up['name']
        print(f"\n{'─' * 40}")
        print(f"[检查] {name} (uid={uid})")

        items = monitor.get_dynamics(uid)
        print(f"  获取到 {len(items)} 条动态")

        if items:
            text_dynamics = monitor.process_dynamics(items, name)
            print(f"  其中含文字的: {len(text_dynamics)} 条")

            for d in text_dynamics:
                # 只推送上次检测时间之后的新动态
                try:
                    pub_ts_float = float(d['pub_ts'])
                    if pub_ts_float > last_check_time and d['id'] not in sent_ids:
                        all_new.append(d)
                        print(f"  [新] {d['id']} | {d['text'][:40]}...")
                except (ValueError, TypeError):
                    continue

        # 随机延迟 2-4 秒，避免固定间隔被识别
        random_delay = random.uniform(2, 4)
        print(f"  [安全] 随机延迟 {random_delay:.1f} 秒")
        time.sleep(random_delay)

    # 推送新动态
    print(f"\n{'─' * 40}")
    print(f"[汇总] 发现 {len(all_new)} 条新动态需要推送")

    for d in all_new:
        title = f"{d['up_name']}发布新动态"
        content = (
            f"**{d['up_name']}** · {d['pub_time']}\n\n"
            f"---\n\n"
            f"{d['text']}\n\n"
            f"---\n\n"
            f"🔗 [点击查看原文]({d['url']})"
        )

        print(f"\n[推送] {title}")
        for key in send_keys:
            send_wechat(key, title, content)
            time.sleep(1)

        sent_ids.append(d['id'])

    # 保存状态
    save_sent_ids(sent_ids)
    save_last_check_time(current_time)
    print(f"\n[完成] 已保存发送记录，当前共 {len(sent_ids)} 条")


if __name__ == '__main__':
    main()
