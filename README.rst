======================================================
File operations in Python, with a focus on image files
======================================================
This is a collection of file operations in Python. The methods are untested!
The image operations depend on Pillow, the movie operations on ffmpeg. For some image operations, numpy is used
(to handle matrices with image pixels).
Some methods might be useful in your project, just copy and paste them.

All of these methods can be plugged in easily to the Nautilus file system, using 'python_nautilus'
(select the file(s) or directory, and then right click and choose the action).
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
Here is a list of all the methods, including a user input prompt window, when you run the method as a Nautilus script.

* File operations

* Image operations

* Movie operations


====
TODO
====
Test all these methods.

update the readme

Add more methods that I stashed

write unit tests
