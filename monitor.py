#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站UP主动态监控脚本 - 网页抓取版本
监控指定UP主的文字帖子，过滤纯图片帖子，通过微信推送
"""

import requests
import json
import time
import hashlib
from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re

# B站动态页面URL
DYNAMIC_URL = "https://space.bilibili.com/{uid}/dynamic"

# 请求头，模拟真实浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def get_up_dynamics(uid):
    """
    通过网页抓取获取UP主的动态列表
    :param uid: UP主的用户ID
    :return: 动态列表
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    dynamics = []

    try:
        # 访问动态页面
        url = DYNAMIC_URL.format(uid=uid)
        print(f"  正在访问: {url}")

        response = session.get(url, timeout=15)
        response.raise_for_status()

        # 解析HTML
        soup = BeautifulSoup(response.text, 'lxml')

        # 查找动态卡片 - B站动态页面的结构
        # 动态通常在 <div class="card"> 或类似的容器中
        dynamic_cards = soup.find_all('div', class_='card')

        if not dynamic_cards:
            # 尝试其他可能的选择器
            dynamic_cards = soup.find_all('div', {'data-type': 'dynamic'})

        if not dynamic_cards:
            # 尝试查找包含动态内容的元素
            dynamic_cards = soup.find_all('div', class_='bili-dyn-item')

        print(f"  找到 {len(dynamic_cards)} 个动态卡片")

        for card in dynamic_cards[:10]:  # 只处理前10条
            try:
                dynamic_data = parse_dynamic_card(card, uid)
                if dynamic_data:
                    dynamics.append(dynamic_data)
            except Exception as e:
                continue

        # 如果还是没找到，尝试从页面源码中提取JSON数据
        if not dynamics:
            dynamics = extract_from_page_source(response.text, uid)

    except Exception as e:
        print(f"  请求异常: {str(e)}")

    return dynamics


def parse_dynamic_card(card, uid):
    """
    解析动态卡片
    :param card: BeautifulSoup元素
    :param uid: UP主UID
    :return: 动态数据字典
    """
    try:
        # 尝试提取动态ID
        dynamic_id = ''
        id_attr = card.get('data-did') or card.get('data-id') or card.get('id', '')
        if id_attr:
            dynamic_id = str(id_attr)

        # 尝试提取内容
        text_content = ''
        title = ''

        # 查找文本内容
        text_elem = card.find('div', class_='text') or card.find('p', class_='text')
        if text_elem:
            text_content = text_elem.get_text(strip=True)

        # 查找标题
        title_elem = (
            card.find('h4') or card.find('h3') or card.find('a', class_='title')
        )
        if title_elem:
            title = title_elem.get_text(strip=True)

        # 查找时间
        pub_time = ''
        time_elem = card.find('span', class_='time') or card.find(
            'div', class_='publish-time'
        )
        if time_elem:
            pub_time = time_elem.get_text(strip=True)

        if not text_content and not title:
            return None

        return {
            'id_str': dynamic_id
            or hashlib.md5(f"{uid}_{time.time()}".encode()).hexdigest(),
            'title': title,
            'text': text_content,
            'pub_time': pub_time,
            'url': (
                f"https://t.bilibili.com/{dynamic_id}"
                if dynamic_id
                else f"https://space.bilibili.com/{uid}/dynamic"
            ),
        }
    except:
        return None


def extract_from_page_source(html, uid):
    """
    从页面源码中提取动态数据
    :param html: 页面HTML
    :param uid: UP主UID
    :return: 动态列表
    """
    dynamics = []

    try:
        # 查找包含动态数据的JSON
        # B站通常在页面中嵌入JSON数据
        json_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        matches = re.findall(json_pattern, html)

        if matches:
            import json

            data = json.loads(matches[0])

            # 尝试从数据结构中提取动态
            if 'dynamic' in data:
                items = data['dynamic'].get('list', [])
                for item in items[:10]:
                    try:
                        dynamic = {
                            'id_str': str(item.get('id', '')),
                            'title': item.get('title', ''),
                            'text': item.get('description', item.get('content', '')),
                            'pub_time': item.get('pub_time', item.get('pubDate', '')),
                            'url': f"https://t.bilibili.com/{item.get('id', '')}",
                        }
                        if dynamic['text'] or dynamic['title']:
                            dynamics.append(dynamic)
                    except:
                        continue
    except Exception as e:
        print(f"  从页面源码提取失败: {str(e)}")

    return dynamics


def is_text_post(item):
    """
    判断是否为文字帖子（排除纯图片帖子）
    :param item: 动态项
    :return: True表示是文字帖子
    """
    try:
        text = item.get('text', '')
        title = item.get('title', '')

        # 如果有文字内容或标题，认为是文字帖子
        if text or title:
            return True

        return False
    except:
        return True


