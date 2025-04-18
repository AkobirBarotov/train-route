import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

# .env faylidan tokenni o'qish
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# JSON faylni o'qish
try:
    with open('trains.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    print("Xatolik: 'trains.json' fayli topilmadi. Iltimos, faylni tekshiring.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Xatolik: JSON faylni o'qishda xato yuz berdi - {e}")
    exit(1)

# 1. Poyezd raqamlari ro'yxatini chiqarish
def get_train_numbers():
    train_numbers = [train['number'] for train in data]
    return "\n".join([f"- {num}" for num in train_numbers])

# 2. Marshrutlar ro'yxatini chiqarish
def get_routes():
    routes = [f"{train['route']['station'][0]} -> {train['route']['station'][1]}" for train in data]
    return "\n".join([f"- {route}" for route in routes])

# 3. Har bir poyezdning ketish vaqti va yo'ldagi vaqtini ro'yxatlash
def get_departure_and_travel_time():
    result = []
    for train in data:
        result.append(f"Poyezd {train['number']}:")
        result.append(f"  Ketish vaqti: {train['departure']['time']} ({train['departure']['localDate']})")
        result.append(f"  Yo'ldagi vaqt: {train['timeInWay']}")
    return "\n".join(result)

# 4. Mavjud bo'sh o'rindiqlar sonini hisoblash
def get_free_seats():
    result = []
    for train in data:
        total_free_seats = 0
        for car in train['places']['cars']:
            free_seats = car.get('freeSeats')
            if free_seats:
                total_free_seats += int(free_seats)
        result.append(f"Poyezd {train['number']}: {total_free_seats} ta bo'sh o'rindiq")
    return "\n".join(result)

# 5. Poyezdlarni ketish vaqti bo'yicha saralash
def get_sorted_by_departure():
    def parse_time(train):
        time_str = train['departure']['time']
        date_str = train['departure']['localDate']
        return datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")

    sorted_trains = sorted(data, key=parse_time)
    result = []
    for train in sorted_trains:
        result.append(f"Poyezd {train['number']}: {train['departure']['time']} ({train['departure']['localDate']})")
    return "\n".join(result)

# 6. Poyezdlar bo'yicha umumiy komissiya summasi
def get_total_commission():
    result = []
    for train in data:
        total_commission_per_train = 0
        commission_count = 0
        for car in train['places']['cars']:
            for tariff in car['tariffs']['tariff']:
                commission_fee = tariff.get('comissionFee')
                if commission_fee:
                    total_commission_per_train += int(commission_fee)
                    commission_count += 1
        if commission_count > 0:
            result.append(f"Poyezd {train['number']}: {total_commission_per_train} so'm")
    return "\n".join(result)

# 7. O'rtacha komissiya summasi
def get_average_commission():
    total_commission_all = 0
    train_count = 0
    for train in data:
        total_commission_per_train = 0
        commission_count = 0
        for car in train['places']['cars']:
            for tariff in car['tariffs']['tariff']:
                commission_fee = tariff.get('comissionFee')
                if commission_fee:
                    total_commission_per_train += int(commission_fee)
                    commission_count += 1
        if commission_count > 0:
            total_commission_all += total_commission_per_train
            train_count += 1

    if train_count > 0:
        average_commission = total_commission_all / train_count
        return f"O'rtacha komissiya summasi: {average_commission:.2f} so'm"
    return "Komissiya ma'lumotlari mavjud emas."

# Menyu tugmalarini yaratish funksiyasi
def create_menu():
    reply_keyboard = [
        ["1. Poyezd raqamlari ro'yxati", "2. Marshrutlar ro'yxati"],
        ["3. Ketish vaqti va yo'ldagi vaqti", "4. Mavjud bo'sh o'rindiqlar soni"],
        ["5. Poyezdlar ketish vaqti bo'yicha saralangan", "6. Umumiy komissiya summasi"],
        ["7. O'rtacha komissiya summasi"]
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

# Telegram bot uchun handlerlar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = create_menu()
    await update.message.reply_text(
        "Salom! Men poyezdlar haqida ma'lumot beruvchi botman.\n"
        "Quyidagi menyudan birini tanlang:",
        reply_markup=markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    markup = create_menu()  # Har safar menyuni qayta ko'rsatish uchun

    if user_choice == "1. Poyezd raqamlari ro'yxati":
        await update.message.reply_text(f"1. Poyezd raqamlari ro'yxati:\n{get_train_numbers()}", reply_markup=markup)
    elif user_choice == "2. Marshrutlar ro'yxati":
        await update.message.reply_text(f"2. Marshrutlar ro'yxati:\n{get_routes()}", reply_markup=markup)
    elif user_choice == "3. Ketish vaqti va yo'ldagi vaqti":
        await update.message.reply_text(f"3. Ketish vaqti va yo'ldagi vaqti:\n{get_departure_and_travel_time()}", reply_markup=markup)
    elif user_choice == "4. Mavjud bo'sh o'rindiqlar soni":
        await update.message.reply_text(f"4. Mavjud bo'sh o'rindiqlar soni:\n{get_free_seats()}", reply_markup=markup)
    elif user_choice == "5. Poyezdlar ketish vaqti bo'yicha saralangan":
        await update.message.reply_text(f"5. Poyezdlar ketish vaqti bo'yicha saralangan:\n{get_sorted_by_departure()}", reply_markup=markup)
    elif user_choice == "6. Umumiy komissiya summasi":
        await update.message.reply_text(f"6. Poyezdlar bo'yicha umumiy komissiya summasi:\n{get_total_commission()}", reply_markup=markup)
    elif user_choice == "7. O'rtacha komissiya summasi":
        await update.message.reply_text(f"7. O'rtacha komissiya summasi:\n{get_average_commission()}", reply_markup=markup)
    else:
        await update.message.reply_text(
            "Iltimos, menyudan biror variantni tanlang.\n"
            "Agar tugmalar ko'rinmasa, /start buyrug'ini qayta yuboring yoki Telegram ilovasini yangilang.",
            reply_markup=markup
        )

# Botni ishga tushirish
def main():
    # Application obyektini yaratish
    application = Application.builder().token(TOKEN).build()

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Botni ishga tushirish
    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == '__main__':
    main()