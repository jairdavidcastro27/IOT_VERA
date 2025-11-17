# app.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from models import db, Alerta
from datetime import datetime
import os

app = Flask(__name__)

# TU BASE DE DATOS DE RAILWAY (ya incluida)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:rCZnTfVYDdrCRweXljbxZldipWzegASf@yamabiko.proxy.rlwy.net:15990/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'alarma-laser-2025-super-secreta'

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Crear tablas si no existen
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    alertas = Alerta.query.order_by(Alerta.timestamp.desc()).limit(25).all()
    return render_template('index.html', alertas=alertas)

@app.route('/alerta', methods=['POST'])
def recibir_alerta():
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', '¡INTRUSO DETECTADO!') if data else '¡INTRUSO DETECTADO!'
        
        nueva_alerta = Alerta(mensaje=mensaje)
        db.session.add(nueva_alerta)
        db.session.commit()

        alerta_dict = {
            "id": nueva_alerta.id,
            "mensaje": nueva_alerta.mensaje,
            "timestamp": nueva_alerta.timestamp.strftime("%H:%M:%S %d/%m/%Y")
        }

        # Enviar a todos los navegadores conectados
        socketio.emit('nueva_alerta', alerta_dict)

        return jsonify({"success": True, "alerta": alerta_dict}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def cliente_conectado():
    print(f"Cliente conectado: {request.sid}")

if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=False,
        use_reloader=False
    )