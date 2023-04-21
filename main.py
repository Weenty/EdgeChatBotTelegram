import asyncio
import functools
import threading
import time
import json
import sqlite3
import re
from telebot import types
from background import keep_alive
import telebot
from EdgeGPT import Chatbot, ConversationStyle
from telebot.util import quick_markup

temperature = 0.9
gbot = Chatbot(cookiePath='./cookies.json')
markup = quick_markup({
    'Github': {'url': 'https://github.com/pininkara/BingChatBot'},
}, row_width=1)

bot = telebot.TeleBot('')

conn = sqlite3.connect('dialogue.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS history (chatID INTEGER, message TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS list (userID TEXT UNIQUE, tokens INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS access (userID TEXT UNIQUE, userName TEXT, chatID TEXT UNIQUE)''')
try:
  cursor.execute("INSERT INTO list VALUES ('752816477', 600)")
except:
  pass
conn.commit()
conn.close()


def restricted(func):
    @functools.wraps(func)
    def wrapped(message):
        if str(message.from_user.id) not in get_users_list():
            bot.reply_to(message, ". . .")
            return
        return func(message)
    return wrapped

def get_users_list():
    conn = sqlite3.connect('dialogue.db')
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT userID FROM list")
        results = [x[0] for x in cursor.fetchall()]
    return results

@bot.message_handler(commands=['list'])
@restricted
def get_list(message):
    if message.from_user.id == 752816477:
        bot.send_message(message.chat.id, '\n'.join(get_users_list()))
    else:
        bot.send_message(message.chat.id, 'Даже не пытайся.')


@bot.message_handler(commands=['del'])
@restricted
def del_user_in_list(message):
    if message.from_user.id == 752816477:
        keyboard = types.InlineKeyboardMarkup()
        for user in get_users_list():
            button = types.InlineKeyboardButton(user, callback_data=user)
            keyboard.add(button)
        bot.send_message(message.chat.id, "Кого удалить?", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Даже не пытайся.')
        
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    conn = sqlite3.connect('dialogue.db')
    cursor = conn.cursor()
    acccess = (call.data).split('#')
    print(call.data, type(call.data))
    if acccess[0] == 'access':
        cursor.execute("DELETE from access where userID = ?", (acccess[1], ))
        cursor.execute("INSERT INTO list VALUES (?, ?)", (acccess[1], 600))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Доступ разрешен")
        bot.send_message(int(acccess[2]), 'Поздравляю! Вам был предоставлен доступ доступ!')
    elif acccess[0] == 'deny':
        cursor.execute("DELETE from access where userID = ?", (acccess[1], ))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Доступ отклонен")
        bot.send_message(int(acccess[2]), 'К сожалению, запрос на приглашение был отклонен...')
    elif (call.data).isdigit():
        selected_name = call.data
        cursor.execute("DELETE from list where userID = ?", (call.data, ))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"{selected_name} удален")
    else:
        responseList = asyncio.run(bingChat(call.data))
    bot.reply_to(
        call.message, responseList[0], parse_mode='Markdown', reply_markup=responseList[1])
    
    conn.commit()
    conn.close()
    

async def bingChat(messageText):
    response_dict = await gbot.ask(prompt=messageText, conversation_style=ConversationStyle.creative)

    json_str = json.dumps(response_dict)

    if 'text' in response_dict['item']['messages'][1]:
        response = re.sub(r'\[\^\d\^\]', '',
                          response_dict['item']['messages'][1]['text'])
    else:
        response = "Something wrong. Please reset chat"

    if 'suggestedResponses' in response_dict['item']['messages'][1]:
        suggestedResponses0 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['suggestedResponses'][0]['text'])
        suggestedResponses1 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['suggestedResponses'][1]['text'])
        suggestedResponses2 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['suggestedResponses'][2]['text'])
        markup = quick_markup({
            suggestedResponses0: {'callback_data': suggestedResponses0},
            suggestedResponses1: {'callback_data': suggestedResponses1},
            suggestedResponses2: {'callback_data': suggestedResponses2}
        }, row_width=1)
    else:
        markup = quick_markup({
            'No Suggested Responses': {'url': 'https://bing.com/chat'}
        }, row_width=1)

    if 'maxNumUserMessagesInConversation' in response_dict['item']['throttling'] and 'numUserMessagesInConversation' in response_dict['item']['throttling']:
        maxNumUserMessagesInConversation = response_dict['item'][
            'throttling']['maxNumUserMessagesInConversation']
        numUserMessagesInConversation = response_dict['item']['throttling']['numUserMessagesInConversation']
        response = response+"\n----------\n"
        response = response+"Messages In Conversation : %d / %d" % (
            numUserMessagesInConversation, maxNumUserMessagesInConversation)

    if numUserMessagesInConversation >= maxNumUserMessagesInConversation:
        await gbot.reset()
        response = response+"\nAutomatic reset succeeded🎉"

    if (len(response_dict['item']['messages'][1]['sourceAttributions']) >= 3):
        providerDisplayName0 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['sourceAttributions'][0]['providerDisplayName'])
        seeMoreUrl0 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['sourceAttributions'][0]['seeMoreUrl'])
        providerDisplayName1 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['sourceAttributions'][1]['providerDisplayName'])
        seeMoreUrl1 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['sourceAttributions'][1]['seeMoreUrl'])
        providerDisplayName2 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['sourceAttributions'][2]['providerDisplayName'])
        seeMoreUrl2 = re.sub(
            r'\[\^\d\^\]', '', response_dict['item']['messages'][1]['sourceAttributions'][2]['seeMoreUrl'])
        response = response+"\n----------\nReference:\n"
        response = response + \
            "1.[%s](%s)\n" % (providerDisplayName0, seeMoreUrl0)
        response = response + \
            "2.[%s](%s)\n" % (providerDisplayName1, seeMoreUrl1)
        response = response + \
            "3.[%s](%s)\n" % (providerDisplayName2, seeMoreUrl2)

    markup = quick_markup({
        suggestedResponses0: {'callback_data': suggestedResponses0},
        suggestedResponses1: {'callback_data': suggestedResponses1},
        suggestedResponses2: {'callback_data': suggestedResponses2}
    }, row_width=1)
    responseList = [response, markup]
    return responseList


