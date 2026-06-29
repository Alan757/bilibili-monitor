# 如何获取BILI_COOKIE（关键步骤）

## 为什么需要BILI_COOKIE？

B站API返回412错误是因为缺少认证信息。`BILI_COOKIE`包含你的B站登录凭证，能有效绕过反爬虫。

---

## 获取步骤

### 方法1：使用浏览器开发者工具（推荐）

1. **打开Chrome浏览器，访问B站并登录**
   - 访问 https://www.bilibili.com
   - 确保你已经登录了B站账号

2. **打开开发者工具**
   - 按 `F12` 键
   - 或右键 → "检查"

3. **切换到Network标签**
   - 点击顶部的 "Network" 标签

4. **刷新页面**
   - 按 `F5` 刷新B站页面

5. **找到任意请求**
   - 在Network列表中点击任意一个请求（比如第一个）

6. **复制Cookie**
   - 在右侧找到 "Request Headers"
   - 找到 `Cookie:` 字段
   - 复制整个Cookie值（很长一串）

7. **精简Cookie（可选）**
   - 如果Cookie太长，可以只保留关键字段：
   ```
   SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; buvid3=xxx; buvid4=xxx
   ```

### 方法2：使用浏览器控制台（更简单）

1. **登录B站后，按F12打开开发者工具**

2. **切换到Console标签**

3. **输入以下命令并回车**：
   ```javascript
   document.cookie
   ```

4. **复制输出的内容**

---

## 配置到GitHub Secrets

1. **进入你的GitHub仓库**
   - https://github.com/Alan757/bilibili-monitor

2. **点击 Settings → Secrets and variables → Actions**

3. **点击 "New repository secret"**

4. **填写信息**：
   - **Name**: `BILI_COOKIE`
   - **Value**: 粘贴你刚才复制的Cookie值

5. **点击 "Add secret"**

---

## Cookie示例格式

完整的Cookie类似这样（非常长）：
```
SESSDATA=abc123def456; bili_jct=xyz789; DedeUserID=12345678; buvid3=ABCDEF123456789; buvid4=XYZ123; ...
```

**关键字段说明**：
- `SESSDATA` - 登录凭证（必需）
- `bili_jct` - CSRF令牌（必需）
- `DedeUserID` - 你的B站UID（必需）
- `buvid3` / `buvid4` - 浏览器指纹（必需）

---

## 测试配置

配置完BILI_COOKIE后：

1. 进入仓库的 **Actions** 标签
2. 选择 "B站动态监控" 工作流
3. 点击 **Run workflow** → **Run workflow**
4. 查看运行日志

**成功标志**：
- 看到 `[OK] buvid3=...`
- 看到 `[OK] WBI keys获取成功`
- 看到 `[API] uid=xxx HTTP=200`（而不是412）
- 成功获取到动态列表

**如果还是412**：
- 说明Cookie可能过期或不完整
- 重新登录B站获取新的Cookie
- 确保Cookie包含所有关键字段

---

## 注意事项

⚠️ **Cookie是敏感信息**：
- 不要分享给他人
- 定期更新（B站Cookie会过期）
- 如果推送失败，首先检查Cookie是否有效

⚠️ **GitHub Secrets是安全的**：
- 加密存储
- 不会在日志中显示
- 只有仓库管理员可见

---

## 备选方案

如果无法获取Cookie，可以：

1. **使用自建RSSHub**（最稳定）
2. **使用代理**（在Secrets中添加PROXY_URL）
3. **使用Cloudflare Worker中转**

需要这些方案的详细说明吗？