import os
import random
from time import time

from PIL import Image, ImageFilter, ImageChops, ImageDraw, ImageOps

from helpers import split_file_path, save_image, TagDictionary, get_new_file_path


class Colors:
    black = (0, 0, 0)
    gray = (127, 127, 127)
    white = (255, 255, 255)


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
    return save_image(
        pil_image=image,
        new_file_path=get_new_file_path(file_path, post_fix_filename='resized'),
    )


resize_image.combo_choices = {'resample': [
    # these are defined as integers in PIL (Image.LANCZOS = 1). For readability and ease in the combo boxes,
    # these string values are used. Note that ANTIALIAS is exactly the same as LANCZOS
    'NEAREST', 'LANCZOS', 'BILINEAR', 'BICUBIC', 'BOX', 'HAMMING', 'ANTIALIAS'
]}


def add_margin(
    file_path: str,
    margin: int = 100,
    background_color: tuple = Colors.black,
):
    """
    Take the original image from the file_path, then resize it, so it can be pasted on a new
    image, that has the same dimensions as the original image, but with an equal margin on all sides around
    the (resized) original image.
    """
    original_image = Image.open(file_path)
    original_width, original_height = original_image.size

    new_image = Image.new(mode=original_image.mode, size=original_image.size, color=background_color)

    original_image = original_image.resize(
        size=(original_width - 2 * margin, original_height - 2 * margin),
        resample=Image.LANCZOS,
    )
    new_image.paste(im=original_image, box=(margin, margin))

    new_file_path = get_new_file_path(file_path, post_fix_filename='with_margin{}'.format(margin))
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
    background_color: tuple = Colors.white,
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

    new_file_path = get_new_file_path(
        file_path, post_fix_filename='centered{}x{}'.format(new_image_size[0], new_image_size[1]))
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

    new_file_path = get_new_file_path(file_path, post_fix_filename='cropped_center')
    return save_image(pil_image=image, new_file_path=new_file_path)


def apply_filter(file_path: str, filter_name: str = 'BLUR', save_both_images: bool = False):
    """
    Apply the selected filter to the image(s).
    If save_both_images is False, save a new file that is the original file post fixed with the filter_name.
    If save_both_image is True, save a new file with the two images next to each other, left the original,
    right the one with the filter applied.
    """
    directory, file_name, extension = split_file_path(file_path)
    original_image = Image.open(file_path)

    random_seed_str = ''  # will be post fixed to the filename, but should be empty when random is not used
    if filter_name == 'random':
        # set a different seed at every function call, so when this is called for an entire directory, a different
        # random filter will be applied for every image. Save the seed in the image name, so it can be reproduced.
        random_seed = str(time()).split('.')[-1]
        random_seed_str = '_seed{}'.format(random_seed)
        random.seed(random_seed)

        class RandomFilter(ImageFilter.BuiltinFilter):
            name = "Random"
            filterargs = (3, 3), random.randint(0, 6), random.randint(6, 256), (
                random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10),
                random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10),
                random.randint(-10, 10), random.randint(-10, 10), random.randint(-10, 10),
            )
        filtered_image = original_image.filter(filter=RandomFilter)
    else:
        pil_filter = getattr(ImageFilter, filter_name)
        filtered_image = original_image.filter(filter=pil_filter)

    new_file_path = os.path.join(directory, '{}_{}{}.{}'.format(file_name, filter_name, random_seed_str, extension))

    if save_both_images:
        # make a new image, where both the original and the filter image will be pasted next to each other.
        original_width, original_height = original_image.width, original_image.height

        margin = 30
        new_image = Image.new(
            mode=original_image.mode,
            size=(original_width * 2 + 3 * margin, original_height + 2 * margin), color=Colors.white)
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

    new_file_path = get_new_file_path(file_paths[0], post_fix_filename='diff')
    return save_image(pil_image=difference, new_file_path=new_file_path, image_format=image_1.format)


def save_image_tags(
    file_path: str,
    artist: str = '',
    copyright: str = '',
    software: str = '',
    image_description: str = '',
    datetime: str = '',
):
    """
    Save metadata on images. This works for jpeg with exif data, and for tiff files with tiff tags.
    Other formats are currently not supported.

    When leaving inputs blank, they will not be saved.

    Important: Existing exif data will be overridden! So this is only useful to add a few image tags to
    images without any tags.

    Important: When applying other image operations, the exif data could get lost on a new image save (for example
    when a new image was created). So adding exif data makes sense on a final image file that will not be adjusted more.

    Of course this this can be extended with more tags. Unfortunately they are defined differently for different file
    formats. So when you want a general solution for all files, you have to look for specific software.
    This is made to add a few of the basic tags. Useful if you want to add your name / software / description
    and copyright (change the empty default strings to your name, your copyright notice, etc).

    To inspect the exif tags in Linux with Imagemagick:
    identify -verbose filename.jpeg
    """
    TagDictionary(
        artist=artist or None,
        copyright=copyright or None,
        software=software or None,
        image_description=image_description or None,
        datetime=datetime or None,
    ).save_tags(image_file_path=file_path)


