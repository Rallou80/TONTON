import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.ui import View, Button, Select # Import manquant corrigé
import random
import threading
from flask import Flask
import os

# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1399014657209008168  #id du serveur

ANNONCE_CHANNEL_ID = 1399018858131624027  # embed d'ouverture et fermeture
SALON_CLIENTS_ID = 1399021433325223946    # /sonnette
ROLE_CROUPIER_ID = 1399857058383138876   #id du rôles à mentionner à la sonnette
STAFF_ROLE_ID = 1399016778553753731 #id du rôle à ajouter aux tickets
CATEGORY_ID = 1399021383262011402 # id de la catégorie où sont créer les tickets

ROLE_CASINO_ID = 1399858237599256596 #id du rôle ouverture
ROLE_PAUSE_ID = 1399858167852040294 #id du rôle pause
SALON_ROUE_ID = 1399859154600071199 #roue (clients)
SALON_LOGS_ID = 1399859434968322078 #roue (staff)

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

# ==== Tickets : utilitaires ====
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


# ==== VUES ====
class ChoixCommandeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Choisissez le type de commande",
        custom_id="commande_type",
        options=[
            discord.SelectOption(label="Vêtement", value="vetement"),
            discord.SelectOption(label="Voiture (UV Nova Life)", value="voiture"),
        ]
    )
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "vetement":
            options = [
                discord.SelectOption(label="Costard", value="costard"),
                discord.SelectOption(label="T-shirt", value="tshirt"),
                discord.SelectOption(label="Entreprise", value="entreprise"),
                discord.SelectOption(label="Tatouage", value="tatouage"),
                discord.SelectOption(label="Autre", value="autre"),
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
                discord.SelectOption(label="FTR", value="ftr"),
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
            overwrites=overwrites
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


# ==== Commande /commande ====
@bot.tree.command(name="commande", description="Ouvrir un ticket de commande", guild=discord.Object(id=GUILD_ID))
async def commande(interaction: discord.Interaction):
    await interaction.response.send_message("📦 Choisissez le type de votre commande :", view=ChoixCommandeView(), ephemeral=True)


# ==== Commandes staff pour suivi des tickets ====
@bot.tree.command(name="2", description="Marquer une commande en cours", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_en_cours(interaction: discord.Interaction, numero: int):
    channel = discord.utils.get(interaction.guild.channels, name=f"cmd-{numero}")
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    embed = discord.Embed(
        title=f"Commande CMD-{numero}",
        description=f"Statut : 🟡 En cours\nClient ping: {channel.topic or 'inconnu'}",
        color=discord.Color.yellow()
    )
    await channel.send(content=f"<@&{STAFF_ROLE_ID}>", embed=embed)
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
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Ticket CMD-{numero} marqué terminé.", ephemeral=True)


@bot.tree.command(name="del", description="Supprimer un ticket", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_supprimer(interaction: discord.Interaction, numero: int):
    channel = discord.utils.get(interaction.guild.channels, name=f"cmd-{numero}")
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    await channel.delete()
    await interaction.response.send_message(f"🗑️ Ticket CMD-{numero} supprimé.", ephemeral=True)

# ==== CLASSE : CasinoControlView (anciennement CasinoView, renommée) ====
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

        croupier_role = interaction.guild.get_role(ROLE_CROUPIER_ID)
        if croupier_role:
            await interaction.user.add_roles(croupier_role)

        embed = discord.Embed(
            title="✅ Annonce d'Ouverture",
            description="**Le Blouson d'TONTON** est officiellement ouvert !\n\nDécouvrez nos nouvelles créations sur-mesure, des pièces uniques conçues avec passion. 🧵🪡\n\nL’atelier est prêt, il ne manque plus que vous. 👔✨\n\n**Le Blouson d'TONTON.**",
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

        croupier_role = interaction.guild.get_role(ROLE_CROUPIER_ID)
        if croupier_role:
            await interaction.user.remove_roles(croupier_role)

        embed = discord.Embed(
            title="🚫 Annonce de Fermeture",
            description="**Le Blouson d'TONTON** ferme les portes de son atelier pour le moment.\n\nMerci à tous pour votre présence. Nous reviendrons très bientôt avec de nouvelles pièces ! 🧶🧥\n\nUn peu de repos pour mieux coudre demain. 🛌💤\n\n**Le Blouson d'TONTON.**",
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
            description="**Le Blouson d'TONTON** marque une courte **pause** dans l’atelier.\n\nUn moment pour se recentrer avant de reprendre le fil. ☕️🧷\n\nRestez connectés, nos créations reviennent très bientôt. 🧵⏱️\n\n**Le Blouson d'TONTON.**",
            color=discord.Color.blurple()
        )
        embed.set_image(url=TONTON_IMAGE_URL)
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("⏸️ Pause activée et annonce envoyée.", ephemeral=True)



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

@bot.tree.command(name="upload", description="Préparer un vêtement à imprimer", guild=discord.Object(id=GUILD_ID))
async def upload(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Tu n’as pas la permission.", ephemeral=True)
        return

    class UploadModal(ui.Modal, title="📥 Ajouter un vêtement"):
        lien = ui.TextInput(
            label="Lien de l'image",
            style=discord.TextStyle.short,
            required=True,
            placeholder="https://exemple.com/image.png"
        )
        nom = ui.TextInput(
            label="Nom du vêtement",
            style=discord.TextStyle.short,
            required=True,
            placeholder="Exemple : T-shirt bleu"
        )
        quantite = ui.TextInput(
            label="Quantité",
            style=discord.TextStyle.short,
            required=True,
            placeholder="Exemple : 10"
        )

        async def on_submit(self, interaction: discord.Interaction):
            embed = discord.Embed(title="👕 Vêtement à imprimer", color=discord.Color.green())
            embed.set_thumbnail(url=self.lien.value)
            embed.add_field(name="📋 À copier dans le jeu", value="```\n/vetement\n```", inline=False)
            embed.add_field(name="📎 Lien", value=f"```\n{self.lien.value}\n```", inline=False)
            embed.add_field(name="🏷️ Nom", value=f"```\n{self.nom.value}\n```", inline=False)
            embed.add_field(name="🔢 Quantité", value=f"```\n{self.quantite.value}\n```", inline=False)
            embed.set_footer(text=f"Ajouté par : {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed)

    await interaction.response.send_modal(UploadModal())




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
