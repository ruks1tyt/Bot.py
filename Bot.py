# requirements: aiogram==3.13.1
# pip install aiogram

import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "8614916409:AAFqAEInhobCQC4A02fgjNefzL7PM7Bx1-g"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

offers: dict[int, dict] = {}

NFT_RE = re.compile(r"https://t\.me/nft/[\w\-]+")

LANGS = {
    "ru": {
        "offer_title": "🎁 Новый оффер",
        "nft": "NFT",
        "price": "Цена",
        "seller": "Продавец",
        "pay_stars": "⭐️ Оплатить звёздами",
        "pay_gram": "💎 Оплатить в GRAM",
        "check": "🔍 Проверить",
        "cancel": "❌ Отменить",
        "paid_stars": "✅ Пользователь заявил об оплате {price} ⭐️\nПередайте NFT покупателю для завершения сделки.",
        "paid_gram": "✅ Пользователь заявил об оплате {price} GRAM\nПередайте NFT покупателю для завершения сделки.",
        "cancelled": "❌ Оффер отменён.",
        "no_offer": "Нет активного оффера.",
        "already": "Уже есть активный оффер в этом чате.",
        "bad_cmd": "Использование: /ar ССЫЛКА ЦЕНА ВАЛЮТА [ЯЗЫК]\nПример: /ar https://t.me/nft/DurovsCap-1234 500 stars ru",
        "bad_url": "❌ Неверная ссылка на NFT. Формат: https://t.me/nft/ИМЯ-НОМЕР",
        "bad_currency": "❌ Валюта должна быть stars или gram.",
    },
    "en": {
        "offer_title": "🎁 New Offer",
        "nft": "NFT",
        "price": "Price",
        "seller": "Seller",
        "pay_stars": "⭐️ Pay with Stars",
        "pay_gram": "💎 Pay with GRAM",
        "check": "🔍 Check",
        "cancel": "❌ Cancel",
        "paid_stars": "✅ User claimed payment of {price} ⭐️\nTransfer the NFT to complete the deal.",
        "paid_gram": "✅ User claimed payment of {price} GRAM\nTransfer the NFT to complete the deal.",
        "cancelled": "❌ Offer cancelled.",
        "no_offer": "No active offer.",
        "already": "There is already an active offer in this chat.",
        "bad_cmd": "Usage: /ar LINK PRICE CURRENCY [LANG]\nExample: /ar https://t.me/nft/DurovsCap-1234 500 stars en",
        "bad_url": "❌ Invalid NFT link. Format: https://t.me/nft/NAME-NUMBER",
        "bad_currency": "❌ Currency must be stars or gram.",
    },
    "zh": {
        "offer_title": "🎁 新报价",
        "nft": "NFT",
        "price": "价格",
        "seller": "卖家",
        "pay_stars": "⭐️ 用星星支付",
        "pay_gram": "💎 用 GRAM 支付",
        "check": "🔍 检查",
        "cancel": "❌ 取消",
        "paid_stars": "✅ 用户声称已支付 {price} ⭐️\n请将 NFT 转让给买家以完成交易。",
        "paid_gram": "✅ 用户声称已支付 {price} GRAM\n请将 NFT 转让给买家以完成交易。",
        "cancelled": "❌ 报价已取消。",
        "no_offer": "没有活跃报价。",
        "already": "此聊天中已有活跃报价。",
        "bad_cmd": "用法：/ar 链接 价格 货币 [语言]\n示例：/ar https://t.me/nft/DurovsCap-1234 500 stars zh",
        "bad_url": "❌ NFT 链接无效。格式：https://t.me/nft/名称-编号",
        "bad_currency": "❌ 货币必须是 stars 或 gram。",
    },
    "ar": {
        "offer_title": "🎁 عرض جديد",
        "nft": "NFT",
        "price": "السعر",
        "seller": "البائع",
        "pay_stars": "⭐️ الدفع بالنجوم",
        "pay_gram": "💎 الدفع بـ GRAM",
        "check": "🔍 تحقق",
        "cancel": "❌ إلغاء",
        "paid_stars": "✅ أعلن المستخدم عن دفع {price} ⭐️\nانقل NFT للمشتري لإتمام الصفقة.",
        "paid_gram": "✅ أعلن المستخدم عن دفع {price} GRAM\nانقل NFT للمشتري لإتمام الصفقة.",
        "cancelled": "❌ تم إلغاء العرض.",
        "no_offer": "لا يوجد عرض نشط.",
        "already": "يوجد عرض نشط بالفعل في هذه المحادثة.",
        "bad_cmd": "الاستخدام: /ar رابط سعر عملة [لغة]\nمثال: /ar https://t.me/nft/DurovsCap-1234 500 stars ar",
        "bad_url": "❌ رابط NFT غير صالح. الصيغة: https://t.me/nft/الاسم-الرقم",
        "bad_currency": "❌ يجب أن تكون العملة stars أو gram.",
    },
}

