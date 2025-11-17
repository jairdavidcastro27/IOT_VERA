# app.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from models import db, Alerta
from datetime import datetime
import os

app = Flask(__name__)

# Base de datos (funciona en Railway y local)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:rCZnTfVYDdrCRweXljbxZldipWzegASf@yamabiko.proxy.rlwy.net:15990/railway'
).replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'alarma-laser-2025-super-secreta'

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Crear tablas si no existen
with app.app_context():
    db.create_all()

# === PÁGINA PRINCIPAL ===
@app.route('/')
def index():
    alertas = Alerta.query.order_by(Alerta.timestamp.desc()).limit(25).all()
    return render_template('index.html', alertas=alertas)

# === RECIBIR ALERTA DEL ESP32 (POST) + DEVOLVER ALERTAS (GET) ===
@app.route('/alerta', methods=['GET', 'POST'])
def alerta():
    if request.method == 'POST':
        # Recibir desde ESP32
        try:
            data = request.get_json(silent=True) or {}
            mensaje = data.get('mensaje', '¡INTRUSO DETECTADO!')
            
            nueva = Alerta(mensaje=mensaje)
            db.session.add(nueva)
            db.session.commit()

            alerta_dict = {
                "id": nueva.id,
                "mensaje": nueva.mensaje,
                "timestamp": nueva.timestamp.strftime("%H:%M:%S %d/%m/%Y")
            }

            # Enviar por WebSocket (si hay clientes)
            socketio.emit('nueva_alerta', alerta_dict)

            return jsonify({"success": True, "alerta": alerta_dict}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:  # GET → polling del navegador
        alertas = Alerta.query.order_by(Alerta.timestamp.desc()).limit(30).all()
        return jsonify({
            "alertas": [
                {
                    "timestamp": a.timestamp.strftime("%H:%M:%S %d/%m/%Y"),
                    "mensaje": a.mensaje
                }
                for a in alertas
            ]
        })

# === WEBSOCKET ===
@socketio.on('connect')
def cliente_conectado():
    print(f"Cliente conectado: {request.sid}")

# === INICIAR SERVIDOR (Railway + local) ===
if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=False,
        use_reloader=False
    )