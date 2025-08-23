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
AVIS_ID = 1399029522816565299 # Id du salon avis

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
# ==== Hébergement ====
@bot.tree.command(name="hebergement", description="Indiquer qu'une tenue est en cours d'hébergement", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro du ticket à mettre en hébergement")
async def hebergement(interaction: discord.Interaction, numero: int):
    # Recherche du channel avec ou sans pastille
    channel = next(
        (ch for ch in interaction.guild.channels if ch.name.endswith(f"cmd-{numero}")),
        None
    )
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    # Retirer les anciennes pastilles et ajouter 🟡
    new_name = channel.name
    for emoji in ["🟠-", "🟢-", "🟡-"]:
        if new_name.startswith(emoji):
            new_name = new_name.replace(emoji, "")
    new_name = f"🟡-{new_name}"

    await channel.edit(name=new_name)

    await interaction.response.send_message(f"⚡ Ticket {new_name} est maintenant en hébergement.", ephemeral=True)


# ==== NUMÉROTATION ====
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

# ==== FORMULAIRES ====
class VetementModal(ui.Modal, title="👕 Commande Vêtement"):
    def __init__(self):
        super().__init__(timeout=None)

        self.desc = ui.TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            required=True,
            placeholder="Exemple : T-shirt bleu avec logo à gauche..."
        )
        self.add_item(self.desc)

        self.liens = ui.TextInput(
            label="Liens (Tu enverras les images dans le ticket)",
            style=discord.TextStyle.paragraph,
            required=False,
            placeholder="Exemple : https://exemple.com/modele"
        )
        self.add_item(self.liens)

        self.impressions = ui.TextInput(
            label="Nombre d'impressions",
            style=discord.TextStyle.short,
            required=True,
            placeholder="Exemple : 50"
        )
        self.add_item(self.impressions)

        self.bas = ui.TextInput(
            label="Faut-il aussi créer le bas ?",
            style=discord.TextStyle.short,
            required=True,
            placeholder="Oui / Non"
        )
        self.add_item(self.bas)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        number = await get_next_ticket_number(guild)
        ticket_name = f"cmd-{number}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        channel = await guild.create_text_channel(
            name=ticket_name,
            category=guild.get_channel(CATEGORY_ID),
            overwrites=overwrites,
            topic=str(interaction.user.id)  # Stocke l'ID du client
        )

        embed = discord.Embed(
            title=f"Commande {ticket_name} - Vêtement",
            description=(
                f"**Client :** {interaction.user.mention}\n"
                f"**Description :** {self.desc.value}\n"
                f"**Liens :** {self.liens.value or 'Aucun'}\n"
                f"**Nombre d'impressions :** {self.impressions.value}\n"
                f"**Bas inclus :** {self.bas.value}"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Acceptez-vous le règlement de la boutique ?")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        await interaction.response.send_message(f"🎟️ Ton ticket a été créé : {channel.mention}", ephemeral=True)

# ==== FORMULAIRE VOITURE ====
class VoitureModal(ui.Modal, title="🚗 Commande Voiture"):
    def __init__(self, modele: str):
        super().__init__(timeout=None)
        self.modele = modele

        self.desc = ui.TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            required=True,
            placeholder="Exemple : Voiture rouge avec bandes blanches..."
        )
        self.add_item(self.desc)

        self.liens = ui.TextInput(
            label="Liens (Tu enverras les images dans le ticket)",
            style=discord.TextStyle.paragraph,
            required=False,
            placeholder="Exemple : https://exemple.com/modele"
        )
        self.add_item(self.liens)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        number = await get_next_ticket_number(guild)
        ticket_name = f"cmd-{number}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        channel = await guild.create_text_channel(
            name=ticket_name,
            category=guild.get_channel(CATEGORY_ID),
            overwrites=overwrites,
            topic=str(interaction.user.id)  # Stocke l'ID du client
        )

        embed = discord.Embed(
            title=f"Commande {ticket_name} - Voiture",
            description=(
                f"**Client :** {interaction.user.mention}\n"
                f"**Modèle choisi :** {self.modele}\n"
                f"**Description :** {self.desc.value}\n"
                f"**Liens :** {self.liens.value or 'Aucun'}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Acceptez-vous le règlement de la boutique ?")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        await interaction.response.send_message(f"🎟️ Ton ticket a été créé : {channel.mention}", ephemeral=True)

# ==== SELECT POUR LES VOITURES ====
class ModeleVoitureSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Premier", value="Premier"),
            discord.SelectOption(label="Master", value="Master"),
            discord.SelectOption(label="Berlingo Civil", value="Berlingo Civil"),
            discord.SelectOption(label="206", value="206"),
            discord.SelectOption(label="Range Rover", value="Range Rover"),
            discord.SelectOption(label="C4 Grand Picasso", value="C4 Grand Picasso"),
            discord.SelectOption(label="5008 Civil", value="5008 Civil"),
            discord.SelectOption(label="Mégane IV Civil", value="Mégane IV Civil"),
            discord.SelectOption(label="Dodge Charger 1970", value="Dodge Charger 1970"),
            discord.SelectOption(label="Olympia A7", value="Olympia A7"),
            discord.SelectOption(label="RX7", value="RX7"),
            discord.SelectOption(label="V Model S", value="V Model S"),
            discord.SelectOption(label="Stellar Coupé", value="Stellar Coupé"),
            discord.SelectOption(label="Premier Limo", value="Premier Limo"),
            discord.SelectOption(label="911", value="911"),
            discord.SelectOption(label="KAT", value="KAT"),
            discord.SelectOption(label="Dépanneuse", value="Dépanneuse"),
            discord.SelectOption(label="FTR", value="FTR"),
        ]
        super().__init__(placeholder="Choisissez un modèle de voiture", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VoitureModal(self.values[0]))

