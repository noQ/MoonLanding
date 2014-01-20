import pygame
import sys
import os
import traceback
import conf
from engine.locals import *


def load_class(module, clazz_str):
    try:
        clazz = getattr(module, clazz_str)
        return clazz()
    except AttributeError:
        traceback.print_exc()
        raise AttributeError("Unable to load class. Value not exists in package! ")

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    package_dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            package_dot = package.rindex('.', 0, package_dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:package_dot], name)

def import_module(name, package=None):
    """Import a module.
       the 'package' argument is required when performing a relative import
    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]

def get_path(filename, dirs):
    """return the first existing file found in directories """
    for dir in dirs:
        full_path = os.path.join(dir, filename)
        if os.path.exists(full_path):
            return full_path

DEFAULT_FONT_DIR = "fonts"
directory_cache = {}
def read_directories(type=None):
    ''' read directory structure '''

    global directory_cache
    if directory_cache.has_key(type):
        ''' return dir for chache '''
        return directory_cache[type]
    else:
        cwd = os.path.abspath('.')
        dir_list = []

        dir_list.append(cwd)
        default_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        if default_dir not in dir_list:
            dir_list.append(default_dir)

        data = os.path.join(default_dir, 'data')
        if type is not None:
            datatype = os.path.join(data, type)
            if os.path.isdir(datatype) and datatype not in dir_list:
                dir_list.append(datatype)
            else:
                pass
        if os.path.isdir(data) and data not in dir_list:
            dir_list.append(data)
            
        directory_cache[type] = dir_list
        return dir_list

def convert_to_alpha_mask(image):
    alpha_mask = image.get_masks()
    if not alpha_mask:
        image = image.convert()
    return image

image_cache = {}
DEFAULT_IMAGE_DIR = "images"
def load_image(filename, convert=1):
    global image_cache

    if image_cache.has_key(filename):
        image = image_cache[filename]
    else:
        dirs = read_directories(DEFAULT_IMAGE_DIR)
        path = get_path(filename, dirs)
        try:
            image = pygame.image.load(path)
        except pygame.error:
            raise pygame.error, 'Could not load %s' % filename
        image_cache[filename] = image

    if convert:
        image = convert_to_alpha_mask(image)
    return image


def load_images(filenames=None, dirname=None, convert=1):
    if filenames is None and dirname is None:
        raise TypeError, 'must specify firname or filenames'
    
    images = []
    if dirname is not None:
        directories = read_directories(DEFAULT_IMAGE_DIR)
        for dir in directories:
            path = os.path.join(dir, dirname)
            if os.path.isdir(path):
                filenames = os.listdir(path)
                for filename in filenames:
                    image_path = os.path.join(path, filename)
                    try:
                        image = load_image(image_path, convert)
                    except pygame.error:
                        pass
                    else:
                        images.append(image)
                break

    elif filenames is not None:
        [load_image(file, convert) for file in filenames]
    return images


def load_dict_with_images(filenames=None, dirname=None, convert=1):
    images = {}
    if dirname is not None:
        directories = read_directories(DEFAULT_IMAGE_DIR)
        for dir in directories:
            path = os.path.join(dir, dirname)
            if os.path.isdir(path):
                for filename in os.listdir(path):
                    image_path = os.path.join(path, filename)
                    images[filename] = load_image(image_path, convert)
                break
    elif filenames is not None:
        for filename in filenames:
            images[filename] = load_image(filename, convert)
    else:
        images = {}
    return images


def keep_aspect_ratio(img, w, h):
    img_width, img_height = img.get_size()
    new_img = pygame.Surface((w, h), img.get_flags(), img)
    
    colorkey = img.get_colorkey()
    if img.get_colorkey() is None:
        colorkey = TRANSPARENT
    new_img.fill(colorkey)
    new_img.set_colorkey(colorkey)

    if img.get_alpha() is not None:
        new_img.set_alpha(img.get_alpha())

    x, y = 0, 0
    ratio = float(img_width) / img_height
    new_ratio = float(w) / h
    if ratio >= new_ratio:
        new_width = int(w)
        new_height = int(float(new_width) / ratio)
        y = (h - new_width) / 2
    else:
        new_height = int(h)
        new_width = int(float(new_width) * ratio)
        x = (w - new_width) / 2
    scaled_image = pygame.transform.scale(img, (
                                              new_width,
                                              new_height
                                              )
                                        )
    return new_img.blit(scaled_image, (x, y))
