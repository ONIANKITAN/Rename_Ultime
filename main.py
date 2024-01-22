import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
import os
from keep_alive import keep_alive

# Créez une instance de client avec votre propre token de bot et votre nom d'utilisateur
app = Client("my_account", bot_token="6813590394:AAFtdbMTylWbr-yFdhqwV1CP2bmTIYoMGUk", api_id="29022005", api_hash="bfd616932410d155a39403b4fac5884b")


# Créez un sémaphore avec une limite de 1
semaphore = asyncio.Semaphore(5)

# Liste de textes à remplacer
text_to_replace = ["Shar.Club", "SharClub"]

# Variable pour stocker le nom de l'image de la vignette
thumbnail_image = "img.jpg"

# Définition de la variable change_thumbnail
change_thumbnail = False

processing_enabled = True



# Commande /add pour ajouter des textes à remplacer
@app.on_message(filters.command("add"))
async def add_text_to_replace(client: Client, message: Message):
    global text_to_replace

    if len(message.command) > 1:
        new_text = message.command[1]

        # Ajouter le nouveau texte uniquement s'il n'est pas déjà dans la liste
        if new_text not in text_to_replace:
            text_to_replace.append(new_text)
            all_texts = '\n'.join([f'- {text}' for text in text_to_replace])  # Formatage de la liste
            await message.reply_text(f'Texte "{new_text}" ajouté à la liste.\nListe actuelle :\n{all_texts}')
        else:
            await message.reply_text(f'Texte "{new_text}" est déjà dans la liste.')
    else:
        await message.reply_text('Veuillez spécifier un texte à ajouter à la liste.')


# Commande /start_processing pour démarrer le traitement des fichiers
@app.on_message(filters.command("start_processing"))
async def start_processing(client: Client, message: Message):
    global processing_enabled
    processing_enabled = True
    await message.reply_text('Le traitement des fichiers a été démarré.')

# Commande /stop_processing pour arrêter le traitement des fichiers
@app.on_message(filters.command("stop_processing"))
async def stop_processing(client: Client, message: Message):
    global processing_enabled
    processing_enabled = False
    await message.reply_text('Le traitement des fichiers a été arrêté.')



# Ajoutez une commande /start
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text("Bonjour ! Je suis votre bot. Comment puis-je vous aider aujourd'hui ...")

# Filtre pour les commandes
@app.on_message(filters.command(['activer', 'desactiver']))
async def handle_thumbnail_command(client: Client, message: Message):
    global change_thumbnail

    if message.command[0] == 'activer':
        change_thumbnail = True
        await message.reply_text('La fonctionnalité de modification de la vignette a été activée.')
    elif message.command[0] == 'desactiver':
        change_thumbnail = False
        await message.reply_text('La fonctionnalité de modification de la vignette a été désactivée.')


@app.on_message(filters.document)
async def rename_media(client: Client, message: Message):
    global processing_enabled, thumbnail_image, text_to_replace

    if not processing_enabled:
        await message.reply_text('Le traitement des fichiers est actuellement désactivé.')
        return
    
    # Acquérir le sémaphore
    async with semaphore:
        # Vérifiez si la taille du fichier est inférieure à 2 Go (2 * 1024 * 1024 * 1024 octets)
        if message.document.file_size <= 2 * 1024 * 1024 * 1024 :
            # Envoyez un message à l'utilisateur pour lui faire savoir que le fichier a été reçu
            await message.reply_text("Fichier reçu, patientez un instant...")

            # Vérifiez si le nom du fichier contient la partie à remplacer
            if any(text in message.document.file_name for text in text_to_replace):
                # Téléchargez le fichier
                file_path = await message.download()

                # Vérifiez si "@" est présent dans le nom du fichier
                if "@" in message.document.file_name:
                    # Si "@" est présent, retirez "@" du nom du fichier
                    message.document.file_name = message.document.file_name.replace("@", "")
                else:
                    message.document.file_name = message.document.file_name

                # Remplacez chaque partie à remplacer par "@TurboSearch" dans le nom du fichier
                for text in text_to_replace:
                    message.document.file_name = message.document.file_name.replace(text, "")
                
                # Ajoutez "@TurboSearch" au début du nom du fichier
                new_file_name = f"[@TurboSearch] {message.document.file_name.strip()}"

                # Renommez le fichier
                new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                os.rename(file_path, new_file_path)

                # change_thumbnail = True
                if change_thumbnail:
                    # Vérifiez si le fichier de l'image de la vignette existe
                    if not os.path.isfile(os.path.join('tools', thumbnail_image)):
                        # Si le fichier n'existe pas, utilisez l'image par défaut
                        thumbnail_image = 'img.jpg'
                    # Ouvrez l'image que vous voulez utiliser comme vignette
                    with Image.open(os.path.join('tools', thumbnail_image)) as img:
                        # Enregistrez l'image en tant que vignette pour le fichier
                        img.save(new_file_path + '.thumbnail', 'JPEG')

                    # Envoyez le fichier renommé avec la nouvelle vignette
                    await message.reply_document(new_file_path, thumb=os.path.join('tools', thumbnail_image))

                    img_thumb = os.path.join(new_file_path + '.thumbnail')

                    os.remove(img_thumb)
                else:
                    # Envoyez le fichier renommé sans la nouvelle vignette
                    await message.reply_document(new_file_path)

                os.remove(new_file_path)

            else:
                await message.reply_document(message.document.file_id)
        else:
            # Si la taille du fichier est supérieure à 2 Go, ignorer le traitement
            await message.reply_text("Le fichier est trop volumineux et ne peut pas être traité.")

keep_alive()
app.run()
