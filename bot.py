#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from tinydb import TinyDB, Query
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import hashlib
import os
from wordcloud_fa import WordCloudFa
from stop_words import get_stop_words

EMO_HAND_UP = ['👍','👍🏻','👍🏼','👍🏽','👍🏾','👍🏿','👌','🤟','💪','Gracias','gracias']
EMO_HAND_DOWN = ['👎','👎🏻','👎🏼','👎🏽','👎🏾','👎🏿']
NUMBERS = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

LOGGER_MSG = 'Info: {} / ChatID: {} / From: {} / To: {} / MsgID: {}'
LOGGER_LK_MSG = 'Info: {} / ChatID: {} / From: {} / To: {} / MsgID: {} / Vote: {}'

TOKEN = os.environ['BOT_TOKEN']
BOT_ID = int(TOKEN.split(':')[0])

def get_ranking(rank):
    for i in range(10):
        lvl_var = os.environ['BOT_RANKING_LVL_' + str(i)]
        lvl = lvl_var.split(',')
        if ( int(lvl[0]) <= rank <= int(lvl[1]) ):
            level = lvl[2]
            level_num = i
    return level, level_num

def return_db(chat_id):
    db = TinyDB('./data/database' + str(chat_id) + '.json')
    likedMessages = db.table('LikedMessages')
    uniqueLikes = db.table('UniqueLikes')
    votedUsers = db.table('VotedUsers')
    return likedMessages, uniqueLikes, votedUsers

def return_words_db(chat_id):
    db = TinyDB('./data/database_words' + str(chat_id) + '.json')
    words = db.table('Words')
    return words

def return_noisy_users_db(chat_id):
    db = TinyDB('./data/database_noisy_users' + str(chat_id) + '.json')
    users = db.table('noisyUsers')
    return users

def manage_msg(update):
    chat_id = update.message.chat_id 
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    words = return_words_db(chat_id)
    words_list = update.message.text.split()
    words_length = len(words_list)
    for i in words_list:
        new_word = {
            'word': i 
            }
        words.insert(new_word)
    Messages = Query()
    msgsUsers = return_noisy_users_db(chat_id)
    if not msgsUsers.search(Messages.user_id == user_id):
        new_user = {
            'user_id': user_id,
            'username': username,
            'words': words_length
        }
        msgsUsers.insert(new_user)
    else:
        old_amount_words = msgsUsers.search(Messages.user_id == user_id)[0]['words']
        new_words = old_amount_words + words_length
        msgsUsers.update({'words': new_words}, Messages.user_id == user_id)
    return 

def manage_vote(update, vote_type):
    chat_id = update.message.chat_id 
    donor_id = update.message.from_user.id
    donor_username = update.message.from_user.username
    receiver_id = update.message.reply_to_message.from_user.id 
    receiver_username = update.message.reply_to_message.from_user.username
    liked_msg_id = update.message.reply_to_message.message_id
    vote_msg_id = update.message.message_id
    string = str(donor_id) + str(receiver_id) + str(liked_msg_id)
    md5_like = hashlib.md5(string.encode()).hexdigest()
    likedMessages, uniqueLikes, votedUsers = return_db(chat_id)
    if vote_type: 
        increment = +1
    else:
        increment = -1
    if receiver_id == donor_id:
        msg = LOGGER_MSG.format('SelfVote', str(chat_id), donor_username, receiver_username, str(liked_msg_id))
        logger.info(msg)
        return
    if receiver_id == BOT_ID:
        msg = LOGGER_MSG.format('Vote to the Bot', str(chat_id), donor_username, receiver_username, str(liked_msg_id))
        logger.info(msg)
        return
    Messages = Query()
    if not uniqueLikes.search(Messages.hash == md5_like):
        new_like = {
            'donor_id': donor_id,
            'receiver_id': receiver_id,
            'msg_id': liked_msg_id,
            'hash': md5_like
        }
        uniqueLikes.insert(new_like)
        if not likedMessages.search(Messages.msg_id == liked_msg_id):
            new_msg = {
                'msg_id': liked_msg_id,
                'likes': increment
            }
            likedMessages.insert(new_msg)
        else:
            old_likes = likedMessages.search(Messages.msg_id == liked_msg_id)[0]['likes']
            likes = old_likes + increment
            likedMessages.update({'likes': likes}, Messages.msg_id == liked_msg_id)
        msg = LOGGER_LK_MSG.format('Like/Dislike', str(chat_id), donor_username, receiver_username, str(liked_msg_id), str(increment))
        logger.info(msg)
        if not votedUsers.search(Messages.user_id == receiver_id):
            new_user = {
                'user_id': receiver_id,
                'username': receiver_username,
                'votes': increment
            }
            votedUsers.insert(new_user)
        else:
            old_votes = votedUsers.search(Messages.user_id == receiver_id)[0]['votes']
            level,prev_level = get_ranking(old_votes)
            votes = old_votes + increment
            level,new_level = get_ranking(votes)
            votedUsers.update({'votes': votes}, Messages.user_id == receiver_id)
            votedUsers.update({'username': receiver_username}, Messages.user_id == receiver_id)
            if prev_level < new_level:
                    response = '@' + receiver_username + ' sube de reputación ! Reputación: ' + str(votes) + ' Rango: ' + level
                    update.message.reply_text(response, reply_to_message_id=liked_msg_id, quote=True)
            if prev_level > new_level:
                    response = '@' + receiver_username + ' baja de reputación ! Reputación: ' + str(votes) + ' Rango: ' + level
                    update.message.reply_text(response, reply_to_message_id=liked_msg_id, quote=True)
    else:
        msg = LOGGER_MSG.format('Duplicate', str(chat_id), donor_username, receiver_username, str(liked_msg_id))
        logger.info(msg)
        return

