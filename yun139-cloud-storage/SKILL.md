---
name: yun139-cloud-storage
description: 操作中国移动云盘（yun.139.com）的技能。支持浏览器自动化(playwright-cli)和API两种方式操作云盘。当用户提到云盘、云空间、和彩云、手机登录云盘、上传文件到云盘、从云盘下载、管理云盘文件、创建云盘文件夹、通过API操作云盘等与中国移动云盘相关的操作时触发。
---

# 中国移动云盘操作技能

## 工作流程概览

```
1. 询问手机号 → 2. 浏览器登录获取Token → 3. 通过API执行文件操作
```

## Token 持久化（推荐）

Token 保存到 `scripts/yun139_token.env`（技能目录下）：

```env
YUN139_TOKEN=cGM6MT...
> **安全提示**：`yun139_token.env` 包含明文授权 token，不要提交到 git，建议加入 `.gitignore`。

**脚本读取方式**：

```python
import os
def get_token():
    env_tok = os.environ.get("YUN139_TOKEN", "").strip()
    if env_tok:
        return env_tok
    token_file = os.path.join(os.path.dirname(__file__), "..", "scripts", "yun139_token.env")
    if os.path.isfile(token_file):
        with open(token_file) as f:
            for line in f:
                if line.startswith("YUN139_TOKEN=***                        return line.split("=", 1)[1].strip()
    raise RuntimeError("YUN139_TOKEN 未找到")
```

**已知常量：**

| 资源 | ID |
|------|----|
| AI空间 文件夹 | `FgqAR0GH6rLhqrVtw9FBJxpfwQV-z-r04` |

**Token 刷新**（自动化任务必做）：

```python
session = Yun139Session(token)
ok, result = session.refresh_token()  # 有效期<15天时刷新
if ok:
    new_token = result["token"]
```

**自动上传模式（Hermes Cron / 脚本）：

```python
import os, sys
sys.path.insert(0, '<skill>/scripts')
from yun139_api import Yun139Session, Yun139UploadManager

token = get_token()
session = Yun139Session(token)
session.refresh_token()

AI_SPACE = "FgqAR0GH6rLhqrVtw9FBJxpfwQV-z-r04"
upload_mgr = Yun139UploadManager(session)

def progress(p):
    print(f"\r上传进度: {p}%", end="", flush=True)

ok, data = upload_mgr.upload_file(
    os.path.basename(local_path), local_path,
    AI_SPACE, progress_callback=progress
)
```

## 踩坑记录

### 坑1：协议勾选框不是原生 checkbox

| 表现 | 解决 |
|------|------|
| `playwright-cli check` 报错 | 自定义 DOM 组件，JS 点击 `.check-img-wrap` |
| 协议未勾选时登录无反馈 | 先勾选协议再点登录 |

### Token 有效期

- 有效期编码在 token 内的过期时间戳
- `refresh_token()` 仅在有效期 < 15 天时刷新；已过期需重新手机登录
- 自动上传前务必调用 `refresh_token()` 保证 token 可用
