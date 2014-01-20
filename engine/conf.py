import ConfigParser
import os

IMG_BACKGROUND = "bg.png"
IMG_SOFT_GROUND = "holes_land.png"
IMG_HARD_GROUND = "ground.png"
IMG_SPACE_AIRPORT = "airport.png"
IMG_SPACE_AIRPORT_GROUND = "airport_ground.png"
IMG_GIFT = "gift.png"
IMG_ASTEROID = "asteroid.png"

IMG_ALIEN_SHIP = "alien.png"

FIRST_IMG_LANDER = "01_rocket.png"
IMGS_LANDER = ['01_rocket.png', '02_rocket.png', 
               '03_rocket.png', '04_rocket.png']

FIRST_IMG_BLUE_LANDER = "01_blue_rocket.png"
IMG_LANDER_BLUE = ['01_blue_rocket.png', '02_blue_rocket.png', 
               '03_blue_rocket.png', '04_blue_rocket.png']

IMG_PLANETS = ['planet_earth.png', 'planet-saturn.png']
ITEM_SHIELD = "shield"
ITEM_SHIP = "ship"
ITEM_FUEL_PACK = "fuelpack"

MSG_RESTART_GAME = "Press << ENTER >> key to restart the game"
MSG_SCORE_LANDING = "Total Landings: "
GAME_MESSAGE_LANDING = ['Hmmm...good landing', 'Nice landing', 'Awesome!', 'Congratulations, you landed!',
                        'Cool and easy :)', 'Well done', 'Excellent landing, Captain!', 'Nice!']

GAME_OVER_MESSAGE = "Game Over"
PLAY_AGAIN_MESSAGE = "Press << ENTER >> key to play again"

MIN_POINT_TO_GET = 1
''' penalty fuel - 3 seconds '''
PENALTY_FUEL = 3000

DEFAULT_FONT = "captain.ttf"
FULL_FONT_PATH = "data/fonts/captain.ttf"
GAME_MENU_ITEMS = ['PLAY','STORE', 'ABOUT','EXIT']

ABOUT_URL = "https://github.com/noQ"
ABOUT_URL_RTS = "https://github.com/noQ/PyRTS"
ABOUT_URL_NOSQL = "https://github.com/noQ/mongodb-admin"

MAX_WINWIDTH = 1024
MIN_WINWIDTH = 580
MAX_WINHEIGHT = 768
MIN_WINHEIGHT = 360

configParser = ConfigParser.ConfigParser()
try:
    configParser.read(os.path.expanduser('config'))
    WINWIDTH = int(c.get('screen', 'WINWIDTH'))
    WINHEIGHT = int(c.get('screen', 'WINHEIGHT'))
    WINFULL = int(c.get('screen', 'WINFULL'))
except:
    #WINWIDTH = 640
    WINWIDTH = 800
    #WINHEIGHT = 480
    WINHEIGHT = 600
    WINFULL = 0

WINWIDTH = max(WINWIDTH, MIN_WINWIDTH)
WINWIDTH = min(WINWIDTH, MAX_WINWIDTH)
WINHEIGHT = max(WINHEIGHT, MIN_WINHEIGHT)
WINHEIGHT = min(WINHEIGHT, MAX_WINHEIGHT)

WINSIZE = [WINWIDTH, WINHEIGHT]
MAX_FPS = 30
MAX_TICK = 50

ticks = 0
sound_status = None
game = None
