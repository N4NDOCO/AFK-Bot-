import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import os

# ================= CONFIG =================
TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465477542919016625
AFK_CHANNEL_ID = 1466487369195720777  # ⏳┃afk-status

BR_TZ = timezone(timedelta(hours=-3))
RESET_DAY = 28
# =========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# user_id: {start, message, name}
afk_users = {}

# user_id: total_seconds
afk_totals = {}

last_reset_month = datetime.now(BR_TZ).month

# ---------- READY ----------
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    update_afk.start()
    check_reset.start()
    print("AFK (bot) está online!")

# ---------- FORMAT TIME ----------
def format_time(seconds: int):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

# ---------- RANKING ----------
def get_ranking():
    ranking = sorted(afk_totals.items(), key=lambda x: x[1], reverse=True)
    return ranking[:3]

# ---------- /afk ----------
@bot.tree.command(
    name="afk",
    description="Ficar AFK (OFF)",
    guild=discord.Object(id=GUILD_ID)
)
async def afk(interaction: discord.Interaction):
    await interaction.response.send_message(
        "⏳ Você está **AFK (OFF)**.", ephemeral=True
    )

    user = interaction.user
    channel = bot.get_channel(AFK_CHANNEL_ID)
    if not channel or user.id in afk_users:
        return

    start = datetime.now(BR_TZ)
    afk_totals.setdefault(user.id, 0)

    embed = discord.Embed(
        title=user.display_name,
        color=0x5865F2
    )
    embed.add_field(
        name="Status AFK",
        value=(
            "⏳ Tempo AFK: 0h 0m 0s\n"
            f"🕓 Horário: {start.strftime('%H:%M:%S')}"
        ),
        inline=False
    )
    embed.add_field(
        name="Total",
        value=format_time(afk_totals[user.id]),
        inline=False
    )
    embed.add_field(
        name="Ranking",
        value="Calculando...",
        inline=False
    )
    embed.set_footer(text="Status: OFF")

    msg = await channel.send(embed=embed)

    afk_users[user.id] = {
        "start": start,
        "message": msg,
        "name": user.display_name
    }

# ---------- /unafk ----------
@bot.tree.command(
    name="unafk",
    description="Voltar do AFK (ON)",
    guild=discord.Object(id=GUILD_ID)
)
async def unafk(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ Você está **ON** novamente.", ephemeral=True
    )

    data = afk_users.pop(interaction.user.id, None)
    if data:
        elapsed = int((datetime.now(BR_TZ) - data["start"]).total_seconds())
        afk_totals[interaction.user.id] += elapsed
        await data["message"].delete()

# ---------- SAIR AO FALAR ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        data = afk_users.pop(message.author.id)
        elapsed = int((datetime.now(BR_TZ) - data["start"]).total_seconds())
        afk_totals[message.author.id] += elapsed

        try:
            await data["message"].delete()
        except:
            pass

        await message.channel.send(
            f"✅ {message.author.mention} saiu do **AFK** e está **ON**."
        )

    await bot.process_commands(message)

# ---------- UPDATE EMBEDS ----------
@tasks.loop(seconds=5)
async def update_afk():
    now = datetime.now(BR_TZ)
    ranking = get_ranking()

    ranking_text = ""
    for i, (uid, total) in enumerate(ranking, start=1):
        ranking_text += f"**Top {i}** <@{uid}> — {format_time(total)}\n"

    if not ranking_text:
        ranking_text = "Sem dados ainda."

    for uid, data in afk_users.items():
        elapsed = int((now - data["start"]).total_seconds())

        embed = discord.Embed(
            title=data["name"],
            color=0x5865F2
        )
        embed.add_field(
            name="Status AFK",
            value=(
                f"⏳ Tempo AFK: {format_time(elapsed)}\n"
                f"🕓 Horário: {data['start'].strftime('%H:%M:%S')}"
            ),
            inline=False
        )
        embed.add_field(
            name="Total",
            value=format_time(afk_totals.get(uid, 0) + elapsed),
            inline=False
        )
        embed.add_field(
            name="Ranking",
            value=ranking_text,
            inline=False
        )
        embed.set_footer(text="Status: OFF")

        try:
            await data["message"].edit(embed=embed)
        except:
            pass

# ---------- RESET MENSAL ----------
@tasks.loop(minutes=1)
async def check_reset():
    global last_reset_month
    now = datetime.now(BR_TZ)

    if now.day == RESET_DAY and now.month != last_reset_month:
        afk_totals.clear()
        last_reset_month = now.month
        print("🔄 Ranking AFK resetado!")

# ---------- RUN ----------
bot.run(TOKEN)