def t(lang: str, key: str, **kw) -> str:
    s = LANGS.get(lang, LANGS["ru"]).get(key, key)
    return s.format(**kw) if kw else s

def offer_keyboard(lang: str, currency: str) -> InlineKeyboardMarkup:
    pay_label = t(lang, "pay_stars") if currency == "stars" else t(lang, "pay_gram")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=pay_label, callback_data=f"pay:{currency}")],
        [
            InlineKeyboardButton(text=t(lang, "check"), callback_data="check"),
            InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel"),
        ],
    ])

def offer_text(offer: dict) -> str:
    lang = offer["lang"]
    currency_label = "⭐️ Stars" if offer["currency"] == "stars" else "💎 GRAM"
    lines = [
        f"<b>{t(lang, 'offer_title')}</b>",
        "",
        f"🔗 <b>{t(lang, 'nft')}:</b> <a href='{offer['url']}'>{offer['nft_name']}</a>",
        f"💰 <b>{t(lang, 'price')}:</b> {offer['price']} {currency_label}",
        f"👤 <b>{t(lang, 'seller')}:</b> @{offer['seller_username']}",
    ]
    return "\n".join(lines)

@dp.message(Command("ar"))
async def cmd_ar(message: Message):
    chat_id = message.chat.id
    lang = "ru"

    args = message.text.split()[1:]

    if not args:
        await message.reply(t(lang, "bad_cmd"))
        return

    url = None
    rest = []
    for a in args:
        if NFT_RE.match(a):
            url = a
        else:
            rest.append(a)

    if not url:
        await message.reply(t(lang, "bad_url"))
        return

    if len(rest) < 2:
        await message.reply(t(lang, "bad_cmd"))
        return

    price_str, currency = rest[0], rest[1].lower()
    if len(rest) >= 3:
        lang = rest[2].lower() if rest[2].lower() in LANGS else "ru"

    try:
        price = float(price_str)
    except ValueError:
        await message.reply(t(lang, "bad_cmd"))
        return

    if currency not in ("stars", "gram"):
        await message.reply(t(lang, "bad_currency"))
        return

    if chat_id in offers:
        await message.reply(t(lang, "already"))
        return

    nft_name = url.rstrip("/").split("/")[-1]
    seller_username = message.from_user.username or str(message.from_user.id)

    offers[chat_id] = {
        "url": url,
        "nft_name": nft_name,
        "price": price,
        "currency": currency,
        "lang": lang,
        "seller_id": message.from_user.id,
        "seller_username": seller_username,
    }

    await message.answer(
        offer_text(offers[chat_id]),
        reply_markup=offer_keyboard(lang, currency),
        parse_mode="HTML",
        disable_web_page_preview=False,
    )

@dp.callback_query(F.data.startswith("pay:"))
async def cb_pay(call: CallbackQuery):
    chat_id = call.message.chat.id
    offer = offers.get(chat_id)
    if not offer:
        await call.answer(t("ru", "no_offer"), show_alert=True)
        return

    lang = offer["lang"]
    currency = offer["currency"]

    if currency == "stars":
        text = t(lang, "paid_stars", price=int(offer["price"]))
    else:
        text = t(lang, "paid_gram", price=offer["price"])

    await call.message.edit_text(
        offer_text(offer) + "\n\n" + text,
        parse_mode="HTML",
        reply_markup=None,
    )
    await call.answer()

@dp.callback_query(F.data == "check")
async def cb_check(call: CallbackQuery):
    chat_id = call.message.chat.id
    offer = offers.get(chat_id)
    if not offer:
        await call.answer(t("ru", "no_offer"), show_alert=True)
        return
    await call.answer(f"NFT: {offer['nft_name']} | {offer['price']} {offer['currency']}", show_alert=True)

@dp.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery):
    chat_id = call.message.chat.id
    offer = offers.pop(chat_id, None)
    if not offer:
        await call.answer(t("ru", "no_offer"), show_alert=True)
        return
    lang = offer["lang"]
    await call.message.edit_text(t(lang, "cancelled"), reply_markup=None)
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
