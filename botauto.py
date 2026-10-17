import os
import time
import threading
import random
import requests
import yt_dlp
import schedule
from flask import Flask

# --- 1. SERVEUR WEB FLASK ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Le bot Clipfarm est en ligne, actif et prêt !"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- 2. LOGIQUE ET FONCTIONNALITÉS DU BOT ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
DOWNLOAD_FOLDER = "clips_telecharges"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

GAMING_CHANNELS = [
    "https://www.youtube.com/@PrestonShorts/shorts",
    "https://www.youtube.com/@SypherPK/shorts",
    "https://www.youtube.com/@LazarBeam/shorts",
]

def find_and_download_best_clip():
    print("\n🔍 [Bot] Analyse et recherche dynamique du meilleur contenu récent...")
    
    if not DISCORD_WEBHOOK_URL or "discord.com/api/webhooks" not in DISCORD_WEBHOOK_URL:
        print("❌ [Bot] ERREUR : La variable DISCORD_WEBHOOK_URL est absente ou invalide sur Render !")
        return

    target_channel = random.choice(GAMING_CHANNELS)
    print(f"📡 [Bot] Exploration de la source : {target_channel}")

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
        'playlistend': 1,
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        # Emulation complète d'un navigateur de bureau pour valider les cookies
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_channel, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Clip Gaming')
            webpage_url = info.get('webpage_url', target_channel)

        print(f"✅ [Bot] Nouveau contenu viral détecté et téléchargé : {title}")
        send_video_to_discord(filename, title, webpage_url)

    except Exception as e:
        print(f"❌ [Bot] Erreur lors de l'extraction dynamique : {e}")

def send_video_to_discord(file_path, title, video_url):
    if not file_path or not os.path.exists(file_path):
        print("❌ [Bot] Fichier vidéo introuvable.")
        return

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📦 [Bot] Taille du fichier : {file_size_mb:.2f} MB")

    payload = {
        "content": f"🔥 **Pépite Gaming Automatique !**\n📌 **Titre :** {title}\n🔗 {video_url}"
    }

    try:
        if file_size_mb < 24.5:
            print("📤 [Bot] Envoi de la vidéo sur Discord...")
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
                response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files, timeout=60)
        else:
            print("⚠️ [Bot] Fichier trop lourd pour Discord (> 25MB). Envoi du lien uniquement...")
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30)

        if response.status_code in (200, 204):
            print("🎉 [Bot] Clip publié avec succès sur Discord !")
        else:
            print(f"❌ [Bot] Échec de l'envoi Discord (Code {response.status_code}) : {response.text}")

    except Exception as e:
        print(f"❌ [Bot] Erreur lors de la requête Discord : {e}")

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print("🧹 [Bot] Fichier local nettoyé.")
            except Exception as e:
                print(f"⚠️ [Bot] Impossible de supprimer le fichier temporaire : {e}")

def run_scheduler():
    print("🚀 [Bot] Démarrage du planificateur de tâches autonomes...")
    find_and_download_best_clip()
    schedule.every(6).hours.do(find_and_download_best_clip)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    run_web()
