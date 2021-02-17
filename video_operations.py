import os
import subprocess
import shutil
import glob

from helpers import split_file_path


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
    """
    movie_name += '_br{}'.format(bitrate)  # add the bitrate to the movie name
    video_path = os.path.join(directory_path, '{}.{}'.format(movie_name, video_extension))
    target_path = os.path.join(directory_path, '*.{}'.format(image_extension))

    # 3300 works for instagram (but up to 3500 should work. Youtube can be 6000)
    bitrate_part = '-b:v {}k -bufsize {}k'.format(bitrate, bitrate)
    command = "ffmpeg -framerate {} -pattern_type glob -i '{}' {} -c:v {} -pix_fmt {} {}".format(
        frames_per_second, target_path, bitrate_part, codec, pixel_format, video_path)

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


make_movie.combo_choices = {
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


def merge_videos(file_paths: list, final_video_name: str = 'final'):
    directory, file_name, extension = split_file_path(file_paths[0])
    videos_to_merge_file_name = 'videos_to_merge.txt'

    with open(videos_to_merge_file_name, 'w') as out:
        text_to_write = '\n'.join(['file {}'.format(video_name) for video_name in file_paths])
        out.write(text_to_write)

    final_video_path = os.path.join(directory, '{}.{}'.format(final_video_name, extension))
    command = "ffmpeg -safe 0 -f concat -i {} -vcodec copy -acodec copy {}".format(
        videos_to_merge_file_name, final_video_path)

    proc = subprocess.Popen(command, shell=True)
    proc.wait()

    os.unlink(videos_to_merge_file_name)


# TODO: make movie slideshow!