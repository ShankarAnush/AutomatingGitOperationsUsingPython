# -*- coding: utf-8 -*
module_description = """This module identifies all changes of the technical documentation of a project. 

Summary and Assumptions:
The calculation of changes is done by using the Git utilities. This allows to identify added, modified and deleted files. 
Each product has a so called Backup repository. This repository contains the html content used for import into the Main Internal Documentation Area (Confluence). 
Purpose of this is to reduce the network traffic when importing content into Confluence. Only modified and new files will be imported and all other files will be skipped.
 \r\n
This module expected that the technical documentation has already been converted and that the result is located inside of a folder. 
Furthermore it is expected that the Backup repository exists already.
 \r\n
Workflow description \r\n
1. Read command line options \r\n
2. Clone the Backup Git repository and checkout the version specific branch \r\n
3. Calculate the delta between the tip of the branch and the given input directory \r\n
4. Copy all changed files into a separate folder that will be used for the import \r\n
"""
import time
import tempfile
import git
import os
from git_Operations import GitOperations
from getInputs import GetInputs
from distutils.dir_util import copy_tree
import shutil
import stat
import sys
import errno
from subprocess import call
import argparse

# As alternative the tempdir could be used for the backup repository
#defaultTmpRepositoryRoot = tempfile.gettempdir()
parser = argparse.ArgumentParser(description=module_description)
#
parser.add_argument('--input_folder', help='Absolute path to the folder that contains the converted html files', required=True)
parser.add_argument('--git_url', help='URL to the Git repository', required=True)
parser.add_argument('--branch_name', help='Branch name of the remote Backup repository', required=True)
parser.add_argument('--output_folder', help='Absolute path to the folder that contains the files which should be imported into the Common Documentation Platform.', required=True)
parser.add_argument('--date_time_stamp_regex_1', help='Regular expression to match the revision date and time stamp', required=True)
parser.add_argument('--date_time_stamp_regex_2', help='Regular expression to match the last updated date and time stamp', required=True)
parser.add_argument('--repository_root', help='Absolute path to the root directory the Backup Repository should be stored to. If not defined a temp folder is used.', default=os.path.abspath(os.path.join(os.getcwd(), os.pardir)))

args = parser.parse_args()

#  get the current working directory
get_inputs = GetInputs()  # instance of a class
git_operations = GitOperations()

