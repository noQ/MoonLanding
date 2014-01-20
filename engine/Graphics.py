import random
import math
import pygame
import pygame.draw
from pygame.sprite import Sprite, RenderUpdates
import conf
import Utility
import Screen
import Path

from Utility import load_image 
from locals import WHITE, TRANSPARENT
from locals import PI, PIx2


class SpriteGroup(RenderUpdates):
    def __init__(self, layer=None, sprites=[]):
        """Initialize the sprite group.

        @param layer: L{Screen.Layer} in which the sprite lives.
        @param sprites: Initial sprite or sequence of sprites in the group.

        """
        self.levels = {0: self}
        if layer is None:
            layer = conf.window
        else:
            pass
        self.layer = layer
        self.screen = layer.screen
        self.bg = layer.bg
        RenderUpdates.__init__(self, sprites)

    def add(self, sprites, level=0):
        """Add sprite to group.

            - sprites: a single sprite, or multiple sprites.
            - level: drawing layer at which to add the sprite.
                     higher numbers will be drawn on top of lower numbers.
                     level less than 0 indicate that sprits will be drawn bellow others
                     Default level is ZERO 
        """
        if level == 0:
            RenderUpdates.add(self, sprites)
        else:
            if not self.levels.has_key(level):
                level_group = SpriteGroup(self.layer)
                self.levels[level] = level_group
            else:
                level_group = self.levels[level]
            level_group.add(sprites)

    def change_level(self, level, to_level):
        """
            Change the drawing level.
        """
        levels = self.levels
        levels[to_level] = levels[level]
        del(levels[level])

    def clear(self):
        """
            Clear all of the sprites in the group to the background.
        """
        levels = self.levels.keys()
        levels.sort()
        for l in levels:
            level = self.levels[l]
            RenderUpdates.clear(level, self.screen, self.bg)

    def clear_layer(self):
        """Not used at this time.
        """
        for sprite in self.sprites():
            if len(self.levels) > 1:
                levels = self.levels.keys()
                levels.sort()
                for l in levels[1:]:
                    level = self.levels[l]
                    RenderUpdates.clear(level, self.screen, self.bg)


    def draw(self):
        """
            draw all sprites onto the surface
        """
        render = []
        levels = self.levels.keys()
        levels.sort()
        for lvl in levels:
            level = self.levels[lvl]
            render += RenderUpdates.draw(level, self.screen)
        return render

    def draw_visible(self, surface=None):
        """
            draw not hidden sprites
        """
        if surface is None:
            surface = self.screen

        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append
        for s, r in spritedict.items():
            if not s.hidden:
                newrect = surface_blit(s.image, s.rect)
                if r == 0:
                    dirty_append(newrect)
                else:
                    dirty_append(newrect.union(r))
                spritedict[s] = newrect
            elif r:
                dirty_append(r)
        return dirty

    def move(self):
        levels = self.levels.keys()
        for lvl in levels:
            for sprite in self.levels[lvl].sprites():
                sprite.move()

    def pop(self):
        sprite = self.sprites()[0]
        self.remove(sprite)
        return sprite

    def kill(self):
        """
             remove all of the sprites from all of the groups 
        """
        for sprite in self.sprites():
            sprite.kill()
        levels = self.levels.values()
        levels.remove(self)
        for level in levels:
            level.kill()


