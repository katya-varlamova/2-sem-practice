"""
Организация пользовательского интерфейса.
"""
import glob
from os import system, path, remove
from random import choice, sample
import telebot
from cv2 import cv2
from telebot import types, apihelper
from bar_code import get_barcode
from database.database import Database
from synonyms import find_category



GREETING = u'Просто здравствуй, просто как дела? Если тебе нужна помощь, используй /help. \
Если хочешь узнать обо мне больше, используй /about.'
ABOUT = u'Я предоставляю вам информацию о результатах исследования качества и безопасности \
товаров, продающихся в торговых точках на всей территории Российской Федерации.\n \
Результаты исследований на сайте Роскачества: https://rskrf.ru/\n \
Информация обновляется 1 раз в неделю.'
HELP = u'Работать со мной очень просто! Если хочешь получить информацию о категории продуктов, \
просто введи её название. Если хочешь участвовать в викторине, набери /quiz. \
Ещё ты можешь отправить фотографию или сообщение со штрих-кодом и \
получить ценную информацию о продукте.'
INFO = u'Состав команды ДЕМКа:\nЕгор Воронин ИУ7-21Б\nМаксим Мицевич ИУ7-21Б\n \
Екатерина Варламова ИУ7-21Б\nЛапаев Денис ИУ7-21Б\nКирилл Рядинский ИУ7-23Б\n\n \
Менторы команды:\nСадулаева Теона\nБогаченко Артём\n'

CANT_FIND = u'Хм... Что-то я не могу ничего такого найти! \
Возможно, данной информации у меня нет, или же Вы просто опечатались.'
WANT_REV = u'Желаете оставить отзыв о данном продукте?\n'

print('connecting server...')
apihelper.proxy = {'https': 'https://163.172.190.160:8811'}

bot = telebot.TeleBot('token') ## токен

dbase = Database.get_shared()
categories = dbase.get_categories()


def bar2prod(bar_code):
    """
    returns info about product by barcode
    """
    if not bar_code.isdigit():
        return bar_code
    prod = dbase.get_product_by_barcode(bar_code)
    if not prod:
        text = CANT_FIND
        return text
    text = 'Название: {}\n\nПроизводитель: {}\n\n\
Оценка: {}\n'.format(prod.name, prod.producer, prod.points)
    if len(prod.adv) != 0:
        text += '\nПлюсы:\n'
    else:
        text += '\nПлюсов нет, но выдержитесь\n'
        for adv in prod.adv:
            text += '+ ' + adv + '\n'
    if len(prod.disadv) != 0:
        text += '\nМинусы:\n'
        for dis in prod.disadv:
            text += '- ' + dis + '\n'
    if len(prod.indicators) != 0:
        text += '\nИндикаторы:\n'
        for ind in prod.indicators:
            text += '-- ' + ind + '\n'
    if len(prod.res) != 0:
        text += '\nРезультаты исследования Роскачества:\n' + prod.res
    if len(prod.reviews) != 0:
        text += '\nОтзывы:\n'
        for rev in prod.reviews:
            text += '- ' + rev + '\n'
    return text

def check_answer(msg, products):
    """
    check user's answer on quiz
    """
    score_name = []

    for i in products:
        score_name.append((i.producer.strip(), i.points))

    answer = max(score_name, key=lambda x: x[1])[1]
    find = tuple_find(score_name, msg.text, 0)
    if not find:
        str_answer = u'Нужно было нажать на кнопочку...'
    elif answer == find[1]:
        str_answer = u'Да, вы правы! Оценка данного продукта {}.'.format(answer)
    else:
        str_answer = "Нет, это неправильный ответ. В следующий раз повезет!"
        str_answer += u"\nПравильный ответ: {}.".format(tuple_find(score_name, answer, 1)[0])
        str_answer += u"\nБаллы у этого продутка {}".format(answer)

        str_answer += u"\nИ баллы выбранного продукта {}".format(find[1])

    bot.send_message(msg.chat.id, str_answer, reply_markup=types.ReplyKeyboardRemove())

def tuple_find(tup, val, k):
    """
    find right answer on quiz
    """
    for i in tup:
        if i[k] == val:
            return i
    return None

