import math
import random
from random import randrange, choice
import db
import pygame
from pygame.locals import K_UP, K_LEFT, K_RIGHT, K_LCTRL, K_RETURN
from engine import Game, conf
from engine.locals import *
from engine.Graphics import MultiRotated
from engine.Graphics import Image
from engine.Graphics import Circle
from engine.Widget import VerticalProgressBar, MenuActionHandler, Score
from engine.Graphics import String
from engine.Graphics import StaticObject
from engine.Path import AccelerationPath
from engine import Event
from engine.Game import Game


class AlienShip(Image):
    ''' 
        create alien ship from image and set random moving path 
    '''
    def __init__(self):
        Image.__init__(self, filename=conf.IMG_ALIEN_SHIP)
        self.set_position(-90, -90)
        self.object_dropped = 0
        self.set_path(AlienShipPath())

    def move(self):
        ''' alien ship is moving on screen and drop fuel 
            to help us to land on the moon (or bomb to distory us ) 
        '''
        if not self.object_dropped:
            if self.path.approach:
                self.object_dropped = 1
        elif not self.is_on_screen(100):
            self.reset()
        Image.move(self)

    def reset(self):
        self.object_dropped = 0
        self.path.reset()


class Lander(MultiRotated):
    """
        Create lander ship using multirotate object
    """
    def __init__(self, consumable=None):
        """
            Create multi rotate object lander
        """
        ship = conf.IMGS_LANDER
        self.ship_first_image = conf.IMGS_LANDER[0]
        ''' load consumable if found '''
        if consumable is not None:
            _ship = self.load_ship(consumable)
            if _ship is not None:
                ship = _ship
                self.ship_first_image = ship[0] 
                
        MultiRotated.__init__(self, filenames=ship,
                                steps=60,
                                colorkey=TRANSPARENT)

        self.path.set_restriction(speed=400)
        self.reset()
        self.fuel = ShipFuel()
        self.uprightImage = self.image
        
        self._flip_ticks = 0
        min_size = min(self.crect.h, self.crect.w)
        self.crect.h = min_size
        self.crect.w = min_size
        self.crect.inflate_ip(-4, -4)

    def load_ship(self, consumable_item):
        if hasattr(consumable_item, conf.ITEM_SHIP) and consumable_item.ship is True:
            return conf.IMG_LANDER_BLUE
        return None

    def reset(self):
        self.crashed = 0
        ticks = conf.ticks
        self.ticks = ticks
        self.path.ticks = ticks

        self.path.set_direction(PI/2)
        self.set_rotation(PI/2)
        self.set_closest()
        self.path.set_velocity(vx=20, vy=-5)
        self.path.set_acceleration(ax=-10, ay=0)

        self.turningRight = 0
        self.turningLeft = 0
        self.turning = ''
        self.turnRate = 2.0 / 1000.0
        self.turnTicks = 0

        self.accel = 0
        self.accelRate = 277
        self.gravRate = 117
        self.set_gravity(self.gravRate)
        self.accelTicks = ticks

        self.landed = 0
        self.turn()
        self.turnTicks = 0

    def set_gravity(self, rate):
        self.path.set_gravity(gx=0, gy=rate)

    def set_randomPosition(self):
        """
            set random position for lander
        """
        x = random.randrange(100, conf.WINWIDTH-150)
        y = 100
        self.set_position((x, y))

    def refuel(self):
        self.fuel.reset()

    def move(self):
        """
            Move lander and cosume fuel 
        """
        ticks = conf.ticks
        if not self.landed:
            self.turn()
            self.accelerate(ticks)
            MultiRotated.move(self)
        self.fuel.burn(ticks / 30.0)

    def moving_on_path(self):
        self.stop_engine()
        self.flap_right_stop()
        self.flap_left_stop()
        MultiRotated.unpause(self)

    def accelerate(self, ticks):
        """
            accelerate (consume fuel if user accelerate the ship)
        """
        acc_x, acc_y = 0, 0
        if self.accel and not self.fuel.empty() and not self.crashed:
            self._flip_ticks += ticks
            if self._flip_ticks > 90:
                self.flip_images()
                self._flip_ticks -= 50
            self.fuel.burn(ticks)
            rotation = self.get_rotation()
            acc_x += self.accelRate * math.cos(rotation)
            acc_y -= self.accelRate * math.sin(rotation)
        else:
            self.change_image_to(self.ship_first_image)
        ''' update acceleration '''
        self.path.set_acceleration(ax=acc_x, ay=acc_y)

    def start_engine(self, pygame_event):
        self.accel = 1

    def stop_engine(self, pygame_event=None):
        self.accel = 0

    def flap_right(self, pygame_event=None):
        """ move right ship flap """
        if not self.crashed:
            self.turningRight = 1

    def flap_right_stop(self, pygame_event=None):
        if not self.crashed:
            self.turningRight = 0

    def flap_left(self, pygame_event=None):
        """ move left ship flap """
        if not self.crashed:
            self.turningLeft = 1

    def flap_left_stop(self, pygame_event=None):
        if not self.crashed:
            self.turningLeft = 0

    def turn(self):
        """ turn ship in diferent position """
        if self.turningRight and not self.turningLeft:
            self.rotate_right()
        elif self.turningLeft and not self.turningRight:
            self.rotate_left()
        else:
            self.rotate_stop()
            if 0 < abs(self.get_rotation() - PI/2) <= 0.1:
                self.set_rotation(PI/2)

    def vertical(self):
        """ check if ship is vertical """
        abs_rotation = abs(self.get_rotation() - PI/2)
        if abs_rotation < 0.05 or self.image == self.uprightImage:
            return 1 + abs_rotation
        else:
            return 0

    def landing_ship(self, py):
        """ here we will land our ship """
        self.landed = 1
        self.path.set_direction(PI/2)
        self.set_rotation(PI/2)
        self.set_closest()
        self.path.set_velocity(vx=0, vy=0)

        ''' lander must be on top of airport '''
        pos_x, pos_y = self.get_position()
        weight, height = self.image.get_size()
        direction_y = height / 2.0
        self.set_position(
                          (pos_x, py - direction_y)
                          )

    def check_if_ship_crash(self):
        penalty = False
        if not self.crashed:
            """ 3 seconds of fuel penalty if ship crashed ! """
            self.fuel.burn(conf.PENALTY_FUEL)
            self.flap_left()
            self.crashed = 1
            self.path.set_velocity(vx=0, vy=0)
            self.path.set_acceleration(ax=0, ay=0)
            penalty = True
        return penalty


