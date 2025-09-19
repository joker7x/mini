import importlib, subprocess, sys
import asyncio
import urllib.parse
import os
import re
import json
import base64

def ensure_package(package_name, import_name=None, version_spec=None):
    mod_name = import_name or package_name
    try:
        return importlib.import_module(mod_name)
    except ImportError:
        pkg_spec = f"{package_name}{version_spec or ''}"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg_spec])
        return importlib.import_module(mod_name)

requests = ensure_package("requests")
ensure_package("colorama")
ensure_package("pytz")
ensure_package("tzlocal")
from colorama import Fore, Style, init
try:
    dotenv = ensure_package("python-dotenv")
    from dotenv import load_dotenv
except Exception:
    dotenv = None
    def load_dotenv(*args, **kwargs):
        return False

# تأكد من مكتبات الجدولة المتوافقة قبل تيليجرام
ensure_package("APScheduler", import_name="apscheduler", version_spec="<4")
ensure_package("tzlocal", version_spec="<3")

# طبّق ضبط المنطقة الزمنية لـ APScheduler قبل استيراد تيليجرام
import pytz as _pytz_for_aps
from apscheduler import util as _aps_util
_aps_util.get_localzone = lambda: _pytz_for_aps.utc

# تأكد من مكتبة تيليجرام (v20+)
ensure_package("python-telegram-bot", import_name="telegram", version_spec=">=20.0")
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.ext._jobqueue import JobQueue as _BaseJobQueue
from apscheduler.schedulers.asyncio import AsyncIOScheduler as _AsyncIOScheduler
import pytz as _pytz

class UTCJobQueue(_BaseJobQueue):
    def __init__(self):
        super().__init__()
        try:
            # استبدل المجدول الافتراضي بواحد مضبوط على UTC
            self.scheduler = _AsyncIOScheduler(timezone=_pytz.utc)
        except Exception:
            pass

init(autoreset=True)

# استخدم Session لتحسين الأداء وإعادة استخدام الاتصالات
SESSION = requests.Session()
DEFAULT_TIMEOUT = 10

def http_get(url, headers=None, timeout=None):
    return SESSION.get(url, headers=headers, timeout=timeout or DEFAULT_TIMEOUT)

# مفاتيح الحالة في التيليجرام
TG_STATE = {}
CHAT_SETTINGS = {}

def _tg_set(chat_id, key, value):
    if chat_id not in TG_STATE:
        TG_STATE[chat_id] = {}
    TG_STATE[chat_id][key] = value

def _tg_get(chat_id, key, default=None):
    return TG_STATE.get(chat_id, {}).get(key, default)

def _settings_get(chat_id):
    if chat_id not in CHAT_SETTINGS:
        CHAT_SETTINGS[chat_id] = {
            "web_preview": False,
            "max_links": 10,
            "mini_app_url": "https://mini-jet.vercel.app/",
        }
    return CHAT_SETTINGS[chat_id]

# ⚙️ الإعدادات الثابتة
BASE_URL = "https://abcdef.flech.tn/egybestanto/public/api"
TOKEN = "p2lbgWkFrykA4QyUmpHihzmc5BNzIABq"
BEARER_TOKEN = "AuHLIRR82MvrdTTeaQKUxdA7mlNuk0WD6NnX2ffpn0wqeMP5zwkCClOHClRIbCFf"
TELEGRAM_BOT_TOKEN_HARDCODED = "5911061931:AAGSgzXHr6mDMLzle0vdxRE_ksr5BJmD87M"