class Graphics(Sprite):
    """
        Things to draw on screen.
        - use sprite from pygame.
    """
    def __init__(self, w=None):
        """Initialize Drawable sprite.
             w: Layer on which sprite lives.
        """
        Sprite.__init__(self)
        if w is None:
            if hasattr(conf, 'window'):
                w = conf.window
            else:
                w = Screen.Window()
        self.window = w
        self.screen = w.screen
        self.bg = w.bg
        self.rect = pygame.Rect((0, 0), (0, 0))

        location = (0, 0)
        self.position = [0, 0]
        ''' set distance from upper left to center '''
        self.cx = 0
        self.cy = 0
        Graphics.set_position(self, location)
        self.set_path(Path.ComplexObjectPath())
        self.set_collision_rect()
        self.hidden = 0

    def set_position(self, location, *args):
        """ 
            move sprite to location
            location - can be a single 2-tuple C{(x, y)}, or 2 numbers
            
        """
        if len(args) > 1:
            raise TypeError, "set_position takes either a 2-tuple of numbers, or 2 numbers"
        try:
            x, y = location
        except TypeError:
            x, y = location, args[0]
        else:
            if len(args) > 1:
                raise TypeError, "set_position takes either a 2-tuple of numbers, or 2 numbers"
        self.move_to_position((x, y))

    def direction(self, point):
        """
            return the direction from the sprite to a point
            point: point to find the distance to.
        """
        x, y = self.get_position()
        x1, y1 = point
        return math.atan2(-(y1 - y), (x1 - x))

    def get_position(self):
        return self.position[:]

    def distance(self, point):
        """
            return the distance from the sprite to a point
            point: point to find the distance to.
        """
        x, y = self.get_position()
        x1, y1 = point
        """
           return the Euclidean norm, sqrt(x*x + y*y).
           this is the length of the vector from the origin to point (x, y) 
        """
        return math.hypot((x1 - x), (y1 - y))

    def draw(self, surface=None):
        """Blit image to layer
            surface:  - surface to draw to
                      - if None will draw to the sprite's screen.
        """
        if surface is None:
            self.screen.blit(self.image, self.rect)
        else:
            surface.blit(self.image, self.rect)
        return pygame.Rect(self.rect)

    def update_draw(self, surface=None):
        """
            Draw image and update display.
            surface:  - surface to draw to
                      - if None will draw to the sprite's screen.
        """
        self.draw(surface=surface)
        pygame.display.update(self.rect)

    def clear(self, surface=None):
        """
            Erase sprite to background
            surface:  - surface to draw to
                      - if None will draw to the sprite's screen.
        """
        if surface is None:
            self.screen.blit(self.bg, self.rect, self.rect)
        else:
            surface.blit(self.bg, self.rect, self.rect)
        return pygame.Rect(self.rect)

    def clear_sprite_and_update(self, surface=None):
        """clear sprite and update display
            surface:  - surface to draw to
                      - if None will draw to the sprite's screen.
        """
        self.clear(surface=surface)
        pygame.display.update(self.rect)

    def move_to_position(self, to):
        """
             Move sprite to location.
            'to'  must be tuple: (x,y)
        """
        x, y = to
        self.rect[0] = x - self.cx
        self.rect[1] = y - self.cy
        self.position[0], self.position[1] = x, y
        self.set_collision_rect()

    def set_random_position(self, constrain_to=0):
        """Move sprite to a random location on screen
            constrain_to - the sprite will be more or less constrained to the screen.
                         - negative number - restrict to small area
                         - positive number - the sprite will be offscreen
        """
        sx, sy = self.get_size()
        maxX = conf.WINWIDTH - sx - constrain_to
        maxY = conf.WINHEIGHT - sy - constrain_to

        minX, minY  = -constrain_to, -constrain_to 
        self.move_to_position((
                               random.randrange(minX, maxX+1),
                               random.randrange(minY, maxY+1)
                               )
                              )

    def center(self, x=None, y=None, dx=None, dy=None):
        """ 
        If no parameters are included, the sprite will be moved
        to the center of its screen layer, or use the parameters
        to adjust where exactly the sprite should be placed.

        x: offset from left edge
            if negative, offset from right edge
        y: offset from top edge
            if negative, offset from bottom edge
        dx: horizontal offset from center
        dy: vertical offset from center

        """
        if y is not None and dy is not None:
            raise TypeError, "Must use only y or dy"
        if x is not None and dx is not None:
            raise TypeError, "Must use only x or dx"

        w, h = self.get_size()
        width_obj, height_obj = self.screen.get_size()

        if x is None and dx is None:
            x = (width_obj - w) / 2
        elif x is None:
            x = ((width_obj - w) / 2) + dx
        elif x < 0:
            x = width_obj - w + x

        if y is None and dy is None:
            y = (height_obj - h) / 2
        elif y is None:
            y = ((height_obj - h) / 2) + dy
        elif y < 0:
            y = height_obj - h + y
        self.move_to_position((x+self.cx, y+self.cy))

    def move_sprite_to(self, dx=0, dy=0):
        """Move sprite to
            - dx: distance to move in x-direction.
            - dy: Distance to move in y-direction.
        """
        x, y = self.get_position()
        x += dx
        y += dy
        self.set_position((x, y))

    def set_size(self, size):
        """set size of sprite's rect - (width, height) """
        x, y = size
        self.rect[2] = x
        self.rect[3] = y

    def get_size(self):
        """return size of sprite's rect """
        return (
                self.rect[2],
                self.rect[3]
                )


    def is_on_screen(self, slack=None, **kw):
        """
        Return True if image is on the layer.
        if slack is None, and keyword args are included for
        particular edges  checks only
        the edges passed by keyword.
            - top: sprite can be this far from top edge.
            - bottom: sprite can be this far from bottom edge.
            - left: sprite can be this far from left edge.
            - right: sprite can be this far from right edge.
        """

        if not kw.has_key('layer'):
            layer_rect = self.window.rect
        else:
            layer_rect = kw['layer'].rect
            del(kw['layer'])

        if slack is None and len(kw) == 0:
            return layer_rect.contains(self.rect)
        else:
            sx, sy = layer_rect.size

        x, y = self.get_position()
        width, height = self.get_size()
        if slack is None:
            top, bottom, left, right = None, None, None, None
            if kw.has_key('top'):
                top = kw['top']
            if kw.has_key('bottom'):
                bottom = kw['bottom']
            if kw.has_key('left'):
                left = kw['left']
            if kw.has_key('right'):
                right = kw['right']
        else:
            left, right, top, bottom = slack, slack, slack, slack

        on_object = 0
        if top is not None:
            minY = -top
            if y < minY:
                y = minY
                on_object = 1
        if bottom is not None:
            maxY = sy - height + bottom
            if y > maxY:
                y = maxY
                on_object = 1
        if left is not None:
            minX = -left
            if x < minX:
                x = minX
                on_object = 1
        if right is not None:
            maxX = sx - width + right
            if x > maxX:
                x = maxX
                on_object = 1
        return not on_object

    def set_collision_rect(self, crect=None):
        """set the collision. is used for collision checking.

        crect: rect is used for collision checking.
        crect gets centered on the rect.
        """

        if crect is None:
            if hasattr(self, 'crect'):
                self.crect.center = self.rect.center
            else:
                self.crect = pygame.Rect(self.rect)
        else:
            self.crect = pygame.Rect(crect)
            self.crect.center = self.rect.center

    def collide(self, other):
        """return True if this sprite and other sprite overlap. 
            other: the other sprite to check for collision.
        returns: True if the sprites overlap.
        """
        return self.crect.colliderect(other.crect)

    def collidelist(self, others):
        """
            return True if this sprite and any in list of others collide.
        """
        rects = [o.crect for o in others]
        index = self.crect.collidelist(rects)
        if index == -1:
            return 0
        else:
            return others[index]

    def collidelistall(self, others):
        """
            return True if this sprite and any in list of others collide.
            others: List of other sprites to check for collision.
        """
        rects = [o.crect for o in others]
        indexes = self.crect.collidelistall(rects)
        if not indexes:
            return []
        rects = [others[index] for index in indexes]
        return rects

    def set_path(self, path):
        """set which path to follow """
        self.path = path
        position = path.get_position()
        path.position = self.position
        self.move_to_position(position)
        Graphics.move(self)

    def runPath(self, frames=0):
        """call move() continuously
        frames: number of times to call move(), or
            if frames is 0, call move() until EndOfPath.
        """

        self.path.reset()
        count = 0
        clock = pygame.time.Clock()
        while count < frames or not frames:
            conf.ticks = clock.tick(conf.MAX_FPS)
            dirty = [self.clear()]
            try:
                self.move()
            except Path.EndOfPath:
                self.path.reset()
                raise
            dirty.append(self.draw())
            pygame.display.update(dirty)
            count += 1

    def move(self):
        """set position to next position on path"""
        try:
            self.move_to_position(self.path.next())
        except StopIteration:
            raise Path.EndOfPath

    def pause(self):
        """stop moving along Path"""
        self.path.pause()

    def unpause(self):
        """start moving along Path"""
        self.path.unpause()


