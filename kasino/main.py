import telebot
import sqlite3
import time

from telebot import TeleBot, types


from config import TOKEN

from telebot import TeleBot

import random 



bot = TeleBot(TOKEN) 


virtual_currency = "🪙" 

initial_balance = 100 

users = {} 

def get_balance(user_id):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else initial_balance

def add_balance(user_id, amount):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, initial_balance + amount))
    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@bot.message_handler(commands=['start']) 
def start(message): 
    user_id = message.from_user.id  
    user_name = message.from_user.first_name 
    balance = get_balance(user_id) 
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Меню"))
    
    bot.send_message(message.chat.id, f"Привет, {user_name}! Залетай в НеКазик и лутай НеCash, Но монеты 🪙, выбери 🟥 или ⬛️. Большие выйгрыши, высокие кофиценты!!", reply_markup=markup) 

@bot.message_handler(content_types=['text'])
def func(message):
    user_id = message.from_user.id
    
    if message.text == "Привет":
        bot.send_message(message.chat.id, "Привеет..)")
        
    elif message.text == "Профиль 👤":
        balance = get_balance(user_id)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Вернуться в главное меню")
        markup.add(back)
        
        bot.send_message(message.chat.id, 
                         f"👤 Твой профиль:\n💰 Баланс: {balance} {virtual_currency}", reply_markup=markup)
        
    elif message.text == "Играть ☘️":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        b1 = types.KeyboardButton("НеРулетка")
        back = types.KeyboardButton("Вернуться в главное меню")
        markup.add(b1, back) 
        
        bot.send_message(message.chat.id, "Выберите игру из списка ниже:", reply_markup=markup) 


    elif(message.text == "НеРулетка"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        roulette(message)


    elif message.text == "Вернуться в главное меню":
        menu(message)

    elif(message.text == "Меню"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        menu(message)

    elif message.text == "Помощь  📞":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Вернуться в главное меню"))
        
        bot.send_message(message.chat.id, "Помощи пока нет, но вы держитесь!", reply_markup=markup)
        


@bot.message_handler(commands=['menu'])
def menu(message):
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn1 = types.KeyboardButton("Профиль 👤")
    btn2 = types.KeyboardButton("Играть ☘️")
    btn3 = types.KeyboardButton("Помощь  📞")
    
    markup.add(btn1, btn2) 
    markup.add(btn3)       
    
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)


@bot.message_handler(commands=['roulette']) 
def roulette(message): 
  user_id = message.from_user.id  
  balance = get_balance(user_id) 

  if balance == 0: 
    bot.send_message(message.chat.id, "У вас нет средств для игры.") 
    return 

  bot.send_message(message.chat.id, f"Введите сумму ставки не болие чем: {balance} {virtual_currency}") 
  bot.register_next_step_handler(message, handle_bet, user_id, balance) 

def handle_bet(message, user_id, balance):
    try:
        bet = int(message.text)
        if bet <= 0 or bet > balance:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка! Введите корректную сумму.")
        return

    
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Красное', 'Черное', 'Зеленое (0)')
    
    msg = bot.send_message(message.chat.id, "На что ставим?", reply_markup=markup)
    
    bot.register_next_step_handler(msg, process_choice, user_id, bet)  

def process_choice(message, user_id, bet):
    choice = message.text
    number = random.randint(0, 36) 
    
    # Определяем цвет выпавшего числа
    if number == 0:
        win_color = "Зеленое (0)"
    elif number % 2 == 0:
        win_color = "Черное"
    else:
        win_color = "Красное"

    bot.send_message(message.chat.id, f"🎰 Выпало: {number} ({win_color})")

    # --- ЛОГИКА ВЫИГРЫША ---
    winnings = 0
    if choice == win_color:
        if choice == "Зеленое (0)":
            winnings = bet * 30  # Джекпот за 0
        else:
            winnings = bet * 1.4   # Удвоение за цвет
    
    # Обновляем баланс
    change = winnings - bet
    add_balance(user_id, change)

    if winnings > 0:
        bot.send_message(message.chat.id, f"🎉 Победили! +{winnings} {virtual_currency}")
        menu(message)
    else:
        bot.send_message(message.chat.id, f"💀 Проигрыш. -{bet} {virtual_currency}")
        menu(message)
    
    # Запуск бота 
if __name__ == "__main__":
    bot.infinity_polling()