def _blur_edges(original_image, radius: int = 20, background_color: tuple = Colors.white):
    double_radius = 2 * radius
    original_width, original_height = original_image.size

    new_dimensions = (original_width + double_radius, original_height + double_radius)
    new_image = Image.new(mode=original_image.mode, size=new_dimensions, color=background_color)

    new_image.paste(original_image, (radius, radius))

    # blur mask
    mask = Image.new(mode='L', size=new_dimensions, color=255)
    black = Image.new(mode='L', size=(original_width - double_radius, original_height - double_radius), color=0)
    mask.paste(black, (double_radius, double_radius))

    blur = new_image.filter(ImageFilter.GaussianBlur(radius / 2))
    new_image.paste(blur, mask=mask)

    return new_image


def blur_edges(file_path: str, radius: int = 20, background_color: tuple = Colors.white):
    original_image = Image.open(file_path)
    background = _blur_edges(original_image, radius=radius, background_color=background_color)

    new_file_path = get_new_file_path(file_path, post_fix_filename='blurred_edge')
    return save_image(pil_image=background, new_file_path=new_file_path)


blur_edges.color_parameters = ('background_color', )


def put_images_on_wall(
    file_paths: list,
    wall_color: tuple = Colors.white,
    space_between_two_images: int = 300,
    pixels_above: int = 100,
    pixels_below: int = 100,
    vertical_align: str = 'top',
    frame: str = 'None',
    frame_width: int = 30,
    frame_color: tuple = Colors.black,
):
    """
    Generate one image file, that contains all provided images pasted next to each other, with the provided spaces
    in between. The wall color will be the background color.

    A frame can be drawn around each image, when 'frame_width' is greater than 0 and a frame type is selected.
    'Colored Frame' will draw a colored frame around the image (with the specified 'frame_width' and 'frame_color',
    'Blur' will add a blur effect, that works best on a white background.

    The 'pixels_above' and 'pixels_below' will apply to the tallest image provided. All other images will be placed
    relative to this tallest image, either the top, bottom or center will line up.

    If the new image width exceeds 20000 pixels, do nothing.

    Half the 'space_between_two_images' will be applied to the left and the right side of the image.

    When this is called with one single file, a frame and margin will be added.
    """
    add_frame = frame in ['Colored Frame', 'Blur'] and frame_width > 0

    pil_image_list = []
    image_widths = []
    max_height = 0
    # collect the image widths and the max image height (so the output image dimensions can be calculated).
    # Put the opened images in a list, so we don't have to open them again.
    # When a file_path is not an image, it will fail here, before we create a new image.
    for file_path in file_paths:
        image = Image.open(fp=file_path)
        pil_image_list.append(image)

        image_widths.append(image.width)
        if image.height > max_height:
            max_height = image.height

    image_count = len(file_paths)
    new_image_width = sum(image_widths) + space_between_two_images * image_count
    new_image_height = max_height + pixels_below + pixels_above
    if add_frame:
        new_image_width += (2 * frame_width * image_count)
        new_image_height += (2 * frame_width)

    assert new_image_width < 20000, 'Output image size will exceed 20000 pixels'

    new_image = Image.new(mode=pil_image_list[0].mode, size=(new_image_width, new_image_height), color=wall_color)
    draw = ImageDraw.Draw(new_image)

    # top_x and top_y represent the upper left coordinates of where the image will be pasted
    top_x = int((space_between_two_images / 2))
    for pil_image in pil_image_list:
        top_y = pixels_above

        if vertical_align == 'bottom':
            top_y += (max_height - pil_image.height)
        elif vertical_align == 'center':
            top_y += int((max_height - pil_image.height) / 2)

        if add_frame and frame == 'Colored Frame':
            draw.rectangle(xy=(
                top_x,
                top_y,
                top_x + pil_image.width + 2 * frame_width,
                top_y + pil_image.height + 2 * frame_width
            ), fill=frame_color)

            top_x += frame_width
            top_y += frame_width

            new_image.paste(im=pil_image, box=(top_x, top_y))
        elif add_frame and frame == 'Blur':
            blurred_frame_image = _blur_edges(pil_image, radius=frame_width, background_color=wall_color)
            new_image.paste(im=blurred_frame_image, box=(top_x, top_y))
        else:
            new_image.paste(im=pil_image, box=(top_x, top_y))

        top_x += (pil_image.width + space_between_two_images)

        if add_frame:
            top_x += frame_width

    new_file_path = get_new_file_path(file_paths[0], post_fix_filename='framed_to_wall')
    return save_image(pil_image=new_image, new_file_path=new_file_path)


