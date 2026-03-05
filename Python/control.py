import network
import espnow
import _thread
import server
import re

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

style = """
        body { font-family: Arial, sans-serif; margin: 20px; }
        .control-panel {
            background: #ffffff;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            color: red;
        }
        .control-panel button {
            padding: 10px 20px;
            margin: 8px;
            font-size: 20px;
            font-weight: bold;
            color: white;
            background-color: #4a6fa5;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        .control-panel button:hover {
            background-color: #3a5a8f;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        .control-panel button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        #panneaux-container {
            width: 500px;
            height: 200px;
            position: relative; /* Pour servir de référence aux éléments absolus */
            background-color: white;
            color: red;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden; /* Pour éviter que les panneaux ne débordent */
        }
        .panneau {
            width: 50px;
            height: 50px;
            position: absolute; /* Position absolue */
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            border: none;
            border-radius: 4px;
            transition: border 0.2s;
        }
        .panneau:hover {
            transform: scale(1.05);
        }
        .panneau.encadre {
            border: 3px solid red;
        }
        .panneau img {
            max-width: 90%;
            max-height: 90%;
        }
        #panneau1 { top: 20%; left: 20%; }
        #panneau2 { top: 20%; left: 50%; }
        #panneau3 { top: 20%; left: 80%; }
        #panneau4 { top: 50%; left: 20%; }
        #panneau5 { top: 50%; left: 50%; }
        #panneau6 { top: 50%; left: 80%; }
        #panneau7 { top: 30%; left: 5%; }
        #panneau8 { top: 30%; left: 90%; }

"""

body = """
    <!-- Zone de contrôle -->
    <div class="control-panel">
        <h2>Commandes</h2>
        <button onclick="sendCommand('forward')">Avant</button>
        <button onclick="sendCommand('stop')">Stop</button>
        <br>
        <button onclick="sendCommand('left')">Gauche</button>
        <button onclick="sendCommand('right')">Droite</button>
        <br>
        <button onclick="sendCommand('backward')">Arrière</button>
        <br>
        <button onclick="sendCommand('speed1')">Vitesse 1</button>
        <button onclick="sendCommand('speed2')">Vitesse 2</button>
        <br>
        <button onclick="resetEncadrements()">Réinitialiser</button>
    </div>

    <!-- Zone de visualisation -->
    <div id="panneaux-container">
        <div class="panneau" id="panneau1"><img src="/static/30.png" alt="Limitation 30"></div>
        <div class="panneau" id="panneau2"><img src="/static/cedez_le_passage.png" alt="Cédez le passage"></div>
        <div class="panneau" id="panneau3"><img src="/static/pietons.png" alt="Passage piétons"></div>
        <div class="panneau" id="panneau4"><img src="/static/priorite_a_droite.png" alt="Priorité à droite"></div>
        <div class="panneau" id="panneau5"><img src="/static/rond_point.png" alt="Rond point"></div>
        <div class="panneau" id="panneau6"><img src="/static/stationnement.png" alt="Stationnement interdit"></div>
        <div class="panneau" id="panneau7"><img src="/static/start.png" alt="Start"></div>
        <div class="panneau" id="panneau8"><img src="/static/stop.png" alt="Stop"></div>
    </div>
"""

script = """
        // Envoi des commandes au robot
        function sendCommand(cmd) {
            fetch('/command?cmd=' + cmd)
        }
        
        // Réinitialiser tous les encadrements
        function resetEncadrements() {
            document.querySelectorAll('.panneau').forEach(panneau => {
                panneau.classList.remove('encadre');
            });
        }
        
        // Encadrer un panneau spécifique
        function encadrerPanneau(id) {
            const panneau = document.getElementById(id);
            if (panneau) {
                panneau.classList.add('encadre');
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.panneau').forEach(panneau => {
                panneau.addEventListener('click', function() {
                    this.classList.toggle('encadre');
                    console.log("Click detecte !");
                });
            });        
        });
        
        
        // Mise à jour périodique
        // setInterval(updateSigns, 1000);
"""

"""
"""

# ==========  Gestion des requêtes HTTP et lancement du serveur

# --- Gestion des requêtes HTTP ---
def handle_request(server, request, conn):
    m = re.match(r"GET ([^ ]*) HTTP", request)
    if not m:
        conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
        return False

    print("my handle request=", m.group(1))
    path = m.group(1)
    if "/static/" in path:
        print("static file")
        f = path.split("/static/")[1].split()[0]
        try:
            with open(f"/static/{f}", "rb") as f:
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n")
                conn.send(f.read())
        except OSError as e:
            print(f"Erreur: {e}")
            conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
    elif path.startswith("/detect?"):
        # Exemple : /detect?id=panneau1
        panneau_id = path.split("id=")[1]
        response = f"""
        <script>
            window.onload = function() {{
                encadrerPanneau('{panneau_id}');
            }};
        </script>
        """
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        conn.send(response)
    elif path.startswith("/command?cmd"):
        cmd = path.split("cmd=")[1]
        print("commande=", cmd)
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    else:
        response = server.html()
        conn.send(response)
    conn.close()
    return True


# --- Lancement du serveur ---
serv = server.Server(title="Robot")
serv.set_style(style)
serv.set_script(script)
serv.set_body(body)

serv.run(handle_request)
serv.stop_server()


