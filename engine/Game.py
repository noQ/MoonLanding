"""
    Game is the central object. Game implements game control like pause and quit 
"""
import time, random, math, os
import pygame
import pygame.draw
from pygame.locals import K_RETURN, K_ESCAPE
import conf
import Screen
import Graphics
from Graphics import SpriteGroup
import Widget
import Path
import Event
from locals import BLACK, RED, LGREEN

class GameControl:
    """
        Game control class
    """
    def __init__(self):
        self.events = Event.EventGroup()
        self.events.add(Event.QUIT_Event(callback=self._quit))
        self.layers = []
        self.sprites = self.sprite_group()
        self.quit, self.stop = 0, 0

    def pause(self):
        ''' pause all sprites '''
        for sprite in self.sprites.sprites():
            sprite.pause()

    def resume(self):
        ''' play sprites '''
        for sprite in self.sprites.sprites():
            sprite.unpause()

    def check_collisions(self):
        """
            collision checks.
            this function must be implemented in the game
        """
        pass

    def check_events(self):
        self.events.check()
    
    def sprite_group(self, sprites=[], layer=None):
        if layer is None:
            layer = self.window
        group =  SpriteGroup(layer, sprites)
        return group
    
    def _stop(self, arg=None):
        """
            brack next loop
        """
        self.stop = 1

    def _quit(self, arg=None):
        """
            brack next loop and exist from game 
        """
        self.quit = 1

class Game(GameControl):
    """
        The central game object.
    """
    def __init__(self, window=None):
        conf.game = self

        if window is None:
            if hasattr(conf, 'window'):
                window = conf.window
            else:
                window = Screen.Window()
        self.window = window
        self.screen = window.screen

        pygame.event.set_allowed(None)
        GameControl.__init__(self)
        ''' when user press ESC then exist from game or in main menu '''
        self.events.add(Event.KEYUP_Event(key=K_ESCAPE, callback=self._quit))

        self.set_title()
        self.clock = pygame.time.Clock()
        conf.ticks = 0
        self.show_mouse_cursor()
        self.release_mouse()

        self.initialize()
        self.window.clear()

    def quit(self):
        exit() 

    def set_background(self, filename=None, img=None,
                       tilename=None, tile=None, color=BLACK):
        
        """ set the background. """
        self.window.set_background(filename, img, tilename, tile, color)
        self.bg = self.window.bg

    def set_title(self, title=None):
        if title is not None:
            pygame.display.set_caption(title)
        else:
            import sys
            title = sys.argv[0]
            self.set_title(title)

    def initialize(self):
        self.set_background()

    def resume(self):
        GameControl.resume(self)
        self.clock.tick()

    def show_mouse_cursor(self, show=1):
        """
            show the mouse cursor :
            1 - show
            0 - hide
        """
        self.mouse_visible = show
        pygame.mouse.set_visible(show)

    def hide_mouse_cursor(self, hide=1):
        """
            hide the mouse cursor:
            1 - hide
            0 - no show
        """
        self.show_mouse_cursor(not hide)

    def grab_mouse(self, grab=1):
        """
            capture mouse and keyboard input
           also keeps mouse locked inside of main window
           1 - grab
           0 - release
        """

        self.mouse_grabbed = grab
        pygame.event.set_grab(grab)

    def release_mouse(self, free=1):
        """
            stop capturing all input
            free = 1 - release
                 = 0 - capture
        """

        self.grab_mouse(not free)

    def update(self, areas=None):
        """
            update the display
        """
        if areas is None:
            pygame.display.update()
        else:
            pygame.display.update(areas)

    def if_key_pressed(self, key=K_RETURN, timeout=None):
        """
            pause the game, waiting for a key.
        """
        self.pause()

        if timeout is not None:
            startTime = pygame.time.get_ticks()
        clearQ = pygame.event.get()

        group = Event.EventGroup()
        group.add(Event.QUIT_Event(callback=self._quit))
        group.add(Event.KEYUP_Event(key=K_ESCAPE, callback=self._quit))
        group.add(Event.KEYUP_Event(key=key, callback=self._stop))

        self.stop = 0
        while not self.quit and not self.stop:
            if timeout is not None:
                timeNow = pygame.time.get_ticks()
                if timeNow - startTime >= timeout:
                    self.stop = 1
            group.check()
        self.stop = 0
        self.resume()

    def play_again(self):
        """
            play again dialog
        """
        play_again_msg = Graphics.String(message=conf.PLAY_AGAIN_MESSAGE,
                                fontSize=30, color=LGREEN)
        play_again_msg.center()
        play_again_msg.move_sprite_to(dy=30)
        self.play_again_msg = Graphics.StaticObject(sprite=play_again_msg)
        self.play_again_msg.draw()

        self.if_key_pressed()
        if not self.quit:
            self.play_again_msg.clear()
            self.game_over_msg.clear()
            self.restart()

    def show_game_over(self):
        message = Graphics.String(self.window,
                                  conf.GAME_OVER_MESSAGE,
                                  fontSize=30,
                                  color=RED)
        message.center()
        self.game_over_msg = Graphics.StaticObject(self.window, message)
        self.game_over_msg.draw()
        pygame.display.update()
        pygame.time.wait(1000)
        self.play_again()        

    def restart(self):
        self.sprites.kill()
        self.events.kill()
        self.events.add(Event.QUIT_Event(callback=self._quit))
        self.events.add(Event.KEYUP_Event(key=K_ESCAPE, callback=self.quit))
        self.initialize()

    def run(self, frames=0):
        """    
            run game - this must be implemented to run this game 
        """
        raise NotImplemented