class Image(Graphics):
    """
        static sprite from image
        - used to draw static objects like planets
    """
    filename = None
    
    def __init__(self, w=None, filename=None, image=None, colorkey=TRANSPARENT, alpha=0, convert=1):
        """
            Create sprite from file or surface
        """
        Graphics.__init__(self, w)
        if filename is None and image is None:
            if self.filename is None:
                self.image = load_image('None.png', convert=convert)
            else:
                self.image = load_image(self.filename, convert=convert)
        elif image is None:
            self.image = load_image(filename, convert=convert)
        else:
            self.image = image

        if alpha:
            self.image.set_alpha(alpha, pygame.locals.RLEACCEL)
            self.image.convert_alpha()

        if colorkey is not None:
            self.image.set_colorkey(colorkey)
            if not alpha:
                self.image.convert()

        self.rect = self.image.get_rect()
        self.set_position((0, 0))
        self.set_collision_rect(self.rect)


class Layer(Graphics, Screen.Canvas):
    """
        Screen that can be used as a sprite
    """
    def __init__(self, w=None, size=None, color=TRANSPARENT):
        Graphics.__init__(self, w)
        self._window = self.window
        if size is None:
            size = self.window.screen.get_size()
        Screen.Canvas.__init__(self, size)
        self.image = self._foreground
        self.screen = self._foreground
        self.screen.fill(color)
        self.bg = self._background
        self.bg.fill(color)

        if color == TRANSPARENT:
            self.image.set_colorkey(color)
            self.bg.set_colorkey(color)

        self.sprites = SpriteGroup(layer=self)

    def update_contents(self):
        """
            move and re-draw all the sprites that use this layer
        """
        self.sprites.clear()
        self.sprites.move()
        self.sprites.draw()

    def draw(self, surface=None):
        rect = self.rect
        if surface is None:
            self._window.screen.blit(self.image, rect)
        else:
            surface.blit(self.image, rect)
        return pygame.Rect(rect)

    def clear(self, surface=None):
        """
            erase image to background
        """
        if surface is None:
            self._window.screen.blit(self._window.bg, self.rect, self.rect)
        else:
            surface.blit(self._window.bg, self.rect, self.rect)
        return pygame.Rect(self.rect)

    def center(self, x=None, y=None, dx=None, dy=None):
        if y is not None and dy is not None:
            raise TypeError, "use only y or dy"
        if x is not None and dx is not None:
            raise TypeError, "use only x or dx"

        width, height = self.get_size()
        width_obj, height_obj = self._window.screen.get_size()

        if x is None and dx is None:
            x = (width_obj - width) / 2
        elif x is None:
            x = ((width_obj - width) / 2) + dx
        elif x < 0:
            x = width_obj - width + x

        if y is None and dy is None:
            y = (height_obj - height) / 2
        elif y is None:
            y = ((height_obj - height) / 2) + dy
        elif y < 0:
            y = height_obj - height + y
        self.move_to_position((x, y))


