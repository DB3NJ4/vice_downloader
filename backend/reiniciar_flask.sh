#!/bin/bash

PUERTO=5000

echo "🔎 Buscando procesos en el puerto $PUERTO..."
PIDS=$(lsof -ti :$PUERTO)

if [ -n "$PIDS" ]; then
  echo "⚠️ Se encontraron procesos usando el puerto $PUERTO: $PIDS"
  echo "🔪 Terminando procesos..."
  kill -9 $PIDS
  echo "✅ Puerto liberado."
else
  echo "✅ El puerto $PUERTO está libre."
fi

echo "🚀 Iniciando Flask en 0.0.0.0:$PUERTO"
python3 app.py --host=0.0.0.0 --port=$PUERTO
