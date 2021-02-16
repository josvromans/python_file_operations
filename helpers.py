import glob
import os


def get_sorted_file_paths(directory_path):
    return sorted(glob.glob(os.path.join(directory_path, '*')))


def split_file_path(file_path):
    file_name = os.path.basename(file_path)
    directory = os.path.dirname(file_path)

    split_file_name = file_name.split('.')
    extension = split_file_name[-1]
    file_name = '.'.join(split_file_name[:-1])

    return directory, file_name, extension


def sort_and_filter_extensions(file_paths, allowed_extensions=None):
    if allowed_extensions:
        file_paths = [file_path for file_path in file_paths if file_path.split('.')[-1].lower() in allowed_extensions]

    return sorted(file_paths)


def put_originals_in_subdirectory(file_paths):
    """
    For some file operations, instead of permanently deleting the originals,
    put them in a subdirectory 'original', so the user can easily delete them afterwards.
    """
    directory, file_name, extension = split_file_path(file_paths[0])

    destination_directory = os.path.join(directory, 'originals')
    if not os.path.exists(destination_directory):
        os.mkdir(destination_directory)

    for file_path in file_paths:
        os.rename(
            src=file_path,
            dst=os.path.join(destination_directory, os.path.basename(file_path))
        )


def determine_new_file_path(new_file_path):
    directory, file_name, extension = split_file_path(new_file_path)

    new_path_without_extension = os.path.join(directory, file_name)

    index = 0
    new_path = '{}({}).{}'.format(new_path_without_extension, index, extension)

    while os.path.exists(new_path):
        index += 1
        new_path = '{}({}).{}'.format(new_path_without_extension, index, extension)

    return new_path


def save_image(pil_image, new_file_path, enforce_unique_path=True, image_format=None):
    """
    If the new_file_path already exists, determine a unique name, like new_file_path(2).jpeg

    In case it is a jpeg file, always save it in highest quality.
    """
    if enforce_unique_path and os.path.exists(new_file_path):
        new_file_path = determine_new_file_path(new_file_path)

    extra_params = {}
    if pil_image.format == 'JPEG':
        extra_params['quality'] = 100

    pil_image.save(
        fp=new_file_path,
        format=pil_image.format if image_format is None else image_format,
        **extra_params,
    )
    return new_file_path
