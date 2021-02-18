import os
import shutil
from hashlib import md5
from time import time

from helpers import split_file_path, get_sorted_file_paths, determine_new_file_path


def prefix_filename(file_path: str, prefix: str = '_'):
    if os.path.isdir(file_path):
        file_name = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        new_file_name = '{}{}'.format(prefix, file_name)
    else:
        directory, file_name, extension = split_file_path(file_path)
        new_file_name = '{}{}.{}'.format(prefix, file_name, extension)

    new_file_path = os.path.join(directory, new_file_name)
    os.rename(file_path, new_file_path)


def postfix_filename(file_path: str, postfix: str = '_'):
    if os.path.isdir(file_path):
        file_name = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        new_file_name = '{}{}'.format(file_name, postfix)
    else:
        directory, file_name, extension = split_file_path(file_path)
        new_file_name = '{}{}.{}'.format(file_name, postfix, extension)

    new_file_path = os.path.join(directory, new_file_name)
    os.rename(file_path, new_file_path)


def split_large_folder(directory_path: str, files_per_sub_folder: int = 100):
    """
    Split one directory into subdirectories of maximum 'files_per_sub_folder'.
    This can be useful when a directory becomes too large to download or upload at once, or to open in the filesystem.
    """
    destination_directory = None  # will be set in the first iterations, then every files_per_sub_folder times
    for index, file_path in enumerate(get_sorted_file_paths(directory_path=directory_path)):
        if index % files_per_sub_folder == 0:
            destination_directory = os.path.join(directory_path, str(index // files_per_sub_folder))
            os.mkdir(destination_directory)

        destination = os.path.join(destination_directory, os.path.basename(file_path))
        os.rename(file_path, destination)


def weed_out_files(directory_path: list, keep_one_file_out_of: int = 2):
    """
    Loop through all the files in the directory, ordered by filename, and permanently delete files.
    Only keep one file out of 'keep_one_file_out_of'.
    So if this parameter is set to 2, every second file will be deleted.
    If this parameter is set to 4, every 4th file is kept, and all others will be permanently deleted.

    This is useful for animation frames that take too much disk space. You can keep some amount of the still
    images, but get rid of most of them.
    """
    for index, file_path in enumerate(get_sorted_file_paths(directory_path=directory_path)):
        if index % keep_one_file_out_of > 0:
            os.unlink(file_path)


def make_filename_unrecognizable(file_path: str, keep_original: bool = True):
    """
    Rename the filename with a MD5 hash, based on the file path in combination with a filepath.
    This works for both file_paths and directories
    """
    if os.path.isfile(file_path):
        directory, file_name, extension = split_file_path(file_path)
        extension = '.{}'.format(extension)
    else:
        directory = os.path.dirname(file_path)
        extension = ''

    md5_hash = md5(bytes(file_path, 'utf-8'))
    md5_hash.update(bytes(str(time()), 'utf-8'))

    new_file_path = os.path.join(directory, '{}{}'.format(md5_hash.hexdigest(), extension))

    if keep_original:
        shutil.copy2(src=file_path, dst=new_file_path)
    else:
        os.rename(file_path, new_file_path)

    return new_file_path


def number_filenames(
    file_paths: list,
    start_index: int = 0,
    step: int = 1,
    number_prefix: str = '',
    pre_or_postfix: str = 'prefix'
):
    """
    Prefix the file paths (in alphabetically order) with a number (equally spaced, so when the maximum is 100, the first
    ones are 000, 001). The start index and step can be specified, so it can be 0100, 0200, 0300, 0400, etc.
    """
    length_largest_index = len(str(start_index + len(file_paths) * step))

    index = start_index
    for file_path in sorted(file_paths):
        # prefix the index_string with zero's when needed
        index_string = str(index)
        if len(index_string) < length_largest_index:
            index_string = '0' * (length_largest_index - len(index_string)) + index_string

        directory, file_name, extension = split_file_path(file_path)
        number_part = '{}{}'.format(number_prefix, index_string)

        if pre_or_postfix == 'postfix':
            new_file_name = '{}_{}.{}'.format(file_name, number_part, extension)
        else:
            new_file_name = '{}_{}.{}'.format(number_part, file_name, extension)

        os.rename(file_path, os.path.join(directory, new_file_name))

        index += step


number_filenames.combo_choices = {'pre_or_postfix': ['prefix', 'postfix']}


def sort_files_by_size(directory_path: str):
    """
    Go through all files in a directory, and look at the file size in bytes.
    If there is more then one files with the same size in bytes, make a sub_folder and move the files to there.
    Leave all the files with a unique size in the main directory.

    If every file was generated in a different way, you could detect identical outcomes
    (make sure the file name contains the relevant parameters, so you can understand which ones give the same result).
    """
    size_path_dict = dict()
    for file_path in get_sorted_file_paths(directory_path=directory_path):
        size_path_dict.setdefault(os.path.getsize(file_path), []).append(file_path)

    for file_size, paths in size_path_dict.items():
        if len(paths) > 1:
            # make a new folder, and move all the paths in there
            new_folder_path = os.path.join(directory_path, str(file_size))
            os.mkdir(new_folder_path)

            for file_path in paths:
                directory, file_name, extension = split_file_path(file_path)
                new_file_name = '{}.{}'.format(file_name, extension)

                os.rename(file_path, os.path.join(new_folder_path, new_file_name))


def duplicate_file(file_path: str, number_of_duplicates: int = 10):
    """
    Duplicate a file many times, every next one will be prefixed with (0), (1), (2), etc
    """
    for i in range(number_of_duplicates):
        # this can be more efficient (just adding i to the filename),
        # but the method below makes sure the new file name is unique
        new_path = determine_new_file_path(file_path)
        shutil.copy2(src=file_path, dst=new_path)