DATA_HEADERS = {
    "search": "T38IgEbV/RLlvSL//rFR0DVyo5vYddHELyToJoBRpWzTQUSmKFOz9VL1LJWpsFOva8f5inz7ebwahtGypB4eBnlHLdpvLtdD4t2Sl+xZPlk59GZ7Pb2WDW79U0jY3y1mRF2O8azr+IqzdNfSlxeHl3fi2I9pcWxAzdXXkJoKaSALaO8SnLXefAboK+KTzzTNeiCiPyJgLA841AYU02DpoQH9fEV5zsgAicahzoG9qzoWvGa/OHrwkDDn1HOhFf0ejGXeKifiKsjtaO5O+zeITXgn9EnyjTfAD0KWlVWCDTIDupf8nD57eIsvRbhgvoMjUkzqWv8D2pVA971hnufUEA==",
    "series_show": "Kmy+WhHBjouCYl8+gd/OyZl1vvWqoAv09LFpwDFMmpxkzzVv0J9xQI0ulRNXp2N0v/oRH3iv1PfxI4rHG+lVLoZEcrmFuETxU7CcnW9rBOOvlHx2VX0eJ7y0K+YuHiVLZNl6U3I4Xnhk3AXCylguHAj84Gy1/qp48+RIyYowtzv4u0X1veZS1X5xcGhaZPfH628JeKIbe3uUXEvqyGtHUPy90Q9jafApWF0rBirBas6fbl6Jer1BEIGS78Ze4rTcLgrfbouTxSxpX0eHQA9i95UK4Xxp35d2HSz9CuPLEWYkbiLiAaxT440R4VR1ZxJcDlW0baXHYTJYZtHq4oJxFA==",
}

HEADERS_TEMPLATE = {
    "User-Agent": "okhttp/5.0.0-alpha.6",
    "Accept": "application/json",
    "packagename": "com.egyappwatch",
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "sizato": "87174662",
    "UserData": "dmlkZQ==",
    "DataData": "dmlkZQ=="
}

# ✅ قائمة السيرفرات المدعومة — من الـ config
SUPPORTED_HOSTS = [
    {
        "name": "faselhd",
        "pattern": r"(faselhds?\.life|faselhd\.com)",
        "extractor": "scrape_faselhd",
        "urlsite": "https://www.flech.tn/scrapefaselpostid.php?api=",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "site_pattern": r'file:\s*["\']([^"\']+)["\'].*?label:\s*["\']([^"\']+)["\']'
    },
    {
        "name": "vidtube",
        "pattern": r"vidtube\.pro",
        "extractor": "scrape_vidtube",
        "urlsite": "https://abcdef.flech.tn/scrapefinal/Scriptvidtube.php?api=",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "site_pattern": r'href=["\']([^"\']+)["\'].*?<quality>([^<]+)</quality>'
    },
    {
        "name": "vidhide",
        "pattern": r"(vidhide|streamwish|vidoba|filemoon)",
        "extractor": "scrape_generic_regex",
        "urlsite": "https://abcdef.flech.tn/scrapefinal/testflech.php?api=",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "site_pattern": r'file:\s*["\']([^"\']+)["\']'
    },
    {
        "name": "anafast",
        "pattern": r"anafast\.com",
        "extractor": "scrape_generic_regex",
        "urlsite": "https://abcdef.flech.tn/scrapefinal/testflech.php?api=",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "site_pattern": r'sources.*?(https?://[^\s"\']+\.(?:m3u8|mp4))'
    },
    {
        "name": "liiivideo",
        "pattern": r"liiivideo\.com",
        "extractor": "scrape_generic_regex",
        "urlsite": "https://www.flech.tn/scrapefinal/scriptalvid.php?api=",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "site_pattern": r'file:\s*["\']([^"\']+)["\'].*?label:\s*["\']([^"\']+)["\']'
    },
    {
        "name": "egybestvid",
        "pattern": r"egybestvid\.com",
        "extractor": "scrape_generic_regex",
        "urlsite": "https://abcdef.flech.tn/scrapefinal/testflech.php?api=",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "site_pattern": r'file:\s*["\']([^"\']+)["\']'
    }
]

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def search(query):
    url = f"{BASE_URL}/search/{urllib.parse.quote(query + ' |vide')}/{TOKEN}"
    headers = HEADERS_TEMPLATE.copy()
    headers["Data"] = DATA_HEADERS["search"]
    return http_get(url, headers=headers).json()

