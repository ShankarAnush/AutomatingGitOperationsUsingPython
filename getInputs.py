import os
import validators
import shutil
import time


class GetInputs:

    @staticmethod
    def get_placement_path(content_folder):
        # content_folder = input("Enter a folder path which contains the updated html files \n")
        if os.path.exists(content_folder):
            return content_folder
        else:
            print("Enter a valid folder path \n")
            # self.get_placement_path(content_folder)

    @staticmethod
    def get_clone_link(clone_link):
        #clone_link = input("Enter the repo clone link\n")
        valid = validators.url(clone_link)
        if valid:
            return clone_link
        else:
            print("Invalid link")

    @staticmethod
    def get_branch_name(branch_name):
        # branch_name = input("Enter the branch name \n")
        if branch_name == "":
            print("Enter valid branch name \n")
            # self.get_branch_name(branch_name)
        else:
            return branch_name

    @staticmethod
    def get_branch_type(branch_type):
        # branch_type = input("Enter the branch type \n")
        branch_type = branch_type.lower()
        # check if the string is empty
        if branch_type == 'feature' or branch_type == 'release' or branch_type == 'hotfix' or branch_type == 'bugfix' or branch_type == 'custom' or branch_type == 'master' or branch_type == "":
            print("Attention: The entered value '" + branch_type + "' is invalid! Enter valid branch type \n")
            # self.get_branch_type(branch_type)
        else:
            return branch_type

    @staticmethod
    def get_output_folder(import_folder):
        # import_folder = input("Enter the folder path to which the modified files have to be copied \n")
        if os.path.exists(import_folder):
            # when already exists delete the contents and recreate the base folder
            shutil.rmtree(import_folder)
            time.sleep(1)
            os.makedirs(import_folder, mode=0o777)
            return import_folder
        else:
            # create that directory
            os.makedirs(import_folder, mode=0o777)
            # self.get_import_folder()
            return import_folder
