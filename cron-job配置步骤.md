# cron-job.org 配置详细步骤

## 第1步：生成GitHub Personal Access Token

### 1.1 访问Token生成页面
打开浏览器，访问：
```
https://github.com/settings/tokens/new
```

### 1.2 填写Token信息
- **Token name**: `bilibili-monitor-cron`
- **Expiration**: 选择 `90 days`（或自定义）
- **Scopes**: 勾选以下两项：
  - ✅ `repo` (Full control of private repositories)
  - ✅ `workflow` (Update GitHub Actions workflows)

### 1.3 生成并保存Token
1. 滚动到页面底部，点击 **"Generate token"**
2. **立即复制生成的token**（格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）
3. **重要**：这个token只显示一次，务必保存好！
4. 建议保存在安全的地方（如密码管理器）

---

## 第2步：注册 cron-job.org

### 2.1 访问注册页面
打开浏览器，访问：
```
https://cron-job.org/en/register
```

### 2.2 填写注册信息
- **Username**: 选择一个用户名
- **Email**: 你的邮箱
- **Password**: 设置密码（至少8位）

### 2.3 验证邮箱
1. 检查邮箱，找到验证邮件
2. 点击验证链接激活账户

---

## 第3步：创建cron任务

### 3.1 登录后进入Dashboard
访问：https://cron-job.org/en/dashboard

### 3.2 创建任务 - 股市里的猩猩

需要创建**多个任务**来覆盖不同时间段：

#### 任务1：9:25-9:45 每分钟

1. 点击 **"Create cron-job"**
2. 填写：
   - **Title**: `股市里的猩猩-9:25-9:45`
   - **URL**: 
     ```
     https://api.github.com/repos/Alan757/bilibili-monitor/actions/workflows/monitor-xingu.yml/dispatches
     ```
   - **Method**: `POST`
   - **Headers**: 点击"Add header"，添加：
     ```
     Authorization: token 你的GITHUB_TOKEN
     Accept: application/vnd.github.v3+json
     Content-Type: application/json
     ```
     （把"你的GITHUB_TOKEN"替换为第1步生成的token）
   - **Request body**: 
     ```json
     {"ref":"main"}
     ```
   - **Schedule**: 选择 `Cron expression`
   - **Cron expression**: 
     ```
     * 1-2 25-44 * * 1-5
     ```
     （这是UTC时间，对应UTC+8的9:25-9:45，周一到周五）

3. 点击 **"Create"**

#### 任务2：9:45-10:00 每2分钟

重复上述步骤：
- **Title**: `股市里的猩猩-9:45-10:00`
- **URL**: 同上
- **Headers**: 同上
- **Request body**: 同上
- **Cron expression**: 
  ```
  47,49,51,53,55,57,59 1-2 * * 1-5
  ```

#### 任务3：10:00-15:00 每30分钟

- **Title**: `股市里的猩猩-10:00-15:00`
- **URL**: 同上
- **Headers**: 同上
- **Request body**: 同上
- **Cron expression**: 
  ```
  0,30 2-6 * * 1-5
  ```

### 3.3 创建任务 - 鳄鱼派

#### 任务4：9:30-15:00 每30分钟

- **Title**: `鳄鱼派-9:30-15:00`
- **URL**: 
  ```
  https://api.github.com/repos/Alan757/bilibili-monitor/actions/workflows/monitor-eyu.yml/dispatches
  ```
- **Method**: `POST`
- **Headers**: 同上
- **Request body**: 同上
- **Cron expression**: 
  ```
  0,30 1-6 * * 1-5
  ```

---

## 第4步：禁用GitHub Actions的schedule（可选）

如果使用cron-job.org触发，建议禁用GitHub Actions自带的schedule，避免重复运行。

### 修改 monitor-xingu.yml

打开文件：`bilibili-monitor/.github/workflows/monitor-xingu.yml`

把：
```yaml
on:
  schedule:
    # 周一到周五
    # 9:25-9:45 每分钟 (UTC 1:25-1:45)
    - cron: '25-45 1 * * 1-5'
    # 9:45-10:00 每2分钟 (UTC 1:45-2:00)
    - cron: '45,47,49,51,53,55,57,59 1 * * 1-5'
    # 10:00-15:00 每30分钟 (UTC 2:00-7:00)
    - cron: '0,30 2-6 * * 1-5'
  workflow_dispatch:
```

改为：
```yaml
on:
  # schedule已禁用，使用cron-job.org触发
  # schedule:
  #   - cron: '25-45 1 * * 1-5'
  #   - cron: '45,47,49,51,53,55,57,59 1 * * 1-5'
  #   - cron: '0,30 2-6 * * 1-5'
  workflow_dispatch:
```

### 修改 monitor-eyu.yml

打开文件：`bilibili-monitor/.github/workflows/monitor-eyu.yml`

把：
```yaml
on:
  schedule:
    # 周一到周五
    # 9:30-15:00 每30分钟 (UTC 1:30-7:00)
    - cron: '0,30 1-6 * * 1-5'
  workflow_dispatch:
```

改为：
```yaml
on:
  # schedule已禁用，使用cron-job.org触发
  # schedule:
  #   - cron: '0,30 1-6 * * 1-5'
  workflow_dispatch:
```

---

## 第5步：时区对照表

| UTC+8 时间 | UTC 时间 | cron-job.org 表达式 |
|-----------|---------|-------------------|
| 9:25-9:45 | 1:25-1:45 | `* 1-2 25-44 * * 1-5` |
| 9:47,49,51,53,55,57,59 | 1:47,49,51,53,55,57,59 | `47,49,51,53,55,57,59 1-2 * * 1-5` |
| 10:00-15:00 | 2:00-7:00 | `0,30 2-6 * * 1-5` |
| 9:30-15:00 | 1:30-7:00 | `0,30 1-6 * * 1-5` |

---

## 第6步：测试

1. 在cron-job.org中，找到刚创建的任务
2. 点击任务右侧的 **"Execute"** 按钮手动触发一次
3. 访问 https://github.com/Alan757/bilibili-monitor/actions
4. 查看是否开始运行
5. 如果运行成功，说明配置正确！

---

## 注意事项

1. **Token安全**：
   - 不要泄露GitHub Token
   - 如果泄露，立即在GitHub设置中删除并重新生成
   - Token有90天有效期，记得定期更新

2. **cron-job.org免费版限制**：
   - 免费版完全够用
   - 任务执行时间限制（我们的workflow约1-2分钟，没问题）

3. **时区**：
   - cron-job.org使用UTC时间
   - 所有cron表达式都是UTC时间
   - 对照上面的时区表设置

4. **GitHub Actions限制**：
   - 免费账户每月2000分钟
   - 当前配置每月约1000分钟，在限制内

---

## 故障排查

### 如果手动触发不成功

1. **检查Token**：
   - 确认Token有`repo`和`workflow`权限
   - 确认Token未过期

2. **检查URL**：
   - 确认URL正确
   - 确认workflow文件名正确（monitor-xingu.yml 或 monitor-eyu.yml）

3. **检查Headers**：
   - Authorization格式：`token YOUR_TOKEN`
   - 不要有多余的空格

4. **查看GitHub Actions日志**：
   - 访问Actions页面查看错误信息

### 如果cron-job.org任务不执行

1. 检查cron表达式是否正确
2. 检查任务是否启用（Enabled）
3. 查看cron-job.org的日志