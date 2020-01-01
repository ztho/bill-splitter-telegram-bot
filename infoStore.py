user_info = {}

def clear_user_info(chat_id):
    try: 
        del user_info[chat_id]
    except KeyError:
        pass

def log_user(chat_id):
    file = open("userlog.txt", "a+")
    file.write(str(chat_id) + "\n")
    file.close() 