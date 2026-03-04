import network
import espnow
import socket
import ujson
import _thread

def create_server():
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        pass
    s.bind(("0.0.0.0", 80))
    s.listen(5)
    s.settimeout(2)
    return s


ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="ESP32-Robot", password="12345678")

while not ap.active():
    time.sleep(0.2)

print("IP:", ap.ifconfig()[0])


"""
ap = network.WLAN(network.AP_IF)
ap.active(True)
print("AP configuré. Adresse IP:", ap.ifconfig()[0])
"""

# --- Configuration ESP-NOW ---
sta = network.WLAN(network.STA_IF)
sta.active(True)
e = espnow.ESPNow()
e.active(True)

# Adresse MAC de l'ESP32 + K210 (à remplacer)
peer_mac = b'\xAA\xBB\xCC\xDD\xEE\xFF'
e.add_peer(peer_mac)

# Liste des panneaux détectés
detected_signs = []

# Callback pour recevoir les messages ESP-NOW
def espnow_receive():
    global detected_signs
    while True:
        if e.any():
            mac, msg = e.recv()
            try:
                sign = ujson.loads(msg)
                detected_signs.append(sign)
                print("Panneau reçu:", sign)
            except:
                pass

# Démarrage du thread de réception ESP-NOW
_thread.start_new_thread(espnow_receive, ())


#====================  HTML avec carte de fond et animations

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Contrôle Robot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .control-panel { background: #f0f0f0; padding: 10px; margin-bottom: 20px; }
        .control-panel button { padding: 10px 20px; margin: 5px; }
        .map-container {
            background: #e0e0e0;
            padding: 10px;
            height: 500px;
            position: relative;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 300 300"><rect width="300" height="300" fill="lightgray"/><path d="M50,150 Q150,50 250,150" stroke="darkgray" stroke-width="30" fill="none"/></svg>');
            background-size: cover;
        }
        .road-sign {
            position: absolute;
            transform: translate(-50%, -50%);
            opacity: 0;
            animation: fadeIn 0.5s forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
</head>
<body>
    <h1>Contrôle du Robot</h1>

    <!-- Zone de contrôle -->
    <div class="control-panel">
        <h2>Commandes</h2>
        <button onclick="sendCommand('forward')">Avant</button>
        <button onclick="sendCommand('backward')">Arrière</button>
        <button onclick="sendCommand('left')">Gauche</button>
        <button onclick="sendCommand('right')">Droite</button>
        <button onclick="sendCommand('stop')">Stop</button>
        <button onclick="sendCommand('speed1')">Vitesse 1</button>
        <button onclick="sendCommand('speed2')">Vitesse 2</button>
    </div>

    <!-- Zone de visualisation -->
    <div class="map-container" id="map">
        <h2>Trajet et panneaux détectés</h2>
    </div>

    <script>
        // Envoi des commandes au robot
        function sendCommand(cmd) {
            fetch('/command?cmd=' + cmd)
                .then(response => response.text())
                .then(data => console.log(data));
        }

        // Mise à jour des panneaux détectés
        function updateSigns() {
            fetch('/signs')
                .then(response => response.json())
                .then(signs => {
                    const map = document.getElementById('map');
                    // Conserve les panneaux existants pour éviter les clignotements
                    const existingSigns = map.querySelectorAll('.road-sign');
                    existingSigns.forEach(sign => sign.remove());

                    signs.forEach(sign => {
                        const signElement = document.createElement('div');
                        signElement.className = 'road-sign';
                        signElement.style.left = sign.x + 'px';
                        signElement.style.top = sign.y + 'px';
                        signElement.innerHTML = getSignSVG(sign.type);
                        map.appendChild(signElement);
                    });
                });
        }

        // SVG pour chaque panneau
        function getSignSVG(type) {
            const svgs = {
                "stop": `
                    <svg width="10" height="10" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="16" height="16" fill="red" rx="2" />
                        <text x="12" y="15" font-family="Arial" font-size="12" fill="white" text-anchor="middle">STOP</text>
                    </svg>
                `,
                "parking": `
                    <svg width="10" height="10" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" fill="blue" />
                        <text x="12" y="15" font-family="Arial" font-size="12" fill="white" text-anchor="middle">P</text>
                    </svg>
                `,
                "crosswalk": `
                    <svg width="10" height="10" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="16" height="16" fill="blue" rx="2" />
                        <path d="M8 10v4h3v-4h-3zm5 0v4h3v-4h-3z" fill="white" />
                    </svg>
                `,
                "roundabout": `
                    <svg width="40" height="40" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" fill="blue" />
                        <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm0-2a6 6 0 1 1 0 12 6 6 0 0 1 0-12z" fill="white" />
                    </svg>
                `,
                "priority_right": `
                    <svg width="40" height="40" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="16" height="16" fill="white" stroke="red" stroke-width="2" />
                        <path d="M12 8l4 4-4 4" stroke="red" stroke-width="2" fill="none" />
                    </svg>
                `,
                "yield": `
                    <svg width="40" height="40" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="16" height="16" fill="white" stroke="red" stroke-width="2" />
                        <text x="12" y="15" font-family="Arial" font-size="10" fill="red" text-anchor="middle">YIELD</text>
                    </svg>
                `,
                "speed30": `
                    <svg width="40" height="40" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" fill="white" stroke="red" stroke-width="2" />
                        <text x="12" y="15" font-family="Arial" font-size="12" fill="red" text-anchor="middle">30</text>
                    </svg>
                `
            };
            return svgs[type] || `
                <svg width="40" height="40" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" fill="gray" />
                    <text x="12" y="15" font-family="Arial" font-size="12" fill="white" text-anchor="middle">?</text>
                </svg>
            `;
        }

        // Mise à jour périodique
        setInterval(updateSigns, 1000);
    </script>
</body>
</html>
"""

# ==========  Gestion des requêtes HTTP et lancement du serveur

# --- Gestion des requêtes HTTP ---
def handle_request(request):
    if request.startswith("GET /command?cmd="):
        cmd = request.split("cmd=")[1].split(" ")[0]
        print("Commande reçue:", cmd)
        # Logique pour contrôler le robot (ex: PWM, GPIO)
        return "OK"
    elif request.startswith("GET /signs"):
        return ujson.dumps(detected_signs)
    else:
        return html

# --- Lancement du serveur ---
"""
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 80))
s.listen(5)
print("Serveur démarré. Attente de connexions...")
"""
server = create_server()
running = True
while running:
    try:
        conn, addr = server.accept()
    except OSError:
        continue

    try:
 
        request = conn.recv(1024).decode()
        response = handle_request(request)
        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n' + response)
        conn.close()

        """
        elif "GET /exit" in request:
            conn.send("HTTP/1.1 200 OK\r\n\r\nBYE")
            running = False

        else:
            conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
        """

    except Exception as e:
        print("Erreur:", e)

    finally:
        try:
            conn.close()
        except:
            pass

server.close()
ap.active(False)
camera.deinit()
gc.collect()
time.sleep(1)
machine.reset()


