======================================================
File operations in Python, with a focus on image files
======================================================
This is a collection of file operations in Python.
The image operations depend on Pillow, the movie operations on ffmpeg.
For adding image tags, piexif should be installed.
Some methods might be useful in your project, just copy and paste them.

All of these methods can be plugged in easily to the Nautilus file system, using 'python_nautilus'
(Then you can select the file(s) or directory, and apply any of these actions with a mouseclick).
All the methods are listed with an explanation under 'list of methods'


============
Installation
============

.. code-block:: bash

    $ git clone https://github.com/josvromans/python_file_operations.git
    $ cd python_file_operations/
    $ virtualenv --python=/usr/bin/python3 env
    $ . env/bin/activate
    $ pip install -r requirements.txt


===============
List of methods
===============
Here is a list of all the methods (and more will be added in the near future)

* File operations
- prefix_filename
- postfix_filename
- split_large_folder (for example in subdirectories of 100 files)
- weed_out_files
- make_filename_unrecognizable (convert filenames to an unreadable hash string)
- number_filenames
- sort_files_by_size
- duplicate_file

* Image operations
- resize_image
- add_margin
- crop_image_in_equal_parts
- paste_image_in_center
- crop_center
- apply_filter
- image_difference
- save_image_tags
- put_images_on_wall


* video operations
- make movie (from a directory of image files)
- make_slideshow (from a directory of image files, output a movie file)
- merge videos (take two or more video files, and past them to one final video file)


====
TODO
====
Add descriptions for the methods

Add screenshots as an example how the method can be made visible in Nautilus

Add more methods that I stashed

write unit tests