put_images_on_wall.color_parameters = ('wall_color', 'frame_color')
put_images_on_wall.combo_choices = {'vertical_align': ['top', 'center', 'bottom']}
put_images_on_wall.combo_choices = {'frame': ['None', 'Colored Frame', 'Blur']}


def rotate_image(
    file_path: str,
    angle_in_degrees: float = 90.0,
    background_color: tuple = (255, 255, 255),
    expand: bool = False,
    point_of_rotation: str = 'center',
):
    """
    Rotate the image (around the image center) and save as a new image file.

    When 'expand' is not checked, the new image will have the same dimensions of the original image, and the image
    is not resized. This means some parts (corner areas) of the original image will be outside the frame.

    If 'expand' is checked, the rotated image will be entirely visible, which means the new image will be larger then
    the original image (for all other angles than 0, 90, 180, 270, 360).

    The empty space will be filled with the 'background_color'.
    """
    image = Image.open(fp=file_path)

    # when the center is None, Pil Image.rotate will use the image center as the default.
    center = (0, 0) if point_of_rotation == 'top_left' else None

    rotated_image = image.rotate(
        angle=angle_in_degrees,
        # resample=1,  # default is 1: NEAREST
        expand=expand,
        center=center,
        translate=None,  # optional translation to be applied after the rotation
        fillcolor=background_color,
    )

    new_file_path = get_new_file_path(file_path, post_fix_filename='rotated{}'.format(angle_in_degrees))
    return save_image(pil_image=rotated_image, new_file_path=new_file_path)


rotate_image.color_parameters = ('background_color',)
rotate_image.combo_choices = {'point_of_rotation': ['center', 'top_left']}


def grayscale(file_path: str, convert_mode: str = 'L'):
    """
    Convert the image to grayscale and save as a new image file.
    There are several options to choose from.

    'L' and '1' work for jpeg ('LA' does not)
    All modes work for png.

    L and LA give a smooth result, '1' results in visible individual pixels
    """
    image = Image.open(file_path).convert(convert_mode)
    # ImageOps.grayscale(image) seemed like a good alternative, but it just calls image.convert("L")

    new_file_path = get_new_file_path(file_path, post_fix_filename='grayscale_mode{}'.format(convert_mode))
    return save_image(pil_image=image, new_file_path=new_file_path)


grayscale.combo_choices = {'convert_mode': ['L', '1', 'LA']}


def color_grayscale(
    file_path: str,
    color_1: tuple = Colors.black,
    mid_color: tuple = Colors.gray,
    color_2: tuple = Colors.white,
    use_mid_color: bool = False,

    black_point: int = 0,
    white_point: int = 255,
    mid_point: int = 127,
):
    """
    Colorize grayscale image. From PIL.ImageOps.colorize:

    This function calculates a color wedge which maps all black pixels in
    the source image to the first color and all white pixels to the
    second color. If **mid_point** is specified, it uses three-color mapping.

    Optionally you can use three-color mapping by also specifying **use_mid_color**.
    Mapping positions for any of the colors can be specified
    (e.g. **black_point**), where these parameters are the integer
    value corresponding to where the corresponding color should be mapped.
    These parameters must have logical order, such that
    **black_point** <= **mid_point** <= **white_point** (if **mid_color** and use_mid_color is specified).
    """
    colored_image = ImageOps.colorize(
        image=Image.open(fp=file_path),
        black=color_1,
        white=color_2,
        mid=mid_color if use_mid_color else None,
        blackpoint=black_point, whitepoint=white_point, midpoint=mid_point)

    new_file_path = get_new_file_path(file_path, post_fix_filename='colorized')
    return save_image(pil_image=colored_image, new_file_path=new_file_path)


color_grayscale.color_parameters = ('color_1', 'mid_color', 'color_2')


def solarize(file_path: str, threshold: int = 128):
    """
    Invert all pixel values above a threshold.
    """
    image = ImageOps.solarize(image=Image.open(fp=file_path), threshold=threshold)

    new_file_path = get_new_file_path(file_path, post_fix_filename='solarized{}'.format(threshold))
    return save_image(pil_image=image, new_file_path=new_file_path)
