---
name: yun139-cloud-storage
description: 操作中国移动云盘（yun.139.com）的技能。支持浏览器自动化(playwright-cli)和API两种方式操作云盘。当用户提到云盘、云空间、和彩云、手机登录云盘、上传文件到云盘、从云盘下载、管理云盘文件、创建云盘文件夹、通过API操作云盘等与中国移动云盘相关的操作时触发。
triggers:
  - 云盘
  - yun.139
  - 和彩云
  - 手机登录云盘
  - 云空间管理
  - 139云盘API
  - 云盘API
---

# 中国移动云盘操作技能

## 工作流程概览

```
1. 询问手机号 → 2. 浏览器登录获取Token → 3. 通过API执行文件操作
```

---

## 第一步：询问手机号

使用 `AskUserQuestion` 弹窗让用户输入手机号：

```
请输入您的中国移动云盘手机号（用于登录）
```

---

## 第二步：浏览器登录获取Token

> **核心原则**：登录流程全程使用 `playwright-cli` 浏览器自动化，仅用于获取 `authorization` Cookie。后续所有文件操作均通过 Python API 直连，不再依赖浏览器。

### 2.1 打开云盘首页

```bash
playwright-cli open "https://yun.139.com/w/#/"
```

### 2.2 等待页面加载并获取快照

```bash
playwright-cli snapshot
```

**确认页面状态**：
- 应看到登录框，包含 "手机登录" / "短信登录" / "账号登录" Tab
- 默认通常是 "短信登录" Tab，需要切换到 "手机登录"（如果当前不是的话）
- 看到手机号输入框（ref 如 `e81`）

### 2.3 切换到"手机登录"Tab（如需要）

如果当前是 "短信登录" Tab，点击 "手机登录"：

```bash
playwright-cli eval "() => { const el = Array.from(document.querySelectorAll('*')).find(e => e.textContent === '手机登录'); if(el) el.click(); }"
```

### 2.4 填入手机号

**方法A：通过 ref 填充（推荐，如果有 ref）**

```bash
playwright-cli fill <手机号输入框ref> "<用户手机号>"
```

**方法B：通过 JavaScript 设置 value**

```bash
playwright-cli eval "() => { const input = document.querySelector('input[placeholder*=\"手机号\"]'); if(input) input.value = '<用户手机号>'; }"
```

### 2.5 勾选"同意协议"（关键步骤，易踩坑）

> **坑点**：协议勾选框不是原生 `<input type="checkbox">`，而是自定义 DOM 组件（`<div class="check-img-wrap">`），不能用 `playwright-cli check` 或 `document.querySelector('input[type=checkbox]')` 定位。

**正确做法**——通过类名点击：

```bash
playwright-cli eval "() => { const el = document.querySelector('.check-img-wrap') || document.querySelector('.sim-check-img-wrap'); if(el) { el.click(); return 'clicked'; } return 'not found'; }"
```

**验证勾选成功的方法**：
- 如果勾选成功，再次点击"登录"后不会再出现"请勾选同意相关协议政策"提示
- 如果仍然出现该提示，说明勾选未生效，重试上述 JS 点击

### 2.6 点击登录按钮

```bash
playwright-cli click <登录按钮ref>
# 例如：playwright-cli click e69
```

或如果 ref 不稳定：

```bash
playwright-cli eval "() => { const btn = Array.from(document.querySelectorAll('button')).find(e => e.textContent.includes('登录') && !e.textContent.includes('注册') && !e.disabled); if(btn) btn.click(); }"
```

### 2.7 等待手机端确认

登录请求会推送到用户手机。页面应显示类似：

> "登录请求已发送到您手机上，请在手机确认"

**此时必须等待用户在手机上点击"确认登录"**，流程才能继续。

### 2.8 获取Token

用户确认手机登录后，执行：

```bash
playwright-cli cookie-list
```

从输出中找到 `authorization` cookie 的值，格式为：

```
authorization=Basic cGM6MTM5...（一长串Base64，内容包含手机号信息）
```

**完整提取**：取 `Basic ` 后面的全部内容（包含 `Basic ` 前缀也可以，API 脚本会自动处理）。

### 2.9 关闭浏览器（可选）

```bash
playwright-cli close
```

---

## 第三步：通过API执行文件操作

获取 Token 后，所有操作均使用 Python API：

```python
import sys
sys.path.insert(0, '<skill安装路径>/yun139-cloud-storage/scripts')
from yun139_api import Yun139Session, Yun139FolderManager, Yun139FileManager, Yun139ShareManager

session = Yun139Session(token="<获取到的完整authorization值>")
```

### 列出根目录

```python
folder_mgr = Yun139FolderManager(session)
ok, data = folder_mgr.get_lists("/")
if ok:
    for item in data.get("items", []):
        print(f"{'[文件夹]' if item['type'] == 'folder' else '[文件]'} {item['name']}")
```

### 命令行快速操作

```bash
# 列出根目录
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" list

# 列出指定目录
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" list <parent_id>

# 创建文件夹
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" create <文件夹名> [父目录ID]

# 重命名
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" rename <文件ID> <新名称>

# 删除
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" delete <文件ID1> <文件ID2> ...

# 移动
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" move <文件ID1> ... <目标目录ID>

# 分享
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" share <分享标题> <文件夹ID>

# 上传文件
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" upload <本地文件路径> [目标文件夹ID]

# 下载文件
python <skill安装路径>/yun139-cloud-storage/scripts/yun139_api.py "<token>" download <文件ID> <保存路径>
```

---

