'''
loads database from API
'''
import re
import time
import asyncio
import json
import psycopg2
import requests
from aiohttp import ClientSession
ERROR = 1
SUCCESS = 0
PASSWORD = ""
NEED_UPDATE = True
class Product:
    '''
    class objects contain information abouut each product
    '''
    def __init__(self,
                 prod_id,
                 name="",
                 points=0,
                 adv=None,
                 disadv=None,
                 producer="",
                 res="",
                 indicators=None,
                 reviews=None):
        if adv is None:
            adv = []
        if disadv is None:
            disadv = []
        if indicators is None:
            indicators = []
        if reviews is None:
            reviews = []
        self.name = name
        self.points = points
        self.prod_id = prod_id
        self.adv = adv
        self.disadv = disadv
        self.producer = producer
        self.res = res
        self.indicators = indicators
        self.reviews = reviews
    @classmethod
    def del_html(cls, text):
        '''
        deletes html from string
        '''
        text = re.sub(r'(&\w\w;)|(&quot;)|(&#\d\d)', "", text)
        text = text.replace('<br />', '')
        text = text.replace('&nbsp;', '')
        return text
    async def update_product(self):
        '''
        fills product fields with new values
        '''
        url = 'https://rskrf.ru/api/product/' + str(self.prod_id)
        async with ClientSession() as session:
            async with session.get(url) as resp:
                response = await resp.read()
        json_obj = json.loads(response)
        try:
            err = json_obj["error"]
            if err is not None:
                return ERROR
            return ERROR
        except KeyError:
            try:
                self.name = self.del_html(json_obj["name"])
            except (KeyError, TypeError):
                self.name = ""
            try:
                self.points = float(json_obj["points"])
            except (KeyError, TypeError):
                self.points = 0
            try:
                self.producer = self.del_html(json_obj["trademark"])
            except (KeyError, TypeError):
                self.producer = ""
            try:
                self.res = self.del_html(json_obj["research_results"])
            except (KeyError, TypeError):
                self.res = ""
            try:
                self.adv = json_obj["+"]
            except (KeyError, TypeError):
                self.adv = []
            try:
                self.disadv = json_obj["-"]
            except (KeyError, TypeError):
                self.disadv = []
            try:
                self.indicators = []
                for j in json_obj["indicators"]:
                    self.indicators.append(str(j["name"]) + ": " + str(j["value"]))
            except (KeyError, TypeError):
                self.indicators = []
            return SUCCESS
