import os
import telebot
from telebot import types, apihelper
from flask import Flask, request
from time import sleep
from config import *
import psycopg2
import datetime

"""
SCAM IMPACT BOT BETA v1.4
#Бот для публикации постов о скамерах и  их автоматического бана
#Разработан специально для сети чатов -https://t.me/BazaScamerovGenshin
#2022
"""

TOKEN = os.environ['TOKEN']
APP_URL = os.environ['APP_URL']
APP_URL=APP_URL+TOKEN
DATABASE_URL =os.environ['DATABASE_URL']

bot = telebot.TeleBot(TOKEN)
db_connection = psycopg2.connect(DATABASE_URL, sslmode="require")
db_object = db_connection.cursor()
server = Flask(__name__)


@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return '!', 200


class Scammer:
    """Данные скамера из заявки"""

    def __init__(self):
        self.scammer_id = 0
        self.request_reason = ""
        self.proofs_link = ""
        self.social = ""
        self.username = ""
        self.message_for_pub = types.Message


scammerP = Scammer()  # объект для создания словаря
posts = {1: scammerP}  # словарь постов

bot_commands = [telebot.types.BotCommand("menu", "Главное меню бота"),
                telebot.types.BotCommand("sliv", "Слить скамера"),
                telebot.types.BotCommand("guide", "Инструкция по заполнению заявки"),
                telebot.types.BotCommand("report", "Обращение в тех. поддержку")]
bot.delete_my_commands()
bot.set_my_commands(bot_commands, scope=telebot.types.BotCommandScopeAllPrivateChats())


#   команды старт и меню


@bot.message_handler(commands=['start', 'menu'])
def start(message):
    if message.chat.type == "private":
        try:
            db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                              f" and social = 'Telegram'")
            if len(db_object.fetchall()) != 0:
                bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                      ' так как Вы были обнаружены в Базе Скамеров!')
                return
        except Exception as e:
            send_log("error", "database", message, 0, e)
        if message.text == "/start":
            send_log("com", "start", message, 0, None)
        # кнопкu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("/sliv")
        # проверка взаимодействия в ЛС
        bot.send_message(message.chat.id,
                         '*❗️Бот принадлежит сети чатов - https://t.me/BazaScamerovGenshin\n'
                         'Загрузить пруфы на скамера - https://t.me/bzscamchat\n'
                         'Посмотреть тех, кто уже слит - https://t.me/BazaScamerovGenshin\n'
                         'Найти гаранта - https://t.me/garantsgensh1n*\n'
                         '*Обмен и продажа - https://t.me/tradegensh1n*\n'
                         '/guide - инструкция по заполнению заявки\n'
                         '/report - обращение в тех. поддержку',
                         parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


#   /commands команда для проверки команд


@bot.message_handler(commands=['commands'])  # команда для проверки команд
def commands(message):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            try:
                db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                                  f" and social = 'Telegram'")
                if len(db_object.fetchall()) != 0:
                    bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                          ' так как Вы были обнаружены в Базе Скамеров!')
                    return
            except Exception as e:
                send_log("error", "database", message, 0, e)
            bot.send_message(message.chat.id,
                             '<b>Существующие команды для админов:</b>\n'
                             '/sendmes - отправка сообщения в указаный чат\n'
                             '/banuser - бан пользователя по ID во всех чатах\n'
                             '/unbanuser - разбан пользователя по ID о всех чатах\n'
                             '/sendpost - публикация поста одним сообщением\n'
                             '/about - информация о боте и  и его текущая версия',
                             parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


#   /sliv комнада для заполения заявки на слив


@bot.message_handler(commands=['sliv'])
def sliv(message):
    if message.chat.type == "private":
        try:
            db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                              f" and social = 'Telegram'")
            if len(db_object.fetchall()) != 0:
                bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                      ' так как Вы были обнаружены в Базе Скамеров!')
                return
        except Exception as e:
            send_log("error", "database", message, 0, e)
        if message.text == "/sliv":
            send_log("com", "слив", message, 0, None)  # logs
        #   кнопки
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add('VK', 'Telegram', 'Отменить')
        #    проверка взаимодействия в ЛС

        scammer = Scammer()
        bot.send_message(message.chat.id, 'Заполняем заявку на слив скамера...')
        msg = bot.send_message(message.chat.id, 'Введите социальную сеть (VK/Telegram) : ', reply_markup=markup)
        bot.register_next_step_handler(msg, social_handler, scammer)
    else:
        bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


#   /about команда для получения информации о боте


@bot.message_handler(commands=['about'])
def about(message):
    try:
        db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                          f" and social = 'Telegram'")
        if len(db_object.fetchall()) != 0:
            bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                  ' так как Вы были обнаружены в Базе Скамеров!')
            return
    except Exception as e:
        send_log("error", "database", message, 0, e)
    bot.send_message(message.chat.id, "<b>SKAM IMPACT BOT BETA v1.4</b>\n"
                                      "Бот для публикации постов о скамерах и  их автоматического бана\n"
                                      "Разработан специально для сети чатов BazaScamerovGenshin\n"
                                      "2022", parse_mode='HTML')
    start(message)


#   /repot команда для отправки сообщения о неисправности


@bot.message_handler(commands=['report'])
def report(message):
    if message.chat.type == "private":
        try:
            db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                              f" and social = 'Telegram'")
            if len(db_object.fetchall()) != 0:
                bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                      ' так как Вы были обнаружены в Базе Скамеров!')
                return
        except Exception as e:
            send_log("error", "database", message, 0, e)
        send_log("com", "report", message, 0, None)
        msg = bot.send_message(message.chat.id, "Изложите жалобу или предложение,"
                                                " возникшие при работе с ботом в одном сообщениии, "
                                                "по возможности приложив скриншоты или видеозапись с проблемой:")
        bot.register_next_step_handler(msg, report_send)
    else:
        bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


#   /guide команда для инструкции по пользованию ботом


