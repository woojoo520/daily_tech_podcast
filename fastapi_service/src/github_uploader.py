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
            content = file.read()
        self.upload_contents(content, target_filepath, commit_message)
            
    
    def upload_contents(self, content, target_filepath, commit_message):
        try:
            print(f"target_filepath: {target_filepath}")
            ori_contents = self.repo.get_contents(target_filepath)
            self.repo.update_file(ori_contents.path, commit_message, content, sha=ori_contents.sha)
        except Exception:
            self.repo.create_file(target_filepath, commit_message, content)
            
    def get_content(self, filepath): 
        return self.repo.get_contents(filepath)