def get_series(series_id):
    url = f"{BASE_URL}/series/show/{series_id}/{TOKEN}"
    headers = HEADERS_TEMPLATE.copy()
    headers["Data"] = DATA_HEADERS["series_show"]
    return http_get(url, headers=headers).json()

def print_info(data):
    name = data.get('name', '---')
    first_air_date = data.get('first_air_date', '')
    year = first_air_date[:4] if first_air_date else '----'
    vote_avg = data.get('vote_average', '?')
    genres = get_genres(data)
    networks = get_networks(data)
    overview = data.get('overview', 'لا يوجد ملخص')
    if len(overview) > 300:
        overview = overview[:300] + '...'
    cast = ', '.join(get_cast(data)[:4])

    print(f"\n{Fore.CYAN}🎬 {name} ({year})")
    print(f"{Fore.YELLOW}⭐ {vote_avg}/10 | 🎭 {genres}")
    print(f"{Fore.BLUE}📅 {first_air_date or '---'} | 📺 {networks}")
    print(f"\n{Fore.WHITE}📝 {overview}")
    print(f"{Fore.GREEN}👥 {cast}")
    print(Fore.RED + "—" * 50)

def get_genres(data):
    gl = data.get('genreslist') or []
    if not gl:
        return "غير معروف"
    result = []
    for g in gl:
        if isinstance(g, str):
            result.append(g)
        elif isinstance(g, dict):
            name = g.get('name', '').strip()
            if name:
                result.append(name)
    return ", ".join(result) if result else "غير معروف"

def get_networks(data):
    nl = data.get('networkslist') or []
    names = []
    for n in nl:
        if isinstance(n, dict) and n.get('name'):
            name = n['name'].strip()
            if name:
                names.append(name)
    return ", ".join(names) if names else "غير معروفة"

def get_cast(data):
    cl = data.get('casterslist') or []
    result = []
    for c in cl:
        if isinstance(c, dict) and c.get('name'):
            name = c['name'].strip()
            if name:
                result.append(name)
    return result

# 🆕 استخراج faselhd
def scrape_faselhd_links(embed_url, headers):
    scrape_url = f"https://www.flech.tn/scrapefaselpostid.php?api={urllib.parse.quote(embed_url)}"
    try:
        response = http_get(scrape_url, headers=headers)
        text = response.text.strip()
        parts = text.split("{file:")
        links = []
        for part in parts[1:]:
            file_end = part.find(",label:")
            label_end = part.find("}", file_end)
            if file_end == -1 or label_end == -1:
                continue
            file_url = part[:file_end].strip().strip('"')
            label = part[file_end+7:label_end].strip().strip('"')
            links.append({"label": label, "file": file_url})
        return links
    except Exception as e:
        print(Fore.RED + f"❌ خطأ في استخراج faselhd: {str(e)}")
        return []

# 🆕 استخراج vidtube
def scrape_vidtube_links(embed_url, headers):
    scrape_url = f"https://abcdef.flech.tn/scrapefinal/Scriptvidtube.php?api={urllib.parse.quote(embed_url)}"
    try:
        response = http_get(scrape_url, headers=headers)
        html = response.text
        pattern = r'href="(.*?)".*?<quality>(.*?)</quality>'
        matches = re.findall(pattern, html, re.DOTALL)
        links = []
        for url, quality in matches:
            clean_quality = re.sub(r'[pP]', '', quality.replace(' FHD', '').replace(' HD', '').replace(' SD', '').strip())
            links.append({"label": clean_quality, "file": url})
        return links
    except Exception as e:
        print(Fore.RED + f"❌ خطأ في استخراج vidtube: {str(e)}")
        return []

