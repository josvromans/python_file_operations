import os
import subprocess
import shutil
import glob

from helpers import split_file_path


def _make_movie(
    directory_path: str,
    movie_name: str = 'original',
    video_extension: str = 'mp4',
    image_extension: str = 'jpeg',
    reverse: bool = False,
    bitrate: int = 3300,
    frames_per_second: int = 30,
    codec: str = 'libx264',
    pixel_format: str = 'yuv420p',
    seconds_per_frame=None,
):
    """
    In Nautilus, I like to have two seperate methods available, 'make_movie' and 'make_slideshow'.
    That's why they are spilt up below in two seperate methods.
    """
    movie_name += '_br{}'.format(bitrate)  # add the bitrate to the movie name
    video_path = os.path.join(directory_path, '{}.{}'.format(movie_name, video_extension))
    target_path = os.path.join(directory_path, '*.{}'.format(image_extension))

    # 3300 works for instagram (but up to 3500 should work. Youtube can be 6000)
    bitrate_part = '-b:v {}k -bufsize {}k'.format(bitrate, bitrate)

    if seconds_per_frame is None:
        command = "ffmpeg -framerate {} -pattern_type glob -i '{}' {} -c:v {} -pix_fmt {} {}".format(
            frames_per_second, target_path, bitrate_part, codec, pixel_format, video_path)
    else:
        # generate a slideshow, where each still image will be duplicated frames_per_second * seconds_per_frame times
        command = "ffmpeg -framerate 1/{} -pattern_type glob -i '{}' {} -c:v {} -r {} -pix_fmt {} {}".format(
            seconds_per_frame, target_path, bitrate_part, codec, frames_per_second, pixel_format, video_path)

    proc = subprocess.Popen(command, shell=True)
    proc.wait()

    #
    # if desired, make a video in reverse, then add the original and the merged one together.
    #
    if reverse:
        reversed_video_path = os.path.join(directory_path, '{}_reversed.{}'.format(movie_name, video_extension))
        command = 'ffmpeg -i {} {} -vf reverse {}'.format(video_path, bitrate_part, reversed_video_path)
        proc = subprocess.Popen(command, shell=True)
        proc.wait()

        merge_videos(file_paths=[video_path, reversed_video_path], final_video_name='{}_final'.format(movie_name))

    #
    # move the stills to a sub folder 'stills'
    #
    separate_stills_folder = os.path.join(directory_path, 'stills')
    os.mkdir(separate_stills_folder)

    for image_file in glob.glob(os.path.join(directory_path, '*.{}'.format(image_extension))):
        shutil.move(image_file, separate_stills_folder)


def make_movie(
    directory_path: str,
    movie_name: str = 'original',
    video_extension: str = 'mp4',
    image_extension: str = 'jpeg',
    reverse: bool = False,
    bitrate: int = 3300,
    frames_per_second: int = 30,
    codec: str = 'libx264',
    pixel_format: str = 'yuv420p',
):
    """
    Use ffmpeg to make a movie from all the files in the given 'directory_path' that have the given 'image_extension'
    The image files will be places in a new sub folder 'stills'. The 'directory_path' will contain the movie file, and
    if 'reverse' was checked, a second reversed movie file will be created and a third movie file where the original
    and the reversed are merged into one file (this results in a looping video, start and end frame are equal).

    Make sure every image in the directory_path has the same dimensions. When this is not the case, the operation
    will fail without providing any feedback.
    """
    _make_movie(directory_path=directory_path, movie_name=movie_name, video_extension=video_extension,
                image_extension=image_extension, reverse=reverse, bitrate=bitrate, frames_per_second=frames_per_second,
                codec=codec, pixel_format=pixel_format)


def make_slideshow(
    directory_path: str,
    movie_name: str = 'slideshow',
    video_extension: str = 'mp4',
    image_extension: str = 'jpeg',
    reverse: bool = False,
    bitrate: int = 3300,
    frames_per_second: int = 30,
    codec: str = 'libx264',
    pixel_format: str = 'yuv420p',
    seconds_per_frame: int = 2,
):
    """
    Use ffmpeg to make a slideshow from all the files in the given 'directory_path' that have the given
    'image_extension'. Save it as a movie file.

    Everything will work similar to 'make_movie', except that now, single frames will be shown
    'seconds_per_frame'. So for 30 frames per second and 2 seconds per frame, there will be 60 frames with the
    same image, before continuing with the next image.
    """
    _make_movie(directory_path=directory_path, movie_name=movie_name, video_extension=video_extension,
                image_extension=image_extension, reverse=reverse, bitrate=bitrate, frames_per_second=frames_per_second,
                codec=codec, pixel_format=pixel_format, seconds_per_frame=seconds_per_frame)


movie_combo_choices = {
    'video_extension': ['mp4', 'mov'],

    # the codec / pixel format choices may not work in all combinations. Providing the list of all options seems to
    # be useless, since for some codecs the pixel format parameter should not be provided at all. This setup works
    # with the default values. For other values it is experimental, you have to read the ffmpeg documentation, and
    # it is likely that you have to change the ffmpeg command when you use other codecs.
    # See: https://ffmpeg.org/ffmpeg-codecs.html
    'codec': ['libx264', 'libx264rgb', 'libx265', 'libxvid'],  # ffmpeg -codecs for all the available ones
    # https://ffmpeg.org/ffmpeg-codecs.html#Supported-Pixel-Formats
    'pixel_format': ['yuv420p', 'yuv422p'],
}
make_movie.combo_choices = movie_combo_choices
make_slideshow.combo_choices = movie_combo_choices


def merge_videos(file_paths: list, in_alphabetical_order: bool = False, final_video_name: str = 'final'):
    """
    Paste several videos together, and make one final video file.
    When 'in_alphabetical_order' is checked, apply this on the file_paths sorted alphabetically.
    Otherwise the order of the provided file_paths will be used.
    """
    directory, file_name, extension = split_file_path(file_paths[0])
    videos_to_merge_file_name = 'videos_to_merge.txt'

    if in_alphabetical_order:
        file_paths = sorted(file_paths)

    with open(videos_to_merge_file_name, 'w') as out:
        text_to_write = '\n'.join(['file {}'.format(video_name) for video_name in file_paths])
        out.write(text_to_write)

    final_video_path = os.path.join(directory, '{}.{}'.format(final_video_name, extension))
    command = "ffmpeg -safe 0 -f concat -i {} -vcodec copy -acodec copy {}".format(
        videos_to_merge_file_name, final_video_path)

    proc = subprocess.Popen(command, shell=True)
    proc.wait()

    os.unlink(videos_to_merge_file_name)