def on_rm_error(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        # It is the Permission error caused while deleting working directory
        os.chmod(path, stat.S_IWUSR & stat.S_IWRITE)
        os.unlink(path)
    else:
        raise

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
print(parser.print_help())

if __name__ == "__main__": 
    
    print("--- Verify content folder '", args.input_folder, "'")
    input_folder = get_inputs.get_placement_path(args.input_folder)
    branch_name = args.branch_name
    git_url = args.git_url
    output_folder = args.output_folder
    repository_root = args.repository_root

    current_path = os.getcwd()
    print("--- Current directory = '" + current_path + "'")
    # get the parent directory
    #repository_root = os.path.abspath(os.path.join(current_path, os.pardir))
    print("--- Parent directory = '" + repository_root + "'")

    print("--- Check if the repo is already cloned")
    # splits the string according to / and gets the last split part i.e. -1
    dir_name = str(git_url.split('/')[-1]).replace('.git', '')

    os.chmod(repository_root, stat.S_IWRITE)
    backup_repository_path = repository_root + "\\" + dir_name
    print("--- Backup repository path = '" + backup_repository_path + "'")

    if os.path.exists(backup_repository_path):
        print("--- Backup repository folder exists already. Cleanup will be done ...")
        shutil.rmtree(backup_repository_path, ignore_errors=False, onerror=on_rm_error)
        print("--- ... Cleanup finished.")
    else:
        print("--- Backup repository working dir does not exist yet and will be created.")
        os.makedirs(backup_repository_path)
        os.chmod(backup_repository_path, stat.S_IWRITE)
    #
    # clone the repository to a local directory
    GitOperations.git_clone(repository_root, git_url)

    print("--- Get instance of the Git repository")
    repo = git.Repo(backup_repository_path)
    
    # Now before deleting the working directory, check if the branch exists in the repo and do checkout
    print("--- Check if the given branch exists in the Backup repository and do checkout")
    branch_exists = GitOperations.git_check_if_branch_exists(repo, branch_name)

    # if branch doesn't exist then create that branch
    if branch_exists:
        # perform git pull to pull the latest changes, if any
        print("--- Branch exist")
        GitOperations.git_pull(repo, branch_name, git_url)
    else:
        GitOperations.git_create_branch(repo, branch_name)

    # checkout the branch
    repo.git.checkout(branch_name)

    # TODO: Clarify if this is really correct
    #
    # delete the working directory of the backup_local_repo
    print("--- Delete the working directory of the local backup repository")
    for item in os.listdir(backup_repository_path):
        if item.endswith('git'):
            continue
        else:
            abs_file_path = os.path.abspath(os.path.join(backup_repository_path, item))
            if os.path.exists(abs_file_path):
                print("--- Delete item '" + abs_file_path + "'")
                if os.path.isfile(abs_file_path):
                    os.unlink(abs_file_path)
                else:
                    shutil.rmtree(abs_file_path, ignore_errors=False, onerror=on_rm_error)
                    #
            else:
                print("--- Item '"+ abs_file_path +"' does not exist.")
    print("--- Copy the content from the input folder '" + input_folder + "' to the working directory '" +  backup_repository_path + "'of the Backup repository")
    # when copied, it recreates the working directory if it doesn't exist
    copy_tree(input_folder, backup_repository_path)  # this should overwrite the existing content

    # folder path to which you want to copy the modified files
    print("--- Cleanup folder '" + output_folder + "'")
    output_folder = get_inputs.get_output_folder(output_folder)

    print("--- All modified files will be copied to '" + output_folder + "' ...")
    print("--- Check git status")
    GitOperations.git_status(backup_repository_path)

    print("--- Create a list to append the modified and staged files")
    modified_untracked_files = list()   # contains all but deleted files
    files_to_be_committed = set()  # set that contains the files to be pushed to the backup repository
    deleted_files = set()   # set of deleted files
    # get the list of the modified and staged files
    print("---------------------------Checking files for the modified content------------------------------")
    print("-----------------------If modified content is only the date time stamp--------------------------")
    print("--------------------------------Do not commit or copy such file---------------------------------")
    for file_folder in repo.index.diff(None):
        # a_rawpath gives the name of the file along with the path
        # copy the modified files to output_folder

        srcpath = os.path.join(backup_repository_path, file_folder.a_rawpath.decode("utf-8").replace("/", "\\"))
        destinationpath = os.path.join(output_folder, file_folder.a_rawpath.decode("utf-8").replace("/", "\\"))
        # since this also contains deleted files, you cannot copy those once you delete them
        if os.path.exists(srcpath):
            # to check if the modified files belong to the intricate folders
            # also extract the changed lines from the file
            changed_lines = repo.git.diff(srcpath)  # multiple lines as string
            # ----------------------------- parsing the selected string ------------------------------
            changed_lines = str(changed_lines).split("\n")
            interested_Files = [line for line in changed_lines if line[0] == "+" and line[1] != "+"]
            print(interested_Files)
            # ----------------------------- parsing complete ------------------------------------------
            # regular expressions matching the date time stamp lines
            # date_time_stamp_regex_1 = re.compile("[+].span id=\"revdate\".[0-9]+.[0-9]+.[0-9]+./span.")
            date_time_stamp_regex_1 = re.compile(args.date_time_stamp_regex_1)
            # date_time_stamp_regex_2 = re.compile("[+]Last updated [0-9]+.[0-9]+.[0-9]+ [0-9]+.[0-9]+.[0-9]+ CEST")
            date_time_stamp_regex_2 = re.compile(args.date_time_stamp_regex_2)
            if os.path.exists(os.path.dirname(destinationpath)):
                pass
            else:
                os.makedirs(os.path.dirname(destinationpath))
            # ------------------- Check if the parsed lines in interested_Items matches with the regex-------------------
            # ------------- if the date time stamp is the only modification in the file, don't copy the file--------------
            for item in interested_Files:
                if date_time_stamp_regex_1.search(item) or date_time_stamp_regex_2.search(item):
                    # do not copy such files to the import folder
                    pass
                else:
                    files_to_be_committed.add(file_folder.a_rawpath.decode("utf-8"))    # files that have to be pushed
                    shutil.copyfile(srcpath, destinationpath)   # copy only these files into import folder
            modified_untracked_files.append(file_folder.a_rawpath.decode("utf-8"))  # contains all but deleted files
        else:
            deleted_files.add(file_folder.a_rawpath.decode("utf-8"))    # files that have to be deleted from the repo
    print("--- Check untracked files ...")
    for file_folder_new in repo.untracked_files:
        srcpath_new = os.path.join(backup_repository_path, file_folder_new.replace("/", "\\"))
        destinationpath_new = os.path.join(output_folder, file_folder_new.replace("/", "\\"))
        # For all intricate folders, check if the folders exist first
        # if not create the folders before copying file
        if os.path.exists(os.path.dirname(destinationpath_new)):
            pass
        else:
            os.makedirs(os.path.dirname(destinationpath_new))
        shutil.copyfile(srcpath_new, destinationpath_new)
        files_to_be_committed.add(file_folder_new)  # files that have to be pushed to the repository
        modified_untracked_files.append(file_folder_new)

    print(modified_untracked_files)
    print("\n***************** Add the set of deleted files to the set of files to be staged ****************")
    # set of all deleted html files
    htmlFilesToDeletedFolder = set()
    # adding file to the set is possible only if the count of deleted files is greater than zero
    print("collecting all deleted html files, if any...........")
    if len(deleted_files) > 0:
        for file in deleted_files:
            files_to_be_committed.add(file)
            # check the extension of the file
            if file.endswith('.html'):
                htmlFilesToDeletedFolder.add(file)
            else:
                pass
    # "DELETED" folder path that contains all the deleted html files in the form of empty files
    deletedFolderPath = backup_repository_path + "\\" + "DELETED"
    # check if the "DELETED" folder exists!
    if os.path.exists(deletedFolderPath):
        os.chmod(deletedFolderPath, stat.S_IWRITE)
    else:
        os.makedirs(deletedFolderPath)
        os.chmod(deletedFolderPath, stat.S_IWRITE)
    print("To also delete the files from the confluence, write the deleted file names into a text file in DELETED folder")
    # get the list of all the delted fiels in the repository over all the commits
    repo_object = git.Git(backup_repository_path)
    with open(deletedFolderPath + "\\" + "deletedHTMLFiles.txt", 'a') as fp:
        fp.write(repo_object.log('--pretty=format:', '--name-only', '--diff-filter=D'))
        if len(htmlFilesToDeletedFolder) > 0:
            for deletedHTMLFile in htmlFilesToDeletedFolder:
                fp.write("\n{}".format(deletedHTMLFile))
        fp.close()
    # if the file with a same name as the previously deleted file is created, then it's name should be removed from the..
    # ..file containing the deleted html file names
    with open(deletedFolderPath + "\\" + "deletedHTMLFiles.txt", 'r') as rp:
        lines = rp.readlines()
        rp.close()
        check_flag = 0
        for item in modified_untracked_files:
            for line in lines:
                if line.strip("\n") == item:
                    lines.remove(line)
                    check_flag += 1
    # write back to file only if there are any modification to the read lines
    if check_flag > 0:
        with open(deletedFolderPath + "\\" + "deletedHTMLFiles.txt", 'w') as wp:
            wp.writelines(lines)
            wp.close()
    print(" \n************************************ Files to be pushed to the backup repository ************************************\n")
    print(files_to_be_committed)
    print("\n***************** Find the modified files other than the one with modified date time stamp ****************")
    for fileItem in files_to_be_committed:
        try:
            modified_untracked_files.remove(fileItem)
        except ValueError as error:
            print("file {} is not present in the list of modified files".format(fileItem))
        # could be used to restore files with only date_time stamp modification, if needed in the future
    print("***********************************************************************************************************\n")

    # commit and push the changes only if there are any modified files apart from data_time_stamp modification
    if len(files_to_be_committed) > 0:
        if repo.index.diff(None) or repo.untracked_files:
            print("--- Add the changed files to stage ...")
            GitOperations.git_add(backup_repository_path, files_to_be_committed)
            print("--- Status after all the changes ...")
            GitOperations.git_status(backup_repository_path)
            print("--- Commit the changes to the local branch in the local repo ...")
            GitOperations.git_commit(backup_repository_path)
            print("--- push the changes to the repo ...")
            GitOperations.git_push(backup_repository_path, repo.active_branch)
        elif repo.iter_commits('BRANCH..BRANCH@{u}'):
            print("--- PUSH changes ...")
            repo.git.push('origin', branch_name)
        else:
            pass
        
    else:
        print("\n************ There are no modified files **************")
    print("\n end handling of Backup repository.")