# 🆕 استخراج عام باستخدام Regex
def scrape_generic_regex(embed_url, headers, pattern):
    try:
        # جرب نستخرج من الصفحة مباشرة
        response = http_get(embed_url, headers=headers)
        html = response.text

        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        links = []
        for match in matches:
            if isinstance(match, tuple):
                file_url = match[0]
                label = match[1] if len(match) > 1 else "Auto"
                links.append({"label": label, "file": file_url})
            else:
                links.append({"label": "Auto", "file": match})

        # لو مفيش حاجة — جرب نمط m3u8 عام
        if not links:
            m3u8_matches = re.findall(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html, re.IGNORECASE)
            for url in m3u8_matches:
                links.append({"label": "Auto", "file": url})

        return links
    except Exception as e:
        print(Fore.RED + f"❌ خطأ في الاستخراج: {str(e)}")
        return []

# 🆕 تحويل اسم الجودة لرقم للمقارنة
def quality_to_number(q):
    if not isinstance(q, str):
        return 0
    q = q.lower()
    if "auto" in q: return 9999
    if "1080" in q or "fhd" in q or "full hd" in q: return 1080
    if "720" in q or "hd" in q: return 720
    if "480" in q or "sd" in q: return 480
    if "360" in q: return 360
    if "240" in q: return 240
    return 0

# 🆕 فرز الروابط حسب الجودة (من الأعلى للأدنى)
def sort_links_by_quality(links):
    return sorted(links, key=lambda x: quality_to_number(x["quality"]), reverse=True)

# 🆕 جلب الروابط المباشرة — مدعومة لكل السيرفرات
def get_direct_links(videos):
    direct_links = []
    for video in videos:
        link = video.get("link", "").strip()
        server = video.get("server", "")

        # ✅ تأكد إن الرابط مكتمل
        if link and not link.startswith("http"):
            link = "https://" + link

        if not link:
            continue

        # 🔍 دور على السيرفر المناسب
        host_config = None
        for host in SUPPORTED_HOSTS:
            if re.search(host["pattern"], link, re.IGNORECASE):
                host_config = host
                break

        if host_config:
            print(Fore.YELLOW + f"⏳ جاري استخراج روابط من {host_config['name']}...")
            headers = {
                "User-Agent": host_config["user_agent"],
                "Referer": link
            }

            # نفذ الاستخراج حسب النوع
            if host_config["extractor"] == "scrape_faselhd":
                extracted = scrape_faselhd_links(link, headers)
            elif host_config["extractor"] == "scrape_vidtube":
                extracted = scrape_vidtube_links(link, headers)
            elif host_config["extractor"] == "scrape_generic_regex":
                extracted = scrape_generic_regex(link, headers, host_config["site_pattern"])
            else:
                extracted = []

            for item in extracted:
                direct_links.append({
                    "server": server,
                    "quality": item.get("label", "Auto"),
                    "url": item["file"],
                    "referer": link,
                    "ua": host_config["user_agent"],
                })
        else:
            # لو السيرفر مش معروف — خده كرابط مباشر
            direct_links.append({
                "server": server,
                "quality": "رابط مباشر",
                "url": link,
                "referer": None,
                "ua": HEADERS_TEMPLATE.get("User-Agent", "Mozilla/5.0"),
            })

    return sort_links_by_quality(direct_links)

# ===================== Telegram Handlers =====================
async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = _settings_get(chat_id)
    text = (
        "مرحبا بك 👋\n\n"
        "هذه أوامر البوت:\n"
        "- /search اسم_المسلسل — بحث سريع\n"
        "- ابعث اسم المسلسل مباشرة بدون أمر\n"
        "- /id 12345 — فتح مسلسل عبر ID\n"
        "- /settings — الإعدادات\n"
        "- /help — المساعدة\n\n"
        f"حالة المعاينة: {'مغلّقة' if not s['web_preview'] else 'مفعّلة'} | أقصى روابط: {s['max_links']}\n"
    )
    await update.message.reply_text(text, disable_web_page_preview=not s["web_preview"])

