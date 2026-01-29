import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
import os

# ================= CONFIG =================
TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465477542919016625
AFK_CHANNEL_ID = 1466487369195720777  # ⏳┃afk-status

BR_TZ = timezone(timedelta(hours=-3))  # Fuso horário Brasil
# =========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# user_id: {start, message}
afk_users = {}

# ---------- READY ----------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    update_afk.start()
    print("AFK (bot) está online!")

# ---------- /afk ----------
@bot.tree.command(
    name="afk",
    description="Ficar AFK (OFF)",
    guild=discord.Object(id=GUILD_ID)
)
async def afk(interaction: discord.Interaction):
    # responde rápido (evita timeout)
    await interaction.response.send_message(
        "⏳ Você está **AFK (OFF)**.", ephemeral=True
    )

    user = interaction.user
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if not channel:
        return

    if user.id in afk_users:
        return

    start = datetime.now(BR_TZ)

    embed = discord.Embed(color=0x5865F2)
    embed.add_field(
        name=user.name,
        value=(
            "⏳ Tempo AFK: 0s\n"
            f"🕓 Horário: {start.strftime('%H:%M')}"
        ),
        inline=False
    )
    embed.set_footer(text="Status: OFF")

    msg = await channel.send(embed=embed)

    afk_users[user.id] = {
        "start": start,
        "message": msg
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
        await data["message"].delete()

# ---------- RESET AO FALAR ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        data = afk_users.pop(message.author.id)

        try:
            await data["message"].delete()
        except:
            pass

        try:
            await message.channel.send(
                f"✅ {message.author.mention} voltou e está **ON**."
            )
        except:
            pass

    await bot.process_commands(message)

# ---------- ATUALIZA TIMER ----------
@tasks.loop(seconds=5)
async def update_afk():
    now = datetime.now(BR_TZ)

    for user_id, data in list(afk_users.items()):
        elapsed = int((now - data["start"]).total_seconds())
        minutes = elapsed // 60
        seconds = elapsed % 60

        embed = discord.Embed(color=0x5865F2)
        embed.add_field(
            name=data["message"].author.name,
            value=(
                f"⏳ Tempo AFK: {minutes}m {seconds}s\n"
                f"🕓 Horário: {data['start'].strftime('%H:%M')}"
            ),
            inline=False
        )
        embed.set_footer(text="Status: OFF")

        try:
            await data["message"].edit(embed=embed)
        except:
            pass

# ---------- RUN ----------
bot.run(TOKEN)
