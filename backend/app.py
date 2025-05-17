from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import yt_dlp
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
            return jsonify({
                "title": info.get("title", "Sin título"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", "")
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

if __name__ == "__main__":
    app.run(debug=True)
