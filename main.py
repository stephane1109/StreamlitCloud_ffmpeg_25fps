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
import imageio.v3 as iio

# Fonction pour vider le cache
def vider_cache():
    st.cache_data.clear()
    st.write("Cache vidé systématiquement au lancement du script")

# Fonction pour définir un répertoire temporaire
def definir_repertoire_travail_temporaire():
    repertoire_temporaire = tempfile.mkdtemp()
    st.write(f"Répertoire temporaire : {repertoire_temporaire}")
    return repertoire_temporaire

# Fonction pour télécharger la vidéo
def telecharger_video(url, repertoire):
    st.write("Téléchargement en cours...")
    ydl_opts = {
        'outtmpl': os.path.join(repertoire, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'merge_output_format': 'mp4',
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get('title', 'video')
        video_path = os.path.join(repertoire, f"{video_title}.mp4")
    st.write(f"Téléchargement terminé : {video_path}")
    return video_path, video_title

# Fonction pour extraire les frames à 25fps
def extraire_images_25fps_intervalle(video_path, repertoire, debut, fin, video_title):
    images_repertoire = os.path.join(repertoire, f"images_25fps_{video_title}")
    os.makedirs(images_repertoire, exist_ok=True)
    st.write(f"Extraction dans : {images_repertoire}")

    try:
        # Utilisation de ffmpeg-python pour extraire
        output_pattern = os.path.join(images_repertoire, "image_%04d.jpg")

        stream = (
            ffmpeg
            .input(video_path, ss=debut, t=(fin - debut))
            .filter('fps', fps=25)
            .filter('scale', 1920, 1080)
            .output(output_pattern, qscale=1)
            .overwrite_output()
        )
        stream.run()

        st.success(f"Images extraites dans : {images_repertoire}")
        return images_repertoire
    except ffmpeg.Error as e:
        st.error(f"Erreur FFmpeg : {e.stderr.decode()}")
        return None

# Fonction pour créer un fichier ZIP
def creer_zip_images(images_repertoire):
    zip_path = images_repertoire + ".zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(images_repertoire):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, images_repertoire)
                zipf.write(file_path, arcname)
    return zip_path

# Interface utilisateur
st.title("Extraction d'images YouTube à 25fps (Streamlit Cloud Compatible)")

url = st.text_input("Entrez l'URL de la vidéo YouTube :")

col1, col2 = st.columns(2)
debut = col1.number_input("Début (en secondes) :", min_value=0, value=0)
fin = col2.number_input("Fin (en secondes) :", min_value=1, value=10)

if url:
    repertoire_travail = definir_repertoire_travail_temporaire()
    video_path, video_title = telecharger_video(url, repertoire_travail)

    if st.button("Extraire les images"):
        if debut >= fin:
            st.error("Erreur : Début >= Fin")
        else:
            images_repertoire = extraire_images_25fps_intervalle(
                video_path, repertoire_travail, debut, fin, video_title
            )
            if images_repertoire:
                zip_path = creer_zip_images(images_repertoire)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Télécharger les images (ZIP)",
                        data=f,
                        file_name=os.path.basename(zip_path),
                        mime="application/zip"
                    )
