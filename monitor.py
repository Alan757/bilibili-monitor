#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站UP主动态监控脚本
监控指定UP主的文字帖子，过滤纯图片帖子，通过微信推送
"""

import requests
import json
import time
import hashlib
from datetime import datetime
import sys

# B站API配置
BILIBILI_API = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"

# 请求头，模拟浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://space.bilibili.com/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def get_up_dynamics(uid):
    """
    获取UP主的动态列表
    :param uid: UP主的用户ID
    :return: 动态列表
    """
    params = {
        'host_mid': uid,
        'offset': '',
        'timezone_offset': '-480',
        'platform': 'web',
        'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote',
    }

    try:
        response = requests.get(
            BILIBILI_API, params=params, headers=HEADERS, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data['code'] == 0:
            return data['data']['items']
        else:
            print(f"获取动态失败: {data.get('message', '未知错误')}")
            return []
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return []


def is_text_post(item):
    """
    判断是否为文字帖子（排除纯图片帖子）
    :param item: 动态项
    :return: True表示是文字帖子，False表示纯图片帖子
    """
    try:
        modules = item.get('modules', {})
        major_module = modules.get('module_dynamic', {}).get('major', {})

        # 如果有draw模块（图片），检查是否有opus模块（文字）
        has_draw = 'draw' in major_module
        has_opus = 'opus' in major_module

        # 如果有draw但没有opus，说明是纯图片帖子
        if has_draw and not has_opus:
            return False

        # 如果有opus，说明是文字帖子
        if has_opus:
            return True

        # 其他情况（如转发、视频等）也返回True，让用户自己判断
        return True

    except Exception as e:
        print(f"判断帖子类型失败: {str(e)}")
        return False


def extract_text_content(item):
    """
    提取文字内容
    :param item: 动态项
    :return: 文字内容字典
    """
    try:
        modules = item.get('modules', {})
        major_module = modules.get('module_dynamic', {}).get('major', {})

        content = {
            'title': '',
            'text': '',
            'publish_time': '',
            'dynamic_id': item.get('id_str', ''),
            'url': f"https://t.bilibili.com/{item.get('id_str', '')}",
        }

        # 提取opus（图文/文字）内容
        if 'opus' in major_module:
            opus = major_module['opus']
            content['title'] = opus.get('title', '')
            content['text'] = opus.get('summary', {}).get('text', '')
            content['publish_time'] = opus.get('pub_time', '')

        # 如果没有opus，尝试从其他模块提取
        if not content['text']:
            desc_module = modules.get('module_dynamic', {}).get('desc', {})
            content['text'] = desc_module.get('text', '')
            content['publish_time'] = item.get('pub_time', '')

        return content

    except Exception as e:
        print(f"提取内容失败: {str(e)}")
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
            # Server酱 API
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

    # 从环境变量读取UP主列表
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

    # 加载配置
    config = load_config()
    up_list = config.get('up_list', [])
    send_keys = config.get('send_keys', [])

    if not up_list:
        print("错误: 配置文件中没有UP主信息")
        sys.exit(1)

    if not send_keys:
        print("错误: 配置文件中没有SendKey信息")
        sys.exit(1)

    # 加载历史记录
    sent_ids = load_history()
    new_sent_ids = set()

    # 监控每个UP主
    for up in up_list:
        uid = up.get('uid')
        name = up.get('name', f'UID:{uid}')

        print(f"\n正在监控: {name} (UID: {uid})")

        # 获取动态
        dynamics = get_up_dynamics(uid)

        if not dynamics:
            print(f"  未获取到动态")
            continue

        print(f"  获取到 {len(dynamics)} 条动态")

        # 处理每条动态
        for item in dynamics:
            dynamic_id = item.get('id_str', '')

            # 跳过已发送的
            if dynamic_id in sent_ids:
                continue

            # 判断是否为文字帖子
            if not is_text_post(item):
                print(f"  ⊘ 跳过纯图片帖子: {dynamic_id}")
                continue

            # 提取内容
            content = extract_text_content(item)
            if not content:
                continue

            # 格式化消息
            message = format_message(content, name)

            # 发送微信通知
            print(f"  ✓ 发现新文字帖子: {content.get('title', '无标题')}")
            if send_wechat_notification(message, send_keys):
                new_sent_ids.add(dynamic_id)
                print(f"  ✓ 已推送")
            else:
                print(f"  ✗ 推送失败")

    # 保存历史记录
    if new_sent_ids:
        sent_ids.update(new_sent_ids)
        save_history(sent_ids)
        print(f"\n✓ 本次推送 {len(new_sent_ids)} 条新动态")
    else:
        print(f"\n✓ 没有新动态需要推送")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监控完成")


if __name__ == "__main__":
    main()