async def tg_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = _settings_get(chat_id)
    text = (
        "دليل استخدام البوت:\n\n"
        "1) ابعث اسم المسلسل مباشرة أو استخدم الأمر /search ثم الاسم.\n"
        "2) اختر المسلسل من الأزرار.\n"
        "3) اختر الموسم ثم الحلقة.\n"
        "4) سيصلك جدول بالروابط المباشرة مرتبة حسب الجودة.\n\n"
        "أوامر:\n"
        "- /start — رسالة البداية\n"
        "- /help — هذه المساعدة\n"
        "- /search اسم — بحث\n"
        "- /id رقم — فتح مسلسل عبر ID\n"
        "- /settings — الإعدادات\n"
    )
    await update.message.reply_text(text, disable_web_page_preview=not s["web_preview"])

async def tg_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = " ".join(context.args).strip()
    if not query_text:
        await update.message.reply_text("اكتب اسم المسلسل بعد الأمر، مثال: /search La Casa de Papel")
        return
    results = search(query_text)
    shows = results.get("search", [])
    if not shows:
        await update.message.reply_text("❌ مفيش نتائج!")
        return
    _tg_set(update.effective_chat.id, 'shows', shows)
    await update.message.reply_text(
        f"✅ اتلاقى {len(shows)} نتيجة:",
        reply_markup=_build_shows_keyboard(shows),
        disable_web_page_preview=not _settings_get(update.effective_chat.id)["web_preview"]
    )

async def tg_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("استخدم: /id 12345")
        return
    sid = context.args[0]
    details = get_series(sid)
    if not isinstance(details, dict) or not details.get("name"):
        await update.message.reply_text("❌ فشل في جلب البيانات!")
        return
    _tg_set(update.effective_chat.id, 'details', details)
    await update.message.reply_text(
        f"🎬 {details.get('name','---')}\nاختر موسم:",
        reply_markup=_build_seasons_keyboard(details),
        disable_web_page_preview=not _settings_get(update.effective_chat.id)["web_preview"]
    )

async def tg_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    start = datetime.now()
    msg = await update.message.reply_text("⏳ Pinging...")
    delta = datetime.now() - start
    await msg.edit_text(f"✅ Pong! {int(delta.total_seconds()*1000)}ms")

def _settings_keyboard(chat_id):
    s = _settings_get(chat_id)
    web = '✅ تفعيل المعاينة' if s['web_preview'] else '❌ تعطيل المعاينة'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(web, callback_data="settings:toggle_preview")],
        [InlineKeyboardButton("- تقليل الروابط", callback_data="settings:maxlinks:-"), InlineKeyboardButton("+ زيادة الروابط", callback_data="settings:maxlinks:+")],
        [InlineKeyboardButton("رجوع", callback_data="settings:back")]
    ])

async def tg_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = _settings_get(chat_id)
    text = (
        "⚙️ الإعدادات:") + f"\n- معاينة الروابط: {'تشغيل' if s['web_preview'] else 'إيقاف'}" + f"\n- أقصى عدد روابط: {s['max_links']}" + f"\n- رابط الميني آب: {s.get('mini_app_url') or 'غير مضبوط'}"
    await update.message.reply_text(text, reply_markup=_settings_keyboard(chat_id), disable_web_page_preview=not s["web_preview"]) 

async def tg_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = _settings_get(chat_id)
    text = (
        "ℹ️ عن البوت:\n"
        "- بوت بحث وعرض روابط مشاهدة مباشرة.\n"
        "- يدعم اختيار المواسم والحلقات والفرز حسب الجودة.\n"
        "- أوامر سهلة ولوحة إعدادات.")
    await update.message.reply_text(text, disable_web_page_preview=not s["web_preview"]) 

