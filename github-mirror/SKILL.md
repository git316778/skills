---
name: github-mirror
description: GitHub 镜像与加速访问技能，提供多种方式加速 GitHub 访问和下载
---

# GitHub 镜像与加速访问技能

这个技能提供多种方法加速 GitHub 访问和下载，特别适合网络受限的环境。

## 方法一：使用 GitHub 镜像站点

### 常用 GitHub 镜像站点：
1. **ghproxy.com** - 最常用的 GitHub 代理
   - 格式：`https://ghproxy.com/https://github.com/user/repo`
   - 示例：`https://ghproxy.com/https://github.com/xingkongliang/skills-manager`

2. **hub.fastgit.org** - FastGit 镜像
   - 格式：`https://hub.fastgit.org/user/repo`
   - 示例：`https://hub.fastgit.org/xingkongliang/skills-manager`

3. **gitclone.com** - GitClone 镜像
   - 格式：`https://gitclone.com/github.com/user/repo`
   - 示例：`https://gitclone.com/github.com/xingkongliang/skills-manager`

## 方法二：修改 Git 配置使用代理

### 设置全局 Git 代理：
```bash
# 设置 HTTP 代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 取消代理
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 使用 SSH over HTTPS 代理：
```bash
# 编辑 ~/.ssh/config
Host github.com
    Hostname github.com
    User git
    Port 443
    ProxyCommand connect -H 127.0.0.1:7890 %h %p
```

## 方法三：使用 curl/wget 下载

### 下载单个文件：
```bash
# 使用 ghproxy
curl -L "https://ghproxy.com/https://raw.githubusercontent.com/user/repo/main/file.txt" -o file.txt

# 使用 fastgit
curl -L "https://raw.fastgit.org/user/repo/main/file.txt" -o file.txt
```

### 下载整个仓库：
```bash
# 使用 ghproxy
curl -L "https://ghproxy.com/https://github.com/user/repo/archive/refs/heads/main.zip" -o repo.zip
unzip repo.zip

# 或使用 wget
wget "https://ghproxy.com/https://github.com/user/repo/archive/refs/heads/main.zip"
```

## 方法四：使用 npm/yarn 的镜像源

### 设置 npm 镜像：
```bash
# 设置淘宝镜像
npm config set registry https://registry.npmmirror.com/

# 恢复官方源
npm config set registry https://registry.npmjs.org/
```

### 设置 yarn 镜像：
```bash
yarn config set registry https://registry.npmmirror.com/
```

## 方法五：使用系统代理

### Windows 设置代理：
```powershell
# 设置系统代理
netsh winhttp set proxy 127.0.0.1:7890

# 清除代理
netsh winhttp reset proxy
```

### 设置环境变量：
```powershell
# 临时设置
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"

# 永久设置（需要管理员权限）
[System.Environment]::SetEnvironmentVariable("HTTP_PROXY", "http://127.0.0.1:7890", "Machine")
[System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", "http://127.0.0.1:7890", "Machine")
```

## 实用脚本

### 1. 使用镜像克隆仓库
```powershell
function git-clone-mirror {
    param([string]$url)
    
    if ($url -match "github\.com") {
        $mirrorUrl = "https://ghproxy.com/" + $url
        Write-Host "使用镜像克隆: $mirrorUrl"
        git clone $mirrorUrl
    } else {
        git clone $url
    }
}

# 使用示例
git-clone-mirror "https://github.com/xingkongliang/skills-manager.git"
```

### 2. 批量下载 GitHub 文件
```powershell
function download-github-file {
    param(
        [string]$repo,
        [string]$file,
        [string]$branch = "main"
    )
    
    $url = "https://ghproxy.com/https://raw.githubusercontent.com/$repo/$branch/$file"
    Write-Host "下载: $url"
    Invoke-WebRequest -Uri $url -OutFile (Split-Path $file -Leaf)
}

# 使用示例
download-github-file "xingkongliang/skills-manager" "README.md"
```

### 3. 检查网络连接
```powershell
function test-github-connection {
    $sites = @(
        "https://github.com",
        "https://ghproxy.com",
        "https://hub.fastgit.org",
        "https://gitclone.com"
    )
    
    foreach ($site in $sites) {
        try {
            $response = Invoke-WebRequest -Uri $site -Method Head -TimeoutSec 5
            Write-Host "✓ $site - 连接正常 (状态码: $($response.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "✗ $site - 连接失败" -ForegroundColor Red
        }
    }
}
```

## 常见问题解决

### Q1: GitHub 访问超时
**解决方案：**
1. 使用镜像站点：`https://ghproxy.com/https://github.com/...`
2. 设置 Git 代理
3. 使用 VPN 或代理工具

### Q2: 下载速度慢
**解决方案：**
1. 使用 `git clone --depth 1` 只克隆最新提交
2. 使用镜像站点下载 zip 包
3. 使用 aria2 多线程下载

### Q3: SSL 证书问题
**解决方案：**
```bash
# 临时忽略 SSL 验证
git config --global http.sslVerify false

# 或设置正确的 CA 证书
git config --global http.sslCAInfo /path/to/cert.pem
```

## 推荐的代理工具

1. **Clash** - 支持规则代理，适合开发者
2. **v2rayN** - 功能强大，支持多种协议
3. **Proxifier** - 强制指定应用走代理
4. **Tun2socks** - 全局透明代理

## 注意事项

1. 镜像站点可能不稳定，建议多准备几个备用
2. 使用代理时注意隐私和安全
3. 定期更新镜像站点地址（可能失效）
4. 对于重要项目，建议使用官方源以确保完整性

---

**技能作者：** OpenClaw Assistant  
**创建时间：** 2026年5月8日  
**适用场景：** 网络受限环境下的 GitHub 访问优化