def create_keyboard(products):
    """
    create keyboard for quiz
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)

    nameoffirst = types.KeyboardButton(products[0].producer.replace('&quot;', ''))
    nameofsecond = types.KeyboardButton(products[1].producer.replace('&quot;', ''))
    nameofthird = types.KeyboardButton(products[2].producer.replace('&quot;', ''))
    nameoffourth = types.KeyboardButton(products[3].producer.replace('&quot;', ''))

    markup.row(nameoffirst, nameofsecond)
    markup.row(nameofthird, nameoffourth)

    return markup

def cat_prod_for_quiz():
    """
    returns info about random products and their category
    """
    category = get_random_category()
    products = get_random_product(category)

    return category, products

def get_random_category():
    """
    returns random product category
    """
    return choice(list(categories.keys()))

def get_random_product(category):
    """
    returns random product from the top of category
    """
    products = dbase.get_top(category)
    return sample(products, k=4)


@bot.message_handler(commands=['start'])
def start_message(message):
    """
    start command handling
    """
    bot.send_message(message.chat.id, GREETING)

@bot.message_handler(commands=['about'])
def about_message(message):
    """
    about command handling
    """
    bot.send_message(message.chat.id, ABOUT)

@bot.message_handler(commands=['help'])
def help_message(message):
    """
    help command handling
    """
    bot.send_message(message.chat.id, HELP)

@bot.message_handler(commands=['info'])
def info_message(message):
    """
    info command handling
    """
    bot.send_message(message.chat.id, INFO)


@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    """
    quiz handling function
    """
    bot.reply_to(message, "Начинаем викторину")
    bot.send_message(message.chat.id, "Выбираем случайную категорию.")

    category, products = cat_prod_for_quiz()

    bot.send_message(message.chat.id, f"Это {categories[category]}!")

    markup = create_keyboard(products)

    msg = bot.send_message(message.chat.id, "Выберите один продукт!:", reply_markup=markup)

    bot.register_next_step_handler(msg, check_answer, products)



def create_comment(msg, markup, bar_code):
    """
    add user's comment into database
    """
    markup = types.ReplyKeyboardRemove()
    dbase.insert_review(bar_code, msg.text)
    bot.send_message(msg.chat.id, u'Отзыв добавлен.', reply_markup=markup)

def comment_handler(msg, markup, bar_code):
    """
    waits answer from user about comment
    """
    if msg.text == u'Да' or msg.text == u'Нет':
        markup = types.ReplyKeyboardRemove()
        if msg.text == u'Да':
            bot.send_message(msg.chat.id, u'Будте внимательны, когда оставляете отзыв!',
                             reply_markup=markup)
            bot.register_next_step_handler(msg, create_comment, markup, bar_code)
        if msg.text == u'Нет':
            bot.send_message(msg.chat.id, u'Конечно, как пожелаете.', reply_markup=markup)


def ask_comment(message, bar_code):
    """
    ask user to leave a comment
    """
    markup = markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, selective=False)
    markup.row('Да')
    markup.row('Нет')
    msg = bot.send_message(message.chat.id, WANT_REV, reply_markup=markup)
    bot.register_next_step_handler(msg, comment_handler, markup, bar_code)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """
    text handling function
    """
    try:
        text = ""
        markup = types.ReplyKeyboardRemove()
        rev = False
        if len(message.text) == 13 and message.text.isdigit():
            text = bar2prod(message.text)
            if message.text.isdigit() and dbase.get_product_by_barcode(message.text):
                rev = True
        else:
            find = find_category(message.text, categories)
            if not find[0]:
                text = CANT_FIND
            elif find[0] == 1:
                top = dbase.get_top(find[1])
                for product in top:
                    text += u'Название: {}\nПроизводитель: {}\n\
Оценка: {}\n\n'.format(product.name, product.producer, product.points)
            else:
                markup = types.ReplyKeyboardMarkup(selective=False, one_time_keyboard=True)
                for syno in find[1]:
                    markup.row(syno)
                text = u'Хм! Возможно, я чего-то не понял. Пожалуйста, уточните!\n'
        bot.send_message(message.chat.id, text, reply_markup=markup)
        if rev:
            ask_comment(message, message.text)
    except (AttributeError, cv2.error, IOError, ImportError, IndexError, KeyError, NameError, OSError, \
        SyntaxError, TypeError, ValueError, IndexError, ZeroDivisionError, RuntimeError):
        print('ошибка в handle_text')

@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    """
    photo handling function
    """
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = 'C:\\photo\\' + file_info.file_path[7:]
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        bar_code = get_barcode(src)
        text = bar2prod(get_barcode(src))
        bot.reply_to(message, text)
        if bar_code.isdigit() and dbase.get_product_by_barcode(bar_code):
            ask_comment(message, bar_code)
    except (AttributeError, cv2.error, IOError, ImportError, IndexError, KeyError, NameError, OSError, \
        SyntaxError, TypeError, ValueError, IndexError, ZeroDivisionError, RuntimeError):
        bot.reply_to(message, CANT_FIND)

try:
    print('done!')
    bot.polling(timeout=5000)
except (AttributeError, cv2.error, IOError, ImportError, IndexError, KeyError, NameError, OSError, \
        SyntaxError, TypeError, ValueError, IndexError, ZeroDivisionError, RuntimeError):
    print('Произошёл екзепшон...')
    filelist = glob.glob(path.join('C:\\photo\\', "*.jpg"))
    for file in filelist:
        remove(file)
    bot.stop_polling()
    system('pause')