async def tg_setminiapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("استخدم: /setminiapp https://your-mini-app.host")
        return
    url = context.args[0].strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("الرابط غير صالح. يجب أن يبدأ بـ http أو https")
        return
    _settings_get(chat_id)["mini_app_url"] = url
    await update.message.reply_text(f"تم ضبط رابط الميني آب: {url}")

def _build_shows_keyboard(shows):
    keyboard = []
    row = []
    for idx, show in enumerate(shows, 1):
        title = show.get('title') or show.get('original_name', '---')
        sid = str(show.get('id', ''))
        row.append(InlineKeyboardButton(title[:30], callback_data=f"show:{sid}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def _build_seasons_keyboard(details):
    seasons = details.get("seasons", [])
    keyboard = []
    row = []
    for i, s in enumerate(seasons, 1):
        name = s.get("name", f"S{i}")
        row.append(InlineKeyboardButton(name[:20], callback_data=f"season:{i-1}"))
        if len(row) == 3:
            keyboard.append(row); row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def _build_episodes_keyboard(episodes):
    keyboard = []
    row = []
    for i, ep in enumerate(episodes, 1):
        ep_name = ep.get('name', f"EP {i}")
        row.append(InlineKeyboardButton(str(i), callback_data=f"ep:{i-1}"))
        if len(row) == 5:
            keyboard.append(row); row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def tg_on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return
    results = search(query)
    shows = results.get("search", [])
    if not shows:
        await update.message.reply_text("❌ مفيش نتائج!")
        return
    _tg_set(update.effective_chat.id, 'shows', shows)
    await update.message.reply_text(
        f"✅ اتلاقى {len(shows)} نتيجة:",
        reply_markup=_build_shows_keyboard(shows),
        disable_web_page_preview=not _settings_get(update.effective_chat.id)["web_preview"]
    )

async def tg_on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id
    await query.answer()

    if data.startswith("show:"):
        sid = data.split(":",1)[1]
        details = get_series(sid)
        if not isinstance(details, dict) or not details.get("name"):
            await query.edit_message_text("❌ فشل في جلب البيانات!")
            return
        _tg_set(chat_id, 'details', details)
        await query.edit_message_text(
            f"🎬 {details.get('name','---')}\nاختر موسم:",
            reply_markup=_build_seasons_keyboard(details)
        )
    elif data.startswith("season:"):
        idx = int(data.split(":",1)[1])
        details = _tg_get(chat_id, 'details')
        seasons = details.get("seasons", []) if details else []
        if not seasons or not (0 <= idx < len(seasons)):
            await query.edit_message_text("❌ موسم غير صحيح")
            return
        _tg_set(chat_id, 'season_idx', idx)
        episodes = seasons[idx].get("episodes", [])
        _tg_set(chat_id, 'episodes', episodes)
        await query.edit_message_text(
            f"📂 {seasons[idx].get('name','الموسم')}\nاختر حلقة:",
            reply_markup=_build_episodes_keyboard(episodes)
        )
    elif data.startswith("ep:"):
        ep_idx = int(data.split(":",1)[1])
        episodes = _tg_get(chat_id, 'episodes', [])
        if not episodes or not (0 <= ep_idx < len(episodes)):
            await query.edit_message_text("❌ حلقة غير صحيحة")
            return
        ep = episodes[ep_idx]
        videos = ep.get("videos", [])
        if not videos:
            await query.edit_message_text("❌ مفيش روابط!")
            return
        # جهّز الروابط المباشرة (سنرسلها للميني آب مش للمستخدم)
        await query.edit_message_text("⏳ تجهيز المشغل...")
        links = get_direct_links(videos)
        if not links:
            await context.bot.send_message(chat_id, "❌ فشل في استخراج أي روابط.")
            return
        s = _settings_get(chat_id)
        mini = s.get("mini_app_url")
        if not mini:
            await query.edit_message_text("⚙️ لم يتم ضبط رابط الميني-آب بعد. استخدم /setminiapp https://your-mini-app.host")
            return
        # قلّل الحجم وأرسل أول N روابط كحزمة base64
        max_links = s["max_links"]
        compact = [{
            "q": dl.get("quality"),
            "u": dl.get("url"),
            "r": dl.get("referer"),
            "ua": dl.get("ua"),
        } for dl in links[:max_links]]
        payload = base64.urlsafe_b64encode(json.dumps({"sources": compact}).encode()).decode()
        from urllib.parse import urlencode
        params = urlencode({"s": payload})
        open_url = f"{mini}?{params}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ فتح المشغل", web_app=WebAppInfo(open_url))]])
        await query.edit_message_text("🎬 افتح المشغل لاختيار الجودة والمشاهدة.", reply_markup=kb)
    elif data.startswith("settings:" ):
        action = data.split(":", 1)[1]
        s = _settings_get(chat_id)
        if action == "toggle_preview":
            s["web_preview"] = not s["web_preview"]
        elif action.startswith("maxlinks"):
            sign = action.split(":")[-1]
            if sign == "+":
                s["max_links"] = min(20, s["max_links"] + 1)
            else:
                s["max_links"] = max(3, s["max_links"] - 1)
        txt = ("⚙️ الإعدادات:\n" 
               f"- معاينة الروابط: {'تشغيل' if s['web_preview'] else 'إيقاف'}\n"
               f"- أقصى عدد روابط: {s['max_links']}")
        await query.edit_message_text(txt, reply_markup=_settings_keyboard(chat_id))

