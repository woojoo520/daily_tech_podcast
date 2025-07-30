from github_uploader import GitHubUploader
from config import *

github_helpers = GitHubUploader(GITHUB_TOKEN, GITHUB_REPO)

src_filepath = "/Users/mini/woojoo/daily_tech_podcast/fastapi_service/output/output_total_1753358519.mp3"
tar_filepath = "test_audio.mp3"

try:
    github_helpers.upload_file(
        source_filepath=src_filepath,
        target_filepath=tar_filepath,
        commit_message="tset upload"   
    )
except Exception as e:
    print("Exception: ", e)

import time 
time.sleep(300)


# import base64
# import requests

# # 参数配置
# branch = "main"
# commit_message = "Add audio for 2025-07-24"   

# # 读取并编码文件内容
# with open(src_filepath, "rb") as f:
#     encoded_content = base64.b64encode(f.read()).decode("utf-8")

# # 构建 API URL
# url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{tar_filepath}"

# # 构建请求体
# data = {
#     "message": commit_message,
#     "content": encoded_content,
#     "branch": branch
# }

# # 构建请求头
# headers = {
#     "Authorization": f"Bearer {GITHUB_TOKEN}",
#     "Accept": "application/vnd.github+json"
# }

# print(f"url: {url} \n headers: {headers}")

# # 发起 PUT 请求
# response = requests.put(url, json=data, headers=headers)

# # 打印结果
# print(response.status_code)
# print(response.json())
