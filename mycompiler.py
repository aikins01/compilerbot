
# -*- coding: utf-8 -*-

import configparser
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import InlineQueryResultArticle, ChatAction, InputTextMessageContent
from uuid import uuid4
import time
import logging
import sys
import os
import pprint

from io import StringIO
import contextlib


@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


TOKEN = os.environ["TOKEN"]

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher


def start(update, context):
    context.bot.sendChatAction(chat_id=update.effective_chat.id,
                               action=ChatAction.TYPING)
    context.bot.sendMessage(chat_id=update.effective_chat.id, text="""Type your code...\n
Note that python language is case sensitive!\n
Try these commands:
    print('Hello World')
    x = 2
    print(x)
    for i in range(10): print(i)
or any desired code!""")


def execute(update, context):

    try:
        code = update.message.text
        inline = False
    except AttributeError:
        # Using inline
        code = update
        inline = True

    flag = True
    with stdoutIO() as screen:
        try:
            exec(code)
        except Exception as exception:
            flag = False
            error = str(exception)
            print(error)

    result = screen.getvalue()
    if ((result.find('name') != -1) and (result.find('is not defined') != -1) and result != result.lower()):
        result += '\n' + '-May help you: Python language is case sensitive!'
    if flag:
        output = '>>> Result\n'
    else:
        output = '>>> Error\n'
    if not inline:
        context.bot.sendChatAction(chat_id=update.effective_chat.id,
                                   action=ChatAction.TYPING)
    output += '\n' + result

    if not inline:
        context.bot.sendMessage(chat_id=update.effective_chat.id,
                                text=output)
        return False

    if inline:
        return output


def inlinequery(update, context):
    query = update.inline_query.query
    o = execute(query, context)
    results = list()

    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title=query,
                                            description=o,
                                            input_message_content=InputTextMessageContent(
                                                '*{0}*\n\n{1}'.format(query, o))))

    context.bot.answerInlineQuery(context.inline_query.id,
                                  results=results, cache_time=10)


start_handler = CommandHandler('start', start)
execute_handler = MessageHandler(Filters.text, execute)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(execute_handler)
dispatcher.add_handler(InlineQueryHandler(inlinequery))

# dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
