import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
import os

# ================= CONFIG FIXA =================
TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465477542919016625          # ID DO SEU SERVIDOR
AFK_CHANNEL_ID = 1466487369195720777    # ⏳┃afk-status
# ==============================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}  # user_id: {start, message_id, channel_id}

# ---------- READY ----------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    update_afk.start()
    print("AFK Bot está online!")

# ---------- /afk ----------
@bot.tree.command(name="afk", description="Ficar AFK (off)")
async def afk(interaction: discord.Interaction):
    user = interaction.user
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if user.id in afk_users:
        await interaction.response.send_message(
            "Você já está AFK.", ephemeral=True
        )
        return

    start_time = int(time.time())
    start_clock = time.strftime("%H:%M", time.localtime(start_time))

    msg = await channel.send(
        f"**{user.display_name}**\n"
        f"⏳ Tempo AFK: 0s\n"
        f"🕓 Horário: {start_clock}"
    )

    afk_users[user.id] = {
        "start": start_time,
        "message_id": msg.id,
        "channel_id": channel.id
    }

    await interaction.response.send_message(
        "Você está AFK.", ephemeral=True
    )

# ---------- /unafk ----------
@bot.tree.command(name="unafk", description="Voltar do AFK (on)")
async def unafk(interaction: discord.Interaction):
    user = interaction.user

    if user.id not in afk_users:
        await interaction.response.send_message(
            "Você não está AFK.", ephemeral=True
        )
        return

    data = afk_users.pop(user.id)
    channel = bot.get_channel(data["channel_id"])

    try:
        msg = await channel.fetch_message(data["message_id"])
        await msg.delete()
    except:
        pass

    await interaction.response.send_message(
        "Você está disponível (ON).", ephemeral=True
    )

# ---------- AUTO SAIR DO AFK AO FALAR ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        data = afk_users.pop(message.author.id)
        channel = bot.get_channel(data["channel_id"])

        try:
            msg = await channel.fetch_message(data["message_id"])
            await msg.delete()
        except:
            pass

    await bot.process_commands(message)

# ---------- ATUALIZAR TEMPO A CADA 5s ----------
@tasks.loop(seconds=5)
async def update_afk():
    for user_id, data in list(afk_users.items()):
        channel = bot.get_channel(data["channel_id"])
        try:
            msg = await channel.fetch_message(data["message_id"])
            elapsed = int(time.time()) - data["start"]

            minutes = elapsed // 60
            seconds = elapsed % 60

            await msg.edit(
                content=
                f"**{msg.author.display_name}**\n"
                f"⏳ Tempo AFK: {minutes}m {seconds}s\n"
                f"🕓 Horário: {time.strftime('%H:%M', time.localtime(data['start']))}"
            )
        except:
            pass

# ---------- RUN ----------
bot.run(TOKEN)
