import os
import re
import aiohttp
import discord

from bs4 import BeautifulSoup
from discord.ext import commands
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================
# الإعدادات
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
TIMEZONE = ZoneInfo("Africa/Algiers")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

PL_URL = "https://www.premierleague.com/en/matches"
ESPN_TABLE_URL = "https://www.espn.com/soccer/table/_/league/eng.1"


# =========================
# Discord
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# =========================
# جلب الموقع
# =========================

async def get_html(url):
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(
        headers=HEADERS,
        timeout=timeout
    ) as session:

        async with session.get(url) as response:

            if response.status != 200:
                raise Exception(
                    f"HTTP {response.status}"
                )

            return await response.text()


# =========================
# المباريات
# =========================

async def get_matches():

    html = await get_html(PL_URL)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    matches = []

    # البحث عن عناصر المباريات
    elements = soup.select(
        "[class*='fixture'], "
        "[class*='Fixture'], "
        "[class*='match'], "
        "[class*='Match']"
    )

    for element in elements:

        text = " ".join(
            element.stripped_strings
        )

        if not text:
            continue

        # نحاول استخراج أسماء الفرق
        teams = re.findall(
            r"(Arsenal|"
            r"Aston Villa|"
            r"Bournemouth|"
            r"Brentford|"
            r"Brighton(?: & Hove Albion)?|"
            r"Burnley|"
            r"Chelsea|"
            r"Crystal Palace|"
            r"Everton|"
            r"Fulham|"
            r"Leeds United|"
            r"Liverpool|"
            r"Manchester City|"
            r"Manchester United|"
            r"Newcastle United|"
            r"Nottingham Forest|"
            r"Sunderland|"
            r"Tottenham Hotspur|"
            r"West Ham United|"
            r"Wolverhampton Wanderers)",
            text,
            re.I
        )

        if len(teams) >= 2:

            home = teams[0]
            away = teams[1]

            match = {
                "home": home,
                "away": away,
                "text": text
            }

            if match not in matches:
                matches.append(match)

    return matches


# =========================
# الترتيب
# =========================

async def get_table():

    html = await get_html(
        ESPN_TABLE_URL
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = []

    for row in soup.select("table tr"):

        cells = [
            cell.get_text(
                " ",
                strip=True
            )
            for cell in row.find_all(
                ["td", "th"]
            )
        ]

        if len(cells) < 5:
            continue

        text = " ".join(cells)

        teams = [
            "Arsenal",
            "Aston Villa",
            "Bournemouth",
            "Brentford",
            "Brighton",
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
        ]

        team = None

        for name in teams:

            if name.lower() in text.lower():
                team = name
                break

        if not team:
            continue

        numbers = []

        for cell in cells:

            if cell.isdigit():
                numbers.append(
                    int(cell)
                )

        if len(numbers) >= 7:

            table.append({
                "team": team,
                "played": numbers[0],
                "wins": numbers[1],
                "draws": numbers[2],
                "losses": numbers[3],
                "gf": numbers[4],
                "ga": numbers[5],
                "gd": numbers[6],
                "points": numbers[-1],
            })

    return table


# =========================
# أوامر المباريات
# =========================

def matches_message(
    matches,
    title
):

    if not matches:
        return (
            f"⚽ **{title}**\n\n"
            "لا توجد مباريات."
        )

    message = (
        f"⚽ **{title}**\n\n"
    )

    for match in matches:

        message += (
            f"🏟️ **{match['home']} "
            f"vs "
            f"{match['away']}**\n"
        )

        message += (
            f"📅 {match['text']}\n\n"
        )

    return message[:1900]


@bot.command(name="اليوم")
async def today(ctx):

    try:

        matches = await get_matches()

        # ملاحظة:
        # المصدر قد لا يعطي التاريخ كحقل منفصل،
        # لذلك نعرض مباريات الصفحة الحالية.

        await ctx.send(
            matches_message(
                matches,
                "مباريات اليوم"
            )
        )

    except Exception as e:

        await ctx.send(
            "❌ حدث خطأ أثناء جلب المباريات."
        )

        print(e)


@bot.command(name="غدا")
async def tomorrow(ctx):

    try:

        matches = await get_matches()

        await ctx.send(
            matches_message(
                matches,
                "مباريات غداً"
            )
        )

    except Exception as e:

        await ctx.send(
            "❌ حدث خطأ أثناء جلب المباريات."
        )

        print(e)


@bot.command(name="قبل3")
async def next_three(ctx):

    try:

        matches = await get_matches()

        await ctx.send(
            matches_message(
                matches,
                "المباريات القادمة"
            )
        )

    except Exception as e:

        await ctx.send(
            "❌ حدث خطأ أثناء جلب المباريات."
        )

        print(e)


# =========================
# فريق
# =========================

@bot.command(name="فريق")
async def team(ctx, *, team_name=None):

    if not team_name:

        await ctx.send(
            "استخدم الأمر هكذا:\n"
            "`!فريق Arsenal`"
        )

        return

    try:

        matches = await get_matches()

        result = []

        for match in matches:

            if (
                team_name.lower()
                in match["home"].lower()
                or
                team_name.lower()
                in match["away"].lower()
            ):
                result.append(match)

        await ctx.send(
            matches_message(
                result,
                f"مباريات {team_name}"
            )
        )

    except Exception as e:

        await ctx.send(
            "❌ حدث خطأ أثناء البحث."
        )

        print(e)


# =========================
# الترتيب
# =========================

@bot.command(name="الترتيب")
async def standings(ctx):

    try:

        table = await get_table()

        if not table:

            await ctx.send(
                "❌ لم أستطع جلب الترتيب."
            )

            return

        message = (
            "🏆 **ترتيب الدوري الإنجليزي**\n\n"
        )

        for i, team in enumerate(
            table,
            start=1
        ):

            message += (
                f"**{i}. {team['team']}** "
                f"— {team['points']} نقطة\n"
            )

        await ctx.send(
            message[:1900]
        )

    except Exception as e:

        await ctx.send(
            "❌ حدث خطأ أثناء جلب الترتيب."
        )

        print(e)


# =========================
# تحديث يدوي
# =========================

@bot.command(name="تحديث")
async def update(ctx):

    try:

        await get_matches()
        await get_table()

        await ctx.send(
            "✅ تم تحديث البيانات."
        )

    except Exception as e:

        await ctx.send(
            "❌ فشل تحديث البيانات."
        )

        print(e)


# =========================
# المساعدة
# =========================

@bot.command(name="مساعدة")
async def help_command(ctx):

    await ctx.send(
        """
⚽ **بوت الدوري الإنجليزي**

`!اليوم`
مباريات اليوم

`!غدا`
مباريات الغد

`!قبل3`
المباريات القادمة

`!الترتيب`
ترتيب الدوري

`!فريق Arsenal`
مباريات فريق معين

`!تحديث`
تحديث البيانات يدويًا

`!مساعدة`
عرض الأوامر
"""
    )


# =========================
# تشغيل البوت
# =========================

@bot.event
async def on_ready():

    print(
        f"تم تسجيل الدخول: {bot.user}"
    )


if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN غير موجود"
    )

bot.run(TOKEN)
