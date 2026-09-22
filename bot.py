import os
import json
import asyncio
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp
import discord
from discord.ext import commands, tasks
from bs4 import BeautifulSoup


# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

CHECK_INTERVAL_MINUTES = 5
TIMEZONE = ZoneInfo("Africa/Algiers")

PL_FIXTURES_URL = (
    "https://www.premierleague.com/en/matches/"
    "premier-league/2026-27"
)

ESPN_TABLE_URL = (
    "https://www.espn.com/soccer/table/_/league/eng.1"
)

DATA_FILE = "cache.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/140 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("pl-bot")


# =========================================================
# DISCORD
# =========================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# =========================================================
# CACHE
# =========================================================

def load_cache():
    if not os.path.exists(DATA_FILE):
        return {
            "fixtures": [],
            "table": [],
            "last_update": None
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "fixtures": [],
            "table": [],
            "last_update": None
        }


def save_cache(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


cache = load_cache()


# =========================================================
# HTTP
# =========================================================

async def fetch_html(url):
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(
        headers=HEADERS,
        timeout=timeout
    ) as session:

        async with session.get(url) as response:

            if response.status != 200:
                raise RuntimeError(
                    f"HTTP {response.status}: {url}"
                )

            return await response.text()


# =========================================================
# HELPERS
# =========================================================

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def parse_date(text):
    """
    يحاول تحويل التاريخ من عدة صيغ.
    """

    formats = [
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    return None


def team_match(team, query):
    team = team.lower()
    query = query.lower()

    aliases = {
        "man utd": "manchester united",
        "man united": "manchester united",
        "man city": "manchester city",
        "spurs": "tottenham",
        "tottenham": "tottenham hotspur",
        "wolves": "wolverhampton",
        "nott'm forest": "nottingham forest",
        "forest": "nottingham forest",
        "brighton": "brighton & hove albion",
        "newcastle": "newcastle united",
        "villa": "aston villa",
        "west ham": "west ham united",
        "leeds": "leeds united",
        "arsenal": "arsenal",
        "liverpool": "liverpool",
        "chelsea": "chelsea",
    }

    query = aliases.get(query, query)

    return (
        query in team
        or team in query
    )


# =========================================================
# PREMIER LEAGUE SCRAPER
# =========================================================

async def scrape_premier_league():

    html = await fetch_html(PL_FIXTURES_URL)

    soup = BeautifulSoup(html, "html.parser")

    fixtures = []

    # -----------------------------------------------------
    # محاولة قراءة البيانات الموجودة في الصفحة
    # -----------------------------------------------------

    text = soup.get_text(" ", strip=True)

    # نبحث عن عناصر المباريات المحتملة.
    # تصميم PL قد يتغير، لذلك توجد عدة selectors.
    selectors = [
        "[data-testid*='fixture']",
        "[class*='fixture']",
        "[class*='Fixture']",
        "[class*='match']",
        "[class*='Match']",
    ]

    elements = []

    for selector in selectors:
        found = soup.select(selector)

        if found:
            elements.extend(found)

    # إزالة التكرار
    unique = []

    seen = set()

    for element in elements:

        value = clean_text(element.get_text(" ", strip=True))

        if not value:
            continue

        if value in seen:
            continue

        seen.add(value)
        unique.append(value)

    # -----------------------------------------------------
    # محاولة استخراج المباريات من النص
    # -----------------------------------------------------

    team_names = [
        "Arsenal",
        "Aston Villa",
        "Bournemouth",
        "Brentford",
        "Brighton",
        "Burnley",
        "Chelsea",
        "Crystal Palace",
        "Everton",
        "Fulham",
        "Leeds United",
        "Liverpool",
        "Manchester City",
        "Manchester United",
        "Newcastle United",
        "Nottingham Forest",
        "Sunderland",
        "Tottenham Hotspur",
        "West Ham United",
        "Wolverhampton Wanderers",
        "Coventry City",
        "Hull City",
        "Ipswich Town",
    ]

    # -----------------------------------------------------
    # البحث عن JSON مضمّن في الصفحة
    # -----------------------------------------------------

    scripts = soup.find_all("script")

    json_strings = []

    for script in scripts:

        content = script.string

        if not content:
            continue

        if "Arsenal" in content or "Liverpool" in content:
            json_strings.append(content)

    # محاولة عامة لاستخراج أزواج الفرق
    for script_text in json_strings:

        for home in team_names:

            for away in team_names:

                if home == away:
                    continue

                pattern = (
                    rf'"(?:homeTeam|home|name)"\s*:\s*'
                    rf'"{re.escape(home)}".{{0,1500}}?'
                    rf'"(?:awayTeam|away|name)"\s*:\s*'
                    rf'"{re.escape(away)}"'
                )

                if re.search(
                    pattern,
                    script_text,
                    flags=re.IGNORECASE | re.DOTALL
                ):

                    key = f"{home}|{away}"

                    if not any(
                        f"{x['home']}|{x['away']}" == key
                        for x in fixtures
                    ):
                        fixtures.append({
                            "home": home,
                            "away": away,
                            "date": None,
                            "status": "مجدولة",
                            "score": None,
                            "source": "Premier League"
                        })

    # -----------------------------------------------------
    # fallback
    # -----------------------------------------------------

    if not fixtures:
        log.warning(
            "Premier League scraper returned no structured fixtures."
        )

    return fixtures


# =========================================================
# ESPN TABLE SCRAPER
# =========================================================

async def scrape_espn_table():

    html = await fetch_html(ESPN_TABLE_URL)

    soup = BeautifulSoup(html, "html.parser")

    rows = []

    # ESPN يستخدم جدول standings
    table_rows = soup.select("table tr")

    for tr in table_rows:

        cells = [
            clean_text(td.get_text(" ", strip=True))
            for td in tr.find_all(["td", "th"])
        ]

        if len(cells) < 5:
            continue

        text = " ".join(cells)

        # نحاول العثور على فريق PL
        known_team = None

        for team in [
            "Arsenal",
            "Aston Villa",
            "Bournemouth",
            "Brentford",
            "Brighton & Hove Albion",
            "Chelsea",
            "Crystal Palace",
            "Everton",
            "Fulham",
            "Leeds United",
            "Liverpool",
            "Manchester City",
            "Manchester United",
            "Newcastle United",
            "Nottingham Forest",
            "Sunderland",
            "Tottenham Hotspur",
            "West Ham United",
            "Wolverhampton Wanderers",
            "Coventry City",
            "Hull City",
            "Ipswich Town",
        ]:

            if team.lower() in text.lower():
                known_team = team
                break

        if not known_team:
            continue

        numbers = []

        for cell in cells:
            if re.fullmatch(r"-?\d+", cell):
                numbers.append(int(cell))

        if len(numbers) >= 7:

            rows.append({
                "team": known_team,
                "played": numbers[0],
                "wins": numbers[1],
                "draws": numbers[2],
                "losses": numbers[3],
                "gf": numbers[4],
                "ga": numbers[5],
                "gd": numbers[6],
                "points": numbers[7] if len(numbers) > 7 else 0,
            })

    # إذا لم نستطع القراءة
    if not rows:
        log.warning("ESPN table scraper returned no rows.")

    # ترتيب حسب النقاط
    rows.sort(
        key=lambda x: (
            x["points"],
            x["gd"],
            x["gf"]
        ),
        reverse=True
    )

    return rows


# =========================================================
# DATA UPDATE
# =========================================================

async def update_data():

    global cache

    old_fixtures = cache.get("fixtures", [])
    old_table = cache.get("table", [])

    try:
        new_fixtures = await scrape_premier_league()
    except Exception as e:

        log.exception(
            "Premier League scraping failed: %s",
            e
        )

        new_fixtures = old_fixtures

    try:
        new_table = await scrape_espn_table()
    except Exception as e:

        log.exception(
            "ESPN scraping failed: %s",
            e
        )

        new_table = old_table

    changed = (
        new_fixtures != old_fixtures
        or new_table != old_table
    )

    cache = {
        "fixtures": new_fixtures,
        "table": new_table,
        "last_update": datetime.now(
            TIMEZONE
        ).isoformat()
    }

    save_cache(cache)

    return changed


# =========================================================
# FIXTURE FILTERS
# =========================================================

def get_today_fixtures():

    today = datetime.now(TIMEZONE).date()

    result = []

    for match in cache["fixtures"]:

        date_text = match.get("date")

        if not date_text:
            continue

        try:
            dt = datetime.fromisoformat(date_text)

            if dt.date() == today:
                result.append(match)

        except Exception:
            pass

    return result


def get_tomorrow_fixtures():

    tomorrow = (
        datetime.now(TIMEZONE).date()
        + timedelta(days=1)
    )

    result = []

    for match in cache["fixtures"]:

        date_text = match.get("date")

        if not date_text:
            continue

        try:
            dt = datetime.fromisoformat(date_text)

            if dt.date() == tomorrow:
                result.append(match)

        except Exception:
            pass

    return result


def get_next_days(days=3):

    now = datetime.now(TIMEZONE)

    end = now + timedelta(days=days)

    result = []

    for match in cache["fixtures"]:

        date_text = match.get("date")

        if not date_text:
            continue

        try:
            dt = datetime.fromisoformat(date_text)

            if now <= dt <= end:
                result.append(match)

        except Exception:
            pass

    return result


# =========================================================
# DISCORD FORMATTING
# =========================================================

def format_match(match):

    home = match.get("home", "?")
    away = match.get("away", "?")

    score = match.get("score")

    status = match.get("status", "مجدولة")

    date_text = match.get("date")

    if score:
        result = f"**{home} {score} {away}**"
    else:
        result = f"**{home} vs {away}**"

    if date_text:

        try:
            dt = datetime.fromisoformat(date_text)

            result += (
                f"\n🕐 {dt.astimezone(TIMEZONE):%d/%m %H:%M}"
            )

        except Exception:
            pass

    result += f"\n📌 {status}"

    return result


def format_matches(matches, title):

    if not matches:
        return f"⚽ **{title}**\n\nلا توجد مباريات."

    text = f"⚽ **{title}**\n\n"

    for match in matches[:20]:

        text += format_match(match)
        text += "\n\n"

    return text


# =========================================================
# COMMANDS
# =========================================================

@bot.command(name="اليوم")
async def today(ctx):

    await update_data()

    matches = get_today_fixtures()

    await ctx.send(
        format_matches(
            matches,
            "مباريات اليوم"
        )
    )


@bot.command(name="غدا")
async def tomorrow(ctx):

    await update_data()

    matches = get_tomorrow_fixtures()

    await ctx.send(
        format_matches(
            matches,
            "مباريات غداً"
        )
    )


@bot.command(name="قبل3")
async def next_three(ctx):

    await update_data()

    matches = get_next_days(3)

    await ctx.send(
        format_matches(
            matches,
            "المباريات القادمة"
        )
    )


@bot.command(name="مباشر")
async def live(ctx):

    await update_data()

    live_matches = []

    for match in cache["fixtures"]:

        status = str(
            match.get("status", "")
        ).lower()

        if any(
            word in status
            for word in [
                "live",
                "مباشر",
                "half",
                "ht",
                "45",
                "90"
            ]
        ):
            live_matches.append(match)

    await ctx.send(
        format_matches(
            live_matches,
            "المباريات المباشرة"
        )
    )


@bot.command(name="الترتيب")
async def table(ctx):

    await update_data()

    rows = cache.get("table", [])

    if not rows:

        await ctx.send(
            "❌ لم أستطع الحصول على جدول الدوري حالياً."
        )

        return

    message = "🏆 **ترتيب الدوري الإنجليزي**\n\n"

    for index, row in enumerate(rows, start=1):

        message += (
            f"**{index}. {row['team']}** — "
            f"{row['points']} نقطة "
            f"({row['played']} مباراة)\n"
        )

    # Discord message limit
    await ctx.send(message[:1900])


@bot.command(name="فريق")
async def team(ctx, *, team_name=None):

    if not team_name:

        await ctx.send(
            "استخدم:\n`!فريق Arsenal`\n"
            "أو\n"
            "`!فريق Liverpool`"
        )

        return

    await update_data()

    matches = []

    for match in cache["fixtures"]:

        if (
            team_match(
                match.get("home", ""),
                team_name
            )
            or
            team_match(
                match.get("away", ""),
                team_name
            )
        ):
            matches.append(match)

    if not matches:

        await ctx.send(
            f"❌ لم أجد مباريات للفريق: `{team_name}`"
        )

        return

    await ctx.send(
        format_matches(
            matches[:10],
            f"مباريات {team_name}"
        )
    )


@bot.command(name="تحديث")
async def manual_update(ctx):

    changed = await update_data()

    if changed:

        await ctx.send(
            "🔄 تم تحديث البيانات ووجدت تغييرات جديدة."
        )

    else:

        await ctx.send(
            "✅ تم الفحص. لا توجد تغييرات."
        )


# =========================================================
# HELP
# =========================================================

@bot.command(name="مساعدة")
async def help_command(ctx):

    text = """
⚽ **Premier League Bot**

`!اليوم`
مباريات اليوم

`!غدا`
مباريات الغد

`!قبل3`
المباريات القادمة خلال 3 أيام

`!مباشر`
المباريات المباشرة

`!الترتيب`
جدول الدوري

`!فريق Arsenal`
مباريات فريق معين

`!تحديث`
إجبار البوت على تحديث البيانات

`!مساعدة`
عرض هذه القائمة
"""

    await ctx.send(text)


# =========================================================
# AUTO UPDATE
# =========================================================

@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def automatic_update():

    try:

        changed = await update_data()

        if changed:

            log.info(
                "New Premier League data detected."
            )

            # ------------------------------------------------
            # إذا أردت إرسال إشعار تلقائي:
            #
            # ضع CHANNEL_ID في Render
            # ------------------------------------------------

            channel_id = os.getenv("CHANNEL_ID")

            if channel_id:

                channel = bot.get_channel(
                    int(channel_id)
                )

                if channel:

                    await channel.send(
                        "🔄 **تم تحديث بيانات الدوري الإنجليزي.**\n"
                        "استخدم `!اليوم` أو `!قبل3` لعرض البيانات."
                    )

        else:

            log.info(
                "No changes detected."
            )

    except Exception as e:

        log.exception(
            "Automatic update failed: %s",
            e
        )


@automatic_update.before_loop
async def before_automatic_update():

    await bot.wait_until_ready()


# =========================================================
# BOT EVENTS
# =========================================================

@bot.event
async def on_ready():

    log.info(
        "Logged in as %s (%s)",
        bot.user,
        bot.user.id
    )

    if not automatic_update.is_running():

        automatic_update.start()


# =========================================================
# START
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN is not configured."
    )


bot.run(TOKEN)