async def tg_on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id if isinstance(update, Update) and update.effective_chat else None
    except Exception:
        chat_id = None
    err_msg = "⚠️ حصل خطأ غير متوقع. حاول تاني بعد شوية."
    if chat_id:
        try:
            await context.bot.send_message(chat_id, err_msg)
        except Exception:
            pass
    print(Fore.RED + f"[ERROR] {getattr(context, 'error', 'Unknown error')}")

async def _post_init(app):
    try:
        # تأكد من إلغاء أي Webhook قديم قبل تشغيل الPolling
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            print(Fore.YELLOW + "تم إلغاء أي Webhook سابق (إن وُجد).")
        except Exception as e:
            print(Fore.YELLOW + f"تنبيه: تعذر إلغاء Webhook: {e}")

        await app.bot.set_my_commands([
            ("start", "رسالة البداية"),
            ("help", "المساعدة"),
            ("search", "بحث عن مسلسل"),
            ("id", "فتح مسلسل عبر ID"),
            ("settings", "الإعدادات"),
            ("ping", "اختبار الاستجابة"),
            ("about", "عن البوت"),
        ])
    except Exception as e:
        print(Fore.YELLOW + f"تنبيه: تعذر ضبط أوامر البوت: {e}")

def show_episodes(data):
    seasons = data.get("seasons", [])
    if not seasons:
        print(Fore.RED + "❌ مفيش مواسم!")
        return

    while True:
        clear()
        print(Fore.CYAN + "\n📂 المواسم:")
        for i, s in enumerate(seasons, 1):
            name = s.get("name", f"الموسم {s.get('season_number', '?')}")
            count = len(s.get("episodes", []))
            print(f"  {Fore.GREEN}{i}. {name} ({count} حلقات)")

        print(f"\n{Fore.YELLOW}🔙 0 للعودة")
        choice = input(Fore.WHITE + "\n👉 اختر موسم: ").strip()
        if choice == "0": return
        if not choice.isdigit() or not (1 <= int(choice) <= len(seasons)):
            print(Fore.RED + "❌ اختيار غير صحيح!")
            input("↵ Enter...")
            continue

        season = seasons[int(choice)-1]
        episodes = season.get("episodes", [])
        while True:
            clear()
            print(Fore.CYAN + f"\n📌 {season.get('name', '---')}")
            for i, ep in enumerate(episodes, 1):
                ep_name = ep.get('name', f"الحلقة {ep.get('episode_number', '?')}")
                print(f"  {Fore.BLUE}{i}. {ep_name}")

            print(f"\n{Fore.YELLOW}🔙 0 للعودة | 🖱️ ادخل رقم الحلقة للمشاهدة")
            ep_choice = input(Fore.WHITE + "\n👉 اختر: ").strip()
            if ep_choice == "0": break
            if not ep_choice.isdigit() or not (1 <= int(ep_choice) <= len(episodes)):
                print(Fore.RED + "❌ غير صحيح!")
                input("↵ Enter...")
                continue

            ep = episodes[int(ep_choice)-1]
            videos = ep.get("videos", [])
            if not videos:
                print(Fore.RED + "❌ مفيش روابط!")
                input("↵ Enter...")
                continue

            clear()
            print(Fore.GREEN + f"\n▶️ جاري تجهيز روابط المشاهدة: {ep.get('name', '---')}\n")
            direct_links = get_direct_links(videos)

            if not direct_links:
                print(Fore.RED + "❌ فشل في استخراج أي روابط مباشرة.")
                input("↵ Enter...")
                continue

            # عرض الروابط بعد الترتيب
            print(Fore.CYAN + "\n✅ الروابط المباشرة (مرتبة حسب الجودة):")
            for i, dl in enumerate(direct_links, 1):
                print(f"   {Fore.YELLOW}{i}. [{dl['server']}] {dl['quality']} → {Fore.CYAN}{dl['url']}")

            input(f"\n{Fore.YELLOW}↵ Enter للعودة...")

