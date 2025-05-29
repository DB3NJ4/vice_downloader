from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import yt_dlp
from slugify import slugify  # pip install python-slugify
import os
import tempfile
from io import BytesIO

app = Flask(__name__)
CORS(app)


@app.route("/info")
def info():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "No se proporcionó ninguna URL"}), 400

    print("🔍 Obteniendo info para:", url)

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
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

            # Ordenar por valor numérico descendente (1080 > 720 > 480...)
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
        return jsonify({"error": f"Error al obtener info: {str(e)}"}), 500

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
    video_url = request.json.get("url")
    resolucion = request.json.get("resolucion", "720p").replace("p", "")
    print(f"📽️ Descargando {resolucion}p para:", video_url)

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": f"bestvideo[height={resolucion}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "outtmpl": output,
            "merge_output_format": "mp4",
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
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

        print("✅ Video listo:", video_file)

        with open(video_file, "rb") as f:
            file_data = BytesIO(f.read())

    response = make_response(send_file(file_data, as_attachment=True, download_name=f"{slug}.mp4"))
    response.headers["X-Filename"] = f"{slug}.mp4"
    response.headers["Access-Control-Expose-Headers"] = "X-Filename"
    return response


if __name__ == "__main__":
    app.run(debug=True)
