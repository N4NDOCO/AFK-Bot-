import discord
from discord.ext import commands, tasks
from config import TOKEN, GUILD_ID, AFK_CHANNEL_ID
import datetime

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Dicionário para armazenar usuários AFK
afk_users = {}

# ----- Evento on_ready -----
@bot.event
async def on_ready():
    print("AFK (Bot) está online!")
    afk_timer.start()  # inicia loop de atualização do timer

# ----- Comando /afk -----
@bot.tree.command(name="afk", description="Coloque-se AFK")
async def afk(interaction: discord.Interaction):
    afk_users[interaction.user.id] = datetime.datetime.utcnow()
    channel = bot.get_channel(AFK_CHANNEL_ID)
    if channel:
        await channel.send(f"⏳ | {interaction.user.mention} está AFK\n⏱️ Tempo: 00:00:00")
    await interaction.response.send_message("Você está AFK!", ephemeral=True)

# ----- Comando /unafk -----
@bot.tree.command(name="unafk", description="Volte do AFK")
async def unafk(interaction: discord.Interaction):
    if interaction.user.id in afk_users:
        del afk_users[interaction.user.id]
        channel = bot.get_channel(AFK_CHANNEL_ID)
        if channel:
            await channel.send(f"{interaction.user.mention} voltou! ✅")
        await interaction.response.send_message("Você não está mais AFK!", ephemeral=True)
    else:
        await interaction.response.send_message("Você não estava AFK.", ephemeral=True)

# ----- Loop de atualização do timer -----
@tasks.loop(seconds=10)
async def afk_timer():
    channel = bot.get_channel(AFK_CHANNEL_ID)
    if not channel:
        return

    # limpa mensagens antigas (máx 50)
    await channel.purge(limit=50)

    now = datetime.datetime.utcnow()
    for user_id, start_time in afk_users.items():
        delta = now - start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        try:
            member = await bot.fetch_user(user_id)
            await channel.send(f"⏳ | {member.mention} está AFK\n⏱️ Tempo: {hours:02d}:{minutes:02d}:{seconds:02d}")
        except Exception:
            continue

# ----- Rodar bot -----
bot.run(TOKEN)
