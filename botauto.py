import os
import time
import threading
import requests
import yt_dlp
import schedule
from flask import Flask

# --- 1. PETIT SERVEUR WEB (Pour garder Render éveillé gratuitement) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Le bot Twitch/Gaming automatique est en ligne et actif !"

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- 2. LOGIQUE DU BOT ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "VOTRE_URL_WEBHOOK_DISCORD")
DOWNLOAD_FOLDER = "clips_telecharges"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def find_and_download_best_clip():
    print("\n🔍 [Bot] Recherche automatique d'un clip gaming tendance...")
    search_query = "ytsearch1:twitch gaming funny moments short"

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
        'max_downloads': 1,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Clip Gaming')
            webpage_url = info.get('webpage_url', '')

        print(f"✅ [Bot] Clip téléchargé : {title}")
        send_video_to_discord(filename, title, webpage_url)

    except Exception as e:
        print(f"❌ [Bot] Erreur : {e}")

def send_video_to_discord(file_path, title, video_url):
    if not os.path.exists(file_path):
        return

    print("📤 [Bot] Envoi sur Discord...")
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
        payload = {
            "content": f"🔥 **Pépite Gaming Automatique !**\n📌 **Titre :** {title}\n🔗 {video_url}"
        }
        requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)

    try:
        os.remove(file_path)
    except Exception:
        pass

def run_scheduler():
    # Le bot cherchera un clip toutes les 6 heures (vous pouvez ajuster)
    schedule.every(6).hours.do(find_and_download_best_clip)
    
    # (Optionnel) Décommentez la ligne ci-dessous si vous voulez tester le bot dès le démarrage du serveur
    # find_and_download_best_clip()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Lancement du planificateur dans un fil d'exécution séparé (Thread)
    t = threading.Thread(target=run_scheduler)
    t.daemon = True
    t.start()

    # Lancement du serveur web Flask
    run_web()