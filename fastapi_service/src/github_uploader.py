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
        from github import Github, InputGitTreeElement
        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)
        self.InputGitTreeElement = InputGitTreeElement

    def upload_file(self, source_filepath, target_filepath, commit_message):
        with open(source_filepath, 'rb') as file:
            content = base64.b64encode(file.read()).decode('utf-8')
        # Use synchronous upload to ensure file is uploaded before returning
        self.upload_contents(content, target_filepath, commit_message)
            
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
                print(f"[upload_contents] branch={self.branch} target_filepath={target_filepath}")
                st = time.time()
                ori_contents = self.repo.get_contents(target_filepath, ref=self.branch)
                self.repo.update_file(
                    ori_contents.path,
                    commit_message,
                    content,
                    sha=ori_contents.sha,
                    branch=self.branch,
                )
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
        get_url = f"{url}?ref={self.branch}"
        data = {
            "message": commit_message,
            "content": content,
            "branch": self.branch,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        print(f"[upload_contents_by_url] branch={self.branch} target_filepath={target_filepath}")
        print(f"[upload_contents_by_url] put_url={url}")
        print(f"[upload_contents_by_url] get_url={get_url}")
        try:
            response = None
            get_resp = requests.get(get_url, headers=headers)
            if get_resp.status_code == 200:
                sha = get_resp.json().get("sha")
                print(f"[upload_contents_by_url] GET 200 sha={sha}")
                if sha:
                    data["sha"] = sha
                response = requests.put(url, json=data, headers=headers)
            elif get_resp.status_code == 404:
                print("[upload_contents_by_url] GET 404 -> create")
                response = requests.put(url, json=data, headers=headers)
            else:
                get_resp.raise_for_status()

            if response is not None and response.status_code == 409:
                print("[upload_contents_by_url] PUT 409 -> refetch sha and retry")
                # Possible race: refetch sha then retry once.
                get_resp = requests.get(get_url, headers=headers)
                get_resp.raise_for_status()
                sha = get_resp.json().get("sha")
                print(f"[upload_contents_by_url] RETRY sha={sha}")
                if sha:
                    data["sha"] = sha
                    response = requests.put(url, json=data, headers=headers)

            if response is None:
                raise RuntimeError("upload_contents_by_url failed: no response from PUT request")
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

    def batch_upload(self, files, commit_message):
        """
        Upload multiple files in a single commit.

        Args:
            files: List of dict with keys: 'source_filepath' (optional), 'content' (optional),
                   'target_filepath' (required). Either source_filepath or content must be provided.
            commit_message: Commit message for the batch upload

        Example:
            files = [
                {'source_filepath': 'local/audio.mp3', 'target_filepath': 'episodes/2026-01-20/audio.mp3'},
                {'content': 'base64_encoded_content', 'target_filepath': 'episodes/2026-01-20/script.txt'}
            ]
        """
        try:
            # Get the current commit SHA
            branch = self.repo.get_branch(self.branch)
            base_tree = branch.commit.commit.tree

            # Prepare tree elements for all files
            tree_elements = []
            for file_info in files:
                target_path = file_info['target_filepath']

                # Get content either from file or directly
                if 'source_filepath' in file_info:
                    with open(file_info['source_filepath'], 'rb') as f:
                        content = base64.b64decode(base64.b64encode(f.read()).decode('utf-8'))
                elif 'content' in file_info:
                    # Assume content is already base64 encoded
                    content = base64.b64decode(file_info['content'])
                else:
                    raise ValueError(f"File {target_path} must have either 'source_filepath' or 'content'")

                # Create blob
                blob = self.repo.create_git_blob(base64.b64encode(content).decode('utf-8'), 'base64')

                # Add to tree elements
                tree_elements.append(
                    self.InputGitTreeElement(
                        path=target_path,
                        mode='100644',  # Regular file
                        type='blob',
                        sha=blob.sha
                    )
                )

            # Create new tree
            new_tree = self.repo.create_git_tree(tree_elements, base_tree)

            # Create commit
            parent_commit = branch.commit.commit  # Get GitCommit object instead of Commit
            new_commit = self.repo.create_git_commit(commit_message, new_tree, [parent_commit])

            # Update branch reference
            ref = self.repo.get_git_ref(f'heads/{self.branch}')
            ref.edit(new_commit.sha)

            print(f"Batch upload successful: {len(files)} files uploaded in commit {new_commit.sha[:7]}")

        except Exception as e:
            print(f"batch_upload failed: {type(e).__name__}: {e}")
            raise

    def get_content(self, filepath):
        return self.repo.get_contents(filepath)
