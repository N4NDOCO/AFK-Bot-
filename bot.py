import discord
from discord.ext import commands
from discord import app_commands
import time
from config import TOKEN, GUILD_ID, AFK_CHANNEL_ID

intents = discord.Intents.default()
intents.members = True

# PREFIX = /
bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("AFK (bot) está online!")

# ─── /afk ─────────────────────────────
@bot.tree.command(name="afk", description="Ficar AFK")
async def afk(interaction: discord.Interaction):
    channel = bot.get_channel(AFK_CHANNEL_ID)
    afk_users[interaction.user.id] = time.time()

    await channel.send(
        f"⏳┃ **AFK**\n"
        f"👤 {interaction.user.mention}\n"
        f"⏱️ Agora está AFK"
    )
    await interaction.response.send_message(
        "Você entrou em AFK.", ephemeral=True
    )

# ─── /unafk ────────────────────────────
@bot.tree.command(name="unafk", description="Sair do AFK")
async def unafk(interaction: discord.Interaction):
    channel = bot.get_channel(AFK_CHANNEL_ID)

    start = afk_users.pop(interaction.user.id, None)
    if not start:
        await interaction.response.send_message(
            "Você não está AFK.", ephemeral=True
        )
        return

    tempo = int(time.time() - start)
    minutos = tempo // 60
    segundos = tempo % 60

    await channel.send(
        f"✅┃ **ON**\n"
        f"👤 {interaction.user.mention}\n"
        f"⏱️ AFK por {minutos}m {segundos}s"
    )

    await interaction.response.send_message(
        "Você saiu do AFK.", ephemeral=True
    )

bot.run(TOKEN)