class Shape(Graphics):
    """ 
        Geometric shapes. All other objects will be derived 
        from this object.
    """
    def __init__(self, w=None):
        Graphics.__init__(self, w)

    def paint(self):
        raise NotImplementedError

    def set_color(self, color=None, r=None, g=None, b=None):
        """Set the color for drawing.
            - if no parameters are passed at all, the color is set to WHITE.

        color: an RGB tuple, or the word 'random' which will choose
            a color at random from (not quite) all possible.
        r: The red value of the color (0 - 255)
        g: The green value of the color (0 - 255)
        b: The blue value of the color (0 - 255)
        """
        if color is None and r is None and g is None and b is None:
            rr = 255
            rg = 255
            rb = 255
        elif color is None:
            rr, rg, rb = self.color
        elif color:
            rr, rg, rb = color[:3]
            
        if color == 'random':
            rr = random.randint(50, 250)
            rg = random.randint(50, 250)
            rb = random.randint(50, 250)
        if r is not None:
            rr = r
        if g is not None:
            rg = g
        if b is not None:
            rb = b

        color = (rr, rg, rb)
        self.color = color
        self.paint()


class Rectangle(Shape):
    def __init__(self, w=None, width=10, height=5, color=WHITE):
        Shape.__init__(self, w)
        self.width = width
        self.height = height
        self.image = pygame.Surface((width, height)).convert()
        self.set_color(color)
        self.rect = pygame.Rect((0, 0), (width, height))
        self.set_position((0, 0))
        self.set_collision_rect(self.rect)

    def paint(self):
        """Change the color of the rectangle."""
        self.image.fill(self.color)

    def border(self, width=10, color=WHITE, left=None, right=None, top=None, bottom=None):
        """Draw a border around the rectangle

        width: pixel width of border
        color: color of border - default white
        left: left-side border
        right: right-side border
        top: top-side border
        bottom: bottom-side border
        """
        img_width, img_height = self.image.get_size()
        if left is None:
            left = width
        if right is None:
            right = width
        if top is None:
            top = width
        if bottom is None:
            bottom = width
        if top:
            pygame.draw.rect(self.image,
                             color,
                             (0, 0, img_width, top)
                             )
        if bottom:
            pygame.draw.rect(self.image, color, (
                                            0,
                                            img_height-bottom,
                                            img_width,
                                            img_height
                                            ))
        if left:
            pygame.draw.rect(self.image, color, (
                                            0,
                                            0,
                                            left,
                                            img_height
                                            ))
        if right:
            pygame.draw.rect(self.image, color, (
                                            img_width-right,
                                            0,
                                            img_width,
                                            img_height
                                            ))