# ==== BOUTONS ====
class ChoixCommandeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👕 Commande Vêtement", style=discord.ButtonStyle.blurple)
    async def vetement(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VetementModal())

    @discord.ui.button(label="🚗 Commande Voiture", style=discord.ButtonStyle.green)
    async def voiture(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Choisissez le modèle :", view=discord.ui.View().add_item(ModeleVoitureSelect()), ephemeral=True)

# ==== COMMANDE POUR AFFICHER LES BOUTONS ====
@bot.tree.command(name="commande", description="Afficher le panneau de commandes", guild=discord.Object(id=GUILD_ID))
async def commande(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Tu n’as pas la permission.", ephemeral=True)
    await interaction.response.send_message("📦 Cliquez sur un bouton pour ouvrir un ticket :", view=ChoixCommandeView())

# ==== COMMANDES STAFF ====
@bot.tree.command(name="2", description="Marquer une commande en cours", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_en_cours(interaction: discord.Interaction, numero: int):
    # Recherche du channel avec ou sans pastille
    channel = next(
        (ch for ch in interaction.guild.channels if ch.name.endswith(f"cmd-{numero}")),
        None
    )
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    # Ajouter pastille orange et retirer pastille verte si nécessaire
    new_name = channel.name
    if new_name.startswith("🟢-"):
        new_name = new_name.replace("🟢-", "🟠-")
    elif not new_name.startswith("🟠-"):
        new_name = f"🟠-{new_name}"

    await channel.edit(name=new_name)

    client_mention = f"<@{channel.topic}>" if channel.topic else "inconnu"

    embed = discord.Embed(
        title=f"Commande {new_name}",
        description=f"Statut : 🟠 En cours\n{interaction.user.mention} prend en charge votre demande.",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"L'équipe Du Blouson D'Tonton")

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Ticket {new_name} marqué en cours.", ephemeral=True)


@bot.tree.command(name="3", description="Marquer une commande terminée", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_terminee(interaction: discord.Interaction, numero: int):
    # Recherche du channel avec ou sans pastille
    channel = next(
        (ch for ch in interaction.guild.channels if ch.name.endswith(f"cmd-{numero}")),
        None
    )
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    # Ajouter pastille verte et retirer pastille orange si nécessaire
    new_name = channel.name
    if new_name.startswith("🟠-"):
        new_name = new_name.replace("🟠-", "🟢-")
    elif not new_name.startswith("🟢-"):
        new_name = f"🟢-{new_name}"

    await channel.edit(name=new_name)

    client_mention = f"<@{channel.topic}>" if channel.topic else "inconnu"

    embed = discord.Embed(
        title=f"Commande {new_name}",
        description=f"Statut : 🟢 Terminée !\nQuand êtes-vous disponible pour que nous procédions à la vente?\n{client_mention}",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"L'équipe Du Blouson D'Tonton")

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Ticket {new_name} marqué terminé.", ephemeral=True)


# ==== SYSTEME DE CLOTURE DE TICKET ====

class AvisModal(discord.ui.Modal, title="⭐ Donne ton avis"):
    def __init__(self, stars: int, client_id: int, staff_id: int, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.stars = stars
        self.client_id = client_id
        self.staff_id = staff_id
        self.channel = channel

        self.comment = ui.TextInput(
            label="Ton avis (facultatif)",
            style=discord.TextStyle.paragraph,
            required=False,
            placeholder="Partage ton ressenti..."
        )
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        # Embed récapitulatif
        avis_channel = interaction.guild.get_channel(AVIS_ID)
        embed = discord.Embed(
            title="📝 Nouvel avis client",
            color=discord.Color.gold()
        )
        embed.add_field(name="Client", value=f"<@{interaction.user.id}>", inline=True)
        embed.add_field(name="Employé", value=f"<@{self.staff_id}>", inline=True)
        embed.add_field(name="Note", value="⭐" * self.stars, inline=False)
        embed.add_field(name="Commentaire", value=self.comment.value or "Aucun", inline=False)

        if avis_channel:
            await avis_channel.send(embed=embed)

        # Confirmation + suppression du salon
        await interaction.response.send_message("✅ Merci pour ton avis ! Le ticket va être clôturé.", ephemeral=True)
        await self.channel.delete()


class EtoilesView(discord.ui.View):
    def __init__(self, client_id: int, staff_id: int, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.client_id = client_id
        self.staff_id = staff_id
        self.channel = channel

        for i in range(1, 6):
            self.add_item(self.StarButton(i))

    class StarButton(discord.ui.Button):
        def __init__(self, stars: int):
            super().__init__(label=f"{stars} ⭐", style=discord.ButtonStyle.secondary)
            self.stars = stars

        async def callback(self, interaction: discord.Interaction):
            parent: EtoilesView = self.view
            await interaction.response.send_modal(AvisModal(self.stars, parent.client_id, parent.staff_id, parent.channel))


class ClotureView(discord.ui.View):
    def __init__(self, client_id: int, staff_id: int, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.client_id = client_id
        self.staff_id = staff_id
        self.channel = channel

    @discord.ui.button(label="Clôturer le ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⭐ Choisis une note :", view=EtoilesView(self.client_id, self.staff_id, self.channel))


# ==== COMMANDE MODIFIEE ====
@bot.tree.command(name="del", description="Clôturer un ticket avec avis", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(numero="Numéro de la commande")
async def commande_supprimer(interaction: discord.Interaction, numero: int):
     # Recherche du channel avec ou sans pastille
    channel = next(
        (ch for ch in interaction.guild.channels if ch.name.endswith(f"cmd-{numero}")),
        None
    )
    if not channel:
        return await interaction.response.send_message("❌ Ticket introuvable", ephemeral=True)

    # Récupère le client depuis le topic du salon
    try:
        client_id = int(channel.topic)
    except:
        client_id = interaction.user.id  # fallback

    staff_id = interaction.user.id
    # Modifier le nom du ticket pour ajouter 🚫
    new_name = channel.name
    for emoji in ["🟠-", "🟢-", "🟡-"]:
        if new_name.startswith(emoji):
            new_name = new_name.replace(emoji, "")
    new_name = f"🚫-{new_name}"
    await channel.edit(name=new_name)


    await interaction.response.send_message(
        f"🔒 Veux-tu clôturer le ticket {channel.mention} ?", 
        view=ClotureView(client_id, staff_id, channel)
    )


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







