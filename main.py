########
# Extraction d'une vidéo en images 25fps + Téléchargement zip - Compatible Streamlit Cloud
# wwww.codeandcortex.fr
########

# pip install streamlit yt-dlp ffmpeg-python imageio imageio-ffmpeg Pillow

import streamlit as st
import tempfile
import os
import zipfile
import ffmpeg
from yt_dlp import YoutubeDL
from PIL import Image
import shutil

# Fonction pour vider le cache
def vider_cache():
    st.cache_data.clear()
    st.write("Cache vidé systématiquement au lancement du script.")

# Fonction pour définir un répertoire temporaire
def definir_repertoire_travail_temporaire():
    return tempfile.mkdtemp()

# Fonction pour télécharger une vidéo YouTube avec yt-dlp et option cookies
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

# Fonction pour extraire des images à 25fps sur un intervalle
def extraire_images_25fps_intervalle(video_path, repertoire, debut, fin, video_title):
    images_repertoire = os.path.join(repertoire, f"images_25fps_{video_title}")
    os.makedirs(images_repertoire, exist_ok=True)

    output_pattern = os.path.join(images_repertoire, "image_%04d.jpg")

    try:
        (
            ffmpeg
            .input(video_path, ss=debut, t=(fin - debut))
            .filter('fps', fps=25)
            .filter('scale', 1920, 1080)
            .output(output_pattern, qscale=1)
            .overwrite_output()
            .run()
        )
        return images_repertoire, None
    except ffmpeg.Error as e:
        return None, e.stderr.decode()

# Fonction pour zipper les images extraites
def creer_zip_images(images_repertoire):
    zip_path = images_repertoire + ".zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(images_repertoire):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, images_repertoire)
                zipf.write(file_path, arcname)
    return zip_path

# Interface utilisateur principale Streamlit
st.title("Extraction d'images YouTube à 25fps (Compatible Streamlit Cloud)")

# Vider cache au démarrage
vider_cache()

# Initialiser les variables de session Streamlit
if 'video_path' not in st.session_state:
    st.session_state['video_path'] = None
if 'video_title' not in st.session_state:
    st.session_state['video_title'] = None
if 'repertoire_travail' not in st.session_state:
    st.session_state['repertoire_travail'] = None

# Zone d'entrée pour l'URL de la vidéo
url = st.text_input("Entrez l'URL de la vidéo YouTube :")

# Upload du fichier cookies.txt
cookies_file = st.file_uploader("Uploader votre fichier cookies.txt (optionnel)", type=["txt"])

# Bouton pour lancer le téléchargement
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
            st.error(f"Erreur lors du téléchargement : {erreur}")
        else:
            st.success(f"Téléchargement réussi : {video_title}")
            st.session_state['video_path'] = video_path
            st.session_state['video_title'] = video_title
    else:
        st.error("Veuillez entrer une URL valide.")

# Une fois la vidéo téléchargée, proposer l'extraction
if st.session_state['video_path']:
    st.markdown("---")
    st.subheader("Paramètres d'extraction d'images")
    col1, col2 = st.columns(2)
    debut = col1.number_input("Début de l'intervalle (en secondes)", min_value=0, value=0)
    fin = col2.number_input("Fin de l'intervalle (en secondes)", min_value=1, value=10)

    if st.button("Extraire les images"):
        if debut >= fin:
            st.error("Erreur : Le début doit être inférieur à la fin.")
        else:
            images_repertoire, erreur = extraire_images_25fps_intervalle(
                st.session_state['video_path'],
                st.session_state['repertoire_travail'],
                debut,
                fin,
                st.session_state['video_title']
            )
            if erreur:
                st.error(f"Erreur lors de l'extraction des images : {erreur}")
            else:
                st.success(f"Images extraites dans : {images_repertoire}")
                zip_path = creer_zip_images(images_repertoire)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Télécharger les images (ZIP)",
                        data=f,
                        file_name=os.path.basename(zip_path),
                        mime="application/zip"
                    )
