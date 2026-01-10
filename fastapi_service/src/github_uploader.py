import base64
import time
import threading


class GitHubUploader:
    def __init__(self, token, repo_name, branch="main"):
        self.token = token
        self.repo_name = repo_name
        self.github = None
        self.branch = branch
        self.authenticate()
        self.base_path = f"https://github.com/{self.repo_name}/blob/{self.branch}/"
        self.source_base_path = f"https://raw.githubusercontent.com/{self.repo_name}/refs/heads/{self.branch}/"
        
    def authenticate(self):
        from github import Github
        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)

    def upload_file(self, source_filepath, target_filepath, commit_message):
        with open(source_filepath, 'rb') as file:
            content = base64.b64encode(file.read()).decode('utf-8')
        self.upload_in_background(content, target_filepath, commit_message)
            
    def upload_in_background(self, content, target_filepath, commit_message):
        thread = threading.Thread(
            target=self.upload_contents, 
            args=(content, target_filepath, commit_message, ), 
            daemon=True
        )
        thread.start()
    
    def upload_contents(self, content, target_filepath, commit_message):
        try:
            try:
                print(f"target_filepath: {target_filepath}")
                st = time.time()
                ori_contents = self.repo.get_contents(target_filepath)
                self.repo.update_file(ori_contents.path, commit_message, content, sha=ori_contents.sha)
                en = time.time() 
                print(f"Upload time cost: {en - st}s.")
            except Exception as e:
                # Only fall back to create when the file truly does not exist.
                try:
                    from github import GithubException
                    if isinstance(e, GithubException) and e.status == 404:
                        print("File not exists, try to create new file")
                        self.upload_contents_by_url(content, target_filepath, commit_message)
                    else:
                        raise
                except Exception as inner_e:
                    print(f"upload_contents failed: {type(inner_e).__name__}: {inner_e}")
                    raise
        except Exception as e:
            print(f"github api failed, reason: {type(e).__name__}: {e}.\nUpload file by sending request...")
            # self.upload_contents_by_url(content, target_filepath, commit_message)


    def upload_contents_by_url(self, content, target_filepath, commit_message):
        import requests

        url = f"https://api.github.com/repos/{self.repo_name}/contents/{target_filepath}"
        data = {
            "message": commit_message,
            "content": content,
            "branch": 'main'
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        print(f"url: {url} \n headers: {headers}")
        try:
            response = requests.put(url, json=data, headers=headers)
            if response.status_code == 409:
                # File exists: fetch SHA and retry as update.
                get_resp = requests.get(url, headers=headers)
                get_resp.raise_for_status()
                sha = get_resp.json().get("sha")
                if sha:
                    data["sha"] = sha
                    response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            print(f"response: {response}")
        except Exception as e: 
            detail = ""
            try:
                if response is not None:
                    detail = f" status={response.status_code} body={response.text}"
            except Exception:
                pass
            print(f"upload_contents_by_url failed: {type(e).__name__}: {e}.{detail}")

    def get_content(self, filepath): 
        return self.repo.get_contents(filepath)