class AlienShipPath(AccelerationPath):
    """ create alien ship randmon path """
    def __init__(self):
        AccelerationPath.__init__(self)
        self.reset_path()

    def reset_path(self):
        AccelerationPath.reset(self)
        ''' set position for alien ship out of the screen '''
        self.set_position((-90, -90))
        ''' set no velocity and acceleration '''
        self.set_acceleration(0, 0)
        self.set_velocity(0, 0)
        self.is_hidden = True
        self.hide_time, self.show_time = 0, 0
        self.hide_object_time = random.randrange(5, 25) * 1000
        self.show_object_time = random.randrange(1, 10) * 1000
        self.visible_on_screen, self.approach_object = False, False

    def approach(self):
        ''' approach to alien ship! see collision! '''
        self.approach_object = True
        self.set_acceleration(0.004, -0.004)

    def next(self):
        ticks = conf.ticks
        if not self.is_hidden:
            self.show_time += ticks
            if self.show_time > self.show_object_time:
                self.approach()
        else:
            self.hide_time += ticks
            if self.hide_time > self.hide_object_time:
                self.set_random_path()
                self.is_hidden = False
                self.visible_on_screen = True
                
        if self.approach_object and self.visible_on_screen:
            if not self.is_on_screen(180):
                self.reset_path()
        return AccelerationPath.next(self, ticks)

    def set_random_path(self):
        self.set_acceleration(0, 0)
        side = random.choice((0, 1, 2, 3))
        if side == 0:
            x = -10
            y = random.randrange(0, conf.WINHEIGHT / 4)
            vx = random.randrange(20, 250) / 1000.0
            vy = (random.randrange(1, 40) - 20) / 1000.0
        elif side == 1:
            x = random.randrange(0, conf.WINWIDTH/2)
            y = -10
            vx = random.randrange(60, 250) / 1000.0
            vy = random.randrange(1, 30) / 1000.0
        elif side == 2:
            x = random.randrange(conf.WINWIDTH/2, conf.WINWIDTH)
            y = -10
            vx = -random.randrange(60, 250) / 1000.0
            vy = random.randrange(1, 30) / 1000.0
        else:
            x = conf.WINWIDTH + 5
            y = random.randrange(0, conf.WINHEIGHT / 4)
            vx = -random.randrange(20, 250) / 1000.0
            vy = (random.randrange(1, 40) - 20) / 1000.0
        self.set_position((x, y))
        self.set_velocity(vx, vy)


