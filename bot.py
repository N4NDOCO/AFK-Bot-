import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime
from config import TOKEN, GUILD_ID, AFK_CHANNEL_ID

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Dicionário para armazenar usuários AFK
afk_users = {}  # {user_id: start_time}

# ----- Sincronização dos comandos -----
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    try:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    print("AFK (Bot) está online!")

# ----- /afk -----
@bot.tree.command(name="afk", description="Fique AFK e apareça offline")
async def afk(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in afk_users:
        await interaction.response.send_message("Você já está AFK!", ephemeral=True)
        return

    afk_users[user_id] = datetime.utcnow()
    channel = bot.get_channel(AFK_CHANNEL_ID)
    await interaction.response.send_message("Você entrou em AFK!", ephemeral=True)
    await channel.send(f"⏳┃ {interaction.user.mention} está AFK! ⏳")

# ----- /unafk -----
@bot.tree.command(name="unafk", description="Remova o status AFK")
async def unafk(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in afk_users:
        await interaction.response.send_message("Você não está AFK!", ephemeral=True)
        return

    afk_users.pop(user_id)
    channel = bot.get_channel(AFK_CHANNEL_ID)
    await interaction.response.send_message("Você saiu do AFK!", ephemeral=True)
    await channel.send(f"✅┃ {interaction.user.mention} voltou! ✅")

# ----- Timer público de AFK -----
@tasks.loop(seconds=10)
async def update_afk_status():
    channel = bot.get_channel(AFK_CHANNEL_ID)
    if not channel:
        return

    for user_id, start_time in afk_users.items():
        user = bot.get_user(user_id)
        if user:
            delta = datetime.utcnow() - start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            hours, minutes = divmod(minutes, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            try:
                # Limpa mensagens antigas do AFK do mesmo usuário
                async for msg in channel.history(limit=50):
                    if user.mention in msg.content and "AFK!" in msg.content:
                        await msg.delete()
            except:
                pass
            await channel.send(f"⏳┃ {user.mention} está AFK há {time_str}")

@bot.event
async def on_ready():
    if not update_afk_status.is_running():
        update_afk_status.start()

# ----- Rodar bot -----
bot.run(TOKEN)