class Square(Rectangle):
    def __init__(self, w=None, side=10, color=WHITE):
        Rectangle.__init__(self, w, side, side, color)

class Circle(Shape):
    def __init__(self, w=None, radius=10, color=WHITE, bgcolor=TRANSPARENT):
        Shape.__init__(self, w)
        self.radius = radius
        self.width = 2 * radius
        self.height = 2 * radius
        self.image = pygame.Surface((self.width, self.height)).convert()
        self.image.fill(bgcolor)
        self.image.set_colorkey(bgcolor)
        self.set_color(color)
        
        self.rect = pygame.Rect(
                                (0, 0),
                                (self.width, self.height)
                                )
        self.set_position((0, 0))
        self.set_collision_rect(self.rect)

    def paint(self):
        radius = self.radius
        pygame.draw.circle(self.image,
                           self.color,
                           (radius, radius),
                           radius, 0
                           )


class MultipleObjects(Graphics):
    filenames = None
    def __init__(self, w=None, filenames=None, dirname=None, defaultImage=None,
                    colorkey=TRANSPARENT, convert=1):
        """Load multiple images from multiple files
        w: object to draw in.
        filenames: List of image file names to load.
        dirname: Name of directory from which to load all images.
        defaultImage: Name of the default image.
        colorkey: RGB tuple to use for transparency.
        convert: If True, call convert() for all images.
        """

        if filenames is None and dirname is None:
            filenames = self.filenames
        Graphics.__init__(self, w)
        
        self.images = Utility.load_dict_with_images(filenames, dirname)
        self.defaultImage = defaultImage
        for filename in self.images.keys():
            self.add(filename,
                     self.images[filename],
                     colorkey,
                     convert
                     )

        if not self.images:
            ''' default image is None.png (null) '''
            self.add('None.png', 
                     Utility.load_image('None.png'),
                     colorkey,
                     convert=1
                     )
            self.defaultImage = 'None.png'
        else:
            self.defaultImage = self.images.keys()[0]

        self.image = self.images[self.defaultImage]
        self.set_position((0, 0))
        self.set_size(self.image.get_size())
        self.set_collision_rect(self.rect)

    def add(self, filename='default', image=None, colorkey=TRANSPARENT, convert=1):
        """add image to list of available images """

        if image is None:
            image = load_image(filename, convert)
        if colorkey is not None:
            image.set_colorkey(colorkey)

        self.images[filename] = image
        if self.defaultImage == 'None.png':
            self.delete('None.png')
            self.defaultImage = filename

    def delete(self, key):
        """remove image by name"""
        del(self.images[key])

    def flip(self, imageName='default'):
        """
            switch image by name
        """
        self.image = self.images[imageName]
        self.set_size(self.image.get_size())
        self.set_collision_rect()

        