class ShipFuel(VerticalProgressBar):
    POSITION = (770, 5)
    WARNING_EMPTY_TANK_STEP = 80
    STEPS_TO_CONSUME = 50
    EXTRA_STEPS = 100
    EXTRA_SECONDS_TO_COSUME = 30
    SECONDS_TO_COSUME = 10
    DEFAULT_COLOR = DARK_BLUE
    
    def __init__(self):
        self.progress = ShipFuel.STEPS_TO_CONSUME
        VerticalProgressBar.__init__(self, steps = self.progress,
                                     position = ShipFuel.POSITION,
                                     color = ShipFuel.DEFAULT_COLOR,
                                     height = 200,
                                     width = 10
                                     )
        ''' seconds to consume the fuel '''
        self.seconds = ShipFuel.SECONDS_TO_COSUME
        ''' consume rate '''
        self.set_rate()
        self.part = 0
    
    def set_rate(self):
        self.rate = self.progress / (self.seconds * 1000.0)

    def burn_slow(self):
        """ consume fuel slow if any consumable found
            - reduce number of seconds
        """
        self.seconds = ShipFuel.EXTRA_SECONDS_TO_COSUME
        self.progress = ShipFuel.EXTRA_SECONDS_TO_COSUME
        self.set_rate() 

    def show_warning(self):
        """ show warning when fuel burned """
        if self.value_left == ShipFuel.WARNING_EMPTY_TANK_STEP:
            self.set_color(RED)
    
    def burn(self, t):
        ''' burn fuel and update progress bar. 
            color progress in red if progress = 80 
        '''
        part = self.part
        part += t * self.rate
        self.part = part
        while self.part > 1:
            self.part -= 1
            self.consume_value()
            self.show_warning()

    def reset(self):
        VerticalProgressBar.reset(self)

    def empty(self):
        return not self.value_left
    

class Asteroid(Image):
    """ create asteroid image. by default is bomb :P  """
    def __init__(self):
        Image.__init__(self, filename=conf.IMG_ASTEROID)
        obj_path = AccelerationPath(startLocation=(-100,-100))
        self.set_path(obj_path)
        self.path.set_gravity(0, 0.00013)
        self.bomb = True

    def reset(self):
        self.path.reset()

    def gone(self):
        x, y = self.get_position()
        if y > conf.WINHEIGHT + 200:
            return 1
        else:
            return 0

class DropObject(Image):
    """
        Drop gift (fuel or bomb) by alien ship
    """
    def __init__(self):
        Image.__init__(self, filename=conf.IMG_GIFT)
        obj_path = AccelerationPath(startLocation=(-100,-100))
        self.set_path(obj_path)
        self.path.set_gravity(0, 0.00013)
        self.bomb = False

    def set_bomb(self, bool):
        self.bomb = bool
        
    def is_bomb(self):
        return self.bomb
        
    def reset(self):
        self.path.reset()

    def gone(self):
        x, y = self.get_position()
        if y > conf.WINHEIGHT + 200:
            return 1
        else:
            return 0


class Ground(StaticObject):
    """
        define base class for ground.
        ground is static object
    """
    def __init__(self, filename, pos):
        img = Image(filename=filename, colorkey=TRANSPARENT2)
        img.set_position(pos)
        StaticObject.__init__(self, sprite=img)
        self.draw()

class SpaceAirport(Ground):
    """
        create static space airport.
        park ship here and you will get some points 
    """
    def __init__(self, pos, filename=conf.IMG_SPACE_AIRPORT):
        Ground.__init__(self, filename, pos)

class MoonRock(Ground):
    """
        create moon land using images from array
    """
    def __init__(self, pos, image=conf.IMG_HARD_GROUND):
        Ground.__init__(self, image, pos)


