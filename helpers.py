import glob
import os
import piexif

from PIL import Image, TiffImagePlugin


TIFF_FORMAT = 'TIFF'
JPEG_FORMAT = 'JPEG'


def get_sorted_file_paths(directory_path):
    return sorted(glob.glob(os.path.join(directory_path, '*')))


def split_file_path(file_path):
    file_name = os.path.basename(file_path)
    directory = os.path.dirname(file_path)

    split_file_name = file_name.split('.')
    extension = split_file_name[-1]
    file_name = '.'.join(split_file_name[:-1])

    return directory, file_name, extension


def get_new_file_path(original_file_path, post_fix_filename):
    """
    Take the original file path, and append a postfix to the file name
    """
    directory, file_name, extension = split_file_path(original_file_path)
    file_name = '{}_{}'.format(file_name, post_fix_filename)[:180]  # prevent large file names
    return os.path.join(directory, '{}.{}'.format(file_name, extension))


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

    In case it is a jpeg file, keep the quality and subsampling.
    """
    if enforce_unique_path and os.path.exists(new_file_path):
        new_file_path = determine_new_file_path(new_file_path)

    extra_params = {}
    if pil_image.format == 'JPEG':
        # if you are not satisfied with the quality of adjusted jpeg images, the commented code below might achieve
        # what you want, or can point to image properties that are worth studying.
        # quantization = getattr(pil_image, 'quantization', None)
        # subsampling = JpegImagePlugin.get_sampling(pil_image)
        # quality = 100 if quantization is None else -1
        # extra_params['subsampling'] = subsampling
        # extra_params['qtables'] = quantization
        # extra_params['quality'] = quality
        # quality = 100  # works for all images?

        extra_params['subsampling'] = 0
        extra_params['quality'] = 'keep'

    pil_image.save(
        fp=new_file_path,
        format=pil_image.format if image_format is None else image_format,
        **extra_params,
    )
    return new_file_path


TAG_ID_MAPPING = {
    # hard code the mapping, it is implemented in different ways for TiffTag and piexif.ImageIFD,
    # but boils down to the same ids.
    # see piexif.TAGS for all the exif options. The keys here equal the name in piexif.TAGS
    'Artist': 315,
    'Copyright': 33432,
    'Software': 305,
    'ImageDescription': 270,
    'ICCProfile': 34675,  # 0xC691 in exif?
    'DateTime': 306,
    # 'ProcessingSoftware': 11,  # Not in TiffTags
    # 'ProfileCopyright': 50942,  # Not in TiffTags
}


class TagDictionary:
    """
    Container to bundle tag methods.
    That is: exif stuff for jpegs, TiffTags for tiff files.
    """
    def __init__(self, artist=None, copyright=None, software=None, image_description=None, datetime=None):
        tag_dict = {
            TAG_ID_MAPPING['Artist']: artist,
            TAG_ID_MAPPING['Copyright']: copyright,
            TAG_ID_MAPPING['Software']: software,
            TAG_ID_MAPPING['ImageDescription']: image_description,
            TAG_ID_MAPPING['DateTime']: datetime,
            # this id is just 0, 0, 0, 0, 0.. so probably nothing better then the default
            # TAG_ID_MAPPING['ICCProfile']: ImageCms.createProfile(colorSpace='sRGB').profile_id,
        }
        # filter out the None values
        self.tag_dict = {k: v for k, v in tag_dict.items() if v is not None}

    def construct_exif_bytes(self):
        """
        For JPEG images, save an exif bytes dict
        """
        exif_dict = {"0th": self.tag_dict}
        exif_bytes = piexif.dump(exif_dict)
        return exif_bytes

    def construct_tiff_tags(self):
        tiff_info = TiffImagePlugin.ImageFileDirectory()

        for key, value in self.tag_dict.items():
            tiff_info[key] = value

        return tiff_info

    def save_tags(self, image_file_path):
        image = Image.open(image_file_path)
        file_format = image.tile[0][0]

        if file_format == 'jpeg':
            image.save(image_file_path, format=JPEG_FORMAT, exif=self.construct_exif_bytes(), quality='keep')
        elif file_format == 'libtiff':
            image.save(image_file_path, format=TIFF_FORMAT, tiffinfo=self.construct_tiff_tags())
        elif file_format == 'raw':
            raise NotImplementedError(
                'The file_format is \'{}\', probably a tiff file without compression'.format(file_format))
        else:
            raise NotImplementedError('Could not save tags on this file format: {}'.format(file_format))
