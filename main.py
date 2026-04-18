
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from service import get_download_url

TOKEN = getenv("BOT_TOKEN")
dp = Dispatcher()



class EditState(StatesGroup):
    waiting_for_id = State()
    waiting_for_photo = State()



def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼 Rasm Edit"), KeyboardButton(text="👤 Profil")],
            [KeyboardButton(text="❓ Yordam"),    KeyboardButton(text="💳 Donat")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Quyidagilardan birini tanlang...",
    )

def donate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Click orqali", url="https://click.uz")],
        [InlineKeyboardButton(text="💳 Payme orqali", url="https://payme.uz")],
    ])

def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )



@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Salom, {html.bold(message.from_user.full_name)}! 👋\n\n"
        f"Rasm tahrirlash botiga xush kelibsiz.\n"
        f"Quyidagi tugmalardan foydalaning:",
        reply_markup=main_keyboard(),
    )



@dp.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())



@dp.message(F.text == "🖼 Rasm Edit")
async def rasm_edit_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(EditState.waiting_for_id)
    await message.answer(
        "🎨 <b>1-qadam: Effect ID kiriting</b>\n\n"
        "Masalan: <code>24302596</code>\n\n"
        "<i>Effect ID ni bilmasangiz, API hujjatlarini tekshiring.</i>",
        reply_markup=cancel_keyboard(),
    )



@dp.message(EditState.waiting_for_id, F.text)
async def process_effect_id(message: Message, state: FSMContext) -> None:
    effect_id = message.text.strip()

    if not effect_id.isdigit():
        await message.answer(
            "❌ ID faqat raqamlardan iborat bo'lishi kerak.\n"
            "Iltimos, qayta kiriting:"
        )
        return

    await state.update_data(effect_id=effect_id)
    await state.set_state(EditState.waiting_for_photo)
    await message.answer(
        f"✅ Effect ID: <code>{effect_id}</code>\n\n"
        "📸 <b>2-qadam: Rasm URL manzilini yuboring</b>\n\n"
        "Masalan:\n"
        "<code>https://example.com/photo.jpg</code>",
        reply_markup=cancel_keyboard(),
    )



@dp.message(EditState.waiting_for_photo, F.text)
async def process_photo_url(message: Message, state: FSMContext) -> None:
    photo_url = message.text.strip()

    if not photo_url.startswith("http"):
        await message.answer(
            "❌ Noto'g'ri URL. http:// yoki https:// bilan boshlanishi kerak.\n"
            "Qayta kiriting:"
        )
        return

    data = await state.get_data()
    effect_id = data.get("effect_id")

    processing_msg = await message.answer(
        "⏳ <b>Rasm tahrirlanmoqda...</b>\n"
        "<i>Bu bir necha soniya vaqt olishi mumkin.</i>"
    )

    result_url = await get_download_url(photo_url=photo_url, effect_id=effect_id)

    await processing_msg.delete()
    await state.clear()

    if result_url:
        await message.answer_photo(
            photo=result_url,
            caption=f"✅ <b>Tayyor!</b>\n🎨 Effect ID: <code>{effect_id}</code>",
            reply_markup=main_keyboard(),
        )
    else:
        await message.answer(
            "❌ <b>Xato yuz berdi.</b>\n\n"
            "Mumkin sabablar:\n"
            "• Noto'g'ri Effect ID\n"
            "• Rasm URL ishlamayapti\n"
            "• API muammosi\n\n"
            "Qayta urinib ko'ring.",
            reply_markup=main_keyboard(),
        )



@dp.message(F.text == "👤 Profil")
async def profile_handler(message: Message) -> None:
    user = message.from_user
    username = f"@{user.username}" if user.username else "yo'q"
    await message.answer(
        f"👤 <b>Profilingiz:</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📛 Ism: {html.bold(user.full_name)}\n"
        f"🔗 Username: {username}\n"
        f"🌐 Til: {user.language_code or 'nomalum'}",
    )



@dp.message(F.text == "❓ Yordam")
@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "📖 <b>Yordam</b>\n\n"
        "🖼 <b>Rasm Edit</b> — Effect ID va URL kiritib rasm tahrirlash\n"
        "👤 <b>Profil</b> — Profil ma'lumotlaringiz\n"
        "❓ <b>Yordam</b> — Ushbu yordam menyusi\n"
        "💳 <b>Donat</b> — Botni qo'llab-quvvatlash\n\n"
        "❔ Savol bo'lsa: @admin",
    )



@dp.message(F.text == "💳 Donat")
async def donate_handler(message: Message) -> None:
    await message.answer(
        "💳 <b>Donat</b>\n\n"
        "Botni rivojlantirish uchun qo'llab-quvvatlashingiz mumkin:",
        reply_markup=donate_keyboard(),
    )



@dp.message()
async def unknown_handler(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer(
            "❓ Tushunmadim. Tugmalardan foydalaning:",
            reply_markup=main_keyboard(),
        )



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())