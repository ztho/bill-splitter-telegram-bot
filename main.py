import telebot 
from telebot import types
import TOKEN
import ClassHandlers as CH
import infoStore as IS
from flask import Flask, request
import os
import time
import logging 

# Basic Settings
logging.basicConfig(filename = "log.txt")
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

# Initialize bot and server
bot = telebot.TeleBot(TOKEN.token, threaded = False)
server = Flask(__name__) 

#Methods

# Method to handle adding name into nameList
def addNameToArray(msg):
    name = msg.text
    chat_id = msg.chat.id
    
    if(msg.text == "/quit"):
        quit_bot(msg)
        return

    if(msg.text == "/deletename"):
        if(len(IS.user_info[chat_id].nameList) != 0):
            nextMsg = bot.send_message(chat_id, 
                                        "Choose a name to delete, or use /doneaddingnames to cancel deleting", 
                                        reply_markup = generateMarkup(chat_id, False, False, False))
            bot.register_next_step_handler(nextMsg, deleteName)
        else:
            bot.send_message(msg.chat.id, "There are no names in the list, use /add to add names")            

    elif(msg.text != "/doneaddingnames"):
        IS.user_info[chat_id].add_name_to_nameList(name)
        IS.user_info[chat_id].assignIndex()     
        nextMsg = bot.send_message(chat_id, 
                                    (name + " is added to the list. Type the next name to add, or use:\n\n" 
                                    + "/doneaddingnames to proceed\n"
                                    + "/deletename to remove people in the billing list\n"
                                    + "/quit to quit the bot"))
        bot.register_next_step_handler(nextMsg, addNameToArray)    
    else:
        IS.user_info[chat_id].assignIndex()
        guideMsg = ("All names added! Next, use /addorders to begin adding order items to the order list. Or use:\n\n" 
                    + "/add to continue adding names\n" 
                    + "/viewpeople to see people in the billing list\n" 
                    + "/deletename to remove people from the billing list\n"
                    + "/quit to exit the bot")
        nextMsg = bot.send_message(msg.chat.id, guideMsg)

#Method to delete name from list
def deleteName(msg):
    chat_id = msg.chat.id 
    name = msg.text

    if (name == "/doneaddingnames"):
        addNameToArray(msg)
        return 
    
    isRemoved = IS.user_info[chat_id].delete_name_from_list(msg.text)
    if(isRemoved):
        nextMsg = bot.send_message(chat_id, 
                                    name + (" is removed. Please use:\n\n"
                                    + "/doneaddingnames to continue\n"
                                    + "/deletename to remove another name\n"
                                    + "/add to add another name\n" 
                                    + "/quit to quit the bot"))
    else:
        nextMsg = bot.send_message(chat_id, 
                                    "Name is not found, please use buttons provided! Else, use /doneaddingnames to proceed",
                                    reply_markup = generateMarkup(chat_id, False, False, False))
        bot.register_next_step_handler(nextMsg, deleteName)

def createOrder(msg):
    if(msg.text != "/doneaddingorders"):
        newOrder = CH.Order(msg.text)
        nextMsg = bot.send_message(msg.chat.id, "Enter price of " + newOrder.orderName + ", or use /rollback to re-enter the order name") 
        bot.register_next_step_handler(nextMsg, setPrice, newOrder)
    else:
        #On completing all orders, move to adding GST
        nextMsg = bot.send_message(msg.chat.id, "Specify GST percentage amount (0 if not applicable)")
        bot.register_next_step_handler(nextMsg, addGST)     

def setPrice(msg, newOrder):
    chat_id = msg.chat.id
    if(msg.text == "/rollback"):
        nextMsg = bot.send_message(msg.chat.id,"Re-enter the name of the dish, or use /doneaddingorders to finish adding orders")
        bot.register_next_step_handler(nextMsg, createOrder)
    else: 
        try:
            price = float(msg.text)
            newOrder.setPrice(price)
            guideMsg = (newOrder.orderName + " ($" + str("%0.2f" % newOrder.price) +") " + "is added to the order list. Please" + 
                        " select the person who ordered this dish. Select \"Assign Among\" if this dish is split among several people."
                        + " Or use /rollback to re-enter price")
            nextMsg = bot.send_message(msg.chat.id, guideMsg)
            assignOrder(nextMsg, newOrder, IS.user_info[chat_id].nameList)
        except ValueError: 
            nextMsg = bot.send_message(msg.chat.id, "Please enter a valid number!")
            bot.register_next_step_handler(nextMsg, setPrice, newOrder)

