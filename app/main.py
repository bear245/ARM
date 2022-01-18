#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telegram, logging, logging.config, time, random, sys, os
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from modules import database as db
from modules.log_config import LOGGING_DICT

# append path to necessary modules (database.py)
sys.path.append('..\\modules')

# Enable logging to the console and into the filelog.log
logging.config.dictConfig(LOGGING_DICT)
logger = logging.getLogger('double_logger')

# Constants
CHAT_ID = int(os.getenv('CHAT_TEST_ID'))
BOT_TOKEN = os.getenv('API_TESTBOT_TOKEN')
# Define Telegram Limits
LOW_SLEEP_LIMIT = 1.0  # seconds
HIGH_SLEEP_LIMIT = 2.0  # seconds
MESSAGE_SIZE_LIMIT = 10000  # bytes
MESSAGE_FREQUENCY_LIMIT = 20  # items (20 default)
MESSAGE_TIME_LIMIT = 60  # seconds (60 default)
# Global variables for measure msg frequency before output to the chat
START_TIME = time.time()
MSG_COUNTER = 1
TIME_DELTA = 0


def limits_decorator(function):
    """This decorator serves to overcome the telegram limits of bot response."""

    def internal_wrapper(*args, **kwargs):
        update = args[0]
        correct_chat = False
        # Try to define actual chat_id and compare it with granted ID
        try:
            correct_chat = update.message.chat_id == CHAT_ID
        except AttributeError:
            # If Error occured try to read kwarg element and evaluate it
            query = kwargs.get('query')
            correct_chat = query.message.chat_id == CHAT_ID
        finally:
            # If this is granted chat try to output message
            if correct_chat:
                while True:
                    # If each limit isn't overloaded send a message to the chat
                    if telegram_check_time_count_limits():
                        function(*args, **kwargs)
                        break
                    else:
                        time.sleep(1)

    return internal_wrapper


@limits_decorator
def send_message_to_chat(update, context, msg, msg_type=0, rm=None, query=None):
    """
    Decorated function for generating Bot responses into the chat
    :params update, context: get from Telegram module API
    :param msg: a text message for output
    :param msg_type: available 3 types of messages (0-just output, 1 with reply_markup, 2-response to query)
    :param rm: reply_markup from the previous message
    :param query: on a response for the query
    :return:
    """
    if msg_type == 0:
        context.bot.sendMessage(chat_id=update.message.chat_id,
                                text=msg,
                                parse_mode=telegram.ParseMode.HTML,
                                disable_notification=True)
    elif msg_type == 1:
        context.bot.sendMessage(chat_id=update.message.chat_id,
                                text=msg,
                                parse_mode=telegram.ParseMode.HTML,
                                reply_markup=rm)
    elif msg_type == 2:
        context.bot.sendMessage(chat_id=query.message.chat_id,
                                text=msg)


def telegram_output_wlimits(answer, key=0):
    """
    Perform combined T.message as tlg_list for overcome T.limits on msg size
    :param answer:response from DB
    :param key: indicate necessity of checking nextdate conditions =0 or 1
    :return: List of combined (increased to T.size limit) messages for further output
    """
    tlg_list = []
    tlg_message = ''
    if key == 0:
        # Combine each message in answer into entire message, if possible or split on few increased msg
        logger.info("Telegram_Output_wLimits key == 0")
        for x in answer:
            if utf8len(perform_chat_message(tlg_message, x)) < MESSAGE_SIZE_LIMIT:
                tlg_message = perform_chat_message(tlg_message, x)
            else:
                tlg_list.append(tlg_message)
                tlg_message = ""
        if tlg_message:
            tlg_list.append(tlg_message)
    else:
        # Evaluate all msg in answer to nextdate condition and combine to entire message only satisfied records
        logger.info("Telegram_Output_wLimits key == 1")
        my_expression = [x for x in answer if abs((db.Calc_Less_2Months_Date() - x[3]).days) < 60]
        for x in my_expression:
            if utf8len(perform_chat_message(tlg_message, x)) < MESSAGE_SIZE_LIMIT:
                tlg_message = perform_chat_message(tlg_message, x)
            else:
                tlg_list.append(tlg_message)
                tlg_message = ""
        if tlg_message:
            tlg_list.append(tlg_message)
    return tlg_list


