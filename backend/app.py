from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import yt_dlp
from slugify import slugify  # pip install python-slugify
import os
import tempfile
from io import BytesIO
from flask import send_from_directory

app = Flask(__name__)
CORS(app)



@app.route("/")
def serve_frontend():
    return send_from_directory("../frontend/vice-frontend", "index.html")

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory("../frontend/vice-frontend", path)



@app.route("/info")
def info():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "No se proporcionó ninguna URL"}), 400

    print("🔍 Obteniendo info para:", url)

    # Ruta absoluta al cookies.txt
    cookies_path = os.path.join(os.path.dirname(__file__), "cookies.txt")

    try:
        if not os.path.exists(cookies_path) or os.path.getsize(cookies_path) < 500:
            return jsonify({"error": "Archivo cookies.txt inválido o vacío. Asegúrate de exportarlo correctamente desde el navegador."}), 200

        with yt_dlp.YoutubeDL({
            'quiet': True,
            'cookiefile': cookies_path
        }) as ydl:
            info = ydl.extract_info(url, download=False)

            # Duración formateada
            duracion_segundos = info.get("duration", 0)
            minutos = duracion_segundos // 60
            segundos = duracion_segundos % 60
            duracion_formateada = f"{minutos}:{segundos:02d}"

            # Extraer resoluciones únicas disponibles
            resoluciones = []
            for f in info.get("formats", []):
                height = f.get("height")
                ext = f.get("ext")
                if height and ext == "mp4":
                    res_str = f"{height}p"
                    if res_str not in resoluciones:
                        resoluciones.append(res_str)

            resoluciones = list(set(resoluciones))
            resoluciones.sort(key=lambda r: int(r.replace("p", "").split()[0]), reverse=True)

            return jsonify({
                "title": info.get("title", "Sin título"),
                "duration": duracion_formateada,
                "thumbnail": info.get("thumbnail", ""),
                "resolutions": resoluciones
            })

    except Exception as e:
        print("❌ Error al obtener info:", str(e))
        return jsonify({"error": f"Error al obtener info: {str(e)}"}), 200


@app.route("/download", methods=["POST"])
def download():
    video_url = request.json["url"]
    print("🎧 URL recibida para descarga:", video_url)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "audio.%(ext)s")
        final_path = os.path.join(tmpdir, "audio.mp3")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                titulo = info.get("title", "audio")
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        if not os.path.exists(final_path):
            return jsonify({"error": "No se generó el archivo MP3"}), 500

        print("✅ MP3 generado:", final_path)

        # 🧠 Cargar archivo en memoria antes de cerrar el tempdir
        with open(final_path, "rb") as f:
            file_data = BytesIO(f.read())

    # 🔥 Ahora ya fuera del with, enviamos el archivo desde memoria
    response = make_response(send_file(file_data, as_attachment=True, download_name=f"{titulo}.mp3"))
    response.headers["X-Filename"] = f"{titulo}.mp3"
    response.headers["Access-Control-Expose-Headers"] = "X-Filename"
    return response

@app.route("/download_video", methods=["POST"])
def download_video():
    from slugify import slugify
    import traceback

    video_url = request.json.get("url")
    resolucion = request.json.get("resolucion", "720p").replace("p", "")
    print(f"📽️ Descargando {resolucion}p para:", video_url)

    cookies_path = os.path.join(os.path.dirname(__file__), "cookies.txt")

    # Validar cookies
    if not os.path.exists(cookies_path) or os.path.getsize(cookies_path) < 500:
        return jsonify({"error": "Archivo cookies.txt inválido o vacío. Exporta cookies válidas desde tu navegador estando logueado en YouTube."}), 500

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": f"bestvideo[height={resolucion}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "outtmpl": output,
            "merge_output_format": "mp4",
            "cookiefile": cookies_path,
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get("title", "video")
                slug = slugify(title)

            video_file = None
            for fname in os.listdir(tmpdir):
                if fname.endswith(".mp4"):
                    video_file = os.path.join(tmpdir, fname)
                    break

            if not video_file or not os.path.exists(video_file):
                raise FileNotFoundError("No se generó el archivo de video.")
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

        print("✅ Video listo:", video_file)

        with open(video_file, "rb") as f:
            file_data = BytesIO(f.read())

    response = make_response(send_file(file_data, as_attachment=True, download_name=f"{slug}.mp4"))
    response.headers["X-Filename"] = f"{slug}.mp4"
    response.headers["Access-Control-Expose-Headers"] = "X-Filename"
    return response

@app.route("/download_car", methods=["POST"])
def download_car():
    from slugify import slugify
    import subprocess
    import traceback

    video_url = request.json.get("url")
    print(f"🚗 Descargando video para auto desde: {video_url}")

    cookies_path = os.path.join(os.path.dirname(__file__), "cookies.txt")

    if not os.path.exists(cookies_path) or os.path.getsize(cookies_path) < 500:
        return jsonify({"error": "Archivo cookies.txt inválido o vacío."}), 500

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": output,
            "merge_output_format": "mp4",
            "cookiefile": cookies_path,
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get("title", "video")
                slug = slugify(title)

            video_file = None
            for fname in os.listdir(tmpdir):
                if fname.endswith(".mp4"):
                    video_file = os.path.join(tmpdir, fname)
                    break

            if not video_file or not os.path.exists(video_file):
                raise FileNotFoundError("No se generó el archivo de video.")

            # Archivo convertido
            converted_file = os.path.join(tmpdir, f"{slug}_car.mp4")

            # FFmpeg: conversión para autos
            ffmpeg_cmd = [
                "ffmpeg", "-i", video_file,
                "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0", "-pix_fmt", "yuv420p",
                "-preset", "fast", "-b:v", "1500k", "-maxrate", "1500k", "-bufsize", "3000k",
                "-vf", "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease,fps=30",
                "-c:a", "aac", "-ar", "44100", "-b:a", "128k",
                converted_file
            ]

            print("🎛️ Ejecutando FFmpeg para convertir a formato auto...")
            subprocess.run(ffmpeg_cmd, check=True)

        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

        print("✅ Video compatible con autos generado:", converted_file)

        with open(converted_file, "rb") as f:
            file_data = BytesIO(f.read())

    response = make_response(send_file(file_data, as_attachment=True, download_name=f"{slug}_car.mp4"))
    response.headers["X-Filename"] = f"{slug}_car.mp4"
    response.headers["Access-Control-Expose-Headers"] = "X-Filename"
    return response






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