def assignOrder(msg, newOrder, nameList):
    markup = generateMarkup(msg.chat.id, False, True, False)
    nextMsg = bot.send_message(msg.chat.id,"Assign Order", reply_markup = markup)
    bot.register_next_step_handler(nextMsg, handleAssignToPerson, newOrder)

def handleAssignToPerson(msg, order, isACallBack = False):
    chat_id = msg.chat.id
    if (msg.text == "/rollback"):
        nextMsg = bot.send_message(msg.chat.id, "Re-enter the price of " + order.orderName)
        bot.register_next_step_handler(nextMsg, setPrice, order)
        return 
    if(msg.text == "Split Among"):
        #If user selects "Split Among, no need for Split Among again, but need split for all"
        markup = generateMarkup(chat_id, True, False, False)
        nextMsg = bot.send_message(msg.chat.id, "Choose People To Split With", reply_markup = markup)
        bot.register_next_step_handler(nextMsg, handleSplitAssign, order)
    else:
        index = IS.user_info[chat_id].findIndex(msg.text)
        if(index == -1): 
            #If user enters a name not in namelist
            if (isACallBack == True):
                nextMsg = bot.send_message(msg.chat.id, "Name is not identified. Please use buttons provided!", reply_markup = generateMarkup(chat_id, True, True, False))
                bot.register_next_step_handler(nextMsg, handleAssignToPerson, order)
            else:
                nextMsg = bot.send_message(msg.chat.id, "Name is not identified. Please use buttons provided!", reply_markup = generateMarkup(chat_id, False, True, False))
                bot.register_next_step_handler(nextMsg, handleAssignToPerson, order, True)
        else: 
            assignToPerson(index, order, chat_id)
            guideMsg = (order.orderName + " is assigned to " + msg.text 
            + ". Type the name of the next item, or type /doneaddingorders if there are no more orders to add.")
            nextMsg = bot.send_message(msg.chat.id, guideMsg)
            bot.register_next_step_handler(nextMsg, createOrder)

# Assign an order to person
def assignToPerson(index, order, chat_id):
    IS.user_info[chat_id].assign_order_to_person(index, order)

#Method handles logic from users. Assign done in ClassHandlers
def handleSplitAssign(msg, order, isDone = False):
    chat_id = msg.chat.id
    index = IS.user_info[chat_id].findIndex(msg.text)
    if(index != -1 and msg.text != "Done" and msg.text != "Split Among All"): 
        IS.user_info[chat_id].add_to_splitWithIndexes(msg.text)
        markup = generateMarkup(chat_id, False, False, True)
        guideMsg = (order.orderName + " has been split with " + msg.text 
                    + ". Click another person to split this order with, or click \"Done\" if done splitting.")
        nextMsg = bot.send_message(msg.chat.id, guideMsg, reply_markup = markup)
        bot.register_next_step_handler(nextMsg, handleSplitAssign, order, True)

    elif (msg.text == "Split Among All"):
        if(not isDone):
            IS.user_info[chat_id].add_all_to_splitWithIndexes() 
            IS.user_info[chat_id].split_price_computation(order)

            guideMsg = (order.orderName + " is split among everyone. Please type the name of your next order," 
                        +" or /doneaddingorders if there are no more orders to add")
            nextMsg = bot.send_message(msg.chat.id, guideMsg)
            bot.register_next_step_handler(nextMsg, createOrder)
        else:
            guideMsg = (order.orderName + " has already been split with at least 1 person. "  
                        + "Please select the remaining people to split with.")
            nextMsg = bot.send_message(msg.chat.id, guideMsg, reply_markup = generateMarkup(msg.chat.id, False, False, True))
            bot.register_next_step_handler(nextMsg, handleSplitAssign, order, True)

    elif(msg.text == "Done"):
        if(isDone):
            splitPriceComputation(order,chat_id)
            guideMsg = (order.orderName + " has been split. Please type the name of your next order," 
                        +" or /doneaddingorders if there are no more orders to add")
            nextMsg = bot.send_message(msg.chat.id, guideMsg)
            bot.register_next_step_handler(nextMsg, createOrder)
        else: 
            guideMsg = ("Order has not been assigned to anyone yet. Please assign the order to at least 1 person")
            nextMsg = bot.send_message(msg.chat.id, guideMsg , reply_markup = generateMarkup(chat_id, True, False, False))
            bot.register_next_step_handler(nextMsg, handleSplitAssign, order)
    else:
        nextMsg = bot.send_message(msg.chat.id, "Name is not identified. Please use buttons provided!", reply_markup = generateMarkup(chat_id, True, False, False))
        bot.register_next_step_handler(nextMsg, handleSplitAssign, order, isDone)

