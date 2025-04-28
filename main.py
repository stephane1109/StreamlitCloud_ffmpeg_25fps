########
# Extraction multimédia - en local
# wwww.codeandcortex.fr
########

# pip install streamlit yt-dlp

import streamlit as st
import tempfile
import os
import zipfile
import subprocess
from yt_dlp import YoutubeDL

# Fonction pour vider le cache
def vider_cache():
    st.cache_data.clear()

# Fonction pour définir un répertoire temporaire
def definir_repertoire_travail_temporaire():
    return tempfile.mkdtemp()

# Fonction pour télécharger une vidéo YouTube
def telecharger_video(url, repertoire, cookies_path=None):
    st.write("Téléchargement de la vidéo en cours...")
    ydl_opts = {
        'outtmpl': os.path.join(repertoire, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    }
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video')
            video_path = os.path.join(repertoire, f"{video_title}.mp4")
        return video_path, video_title, None
    except Exception as e:
        return None, None, str(e)

# Fonction pour extraire toutes les ressources
def extraire_ressources(video_path, repertoire, debut, fin, video_title, fps_choice, extraire_toute_video):
    ressources = {}

    try:
        ressources['video_complet'] = video_path

        # Extraire audio complet
        mp3_path = os.path.join(repertoire, f"{video_title}.mp3")
        wav_path = os.path.join(repertoire, f"{video_title}.wav")
        subprocess.run(["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", mp3_path], check=True)
        subprocess.run(["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", wav_path], check=True)
        ressources['audio_mp3_complet'] = mp3_path
        ressources['audio_wav_complet'] = wav_path

        # Extraire vidéo extrait
        extrait_video_path = os.path.join(repertoire, f"{video_title}_extrait.mp4")
        subprocess.run(["ffmpeg", "-y", "-ss", str(debut), "-to", str(fin), "-i", video_path, "-c", "copy", extrait_video_path], check=True)
        ressources['video_extrait'] = extrait_video_path

        # Extraire audio extrait
        extrait_mp3_path = os.path.join(repertoire, f"{video_title}_extrait.mp3")
        extrait_wav_path = os.path.join(repertoire, f"{video_title}_extrait.wav")
        subprocess.run(["ffmpeg", "-y", "-ss", str(debut), "-to", str(fin), "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", extrait_mp3_path], check=True)
        subprocess.run(["ffmpeg", "-y", "-ss", str(debut), "-to", str(fin), "-i", video_path, "-vn", "-acodec", "pcm_s16le", extrait_wav_path], check=True)
        ressources['audio_mp3_extrait'] = extrait_mp3_path
        ressources['audio_wav_extrait'] = extrait_wav_path

        # Extraire images
        images_repertoire = os.path.join(repertoire, f"images_{fps_choice}fps_{video_title}")
        os.makedirs(images_repertoire, exist_ok=True)
        output_pattern = os.path.join(images_repertoire, "image_%04d.jpg")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"fps={fps_choice},scale=1920:1080",
            "-q:v", "1",
            output_pattern
        ]

        if not extraire_toute_video:
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(debut),
                "-to", str(fin),
                "-i", video_path,
                "-vf", f"fps={fps_choice},scale=1920:1080",
                "-q:v", "1",
                output_pattern
            ]

        subprocess.run(cmd, check=True)

        # Zipper les images
        zip_images_path = images_repertoire + ".zip"
        with zipfile.ZipFile(zip_images_path, 'w') as zipf:
            for root, dirs, files in os.walk(images_repertoire):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, images_repertoire)
                    zipf.write(file_path, arcname)
        ressources['images_zip'] = zip_images_path

        return ressources, None

    except Exception as e:
        return None, str(e)