class Database:
    '''
    class has 1 instance and contains methods for loading data
    '''
    __instance = None
    MAX = 10
    it = 10
    # 8 - "продукты питания", it is possible to add other categories from getcategories!
    key_categories = ["8", "28"]
    loading_finished = False
    list_categories = []
    top = dict()
    id_product = dict()
    id_name_category = dict()
    @staticmethod
    def get_shared():
        '''
        gives instance of database
        '''
        if Database.__instance is None:
            Database()
        return Database.__instance
    def __init__(self):
        '''
        inits database
        '''
        if Database.__instance is not None:
            raise Exception("This class is a singleton!")
        Database.__instance = self
        if NEED_UPDATE:
            self.__load_database()
        else:
            self.__get_postgresql_database()
    @classmethod
    def __connect_to_postgresql(cls):
        '''
        connects to postgresql database
        '''
        con = psycopg2.connect(
            database="postgres",
            user="postgres",
            password=PASSWORD,
            host="127.0.0.1",
            port="5432"
        )
        return con
    @classmethod
    def __create_products_table(cls, cur):
        '''
        creates products table
        '''
        cur.execute('''CREATE TABLE IF NOT EXISTS PRODUCTS
             (ID INT PRIMARY KEY NOT NULL,
             NAME TEXT NOT NULL,
             POINTS FLOAT(24) NOT NULL,
             TRADEMARK TEXT,
             RESULT TEXT,
             ADVANTAGES TEXT[],
             INDICATORS TEXT[],
             DISADVANTAGES TEXT[],
             REVIEWS TEXT[])
             ;''')
        cur.execute('''CREATE TABLE IF NOT EXISTS TOP
             (ID_CATEGORY INT PRIMARY KEY NOT NULL,
             NAME TEXT NOT NULL,
             PRODUCT_IDS INT[]);''')
    @classmethod
    def __norm(cls, string, mode):
        '''
        deletes quotations
        '''
        if string is None or string == "":
            return string
        res = ""
        if mode == 0:
            for j in string:
                res += j
                if j == "'":
                    res += "'"
        else:
            for j in string:
                res += j
                if j == '"':
                    res += '"'
        return res
    def __form_array(self, array):
        '''
        prepares array for postgres
        '''
        string = ""
        length = len(array)
        for j in range(length):
            if j != length - 1:
                string += '"' + self.__norm(array[j], 1) + '",'
            else:
                string += '"' + self.__norm(array[j], 1) + '"'
        return string
    def __insert_product_to_table(self, cur, prod):
        '''
        inserts product to table
        '''
        string = "INSERT INTO PRODUCTS VALUES ('{}','{}','{}','{}','{}',".format(prod.prod_id,
                                                                                 self.__norm(
                                                                                     prod.name,
                                                                                     0),
                                                                                 prod.points,
                                                                                 self.__norm(
                                                                                     prod.producer,
                                                                                     0),
                                                                                 self.__norm(
                                                                                     prod.res,
                                                                                     0))
        string += "'{"
        string += self.__form_array(prod.adv)
        string += "}','{"
        string += self.__form_array(prod.indicators)
        string += "}','{"
        string += self.__form_array(prod.disadv)
        string += "}','{"
        string += self.__form_array(prod.reviews)
        string += "}');"
        cur.execute(string)
    def __update_product_in_table(self, cur, prod):
        '''
        updates product to table
        '''
        string = "UPDATE PRODUCTS set "
        string += "NAME='{}',POINTS='{}',TRADEMARK='{}',RESULT='{}',".format(self.__norm(prod.name,
                                                                                         0),
                                                                             prod.points,
                                                                             self.__norm(
                                                                                 prod.producer,
                                                                                 0),
                                                                             self.__norm(prod.res,
                                                                                         0))
        string += "ADVANTAGES='{"
        string += self.__form_array(prod.adv)
        string += "}',INDICATORS='{"
        string += self.__form_array(prod.indicators)
        string += "}',DISADVANTAGES='{"
        string += self.__form_array(prod.disadv)
        string += "}', REVIEWS='{"
        string += self.__form_array(prod.reviews)
        string += "}'"
        string += " where ID ='{}'".format(prod.prod_id)
        cur.execute(string)
    def __get_postgresql_products(self):
        '''
        gets postgresql products
        '''
        con = self.__connect_to_postgresql()
        cur = con.cursor()
        cur.execute("SELECT * FROM PRODUCTS")
        rows = cur.fetchall()
        for row in rows:
            Database.id_product[row[0]] = Product(row[0], row[1], row[2],
                                                  row[5], row[7], row[3],
                                                  row[4], row[6], row[8])
        con.close()
    def __get_postgresql_top(self):
        '''
        gets postgresql top
        '''
        con = self.__connect_to_postgresql()
        cur = con.cursor()
        cur.execute("SELECT * FROM TOP")
        rows = cur.fetchall()
        for row in rows:
            Database.id_name_category[int(row[0])] = row[1]
            Database.top[int(row[0])] = []
            for id_pr in row[2]:
                Database.top[int(row[0])].append(Database.id_product[int(id_pr)])
        con.close()
    def __get_postgresql_database(self):
        '''
        get postgresql database
        '''
        self.__get_postgresql_products()
        self.__get_postgresql_top()
        Database.loading_finished = True
    def __load_database(self):
        '''
        inits loading database
        '''
        con = self.__connect_to_postgresql()
        cur = con.cursor()
        self.__create_products_table(cur)
        con.commit()
        con.close()
        self.__update_ids_for_considerable_ctgs()
        self.__update_categories()
        #async
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__update_products()) #got top of products and dict id - product
        loop.close()
        #
        self.__form_top()
        Database.loading_finished = True
    @classmethod
    def __find(cls, array, value):
        '''
        finds value in array
        '''
        for j in array:
            if j == value:
                return True
        return False
    def __update_ids_for_considerable_ctgs(self):
        '''
        updates ids for considerable categories
        '''
        response = requests.get("https://rskrf.ru/api/getcategories")
        json_obj = json.loads(response.text)
        for j in json_obj.values():
            for key, value in j.items():
                if self.__find(Database.key_categories, key):
                    for cat in value["categories"].keys():
                        Database.list_categories.append(int(cat)) #append category id
    def __update_categories(self):
        '''
        updates categories
        '''
        response = requests.get("https://rskrf.ru/api/getresearches")
        json_obj = json.loads(response.text)
        for category in json_obj:
            if self.__find(Database.list_categories, category["category"]):
                Database.id_name_category[int(category["id"])] = category["name"]#append research id
    def __add_or_update_products_postgresql(self):
        '''
        adds or updates products in postgresql database
        '''
        con = self.__connect_to_postgresql()
        cur = con.cursor()
        for prod in Database.id_product.values():
            cur.execute("SELECT ID from PRODUCTS WHERE (ID = {});".format(prod.prod_id))
            rows = cur.fetchall()
            if len(rows) == 0:
                self.__insert_product_to_table(cur, prod)
            else:
                self.__update_product_in_table(cur, prod)
        con.commit()
        con.close()
    @classmethod
    async def __add_category(cls, id_cat):
        '''
        adds category to database
        '''
        url = 'https://rskrf.ru/api/research/' + str(id_cat)
        async with ClientSession() as session:
            async with session.get(url) as resp:
                response = await resp.read()
        json_obj = json.loads(response)
        Database.top[int(id_cat)] = []
        for prod_id in json_obj["products"]:
            if prod_id is None or prod_id == "":
                continue
            product = Product(int(prod_id))
            Database.top[int(id_cat)].append(product)
            Database.id_product[int(prod_id)] = product
    async def __update_products(self):
        '''
        updates products
        '''
        await asyncio.wait(
            [self.__add_category(id_cat) for id_cat in
             Database.id_name_category])
        queue = []
        con = 0
        for prod_id in Database.id_product:
            queue.append(prod_id)
            con += 1
            if con == 100:
                await asyncio.wait([Database.id_product[i].update_product() for i in queue])
                time.sleep(1)
                con = 0
                queue = []
        await asyncio.wait([Database.id_product[i].update_product() for i in queue])
        self.__add_or_update_products_postgresql()
    def __add_or_update_top_postgresql(self):
        '''
        adds or updates top in postgresql
        '''
        con = self.__connect_to_postgresql()
        cur = con.cursor()
        for key, value in Database.top.items():
            cur.execute("SELECT ID_CATEGORY from TOP WHERE (ID_CATEGORY = {});".format(key))
            rows = cur.fetchall()
            if len(rows) == 0:
                string = "INSERT INTO TOP VALUES ('{}', '{}',".format(
                    key,
                    self.__norm(Database.id_name_category[key], 0)
                    )
                string += "'{"
                length = len(value)
                for j in range(length):
                    if j != length - 1:
                        string += '"' + str(value[j].prod_id) + '",'
                    else:
                        string += '"' + str(value[j].prod_id) + '"'
                string += "}')"
                cur.execute(string)
            else:
                string = "UPDATE TOP set NAME = '{}', PRODUCT_IDS =".format(
                    self.__norm(
                        Database.id_name_category[key],
                        0)
                    )
                string += "'{"
                length = len(value)
                for j in range(length):
                    if j != length - 1:
                        string += '"' + str(value[j].prod_id) + '",'
                    else:
                        string += '"' + str(value[j].prod_id) + '"'
                string += "}'"
                string += " WHERE ID_CATEGORY = '{}'".format(key)
                cur.execute(string)
        con.commit()
        con.close()
    def __form_top(self):
        '''
        forms top
        '''
        for key in Database.top:
            Database.top[key].sort(key=lambda x: x.points, reverse=True)
