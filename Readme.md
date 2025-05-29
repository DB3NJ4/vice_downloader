## INICIALIZACION DEL PROYECTO

## CREACION DE CARPETAS
``
mkdir youtube_downloader
cd youtube_downloader

mkdir backend frontend
cd backend
echo > app.py
echo > requirements.txt
mkdir downloads
cd ../frontend
echo > index.html
echo > main.js
echo > style.css
``

## ENTRAR EN LA CARPETA

``
cd backend
``
## CREAR ENTORNO VIRTUAL

``
python -m venv env
``
## ACTIVAR ENTORNO VIRTUAL

``
env\Scripts\activate 
``

## INSTALAR DEPENDENCIAS
``
pip install flask flask-cors yt-dlp
``

## LUEGO
``
pip freeze > requirements.txt
``

## IMPORTANTE TENER "ffmpeg en el path del sistema"
``
ffmpeg -version
``

## SINO INSTALR EN 
``
https://ffmpeg.org/download.html
``

## CORRER EL SERVICIO DE FLASK
``
python app.py
``

## INSTALR PYTUBE PARA DESCARGAR VIDEOS DE YOUTUBE
``
pip install pytube
``

## INSTALAR ESTA DEPENDENCIA
``
pip install python-slugify
``