@bot.message_handler(commands=['guide'])
def guide(message):
    if message.chat.type == "private":
        try:
            db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                              f" and social = 'Telegram'")
            if len(db_object.fetchall()) != 0:
                bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                      ' так как Вы были обнаружены в Базе Скамеров!')
                return
        except Exception as e:
            send_log("error", "database", message, 0, e)
        send_log("com", "guide", message, 0, None)
        bot.send_message(message.chat.id, "1. Для того, чтобы начать заполнять заявку на слив скамера, "
                                          "необходимо "
                                          " прописать команду\n/sliv\n"
                                          "2. После этого бот предложит выбрать: скамера из какой соц. сети "
                                          "Вы хотите слить. <b>Необходимо нажать на всплывающие кнопки и "
                                          "выбрать соц. сеть!</b> \n"
                                          "Если же кнопки не появились, нажмите на значок кнопок в поле"
                                          " ввода сообщения.\n"
                                          "3. Далее необходимо ввести ID скамера. Для отправьте ID цифрами, "
                                          "количество которых должно быть 9 и более!\n"
                                          "4. Далее введите причину, по которой Вы сливаете скамера."
                                          " Отправленый текст должен быть одним предложением,"
                                          " без знаков препинания\n"
                                          "5. Далее отправьте ссылку на сообщение с доказательствами из чата,"
                                          " ссылку на который предоставит бот. Убедитесь, что Вы отправляете"
                                          " ссылку именно на чат, указаный ботом!\n"
                                          "6. Далее бот предложит проверить Вашу заявку. Убедитесь в "
                                          "корректности "
                                          "данных и отправьте заявку на рассмотрение к модераторам. Если "
                                          "заявку "
                                          "необходимо отредактировать, воспользуйтесь всплывающими "
                                          "кнопками.\n"
                                          "7. Если Вы передумали заполнять заявку, нажмите на всплывающую "
                                          "кнопку "
                                          '"Отмена"\n'
                                          'Для того, чтобы обратиться в тех.поддержку, либо выразить свои '
                                          'жалобы'
                                          ' и предложения, введите команду\n/report\nДля того,'
                                          ' чтобы увидеть список доступных команд,'
                                          ' нажмите на при линии слева от поля ввода'
                                          ' сообщения.\n'
                                          'Приятного пользования!', parse_mode='HTML')
        start(message)
    else:
        bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


#   /sendmes команда для отправки пользовательских сообщений


@bot.message_handler(commands=['sendmes'])
def sendmes(message):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add('Отменить')
            if message.from_user.id is not dev_chat_id:
                send_log("com", "sendmes", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id, "Введите ID чата:", reply_markup=markup)
            bot.register_next_step_handler(msg, send_user_msg_id_handler)


#   /banuser бан пользователя по ID


@bot.message_handler(commands=['banuser'])
def banuser(message):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add('Отменить')
            send_log("com", "banuser", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id, "Введите ID пользователя:", reply_markup=markup)
            bot.register_next_step_handler(msg, ban_user_id_handler)


#   /unbanuser разбан пользователя по ID


@bot.message_handler(commands=['unbanuser'])
def unbanuser(message):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add('Отменить')
            send_log("com", "unbanuser", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id, "Введите ID пользователя:", reply_markup=markup)
            bot.register_next_step_handler(msg, unban_user_id_handler)


#   /sendpost команда для публикации поста одним сообщением


@bot.message_handler(commands=['sendpost'])
def sendpost(message):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != 'Отменить':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add('Отменить')
                send_log("com", "sendpost", message, 0, None)  # logs
                bot.send_message(message.chat.id,
                                 "Введите данные для публикации в следующем формате *БЕЗ ФОРМАТИРОВАНИЯ*",
                                 parse_mode='Markdown')
                bot.send_message(message.chat.id, "Соц.сеть\nID\nПричина\nСсылка на пруфы\nНапример:")
                msg = bot.send_message(message.chat.id, "Telegram\n123123123\nСкамер\nhttps://t.me/bzscamchat",
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, sendpost_parsing)
            else:
                bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")


#   логирование любых сообщений


@bot.message_handler(chat_types=['private'],
                     func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                               'text', 'location', 'contact', 'sticker', 'video_note'])
def message_handler(message):
    is_scammer = False
    text = " сообщения без реакции бота содержание ↓: "
    try:
        db_object.execute(f"select * from scammers where id_scammer = '{message.from_user.id}'"
                          f" and social = 'Telegram'")
        if len(db_object.fetchall()) != 0:
            bot.reply_to(message, 'Вам запрещено обращаться к боту,'
                                  ' так как Вы были обнаружены в Базе Скамеров!')
            is_scammer = True
    except Exception as e:
        send_log("error", "database", message, 0, e)
    if is_scammer:
        text = text + " (Скамер) "
    send_log("msg", text, message, 0, None)
    try:
        bot.forward_message(logs_id, message.chat.id, message.message_id)
    except apihelper.ApiTelegramException as e:
        send_log("error", "сообщения без реакции бота", message, 0, e)


@bot.message_handler(content_types=["new_chat_members"], chat_types=['supergroup'])
def handler_scammer(message):
    try:
        db_object.execute(f"select * from scammers where id_scammer = '{message.new_chat_members[0].id}'"
                          f" and social = 'Telegram'")
        if len(db_object.fetchall()) != 0:
            msg = bot.reply_to(message, 'Вам запрещено находиться в этой группе,'
                                        ' так как Вы были обнаружены в Базе Скамеров!')
            # text = f"{msg.text}'\nДля того, чтобы аппелировать блокировку, введите /banrevoke в личные сообщения
            # боту!"
            try:
                bot.send_message(message.new_chat_members[0].id, msg.text)
            except apihelper.ApiException as e:
                send_log("error", "kick", message, message.new_chat_members[0].id, e)
            sleep(1)
            try:
                bot.ban_chat_member(message.chat.id, message.new_chat_members[0].id)
            except apihelper.ApiException as e:
                send_log("error", message.chat.id, message, message.new_chat_members[0].id, e)
            msg_del = message.id + 1
            try:
                bot.delete_message(message.chat.id, msg_del)
            except apihelper.ApiTelegramException as e:
                send_log("error", "", message, 0, e)
            group_name = bot.get_chat(message.chat.id).title
            send_log("kick", group_name, message, 0, None)
    except Exception as e:
        send_log("error", "database", message, 0, e)


