########
# Extraction d'une vidéo en images 25fps + Téléchargement zip - Compatible Streamlit Cloud
# wwww.codeandcortex.fr
########

import streamlit as st
import tempfile
import os
import zipfile
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from PIL import Image

# Fonction pour vider le cache
def vider_cache():
    st.cache_data.clear()
    st.write("Cache vidé systématiquement au lancement du script")

# Appeler la fonction de vidage du cache au début du script
vider_cache()

# Fonction pour définir un répertoire de travail temporaire
def definir_repertoire_travail_temporaire():
    repertoire_temporaire = tempfile.mkdtemp()
    st.write(f"Répertoire temporaire créé : {repertoire_temporaire}")
    return repertoire_temporaire

# Fonction pour télécharger la vidéo avec yt-dlp (forcer le format .mp4)
def telecharger_video(url, repertoire):
    st.write("Téléchargement de la vidéo à partir de YouTube...")
    ydl_opts = {
        'outtmpl': os.path.join(repertoire, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'merge_output_format': 'mp4',
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get("title", "video")
        video_filename = f"{video_title}.mp4"
        video_path = os.path.join(repertoire, video_filename)
    st.write(f"Téléchargement terminé : {video_path}")
    return video_path, video_title

# Fonction pour extraire des images à 25fps dans un intervalle donné avec moviepy
def extraire_images_25fps_intervalle(video_path, repertoire, debut, fin, video_title):
    images_repertoire = os.path.join(repertoire, f"images_25fps_{video_title}")
    if not os.path.exists(images_repertoire):
        os.makedirs(images_repertoire)
        st.write(f"Répertoire créé pour les images : {images_repertoire}")
    else:
        st.write(f"Le répertoire pour les images existe déjà : {images_repertoire}")

    st.write(f"Extraction des images à 25fps entre {debut}s et {fin}s...")

    try:
        clip = VideoFileClip(video_path).subclip(debut, fin)
        fps = 25
        total_frames = int(clip.duration * fps)

        progress_bar = st.progress(0)

        for i, frame in enumerate(clip.iter_frames(fps=fps, dtype='uint8')):
            frame_filename = os.path.join(images_repertoire, f'image_{i:04d}.jpg')
            img = Image.fromarray(frame)
            img.save(frame_filename)
            progress_bar.progress((i + 1) / total_frames)

        progress_bar.empty()
        st.success(f"Images extraites dans le répertoire : {images_repertoire}")
        return images_repertoire

    except Exception as e:
        st.error(f"Erreur lors de l'extraction des images : {str(e)}")
        return None

# Fonction pour zipper les images extraites
def creer_zip_images(images_repertoire):
    zip_path = os.path.join(images_repertoire + ".zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(images_repertoire):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, images_repertoire)
                zipf.write(file_path, arcname)
    return zip_path

# Interface utilisateur Streamlit
st.title("Extraction d'images d'une vidéo YouTube à 25fps")

# Entrée pour l'URL de la vidéo
url = st.text_input("Entrez l'URL de la vidéo YouTube :")

# Entrées pour définir l'intervalle de temps
col1, col2 = st.columns(2)
debut = col1.number_input("Début de l'intervalle (en secondes) :", min_value=0, value=0)
fin = col2.number_input("Fin de l'intervalle (en secondes) :", min_value=1, value=10)

if url:
    repertoire_travail = definir_repertoire_travail_temporaire()
    if repertoire_travail:
        video_path, video_title = telecharger_video(url, repertoire_travail)
        if video_path:
            if st.button("Extraire les images"):
                if debut >= fin:
                    st.error("Erreur : Le début de l'intervalle doit être inférieur à la fin.")
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
