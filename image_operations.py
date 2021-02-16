import os
import random

from PIL import Image, ImageFilter, ImageChops

from helpers import split_file_path, save_image


def resize_image(file_path: str, new_width: int = 1080, new_height: int = 1080, resample: str = 'LANCZOS'):
    """
    Resize the image to the given dimensions (new_width, new_height).

    If the new_width is 0, and the new_height is a positive value, calculate a value for the width in such way
    that the original ratio is maintained, and the new_height is exactly the given new_height.
    Do the same if the new_height is 0 and the new_width a positive value.
    """
    image = Image.open(file_path)

    original_width, original_height = image.size
    if new_width == 0 and new_height > 0:
        new_width = int(original_width * new_height / original_height)
    elif new_height == 0 and new_width > 0:
        new_height = int(original_height * new_width / original_width)
    elif not(new_height > 0 and new_width > 0):
        return

    image = image.resize(size=(new_width, new_height), resample=getattr(Image, resample))
    directory, file_name, extension = split_file_path(file_path)
    return save_image(
        pil_image=image,
        new_file_path=os.path.join(directory, '{}_resized.{}'.format(file_name, extension))
    )


resize_image.combo_choices = {'resample': [
    # these are defined as integers in PIL (Image.LANCZOS = 1). For readability and ease in the combo boxes,
    # these string values are used. Note that ANTIALIAS is exactly the same as LANCZOS
    'NEAREST', 'LANCZOS', 'BILINEAR', 'BICUBIC', 'BOX', 'HAMMING', 'ANTIALIAS'
]}


def add_margin(
    file_path: str,
    margin: int = 100,
    background_color: tuple = (0, 0, 0),
):
    """
    Take the original image from the file_path, then resize it, so it can be pasted on a new
    image, that has the same dimensions as the original image, but with an equal margin on all sides around
    the (resized) original image.
    """
    original_image = Image.open(file_path)
    original_width, original_height = original_image.size
    original_dimensions = original_image.size

    new_image = Image.new(mode=original_image.mode, size=original_dimensions, color=background_color)

    original_image = original_image.resize(
        size=(original_width - 2 * margin, original_height - 2 * margin),
        resample=Image.LANCZOS,
    )
    new_image.paste(im=original_image, box=(margin, margin))

    directory, file_name, extension = split_file_path(file_path)
    new_file_path = os.path.join(directory, '{}_with_margin{}.{}'.format(file_name, margin, extension))
    return save_image(pil_image=new_image, new_file_path=new_file_path)


add_margin.color_parameters = ('background_color', )


def calculate_box_tuples(width: int, height: int, x: int = 2, y: int = 2):
    """
    Cut an image in equal rectangular parts.

    For example: if an 1000 x 1000 image is divided in 2 by 2 parts (x = 2 and y = 2)

    return [
        (0, 0, 500, 500),  # x_index = 0, y_index = 0
        (0, 500, 500, 1000),  # x_index = 0, y_index = 1
        (500, 0, 1000, 500),  #

        (500, 500, 1000, 1000),
    ]

    The steps will be rounded integer values. All parts will have equal dimensions, except the ones that are on the
    right or bottom. They will get their 'edge' coordinate to equal the width and/or height of the original image,
    so no data will be lost. This will make up for the rounding.
    """
    x_step = int(width / x)
    y_step = int(height / y)

    box_tuples = []
    for x_index in range(x):
        for y_index in range(y):
            if x_index == x - 1:
                # it is the last x iteration, the right coordinate should equal the image width
                x_bottom_right = width
            else:
                x_bottom_right = (x_index + 1) * x_step

            if y_index == y - 1:
                # it is the last y iteration, the bottom coordinate should equal the image height
                y_bottom_right = height
            else:
                y_bottom_right = (y_index + 1) * y_step

            box_tuples.append(
                (x_index * x_step,
                 y_index * y_step,
                 x_bottom_right,
                 y_bottom_right),
            )

    return box_tuples


def crop_image_in_equal_parts(file_path: str, x: int = 2, y: int = 2):
    """
    Take an image, and save x * y cropped parts of the image
    """
    image = Image.open(file_path)
    directory, file_name, extension = split_file_path(file_path)

    width, height = image.width, image.height

    new_file_names = []
    for index, dimensions in enumerate(calculate_box_tuples(width, height, x=x, y=y)):
        cropped_image = image.crop(dimensions)

        new_file_path = os.path.join(directory, '{}_crop{}.{}'.format(file_name, index, extension))

        save_image(pil_image=cropped_image, new_file_path=new_file_path, image_format=image.format)
        new_file_names.append(new_file_path)

    return new_file_names


def get_resize_ratio(image_width: int, image_height: int, new_image_size: tuple):
    # if needed, resize the image first
    resize_ratio = 1
    if image_width > new_image_size[0]:
        resize_ratio = new_image_size[0] / image_width
    if image_height > new_image_size[1]:
        resize_ratio_2 = new_image_size[1] / image_height

        # in case there was also a resize ratio determined for the width
        resize_ratio = min(resize_ratio, resize_ratio_2)

    return resize_ratio


