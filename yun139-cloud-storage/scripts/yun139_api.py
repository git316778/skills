#!/usr/bin/env python3
"""
中国移动云盘(139云盘) API 操作封装
基于 https://github.com/kong-hen/cloud_driver_sdk

使用方法:
    from yun139_api import Yun139Session, Yun139FolderManager, Yun139FileManager

    # 初始化会话 (需要从playwright-cli获取的token)
    session = Yun139Session(token="your_base64_token")

    # 文件夹操作
    folder_mgr = Yun139FolderManager(session)
    ok, data = folder_mgr.get_lists("/")  # 获取根目录文件列表
    ok, data = folder_mgr.create_folder("新建文件夹", "/")  # 创建文件夹

    # 文件操作
    file_mgr = Yun139FileManager(session)
    ok, data = file_mgr.rename_file(fid, "新名称")  # 重命名
    ok, data = file_mgr.move_file([fid], target_folder_id)  # 移动
    ok, data = file_mgr.remove_file([fid])  # 删除

    # 分享操作
    share_mgr = Yun139ShareManager(session)
    ok, data = share_mgr.create_share("分享标题", url_type=0, fld_list=[folder_id])
"""

import base64
import hashlib
import json
import string
import secrets
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote
from typing import List, Dict, Any, Optional, Tuple

try:
    import requests
except ImportError:
    print("请先安装requests: pip install requests")
    raise

# API域名和路径常量
DRIVE_DOMAIN = "https://personal-kd-njs.yun.139.com"

# 文件列表
FILE_LIST = "/hcy/file/list"

# 文件操作
FOLDER_CREATE = "/hcy/file/create"
FILE_CREATE = "/hcy/file/create"
FILE_RENAME = "/hcy/file/update"
FILE_DELETE = "/hcy/recyclebin/batchTrash"
FILE_MOVE = "/hcy/file/batchMove"

# 文件上传完成
FILE_COMPLETE = "/hcy/file/complete"

# 文件下载
FILE_DOWNLOAD = "/hcy/file/getDownloadUrl"

# 任务信息
TASK = "/hcy/task/get"

# 分享
SHARE = "https://yun.139.com/orchestration/personalCloud-rebuild/outlink/v1.0/getOutLink"

# 刷新Token接口
REFRESH_TOKEN = "https://aas.caiyun.feixin.10086.cn:443/tellin/authTokenRefresh.do"


