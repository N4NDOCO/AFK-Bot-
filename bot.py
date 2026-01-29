import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import asyncio

from config import TOKEN, GUILD_ID, AFK_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}
afk_messages = {}

# ---------------- READY ----------------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    update_afk.start()
    print("AFK (bot) online!")

# ---------------- /afk ----------------
@bot.tree.command(name="afk", description="Ficar AFK")
async def afk(interaction: discord.Interaction):
    if interaction.user.id in afk_users:
        await interaction.response.send_message(
            "Você já está AFK.", ephemeral=True
        )
        return

    channel = bot.get_channel(AFK_CHANNEL_ID)
    now = datetime.now()

    afk_users[interaction.user.id] = now

    msg = await channel.send(
        f"{interaction.user.display_name}\n"
        f"⏳ Tempo AFK: 00:00\n"
        f"🕓 Horário: {now.strftime('%H:%M')}"
    )

    afk_messages[interaction.user.id] = msg.id

    await interaction.response.send_message(
        "Você agora está AFK.", ephemeral=True
    )

# ---------------- /unafk ----------------
@bot.tree.command(name="unafk", description="Voltar do AFK")
async def unafk(interaction: discord.Interaction):
    if interaction.user.id not in afk_users:
        await interaction.response.send_message(
            "Você não está AFK.", ephemeral=True
        )
        return

    channel = bot.get_channel(AFK_CHANNEL_ID)
    msg_id = afk_messages.get(interaction.user.id)

    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.delete()
        except:
            pass

    afk_users.pop(interaction.user.id)
    afk_messages.pop(interaction.user.id)

    await interaction.response.send_message(
        "Você saiu do AFK.", ephemeral=True
    )

# ---------------- LOOP (5s) ----------------
@tasks.loop(seconds=5)
async def update_afk():
    channel = bot.get_channel(AFK_CHANNEL_ID)
    now = datetime.now()

    for user_id, start_time in afk_users.items():
        elapsed = int((now - start_time).total_seconds())
        minutes = elapsed // 60
        seconds = elapsed % 60

        msg_id = afk_messages.get(user_id)
        if not msg_id:
            continue

        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(
                content=
                f"{msg.author.display_name}\n"
                f"⏳ Tempo AFK: {minutes:02d}:{seconds:02d}\n"
                f"🕓 Horário: {start_time.strftime('%H:%M')}"
            )
        except:
            pass

# ---------------- RUN ----------------
bot.run(TOKEN)