class MoonLander(Game):
    """
        This is the game
    """
    def set_user(self, user):
        self.user = user
    
    def set_consumable_item(self, item):
        self.consumable_item = item

    def get_consumable_item(self):
        return self.consumable_item
    
    def restart_game(self, pygame_event=None):
        if self.lander.landed:
            self.start_game_message.clear()
            self.start_game_message = None
            self.landing_message.clear()
            self.landing_message = None
            self.remove_drop_object()
            self.draw_static_elements()
            self.alien.reset()
            self.init_ship()

    def create_ground(self):
        """
            create lunar ground including space airport 
        """
        choice = random.randrange(1, 20)
        if choice <= 10:
            self.create_hard_ground()
        else:
            self.create_soft_ground()

    def create_hard_ground(self):
        """
            create hard ground including space airport 
        """
        airport = None
        y = random.randrange(conf.WINHEIGHT-90, conf.WINHEIGHT-20)
        p = random.randrange(40, conf.WINWIDTH-120)
        x = 0
        moon_rocks = []
        while x < conf.WINWIDTH:
            y += random.randrange(-17, 17)
            if y > conf.WINHEIGHT-30:
                y = conf.WINHEIGHT-30
            if airport is None and x > p:
                airport = SpaceAirport((x, y), filename = conf.IMG_SPACE_AIRPORT_GROUND)
                ''' 110 - airport size '''
                x += 110
            else:
                r = MoonRock((x, y), image=conf.IMG_HARD_GROUND)
                moon_rocks.append(r.rect)
                x += 10
        self.airport = airport
        self.moon_rocks = moon_rocks
        

    def create_soft_ground(self):
        """
            create soft lunar ground including space airport 
        """
        airport = None
        x = 0
        y = conf.WINHEIGHT - 60
        moon_rocks = []
        
        rect_rock = MoonRock((x, y), image=conf.IMG_SOFT_GROUND)
        moon_rocks.append(rect_rock.rect)

        x += random.randrange(50, 600)
        if airport is None:
            airport = SpaceAirport((x, y))

        self.airport = airport
        self.moon_rocks = moon_rocks

    def create_earth(self):
        """
            create earth from image.
            set random position for this element
        """
        planet_img = None
        choice = random.randrange(1, 20)
        if choice <= 10:
            planet_img = conf.IMG_PLANETS[0]
        else:
            planet_img = conf.IMG_PLANETS[1]
        
        img = Image(filename=planet_img)
        img.set_random_position()
        ''' draw image on screen '''
        earth = StaticObject(self.window, img)
        earth.draw()

    def create_stars(self):
        """
            create static stars objects in random position
        """
        rand_num = random.randrange(10, 70)
        for i in range(rand_num):
            circle_size = random.randrange(1, 3)
            ''' draw 'star' and set random position '''
            star = Circle(self.window, circle_size)
            star.set_random_position()
            ''' draw star on screen. star will never move '''
            stat = StaticObject(self.window, star)
            stat.draw()

    def create_ship(self):
        """
            create ship. 
            with this ship we will land on the moon
        """
        if self.lander is None:
            if hasattr(self, "consumable_item"):
                self.lander = Lander(consumable=self.get_consumable_item())
            else:
                self.lander = Lander()
        self.init_ship()
        ''' load fuel '''
        self.lander.refuel()
        
        ''' check if user buy fuel pack '''
        if hasattr(self, "consumable_item"):
            if hasattr(self.get_consumable_item(), conf.ITEM_FUEL_PACK):
                if self.consumable_item.fuelpack is True:
                    print "slow burning!"
                    self.lander.fuel.burn_slow()
        ''' add lander '''
        self.sprites.add(self.lander)
        self.sprites.add(self.lander.fuel, level=-1)

    def init_ship(self):
        """
            init ship
        """
        self.lander.reset()
        self.set_ship_position()
        self.lander.pause()

    def set_ship_position(self):
        """
            set ship random position on screen
        """
        airportX, airportY = self.airport.get_position()
        self.lander.set_randomPosition()
        ''' set random position for ship ''' 
        ship_pos_x, ship_pos_y = self.lander.get_position()
        while airportX - 100 < ship_pos_x < airportX + 180:
            self.lander.set_randomPosition()
            ship_pos_x, ship_pos_y = self.lander.path.get_position()
        ''' move ship to new position '''
        self.lander.move()
    
    def drop_asteroid(self):
        """ drop asteroid in random position """
        obj = Asteroid()
        rand_x_position = random.randrange(20, 700)
        position = (rand_x_position, -50)
        obj.path.set_position(position)
        obj.path.set_velocity(vx=0.10, vy=0.05)
        obj.move()
        self.sprites.add(obj)
        self.asteroid_drop_object = obj
    
    def remove_asteroid(self):
        if self.asteroid_drop_object is not None:
            self.sprites.remove(self.asteroid_drop_object)
        self.asteroid_drop_object = None

    def drop_object(self, bomb=False):
        ''' drop fuel -or- missile by the alien ship '''
        obj = DropObject()
        ''' set object type: bomb or fuel '''
        obj.set_bomb(bomb)
        obj.path.set_position(self.alien.path.get_position())
        obj.move()
        self.sprites.add(obj)
        self.alien_drop_object = obj

    def remove_drop_object(self):
        if self.alien_drop_object is not None:
            self.sprites.remove(self.alien_drop_object)
        self.alien_drop_object = None
    
    def check_shield(self):
        ''' check if lander has shield '''
        if self.consumable_item is None:
            self.lander.check_if_ship_crash()
        else:
            has_shield = False
            if hasattr(self.consumable_item, conf.ITEM_SHIELD) and self.consumable_item.shield is True:
                shield_message = String(message="", fontSize=20, color=WHITE)
                shield_message.center(dy=20)
                self.shield_message = StaticObject(sprite=shield_message)
                self.shield_message.draw()
                has_shield = True
            if not has_shield:
                self.lander.check_if_ship_crash()
    
    def create_alien_ship(self):
        ''' create alien ship and render on screen '''
        if self.alien is None:
            self.alien = AlienShip()
            self.sprites.add(self.alien)
        self.alien.reset()

    def set_score(self):
        """ draw score on screen """
        score = Score(self.window, (20, 40), text=conf.MSG_SCORE_LANDING, color=GRAY)
        self.score = score
        self.sprites.add(score)

    def restart(self):
        self.remove_drop_object()
        self.alien_drop_object = None
        self.remove_asteroid()
        self.asteroid_drop_object = None
        self.sprites.remove(self.score)
        self.sprites.remove(self.lander)
        self.sprites.remove(self.lander.fuel)
        self.start()

    def show_landing_message(self):
        ''' show landing message if success '''
        
        landing_message = random.choice(conf.GAME_MESSAGE_LANDING)
        message = String(message=landing_message, fontSize=30, color=WHITE)
        message.center()
        self.landing_message = StaticObject(sprite=message)
        self.landing_message.draw()
        ''' press 'enter' to reload the game '''
        start_game_msg = String(message=conf.MSG_RESTART_GAME, fontSize=20, color=WHITE)
        start_game_msg.center(dy=50)
        self.start_game_message = StaticObject(sprite=start_game_msg)
        self.start_game_message.draw()

    def check_collision(self):
        """
            Check ship collision with objects (airport, rocks, alien ship, fuel)
            Here will apply consumable item from store if exist.
        """
        
        ''' check if ship landed '''
        if self.lander.collide(self.airport):
            ship_pos_x, ship_pos_y = self.lander.get_position()
            coord_x = self.lander.cx
            airport_pos_x, airport_pos_y = self.airport.get_position()
            if ship_pos_x-coord_x > airport_pos_x and ship_pos_x-coord_x < airport_pos_x + 25 and self.lander.vertical():
                ''' the ship landed successfully '''
                if not self.lander.landed:
                    ''' set congratulation message and update user score '''
                    self.show_landing_message()
                    self.score.add(conf.MIN_POINT_TO_GET)
                    self.score.set_score()
                self.lander.landing_ship(airport_pos_y)
                return
            else:
                ''' we miss the landing! the ship crashed. '''
                penalty = self.lander.check_if_ship_crash()
                if penalty:
                    self.score.subtract(conf.MIN_POINT_TO_GET)
                    self.score.set_score()
                return
            
        ''' check ship collision with ground '''
        if self.lander.crect.collidelist(self.moon_rocks) != -1:
            self.lander.check_if_ship_crash()
            
        ''' check collision with alien ship '''
        if self.lander.collide(self.alien):
            ''' here our ship will crash '''
            self.lander.check_if_ship_crash()
            self.alien.path.approach()
        
        ''' check collision with asteroid '''
        if self.asteroid_drop_object:
            if self.lander.collide(self.asteroid_drop_object):
                self.lander.check_if_ship_crash()
                self.remove_asteroid()
            else:
                ''' check collision with ground. if collide then remove object from screen '''
                if self.asteroid_drop_object.crect.collidelist(self.moon_rocks) != -1:
                    self.remove_asteroid()
         
        ''' check colission with dropped object '''
        if self.alien_drop_object is not None:
            if not self.lander.crashed and not self.lander.landed:
                if self.lander.collide(self.alien_drop_object):
                    ''' if alien drop a bomb then lander will crash if has no shield '''
                    if self.alien_drop_object.is_bomb():
                        ''' check if lander has shield '''
                        self.check_shield()
                        self.remove_drop_object()
                    else:
                        self.lander.fuel.reset()
                        self.remove_drop_object()
                    self.alien_drop_object = None
                    
    def start(self):
        ''' before start, draw game elements '''
        self.draw_static_elements()
        self.create_ship()
        self.set_score()
        self.create_alien_ship()
        self.drop_asteroid()

    def load_controls(self):
        ''' engine - use UP, LEFT-CONTROL '''
        self.events.add(Event.KEYDOWN_Event(key=K_UP, callback=self.lander.start_engine))
        self.events.add(Event.KEYDOWN_Event(key=K_LCTRL, callback=self.lander.start_engine))
        self.events.add(Event.KEYUP_Event(key=K_UP, callback=self.lander.stop_engine))
        self.events.add(Event.KEYUP_Event(key=K_LCTRL, callback=self.lander.stop_engine))

        ''' to turn left/right use LEFT, RIGHT arrows '''
        self.events.add(Event.KEYDOWN_Event(key=K_LEFT, callback=self.lander.flap_left))
        self.events.add(Event.KEYDOWN_Event(key=K_RIGHT, callback=self.lander.flap_right))
        self.events.add(Event.KEYUP_Event(key=K_LEFT, callback=self.lander.flap_left_stop))
        self.events.add(Event.KEYUP_Event(key=K_RIGHT, callback=self.lander.flap_right_stop))
        
        ''' restart game after landing use ENTER key '''
        self.events.add(Event.KEYUP_Event(key=K_RETURN, callback=self.restart_game))

    def initialize(self):
        """
            init game and set controls 
        """
        self.window.set_title('Moon Lander')

        self.over = 0
        self.lander = None
        self.alien = None
        self.alien_drop_object = None
        self.asteroid_drop_object = None
        self.explosion = None
        self.shield_message = None

    def draw_static_elements(self):
        """
            draw static elements like earth, stars and ground
            and set background color (black)
        """
        self.set_background(color=BLACK)
        self.create_stars()
        self.create_earth()
        self.create_ground()

    def run(self):
        """
            this method will run the game
        """
        self.start()
        self.load_controls()
        self.init_ship()
        
        
        crashed, empty, over = 0, 0, 0
        ''' move lander '''
        self.lander.moving_on_path()
        ''' if user not quit, then run the game '''
        while not self.quit:
            ''' run game at max_fps - see conf file '''
            conf.ticks = self.clock.tick(conf.MAX_FPS)
            self.sprites.clear()
            self.check_events()
            self.sprites.move()
            ''' if no lander set on the screen then create ship '''
            if not self.lander.is_on_screen(150):
                self.init_ship()                
                if self.lander.crashed:
                    pygame.time.wait(900)
                self.lander.moving_on_path()
            ''' check object collision '''
            self.check_collision()

            if self.alien_drop_object is None:
                if self.alien.object_dropped:
                    random_object_type = random.choice([True, False])
                    ''' alien ship drop random object '''
                    self.drop_object(random_object_type)
            elif self.alien_drop_object.gone():
                self.remove_drop_object()
            
            ''' drop asteroid in random position'''
            if self.asteroid_drop_object is None:
                self.drop_asteroid()
            elif self.asteroid_drop_object.gone():
                self.remove_asteroid()

            ''' if no fuel in tank then end the game '''
            if self.lander.fuel.empty():
                if self.lander.landed:
                    over = 1
                elif empty and self.lander.crashed:
                    crashed = 1
                elif empty and crashed and not self.lander.crashed:
                    over = 1
                else:
                    empty = 1

            dirty = self.sprites.draw()
            pygame.display.update(dirty)
            ''' if game is over do something :) '''
            if over:
                import time
                if hasattr(self, 'landing_message') and self.landing_message is not None:
                    self.landing_message.clear()
                    self.landing_message = None
                    self.start_game_message.clear()
                    self.start_game_message = None
                self.show_game_over()
                if not self.quit:
                    self.restart()
                over, empty, crashed = 0, 0, 0