def echo(update, context):
    manage_msg(update)
    if update.message.reply_to_message: 
        if any(x in update.message.text for x in EMO_HAND_UP):
            manage_vote(update, True)
        elif any(x in update.message.text for x in EMO_HAND_DOWN):
            manage_vote(update, False)
    else:
        return

def top(update, context):
    likedMessages, uniqueLikes, votedUsers = return_db(update.message.chat_id)
    users = votedUsers.all()
    users_sorted = sorted(users, key=lambda k: k['votes'], reverse=True) 
    message =   '➖➖➖➖➖➖➖➖\n' \
                '🏆{}\n' \
                'Usuario: {}\n' \
                'Reputación: {}\n' \
                'Rango: {}\n'
    whole_message = []
    whole_message.append('Top 10 Reputación:\n')
    i = 0
    for user in users_sorted[:10]:
        level,level_num = get_ranking(user['votes'])
        usermsg = message.format(NUMBERS[i], user['username'], user['votes'], level)
        whole_message.append(usermsg)
        i += 1
    update.message.reply_text(''.join(whole_message))

def topcotorras(update, context):
    msgsUsers = return_noisy_users_db(update.message.chat_id)
    msgsUsers = msgsUsers.all()
    users_sorted = sorted(msgsUsers, key=lambda k: k['words'], reverse=True) 
    message =   '➖➖➖➖➖➖➖➖\n' \
                '🏆{} - {}\n' \
                'Usuario: {}\n'
    whole_message = []
    whole_message.append('Top 5 Cotorras:\n')
    i = 0
    for user in users_sorted[:5]:
        usermsg = message.format(NUMBERS[i], user['words'], user['username'])
        whole_message.append(usermsg)
        i += 1
    update.message.reply_text(''.join(whole_message))

def toprancios(update, context):
    likedMessages, uniqueLikes, votedUsers = return_db(update.message.chat_id)
    users = votedUsers.all()
    users_sorted = sorted(users, key=lambda k: k['votes']) 
    message =   '➖➖➖➖➖➖➖➖\n' \
                '💩{}\n' \
                'Usuario: {}\n' \
                'Reputación: {}\n' 
    whole_message = []
    whole_message.append('Los 10 Top Rancios:\n')
    i = 0
    for user in users_sorted[:10]:
        usermsg = message.format(NUMBERS[i], user['username'], user['votes'])
        whole_message.append(usermsg)
        i += 1
    update.message.reply_text(''.join(whole_message))

def reputacion(update, context):
    likedMessages, uniqueLikes, votedUsers = return_db(update.message.chat_id)
    if len(context.args) == 1:
        user_name = context.args[0]
        if '@' in user_name:
            user_name = user_name.split('@')[1]
        Users = Query()
        if votedUsers.search(Users.username == user_name):
            update.message.reply_text('La reputación de ' + user_name + ' es ' + str(votedUsers.search(Users.username == user_name)[0]['votes']))
        else:
            update.message.reply_text('Nadie ha votado nunca a ' + user_name + ' ... por algo será 🤣')