#Method handles logic from users, abstracts calculations to ClassHandlers
def splitPriceComputation(order, chat_id):
    try: 
        IS.user_info[chat_id].split_price_computation(order)

    except ZeroDivisionError: 
        nextMsg = bot.send_message(chat_id, "Order has not been assigned to anyone yet. Please assign the order to at least 1 person", reply_markup = generateMarkup(chat_id, True, False, False))
        bot.register_next_step_handler(nextMsg, handleAssignToPerson)

#Method handles logic from users, abstracts calculations to ClassHandlers
def addGST(msg):
    chat_id = msg.chat.id

    if (isinstance(float(msg.text), float)):
        IS.user_info[chat_id].add_GST(msg.text)
        nextMsg = bot.send_message(chat_id, "Please specify service charge percentage amount (0 if not applicable)")
        bot.register_next_step_handler(nextMsg, addServiceCharge)
    else: 
        nextMsg = bot.send_message(chat_id, "Please Enter Valid Number")
        bot.register_next_step_handler(nextMsg, addGST)

#Method handles logic from users, abstracts calculations to ClassHandlers
def addServiceCharge(msg):
    chat_id = msg.chat.id

    if(isinstance(float(msg.text), float)):
        IS.user_info[chat_id].add_service_charge(msg.text)
        bot.send_message(chat_id, "Here's your receipt!")
        handle_done(msg)
    else: 
        nextMsg = bot.send_message(chat_id, "Please enter valid number")
        bot.register_next_step_handler(nextMsg, addServiceCharge)

#generates markup object
def generateMarkup(chat_id, with_among_all, with_split_among, with_done):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
    try: 
        name_list = IS.user_info[chat_id].nameList
        itemBtnArray = []
        for name in name_list:
            itemBtnArray.append(types.KeyboardButton(name.getName()))

        if(with_split_among):
            itemBtnArray.append(types.KeyboardButton("Split Among"))

        if(with_among_all): 
            itemBtnArray.append(types.KeyboardButton("Split Among All"))
        
        if(with_done):
            itemBtnArray.append(types.KeyboardButton("Done"))

        for btn in itemBtnArray:
            markup.add(btn)
        return markup
    except KeyError: 
        nextMsg = bot.send_message(chat_id, "Bot not initialized, please use /start")
        quit_bot(nextMsg)

#Controllers

#Bot entry point
@bot.message_handler(commands = ['start'])
def start_msg(msg):
    #logging, create a new bill
    chat_id = msg.chat.id
    user_name = msg.from_user.first_name
    IS.user_info[chat_id] = CH.Bill()

    #log unique users
    IS.log_user(chat_id)
    
    #clear all previous bill information, set hasStart to true
    del IS.user_info[chat_id].nameList[:]
    IS.user_info[chat_id].hasStart = True
    try: 
        welcomeMsg = ("Hello " + user_name +"! Welcome to Bill Splitter! Use: \n\n"
                        + " /add to begin adding people into the billing list\n"
                        + " /info for more information on using this bot\n" 
                        + " /quit to terminate the bot")
    except:
        welcomeMsg = ("Hello there! Welcome to Bill Splitter!"
                        + " /add to begin adding people's names\n"
                        + " /info for more information on using this bot\n" 
                        + " /quit to terminate the bot")

    bot.send_message(msg.chat.id, welcomeMsg)

#Handles all adding of names
@bot.message_handler(commands = ["add"])
def add_names(msg):
    try:
        IS.user_info[msg.chat.id].hasStart = True
        guideMsg = "Type the name of the person to add to bill, or else type /doneaddingnames to begin adding the bill items"
        nextMsg = bot.send_message(msg.chat.id, guideMsg)
        bot.register_next_step_handler(nextMsg, addNameToArray)
    except KeyError:
        bot.send_message(msg.chat.id, "Please /start the bot first")