def extract_text_content(item):
    """
    提取文字内容
    :param item: 动态项
    :return: 文字内容字典
    """
    try:
        content = {
            'title': item.get('title', ''),
            'text': item.get('text', ''),
            'publish_time': item.get('pub_time', ''),
            'dynamic_id': item.get('id_str', ''),
            'url': item.get('url', ''),
        }
        return content
    except:
        return None


def format_message(content, up_name):
    """
    格式化推送消息
    :param content: 内容字典
    :param up_name: UP主名称
    :return: 格式化后的消息
    """
    title = content.get('title', '无标题')
    text = content.get('text', '')
    pub_time = content.get('publish_time', '')
    url = content.get('url', '')

    # 截断过长的文本
    if len(text) > 200:
        text = text[:200] + "..."

    message = f"📢 B站动态提醒\n\n"
    message += f"UP主: {up_name}\n"
    message += f"标题: {title}\n"
    message += f"时间: {pub_time}\n"
    message += f"\n内容:\n{text}\n"
    message += f"\n🔗 查看原文: {url}"

    return message


def send_wechat_notification(message, send_keys):
    """
    发送微信通知（使用Server酱）
    :param message: 消息内容
    :param send_keys: SendKey列表
    :return: 是否发送成功
    """
    success = True

    for send_key in send_keys:
        try:
            url = f"https://sctapi.ftqq.com/{send_key}.send"
            payload = {'title': 'B站动态监控', 'desp': message}

            response = requests.post(url, data=payload, timeout=10)
            result = response.json()

            if result.get('code') == 0:
                print(f"✓ 微信推送成功 (SendKey: {send_key[:8]}...)")
            else:
                print(
                    f"✗ 微信推送失败 (SendKey: {send_key[:8]}...): {result.get('message', '未知错误')}"
                )
                success = False

        except Exception as e:
            print(f"✗ 微信推送异常 (SendKey: {send_key[:8]}...): {str(e)}")
            success = False

    return success


def load_config():
    """
    从环境变量加载配置
    :return: 配置字典
    """
    import os

    up_list_json = os.environ.get('UP_LIST', '[]')
    send_keys_json = os.environ.get('SEND_KEYS', '[]')

    try:
        up_list = json.loads(up_list_json)
        send_keys = json.loads(send_keys_json)

        return {'up_list': up_list, 'send_keys': send_keys}
    except json.JSONDecodeError as e:
        print(f"错误: 环境变量配置格式错误: {str(e)}")
        sys.exit(1)


def load_history():
    """
    加载已发送的历史记录
    :return: 已发送的动态ID集合
    """
    try:
        with open('history.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('sent_ids', []))
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError:
        return set()


def save_history(sent_ids):
    """
    保存已发送的历史记录
    :param sent_ids: 已发送的动态ID集合
    """
    try:
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump({'sent_ids': list(sent_ids)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史记录失败: {str(e)}")


def main():
    """
    主函数
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始监控B站动态...")

    config = load_config()
    up_list = config.get('up_list', [])
    send_keys = config.get('send_keys', [])

    if not up_list:
        print("错误: 配置文件中没有UP主信息")
        sys.exit(1)

    if not send_keys:
        print("错误: 配置文件中没有SendKey信息")
        sys.exit(1)

    sent_ids = load_history()
    new_sent_ids = set()

    for up in up_list:
        uid = up.get('uid')
        name = up.get('name', f'UID:{uid}')

        print(f"\n正在监控: {name} (UID: {uid})")

        dynamics = get_up_dynamics(uid)

        if not dynamics:
            print(f"  未获取到动态")
            continue

        print(f"  获取到 {len(dynamics)} 条动态")

        for item in dynamics:
            dynamic_id = item.get('id_str', '')

            if dynamic_id in sent_ids:
                continue

            if not is_text_post(item):
                print(f"  ⊘ 跳过纯图片帖子: {dynamic_id}")
                continue

            content = extract_text_content(item)
            if not content:
                continue

            message = format_message(content, name)

            print(f"  ✓ 发现新文字帖子: {content.get('title', '无标题')}")
            if send_wechat_notification(message, send_keys):
                new_sent_ids.add(dynamic_id)
                print(f"  ✓ 已推送")
            else:
                print(f"  ✗ 推送失败")

    if new_sent_ids:
        sent_ids.update(new_sent_ids)
        save_history(sent_ids)
        print(f"\n✓ 本次推送 {len(new_sent_ids)} 条新动态")
    else:
        print(f"\n✓ 没有新动态需要推送")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监控完成")


if __name__ == "__main__":
    main()
