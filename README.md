# B站UP主动态监控

一个基于GitHub Actions的B站UP主文字帖子监控工具，自动过滤纯图片帖子，通过微信推送通知。

## 功能特性

- ✅ 监控多个B站UP主的动态
- ✅ 自动过滤纯图片帖子，只推送文字内容
- ✅ 通过微信Server酱推送通知
- ✅ 基于GitHub Actions，无需后台服务
- ✅ 自动记录已推送历史，避免重复推送
- ✅ 支持手动触发和定时自动运行

## 准备工作

### 1. 获取B站UP主的UID

1. 打开B站，访问UP主的主页
2. 查看浏览器地址栏，URL格式为：`https://space.bilibili.com/UID`
3. 复制URL中的数字部分，即为UID

**示例**：`https://space.bilibili.com/12345678`，UID就是 `12345678`

### 2. 获取微信推送SendKey

本项目使用[Server酱](https://sct.ftqq.com/)进行微信推送：

1. 访问 [Server酱官网](https://sct.ftqq.com/)
2. 使用GitHub账号登录
3. 在"SendKey"页面复制你的SendKey
4. **每个接收微信的用户都需要单独注册并获取自己的SendKey**

**重要**：你需要为两个接收者分别获取SendKey。

## 部署步骤

### 步骤1：创建GitHub仓库

1. 登录GitHub
2. 创建一个新的**公开仓库**（Public Repository）
3. 仓库名可以自定义，例如：`bilibili-monitor`

### 步骤2：上传代码到GitHub

**方法一：使用Git命令行**

```bash
# 进入项目目录
cd bilibili-monitor

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/bilibili-monitor.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

**方法二：使用GitHub网页上传**

1. 进入你创建的仓库
2. 点击 "Add file" -> "Upload files"
3. 上传以下文件：
   - `monitor.py`
   - `requirements.txt`
   - `.github/workflows/bilibili-monitor.yml`
   - `.gitignore`
4. 点击 "Commit changes"

### 步骤3：配置GitHub Secrets（敏感信息）

**这是关键步骤，所有敏感信息都通过Secrets管理**

1. 进入你的GitHub仓库
2. 点击 "Settings" -> "Secrets and variables" -> "Actions"
3. 点击 "New repository secret"
4. 创建以下**两个**Secrets：

#### Secret 1: UP_LIST

**Name**: `UP_LIST`

**Value**（替换为你的UP主信息）:
```json
[
  {
    "uid": "第一个UP主的UID",
    "name": "第一个UP主名称"
  },
  {
    "uid": "第二个UP主的UID",
    "name": "第二个UP主名称"
  }
]
```

**示例**:
```json
[
  {
    "uid": "123456789",
    "name": "某科技UP主"
  },
  {
    "uid": "987654321",
    "name": "某游戏UP主"
  }
]
```

#### Secret 2: SEND_KEYS

**Name**: `SEND_KEYS`

**Value**（替换为你的微信SendKey）:
```json
[
  "第一个微信的SendKey",
  "第二个微信的SendKey"
]
```

**示例**:
```json
[
  "SCT1234567890abcdefg",
  "SCT0987654321xyz"
]
```

### 步骤4：启用GitHub Actions

1. 进入仓库的 "Actions" 标签页
2. 在左侧选择 "B站动态监控" 工作流
3. 点击 "Enable workflow" 启用工作流

### 步骤5：手动测试

1. 在Actions页面，点击 "B站动态监控"
2. 点击 "Run workflow" 下拉按钮
3. 选择分支，点击 "Run workflow"
4. 等待工作流运行完成（通常1-2分钟）
5. 查看运行日志，确认是否成功推送

## 配置说明

### 监控频率

默认每30分钟检查一次。如需修改，编辑 `.github/workflows/bilibili-monitor.yml` 文件中的cron表达式：

```yaml
schedule:
  - cron: '*/30 * * * *'  # 每30分钟
```

常用cron表达式：
- `*/15 * * * *` - 每15分钟
- `*/30 * * * *` - 每30分钟
- `0 * * * *` - 每小时
- `0 */2 * * *` - 每2小时

### 修改监控的UP主

1. 进入仓库的 "Settings" -> "Secrets and variables" -> "Actions"
2. 找到 `UP_LIST` secret，点击 "Update"
3. 修改JSON内容，保存即可

### 修改微信接收者

1. 进入仓库的 "Settings" -> "Secrets and variables" -> "Actions"
2. 找到 `SEND_KEYS` secret，点击 "Update"
3. 修改JSON内容（添加/删除SendKey），保存即可

## 工作原理

1. **定时触发**：GitHub Actions 每30分钟自动运行一次
2. **读取配置**：从GitHub Secrets读取UP主列表和SendKey
3. **获取动态**：通过B站公开API获取UP主的最新动态
4. **过滤内容**：自动识别并过滤纯图片帖子，只保留文字内容
5. **去重检查**：对比历史记录（history.json），跳过已推送的动态
6. **微信推送**：通过Server酱向配置的微信发送通知
7. **记录历史**：将已推送的动态ID保存到 `history.json` 并自动提交到GitHub

## 文件说明

```
bilibili-monitor/
├── monitor.py                    # 主监控脚本
├── requirements.txt              # Python依赖
├── .gitignore                    # Git忽略文件配置
├── history.json                  # 已推送历史记录（自动生成并提交）
└── .github/
    └── workflows/
        └── bilibili-monitor.yml  # GitHub Actions工作流配置
```

**注意**：`config.json` 文件已从项目中移除，所有配置都通过GitHub Secrets管理，确保敏感信息安全。

## 查看运行状态

### 查看运行日志

1. 进入GitHub仓库的 "Actions" 标签
2. 点击对应的工作流运行记录
3. 查看 "Run monitor script" 步骤的详细日志

### 查看历史记录

`history.json` 文件会记录所有已推送的动态ID，该文件会自动提交到GitHub仓库。

## 常见问题

### 1. 收不到微信推送？

- 确认Server酱SendKey是否正确
- 确认已关注Server酱的公众号（微信搜索"Server酱"并关注）
- 检查GitHub Actions运行日志，查看推送失败原因
- Server酱有发送频率限制，请勿过于频繁

### 2. 如何暂停监控？

在仓库的 "Actions" 标签页，点击工作流，然后点击 "Disable workflow"。

### 3. 如何完全删除工作流？

在 `.github/workflows/` 目录下删除对应的YAML文件，然后提交到GitHub。

### 4. history.json文件的作用？

该文件记录已推送的动态ID，避免重复推送。每次推送后会自动更新并提交到GitHub。

### 5. 可以监控多少个UP主？

理论上没有限制，但建议不超过10个，以免超出GitHub Actions的运行时间限制（每次运行最多6小时，本脚本通常几秒即可完成）。

### 6. B站API有限制吗？

B站公开API没有严格的认证限制，但建议不要设置过于频繁的检查间隔（建议不低于15分钟）。

### 7. 如何更新SendKey？

1. 进入仓库 Settings -> Secrets and variables -> Actions
2. 找到 `SEND_KEYS`，点击 "Update"
3. 输入新的SendKey列表（JSON格式）
4. 保存即可

### 8. GitHub Actions免费额度够用吗？

完全够用。GitHub免费账户每月提供2000分钟Actions运行时间，本项目每次运行仅需1-2分钟，每天运行48次（每30分钟一次）也仅需约60分钟/月。

## 安全说明

- ✅ 所有敏感信息（UP主UID、微信SendKey）都存储在GitHub Secrets中
- ✅ Secrets是加密存储的，不会出现在日志中
- ✅ 代码仓库可以设为公开，不会泄露敏感信息
- ✅ 建议不要将包含真实配置的 `config.json` 文件上传到GitHub

## 注意事项

- 本项目使用B站公开API，不保证长期稳定可用
- 如果B站API变更，可能需要更新 `monitor.py` 中的解析逻辑
- Server酱服务可能不稳定，如遇问题请访问官网查看状态
- 请妥善保管你的Server酱SendKey，不要泄露给他人

## 技术栈

- **Python 3.11** - 脚本语言
- **Requests** - HTTP请求库
- **GitHub Actions** - 定时任务调度
- **Server酱** - 微信推送服务

## License

MIT License

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持监控多个UP主
- 支持微信推送
- 自动过滤纯图片帖子
- 历史记录去重
- 敏感信息通过GitHub Secrets管理