class Yun139Session:
    """139云盘会话管理"""

    Token: str

    def __init__(self, token: str):
        if token.startswith("Basic "):
            self.Token = token[6:]
        else:
            self.Token = token

    def cal_sign(self, body: str, ts: str, rand_str: str) -> str:
        """计算签名"""
        body = quote(body, safe='')
        chars = list(body)
        chars.sort()
        body = ''.join(chars)
        body = base64.b64encode(body.encode('utf-8')).decode('utf-8')
        body_md5 = hashlib.md5(body.encode('utf-8')).hexdigest()
        ts_rand_md5 = hashlib.md5(f"{ts}:{rand_str}".encode('utf-8')).hexdigest()
        combined = body_md5 + ts_rand_md5
        result = hashlib.md5(combined.encode('utf-8')).hexdigest().upper()
        return result

    def request(
        self,
        url: str,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Any]:
        """通用请求方法"""
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        alphabet = string.ascii_letters + string.digits
        randomStr = ''.join(secrets.choice(alphabet) for _ in range(16))
        sign = self.cal_sign(json.dumps(data), ts, randomStr)

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": "Basic " + self.Token,
            "Caller": "web",
            "Cms-Device": "default",
            "Mcloud-Channel": "1000101",
            "Mcloud-Client": "10701",
            "Mcloud-Route": "001",
            "Mcloud-Sign": f"{ts},{randomStr},{sign}",
            "Mcloud-Version": "7.14.0",
            "x-DeviceInfo": "||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||",
            "x-huawei-channelSrc": "10000034",
            "x-inner-ntwk": "2",
            "x-m4c-caller": "PC",
            "x-m4c-src": "10002",
            "x-SvcType": "1",
            "X-Yun-Api-Version": "v1",
            "X-Yun-App-Channel": "10000034",
            "X-Yun-Channel-Source": "10000034",
            "X-Yun-Client-Info": "||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||dW5kZWZpbmVk||",
            "X-Yun-Module-Type": "100",
            "X-Yun-Svc-Type": "1",
        }

        params = dict(query_params) if query_params else None

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/json;charset=UTF-8"
                response = requests.post(url, headers=headers, json=data)
            else:
                return False, f"不支持的HTTP方法: {method}"

            response.raise_for_status()
            json_resp = response.json()

            if json_resp.get("success") == True:
                return True, json_resp.get("data")
            else:
                return False, json_resp
        except requests.exceptions.RequestException as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def refresh_token(self) -> Tuple[bool, Any]:
        """刷新访问令牌"""
        try:
            token = self.Token
            decode_bytes = base64.b64decode(token)
            decode_str = decode_bytes.decode('utf-8')
            splits = decode_str.split(":")

            if len(splits) < 3:
                return False, {"msg": "Token无效"}

            strs = splits[2].split("|")
            if len(strs) < 4:
                return False, {"msg": "Token无效"}

            expiration = int(strs[3])
            expiration -= int(time.time() * 1000)

            if expiration > 1000 * 60 * 60 * 24 * 15:
                return True, {"msg": "令牌有效期大于15天，无需刷新", "token": token}

            if expiration < 0:
                return False, {"msg": "Token已经过期"}

            req_body = f"<root><token>{splits[2]}</token><account>{splits[1]}</account><clienttype>656</clienttype></root>"
            headers = {"Content-Type": "application/xml"}
            response = requests.post(REFRESH_TOKEN, data=req_body, headers=headers)
            response.raise_for_status()

            root = ET.fromstring(response.text)
            return_code = root.findtext("return")
            desc = root.findtext("desc")
            auth = root.findtext("token")

            if return_code != "0":
                return False, {"msg": f"Token刷新失败: {desc}"}

            new_auth = f"{splits[0]}:{splits[1]}:{auth}"
            new_token = base64.b64encode(new_auth.encode('utf-8')).decode('utf-8')
            self.Token = new_token
            return True, {"msg": "Token刷新成功", "token": new_token}
        except Exception as e:
            return False, {"msg": f"Token刷新失败: {str(e)}"}


class Yun139FolderManager:
    """文件夹管理"""

    def __init__(self, session: Yun139Session):
        self.session = session

    def get_lists(
        self,
        pdir_fid: str = "/",
        size: int = 50,
        cursor: str = None,
        sort_by: str = "file_name",
        sort_order: str = "asc",
    ) -> Tuple[bool, Any]:
        """
        获取文件夹列表
        :param pdir_fid: 父目录ID，默认"/"（根目录）
        :param size: 每页数量
        :param cursor: 分页游标
        :param sort_by: 排序字段，"file_name" 或 "updated_at"
        :param sort_order: 排序方式，"asc" 或 "desc"
        """
        if sort_by not in ("file_name", "updated_at"):
            return False, "sort_by 只能为 'file_name' 或 'updated_at'"
        if sort_by == "file_name":
            sort_by = "name"
        if sort_order not in ("asc", "desc"):
            return False, "sort_order 只能为 'asc' 或 'desc'"

        url = DRIVE_DOMAIN + FILE_LIST
        data = {
            "pageInfo": {
                "pageSize": size,
                "pageCursor": cursor,
            },
            "orderBy": sort_by,
            "orderDirection": sort_order.upper(),
            "parentFileId": pdir_fid,
            "imageThumbnailStyleList": ["Small", "Large"],
        }

        return self.session.request(url=url, method="POST", data=data)

    def create_folder(
        self,
        folder_name: str,
        pdir_fid: str = "/",
    ) -> Tuple[bool, Any]:
        """
        创建文件夹
        :param folder_name: 文件夹名称
        :param pdir_fid: 父目录ID，默认"/"（根目录）
        """
        url = DRIVE_DOMAIN + FOLDER_CREATE
        data = {
            "parentFileId": pdir_fid,
            "name": folder_name,
            "description": "",
            "type": "folder",
            "fileRenameMode": "force_rename"
        }

        return self.session.request(url=url, method="POST", data=data)


