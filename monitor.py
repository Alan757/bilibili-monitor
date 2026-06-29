#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站UP主动态监控脚本 - RSSHub版本
使用RSSHub服务获取B站动态，避免反爬虫问题
"""

import requests
import json
import time
import hashlib
from datetime import datetime
import sys
import feedparser

# RSSHub服务地址（公共实例）
RSSHUB_BASE = "https://rsshub.app"
# B站用户动态RSS格式
RSS_URL = f"{RSSHUB_BASE}/bilibili/user/dynamic/{{uid}}"

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml',
}


def get_up_dynamics(uid):
    """
    通过RSSHub获取UP主的动态
    :param uid: UP主的用户ID
    :return: 动态列表
    """
    dynamics = []

    try:
        url = RSS_URL.format(uid=uid)
        print(f"  正在获取RSS: {url}")

        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        # 解析RSS feed
        feed = feedparser.parse(response.content)

        if not feed.entries:
            print(f"  未找到动态条目")
            return dynamics

        print(f"  找到 {len(feed.entries)} 条动态")

        for entry in feed.entries[:10]:  # 只处理前10条
            try:
                dynamic_data = parse_rss_entry(entry, uid)
                if dynamic_data:
                    dynamics.append(dynamic_data)
            except Exception as e:
                continue

    except Exception as e:
        print(f"  请求异常: {str(e)}")

    return dynamics


def parse_rss_entry(entry, uid):
    """
    解析RSS条目
    :param entry: feedparser条目
    :param uid: UP主UID
    :return: 动态数据字典
    """
    try:
        # 获取标题和内容
        title = entry.get('title', '')
        content = entry.get('summary', entry.get('description', ''))

        # 清理HTML标签
        from bs4 import BeautifulSoup

        if content:
            soup = BeautifulSoup(content, 'lxml')
            content = soup.get_text(strip=True)

        # 获取发布时间
        pub_time = ''
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_time = datetime(*entry.published_parsed[:6]).strftime(
                '%Y-%m-%d %H:%M:%S'
            )
        elif hasattr(entry, 'published'):
            pub_time = entry.published

        # 获取链接
        link = entry.get('link', f'https://space.bilibili.com/{uid}/dynamic')

        # 生成唯一ID
        dynamic_id = hashlib.md5(link.encode()).hexdigest()

        # 判断是否有内容
        if not content and not title:
            return None

        return {
            'id_str': dynamic_id,
            'title': title,
            'text': content,
            'pub_time': pub_time,
            'url': link,
        }
    except Exception as e:
        print(f"  解析条目失败: {str(e)}")
        return None


def is_text_post(item):
    """
    判断是否为文字帖子
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
