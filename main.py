import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.ui import View, Button, Select
import random
import threading
from flask import Flask
import os

# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1399014657209008168  # id du serveur

ANNONCE_CHANNEL_ID = 1399018858131624027
STAFF_ROLE_ID = 1399016778553753731
CATEGORY_ID = 1399021383262011402

ROLE_CASINO_ID = 1399858237599256596
ROLE_PAUSE_ID = 1399858167852040294
SALON_ROUE_ID = 1399859154600071199
SALON_LOGS_ID = 1399859434968322078
SALON_LOGS_gains_ID = 1399859434968322078
SALON_LOGS_SERVICE_ID = 1399859851529556149

GIF_URL = "https://raw.githubusercontent.com/Rallou80/TONTON/main/royal.png"
TONTON_IMAGE_URL = "https://raw.githubusercontent.com/Rallou80/TONTON/main/tontonGOAT.png"
TONTON_IMAGE = "https://raw.githubusercontent.com/Rallou80/TONTON/main/TONTON.png"

# ==== INTENTS & BOT SETUP ====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== FLASK KEEP ALIVE ====
app = Flask("")

@app.route("/")
def home():
    return "Bot actif."

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()


# ==== CLASSE : CasinoControlView ====
class CasinoControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def remove_pause_role(self, interaction):
        pause_role = interaction.guild.get_role(ROLE_PAUSE_ID)
        if pause_role and pause_role in interaction.guild.me.roles:
            await interaction.guild.me.remove_roles(pause_role)

    async def delete_last_royal_announcement(self, channel: discord.TextChannel):
        async for message in channel.history(limit=10):
            if message.author == channel.guild.me and message.embeds:
                embed = message.embeds[0]
                if embed.description and "Blouson d'TONTON" in embed.description:
                    await message.delete()
                    break

    @discord.ui.button(label="Ouvrir", style=discord.ButtonStyle.success, custom_id="casino_ouvrir")
    async def open_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_pause_role(interaction)
        role = interaction.guild.get_role(ROLE_CASINO_ID)
        if role:
            await interaction.guild.me.add_roles(role)

        embed = discord.Embed(
            title="✅ Annonce d'Ouverture",
            description="**Le Blouson d'TONTON** est officiellement ouvert !",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=TONTON_IMAGE_URL)
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("✅ Atelier ouvert et annonce envoyée.", ephemeral=True)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.danger, custom_id="casino_fermer")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_pause_role(interaction)
        role = interaction.guild.get_role(ROLE_CASINO_ID)
        if role:
            await interaction.guild.me.remove_roles(role)

        embed = discord.Embed(
            title="🚫 Annonce de Fermeture",
            description="**Le Blouson d'TONTON** ferme les portes pour le moment.",
            color=discord.Color.red()
        )
        embed.set_image(url=TONTON_IMAGE)
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("🚫 Atelier fermé et annonce envoyée.", ephemeral=True)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, custom_id="casino_pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_PAUSE_ID)
        if role:
            await interaction.guild.me.add_roles(role)

        embed = discord.Embed(
            title="⏸️ Annonce de Pause",
            description="**Le Blouson d'TONTON** marque une courte pause.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=TONTON_IMAGE_URL)
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("⏸️ Pause activée et annonce envoyée.", ephemeral=True)


# ====== Commande /commande ======

async def get_next_ticket_number(guild: discord.Guild):
    category = guild.get_channel(CATEGORY_ID)
    if not category:
        return 1

    ticket_channels = [ch for ch in category.channels if isinstance(ch, discord.TextChannel) and ch.name.startswith("cmd-")]
    if not ticket_channels:
        return 1

    numbers = []
    for ch in ticket_channels:
        try:
            num = int(ch.name.split("-")[1])
            numbers.append(num)
        except:
            pass
    return max(numbers) + 1 if numbers else 1


class ChoixCommandeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(discord.ui.Select(
            placeholder="Choisissez le type de commande",
            custom_id="commande_type",
            options=[
                discord.SelectOption(label="Vêtement", value="vetement"),
                discord.SelectOption(label="Voiture (UV Nova Life)", value="voiture")
            ]
        ))

    @discord.ui.select(custom_id="commande_type")
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "vetement":
            options = [
                discord.SelectOption(label="Costard", value="costard"),
                discord.SelectOption(label="T-shirt", value="tshirt"),
                discord.SelectOption(label="Entreprise", value="entreprise"),
                discord.SelectOption(label="Tatouage", value="tatouage"),
                discord.SelectOption(label="Autre", value="autre")
            ]
        else:
            options = [
                discord.SelectOption(label="Premier", value="premier"),
                discord.SelectOption(label="Master", value="master"),
                discord.SelectOption(label="Berlingo Civil", value="berlingo_civil"),
                discord.SelectOption(label="206", value="206"),
                discord.SelectOption(label="Range Rover", value="range_rover"),
                discord.SelectOption(label="C4 Grand Picasso", value="c4_grand_picasso"),
                discord.SelectOption(label="5008 Civil", value="5008_civil"),
                discord.SelectOption(label="Mégane IV Civil", value="megane_iv_civil"),
                discord.SelectOption(label="Dodge Charger 1970", value="dodge_charger_1970"),
                discord.SelectOption(label="Olympia A7", value="olympia_a7"),
                discord.SelectOption(label="RX7", value="rx7"),
                discord.SelectOption(label="V Model S", value="v_model_s"),
                discord.SelectOption(label="Stellar Coupé", value="stellar_coupe"),
                discord.SelectOption(label="Premier Limo", value="premier_limo"),
                discord.SelectOption(label="911", value="911"),
                discord.SelectOption(label="KAT", value="kat"),
                discord.SelectOption(label="Dépanneuse", value="depanneuse"),
                discord.SelectOption(label="FTR", value="ftr")
            ]

        view = SousTypeCommandeView(options, select.values[0])
        await interaction.response.edit_message(content="📑 Sélectionnez le modèle :", view=view)


class SousTypeCommandeView(discord.ui.View):
    def __init__(self, options, type_commande):
        super().__init__(timeout=None)
        self.type_commande = type_commande
        self.add_item(discord.ui.Select(
            placeholder="Choisissez le modèle",
            options=options,
            custom_id="commande_sous_type"
        ))

    @discord.ui.select(custom_id="commande_sous_type")
    async def select_modele(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild = interaction.guild
        number = await get_next_ticket_number(guild)
        ticket_name = f"cmd-{number}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        channel = await guild.create_text_channel(
            name=ticket_name,
            category=guild.get_channel(CATEGORY_ID),
            overwrites=overwrites,
            topic=str(interaction.user.id)  # stock ID client
        )

        embed = discord.Embed(
            title=f"Commande {ticket_name}",
            description=(
                f"**Client :** {interaction.user.mention}\n"
                f"**Type :** {select.values[0]}\n\n"
                "Veuillez détailler votre demande, ajouter un lien si vous en avez, et envoyer vos images ci-dessous."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Acceptez-vous le règlement de la boutique ?")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        await interaction.response.edit_message(content=f"🎟️ Ticket créé : {channel.mention}", view=None)


@bot.tree.command(name="commande", description="Ouvrir un ticket de commande", guild=discord.Object(id=GUILD_ID))
async def commande(interaction: discord.Interaction):
    view = ChoixCommandeView()
    await interaction.response.send_message("📦 Choisissez le type de votre commande :", view=view, ephemeral=True)


# ===== Commandes staff =====
@bot.tree.command(name="2", description="Marquer une commande en cours", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_en_cours(interaction: discord.Interaction, numero: int):
    channel = discord.utils.get(interaction.guild.channels, name=f"cmd-{numero}")
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    embed = discord.Embed(
        title=f"Commande CMD-{numero}",
        description=f"Statut : 🟡 En cours\nClient ping: <@{channel.topic}>",
        color=discord.Color.yellow()
    )
    await channel.send(content=f"<@&{STAFF_ROLE_ID}> <@{channel.topic}>", embed=embed)
    await interaction.response.send_message(f"✅ Ticket CMD-{numero} marqué en cours.", ephemeral=True)


@bot.tree.command(name="3", description="Marquer une commande terminée", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_terminee(interaction: discord.Interaction, numero: int):
    channel = discord.utils.get(interaction.guild.channels, name=f"cmd-{numero}")
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    embed = discord.Embed(
        title=f"Commande CMD-{numero}",
        description="Statut : 🟢 Terminée\nMerci pour votre confiance !",
        color=discord.Color.green()
    )
    await channel.send(content=f"<@{channel.topic}> ✅ Votre commande est prête !", embed=embed)
    await interaction.response.send_message(f"✅ Ticket CMD-{numero} marqué terminé.", ephemeral=True)


@bot.tree.command(name="del", description="Supprimer un ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_supprimer(interaction: discord.Interaction, numero: int):
    channel = discord.utils.get(interaction.guild.channels, name=f"cmd-{numero}")
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    await channel.delete()
    await interaction.response.send_message(f"🗑️ Ticket CMD-{numero} supprimé.", ephemeral=True)


# ==== REWARDS ====
rewards = [
    ("500€ Cash", 15),
    ("250€ Cash", 20),
    ("1000€ Cash", 15),
    ("Rien", 40),
    ("*T-shirt offert", 5),
    ("5000€ Cash", 3),
    ("Une photo avec le PDG", 1),
]

def tirer_gain():
    pool = []
    for reward, chance in rewards:
        pool.extend([reward] * chance)
    return random.choice(pool)

class VueRoue(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.joueurs_deja_passes = set()

    @discord.ui.button(label="🎰Tourner la roue", style=discord.ButtonStyle.green, custom_id="tourner_roue")
    async def tourner(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.joueurs_deja_passes:
            await interaction.response.send_message("❌ Tu as déjà tourné la roue aujourd’hui !", ephemeral=True)
            return

        self.joueurs_deja_passes.add(user_id)
        gain = tirer_gain()

        embed = discord.Embed(title="🎁 Votre gain", color=discord.Color.gold())
        embed.add_field(name="Gain", value=gain, inline=False)
        embed.add_field(name="🎉", value="Félicitations ! Venez récupérer votre prix au casino.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        log_channel = bot.get_channel(SALON_LOGS_ID)
        if log_channel:
            await log_channel.send(f"🎡 {interaction.user.display_name} a tourné la roue et a gagné : **{gain}**")


# ==== COMMANDES ====
@bot.tree.command(name="annonce", description="Affiche les boutons de gestion du Blouson d'TONTON", guild=discord.Object(id=GUILD_ID))
async def annonce(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être administrateur pour utiliser cette commande.", ephemeral=True)
        return
    await interaction.response.send_message("🎰 Contrôle du Blouson d'TONTON :", view=CasinoControlView())

@bot.tree.command(name="resetroue", description="Remet la roue à zéro", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def resetroue(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🎡 Roue journalière", description="Clique sur le bouton ci-dessous pour tenter ta chance !", color=discord.Color.blue())
    embed.set_image(url=GIF_URL)
    channel = bot.get_channel(SALON_ROUE_ID)
    if channel:
        await channel.send(embed=embed, view=VueRoue())
        await interaction.followup.send("✅ Roue relancée dans 🌡｜tourner-la-roue.", ephemeral=True)
    else:
        await interaction.followup.send("❌ Salon introuvable.", ephemeral=True)


@bot.tree.command(name="service", description="Envoyer le bouton de prise de service")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def service(interaction: discord.Interaction):
    await interaction.response.send_message("Clique sur le bouton pour prendre ton service :", view=PriseDeServiceView())


# ==== VIEWS pour prise et fin de service ====
class FinServiceModal(ui.Modal, title="📋 Rapport de fin de service"):
    nb_clients = ui.TextInput(label="👥 Nombre de clients", required=True)
    argent_depart = ui.TextInput(label="💸 Argent au départ", required=True)
    argent_fin = ui.TextInput(label="💰 Argent à la fin", required=True)
    temps_service = ui.TextInput(label="⏱️ Temps de service (HH:MM)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(SALON_LOGS_SERVICE_ID)
        embed = discord.Embed(title="📝 Fin de service", color=discord.Color.green())
        embed.add_field(name="👤 Nom", value=interaction.user.display_name, inline=False)
        embed.add_field(name="👥 Nombre de clients", value=self.nb_clients.value, inline=True)
        embed.add_field(name="💸 Argent départ", value=self.argent_depart.value, inline=True)
        embed.add_field(name="💰 Argent fin", value=self.argent_fin.value, inline=True)
        embed.add_field(name="⏱️ Temps de service", value=self.temps_service.value, inline=True)
        await interaction.response.send_message("✅ Ton rapport a bien été envoyé !", ephemeral=True)
        await log_channel.send(embed=embed)

class FinDeServiceView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="⛔ Fin de service", style=discord.ButtonStyle.danger, custom_id="fin_service_btn")
    async def fin_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FinServiceModal())

class PriseDeServiceView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📢 Prise de service", style=discord.ButtonStyle.success, custom_id="prise_service_btn")
    async def prise_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(SALON_LOGS_SERVICE_ID)
        nom = interaction.user.display_name
        await log_channel.send(f"✅ Le joueur **{nom}** a pris son service.")
        await interaction.response.send_message(
            "🟢 Tu es maintenant en service.\nQuand tu veux terminer, clique sur le bouton ci-dessous.",
            view=FinDeServiceView(),
            ephemeral=True)


# ==== Event on_ready ====
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")
    print(f"🤖 Connecté en tant que {bot.user}")


# ==== LANCEMENT FINAL ====
keep_alive()
bot.run(TOKEN)
