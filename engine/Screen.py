import pygame
import pygame.draw
from pygame.locals import FULLSCREEN
import conf
from Utility import load_image

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Canvas:
    def __init__(self, size=None):
        if size is None:
            size = conf.WINSIZE
        self.size = size
        self.offset = [0, 0]        
        self.surface = pygame.Surface(size)
        self._foreground, self._background = self.surface, self.surface
        self.rect = self._foreground.get_rect()
        

    def set_background(self, filename=None, img=None, tilename=None, tile=None, color=None):
        """ set the background.
        filename: Name of the full-screen background image.
        img: Full-screen background image. (pygame Surface)
        tilename: Name of tile image.
        tile: Tile image. (pygame Surface)
        color: Solid background color.

        """
        if filename is not None:
            background = load_image(filename)
        elif img is not None:
            background = img

        if tilename is not None or tile is not None:
            if tilename:
                tile = load_image(tilename)
            background = pygame.Surface(self.size).convert()
            for y in range(0, self.size[1], tile.get_height()):
                for x in range(0, self.size[0], tile.get_width()):
                    background.blit(tile, (x, y))

        if filename is None and img is None:
            if color is None:
                color = BLACK
            background = pygame.Surface(self.size).convert()
            background.fill(color)
             
        if hasattr(self, '_background'):
            self._background.blit(background, (0, 0))
        else:
            self._background = background
        self._foreground.blit(self._background, (0, 0))            
        

    def set_border(self, width=1, color=WHITE,
                    left=None, right=None, top=None, bottom=None):
        """Draw a border around the screen

        Each border width can be specified separately, or if not specified,
        will default to using width. Specify width of 0 for no border on
        a particular side.

        @param color: Color of border.

        @param width: Pixel width of border.
            If only width is passed, an equal width border will be
            drawn around the entire screen.
        
        @param left: Left-side border width.
        @param right: Right-side border width.
        @param top: Top-side border width.
        @param bottom: Bottom-side border width

        """

        bg = self._background
        
        w, h = bg.get_size()
        
        if left is None:
            left = width
        if right is None:
            right = width
        if top is None:
            top = width
        if bottom is None:
            bottom = width

        if left:
            pygame.draw.rect(bg, color, (0, 0, left, h))
        if right:
            pygame.draw.rect(bg, color, (w-right, 0, w, h))
        if top:
            pygame.draw.rect(bg, color, (0, 0, w, top))
        if bottom:
            pygame.draw.rect(bg, color, (0, h-bottom, w, h))
        
        self._foreground.blit(self._background, (0, 0))

    def clear(self):
        """ clear the screen """
        self._foreground.blit(self._background, (0, 0))
        

  
class Window(Canvas):
    """
        This class interfaces with the Pygame display.
         - initiating this class, the pygame display in initiated.
    """

    def __init__(self, size=None, full=None):
        """
            Init display window, 
            where:
            size: 2-tuple specifies the dimensions of window.
            full: set True to set window is fullscreen

        """
        pygame.init()
        if size is None:
            size = conf.WINSIZE
        self.screen = pygame.display.set_mode(size)
        
        Canvas.__init__(self, size)
        self.set_title()
        self._foreground = self.screen
        self.set_background()
        conf.window = self

    def resize(self, size):
        """Resize the window """

        w, h = size
        w = max(w, conf.MIN_WINWIDTH)
        w = min(w, conf.MAX_WINWIDTH)
        h = max(h, conf.MIN_WINHEIGHT)
        h = min(h, conf.MAX_WINHEIGHT)
        conf.WINWIDTH = w
        conf.WINHEIGHT = h
        size = (w, h)
        conf.WINSIZE = size
        self.size = size
        if not conf.WINFULL:
            self.screen = pygame.display.set_mode((w, h))
        else:
            self.screen = pygame.display.set_mode((w, h), FULLSCREEN)
        self._foreground = self.screen
        self._background = pygame.Surface((w, h))
        self.set_background()
        self.rect = self._foreground.get_rect()
        conf.window = self

    def set_title(self, title=''):
        pygame.display.set_caption(title)

    def update(self, areas=None):
        """Update the display
           - this call will update a section (or sections) of the display screen.
           -  If passed with no arguments, this will update the entire display surface.
        """
        if areas is not None:
            pygame.display.update(areas)
        else:
            pygame.display.update()

    def clear(self):
        """ clear the screen """
        Canvas.clear(self)
        pygame.display.update()

    def set_background(self, filename=None, img=None, tilename=None, tile=None, color=None):
        """ set the background image """
        Canvas.set_background(self, filename, img, tilename, tile, color)
        self.bg = self._background
        self.clear()