class RotatedObject(MultipleObjects):
    """Sprite with auto-generated rotated images"""

    def __init__(self, w=None, filename=None, steps=4, image=None,
                    colorkey=TRANSPARENT, convert=1, cx=None, cy=None):
        """Initialize RotatedImage

        w: layer to draw in.
        filename: name of file from which to load image
        steps: number of separate rotated images to create
                   does not work with > 360 steps
        image: image to use, instead of loading from file
        colorkey: set this colorkey on all rotated images
        convert: boolean, 1 = convert() every rotated image
        cx: x-coordinate of center of rotation relative to the
            upper left corner of the image.
        cy: y-coordinate of center of rotation relative to the
            upper left corner of the image.
        """
        MultipleObjects.__init__(self, w=w,
                                colorkey=colorkey,
                                convert=convert
                                )
        if image is None and filename is None:
            raise TypeError, 'Must include filename or image'
        elif image is not None:
            self.add(
                     filename='image',
                     image=image,
                     colorkey=colorkey, convert=convert
                     )
        if image is None:
            self.add(
                     filename,
                     colorkey=colorkey,
                     convert=convert
                     )

        self.set_rotation(0)
        self.set_rotationRate(0)

        name, image = self.images.items()[0]
        if cx is not None or cy is not None:
            w, h = image.get_size()
            if cx is None:
                cx = w / 2.0
            if cy is None:
                cy = h / 2.0

            if cx > w:
                wnew = 2 * cx
                x = 0
            elif cx < 0:
                wnew = (2 * w) + (2 * abs(cx))
                x = w + (2 * -cx)
            else:
                wnew = (2 * w) - (2 * cx)
                x = w - (2 * cx)

            if cy > h:
                hnew = 2 * cy
                y = 0
            elif cy < 0:
                hnew = (2 * h) + (2 * abs(cy))
                y = h + (2 * -cy)
            else:
                hnew = (2 * h) - (2 * cy)
                y = h - (2 * cy)

            wnew = int(wnew)
            hnew = int(hnew)

            i = pygame.Surface((wnew, hnew))
            i.fill(colorkey)
            i.blit(image, (x, y))
            i.set_colorkey(colorkey)
            image = i

        degPerStep = 360 / steps
        for step in range(steps):
            deg = step * degPerStep
            s = pygame.transform.rotate(image, deg)
            s.set_colorkey(colorkey)
            if convert:
                s.convert()
            self.images[int(deg)] = s
        self.delete(name)

        self.keys = list(self.images.keys())
        self.keys.sort()

        self.flip(0)
        self.set_collision_rect(self.image.get_rect())
        

    def set_coord_xy(self, width, height, coord_x, coord_y):
        if coord_x is not None or coord_y is not None:
            if coord_x is None:
                coord_x = width / 2.0
            if coord_y is None:
                coord_y = height / 2.0

            if coord_x > width:
                new_width = 2 * coord_x
                x = 0
            elif coord_x < 0:
                new_width = (2 * width) + (2 * abs(coord_x))
                x = width + (2 * -coord_x)
            else:
                new_width = (2 * width) - (2 * coord_x)
                x = width - (2 * coord_x)

            if coord_y > height:
                new_height = 2 * coord_y
                y = 0
            elif coord_y < 0:
                new_height = (2 * height) + (2 * abs(coord_y))
                y = height + (2 * -coord_y)
            else:
                new_height = (2 * height) - (2 * coord_y)
                y = height - (2 * coord_y)
            return [new_width, new_height, x, y]
    
    def rotate_objects_steps(self, image, steps, color, convert):
        degPerStep = 360 / steps
        for step in range(steps):
            deg = step * degPerStep
            s = pygame.transform.rotate(image, deg)
            s.set_colorkey(color)
            if convert:
                s.convert()
            self.images[int(deg)] = s

    def rotate(self, rad=None):
        """rotate to the left by radians"""

        direction = self.get_rotation()
        self.set_rotation(direction + rad)

    def set_rotation(self, direction=None):
        """set angle of rotation
            - direction: angle to set 0 is pointing to the right positive is counter-clockwise
        """

        if direction is None:
            direction = self.path.get_direction()
        self.rotation = direction % PIx2 % PIx2

    def get_rotation(self):
        """return angle of rotation"""
        return self.rotation

    def set_rotationRate(self, rate):
        """
            set rate of rotation in radians / second
        """
        self.rotationRate = rate

    def rotate_right(self):
        self.set_rotationRate(-2)

    def rotate_left(self):
        self.set_rotationRate(2)

    def rotate_stop(self):
        self.set_rotationRate(0)

    def rotate_towards(self, point):
        direction = self.direction(point)
        rotation = self.get_rotation()
        rad = (rotation - direction) % PIx2

        if rad > PI:
            rad -= PIx2
        elif rad < -PI:
            rad += PIx2

        if rad > 0.1:
            self.rotate_right()
        elif rad < -0.1:
            self.rotate_left()
        else:
            self.rotate_stop()

    def flip(self, key=None):
        """Switch images for the sprite"""

        if key is not None:
            self.key = key
        else:
            self.key += 1
        if self.key >= len(self.keys):
            self.key = 0
        self.set_image(self.key)
        self.set_position(self.get_position())
        self.set_rotation((self.key / len(self.keys)) * PIx2)

    def set_closest(self):
        """flip to the image for the current direction"""

        direction_image = self.get_rotation()
        obj = int(
                (direction_image / PIx2) * len(self.images)
                )
        self.set_image(obj)
        self.set_position(self.get_position())

    def set_image(self, key):
        """Change which image is being shown.
            key: dict key referencing the image to use.
                 The keys are the rotation of the images.
        """
        self.image = self.images[self.keys[key]]
        size = self.image.get_size()
        width, height = size

        self.set_size(size)
        self.cx, self.cy = (width), (height / 2.0)
        self.set_collision_rect()

    def move(self):
        if self.rotationRate:
            ticks = conf.ticks
            self.rotate(self.rotationRate * ticks/1000.0)
        self.set_closest()
        MultipleObjects.move(self)