# 🧭 البرنامج الرئيسي
def main():
    # يعمل كبوت تيليجرام فقط
    # 1) حمل .env إن وجد
    try:
        load_dotenv()
    except Exception:
        pass

    # 2) من وسيطة سطر أوامر --token=...
    token_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("--token="):
            token_arg = arg.split("=",1)[1].strip()
            break

    # 3) من ملف TELEGRAM_BOT_TOKEN.txt إن وجد
    file_token = None
    token_file_path = os.path.join(os.getcwd(), "TELEGRAM_BOT_TOKEN.txt")
    if os.path.exists(token_file_path):
        try:
            with open(token_file_path, "r", encoding="utf-8") as f:
                file_token = f.read().strip()
        except Exception:
            file_token = None

    # 4) من متغير البيئة
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    token = token_arg or file_token or env_token or TELEGRAM_BOT_TOKEN_HARDCODED
    if not token:
        print(Fore.RED + "لم يتم العثور على TELEGRAM_BOT_TOKEN. وفّر التوكن عبر --token أو متغير بيئة أو .env أو TELEGRAM_BOT_TOKEN.txt")
        sys.exit(1)

    print("تشغيل بوت تيليجرام...")
    print(Fore.CYAN + "تهيئة تطبيق تيليجرام...")
    app = ApplicationBuilder().token(token).post_init(_post_init).job_queue(UTCJobQueue()).build()
    app.add_handler(CommandHandler("start", tg_start))
    app.add_handler(CommandHandler("help", tg_help))
    app.add_handler(CommandHandler("search", tg_search_command))
    app.add_handler(CommandHandler("id", tg_id_command))
    app.add_handler(CommandHandler("setminiapp", tg_setminiapp))
    app.add_handler(CommandHandler("settings", tg_settings))
    app.add_handler(CommandHandler("about", tg_about))
    app.add_handler(CommandHandler("ping", tg_ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_on_text))
    app.add_handler(CallbackQueryHandler(tg_on_callback))
    app.add_error_handler(tg_on_error)
    print(Fore.GREEN + "يتم الآن تشغيل البوت باستخدام polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None, close_loop=False)

if __name__ == "__main__":
    main()