def miposicion(update, context):
    likedMessages, uniqueLikes, votedUsers = return_db(update.message.chat_id)
    user_id = update.message.from_user.id
    users = votedUsers.all()
    users_sorted = sorted(users, key=lambda k: k['votes'], reverse=True)
    found = False
    for pos in range(0,len(users_sorted)):
        if user_id == users_sorted[pos]['user_id']:
            found = True
            votes = users_sorted[pos]['votes']
            break
    if found:
        pos += 1
        total = len(users_sorted)
        update.message.reply_text('Tu posición es ' + str(pos) + ' de ' + str(total) + '. Reputación: ' + str(votes))
    else:
        update.message.reply_text('Ni estás en la lista de votados 🤣')

def posicion(update, context):
    likedMessages, uniqueLikes, votedUsers = return_db(update.message.chat_id)
    if len(context.args) == 1:
        user_name = context.args[0]
        if '@' in user_name:
            user_name = user_name.split('@')[1]
        users = votedUsers.all()
        users_sorted = sorted(users, key=lambda k: k['votes'], reverse=True)
        found = False
        for pos in range(0,len(users_sorted)):
            if user_name == users_sorted[pos]['username']:
                found = True
                votes = users_sorted[pos]['votes']
                break
        if found:
            pos += 1
            total = len(users_sorted)
            update.message.reply_text('La posición de ' + user_name + ' es ' + str(pos) + ' de ' + str(total) + '. Reputación: ' + str(votes))
        else:
            update.message.reply_text(user_name + ' no está en la lista de votados 🤣')

def mejores(update, context):
    likedMessages, uniqueLikes, votedUsers = return_db(update.message.chat_id)
    messages = likedMessages.all()
    messages_sorted = sorted(messages, key=lambda k: k['likes'], reverse=True) 
    update.message.reply_text('Aquí va el TOP3 de mensajes mejor valorados:')
    for message in messages_sorted[:3]:
        update.message.reply_text('⬆️', reply_to_message_id=message['msg_id'])

def ayuda(update, context):
    message =   'Hola, soy el bot de Reputación !\n' \
                '\n' \
                'Tienes los siguientes comandos disponibles ...\n' \
                '    /top (Top 10 usuarios por grado de Reputación)\n' \
                '    /toprancios (Pues eso 🤣) \n' \
                '    /reputacion @usuario (ver la reputación del usuario en concreto)\n' \
                '    /mejores (recuperar el TOP 3 de comentarios más valorados)\n' \
                '    /miposicion (sacar tu propia posición en el la tabla) \n' \
                '    /posicion @usuario (sacar la posición de un usuario en el la tabla) \n' \
                '    /resumen (nube de palabras del día) \n' \
                '    /topcotorras (lista de usuarios más habladores) \n' \
                '\n' \
                'Para votar, simplemente puedes responder a un usario y poner el 👍 o 👎 (con o sin texto adicional)\n'
    update.message.reply_text(message)

def resumen(update, context):
    stop_words_sp = get_stop_words('es')
    wordsTable = return_words_db(update.message.chat_id)
    words = wordsTable.all()
    word_list = list(map(lambda x: x['word'], words))
    string = ' '.join(word_list)
    #clean_string = re.sub(r'[^\w\s]','',string)
    wordcloud = WordCloudFa(stopwords=stop_words_sp, width=800, height=400, include_numbers=False)
    wc = wordcloud.generate(string)
    image = wc.to_image()
    image.save('/tmp/cloud.png')
    update.message.reply_photo(photo=open('/tmp/cloud.png', 'rb'))

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("ayuda", ayuda))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(CommandHandler("topcotorras", topcotorras))
    dp.add_handler(CommandHandler("toprancios", toprancios))
    dp.add_handler(CommandHandler("reputacion", reputacion))
    dp.add_handler(CommandHandler("mejores", mejores))
    dp.add_handler(CommandHandler("miposicion", miposicion))
    dp.add_handler(CommandHandler("posicion", posicion))
    dp.add_handler(CommandHandler("resumen", resumen))
    dp.add_handler(CommandHandler("quitar", quitar))
    dp.add_handler(CommandHandler("purge", purge))
    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