class MultiRotated(RotatedObject):
    """Sprite with multiple auto-generated rotated images"""

    def __init__(self, w=None, filenames=None, steps=4,
                    colorkey=TRANSPARENT, convert=1, cx=None, cy=None):
        """Initialize MultiRotated

        @param w: L{Screen.Layer} to draw in.
        @param filenames: list of names of files from which to load images
        @param steps: number of separate rotated images to create for each
            image in C{filenames} I{B{Note} -- does not work with > 360 steps}
        @param colorkey: set this colorkey on all rotated images
        @param convert: boolean, 1 = convert() every rotated image
        @param cx: x-coordinate of center of rotation relative to the
            upper left corner of the image.
        @param cy: y-coordinate of center of rotation relative to the
            upper left corner of the image.

        """
        RotatedObject.__init__(self, w=w, filename=filenames[0], steps=steps,
                            colorkey=colorkey, convert=convert, cx=cx, cy=cy)
        self._images = {}

        for f in filenames:
            ri = RotatedObject(w=w, filename=f, steps=steps,
                    colorkey=colorkey, convert=convert, cx=cx, cy=cy)
            self._images[f] = ri

        self._images_keys = list(filenames)
        self._images_keys.sort()
        self._images_key_idx = 0

        self.change_image_to(filenames[0])
        self.set_flip_images_rate(0)
        self.flip_images_ticks = 0
        self.reset_flip_images()

    def set_flip_images_rate(self, rate):
        """Used to animate objects 
            rate: number of times per second to switch to next image.
        """
        self.flip_images_rate = rate

    def reset_flip_images(self):
        """go back to the first image in the array.
           reset counter when finish
        """
        if self.flip_images_rate:
            self.flip_images_ticks = 1000 / self.flip_images_rate
            self.flip_images_ticks_orig = self.flip_images_ticks

    def change_image_to(self, f):
        """Change which set of images is being shown.
            f - image name
        """
        self.keys = self._images[f].keys
        self.images = self._images[f].images

    def flip_images(self):
        """flip to the next set of images."""

        idx = self._images_key_idx
        idx += 1
        if idx >= len(self._images):
            idx = 0
        key = self._images_keys[idx]
        self.keys = self._images[key].keys
        self.images = self._images[key].images
        self._images_key_idx = idx

    def move(self):
        if self.flip_images_rate:
            self.flip_images_ticks -= conf.ticks
            if self.flip_images_ticks < 0:
                self.flip_images()
                self.reset_flip_images()
        RotatedObject.move(self)