#Handles the done adding of names
@bot.message_handler(commands =["doneaddingnames"])
def done_adding_names(msg):
    try: 
        addNameToArray(msg)
    except:
        bot.send_message(msg.chat.id, "Please /start the bot first")

#Handles viewing of the people in the list
@bot.message_handler(commands = ["viewpeople"])
def view_people(msg):
    try: 
        chat_id = msg.chat.id
        localBillInfo = IS.user_info[chat_id]
        if (len(localBillInfo.nameList) == 0):
            bot.send_message(msg.chat.id, "There are no names in the list, use /add to add names")
        else: 
            output = localBillInfo.viewNameList()
            output += ("\n Please use:\n" 
                        + "/add to add more names\n" 
                        + "/deletename to remove people from the billing list\n"
                        + "/addorders to begin adding orders\n" 
                        + "/quit to exit the bot")
            bot.send_message(msg.chat.id, output, parse_mode = "HTML")
    except KeyError: 
        bot.send_message(msg.chat.id, "Please /start the bot first")

#Handles the info reply
@bot.message_handler(commands = ["info"])
def show_info(msg):
    guideMsg = ("Welcome to Bill Splitter! This bot helps you split your bill. I will do so with these steps:\n"
                + "1. I will first take in a list of names of the people you want to split the bill with.\n"
                + "2. Then, I will take in the list of orders and their prices.\n"
                + "3. Lastly, I will add any prevailing GST or service charge at your given percentage.\n"
                + "I will then return you a generated receipt of the price everyone should pay\n\n"
                + "Use /start to initialize the bot!"
    )

    bot.send_message(msg.chat.id, guideMsg)

#handles the command to start adding orders
@bot.message_handler(commands = ["addorders"])
def add_orders(msg):
    try: 
        if(len(IS.user_info[msg.chat.id].nameList) == 0):
            bot.send_message(msg.chat.id, "No names in list. Please /add people's names into list first")
        else: 
            nextMsg = bot.send_message(msg.chat.id,"Type the name of your first order")
            bot.register_next_step_handler(nextMsg, createOrder)  
    except KeyError:
        bot.send_message(msg.chat.id, "Please /start the bot first")

# handles the command to delete names 
@bot.message_handler(commands = ["deletename"])
def delete_name(msg):
    chat_id = msg.chat.id
    try: 
        if(len(IS.user_info[chat_id].nameList) != 0):
            nextMsg = bot.send_message(chat_id, 
                                        "Choose a name to delete, or use /doneaddingnames to cancel deleting", 
                                        reply_markup = generateMarkup(chat_id, False, False, False))
            bot.register_next_step_handler(nextMsg, deleteName)
        else:
            bot.send_message(chat_id, "No names in billing list to delete. Please use /add to add names into the list, or /quit to quit the bot")
    except KeyError:
        bot.send_message(chat_id,"Please /start the bot first")

#handles the final done message
@bot.message_handler(commands = ["done"])
def handle_done(msg):
    try: 
        chat_id = msg.chat.id
        output = IS.user_info[chat_id].generate_receipt()
        bot.send_message(chat_id, output, parse_mode = "HTML")
        
        #clear data after gene 
        IS.user_info[chat_id].clear_bill()
        IS.clear_user_info(chat_id)
        bot.send_message(msg.chat.id, "All Done! Please use /start to do another, or /quit to exit!")
    except: 
        bot.send_message(msg.chat.id, "No orders added yet!")

#handles quitting of bot
@bot.message_handler(commands = ["quit"])
def quit_bot(msg):
    bot.send_message(msg.chat.id, "Bot exited. Please use /start to do another bill")
    try: 
        IS.clear_user_info(msg.chat.id)
    except KeyError:
        pass

#handles all other invalid commands
@bot.message_handler(func = lambda m: True)
def invalid_reply(msg):
    bot.send_message(msg.chat.id, "Invalid Command!")

# # Webhooks
@server.route('/' + TOKEN.token, methods = ['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://bill-split-bot.onrender.com' + TOKEN.token)
    return "!", 200

def main():
    try:
        bot.polling(none_stop = True)
    
    except Exception:
        time.sleep(5)
        print("Internet Error!")

if __name__ == "__main__":
    server.run(host = "0.0.0.0", port = int(os.environ.get('PORT', 5000)))