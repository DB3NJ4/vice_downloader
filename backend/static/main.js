const API_URL = "http://34.42.138.190:5000";

// Función para obtener info del video
async function obtenerInfo() {
  const url = document.getElementById("url").value;
  if (!url) return alert("Pega un link primero");

  mostrarLoader();

  try {
    const res = await fetch(`${API_URL}/info?url=${encodeURIComponent(url)}`);
    const data = await res.json();

    if (data.error) {
      alert("Error al obtener info del video.");
      return;
    }

    document.getElementById("titulo").innerText = data.title;
    document.getElementById("duracion").innerText = "Duración: " + data.duration;
    document.getElementById("thumbnail").src = data.thumbnail;
    document.getElementById("urlFinal").value = url;
    document.getElementById("preview").style.display = "block";
  } catch (error) {
    console.error("❌ Error al obtener info:", error);
    alert("Hubo un error al conectarse con el servidor.");
  } finally {
    ocultarLoader();
  }
}

// Función para descargar el MP3
async function descargarMP3() {
  console.log("▶ Botón de descarga presionado");
  const url = document.getElementById("urlFinal").value;

  if (!url) return alert("No hay URL válida para descargar.");

  mostrarLoader();

  try {
    const res = await fetch(`${API_URL}/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      let errorMsg = "No se pudo descargar el archivo.";
      try {
        const error = await res.json();
        errorMsg = error.error || errorMsg;
      } catch (_) {}
      alert("❌ Error: " + errorMsg);
      return;
    }

    // 💡 Aquí capturamos el nombre desde el header del backend
    const filename = res.headers.get("X-Filename") || "mi_cancion.mp3";

    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  } catch (err) {
    console.error("❌ Error inesperado:", err);
    alert("❌ Error inesperado: " + err.message);
  } finally {
    ocultarLoader();
  }
}

// Loader visual
function mostrarLoader() {
  document.getElementById("loader").style.display = "block";
}

function ocultarLoader() {
  document.getElementById("loader").style.display = "none";
}

// Conectar eventos al DOM
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnInfo").addEventListener("click", obtenerInfo);
  document.getElementById("btnDescargar").addEventListener("click", descargarMP3);
});
