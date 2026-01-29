import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import asyncio
import os

# ================= CONFIG =================
TOKEN = os.environ.get("TOKEN")

GUILD_ID = 1465477542919016625
AFK_CHANNEL_ID = 1466487369195720777  # ⏳┃afk-status
# =========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}  # user_id: {start, message}

# ---------- READY ----------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("AFK (bot) está online!")

    update_afk.start()

# ---------- /afk ----------
@bot.tree.command(name="afk", description="Ficar AFK (off)", guild=discord.Object(id=GUILD_ID))
async def afk(interaction: discord.Interaction):

    # RESPONDE IMEDIATO (resolve o erro)
    await interaction.response.send_message(
        "⏳ Status AFK ativado.", ephemeral=True
    )

    user = interaction.user
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if user.id in afk_users:
        return

    start = datetime.now()

    embed = discord.Embed(color=0x5865F2)
    embed.add_field(
        name=user.name,
        value="⏳ Tempo AFK: 0s\n🕓 Horário: " + start.strftime("%H:%M"),
        inline=False
    )
    embed.set_footer(text="Status: OFF")

    msg = await channel.send(embed=embed)

    afk_users[user.id] = {
        "start": start,
        "message": msg
    }

# ---------- /unafk ----------
@bot.tree.command(name="unafk", description="Voltar do AFK", guild=discord.Object(id=GUILD_ID))
async def unafk(interaction: discord.Interaction):

    await interaction.response.send_message(
        "✅ Você está disponível (ON).", ephemeral=True
    )

    data = afk_users.pop(interaction.user.id, None)
    if data:
        await data["message"].delete()

# ---------- RESET AUTOMÁTICO AO FALAR ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        data = afk_users.pop(message.author.id)
        await data["message"].delete()

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
    for user_id, data in list(afk_users.items()):
        elapsed = int((datetime.now() - data["start"]).total_seconds())
        minutes = elapsed // 60
        seconds = elapsed % 60

        embed = discord.Embed(color=0x5865F2)
        embed.add_field(
            name=data["message"].author.name,
            value=f"⏳ Tempo AFK: {minutes}m {seconds}s\n🕓 Horário: {data['start'].strftime('%H:%M')}",
            inline=False
        )
        embed.set_footer(text="Status: OFF")

        try:
            await data["message"].edit(embed=embed)
        except:
            pass

# ---------- RUN ----------
bot.run(TOKEN)