##            n = len(Database.top[key])
##            while (n > Database.MAX):
##                Database.top[key].pop()
##                n -= 1
        self.__add_or_update_top_postgresql()
    @classmethod
    def get_top(cls, id_cat):
        '''
        getter for top
        '''
        if not Database.loading_finished:
            return None
        if int(id_cat) in Database.top.keys():
            return Database.top[int(id_cat)][:10]
        return None
    @classmethod
    def get_categories(cls):
        '''
        getter for categories
        '''
        if not Database.loading_finished:
            return None
        return Database.id_name_category
    @classmethod
    def get_id_by_barcode(cls, barcode):
        '''
        getter for id by barcode
        '''
        response = requests.get('https://rskrf.ru/api/getproduct/' + str(barcode))
        json_obj = json.loads(response.text)
        try:
            err = json_obj["error"]
            if err is not None:
                return None
            return None
        except (KeyError, TypeError):
            product_id = json_obj[0]["id"]
            return int(product_id)

    def get_product_by_barcode(self, barcode):
        '''
        getter for product by barcode
        '''
        product_id = self.get_id_by_barcode(barcode)
        if product_id is None:
            return None
        if product_id in Database.id_product:
            return Database.id_product[product_id]
        return None
    def insert_review(self, barcode, review):
        '''
        inserts review
        '''
        product_id = self.get_id_by_barcode(barcode)
        prod = Database.id_product[product_id]
        prod.reviews.append(review)
        con = self.__connect_to_postgresql()
        cur = con.cursor()
        cur.execute("SELECT ID from PRODUCTS WHERE (ID = {});".format(product_id))
        rows = cur.fetchall()
        if len(rows) != 0:
            self.__update_product_in_table(cur, prod)
        con.commit()
if __name__ == "__main__":
    db = Database.get_shared()
    print("done")
##    db.insert_review("4601780002565", "классная мука")
##    db.insert_review("4602950114071", "классные сушки")
    #########################
##    top = db.get_top(5145)
##    for i in top:
##        print(i.name, i.reviews, i.prod_id)
##        print()
    #########################
##    categories = db.get_categories()
##    for k, v in categories.items():
##        print(k, v)
    #########################
##    product_by_barcode = db.get_product_by_barcode("4601780002565")##"4601780002565")
##    print(product_by_barcode.name, product_by_barcode.res)
