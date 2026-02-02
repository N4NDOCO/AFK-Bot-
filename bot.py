import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import os

# ================= CONFIG =================
TOKEN = os.environ.get("AFK_TOKEN")  # token do bot AFK

GUILD_ID = 1465477542919016625
AFK_CHANNEL_ID = 1466487369195720777

BR_TZ = timezone(timedelta(hours=-3))
ONLINE_GAP = 900  # 15 minutos
MAX_DISCOUNT = 20
# =========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}
afk_totals = {}
last_message_time = {}
online_seconds = {}

# ---------- UTILS ----------
def format_time(seconds: int):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_user_discount(user_id: int) -> int:
    hours = online_seconds.get(user_id, 0) // 3600
    return min(hours, MAX_DISCOUNT)

# ---------- READY ----------
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    update_afk.start()
    print("AFK bot online!")

# ---------- /afk ----------
@bot.tree.command(name="afk", description="Ficar AFK", guild=discord.Object(id=GUILD_ID))
async def afk(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Você está AFK.", ephemeral=True)

    user = interaction.user
    if user.id in afk_users:
        return

    channel = bot.get_channel(AFK_CHANNEL_ID)
    if not channel:
        return

    start = datetime.now(BR_TZ)

    afk_totals.setdefault(user.id, 0)
    online_seconds.setdefault(user.id, 0)

    embed = discord.Embed(title=user.display_name, color=0x5865F2)
    embed.add_field(
        name="Status AFK",
        value=f"⏳ Tempo AFK: 0s\n🕓 Horário: {start.strftime('%H:%M:%S')}",
        inline=False
    )
    embed.add_field(
        name="Total",
        value=format_time(afk_totals[user.id]),
        inline=False
    )
    embed.add_field(
        name="💸 Desconto",
        value=f"{get_user_discount(user.id)}%",
        inline=False
    )
    embed.set_footer(text="Status: OFF")

    msg = await channel.send(embed=embed)

    afk_users[user.id] = {"start": start, "message": msg, "name": user.display_name}

# ---------- /unafk ----------
@bot.tree.command(name="unafk", description="Voltar do AFK", guild=discord.Object(id=GUILD_ID))
async def unafk(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Você voltou.", ephemeral=True)

    data = afk_users.pop(interaction.user.id, None)
    if data:
        elapsed = int((datetime.now(BR_TZ) - data["start"]).total_seconds())
        afk_totals[interaction.user.id] += elapsed
        await data["message"].delete()

# ---------- ON MESSAGE ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = datetime.now(BR_TZ)

    if uid in last_message_time:
        gap = (now - last_message_time[uid]).total_seconds()
        if gap <= ONLINE_GAP:
            online_seconds[uid] = online_seconds.get(uid, 0) + gap

    last_message_time[uid] = now

    if uid in afk_users:
        data = afk_users.pop(uid)
        elapsed = int((now - data["start"]).total_seconds())
        afk_totals[uid] += elapsed

        try:
            await data["message"].delete()
        except:
            pass

        await message.channel.send(f"✅ {message.author.mention} saiu do AFK.")

    await bot.process_commands(message)

# ---------- UPDATE EMBEDS ----------
@tasks.loop(seconds=5)
async def update_afk():
    now = datetime.now(BR_TZ)

    for uid, data in afk_users.items():
        elapsed = int((now - data["start"]).total_seconds())

        embed = discord.Embed(title=data["name"], color=0x5865F2)
        embed.add_field(
            name="Status AFK",
            value=f"⏳ Tempo AFK: {format_time(elapsed)}\n🕓 Horário: {data['start'].strftime('%H:%M:%S')}",
            inline=False
        )
        embed.add_field(
            name="Total",
            value=format_time(afk_totals.get(uid, 0) + elapsed),
            inline=False
        )
        embed.add_field(
            name="💸 Desconto",
            value=f"{get_user_discount(uid)}%",
            inline=False
        )
        embed.set_footer(text="Status: OFF")

        await data["message"].edit(embed=embed)

# ---------- RUN ----------
bot.run(TOKEN)
