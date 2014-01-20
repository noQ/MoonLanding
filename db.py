import pickle
import uuid
import time
import random
from engine.Utility import read_directories, get_path

""" 
    Clase to manipulate local database (conenct to db server in real live)
"""

class DBBase(object):

    DB_WRITE_FLAG = "wb"
    DB_READ_FLAG = "rb"
    DB_DIR = "db"

    def generate_id(self, tip=None):
        '''
            generate unique ID
        '''
        current_time = long(round(time.time() * 1000))
        if tip is None:
            tip = random.random()
        rnd = "%s%s" % (str(current_time), str(tip))
        return uuid.uuid5(uuid.NAMESPACE_DNS, rnd)

    def get_id(self):
        return self.id

    def set_value(self, kwargs, value_name):
        if kwargs.has_key(value_name):
            return kwargs.get(value_name)
        return None    

    def _get_db(self, name):
        dirs = read_directories(DBBase.DB_DIR)
        self.db_name = get_path(name, dirs)
        return self.db_name
    
    def get_all(self):
        return NotImplemented
    
    def save(self):
        return NotImplemented

class Account(DBBase):
    DB = "users.db"
    
    def add_account(self, user_clazz):
        self.accounts = self.load_accounts()
        self.accounts.update({user_clazz.account : user_clazz})
        
        pickle_file = open(self._get_db(Account.DB), DBBase.DB_WRITE_FLAG)
        pickle.dump(self.accounts, pickle_file, pickle.HIGHEST_PROTOCOL)

    def load_accounts(self):
        self.accounts = {}
        pickle_file = open(self._get_db(Account.DB), DBBase.DB_READ_FLAG)
        try:
            self.accounts = pickle.load(pickle_file)
        except EOFError:
            pass         
        return self.accounts
            
db_account = Account()
class User(Account):
    def __init__(self, account=None, **kwargs):
        self.id = None
        self.account = account
        self.name = self.set_value(kwargs, "name")
        
    def save(self):
        self.id = self.generate_id()
        db_account.add_account(self)

    def get_id(self):
        return self.id
        
    def get_account(self, account):
        user_accounts = db_account.load_accounts()
        if user_accounts:
            if user_accounts.has_key(account):
                return user_accounts.get(account)
        return None
    
class Product(DBBase):
    DB = "products.db"
    CURRENCY = "COINS"
    
    def __init__(self, **kwargs):
        self.id = self.generate_id()
        self.name = self.set_value(kwargs, "name")
        self.description = self.set_value(kwargs, "description")
        self.photo = self.set_value(kwargs, "photo")
        self.price = self.set_value(kwargs, "price")
        self.currency = self.set_value(kwargs, "currency")
        if self.currency:
            self.currency = Product.CURRENCY

    def get_all(self):
        self.products = {}
        pickle_file = open(self._get_db(Product.DB), DBBase.DB_READ_FLAG)
        try:
            self.products = pickle.load(pickle_file)
        except EOFError:
            pass         
        return self.products
    
    def get(self, product_name):
        products = self.get_all()
        if products.has_key(product_name):
            return products.get(product_name)
        return None
    
    def to_list(self):
        self.products = self.get_all()
        return self.products.keys()
    
    def save(self):
        self.id = self.generate_id()
        
        self.products = self.get_all()
        self.products.update({self.name : self})
        
        pickle_file = open(self._get_db(Product.DB), DBBase.DB_WRITE_FLAG)
        pickle.dump(self.products, pickle_file, pickle.HIGHEST_PROTOCOL)



class Wallet(DBBase):
    DB = "wallet.db"
    
    EMPTY = "Your wallet is empty! Buy 100 Coins"
    COINS = "Coins"
    DEFAULT_COINS = 100
    
    def __init__(self, uid):
        self.value = 0
        self.uid = uid

    def get_all(self):
        wallets = {}
        pickle_file = open(self._get_db(Wallet.DB), DBBase.DB_READ_FLAG)
        try:
            wallets = pickle.load(pickle_file)
        except EOFError:
            pass         
        return wallets   

    def get(self):
        wallets = self.get_all()
        if wallets.has_key(self.uid):
            self.wallet = wallets.get(self.uid)
            self.value = self.wallet.value
            return self.wallet
        return None
    
    def get_balance(self):
        return self.value
    
    def set_total_coins(self, value):
        self.value = value
    
    def add_coins(self, deposit=0):
        self.value += deposit
            
    def substract_coins(self, debit=0):
        self.value -= debit
    
    def get_payment(self, bill):
        payment_allowed = False
        if self.get_balance() > bill:
            self.substract_coins(bill)
            payment_allowed = True
        return payment_allowed
    
    def save(self):
        wallets = self.get_all()
        wallets.update({self.uid : self})
        pickle_file = open(self._get_db(Wallet.DB), DBBase.DB_WRITE_FLAG)
        pickle.dump(wallets, pickle_file, pickle.HIGHEST_PROTOCOL)
    
    
class Store(DBBase):
    DB = "store.db"

    def __init__(self, uid):
        self.item = None
        self.id = None
        self.uid = uid
        self.product = None
    
    def get_all(self):
        products = {}
        pickle_file = open(self._get_db(Store.DB), DBBase.DB_READ_FLAG)
        try:
            products = pickle.load(pickle_file)
        except EOFError:
            pass
        return products

    def get(self):
        products = self.get_all()
        if products.has_key(self.uid):
            return products.get(self.uid)
        return None
    
    def add(self):
        self.id = self.generate_id()
        products = self.get_all()
        if products is None:
            products = {}
        products.update({self.uid : self.product })
        self._save(products)
    
    def _save(self, data):
        pickle_file = open(self._get_db(Store.DB), DBBase.DB_WRITE_FLAG)
        pickle.dump(data, pickle_file, pickle.HIGHEST_PROTOCOL)
    
    def get_product(self, item_name):
        if item_name is not None:
            self.product = Product().get(item_name)
            return self.product
        return None
    
    def buy(self, item_name=None):
        if item_name is not None:
            self.product = Product().get(item_name)
            self.add()
    
    def consume_item(self):
        product = self.get()
        if product is None:
            return None
        products = self.get_all()
        products.update({self.uid : None })
        self._save(products)
        return product

if __name__ == '__main__':
    product1 = Product(name="Blue Ship", description="super mega ship", photo="ship1.img", price="10")
    print "id: " + str(product1.get_id())
    product1.save()
    
    product2 = Product(name="Megatron ship", description="Megathron blue ship", photo="ship2.img", price="15")
    print "id: " + str(product2.get_id())
    product2.save()

    product3 = Product(name="Shield", description="Megathron blue ship", photo="shield.img", price="20")
    print "id: " + str(product3.get_id())
    product3.save()

    product4 = Product(name="Fuel Pack", description="Fuel ultra pack - 10 units", photo="fuel_pack.img", price="40")
    print "id: " + str(product4.get_id())
    product4.save()
    
