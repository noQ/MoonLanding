from engine.Widget import MenuActionHandler, TextBox
from engine.Utility import get_path, read_directories, DEFAULT_IMAGE_DIR, DEFAULT_FONT_DIR, \
     import_module
from engine.conf import IMG_BACKGROUND, GAME_MENU_ITEMS, DEFAULT_FONT
import db

''' loading products to be render in the menu.store '''
db_product = db.Product()
PRODUCTS = db_product.to_list()
if len(PRODUCTS) == 0:
    ''' if DB has no products then will save few default products '''
    product1 = db.Product(name="Blue Ship", description="Super Mega Blue Ship", photo="ship1.img", price="50")
    product1.ship = True
    product1.save()
    
    product3 = db.Product(name="Shield", description="Megathron blue ship", photo="shield.img", price="20")
    product3.shield = True
    product3.save()

    product4 = db.Product(name="Fuel Pack", description="Slow consume fuel", photo="fuel_pack.img", price="30")
    product4.fuelpack = True
    product4.save()

    product5 = db.Product(name="100 Coins - USD 2", description="Buy 100 coins", photo="coins.img", price="100", currency="USD")
    product5.save()
    ''' save all producs in list - used for rendering in store section '''
    PRODUCTS = db_product.to_list()
    
if "BACK" not in PRODUCTS:
    ''' apply back button. '''
    PRODUCTS.append("BACK")

def render_menu(user):
    ''' Function to display menu on screen ''' 
    dirs = read_directories(DEFAULT_IMAGE_DIR)
    background = get_path(IMG_BACKGROUND, dirs)

    menu = MenuActionHandler(bg_filename = background)
    menu.set_user(user)
    ''' define menus '''
    main_menu = { 
                    "menu": GAME_MENU_ITEMS,
                    "font1": menu.font1,
                    "pos": MenuActionHandler.CENTER_POSITION,
                    "color1": (240,230,140), 
                    "light": 5,
                    "speed": 200,
                    "lag": 20,
                    "interline" : 0
                    }
    ''' define store menu '''
    store_menu = { 
                  "menu": PRODUCTS,
                  "font1": menu.font1,
                  "font2": menu.font1,
                  "pos":  MenuActionHandler.CENTER_POSITION,
                  "color1": (240,230,140),
                  "light": 5,
                  "speed": 200,
                  "lag": 20,
                  "interline" : 0
                  }
    ''' define wallet submenu '''
    wallet_menu = { 
                  "menu": ["BUY 100 coins", "BACK"],
                  "font1": menu.font1,
                  "font2": menu.font1,
                  "pos":  MenuActionHandler.CENTER_POSITION,
                  "color1": (240,230,140),
                  "light": 5,
                  "speed": 200,
                  "lag": 20,
                  "interline" : 0
                  }
    ''' set menus '''
    menus = [main_menu, store_menu, wallet_menu]
    menu.add_menu(menus)
    ''' set action for each menu item '''
    menu.set_action(MenuActionHandler.ACTION_PLAY, 
                    package="lunar",
                    clazz="MoonLander")
    ''' render menu on screen '''
    menu.show()

''' MAIN FUNCTION '''
def main():
    ''' Display 'captain name' dialog. User must enter his nickname '''
    dialog = TextBox()
    player_name = dialog.show("Captain ")
    ''' create or get player account '''
    user = db.User()
    user = user.get_account(player_name)
    if user is None:
        ''' create new account with player nickname '''
        user = db.User(account=player_name)
        user.save()
    ''' render and load menu '''
    render_menu(user)

if __name__ == '__main__':
    ''' Run game :) '''
    main()
