"""Graphical input devices"""
import sys
import importlib
import pygame
from pygame import *
import pygame.draw
from pygame.locals import K_RETURN, K_ESCAPE, K_BACKSPACE, K_F1, K_UP, K_DOWN
from pygame.locals import K_PAGEUP, K_PAGEDOWN, K_LEFT, K_RIGHT, K_DELETE
from pygame.locals import QUIT, MOUSEBUTTONUP
from math import cos, radians
from random import randrange, choice

import conf
import Graphics
from Graphics import Rectangle
import Path
import Event
import db
from locals import TRANSPARENT, BLACK, WHITE, LGREEN, LGRAY, GRAY, BLUE, RED
from os.path import join
from engine.Utility import get_path, load_class, import_module
from db import Wallet
import webbrowser

font.init()

class MenuItem(Rect):
    def __init__(self, menu, label):
        Rect.__init__(self,menu)
        self.label = label

POSITION_CENTER = "center"

class Menu:
    def __init__(self, screen, bg, menu, pos=POSITION_CENTER, font1=None,
             font2=None, color1=(255,255,255), color2=None,
             interline=5, justify=False, light=5, speed=300, lag=30):
        self.font2 = font2
        self.font1 = font1
        self.justify = justify
        self.light = light
        self.speed = speed
        self.lag = lag
        self.color1 = color1
        self.color2 = color2
        self.pos = pos
        self.title = ""
        self.menu = menu
        self.interline = interline
        self.screen = screen
        self.bg = bg

    def show(self, idx):
        itm = Rect(
                 (0, 0),
                 self.font1.size(self.menu[idx].label)
                 )
        
        if self.justify: 
            itm.center = self.menu[idx].center 
        else: 
            itm.midleft = self.menu[idx].midleft
            
        display.update((
                        self.screen.blit(self.bg, self.menu[idx], self.menu[idx]),
                        self.screen.blit(self.font1.render(self.menu[idx].label, 0, (189,183,107)), itm)
                        )
                       )
        
        time.wait(50)
        self.screen.blit(self.bg, self.r2, self.r2)
        for item in self.menu:
            if item != self.menu[idx]:
                self.screen.blit(self.font1.render(item.label,0, (240,230,140)), item)
        
        for mitem in self.menu:
            if mitem != self.menu[idx]:
                self.screen.blit(self.font1.render(mitem.label,0, (240,230,140)), mitem)
        rect = self.screen.blit(self.font2.render(self.menu[idx].label, 0, (189,183,107)), item)
        display.update(self.r2)
        return rect

    def animate(self):
        clock = time.Clock()
        obj_rect = [self.menu[0]] if self.lag else self.menu[:]
        coord = 0
        while obj_rect:
            for itm in obj_rect:
                itm_copy = itm.copy()
                itm.x = itm.animx.pop(0)
                rect = self.screen.blit(
                                     self.font1.render(
                                                       itm.label,1, self.color1
                                                       ), itm
                                     )
                display.update( (itm_copy, rect) )
                self.screen.blit(self.bg, rect, rect)
                
            coord +=1
            if not obj_rect[0].animx:
                obj_rect.pop(0)
                if not self.lag: break
                
            if self.lag:
                foo, bar = divmod(coord, self.lag)
                if not bar and foo < len(self.menu):
                    obj_rect.append(self.menu[foo])
            clock.tick(self.speed)
        
    def load_fonts(self, surface):
        if not self.font1: 
            self.font1 = font.Font("FEASFBRG.TTF", surface.h // len(self.menu) // 2)
        if not self.font2:
            self.font2 = self.font1
        if not self.color1:
            self.color1 = (255,255,255)
        if not self.color2:
            self.color2 = list(map(lambda x:x+(255-x)* self.light// 5, self.color1))
        
    def render(self):
        events = event.get()
        surface = display.get_surface()
        surface_rect = surface.get_rect()
        bg = surface.copy()
        self.load_fonts(surface)
         
        max_font = max(self.menu, key=self.font1.size)
        w, h =  self.font1.size(max_font)
        
        self.r1 = Rect( (0,0), (w, h + 10) )
        ih = self.r1.size[1] + 5
        self.r2 = Rect((0,0), self.font2.size(max_font))
        
        try: 
            setattr(self.r2, self.pos, getattr(surface_rect, self.pos))
        except:
            self.r2.topleft = self.pos
            
        if self.justify:
            self.r1.center = self.r2.center
        else:
            self.r1.midleft = self.r2.midleft
        
        self.menu = [MenuItem(((self.r1.x, self.r1.y + elem*(ih + self.interline)),
                          self.font1.size(itm)), itm) for elem, itm in enumerate(self.menu) if itm]
        if self.justify:
            for i in self.menu: 
                i.centerx = self.r1.centerx
             
        if self.speed:
            for i in self.menu:
                z = self.r1.w-i.x + self.r1.x
                i.animx = [cos(radians(x))*(i.x+z)-z for x in list(range(90, -1, -1))]
                i.x = i.animx.pop(0)
            self.animate()
            for i in self.menu:
                z = surface_rect.w+i.x - self.r1.x
                i.animx = [cos(radians(x))*(-z+i.x)+z for x in list(range(0, -91, -1))]
                i.x = i.animx.pop(0)
        
        mpos = Rect(mouse.get_pos(), (0,0) )
        event.post(event.Event(
                               MOUSEMOTION, {'pos': mpos.topleft if mpos.collidelistall(self.menu) else self.menu[0].center } 
                               )
                   )
        idx = -1
        display.set_caption("")
        while True:
            ev = event.wait()
            if ev.type == MOUSEMOTION:
                idx_ = Rect(ev.pos, (0,0) ).collidelist(self.menu)
                if idx_ > -1 and idx_ != idx:
                    idx = idx_
                    self.render = self.show(idx)
            elif ev.type == MOUSEBUTTONUP:
                ret = self.menu[idx].label, idx
                break
            elif ev.type == KEYDOWN:
                try:
                    idx = (idx + {K_UP:-1, K_DOWN:1}[ev.key]) % len(self.menu)
                    self.render = self.show(idx)
                except:
                    if ev.key in (K_RETURN, K_KP_ENTER):
                        ret = self.menu[idx].label, idx
                        break
                    #elif ev.key == K_ESCAPE:
                    #    ret = None, None
                    #    break
                    
        self.screen.blit(bg, self.r2, self.r2)
        if self.speed:
            [surface.blit(self.font1.render(i.label, 0, self.color1), i) for i in self.menu]
            display.update(self.r2)
            time.wait(50)
            surface.blit(bg, self.r2, self.r2)
            self.animate()
        else:
            display.update(self.r2)
        for ev in events:
            event.post(ev)
        return ret
    

class MenuActionHandler(object):
    ''' perform action for each menu item '''
    ACTION_PLAY = "PLAY"
    ACTION_STORE = "STORE"
    ACTION_EXIT = "EXIT"
    ACTION_BACK = "BACK"
    ACTION_ABOUT = "ABOUT"
    ACTION_SHOW = "SHOW_MENU"
    CENTER_POSITION = "center"
    
    def __init__(self, width=800, height=600, bg_filename='bg.png', font_name="data/fonts/captain.ttf", title=''):
        self.width = width
        self.height = height
        self.screen = display.set_mode(
                                       (self.width, self.height)
                                       )
        self.font = font.Font(join(font_name), 45)
        self.font1 = font.Font(join(font_name), 30)
        self.font2 = font.Font(join(font_name), 15)
        self.bg = image.load(bg_filename).convert()
        self.title = title
        self.menus = []
        self.actions = {}
        self.user = None
    
    def set_user(self, user):
        self.user = user
    
    def set_title(self, label):
        self.title = label
    
    def add_menu(self, properties):
        if isinstance(properties, list):
            self.menus.extend(properties)
        else:
            self.menus.append(properties)
    
    def get_menu(self, idx):
        try:
            return self.menus[idx]
        except ValueError:
            raise pygame.error 
    
    def set_action(self, item_name, package, clazz):
        self.actions[item_name] = { package : clazz }
    
    def get_action(self, item_name):
        if self.actions.has_key(item_name):
            return self.actions.get(item_name)
    
    def show(self):
        from main import PRODUCTS
        time.Clock()

        mainmenu = self.font.render(self.title, 1, (255,255,255) )
        rect_title = mainmenu.get_rect()
        rect_title.centerx, rect_title.top = 300, 120
        
        self.screen.blit(self.bg, (0,0) )
        bg = self.screen.copy()
        self.screen.blit(mainmenu, rect_title)
        display.flip()
        
        resp = MenuActionHandler.ACTION_SHOW
        while resp == MenuActionHandler.ACTION_SHOW:
            menu = Menu(screen=self.screen, bg=bg,  **self.get_menu(0))
            resp = menu.render()
        
        show_menu = True
        while show_menu:
            ''' show store submenu and render items on screen '''    
            if resp[0] == MenuActionHandler.ACTION_STORE:
                ''' get user balance '''
                wallet = db.Wallet(self.user.id)
                user_wallet = wallet.get()
                balance = 0
                if user_wallet:
                    balance = wallet.get_balance()
                ''' set menu title and display user balance '''
                menu_title = ("%s - %s coins") % (MenuActionHandler.ACTION_STORE, str(balance)) 
                display.update(self.screen.blit(self.bg, (0, 0) ))
                display.update(self.screen.blit(
                                                self.font.render(menu_title, 1, (255,255,255)), (450, 450)
                                                )
                               )
                menu = Menu(screen=self.screen, bg=bg, **self.get_menu(1))
                resp = menu.render()
            
            ''' user wants to buy something from store '''
            if resp[0] in PRODUCTS:
                product_name = resp[0]
                uid = self.user.id
                ''' check if user has enough coins to buy an item from store '''
                wallet = db.Wallet(uid)
                user_wallet = wallet.get()
                if user_wallet is None:
                    ''' if user wallet is empty then show error '''
                    display.update(self.screen.blit(self.bg, (0,0) ))
                    display.update(self.screen.blit(
                                                    self.font2.render(Wallet.EMPTY, 1, (255,255,255)), (450, 450)
                                                    )
                                   )
                    ''' else, maybe, user wants to buy 100 coins = 2USD '''
                    if Wallet.COINS in resp[0]:
                        wallet.set_total_coins(Wallet.DEFAULT_COINS)
                        wallet.save()
                else:
                    ''' user wants to buy 100 coins = 2USD '''
                    if Wallet.COINS in resp[0]:
                        wallet.add_coins(Wallet.DEFAULT_COINS)
                        wallet.save()
                    else:
                        ''' user wants to buy some item(s) '''
                        balance = wallet.get_balance()
                        if balance == 0:
                            display.update(self.screen.blit(self.bg, (0,0) ))
                            display.update(self.screen.blit(
                                                            self.font2.render(Wallet.EMPTY, 1, (255,255,255)), (450, 450)
                                                            )
                                           )
                        else:
                            store = db.Store(uid)
                            product = store.get_product(product_name)
                            if product:
                                ''' check if user has enough coins to buy a item from store '''
                                if wallet.get_payment(int(product.price)):
                                    wallet.save()
                                    ''' buy product and save in user store '''
                                    store.buy(product_name)
                                else:
                                    display.update(self.screen.blit(self.bg, (0,0) ))
                                    display.update(self.screen.blit(
                                                                    self.font2.render(Wallet.EMPTY, 1, (255,255,255)), (450, 450)
                                                                    )
                                                   )
                                    
    
                ''' return to menu '''
                menu = Menu(screen=self.screen, bg=bg,  **self.get_menu(0))
                resp = menu.render()            
    
            ''' exit from app '''
            if resp[0] == MenuActionHandler.ACTION_EXIT:
                show_menu = False
                sys.exit(0)

            ''' perform http request to github'''
            if resp[0] == MenuActionHandler.ACTION_ABOUT:
                webbrowser.open_new(conf.ABOUT_URL)
                webbrowser.open_new_tab(conf.ABOUT_URL_RTS)
                webbrowser.open_new_tab(conf.ABOUT_URL_NOSQL)
                
                menu = Menu(screen=self.screen, bg=bg,  **self.get_menu(0))
                resp = menu.render()            
                
            
            ''' user press back button and returns to main menu '''
            if resp[0] == MenuActionHandler.ACTION_BACK:
                self.screen.blit(self.bg,(0,0))
                display.update(self.screen.blit(
                                                self.font.render(
                                                                 self.title,1,(255,255,255)
                                                                 ),
                                                (185, 120)
                                                )
                               )
                menu = Menu(screen=self.screen, bg=bg, **self.get_menu(0))
                resp = menu.render()            
            
            ''' user wants to play this game '''
            if resp[0] == MenuActionHandler.ACTION_PLAY:
                action_class = self.get_action(MenuActionHandler.ACTION_PLAY)
                ''' before play load user consumable item from store if exists '''
                store = db.Store(self.user.id)
                consumable_item = store.consume_item()  
    
                ''' load package and game clazz '''
                package = action_class.keys()[0]
                clazz = action_class.get(package)
                ''' import module '''
                #module = import_module(package)
                ''' load game clazz '''
                from lunar import MoonLander
                game = MoonLander()
                #game = load_class(module, clazz)
                game.set_user(self.user)
                ''' add consumable item from store '''
                game.set_consumable_item(consumable_item)
                game.run()
                show_menu = False    


def run_menu():
    menu = MenuActionHandler(title="Moon Lander")
    ''' define menus '''
    main_menu = { 
                    "menu": ['PLAY','STORE', 'ABOUT','EXIT'],
                    "font1": menu.font1,
                    "pos":'center',
                    "color1": (154,180,61), 
                    "light":6,
                    "speed":200,
                    "lag":20
                    }
    store_menu = { 
                  "menu": ['BUY SHIP 1','BUY SHIP 2' ,'BUY ENERGY PACK' ,'BACK'],
                  "font1": menu.font1,
                  "font2": menu.font1,
                  "pos":'center',
                  "color1":(154,180,61),
                  "light":5,
                  "speed":200,
                  "lag":20
                  }
    menus = [main_menu, store_menu]
    ''' set menus '''
    menu.add_menu(menus)
    ''' render menu on screen '''
    menu.show()

class Widget:
    def __init__(self, callback=None, group=()):
        self.set_callback(callback)
        self.events = Event.EventGroup()

    def set_callback(self, callback):
        if callback is None:
            callback = self.nop
        self.callback = callback

    def nop(self, arg=None):
        pass

    def activate(self):
        self.active = 1

    def deactivate(self):
        self.active = 0

    def _stop(self, pygame_event=None):
        self.stop = 1

    def _quit(self, pygame_event=None):
        ev = pygame.event.Event(QUIT)
        pygame.event.post(ev)
        self._stop()

    def modal(self):
        stop = Event.KEYUP_Event(key=K_ESCAPE, callback=self._stop)
        while not self.stop:
            self.events.check()



class Score(Widget, Graphics.Graphics):
    """Keep and display a score or value."""
    def __init__(self,
                    w=None,
                    position=(100, 100),
                    text="Score:",
                    fontSize=18,
                    color=WHITE,
                    bgcolor=TRANSPARENT):
        
        Graphics.Graphics.__init__(self, w)
        self.score_position = position
        self.text = text
        self.color = color
        self.bgcolor = bgcolor
        self.font = pygame.font.Font(conf.FULL_FONT_PATH, fontSize)
        self.points = 0
        self.set_score()
        self.set_position(position)
        self.set_collision_rect(self.rect)

    def add(self, value):
        """Add points to the score."""
        self.points += value

    def subtract(self, value):
        """Subtract points from the score."""

        self.points -= value
        if self.points <= 0:
            self.points = 0

    def set_points(self, points):
        """Set the score to a particular value."""
        self.points = points

    def set_score(self):
        """Render the text for showing the score."""
        if hasattr(self, 'image'):
            self.clear_sprite_and_update()

        line = '%s %d' % (self.text, self.points)
        self.image = self.font.render(line, 1, self.color, self.bgcolor)
        self.rect = self.image.get_rect()
        self.set_position(self.score_position)
        if self.bgcolor == TRANSPARENT:
            self.image.set_colorkey(TRANSPARENT)

class ProgressBar(Widget, Rectangle):
    """Percentage bar graph."""

    def __init__(self,
                    w=None,
                    steps=100,
                    position=None,
                    color=BLACK,
                    width=None,
                    height=10,
                    fill=1,
                    border=0,
                    borderColor=WHITE):
        if width is None:
            width = conf.WINWIDTH - 50
            
        self.original_color = color
        self.set_color(color)
        self.width = width
        self.height = height
        
        Rectangle.__init__(self, w, width, height, color=color)
        self.image.set_colorkey(TRANSPARENT)
        if position is None:
            self.center(y=-20)
        else:
            self.set_position(position)
            
        self.fill_bar = fill
        self.add_progress(steps)
        self.set_collision_rect(self.image.get_rect())

    def add_progress(self, steps):
        self.progress = steps
        self.percent_step = float(self.width) / steps
        if self.fill_bar:
            self.value_left = steps
        else:
            self.value_left = 0
        self.render()

    def consume_value(self):
        if self.fill_bar:
            self.value_left -= 1
            if self.value_left < 1:
                self.value_left = 0
        else:
            self.value_left += 1
            if self.value_left > self.progress:
                self.value_left = self.progress
        self.render()

    def reset(self):
        self.value_left = self.progress
        self.set_color(self.original_color)
        self.render()

    def set_color(self, color):
        self.color = color

    def render(self):
        width = int(self.value_left * self.percent_step)
        height = self.height

        bar = pygame.Surface((width, height))
        bar.fill(self.color)

        self.image.fill(TRANSPARENT)
        self.image.blit(bar, (0, 0))


class VerticalProgressBar(ProgressBar):
    def __init__(self,
                    w=None,
                    steps=100,
                    position=None,
                    color=BLACK,
                    width=10,
                    height=None,
                    fill=1):
        if height is None:
            height = conf.WINHEIGHT-60
        self.original_color = color
        self.set_color(color)
        self.width = width
        self.height = height
        Rectangle.__init__(self, w, width, height, color=color)
        self.image.set_colorkey(TRANSPARENT)
        if position is None:
            self.center(x=30)
        else:
            self.set_position(position)
        self.fill_bar = fill
        self.add_progress(steps)
        self.set_collision_rect(self.image.get_rect())

    def add_progress(self, steps):
        self.progress = steps
        self.percent_step = float(self.height) / steps
        if self.fill_bar:
            self.value_left = steps
        else:
            self.value_left = 0
        self.render()

    def render(self):
        ''' render progress bar '''
        width = self.width
        ''' this will be always updated '''
        height = int(self.value_left * self.percent_step)
        ''' create progress bar using pygame surface and fill wiht color '''
        bar = pygame.Surface((width, height))
        bar.fill(self.color)
        self.image.fill(TRANSPARENT)
        self.image.blit(bar, (0, self.height - height))


class TextBox():
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.screen = display.set_mode(
            (self.width, self.height))
        self.font = font.Font(conf.FULL_FONT_PATH, 18)
        
    def get_key(self):
        while 1:
            event = pygame.event.poll()
            if event.type == KEYDOWN:
                return event.key
            else:
                pass
            
    def _dialog(self, message):
        "Print a message in a box in the middle of the screen"
        pygame.draw.rect(self.screen, (0,0,0),
                       ((self.screen.get_width() / 2) - 20,
                        (self.screen.get_height() / 2) - 10,
                        200, 20), 0)
        pygame.draw.rect(self.screen, (255,255,255),
                       ((self.screen.get_width() / 2) - 102,
                        (self.screen.get_height() / 2) - 12,
                        204,24), 1)
        if len(message) != 0:
            self.screen.blit(self.font.render(message, 1, (255,255,255)),
                    ((self.screen.get_width() / 2) - 100, (self.screen.get_height() / 2) - 10))
        pygame.display.flip()
    
    def show(self, question):
        """ show dialog """
        current_string = []
        self._dialog(question + ": " + string.join(current_string,""))
        while 1:
            inkey = self.get_key()
            if inkey == K_BACKSPACE:
                current_string = current_string[0:-1]
            elif inkey == K_RETURN:
                if len(current_string) > 0:
                    break
            elif inkey == K_MINUS:
                current_string.append("_")
            elif inkey <= 127:
                current_string.append(chr(inkey))
            self._dialog(question + ": " + string.join(current_string,""))
        if len(current_string) > 0:
            return string.join(current_string,"")

def main():
    """ test main function """
    screen = pygame.display.set_mode((800, 600))
    txt = TextBox(screen)
    ret = txt.show("Player Name")
    print str(ret)

if __name__ == '__main__': 
    main()
    