class Yun139FileManager:
    """文件管理"""

    def __init__(self, session: Yun139Session):
        self.session = session

    def move_file(
        self,
        src_fids: List[str],
        dst_pdir_fid: str,
    ) -> Tuple[bool, Any]:
        """
        移动文件/文件夹
        :param src_fids: 源文件/文件夹ID列表
        :param dst_pdir_fid: 目标文件夹ID
        """
        url = DRIVE_DOMAIN + FILE_MOVE
        data = {
            "fileIds": src_fids,
            "toParentFileId": dst_pdir_fid
        }
        return self.session.request(url=url, method="POST", data=data)

    def rename_file(
        self,
        fid: str,
        new_name: str,
    ) -> Tuple[bool, Any]:
        """
        重命名文件/文件夹
        :param fid: 文件/文件夹ID
        :param new_name: 新名称
        """
        url = DRIVE_DOMAIN + FILE_RENAME
        data = {
            "fileId": fid,
            "name": new_name,
            "description": ""
        }
        return self.session.request(url=url, method="POST", data=data)

    def remove_file(
        self,
        fids: List[str],
    ) -> Tuple[bool, Any]:
        """
        删除文件/文件夹
        :param fids: 文件/文件夹ID列表
        """
        url = DRIVE_DOMAIN + FILE_DELETE
        data = {"fileIds": fids}
        return self.session.request(url=url, method="POST", data=data)


class Yun139ShareManager:
    """分享管理"""

    def __init__(self, session: Yun139Session):
        self.session = session

    def create_share(
        self,
        title: str,
        url_type: int = 0,
        fid_list: List[str] = None,
        fld_list: List[str] = None,
        expired_time: int = 0,
    ) -> Tuple[bool, Any]:
        """
        创建分享链接
        :param title: 分享标题
        :param url_type: 分享类型 (0: 无密码；1: 有密码)
        :param fid_list: 要分享的文件ID列表
        :param fld_list: 要分享的文件夹ID列表
        :param expired_time: 过期时间 (0: 永久；其他：天数)
        """
        if fid_list is None:
            fid_list = []
        if fld_list is None:
            fld_list = []

        try:
            token = self.session.Token
            decode_bytes = base64.b64decode(token)
            decode_str = decode_bytes.decode('utf-8')
            splits = decode_str.split(":")
            if len(splits) < 3:
                return False, {"msg": "Token无效"}
        except:
            return False, {"msg": "解析Token失败"}

        data = {
            "getOutLinkReq": {
                "subLinkType": 0,
                "encrypt": url_type,
                "coIDLst": fid_list,
                "caIDLst": fld_list,
                "pubType": 1,
                "dedicatedName": title,
                "periodUnit": 1,
                "viewerLst": [],
                "extInfo": {
                    "isWatermark": 0,
                    "shareChannel": "3001"
                },
                "commonAccountInfo": {
                    "account": splits[1],
                    "accountType": 1
                }
            }
        }

        if expired_time > 0:
            data["getOutLinkReq"]["period"] = expired_time

        return self.session.request(url=SHARE, method="POST", data=data)