def telegram_check_time_count_limits():
    """
    Function evaluates the actual state of Bot messaging corresponding to Telegram Limits constants
    Output a logging information
    :return: Boolean permission for next output
    """
    global MSG_COUNTER
    global START_TIME
    global TIME_DELTA
    # Calculate TIME_DELTA between previous and next messages
    end = time.time()
    TIME_DELTA = end - START_TIME
    logger.info("Timedelta = {}, Counter = {}".format(TIME_DELTA, MSG_COUNTER))
    # Count outputted messages
    if MSG_COUNTER < MESSAGE_FREQUENCY_LIMIT:
        MSG_COUNTER += 1
        logger.info("Successfull output 1")
        return True
    else:
        if TIME_DELTA > MESSAGE_TIME_LIMIT:
            START_TIME = time.time()
            MSG_COUNTER = 1
            logger.info("Successfull output 2")
            return True
        else:
            logger.info("Out of message limits")
            time.sleep(1)
            return False


def perform_chat_message(message, x):
    """
    Perform a message formatting and collecting for overcome T. flooding limit
    :param message: STR collect few messages into one
    :param x: current response from DB
    :return: enhanced message
    """
    message += "\nid: {: <5} \nmodel: {: <35} \ns/n: {: <40} \nduedate: {} \ncertificate: {: <20}".format(
        x[0], x[1], x[2], x[3], x[4])
    message += "\n-------------------------------------------------------"
    return message


# Evaluate the length of message before output into the chat
utf8len = lambda s: len(s.encode('utf-8'))


def start(update, context):
    """
    Defines a callback for /start command
    :param update, context: get from Telegram module API
    :return: None
    """
    # Get and log user data
    user = update.message.from_user
    logger.info("Chat_id: " + str(update.message.chat_id))
    logger.info("User_id: %s, first_name: %s, last_name: %s, language: %s, is_bot: %s.",
                user.id, user.first_name, user.last_name, user.language_code, user.is_bot)
    # Output Bot's welcome message
    msg = "Welcome to <b>Radics M&TE databot</b>, developed by <b>EQ&C</b> department."
    send_message_to_chat(update, context, msg)
    msg = """The following commands are available: 
/status - display all M&TE with the selected <u>status</u>; 
/loc - display a <u>location</u> of M&TE for selected category;
/manual - display <u>User Manual</u> for selected M&TE"""
    send_message_to_chat(update, context, msg)


