import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio

from config import TOKEN, GUILD_ID, AFK_CHANNEL_ID

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

afk_users = {}  # user_id: {start_time, message_id}

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    update_afk.start()

# ---------------- AFK ----------------

@bot.tree.command(name="afk", description="Ficar AFK", guild=discord.Object(id=GUILD_ID))
async def afk(interaction: discord.Interaction):
    user = interaction.user
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if user.id in afk_users:
        await interaction.response.send_message(
            "Você já está AFK.", ephemeral=True
        )
        return

    start_time = datetime.now()

    embed = discord.Embed(color=0x5865F2)
    embed.add_field(name=user.name, value="⏳ Tempo AFK: 0s", inline=False)
    embed.add_field(
        name="🕓 Horário",
        value=start_time.strftime("%H:%M"),
        inline=False,
    )

    msg = await channel.send(embed=embed)

    afk_users[user.id] = {
        "start_time": start_time,
        "message_id": msg.id,
    }

    await interaction.response.send_message(
        "Status AFK ativado.", ephemeral=True
    )

# ---------------- UNAFK ----------------

@bot.tree.command(name="unafk", description="Sair do AFK", guild=discord.Object(id=GUILD_ID))
async def unafk(interaction: discord.Interaction):
    user = interaction.user
    channel = bot.get_channel(AFK_CHANNEL_ID)

    if user.id not in afk_users:
        await interaction.response.send_message(
            "Você não está AFK.", ephemeral=True
        )
        return

    data = afk_users.pop(user.id)
    msg = await channel.fetch_message(data["message_id"])
    await msg.delete()

    await interaction.response.send_message(
        "Status AFK removido. Você está disponível.", ephemeral=True
    )

# ---------------- ATUALIZA TEMPO ----------------

@tasks.loop(seconds=5)
async def update_afk():
    channel = bot.get_channel(AFK_CHANNEL_ID)

    for user_id, data in afk_users.items():
        try:
            msg = await channel.fetch_message(data["message_id"])
            elapsed = int((datetime.now() - data["start_time"]).total_seconds())

            minutes = elapsed // 60
            seconds = elapsed % 60

            embed = discord.Embed(color=0x5865F2)
            embed.add_field(
                name=msg.embeds[0].fields[0].name,
                value=f"⏳ Tempo AFK: {minutes}m {seconds}s",
                inline=False,
            )
            embed.add_field(
                name="🕓 Horário",
                value=data["start_time"].strftime("%H:%M"),
                inline=False,
            )

            await msg.edit(embed=embed)
        except:
            pass

# ---------------- RUN ----------------

bot.run(TOKEN)
