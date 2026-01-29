import discord
from discord.ext import commands
from discord import app_commands
import time
from config import TOKEN, GUILD_ID, AFK_CHANNEL_ID

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}  # user_id: timestamp
afk_messages = {}  # user_id: message_id


@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    # sincroniza comandos SOMENTE nesse servidor (instantâneo)
    await bot.tree.sync(guild=guild)

    print("AFK (bot) está online!")


# -------- /afk --------
@bot.tree.command(
    name="afk",
    description="Marcar você como AFK",
    guild=discord.Object(id=GUILD_ID)
)
async def afk(interaction: discord.Interaction):
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if interaction.user.id in afk_users:
        await interaction.response.send_message(
            "Você já está AFK.", ephemeral=True
        )
        return

    start_time = int(time.time())
    afk_users[interaction.user.id] = start_time

    msg = await channel.send(
        f"⏳┃ **{interaction.user.mention}** — AFK agora"
    )
    afk_messages[interaction.user.id] = msg.id

    await interaction.response.send_message(
        "Você foi marcado como AFK.", ephemeral=True
    )


# -------- /unafk --------
@bot.tree.command(
    name="unafk",
    description="Remover seu status AFK",
    guild=discord.Object(id=GUILD_ID)
)
async def unafk(interaction: discord.Interaction):
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if interaction.user.id not in afk_users:
        await interaction.response.send_message(
            "Você não está AFK.", ephemeral=True
        )
        return

    msg_id = afk_messages.get(interaction.user.id)
    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.delete()
        except:
            pass

    afk_users.pop(interaction.user.id, None)
    afk_messages.pop(interaction.user.id, None)

    await interaction.response.send_message(
        "Você saiu do AFK e está disponível.", ephemeral=True
    )


bot.run(TOKEN)