# Fonction pour créer un zip général
def creer_zip_global(ressources, repertoire):
    zip_path = os.path.join(repertoire, "ressources_completes.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for nom, chemin in ressources.items():
            if os.path.exists(chemin):
                zipf.write(chemin, os.path.basename(chemin))
    return zip_path

# ---------- Interface utilisateur Streamlit ----------

st.title("Extraction multimédia (mp4 - mp3 - wav - images) depuis une url de YouTube")

# Ajout du site web
st.markdown("**[www.codeandcortex.fr](http://www.codeandcortex.fr)**")

# Explication claire pour l'utilisateur
st.markdown("""

➡ Entrez une URL YouTube.  
➡ **Renseignez votre fichier cookies.txt** (optionnel) : fonctionne sans... tant que YouTube ne le demande pas.  
➡ Le script téléchargera la **vidéo complète** au format .mp4  
➡ Ensuite, il extraira automatiquement :
- L'audio complet (.mp3 et .wav)
- Un extrait vidéo (.mp4 selon l'intervalle défini)
- Un extrait audio (.mp3 et .wav)
- Des images extraites (au choix 1 image/sec ou 25 images/sec) sur l'intervalle ou toutes les images de la vidéo

Enfin, vous pourrez télécharger toutes les ressources dans un seul fichier ZIP.
""")

# Vider cache au démarrage
vider_cache()

# Session Streamlit
if 'video_path' not in st.session_state:
    st.session_state['video_path'] = None
if 'video_title' not in st.session_state:
    st.session_state['video_title'] = None
if 'repertoire_travail' not in st.session_state:
    st.session_state['repertoire_travail'] = None

# URL de la vidéo
url = st.text_input("Entrez l'URL de la vidéo YouTube :")

# Upload fichier cookies.txt
cookies_file = st.file_uploader("Uploader votre fichier cookies.txt (optionnel)", type=["txt"])

# Bouton téléchargement
if st.button("Télécharger la vidéo"):
    if url:
        st.session_state['repertoire_travail'] = definir_repertoire_travail_temporaire()
        cookies_path = None
        if cookies_file:
            cookies_temp_path = os.path.join(st.session_state['repertoire_travail'], "cookies.txt")
            with open(cookies_temp_path, "wb") as f:
                f.write(cookies_file.read())
            cookies_path = cookies_temp_path

        video_path, video_title, erreur = telecharger_video(url, st.session_state['repertoire_travail'], cookies_path)

        if erreur:
            st.error(f"Erreur téléchargement : {erreur}")
        else:
            st.success(f"Téléchargement réussi : {video_title}")
            st.session_state['video_path'] = video_path
            st.session_state['video_title'] = video_title

# Extraction après téléchargement
if st.session_state['video_path']:
    st.markdown("---")
    st.subheader("Lecture de la vidéo téléchargée")
    st.video(st.session_state['video_path'])

    st.markdown("---")
    st.subheader("Paramètres d'extraction")

    col1, col2 = st.columns(2)
    debut = col1.number_input("Début de l'intervalle (en secondes)", min_value=0, value=0)
    fin = col2.number_input("Fin de l'intervalle (en secondes)", min_value=1, value=10)

    fps_choice = st.selectbox("Fréquence d'images pour l'extraction :", options=[1, 25])

    extraire_toute_video = st.checkbox("Extraire toutes les images de toute la vidéo", value=False)

    if st.button("Extraire toutes les ressources"):
        ressources, erreur = extraire_ressources(
            st.session_state['video_path'],
            st.session_state['repertoire_travail'],
            debut,
            fin,
            st.session_state['video_title'],
            fps_choice,
            extraire_toute_video
        )

        if erreur:
            st.error(f"Erreur lors de l'extraction : {erreur}")
        else:
            zip_global_path = creer_zip_global(ressources, st.session_state['repertoire_travail'])
            st.success("Toutes les ressources ont été extraites avec succès !")

            with open(zip_global_path, "rb") as f:
                st.download_button(
                    label="Télécharger toutes les ressources (ZIP)",
                    data=f,
                    file_name="ressources_completes.zip",
                    mime="application/zip"
                )