class StaticObject(Graphics):
    """ 
        draw objects which never move.
    """

    def __init__(self, w=None, sprite=None):
        if sprite is None:
            sprite = Image()
        self.sprite = sprite
        Graphics.__init__(self, w)
        self.draw_on_background()
        self.crect = pygame.Rect(self.rect)

    def draw(self):
        """set image to both background and foreground."""
        rect = self.rect
        self.window.bg.blit(self.image, rect)
        self.window.screen.blit(self.image, rect)
        pygame.display.update(rect)

    def draw_on_background(self):
        sprite = self.sprite
        self.image = sprite.image
        self.rect = sprite.rect
        self.bg = pygame.Surface(self.image.get_size())
        self.bg.blit(self.window.bg, (0, 0), self.rect)

    def clear(self):
        weight, height = self.rect.size
        r = pygame.Rect(0, 0, weight, height)
        self.window.bg.blit(self.bg, self.rect, r)
        self.window.screen.blit(self.bg, self.rect, r)
        pygame.display.update(self.rect)

    def set_position(self, position):
        """Move the sprite after clear old position of item and
        set new position of object
        """
        self.clear()
        self.sprite.set_position(position)
        self.draw_on_background()
        self.draw()

    def get_position(self):
        """get current position"""
        return self.sprite.get_position()

    def move(self):
        """
            Object is static, so is not moving!
        """
        pass


class String(Graphics):
    """A string of numbers, letters, or other characters."""

    def __init__(self, w=None, message="string", fontSize=20,
                    color=WHITE, bgcolor=TRANSPARENT):
        Graphics.__init__(self, w)
        self.message = str(message)

        self.fontSize = fontSize
        font = pygame.font.Font(conf.FULL_FONT_PATH, fontSize)

        if self.message == '':
            size = font.size('TEST')
            w, h = size
            self.image = pygame.Surface((0, h))
        else:
            size = font.size(self.message)
            self.image = font.render(self.message, 1, color, bgcolor)

        if bgcolor == TRANSPARENT:
            self.image.set_colorkey(TRANSPARENT)
        self.rect = pygame.Rect((0, 0), size)
        self.set_collision_rect(self.rect)