@bot.message_handler(commands=['add'])
@restricted
def add_user_to_list(message):
    if message.from_user.id == 752816477:
        msg = bot.send_message(message.chat.id, 'Кого добавить? Укажите ID пользователя')
        bot.register_next_step_handler(msg, process_adding_step)
    else:
        bot.send_message(message.chat.id, 'Даже не пытайся.')


def process_adding_step(message):
    conn = sqlite3.connect('dialogue.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO list VALUES (?, ?)", (message.text, 600))
    bot.send_message(message.chat.id, 'Пользователь добавлен')
    conn.commit()
    conn.close()

def process_temperature_step(message):
    try:
        chat_id = message.chat.id
        global temperature
        temperature = float(message.text)
        bot.send_message(chat_id, "Теперь мой параметр креативности равен " + str(temperature))
    except Exception as e:
        bot.send_message(chat_id, "Кажется, вы указали некорректное число..")


@bot.message_handler(commands=['help'])
@restricted
def send_help(message):
    bot.send_message(message.chat.id, f"""\ 
        Команды для самого бота:
        /reset - очищает контекст диалога.
        /help - Получить помощь. Впрочем, раз вы это читаете, то уже освоились с ней.
        
        Это для меня, трогать нелья:
        /list
        /add
        /del
        """)

@bot.message_handler(commands=['start'])
def start(message):
    if str(message.from_user.id) not in get_users_list():
        bot.send_message(message.chat.id, 'Я понимаю, что хотите со мной пообщаться, но вас, к сожалению, нет в списке разрешенных пользователей... Но вы можете отправить запрос моему Создателю на отправку разрешения! Просто напишите /access')
    else:
        bot.send_message(message.chat.id, "Добро пожаловать в диалог с Telegram-ботом.")

@bot.message_handler(commands=['access'])
def access(message):
    if str(message.from_user.id) not in get_users_list():
        conn = sqlite3.connect('dialogue.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO access VALUES (?, ?, ?)", (message.from_user.id, message.from_user.username, message.chat.id))
            conn.commit()
            send_access(message.from_user.id, message.from_user.username, message.chat.id)
            bot.send_message(message.chat.id, "Запрос был отправлен! Я вам сообщу, когда вам будет предоставлен доступ.")
        except:
            bot.send_message(message.chat.id, "Запрос можно отправлять только один раз!")
        conn.close()
    else:
        bot.send_message(message.chat.id, 'У вас уже есть доступ, зачем вам это..?')

def send_access(id, username, chat_id):
    keyboard = types.InlineKeyboardMarkup()  
    keyboard.add(types.InlineKeyboardButton('Принять', callback_data=f'access#{id}#{chat_id}'))
    keyboard.add(types.InlineKeyboardButton('Отклонить', callback_data=f'deny#{id}#{chat_id}'))
    bot.send_message(752816477, f"Пользователь @{username} хочет получить доступ ко мне... Разрешить?", reply_markup=keyboard)


@bot.message_handler(commands=['reset'])
@restricted
def new(message):
    asyncio.run(gbot.reset())
    bot.reply_to(message, "Reset successful")
    

def send_message_to_gpt(message):
    try:
        responseList = asyncio.run(bingChat(message.text))
        bot.reply_to(message, responseList[0])
    except Exception as e:
        bot.reply_to(message, e)
    return True


def send_typing_action(chat_id, stop_typing):
    while not stop_typing.is_set():
        bot.send_chat_action(chat_id=chat_id, action='typing')
        time.sleep(1)



@bot.message_handler(func=lambda message: True)
@restricted
def echo_message(message):
    stop_typing = threading.Event()
    typing_thread = threading.Thread(target=send_typing_action, args=(message.chat.id, stop_typing))
    typing_thread.start()
    if send_message_to_gpt(message):
        stop_typing.set()
keep_alive()
bot.infinity_polling()