def status(update, context):
    """
    Perform a keyboard with callback_data as a result of /status command
    :param update, context: get from Telegram module API
    :return: None
    """
    button = [
        [InlineKeyboardButton("Calibrated", callback_data="calibrated"),
         InlineKeyboardButton("Less than 2 months", callback_data="less than 2 months")],
        [InlineKeyboardButton("Out of Calibration", callback_data="out of calibration"),
         InlineKeyboardButton("In Storage", callback_data="in storage")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    # Wait for user interaction and log his activity
    user = update.message.from_user
    logger.info("User call STATUS -> %s (%s)", user.id, user.first_name)
    reply_markup = InlineKeyboardMarkup(button)
    # Display a message near to the button menu
    msg = "Select an available query to the MTE database: "
    send_message_to_chat(update, context, msg, msg_type=1, rm=reply_markup)


def location(update, context):
    """
    Perform a keyboard with callback_data as result of /loc command
    :param update, context: get from Telegram module API
    :return: None
    """
    button = [
        [InlineKeyboardButton("Calibrators", callback_data="calys"),
         InlineKeyboardButton("Multimeters", callback_data="fluke"),
         InlineKeyboardButton("Calipers", callback_data="caliper")],
        [InlineKeyboardButton("Power Supplies", callback_data="aps"),
         InlineKeyboardButton("Signal Generators", callback_data="siglent")],
        [InlineKeyboardButton("Resistance Boxes", callback_data="p4831"),
         InlineKeyboardButton("Thermohygrometers", callback_data="tfa")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    # Wait for user interaction and log his activity
    user = update.message.from_user
    logger.info("Call LOCATION -> %s (%s)", user.id, user.first_name)
    reply_markup = InlineKeyboardMarkup(button)
    # Display a message near to button menu
    msg = "Choose M&TE for showing its actual location: "
    send_message_to_chat(update, context, msg, msg_type=1, rm=reply_markup)


def manual(update, context):
    """
    Perform a keyboard with callback_data as a result of /manual command
    :param update, context: get from Telegram module API
    :return: None
    """
    button = [
        [InlineKeyboardButton("Calys-75", callback_data="manual-calys"),
         InlineKeyboardButton("Fluke-289", callback_data="manual-fluke"),
         InlineKeyboardButton("Caliper", callback_data="manual-caliper")],
        [InlineKeyboardButton("APS-9501", callback_data="manual-aps"),
         InlineKeyboardButton("HMP4040", callback_data="manual-hameg"),
         InlineKeyboardButton("SDG1010", callback_data="manual-siglent")],
        [InlineKeyboardButton("Resistance Box", callback_data="manual-p4831"),
         InlineKeyboardButton("TFA-30.3045.IT", callback_data="manual-tfa")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    # Wait for user interaction and log his activity
    user = update.message.from_user
    logger.info("User call MANUAL -> %s (%s)", user.id, user.first_name)
    reply_markup = InlineKeyboardMarkup(button)
    msg = "Choose M&TE for showing its manual: "
    send_message_to_chat(update, context, msg, msg_type=1, rm=reply_markup)


def Menu_button_handler(update: Update, context: CallbackContext):
    """
    Perform processing all queries from a user based on callback_data
    :param update, context: get from Telegram module API
    :return:
    """
    query = update.callback_query
    query.answer()
    # log user activity and clear last chat message (delete buttons for preventing another interaction)
    logger.info("User choose %s.", query.data)
    context.bot.deleteMessage(chat_id=query.message.chat_id, message_id=query.message.message_id)

    # Processing the user choice = CALIBRATED button
    if query.data == 'calibrated':
        with db.open_database() as cur:
            answer = db.Get_mte_status(cur, status='1')
        total = "Total {} positions of <{}> items.".format(len(answer), query.data)
        # combine DB answer into one message, if possible
        tlg_list = telegram_output_wlimits(answer=answer)
        for msg in tlg_list:
            send_message_to_chat(update, context, msg, msg_type=2, query=query)
        # Send the amount of items and total size of message
        msg_size = "".join(tlg_list)
        send_message_to_chat(update, context, total, msg_type=2, query=query)
        msg_text = 'Total: ' + str(utf8len(msg_size)) + ' bytes'
        send_message_to_chat(update, context, msg_text, msg_type=2, query=query)

    # Processing the user choice = OUT OF CALIBRATION button
    elif query.data == 'out of calibration':
        # Define amount of positions both OOC and In_Storage items and perform the first part of message with OOC items
        with db.open_database() as cur:
            answer = db.Get_mte_status(cur, status='2')  # M&TE status in_storage
            items_in_storage = len(answer)
            answer = db.Get_mte_status(cur, status='0')  # M&TE status OOC
            items_ooc = len(answer)
        total_records = items_in_storage + items_ooc
        total_msg = "Total {} positions of <{}> items.".format(total_records, query.data)
        # combine DB answer into one message, if possible
        tlg_list = telegram_output_wlimits(answer=answer)
        for msg in tlg_list:
            send_message_to_chat(update, context, msg, msg_type=2, query=query)
        msg_size1 = "".join(tlg_list)
        # Perform the second part of message with In_Storage items
        with db.open_database() as cur:
            answer = db.Get_mte_status(cur, status='2')  # M&TE status InStorage is also OOC
        # combine DB answer into one message, if possible
        tlg_list = telegram_output_wlimits(answer=answer)
        for msg in tlg_list:
            send_message_to_chat(update, context, msg, msg_type=2, query=query)
        # Send the amount of items and total size of message
        msg_size2 = "".join(tlg_list)
        send_message_to_chat(update, context, total_msg, msg_type=2, query=query)
        msg_text = 'Total: ' + str(utf8len(msg_size1 + msg_size2)) + ' bytes'
        send_message_to_chat(update, context, msg_text, msg_type=2, query=query)

    # Processing the user choice = In_Storage button
    elif query.data == 'in storage':
        with db.open_database() as cur:
            answer = db.Get_mte_status(cur, status='2')
        # Perform the total message
        total = "Total {} positions of <{}> items.".format(len(answer), query.data)
        # combine DB answer into one message, if possible
        tlg_list = telegram_output_wlimits(answer=answer)
        for msg in tlg_list:
            send_message_to_chat(update, context, msg, msg_type=2, query=query)
        # Send the amount of items and total size of message
        msg_size = "".join(tlg_list)
        send_message_to_chat(update, context, total, msg_type=2, query=query)
        msg_text = 'Total: ' + str(utf8len(msg_size)) + ' bytes'
        send_message_to_chat(update, context, msg_text, msg_type=2, query=query)

    # Processing the user choice = Less 2 Months button
    elif query.data == 'less than 2 months':
        with db.open_database() as cur:
            answer = db.Get_mte_status(cur, status='1')
        # combine DB answer into one message, if possible
        tlg_list = telegram_output_wlimits(answer=answer, key=1)
        tlg_str = " ".join(tlg_list)
        total = "Total {} positions of <{}> items.".format(tlg_str.count('id:'), query.data)
        for msg in tlg_list:
            send_message_to_chat(update, context, msg, msg_type=2, query=query)
        # Send the amount of items and total size of message
        msg_size = "".join(tlg_list)
        send_message_to_chat(update, context, total, msg_type=2, query=query)
        msg_text = 'Total: ' + str(utf8len(msg_size)) + ' bytes'
        send_message_to_chat(update, context, msg_text, msg_type=2, query=query)

    # Processing the user choice = CANCEL button -> Don't do anything
    elif query.data == 'cancel':
        pass
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = CALIBRATORS button, output result message with some delay
    elif query.data == 'calys':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="Calys")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = MULTIMETERS button, output result message with some delay
    elif query.data == 'fluke':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="289")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = CALIPERS button, output result message with some delay
    elif query.data == 'caliper':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="500/100")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = POWER SUPPLIES button, output result message with some delay
    elif query.data == 'aps':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="APS")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="HMP")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = GENERATORS button, output result message with some delay
    elif query.data == 'siglent':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="SDG1010")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = RESISTANCE BOX button, output result message with some delay
    elif query.data == 'p4831':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="P4831")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = THERMOHYGROMETERS button, output result message with some delay
    elif query.data == 'tfa':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="3045")
        for x in answer:
            context.bot.sendMessage(chat_id=query.message.chat_id,
                                    text="id:{} model:{}, s/n:{}, location:{}".format(x[0], x[1], x[2], x[3]))
            time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-calys':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="Calys")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="AOIP SAS Calys-75 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-fluke':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="289")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="Fluke-289 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-caliper':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="500/100")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="ЩЦ-III-500/100 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-aps':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="APS")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="APS-9501 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-hameg':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="HMP")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="HMP-4040 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-siglent':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="SDG1010")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="SDG-1010 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-p4831':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="P4831")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="P-4831 User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))

    # Processing the user choice = M&TE manual buttons, output result message with some delay
    elif query.data == 'manual-tfa':
        with db.open_database() as cur:
            answer = db.Get_mte_type(cur, model="3045")
        x = answer[0]
        context.bot.sendMessage(chat_id=query.message.chat_id, text="TFA 30.3045.IT User manual: {}".format(x[4]))
        time.sleep(random.uniform(LOW_SLEEP_LIMIT, HIGH_SLEEP_LIMIT))


def run():
    # allows to register handler -> command, text etc
    updater = Updater(token=BOT_TOKEN)

    # create handlers
    start_handler = CommandHandler("start", start)
    status_handler = CommandHandler("status", status)
    location_handler = CommandHandler("loc", location)
    manual_handler = CommandHandler("manual", manual)
    button_handler = CallbackQueryHandler(Menu_button_handler)

    # add command handler to dispatcher
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(status_handler)
    updater.dispatcher.add_handler(location_handler)
    updater.dispatcher.add_handler(manual_handler)
    updater.dispatcher.add_handler(button_handler)

    # Start the Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    updater.idle()


if __name__ == '__main__':
    run()