## 踩坑记录与解决方案

### 坑1：协议勾选框不是原生 checkbox

| 表现 | `playwright-cli check` 报错 `does not match any elements`；`document.querySelector('input[type=checkbox]')` 返回 null |
|------|------------------------------------------------------------------------------------------------------------------|
| 原因 | 前端使用自定义 DOM 组件（`<div class="check-img-wrap">`）模拟勾选框，无原生 input 元素 |
| 解决 | 用 JS 通过类名 `.check-img-wrap` 或 `.sim-check-img-wrap` 直接点击该 div |

### 坑2：协议未勾选时点击登录无反馈

| 表现 | 点击登录后页面无变化，没有弹窗、没有跳转，似乎没有响应 |
|------|---------------------------------------------------|
| 原因 | 登录按钮实际上是有效的，但反馈信息（"请勾选同意相关协议政策"）显示在协议区域下方，容易被忽略 |
| 解决 | 先执行 2.5 的协议勾选步骤，确认无该提示后再点击登录 |

### 坑3：手机号输入框 ref 不稳定

| 表现 | 不同页面加载时，手机号输入框的 ref ID 可能变化 |
|------|-------------------------------------------|
| 原因 | 页面动态渲染导致 ref 不固定 |
| 解决 | 优先用 `playwright-cli fill <ref>`（如果能从 snapshot 获取到），否则退到 JS 通过 placeholder 定位 |

### 坑4：登录流程依赖手机端人工确认

| 表现 | 点击登录后页面卡在"登录请求已发送"状态 |
|------|-----------------------------------|
| 原因 | 手机登录模式（SIM登录）必须由用户在手机上确认授权，这是安全机制，无法绕过 |
| 解决 | 明确提示用户检查手机并点击确认，等待确认后再继续获取 cookie |

### 坑5：短信登录 vs 手机登录混淆

| 表现 | 填入手机号后要求输入短信验证码，而不是推送到手机确认 |
|------|-------------------------------------------------|
| 原因 | 默认可能处于"短信登录"Tab，需要切换到"手机登录"Tab |
| 解决 | 在填入手机号前，先确认当前是"手机登录"Tab，如果不是则切换 |

---

## API 详细用法

### 安装依赖

```bash
pip install requests
```

### 文件夹操作

```python
folder_mgr = Yun139FolderManager(session)

# 获取文件夹列表
ok, data = folder_mgr.get_lists("/", size=50, sort_by="updated_at", sort_order="desc")

# 创建文件夹
ok, data = folder_mgr.create_folder("新建文件夹", "/")
```

### 文件操作

```python
file_mgr = Yun139FileManager(session)

# 重命名
ok, data = file_mgr.rename_file("文件ID", "新名称")

# 移动文件
ok, data = file_mgr.move_file(["文件ID1", "文件ID2"], "目标文件夹ID")

# 删除文件
ok, data = file_mgr.remove_file(["文件ID1", "文件ID2"])
```

### 分享操作

```python
share_mgr = Yun139ShareManager(session)

# 创建分享链接
ok, data = share_mgr.create_share("分享标题", url_type=0, fld_list=["文件夹ID"])
```

### 上传操作

```python
upload_mgr = Yun139UploadManager(session)

# 上传文件（支持进度回调）
def progress(p):
    print(f"上传进度: {p}%")

ok, data = upload_mgr.upload_file("文件名.zip", "/本地路径/文件.zip", "/", progress_callback=progress)
```

### 下载操作

```python
down_mgr = Yun139DownManager(session)

# 下载文件（支持进度回调）
def progress(p):
    print(f"下载进度: {p}%")

ok, data = down_mgr.download_file("文件ID", "/保存路径/文件名.jpg", progress_callback=progress)
```

### Token 刷新

```python
ok, result = session.refresh_token()
if ok:
    new_token = result['token']  # 刷新后的新token
```

---

## API 接口列表

| 接口 | 路径 | 说明 |
|------|------|------|
| 文件列表 | `POST /hcy/file/list` | 获取文件夹内容 |
| 创建文件夹 | `POST /hcy/file/create` | 新建文件夹 |
| 重命名 | `POST /hcy/file/update` | 重命名文件/文件夹 |
| 删除 | `POST /hcy/recyclebin/batchTrash` | 删除到回收站 |
| 移动 | `POST /hcy/file/batchMove` | 移动文件/文件夹 |
| 分享 | `POST /orchestration/.../getOutLink` | 创建分享链接 |

---

## 快速命令参考

| 操作 | 命令 |
|------|------|
| 打开云盘 | `playwright-cli open "https://yun.139.com/w/#/"` |
| 获取快照 | `playwright-cli snapshot` |
| 执行JS | `playwright-cli eval "<js代码>"` |
| 获取Cookie | `playwright-cli cookie-list` |
| 关闭浏览器 | `playwright-cli close` |
| 列出文件 | `python scripts/yun139_api.py <token> list` |
| 创建文件夹 | `python scripts/yun139_api.py <token> create <名称>` |
| 重命名 | `python scripts/yun139_api.py <token> rename <fid> <新名>` |
| 删除 | `python scripts/yun139_api.py <token> delete <fid>` |
| 移动 | `python scripts/yun139_api.py <token> move <fid> <target>` |
| 分享 | `python scripts/yun139_api.py <token> share <标题> <fid>` |
| 上传文件 | `python scripts/yun139_api.py <token> upload <文件路径> [文件夹ID]` |
| 下载文件 | `python scripts/yun139_api.py <token> download <fid> <保存路径>` |
