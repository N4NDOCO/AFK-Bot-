import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import os
import sys

# ================= CONFIG =================
TOKEN = os.environ.get("TOKEN")

if not TOKEN or not isinstance(TOKEN, str):
    print("❌ ERRO: TOKEN não definido ou inválido")
    sys.exit(1)

GUILD_ID = 1465477542919016625
AFK_CHANNEL_ID = 1466487369195720777

BR_TZ = timezone(timedelta(hours=-3))

STAFF_ROLES = ["Entregador", "Mod", "Staff"]
# =========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ================= DADOS =================
afk_users = {}          # user_id: {start, message, name}
afk_totals = {}         # user_id: total_seconds

user_discounts = {}     # user_id: desconto %
used_codes = {}         # user_id: set(codigos_usados)

VALID_CODES = {
    "START_SEVER": 2,
    "BEST_STORE01": 3,
    "START_SEVER_2.0": 5
}

# ================= UTILS =================
def format_time(seconds: int):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

def has_staff_role(member: discord.Member) -> bool:
    return any(role.name in STAFF_ROLES for role in member.roles)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    update_afk.start()
    print("🟢 AFK bot online!")

# ================= /AFK =================
@bot.tree.command(name="afk", description="Ficar AFK", guild=discord.Object(id=GUILD_ID))
async def afk(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Você está AFK.", ephemeral=True)

    user = interaction.user
    uid = user.id

    if uid in afk_users:
        return

    channel = bot.get_channel(AFK_CHANNEL_ID)
    if not channel:
        return

    start = datetime.now(BR_TZ)

    afk_totals.setdefault(uid, 0)
    user_discounts.setdefault(uid, 0)

    embed = discord.Embed(title=user.display_name, color=0x5865F2)
    embed.add_field(
        name="Status AFK",
        value=f"⏳ Tempo AFK: 0s\n🕓 Horário: {start.strftime('%H:%M:%S')}",
        inline=False
    )
    embed.add_field(
        name="Total AFK",
        value=format_time(afk_totals[uid]),
        inline=False
    )
    embed.set_footer(text="Status: OFF")

    msg = await channel.send(embed=embed)

    afk_users[uid] = {
        "start": start,
        "message": msg,
        "name": user.display_name
    }

# ================= /UNAFK =================
@bot.tree.command(name="unafk", description="Voltar do AFK", guild=discord.Object(id=GUILD_ID))
async def unafk(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Դուք voltou.", ephemeral=True)

    uid = interaction.user.id
    data = afk_users.pop(uid, None)

    if data:
        elapsed = int((datetime.now(BR_TZ) - data["start"]).total_seconds())
        afk_totals[uid] += elapsed
        await data["message"].delete()

# ================= /CODE =================
@bot.tree.command(name="code", description="Usar um código de desconto", guild=discord.Object(id=GUILD_ID))
async def code(interaction: discord.Interaction, codigo: str):
    codigo = codigo.upper()
    uid = interaction.user.id

    if codigo not in VALID_CODES:
        await interaction.response.send_message("❌ Código inválido.", ephemeral=True)
        return

    used_codes.setdefault(uid, set())
    user_discounts.setdefault(uid, 0)

    if codigo in used_codes[uid]:
        await interaction.response.send_message(
            "⚠️ Você já usou esse código.",
            ephemeral=True
        )
        return

    novo_desconto = VALID_CODES[codigo]

    if novo_desconto > user_discounts[uid]:
        user_discounts[uid] = novo_desconto

    used_codes[uid].add(codigo)

    await interaction.response.send_message(
        f"🎉 Código **{codigo}** aplicado!\n💸 Desconto atual: **{user_discounts[uid]}%**",
        ephemeral=True
    )

# ================= /DESCONTO =================
@bot.tree.command(name="desconto", description="Ver desconto de um usuário", guild=discord.Object(id=GUILD_ID))
async def desconto(interaction: discord.Interaction, usuario: discord.Member):
    desconto = user_discounts.get(usuario.id, 0)
    await interaction.response.send_message(
        f"💸 {usuario.mention} possui **{desconto}%** de desconto.",
        ephemeral=True
    )

# ================= /DESCONTO_TIRAR =================
@bot.tree.command(name="desconto_tirar", description="Resetar desconto (STAFF)", guild=discord.Object(id=GUILD_ID))
async def desconto_tirar(interaction: discord.Interaction, usuario: discord.Member):
    if not has_staff_role(interaction.user):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        return

    user_discounts[usuario.id] = 0
    used_codes[usuario.id] = set()

    await interaction.response.send_message(
        f"🔄 Desconto de {usuario.mention} resetado.",
        ephemeral=True
    )

# ================= ON MESSAGE =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    now = datetime.now(BR_TZ)

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

# ================= UPDATE EMBEDS =================
@tasks.loop(seconds=5)
async def update_afk():
    now = datetime.now(BR_TZ)

    for uid, data in afk_users.items():
        elapsed = int((now - data["start"]).total_seconds())
        total = afk_totals.get(uid, 0) + elapsed

        embed = discord.Embed(title=data["name"], color=0x5865F2)
        embed.add_field(
            name="Status AFK",
            value=f"⏳ Tempo AFK: {format_time(elapsed)}\n🕓 Horário: {data['start'].strftime('%H:%M:%S')}",
            inline=False
        )
        embed.add_field(
            name="Total AFK",
            value=format_time(total),
            inline=False
        )
        embed.set_footer(text="Status: OFF")

        await data["message"].edit(embed=embed)

# ================= RUN =================
bot.run(TOKEN)