def sendpost_parsing(message):
    if message.text != "Отменить":
        send_log("msg", "sendpost", message, 0, None)
        try:
            arguments = message.text.splitlines()
            scammer = Scammer()
            if arguments[0] == "Telegram" or arguments[0] == "VK":
                scammer.social = arguments[0]
            else:
                message.text = ""
                send_log("error", "соц.сеть sendpost", message, 0, None)
                bot.send_message(message.chat.id, 'Введена некорректная соц. сеть!\nЗаполните заявку заново!')
                bot.register_next_step_handler(message, sendpost_parsing)
                return
            if 8 < len(arguments[1]) < 11:  # проверка ID
                try:
                    scammer.id_scammer = int(arguments[1])
                except ValueError as e:
                    message.text = ""
                    send_log("error", "IDsendpost", message, 0, e)  # logs
                    bot.send_message(message.chat.id, "Неверный формат ввода! ID должен содержать 9 или 10 цифр!", )
                    bot.register_next_step_handler(message, sendpost_parsing)
                    return
            else:
                message.text = ""
                send_log("error", "IDsendpost lenthg", message, 0, None)  # logs
                bot.send_message(message.chat.id, 'Неверный формат ввода! ID должен содержать 9 и более цифр!'
                                                  '\nВведите заново!')
                bot.register_next_step_handler(message, sendpost_parsing)
                return
            scammer.request_reason = arguments[2]
            if arguments[3].find("//t.me/bzscamchat") != -1:
                scammer.proofs_link = arguments[3]
            else:
                message.text = ""
                send_log("error", "Пруфыsendpost", message, 0, None)  # logs
                bot.send_message(message.chat.id, 'Неверный формат ввода!Ссылка должна содержать "//t.me/bzscamchat"!')
                bot.register_next_step_handler(message, sendpost_parsing)
                return
            ready_request_ann(message, scammer)
        except Exception as e:
            send_log("error", "sendpost pasring", message, 0, e)
            bot.send_message(message.chat.id, "Зафиксирована ошибка! См. логи!\n"
                                              "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
    else:
        bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")


@bot.message_handler(func=lambda message: True)
def publishing_handler(message):  # перехватчик публикации заявки
    if message.chat.id == moderators_chat_id:  # если это чат модеров
        if message.from_user.id in id_moders:
            post_msg = 0
            id_req = 0
            if message.reply_to_message is not None:
                is_unpublicated = False
                is_post_exist = False
                try:
                    db_object.execute("select message_for_pub, id_req from request")
                    messages_for_pub = db_object.fetchall()
                except Exception as e:
                    send_log("error", "database", message, 0, e)
                    return
                for i, item in enumerate(messages_for_pub):
                    if message.reply_to_message.id == item[0]:
                        id_req = messages_for_pub[i][1]
                        try:
                            db_object.execute(f"select status from request where id_req = {id_req}")
                            if db_object.fetchone()[0] is None:
                                is_unpublicated = True
                            is_post_exist = True
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                if is_post_exist and is_unpublicated:
                    if message.reply_to_message.id not in posts:
                        scammer_pub = Scammer()
                        scammer_pub.message_for_pub = message.reply_to_message
                        try:
                            command = f"select scammer_id from request where message_for_pub =" \
                                      f" {message.reply_to_message.id}"
                            db_object.execute(command)
                            if len(db_object.fetchall()) == 1:
                                db_object.execute(command)
                                scammer_pub.id_scammer = db_object.fetchone()[0]
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                            return
                        try:
                            command = f"select proof_link from request where message_for_pub =" \
                                      f" {message.reply_to_message.id}"
                            db_object.execute(command)
                            if len(db_object.fetchall()) == 1:
                                db_object.execute(command)
                                scammer_pub.proofs_link = db_object.fetchone()[0]
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                            return
                        try:
                            command = f"select request_reason from request where message_for_pub = " \
                                      f"{message.reply_to_message.id}"
                            db_object.execute(command)
                            if len(db_object.fetchall()) == 1:
                                db_object.execute(command)
                                scammer_pub.request_reason = db_object.fetchone()[0]
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                            return
                        try:
                            command = f"select social from request where message_for_pub = " \
                                      f"{message.reply_to_message.id}"
                            db_object.execute(command)
                            if len(db_object.fetchall()) == 1:
                                db_object.execute(command)
                                scammer_pub.social = db_object.fetchone()[0].strip()
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                            return
                        if scammer_pub.social == 'VK':
                            scammer_pub.message_for_pub.text = f'<b>VK</b>\n<b>ID: </b><code>{scammer_pub.id_scammer}' \
                                                               f'</code>\n' \
                                                               f'<b>Причина: </b> {scammer_pub.request_reason}\n' \
                                                               f'<b><a href="{scammer_pub.proofs_link}">' \
                                                               f'Открыть пруфы</a></b>\n' \
                                                               f'<b><a href="https://vk.com/id{scammer_pub.id_scammer}">' \
                                                               f'Открыть профиль</a></b> '
                        elif scammer_pub.social == 'Telegram':
                            scammer_pub.message_for_pub.text = f"<b>Telegram</b>\n<b>ID:" \
                                                               f" </b><code>{scammer_pub.id_scammer}</code>\n" \
                                                               f"<b>Причина: </b> {scammer_pub.request_reason}\n" \
                                                               f'<b><a href="{scammer_pub.proofs_link}">' \
                                                               f"Открыть пруфы </a></b>\n" \
                                                               f'<b><a href="tg://user?id={str(scammer_pub.id_scammer)}">' \
                                                               f'Открыть профиль</a></b>'
                    else:
                        scammer_pub = posts[message.reply_to_message.id]
                    if message.reply_to_message.id == scammer_pub.message_for_pub.id:
                        if scammer_pub.social == "Telegram":
                            try:
                                msg = bot.send_message(chanel_chat_id, scammer_pub.message_for_pub.text,
                                                       parse_mode='HTML')
                                post_msg = int(msg.id)
                            except apihelper.ApiTelegramException as e:
                                send_log("error", "pubPost", message, 0, e)
                        elif scammer_pub.social == "VK":
                            try:
                                msg = bot.send_message(chanel_chat_id, scammer_pub.message_for_pub.text,
                                                       parse_mode='HTML')
                                post_msg = int(msg.id)
                            except apihelper.ApiTelegramException as e:
                                send_log("error", "pubPost", message, 0, e)
                            for i in range(len(chats_for_ban_ann_id)):
                                bot.send_message(chats_for_ban_ann_id[i],  #
                                                 f'<b><a href ="https://vk.com/id{scammer_pub.id_scammer}">'
                                                 f'Скамер VK: </a></b>'
                                                 f" <code>{scammer_pub.id_scammer}</code> "
                                                 f"был слит\n"
                                                 f"Посмотреть тех, кто уже слит: https://t.me/BazaScamerovGenshin",
                                                 parse_mode='HTML')
                        if scammer_pub.social == "Telegram":
                            for i in range(len(chats_for_ban_id)):
                                try:
                                    bot.ban_chat_member(chats_for_ban_id[i], scammer_pub.id_scammer)
                                    send_log("ban", f"{chats_for_ban_id[i]}", message, scammer_pub.id_scammer, None)
                                except apihelper.ApiTelegramException as e:
                                    send_log("error", f"{chats_for_ban_id[i]}", message, scammer_pub.id_scammer, e)  # logs
                            for i in range(len(chats_for_ban_ann_id)):
                                bot.send_message(chats_for_ban_ann_id[i],  #
                                                 f'<b><a href ="tg://user?id={str(scammer_pub.id_scammer)}">'
                                                 f'Скамер telegram: </a></b>'
                                                 f" <code>{scammer_pub.id_scammer}</code> "
                                                 f"был забанен\n"
                                                 f"Посмотреть тех, кто уже слит: https://t.me/BazaScamerovGenshin",
                                                 parse_mode='HTML')
                                send_log("msg", f"{chats_for_ban_ann_id[i]}", message, 0, None)
                        send_log("pub", "", message, scammer_pub.id_scammer, None)  # logs
                        try:
                            db_object.execute("INSERT INTO posts(id_req, text, date_pub, id_admin)"
                                              f" VALUES ({id_req},'{post_msg}', '{datetime.datetime.today()}', "
                                              f"'{message.from_user.id}')")
                            db_connection.commit()
                            db_object.execute(f'select id_post from posts where id_req = {id_req}  and id_admin ='
                                              f" '{message.from_user.id}'")
                            id_post = db_object.fetchone()[0]
                            db_object.execute(f"select * from scammers where id_scammer = '{scammer_pub.id_scammer}' "
                                              f'and social = '
                                              f" '{scammer_pub.social}'")
                            if len(db_object.fetchall()) == 0:
                                db_object.execute("INSERT INTO scammers(id_scammer, date_ban, social, id_post)"
                                                  " VALUES (%s, %s, %s, %s)",
                                                  (scammer_pub.id_scammer, datetime.date.today(), scammer_pub.social,
                                                   id_post))
                                db_connection.commit()
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                        bot.reply_to(message.reply_to_message, 'Заявка отпубликована! '
                                                               'Во избежание повторной публикации не '
                                                               'отвечайте или удалите сообщение!')
                        try:
                            db_object.execute(f"update request set status = 'publicated' where id_req = {id_req}")
                            db_connection.commit()
                        except Exception as e:
                            send_log("error", "database", message, 0, e)
                else:
                    bot.send_message(message.chat.id, "Данный пост уже опубликован!")
                    send_log("error", "pub", message, 0, None)


def social_handler(message, scammer):  # перехватчик соц. сети
    #   кнопки отмены
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Отменить')
    if message.text != "Отменить":
        if message.text == "Telegram" or message.text == "VK":
            scammer.social = message.text
            msg = bot.send_message(message.chat.id, 'Введите ID (вечная ссылка): ', reply_markup=markup)
            bot.register_next_step_handler(msg, id_handler, scammer)
        else:
            send_log("error", "соц.сеть", message, 0, None)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add('/sliv')
            msg = bot.send_message(message.chat.id, 'Введена некорректная соц. сеть!\nЗаполните заявку заново!',
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, sliv)
    else:
        if message.from_user.id in id_moders:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
        else:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
        scammer.social = ""
        start(message)


def id_handler(message, scammer):  # перехватчик ID
    if message.text != "Отменить":
        # проверка минимально допустимой длины ID
        if 8 < len(message.text) < 11:
            try:  # проверка цифры ли
                send_log("msg", "ID", message, 0, None)  # logs
                scammer.id_scammer = int(message.text)
                msg = bot.send_message(message.chat.id, "Введите причину:  ")
                bot.register_next_step_handler(msg, reason_handler, scammer)
            except ValueError as e:
                send_log("error", "ID", message, 0, e)  # logs
                msg = bot.send_message(message.chat.id, "Неверный формат ввода! ID должен содержать 9 или 10 цифр!")
                bot.register_next_step_handler(msg, id_handler, scammer)
        else:
            send_log("error", "ID", message, 0, None)
            msg = bot.send_message(message.chat.id, "Неверный формат ввода! ID должен содержать 9 или 10 цифр!")
            bot.register_next_step_handler(msg, id_handler, scammer)
    else:
        if message.from_user.id in id_moders:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
        else:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
        scammer.id_scammer = 0
        start(message)


def username_handler(message, scammer):  # перехватчик никнейма
    if message.text != "Отменить":
        if message.text.find("@") == -1:  # проверка отсутствия собаки
            send_log("msg", "username", message, 0, None)  # logs
            scammer.username = message.text
            msg = bot.send_message(message.chat.id, 'Введите причину: ')
            bot.register_next_step_handler(msg, reason_handler, scammer)
        else:
            send_log("error", "username", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id, "Введите корректный никнейм без @!")
            bot.register_next_step_handler(msg, username_handler, scammer)
    else:
        if message.from_user.id in id_moders:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
        else:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
        scammer.username = ""
        start(message)


def reason_handler(message, scammer):  # перехватчик причины
    if message.text != "Отменить":
        send_log("msg", "причина", message, 0, None)  # logs
        scammer.request_reason = message.text
        msg = bot.send_message(message.chat.id, "Скопируйте ссылку на пруфы из чата и вставьте сюда.\n"
                                                "https://t.me/bzscamchat")
        bot.register_next_step_handler(msg, proofs_handler, scammer)
    else:
        if message.from_user.id in id_moders:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
        else:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
        scammer.request_reason = ""
        start(message)


def proofs_handler(message, scammer):  # перехватчик пруфов
    if message.text != "Отменить":
        if message.text.find("//t.me/bzscamchat") != -1:
            send_log("msg", "пруфы", message, 0, None)  # logs
            scammer.proofs_link = message.text
            ready_request_ann(message, scammer)
        else:
            send_log("error", "пруфы", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id, 'Неверный формат ввода!Ссылка должна содержать '
                                                    '"//t.me/bzscamchat"!')
            bot.register_next_step_handler(msg, proofs_handler, scammer)
    else:
        scammer.proofs_link = ""
        if message.from_user.id in id_moders:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
        else:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
        start(message)


def ready_request_ann(message, scammer):  # оповещение о готовности заявки
    bot.send_message(message.chat.id, "Заявка готова! Проверьте корректность данных: ")
    if scammer.social == "VK":
        bot.send_message(message.chat.id, f'VK\nID : {scammer.id_scammer}\nПричина: {scammer.request_reason}\n'
                                          f'Ссылка: {scammer.proofs_link}')
    elif scammer.social == "Telegram":
        bot.send_message(message.chat.id,
                         f"Telegram\nID: {scammer.id_scammer}\n"
                         f"Причина: {scammer.request_reason}\nСсылка: {scammer.proofs_link}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Да', 'Нет')
    msg = bot.send_message(message.chat.id, "Всё верно?", reply_markup=markup)
    bot.register_next_step_handler(msg, correct_request, scammer)


def correct_request(message, scammer):  # подтверждение корректности заявки
    answer = message.text
    match answer:
        case "Отменить":
            if message.from_user.id in id_moders:
                bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
            else:
                bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
            start(message)
            pass
        case "Да":
            send_log("msg", "send", message, 0, None)  # logs
            a = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, 'Заявка отправлена на рассмотрение модераторам!', reply_markup=a)
            sending_to_moderators(message, scammer)
            start(message)
        case "Нет":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("ID", 'Причина', 'Пруфы', 'Заполнить заново', 'Отменить')
            msg = bot.send_message(message.chat.id, 'Какой параметр необходимо изменить?', reply_markup=markup)
            bot.register_next_step_handler(msg, edit_request_query, scammer)


def edit_request_query(message, scammer):  # предложение варианта исправления заявки
    if message.text == "Заполнить заново":
        sliv(message)
    elif message.text == 'Отменить':
        if message.from_user.id in id_moders:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv или /sendpost")
        else:
            bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
        start(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add('Отменить')
        edit_param = message.text
        msg = bot.send_message(message.chat.id, f'Введите новый параметр: {edit_param}', reply_markup=markup)
        bot.register_next_step_handler(msg, edit_request, edit_param, scammer)


def edit_request(message, edit_param, scammer):  # исправление параметра
    match edit_param:
        case "ID":
            if 8 < len(message.text) < 11:  # проверка ID
                try:
                    send_log("msg", "ID (edit)", message, 0, None)  # logs
                    scammer.id_scammer = int(message.text)
                    ready_request_ann(message, scammer)
                except ValueError as e:
                    send_log("error", "ID", message, 0, e)  # logs
                    msg = bot.send_message(message.chat.id,
                                           "Неверный формат ввода! ID должен содержать 9 или 10 цифр!", )
                    bot.register_next_step_handler(msg, edit_param, "ID")
            else:
                send_log("error", "ID", message, 0, None)  # logs
                msg = bot.send_message(message.chat.id,
                                       'Неверный формат ввода! ID должен содержать 9 и более цифр!\nВведите заново!')
                bot.register_next_step_handler(msg, edit_param, "ID")
        case "Причина":
            send_log("msg", "Причина (edit)", message, 0, None)  # logs
            scammer.request_reason = message.text
            ready_request_ann(message, scammer)
        case "Пруфы":
            if message.text.find("//t.me/bzscamchat") != -1:
                send_log("msg", "Пруфы (edit)", message, 0, None)  # logs
                scammer.proofs_link = message.text
                ready_request_ann(message, scammer)
            else:
                send_log("error", "Пруфы", message, 0, None)  # logs
                msg = bot.send_message(message.chat.id,
                                       'Неверный формат ввода!Ссылка должна содержать "//t.me/bzscamchat"!'
                                       '\nВведите заново!')
                bot.register_next_step_handler(msg, edit_param, "Пруфы")

        # case "Никнейм":
        #     if message.text.find("@") == -1:
        #         send_log("msg", "Никнейм (edit)", message, 0, None)  # logs
        #         scammer.username = message.text
        #         ready_request_ann(message, scammer)
        #     else:
        #         send_log("error", "Никнейм", message, 0, None)  # logs
        #         msg = bot.send_message(message.chat.id, "Введите корректный никнейм без @!")
        #         bot.register_next_step_handler(msg, edit_param, "Никнейм")


def sending_to_moderators(message, scammer):  # отправка заявки модерам
    try:
        bot.send_message(moderators_chat_id,
                         f"Новая заявка на публикацию от @{message.from_user.username}\n<b>Перед публикацией внимательно"
                         f" проверьте соответствие всех данных</b>", parse_mode='HTML')
        if scammer.social == 'VK':
            scammer.message_for_pub = bot.send_message(moderators_chat_id,
                                                       f"<b>VK</b>\n<b>ID: </b><code>{scammer.id_scammer}</code>\n"
                                                       f"<b>Причина: </b> {scammer.request_reason}\n"
                                                       f"<b><a href=\"{scammer.proofs_link}\">Открыть пруфы </a></b>\n"
                                                       f'<b><a href="https://vk.com/id{scammer.id_scammer}">Открыть '
                                                       f'профиль</a></b>', parse_mode='HTML')
            scammer.message_for_pub.text = f'<b>VK</b>\n<b>ID: </b><code>{scammer.id_scammer}</code>\n' \
                                           f'<b>Причина: </b> {scammer.request_reason}\n' \
                                           f'<b><a href=\"{scammer.proofs_link}\">Открыть пруфы </a></b>\n' \
                                           f'<b><a href="https://vk.com/id{scammer.id_scammer}">' \
                                           f'Открыть профиль</a></b> '
        elif scammer.social == 'Telegram':
            scammer.message_for_pub = bot.send_message(moderators_chat_id,
                                                       f"<b>Telegram</b>\n"
                                                       f"<b>ID: </b><code>{scammer.id_scammer}</code>\n"
                                                       f"<b>Причина: </b> {scammer.request_reason}\n"
                                                       f"<b><a href=\"{scammer.proofs_link}\">Открыть пруфы </a></b>\n"
                                                       f'<b><a href="tg://user?id={str(scammer.id_scammer)}">'
                                                       f'Открыть профиль</a></b>', parse_mode='HTML')
            scammer.message_for_pub.text = f"<b>Telegram</b>\n" \
                                           f"<b>ID: </b><code>{scammer.id_scammer}</code>\n" \
                                           f"<b>Причина: </b> {scammer.request_reason}\n" \
                                           f"<b><a href=\"{scammer.proofs_link}\">Открыть пруфы </a></b>\n" \
                                           f'<b><a href="tg://user?id={str(scammer.id_scammer)}">' \
                                           f'Открыть профиль</a></b>'
        posts[scammer.message_for_pub.id] = scammer
        msg = scammer.message_for_pub
        try:
            db_object.execute("INSERT INTO request(scammer_id, request_reason, proof_link, "
                              "social, message_for_pub, author_username) VALUES (%s, %s, %s, %s, %s, %s)",
                              (scammer.id_scammer, scammer.request_reason, scammer.proofs_link,
                               scammer.social, msg.id, message.from_user.username))
            db_connection.commit()
        except Exception as e:
            send_log("error", "database", message, 0, e)
        bot.send_message(moderators_chat_id, f"Сообщение для публикации № {msg.id}\n"
                                             "Чтобы опубликовать сообщение, ответьте на него любым текстом, "
                                             "либо удалите для отмены заявки")
    except apihelper.ApiTelegramException as e:
        send_log("error", "sendingRequest", message, 0, e)


def report_send(message):  # отправка в лс разработчику
    if message.chat.type == "private":
        send_log("msg", "report", message, 0, None)
        try:
            bot.forward_message(dev_chat_id, message.chat.id, message.message_id)
        except apihelper.ApiTelegramException as e:
            send_log("error", "reportSend", message, 0, e)
        bot.send_message(message.chat.id, "Обращение отправлено!\nВ ближайшее время с Вами свяжутся специалисты"
                                          " тех. поддержки либо администраторы!")
        start(message)
    else:
        bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def send_user_msg_id_handler(message):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                if len(message.text) > 8:
                    try:  # проверка цифры ли
                        send_log("msg", "IDChat", message, 0, None)  # logs
                        chat_id = int(message.text)
                        msg = bot.send_message(message.chat.id, "Укажите сообщение"
                                                                " (Для форматирования используйте HTML): ")
                        bot.register_next_step_handler(msg, send_user_msg_checker, chat_id)
                    except ValueError as e:
                        send_log("error", "IDChat", message, 0, e)  # logs
                        msg = bot.send_message(message.chat.id,
                                               "Неверный формат ввода! ID должен содержать 9 и более цифр!")
                        bot.register_next_step_handler(msg, sendmes)
                else:
                    send_log("error", "IDChat", message, 0, None)  # logs
                    msg = bot.send_message(message.chat.id,
                                           "Неверный формат ввода! ID должен содержать 9 и более цифр!")
                    bot.register_next_step_handler(msg, sendmes)
            else:
                bot.send_message(message.chat.id, "Для того, чтобы написать сообщение введите /sendmes")
                start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def send_user_msg_checker(message, chat_id):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add('Отправить', 'Изменить сообщение', 'Изменить ID', 'Отменить')
                send_log("msg", "messageText", message, 0, None)  # logs
                bot.send_message(message.chat.id, f"Ваше сообщение:\n{message.text} \n", parse_mode='HTML')
                msg = bot.send_message(message.chat.id, f'Для отправки нажмите "отправить"', parse_mode='HTML',
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, send_user_msg_sender, chat_id, message.text)
            else:
                bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
                start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def send_user_msg_sender(message, chat_id, message_send):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                if message.text == "Отправить":
                    markup = types.ReplyKeyboardRemove()
                    try:
                        bot.send_message(chat_id, message_send, parse_mode='HTML', )
                        bot.send_message(message.chat.id, "*Сообщение отправлено\\!*", parse_mode='MarkdownV2',
                                         reply_markup=markup)
                    except apihelper.ApiException as e:
                        bot.send_message(message.chat.id, "*Сообщение не отправлено\\!*", parse_mode='MarkdownV2',
                                         reply_markup=markup)
                        send_log("error", "send", message, 0, e)  # logs
                elif message.text == "Изменить сообщение":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add('Отменить')
                    msg = bot.send_message(message.chat.id, "Введите сообщение заново!", reply_markup=markup)
                    bot.register_next_step_handler(msg, send_user_msg_checker, chat_id)
                elif message.text == "Изменить ID":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add('Отменить')
                    msg = bot.send_message(message.chat.id, "Введите ID заново!", reply_markup=markup)
                    bot.register_next_step_handler(msg, send_user_msg_id_handler)
                elif message.text != "Отменить":
                    send_log("error", "send", message, 0, None)  # logs
                else:
                    bot.send_message(message.chat.id, "Для того, чтобы заполнить заявку введите /sliv")
                    start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def ban_user_id_handler(message):
    if message.text != "Отменить":
        if len(message.text) > 8:
            try:  # проверка цифры ли
                send_log("msg", "IDban", message, 0, None)  # logs
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add('Скамер', 'Отменить')
                id_ban = int(message.text)
                msg = bot.send_message(message.chat.id, "Введите причину:\n"
                                                        'Для публикации сообщения о бане в чаты, введите: "Скамер" ',
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, ban_user_checker, id_ban)
            except ValueError as e:
                send_log("error", "IDban", message, 0, e)  # logs
                msg = bot.send_message(message.chat.id,
                                       "Неверный формат ввода! ID должен содержать 9 и более цифр!")
                bot.register_next_step_handler(msg, ban_user_id_handler)
        else:
            send_log("error", "IDban", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id,
                                   "Неверный формат ввода! ID должен содержать 9 и более цифр!")
            bot.register_next_step_handler(msg, ban_user_id_handler)
    else:
        bot.send_message(message.chat.id, "Для того, чтобы забанить пользователя, введите /banuser")
        start(message)


def ban_user_checker(message, id_ban):
    is_scammer = False
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                if message.text == "Скамер":
                    is_scammer = True
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add('Забанить', 'Изменить причину', 'Изменить ID', 'Отменить')
                send_log("msg", "banReason", message, 0, None)  # logs
                bot.send_message(message.chat.id, f"Ваша причина:\n{message.text} \n", parse_mode='HTML')
                msg = bot.send_message(message.chat.id, f'Для бана нажмите "Забанить"', parse_mode='HTML',
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, ban_user_sender, id_ban, is_scammer)
            else:
                bot.send_message(message.chat.id, "Для того, чтобы забанить пользователя, введите /banuser")
                start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def ban_user_sender(message, id_ban, is_scammer):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                if message.text == "Забанить":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    markup.add('/menu')
                    is_ban = False
                    for i in range(len(chats_for_ban_id)):
                        try:
                            bot.ban_chat_member(chats_for_ban_id[i], id_ban)
                            send_log("ban", f"{chats_for_ban_id[i]}", message, id_ban, None)
                            try:
                                db_object.execute(
                                    f"select * from scammers where id_scammer = '{id_ban}' "
                                    f"and social = 'Telegram'")
                                if len(db_object.fetchall()) == 0:
                                    db_object.execute("INSERT INTO scammers(id_scammer, date_ban, social)"
                                                      " VALUES (%s, %s, %s)",
                                                      (id_ban, datetime.date.today(), 'Telegram'))
                                    db_connection.commit()
                            except Exception as e:
                                send_log("error", "database", message, 0, e)
                            is_ban = True
                        except apihelper.ApiTelegramException as e:
                            send_log("error", f"{chats_for_ban_id[i]}", message, id_ban, e)  # logs
                    if is_ban:
                        bot.send_message(message.chat.id, 'Пользователь забанен!', reply_markup=markup)
                        if is_scammer:
                            for i in range(len(chats_for_ban_ann_id)):
                                bot.send_message(chats_for_ban_ann_id[i],  #
                                                 f'<b><a href ="tg://user?id={str(id_ban)}">'
                                                 f'Скамер telegram: </a></b>'
                                                 f" <code>{id_ban}</code> "
                                                 f"был забанен\n"
                                                 f"Посмотреть тех, кто уже слит: https://t.me/BazaScamerovGenshin",
                                                 parse_mode='HTML')
                                send_log("msg", f"{chats_for_ban_ann_id[i]}", message, 0, None)
                    else:
                        bot.send_message(message.chat.id, 'Пользователь не забанен!', reply_markup=markup)
                elif message.text == "Изменить ID":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add('Отменить')
                    msg = bot.send_message(message.chat.id, "Введите ID заново!", reply_markup=markup)
                    bot.register_next_step_handler(msg, ban_user_id_handler)
                elif message.text == "Изменить причину":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add('Отменить')
                    msg = bot.send_message(message.chat.id, "Введите причину заново!", reply_markup=markup)
                    bot.register_next_step_handler(msg, ban_user_checker, id_ban)
                else:
                    bot.send_message(message.chat.id, "Для того, чтобы забанить пользователя, введите /banuser")
                    start(message)
            elif message.text == "Отменить":
                bot.send_message(message.chat.id, "Для того, чтобы забанить пользователя, введите /banuser")
                send_log("error", "ban", message, 0, None)  # logs
                start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def unban_user_id_handler(message):
    if message.text != "Отменить":
        if len(message.text) > 8:
            try:  # проверка цифры ли
                send_log("msg", "IDunban", message, 0, None)  # logs
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add('Отменить')
                id_ban = int(message.text)
                unban_user_checker(message, id_ban)
            except ValueError as e:
                send_log("error", "IDunban", message, 0, e)  # logs
                msg = bot.send_message(message.chat.id,
                                       "Неверный формат ввода! ID должен содержать 9 и более цифр!")
                bot.register_next_step_handler(msg, unban_user_id_handler)
        else:
            send_log("error", "IDban", message, 0, None)  # logs
            msg = bot.send_message(message.chat.id,
                                   "Неверный формат ввода! ID должен содержать 9 и более цифр!")
            bot.register_next_step_handler(msg, unban_user_id_handler)
    else:
        bot.send_message(message.chat.id, "Для того, чтобы разбанить пользователя, введите /unbanuser")
        start(message)


def unban_user_checker(message, id_ban):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add('Разбанить', 'Изменить ID', 'Отменить')
                msg = bot.send_message(message.chat.id, f'Для разбана нажмите "Разбанить"', parse_mode='HTML',
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, unban_user_sender, id_ban)
            else:
                bot.send_message(message.chat.id, "Для того, чтобы разбанить пользователя, введите /unbanuser")
                start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


def unban_user_sender(message, id_ban):
    if message.from_user.id in id_moders:
        if message.chat.type == "private":
            if message.text != "Отменить":
                if message.text == "Разбанить":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    markup.add('/menu')
                    is_unban = False
                    for i in range(len(chats_for_ban_id)):
                        try:
                            bot.unban_chat_member(chats_for_ban_id[i], id_ban)
                            is_unban = True
                            send_log("unban", f"{chats_for_ban_id[i]}", message, id_ban, None)
                            try:
                                db_object.execute(
                                    f"select * from scammers where id_scammer = '{id_ban}' "
                                    f"and social = 'Telegram'")
                                if len(db_object.fetchall()) != 0:
                                    db_object.execute(
                                        f"delete from scammers where id_scammer = '{id_ban}' "
                                        f"and social = 'Telegram'")
                                    db_connection.commit()
                            except Exception as e:
                                send_log("error", "database", message, 0, e)
                        except apihelper.ApiTelegramException as e:
                            send_log("error", f"{chats_for_ban_id[i]}", message, id_ban, e)  # logs
                    if is_unban:
                        bot.send_message(message.chat.id, 'Пользователь разбанен!', reply_markup=markup)
                    else:
                        bot.send_message(message.chat.id, 'Пользователь не разбанен!', reply_markup=markup)
                elif message.text == "Изменить ID":
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add('Отменить')
                    msg = bot.send_message(message.chat.id, "Введите ID заново!", reply_markup=markup)
                    bot.register_next_step_handler(msg, unban_user_id_handler)

            else:
                bot.send_message(message.chat.id, "Для того, чтобы разбанить пользователя, введите /unbanuser")
                send_log("error", "send", message, 0, None)  # logs
                start(message)
        else:
            bot.send_message(message.chat.id, "Для взаимодействия с ботом, напишите в личные сообщения!")


#   logs


def send_log(type_log, step, message, id_log, e):  # публикация логов
    ex = e
    chat_id = logs_id
    tire = '-'
    match type_log:
        case "msg":
            if step.lstrip(tire).isdigit():
                try:
                    int(step)
                    group_name = chats_for_ban_id_dict.get(int(step))
                    bot.send_message(chat_id, f"#msg отправлено уведомление о бане скамера в {group_name}")
                except ValueError as e:
                    print(e)
            else:
                if step == "send":
                    bot.send_message(chat_id,
                                     f"#msg Пользователь <code>{message.from_user.username}</code> ; "
                                     f"<code>{message.from_user.id}</code> "
                                     f"отправил заявку на публикацию", parse_mode='HTML')
                else:
                    bot.send_message(chat_id,
                                     f"#msg Пользователь <code>{message.from_user.username}</code> ; "
                                     f"<code>{message.from_user.id}</code>"
                                     f" ввод {step} <code>{message.text}</code>", parse_mode='HTML')
        case "error":
            if step.lstrip(tire).isdigit():
                try:
                    int(step)
                    group_name = chats_for_ban_id_dict.get(int(step))
                    bot.send_message(chat_id,
                                     f"#error Что то пошло не так в процессе бана(разбана)! "
                                     f"Пользователь <code>{id_log}</code> "
                                     f"не был заблокирован(разблокирован) в {group_name}, Причина : {e}",
                                     parse_mode='HTML')
                except ValueError as e:
                    print(e)
            else:
                if step == "send":
                    bot.send_message(chat_id,
                                     f"#error Ошибка при отправке пользовательского "
                                     f"сообщения! Введенный текст <code>{message.text}</code>", parse_mode='HTML')
                elif step == "pub":
                    bot.send_message(chat_id,
                                     f"#error Ошибка публикации: данный пост уже опубликован!"
                                     f" <code>{message.reply_to_message.id}</code>", parse_mode='HTML')
                elif step == "database":
                    bot.send_message(chat_id,
                                     f"#error Ошибка при работе с базой данных! Исключение: {ex}\n@dannileb",
                                     parse_mode='HTML')
                elif step == "kick":
                    bot.send_message(chat_id,
                                     f"#error Ошибка отправке сообщения кикнутому скамеру "
                                     f"<code>{message.new_chat_members[0].id}</code>;"
                                     f"<code>{message.new_chat_members[0].username}</code>! Исключение: {ex}",
                                     parse_mode='HTML')
                else:
                    bot.send_message(chat_id, f"#error Пользователь <code>{message.from_user.username}</code> ;"
                                              f" <code>{message.from_user.id}</code>"
                                              f" ошибка ввода {step} "
                                              f" <code>{message.text}</code> Ислючение: {ex}", parse_mode='HTML')
        case "ban":
            if step != "":
                group_name = chats_for_ban_id_dict.get(int(step))
                bot.send_message(chat_id, f"#ban Пользователь  <code>{id_log}</code> был забанен {group_name}",
                                 parse_mode='HTML')
        case "unban":
            if step != "":
                group_name = chats_for_ban_id_dict.get(int(step))
                bot.send_message(chat_id, f"#ban Пользователь  <code>{id_log}</code> был разбанен {group_name}",
                                 parse_mode='HTML')
        case "com":
            bot.send_message(chat_id, f"#com Пользователь <code>{message.from_user.username}</code> ;"
                                      f" <code>{message.from_user.id}</code>"
                                      f" использует команду {step}  "
                                      f"<code>{message.text}</code> ", parse_mode='HTML')
        case "pub":
            bot.send_message(chat_id, f"#pub Пользователь <code>{message.from_user.username}</code> ;"
                                      f" <code>{message.from_user.id}</code>"
                                      f" опубликовал пост от сообщения №"
                                      f' <code>{message.reply_to_message.id}</code>',
                             parse_mode='HTML')
        case "kick":
            bot.send_message(chat_id, f"#kick Скамеру <code>{message.from_user.username}</code> ;"
                                      f" <code>{message.from_user.id}</code>"
                                      f" было запрещено писать сообщение в группе {step}.", parse_mode='HTML')


if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