class Yun139UploadManager:
    """文件上传管理"""

    def __init__(self, session: Yun139Session):
        self.session = session

    def create_upload(
        self,
        file_name: str,
        file_path: str,
        parent_folder_id: str = "/",
    ) -> Tuple[bool, Any]:
        """
        创建文件上传任务
        :param file_name: 文件名
        :param file_path: 文件路径
        :param parent_folder_id: 父文件夹ID，默认根目录
        :return: (status, response_data)
        """
        import os
        try:
            file_size = os.path.getsize(file_path)
        except Exception as e:
            return False, f"获取文件大小失败: {str(e)}"

        chunk_size_bytes = 20 * 1024 * 1024
        num_chunks = (file_size + chunk_size_bytes - 1) // chunk_size_bytes

        partList = []
        for i in range(num_chunks):
            start = i * chunk_size_bytes
            end = min(start + chunk_size_bytes, file_size)
            chunk_size = end - start
            partList.append({
                "parallelHashCtx": {"partOffset": start},
                "partNumber": i + 1,
                "partSize": chunk_size
            })

        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
            content_hash = file_hash.hexdigest()
        except Exception as e:
            return False, f"计算文件哈希失败: {str(e)}"

        url = DRIVE_DOMAIN + FILE_CREATE
        data = {
            "parentFileId": parent_folder_id,
            "name": file_name,
            "type": "file",
            "size": file_size,
            "fileRenameMode": "auto_rename",
            "contentHash": content_hash,
            "contentHashAlgorithm": "SHA256",
            "contentType": "application/oct-stream",
            "parallelUpload": False,
            "partInfos": partList
        }

        status, resp = self.session.request(url=url, method="POST", data=data)
        if not status:
            return False, resp
        else:
            resp["content_hash"] = content_hash
            return True, resp

    def upload_chunk(
        self,
        file_path: str,
        upload_url: str,
        part_number: int,
    ) -> Tuple[bool, Any]:
        """
        上传文件分片
        :param file_path: 文件路径
        :param upload_url: 上传URL
        :param part_number: 分片编号
        :return: (status, message)
        """
        headers = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Origin": "https://yun.139.com",
            "Referer": "https://yun.139.com/",
            "Content-Type": "application/oct-stream",
        }

        try:
            chunk_size_bytes = 20 * 1024 * 1024
            with open(file_path, "rb") as f:
                f.seek((part_number - 1) * chunk_size_bytes)
                chunk_data = f.read(chunk_size_bytes)
        except Exception as e:
            return False, f"读取分片数据失败: {str(e)}"

        response = requests.put(upload_url, headers=headers, data=chunk_data)
        if response.status_code == 200:
            return True, f"上传分片{part_number}成功"
        else:
            return False, f"上传分片{part_number}失败: {response.status_code} {response.text}"

    def upload_complete(
        self,
        upload_id: str,
        fid: str,
        content_hash: str,
    ) -> Tuple[bool, Any]:
        """
        完成文件上传
        :param upload_id: 上传ID
        :param fid: 文件ID
        :param content_hash: 文件内容哈希
        """
        url = DRIVE_DOMAIN + FILE_COMPLETE
        data = {
            "fileId": fid,
            "uploadId": upload_id,
            "contentHash": content_hash,
            "contentHashAlgorithm": "SHA256"
        }
        return self.session.request(url=url, method="POST", data=data)

    def upload_file(
        self,
        file_name: str,
        file_path: str,
        pdir_fid: str = "/",
        progress_callback: Optional = None,
    ) -> Tuple[bool, Any]:
        """
        上传文件
        :param file_name: 文件名
        :param file_path: 文件路径
        :param pdir_fid: 父文件夹ID，默认为"/"（根目录）
        :param progress_callback: 进度回调函数，接受一个整数参数(0-100)
        :return: (status, response_data)
        """
        create_status, create_info = self.create_upload(
            file_name=file_name, file_path=file_path, parent_folder_id=pdir_fid
        )
        if not create_status:
            return False, create_info

        if create_info.get("rapidUpload"):
            return True, {"msg": "秒传成功", "fileId": create_info.get("fileId")}

        content_hash = create_info.get("content_hash")
        fileId = create_info.get("fileId")
        uploadId = create_info.get("uploadId")
        if not content_hash or not fileId or not uploadId:
            return False, create_info

        partList = create_info.get("partInfos")
        if not partList:
            return False, create_info

        upload_status = True
        for part in partList:
            part_number = part.get("partNumber", 1)
            upload_url = part.get("uploadUrl")
            status, msg = self.upload_chunk(file_path, upload_url, part_number)
            if not status:
                upload_status = False
                break

            if progress_callback:
                progress_callback(min(100, int(part_number / len(partList) * 100)))

        if not upload_status:
            return False, msg

        return self.upload_complete(upload_id=uploadId, fid=fileId, content_hash=content_hash)


class Yun139DownManager:
    """文件下载管理"""

    def __init__(self, session: Yun139Session):
        self.session = session

    def get_download_url(self, fid: str) -> Tuple[bool, Any]:
        """
        获取文件下载URL
        :param fid: 文件ID
        :return: (status, download_url或错误信息)
        """
        url = DRIVE_DOMAIN + FILE_DOWNLOAD
        data = {"fileId": fid}
        return self.session.request(url=url, method="POST", data=data)

    def download_file(
        self,
        fid: str,
        save_path: str,
        progress_callback: Optional = None,
    ) -> Tuple[bool, Any]:
        """
        下载文件
        :param fid: 文件ID
        :param save_path: 保存路径
        :param progress_callback: 进度回调函数，接受一个整数参数(0-100)
        :return: (status, message)
        """
        ok, data = self.get_download_url(fid)
        if not ok:
            return False, data

        download_url = data.get("url") or data.get("downloadUrl")
        if not download_url:
            return False, "获取下载链接失败"

        headers = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Referer": "https://yun.139.com/",
        }

        try:
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = int(downloaded / total_size * 100)
                            progress_callback(min(100, progress))

            return True, {"msg": "下载成功", "path": save_path}
        except Exception as e:
            return False, f"下载失败: {str(e)}"