def paste_image_in_center(
    file_path: str,
    new_image_width: int = 1920,
    new_image_height: int = 1080,
    background_color: tuple = (255, 255, 255),
):
    """
    Paste the original image in a new frame with the given dimensions.
    Add margin around the image, such that the original image will be in the center.

    When the original image is larger then the new desired dimensions, resize the original image first.

    Example use case if an square image should be pasted on another specific format, like a 13:9 YouTube still
    """
    new_image_size = (new_image_width, new_image_height)
    image = Image.open(file_path)
    image_width = image.width
    image_height = image.height

    resize_ratio = get_resize_ratio(
        image_width=image_width, image_height=image_height, new_image_size=new_image_size
    )
    if resize_ratio != 1:
        # the image has to be resized
        new_width = int(resize_ratio * image_width)
        new_height = int(resize_ratio * image_height)
        image = image.resize((new_width, new_height), Image.LANCZOS)

    delta_x = int((new_image_size[0] - image.width) / 2)
    delta_y = int((new_image_size[1] - image.height) / 2)

    new_image = Image.new(mode=image.mode, size=new_image_size, color=background_color)
    new_image.paste(im=image, box=(delta_x, delta_y))

    directory, file_name, extension = split_file_path(file_path)

    new_file_path = os.path.join(directory, '{}_centered{}x{}.{}'.format(
        file_name, new_image_size[0], new_image_size[1], extension))
    return save_image(pil_image=new_image, new_file_path=new_file_path, image_format=image.format)


paste_image_in_center.color_parameters = ('background_color', )


def crop_center(file_path: str, new_width: int = 1080, new_height: int = 1080):
    """
    Crop a new image of dimensions (new_width, new_height) from the center of the original image
    (equal margins left over on all sides)
    """
    image = Image.open(file_path)

    if image.width < new_width or image.height < new_height:
        return

    diff_x = image.width - new_width
    diff_y = image.height - new_height

    left = int(diff_x / 2)
    right = int(diff_x / 2) + new_width
    top = int(diff_y / 2)
    bottom = int(diff_y / 2) + new_height

    image = image.crop((left, top, right, bottom))

    directory, file_name, extension = split_file_path(file_path)
    new_file_path = os.path.join(directory, '{}_cropped_center.{}'.format(file_name, extension))

    return save_image(pil_image=image, new_file_path=new_file_path)


class RandomFilter(ImageFilter.BuiltinFilter):
    name = "Random"
    filterargs = (3, 3), random.randint(0, 6), random.randint(6, 256), (
        random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10),
        random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10),
        random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10),
    )


def apply_filter(file_path: str, filter_name: str = 'BLUR', save_both_images: bool = False):
    """
    Apply the selected filter to the image(s).
    If save_both_images is False, save a new file that is the original file post fixed with the filter_name.
    If save_both_image is True, save a new file with the two images next to each other, left the original,
    right the one with the filter applied.
    """
    directory, file_name, extension = split_file_path(file_path)
    original_image = Image.open(file_path)

    if filter_name == 'random':
        filtered_image = original_image.filter(filter=RandomFilter)
    else:
        pil_filter = getattr(ImageFilter, filter_name)
        filtered_image = original_image.filter(filter=pil_filter)

    new_file_path = os.path.join(directory, '{}_{}.{}'.format(file_name, filter_name, extension))

    if save_both_images:
        # make a new image, where both the original and the filter image will be pasted next to each other.
        original_width, original_height = original_image.width, original_image.height

        margin = 30
        new_image = Image.new(
            mode=original_image.mode,
            size=(original_width * 2 + 3 * margin, original_height + 2 * margin), color=(255, 255, 255))
        new_image.paste(im=original_image, box=(margin, margin))
        new_image.paste(im=filtered_image, box=(margin * 2 + original_width, margin))

        return save_image(pil_image=new_image, new_file_path=new_file_path, image_format=original_image.format)
    else:
        return save_image(pil_image=filtered_image, new_file_path=new_file_path, image_format=original_image.format)


apply_filter.combo_choices = {'filter_name': (
    'FIND_EDGES', 'BLUR', 'CONTOUR', 'DETAIL', 'EDGE_ENHANCE', 'EDGE_ENHANCE_MORE', 'EMBOSS', 'SHARPEN', 'SMOOTH',
    'SMOOTH_MORE', 'random')
}


def image_difference(file_paths: list):
    """
    Take two images, and calculate and save the difference between them with ImageChops.difference
    """
    assert len(file_paths) == 2, 'Please select exactly 2 files (only).'

    image_1 = Image.open(file_paths[0])
    image_2 = Image.open(file_paths[1])
    difference = ImageChops.difference(image_1, image_2)

    directory, file_name, extension = split_file_path(file_paths[0])
    new_file_path = os.path.join(directory, '{}_diff.{}'.format(file_name, extension))
    return save_image(pil_image=difference, new_file_path=new_file_path, image_format=image_1.format)
