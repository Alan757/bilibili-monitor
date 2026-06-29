# GitHub Secrets 配置说明

## 需要配置的Secrets

进入你的GitHub仓库：https://github.com/Alan757/bilibili-monitor

点击 **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

---

## Secret 1: UP_LIST

**Name**: `UP_LIST`

**Value** (JSON格式):
```json
[
  {
    "uid": "3546610447419885",
    "name": "股市里的猩猩"
  },
  {
    "uid": "470672214",
    "name": "鳄鱼派"
  }
]
```

**说明**:
- `uid`: B站UP主的用户ID（从主页URL中获取）
- `name`: UP主显示名称（自定义）

---

## Secret 2: SEND_KEYS

**Name**: `SEND_KEYS`

**Value** (JSON格式):
```json
[
  "SCT_你的第一个SendKey",
  "SCT_你的第二个SendKey"
]
```

**说明**:
- 每个接收者需要一个SendKey
- 从 https://sct.ftqq.com 获取
- 需要关注Server酱公众号才能接收推送

---

## 获取SendKey步骤

1. 访问 https://sct.ftqq.com
2. 使用GitHub账号登录
3. 在首页复制你的SendKey
4. 微信搜索"Server酱"公众号并关注
5. 第二个接收者需要单独注册一个GitHub账号获取另一个SendKey

---

## 当前代码使用的接口（供参考）

### 已尝试但失败的接口：

1. **B站官方API**
   ```
   https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space
   ```
   状态: 412错误（需要特殊处理）

2. **B站动态页面**
   ```
   https://space.bilibili.com/{uid}/dynamic
   ```
   状态: 412错误（反爬虫）

3. **RSSHub公共服务**
   ```
   https://rsshub.app/bilibili/user/dynamic/{uid}
   ```
   状态: 403错误（被拒绝）

### 正常工作的接口：

**微信推送（Server酱）**
```
https://sctapi.ftqq.com/{SendKey}.send
```
状态: ✅ 正常

---

## 如果你要修改代码

### 关键函数：`get_up_dynamics(uid)`

这个函数负责获取B站动态，目前所有方案都失败。

### 可能的解决方案：

1. **自建RSSHub服务**
   - 在Railway.app、Vercel或自己的服务器上部署
   - 修改代码中的RSSHUB地址

2. **使用B站移动端API**
   - 可能需要添加cookie或token
   - 在Secrets中添加B站登录凭证

3. **使用浏览器自动化**
   - Playwright或Selenium
   - 在GitHub Actions中可能不稳定

4. **使用第三方数据服务**
   - 寻找其他提供B站数据的API

### 需要添加的Secrets（如果使用新方案）：

如果需要添加cookie或token，可以创建新的Secret：
- Name: `BILIBILI_COOKIE`
- Value: 你的B站登录cookie

---

## 测试方法

配置完Secrets后：

1. 进入仓库的 **Actions** 标签
2. 选择 "B站动态监控" 工作流
3. 点击 "Run workflow" 手动运行
4. 查看运行日志

---

## 注意事项

- Secrets的值是加密的，不会显示在日志中
- 修改Secrets后，下次运行工作流会自动生效
- 如果推送失败，检查Server酱公众号是否已关注