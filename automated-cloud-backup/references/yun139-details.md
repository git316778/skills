# 139云盘特定实现细节

## 已知常量

| 资源 | ID |
|------|----|
| AI空间 文件夹 | `FgqAR0GH6rLhqrVtw9FBJxpfwQV-z-r04` |

## Token 文件位置

`C:/Users/Administrator/AppData/Local/hermes/scripts/yun139_token.env`

```env
YUN139_TOKEN=cGM6MT...n
```

## Token 刷新（自动化任务必做）

```python
from yun139_api import Yun139Session

session = Yun139Session(token)
ok, result = session.refresh_token()  # 有效期<15天时刷新
if ok:
    new_token = result["token"]
    # 写回 .env 文件
```

## 自动上传示例

```python
from yun139_api import Yun139Session, Yun139UploadManager

AI_SPACE = "FgqAR0GH6rLhqrVtw9FBJxpfwQV-z-r04"
upload_mgr = Yun139UploadManager(session)

def progress(p):
    print(f"\r上传进度: {p}%", end="", flush=True)

ok, data = upload_mgr.upload_file(
    os.path.basename(local_path), local_path,
    AI_SPACE, progress_callback=progress
)
```

## 踩坑

| 问题 | 解决 |
|------|------|
| Token 已过期 | `refresh_token()` 只刷新有效期 < 15 天的；已过期需重新手机登录 |
| 文件重名 | 自动模式下 `auto_rename` 策略，文件名末尾加编号 |
| zip 内路径重复 | 用 `included_elsewhere` 集合去重 |
| 备份来源树过大 | 排除 `hermes-agent/` 源码目录（100K+ 文件，可重新安装） |
