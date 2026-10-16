import os
import time
import threading
import random
import requests
import yt_dlp
import schedule
from flask import Flask

# --- 1. SERVEUR WEB FLASK (Pour garder Render éveillé) ---
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

GAMING_CLIPS_URLS = [
    "https://www.youtube.com/shorts/1W8Y35q8h4g",
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",
]

def find_and_download_best_clip():
    print("\n🔍 [Bot] Sélection d'un clip gaming dans la liste...")
    
    if not DISCORD_WEBHOOK_URL or "discord.com/api/webhooks" not in DISCORD_WEBHOOK_URL:
        print("❌ [Bot] ERREUR : La variable DISCORD_WEBHOOK_URL est absente ou invalide sur Render !")
        return

    target_url = random.choice(GAMING_CLIPS_URLS)
    print(f"🔗 [Bot] URL ciblée : {target_url}")

    ydl_opts = {
        'format': 'best',  # 👈 Format universel ultra-robuste qui évite l'erreur de formats introuvables
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
        'noplaylist': True,
        'max_downloads': 1,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'extractor_args': {'youtube': {'player_client': ['ios']}},
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Clip Gaming')
            webpage_url = info.get('webpage_url', target_url)

        print(f"✅ [Bot] Clip téléchargé avec succès : {title}")
        send_video_to_discord(filename, title, webpage_url)

    except Exception as e:
        print(f"❌ [Bot] Erreur lors du téléchargement : {e}")

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
    print("🚀 [Bot] Démarrage du planificateur de tâches...")
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