def get_token_from_browser() -> str:
    """
    从浏览器获取token的辅助函数

    实际登录流程（通过playwright-cli浏览器自动化）：
    1. playwright-cli open "https://yun.139.com/w/#/"
    2. 填入手机号 -> 勾选协议（注意：协议勾选框是自定义DOM，非原生checkbox）
    3. 点击登录 -> 在手机上确认
    4. playwright-cli cookie-list
    5. 从cookie中找到 authorization=Basic xxxx，取完整的值作为token

    坑点提醒：
    - 协议勾选框不是原生<input type="checkbox">，而是<div class="check-img-wrap">，
      需要用JS点击：document.querySelector('.check-img-wrap').click()
    - 必须先勾选协议再点登录，否则会出现"请勾选同意相关协议政策"提示
    - 手机登录模式必须在手机上确认授权，无法自动完成
    """
    print("Token获取步骤：")
    print("1. playwright-cli open \"https://yun.139.com/w/#/\"")
    print("2. 登录后执行: playwright-cli cookie-list")
    print("3. 从输出中找到 authorization=Basic xxx 的值")
    return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python yun139_api.py <token> [命令] [参数...]")
        print("")
        print("命令:")
        print("  list [parent_id]     - 列出文件，默认根目录")
        print("  create <name> [parent_id] - 创建文件夹")
        print("  rename <fid> <new_name> - 重命名文件")
        print("  delete <fid> [...]   - 删除文件")
        print("  move <fid> [...] <target_folder_id> - 移动文件")
        print("  share <title> <folder_id> - 创建分享链接")
        print("  upload <file_path> [parent_id] - 上传文件，默认根目录")
        print("  download <fid> <save_path> - 下载文件")
        sys.exit(1)

    token = sys.argv[1]
    session = Yun139Session(token)
    folder_mgr = Yun139FolderManager(session)
    file_mgr = Yun139FileManager(session)
    share_mgr = Yun139ShareManager(session)
    upload_mgr = Yun139UploadManager(session)
    down_mgr = Yun139DownManager(session)

    if len(sys.argv) < 3:
        # 默认列出根目录
        ok, data = folder_mgr.get_lists("/")
        if ok:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"错误: {data}")
        sys.exit(0)

    cmd = sys.argv[2]

    if cmd == "list":
        parent_id = sys.argv[3] if len(sys.argv) > 3 else "/"
        ok, data = folder_mgr.get_lists(parent_id)
    elif cmd == "create":
        name = sys.argv[3]
        parent_id = sys.argv[4] if len(sys.argv) > 4 else "/"
        ok, data = folder_mgr.create_folder(name, parent_id)
    elif cmd == "rename":
        fid, new_name = sys.argv[3], sys.argv[4]
        ok, data = file_mgr.rename_file(fid, new_name)
    elif cmd == "delete":
        fids = sys.argv[3:]
        ok, data = file_mgr.remove_file(fids)
    elif cmd == "move":
        fids = sys.argv[3:-1]
        target = sys.argv[-1]
        ok, data = file_mgr.move_file(fids, target)
    elif cmd == "share":
        title, folder_id = sys.argv[3], sys.argv[4]
        ok, data = share_mgr.create_share(title, fld_list=[folder_id])
    elif cmd == "upload":
        import os
        file_path = sys.argv[3]
        parent_id = sys.argv[4] if len(sys.argv) > 4 else "/"
        file_name = os.path.basename(file_path)

        def progress(p):
            print(f"\r上传进度: {p}%", end="", flush=True)

        print(f"正在上传 {file_name} 到 {parent_id}...")
        ok, data = upload_mgr.upload_file(file_name, file_path, parent_id, progress_callback=progress)
        print()  # 换行
    elif cmd == "download":
        fid, save_path = sys.argv[3], sys.argv[4]

        def progress(p):
            print(f"\r下载进度: {p}%", end="", flush=True)

        print(f"正在下载文件 {fid} 到 {save_path}...")
        ok, data = down_mgr.download_file(fid, save_path, progress_callback=progress)
        print()  # 换行
        if ok:
            print(f"下载完成: {data}")
        else:
            print(f"错误: {data}")
        sys.exit(0)
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)

    if ok:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {data}")
