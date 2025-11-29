from flask import Flask, request, jsonify
from flask_cors import CORS
from mcstatus import JavaServer, BedrockServer
import time

app = Flask(__name__)
CORS(app)

@app.route('/api/status', methods=['POST'])
def check_server():
    data = request.json
    address = data.get('address', '').strip()
    
    if not address:
        return jsonify({'error': 'Alamat server kosong'}), 400

    result = {
        "online": False,
        "type": "Unknown",
        "motd": "",
        "players": {"online": 0, "max": 0},
        "version": "",
        "icon": None,
        "latency": 0
    }

    # 1. Coba Scan sebagai JAVA Edition
    try:
        # Gunakan lookup agar otomatis handle domain & port
        server = JavaServer.lookup(address)
        status = server.status()
        
        result["online"] = True
        result["type"] = "Java Edition"
        result["motd"] = status.description
        result["players"] = {"online": status.players.online, "max": status.players.max}
        result["version"] = status.version.name
        result["latency"] = round(status.latency)
        result["icon"] = status.favicon # Base64 image
        
        return jsonify(result)
    except:
        pass # Lanjut ke Bedrock jika gagal

    # 2. Coba Scan sebagai BEDROCK Edition
    try:
        server = BedrockServer.lookup(address)
        status = server.status()
        
        result["online"] = True
        result["type"] = "Bedrock Edition"
        result["motd"] = status.motd
        result["players"] = {"online": status.players.online, "max": status.players.max}
        result["version"] = status.version.name or "Unknown"
        result["latency"] = round(status.latency * 1000) # Bedrock latency dalam detik, ubah ke ms
        
        return jsonify(result)
    except:
        pass

    # Jika sampai sini berarti OFFLINE di kedua metode
    return jsonify({"error": "Server offline atau tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(debug=True)
