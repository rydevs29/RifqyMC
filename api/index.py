from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

def normalize_data(source, data, server_type):
    """Fungsi untuk menyamakan format data dari berbagai API"""
    result = {
        "online": False,
        "host": "",
        "port": 0,
        "motd": "",
        "players": {"online": 0, "max": 0},
        "version": "",
        "icon": None,
        "source": source
    }

    if source == "mcsrvstat.us":
        if data.get("online"):
            result["online"] = True
            result["host"] = data.get("hostname")
            result["port"] = data.get("port")
            # Motd di mcsrvstat bisa berupa array html atau clean
            motd_clean = data.get("motd", {}).get("clean", [])
            result["motd"] = " ".join(motd_clean) if isinstance(motd_clean, list) else str(motd_clean)
            result["players"]["online"] = data.get("players", {}).get("online", 0)
            result["players"]["max"] = data.get("players", {}).get("max", 0)
            result["version"] = data.get("version")
            result["icon"] = data.get("icon") # Base64
            
    elif source == "mcstatus.io":
        if data.get("online"):
            result["online"] = True
            result["host"] = data.get("host")
            result["port"] = data.get("port")
            # Motd di mcstatus.io
            result["motd"] = data.get("motd", {}).get("clean", "")
            result["players"]["online"] = data.get("players", {}).get("online", 0)
            result["players"]["max"] = data.get("players", {}).get("max", 0)
            result["version"] = data.get("version", {}).get("name_clean") or data.get("version", {}).get("name")
            result["icon"] = data.get("icon") # Base64

    return result

@app.route('/api/status', methods=['POST'])
def check_server():
    data = request.json
    address = data.get('address', '').strip()
    # User memilih tipe: 'java' atau 'bedrock'
    srv_type = data.get('type', 'java').lower() 
    
    if not address:
        return jsonify({'error': 'Alamat kosong'}), 400

    # --- 1. COBA PRIMARY API (mcsrvstat.us v3) ---
    try:
        if srv_type == 'bedrock':
            url_primary = f"https://api.mcsrvstat.us/bedrock/3/{address}"
        else:
            url_primary = f"https://api.mcsrvstat.us/3/{address}"
            
        resp = requests.get(url_primary, timeout=5)
        data_primary = resp.json()

        if data_primary.get("online") == True:
            return jsonify(normalize_data("mcsrvstat.us", data_primary, srv_type))
            
    except Exception as e:
        print(f"Primary API Error: {e}")

    # --- 2. COBA BACKUP API (mcstatus.io v2) ---
    try:
        # mcstatus.io endpoint structure
        url_backup = f"https://api.mcstatus.io/v2/status/{srv_type}/{address}"
        
        resp = requests.get(url_backup, timeout=5)
        data_backup = resp.json()
        
        if data_backup.get("online") == True:
            return jsonify(normalize_data("mcstatus.io", data_backup, srv_type))
            
    except Exception as e:
        print(f"Backup API Error: {e}")

    # Jika kedua API bilang offline atau error
    return jsonify({
        "online": False, 
        "error": "Server offline di kedua API (mcsrvstat & mcstatus)"
    })

if __name__ == '__main__':
    app.run(debug=True)
