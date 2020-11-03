import git
from git import *
import shutil
from subprocess import call
import stat
import os


class GitOperations:
    @staticmethod
    def git_init(repo_local_path):
        git_init_repository = Repo.init(repo_local_path)
        print("initializing git repository \n")

    @staticmethod
    def git_clone(repo_local_path, clone_link):
        try:
            print("--- Start cloning '" + clone_link + "' into '" + repo_local_path + "'")
            git.Git(repo_local_path).clone(clone_link)
        except git.GitCommandError as error:
            print("Unable to Clone" + str(error))

    @staticmethod
    def git_pull(repo_pull, branch_name, clone_link):
        try:
            # origin = repo_pull.remotes.origin
            # origin.pull()
            # repo_pull.git.pull(clone_link)
            repo_pull.git.pull('origin', branch_name)
        except git.GitCommandError as error:
            print("branch doesn't exist" + str(error))

    @staticmethod
    def git_status(does_repo_exist):
        repo_status = Repo(does_repo_exist)
        print(repo_status.git.status())

    @staticmethod
    def git_add(does_repo_exist, files_to_be_committed):
        # modified to include the set of file names to be staged
        repo_add = Repo(does_repo_exist)
        for file in files_to_be_committed:
            repo_add.git.add(file)

    @staticmethod
    def git_restore(does_repo_exist, modified_files):
        repo_restore = Repo(does_repo_exist)
        # restores the files with only date time stamp change to its previous version
        for file in modified_files:
            repo_restore.git.restore(file)

    @staticmethod
    def git_commit(does_repo_exist):
        repo_commit = Repo(does_repo_exist)
        repo_commit.git.commit('-m', 'commit message from python script')

    @staticmethod
    def git_push(does_repo_exist, current_branch):
        repo_push = Repo(does_repo_exist)
        # origin = repo_push.remote(name='origin')
        # origin.push('--set-upstream', current_branch)
        repo_push.git.push('--set-upstream', 'origin', current_branch)

    @staticmethod
    def git_create_branch(repo_create_branch, b_name):
        origin = repo_create_branch.remote()
        repo_create_branch.create_head(b_name)
        # origin.push(b_name)
        print("Branch created", b_name)

    @staticmethod
    def git_check_if_branch_exists(repo_branch_exists, b_name):
        branch_exists = True
        try:
            repo_branch_exists.git.checkout(b_name)
        except git.GitCommandError as error:
            branch_exists = False
        return branch_exists

    @staticmethod
    def delete_git_copied_dir(git_dir):
        # if the directory exists, delete the working directory of the backup_local_repo
        for i in os.listdir(git_dir):
            if i.endswith('git'):
                tmp = os.path.join(git_dir, i)
                # before deleting the working directory, copy the .git directory
                # dest_path = os.path.join(content_folder, '.git')
                # unhide the .git file before unlinking
                while True:
                    call(['attrib', '-H', tmp])
                    break
                shutil.rmtree(tmp, onerror=GitOperations.on_rm_error)

    @staticmethod
    def on_rm_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)
