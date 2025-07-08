class GitHubUploader:
    def __init__(self, token, repo_name):
        self.token = token
        self.repo_name = repo_name
        self.github = None
        self.authenticate()

    def authenticate(self):
        from github import Github
        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)

    def upload_file(self, source_filepath, target_filepath, commit_message):
        with open(source_filepath, 'rb') as file:
            content = file.read()
        try:
            contents = self.repo.get_contents(target_filepath)
            self.repo.update_file(contents.path, commit_message, content, contents.sha)
        except Exception:
            # 不存在则创建
            self.repo.create_file(target_filepath, commit_message, content)
            
        