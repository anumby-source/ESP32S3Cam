import network
import espnow
import _thread
import server
import re
import time
import ujson

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

#====================  Classe Robot

class Robot:
    def __init__(self):
        self.etat = 0  # -1: recule, 0: arrêté, 1: avance
        self.speed = 1  # 1 ou 2

        self.start_time = None
        self.penalties = 0
        self.game_active = False
        self.detected_signs = set()
        self.required_signs = {"p30", "pietons", "cedez_le_passage", "priorite_a_droite", "stationnement", "stop", "start"}
        self.required_signs_id = {"p05", "p03", "p04", "p02", "p01", "p06", "p07"}
        self.stop_time = None

    def start_game(self):
        self.start_time = time.time()
        self.game_active = True
        self.penalties = 0
        self.detected_signs.clear()
        print("Jeu démarré !")

    def stop_game(self):
        if self.game_active:
            self.stop_time = None
            self.game_active = False
            print("Jeu terminé !")

    def add_penalty(self, seconds):
        self.penalties += seconds
        print(f"Pénalité ajoutée : {seconds} secondes")

    def detect_sign(self, sign_id):
        if self.game_active and sign_id in self.required_signs_id:
            self.detected_signs.add(sign_id)
            print(f"Panneau détecté : {sign_id}")

            # Règles de pénalités
            if sign_id in ["p03", "p04", "p02"]:
                if self.etat != 0:
                    self.add_penalty(5)  # 5 secondes de pénalité si on ne s'arrête pas
            elif sign_id in ["p05"]:
                if self.speed != 1:
                    self.add_penalty(3)  # 3 secondes de pénalité si vitesse incorrecte
            elif sign_id == "p01":
                if self.etat == 0:
                    self.add_penalty(2)  # 2 secondes de pénalité si arrêté
            elif sign_id == "p06":
                self.stop_game()

    def get_elapsed_time(self):
        if self.start_time is None:
            return 0
        if self.stop_time is not None:
            return self.stop_time - self.start_time
        return int(time.time() - self.start_time)

    def get_total_score(self):
        if self.start_time is None:
            return 0
        return int(self.get_elapsed_time() + self.penalties)

    def get_penalties(self):
        return int(self.penalties)

    def set_etat(self, nouvel_etat):
        if nouvel_etat in [-1, 0, 1]:
            self.etat = nouvel_etat
            print(f"État du robot mis à jour : {self.etat}")
        else:
            print(f"État invalide : {nouvel_etat}")

    def set_speed(self, nouvel_speed):
        if nouvel_speed in [1, 2]:
            self.speed = nouvel_speed
            print(f"Vitesse du robot mis à jour : {self.speed}")
        else:
            print(f"Vitesse invalide : {nouvel_speed}")

    def get_etat(self):
        return self.etat

    def get_speed(self):
        return self.speed
    
    def get_combined_etat(self):
        return self.etat * self.speed

    def show_etat(self):
        return f"État : {self.get_etat()} Vitesse : {self.get_speed()}"

robot = Robot()


def get_etat_color(etat, speed):
    combined_etat = etat * speed
    colors = {
        -2: "#FF6347",  # Tomate (Recule vite)
        -1: "#FFA07A",  # Saumon (Recule lentement)
        0: "#32CD32",   # Vert lime (Arrêt)
        1: "#4169E1",   # Bleu royal (Vitesse 1 avant)
        2: "#1E90FF"    # Bleu dodger (Vitesse 2 avant)
    }
    return colors.get(combined_etat, "#808080")  # Gris par défaut



#====================  HTML avec carte de fond et animations

"""
        .boutons-commande {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
"""

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
        .etat-robot {
            padding: 10px;
            margin-bottom: 15px;
            text-align: center;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            font-size: 16px;
        }
        #panneaux-container {
            width: 600px;
            height: 300px;
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

        #p05 { top: 40%; left: 20%; }
        #p04 { top: 40%; left: 40%; }
        #p03 { top: 40%; left: 60%; }
        #p02 { top: 80%; left: 30%; }
        #p01 { top: 80%; left: 50%; }
        #p07 { top: 65%; left: 5%; }
        #p06 { top: 65%; left: 80%; }

        #game-info {
            position: absolute;
            top: 10px;
            left: 10px;
            background-color: rgba(255, 255, 255, 0.8);
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
            z-index: 10;
        }
    
        #game-info p {
            margin: 5px 0;
        }
"""


etat_robot = f"État : {robot.get_etat()} Vitesse : {robot.get_speed()}"

body = """
    <!-- Zone de contrôle -->
    <div class="control-panel">
        <h2>Commandes</h2>
        <div class="etat-robot" id="etat-robot" style="background-color: {get_etat_color(robot.get_etat(), robot.get_speed())};">
            {etat_robot} 
        </div>
        <div class="boutons-commande">
            <button onclick="sendCommand('forward')">Avant</button>
            <button onclick="sendCommand('backward')">Arrière</button>
            <button onclick="sendCommand('stop')">Stop</button>
            <br>
            <button onclick="sendCommand('left')">Gauche</button>
            <button onclick="sendCommand('right')">Droite</button>
            <br>
            <button onclick="sendCommand('speed1')">Vitesse 1</button>
            <button onclick="sendCommand('speed2')">Vitesse 2</button>
            <br>
            <button onclick="resetGame()">Réinitialiser</button>
        </div>
    </div>

    <!-- Zone de visualisation -->
    <div id="panneaux-container">
        <div id="game-info">
            Temps écoulé : <span id="elapsed-time">0</span> secondes
            Pénalités : <span id="penalties">0</span> secondes
            Score total : <span id="total-score">0</span> secondes
        </div>

        <div class="panneau" id="p05"><img src="/static/30.png" alt="Limitation 30"></div>
        <div class="panneau" id="p04"><img src="/static/cedez_le_passage.png" alt="Cédez le passage"></div>
        <div class="panneau" id="p03"><img src="/static/pietons.png" alt="Passage piétons"></div>
        <div class="panneau" id="p02"><img src="/static/priorite_a_droite.png" alt="Priorité à droite"></div>
        <div class="panneau" id="p01"><img src="/static/stationnement.png" alt="Stationnement interdit"></div>
        <div class="panneau" id="p07"><img src="/static/start.png" alt="Start"></div>
        <div class="panneau" id="p06"><img src="/static/stop.png" alt="Stop"></div>
    </div>
"""

script = """
        // Envoi des commandes au robot
        function sendCommand(cmd) {
            fetch('/command?cmd=' + cmd)
                .then(response => response.text())
                .then(() => {
                    updateEtatRobot();
                });
        }

        // Réinitialiser tous les encadrements
        function resetEncadrements() {
            document.querySelectorAll('.panneau').forEach(panneau => {
                panneau.classList.remove('encadre');
            });
        }
        
        function resetGame() {
            fetch('/reset_game')
                .then(() => {
                    updateEtatRobot();
                    updateGameInfo();
                    resetEncadrements();
                });
        }
                
        // Encadrer un panneau spécifique
        function encadrerPanneau(id) {
            const panneau = document.getElementById(id);
            if (panneau) {
                panneau.classList.add('encadre');
                fetch('/detect?id=' + id)
                    .then(() => updateGameInfo());
            }
        }
        
        // Mettre à jour l'affichage de l'état du robot
        function updateEtatRobot() {
            fetch('/etat')
                .then(response => response.text())
                .then(etat => {
                    fetch('/speed')
                        .then(response => response.text())
                        .then(speed => {
                            const etatRobotDiv = document.getElementById('etat-robot');
                            let color;
                            let combinedEtat = parseInt(etat) * parseInt(speed);
                            switch(combinedEtat) {
                                case -2: color = "#FF6347"; break; // Tomate
                                case -1: color = "#FFA07A"; break; // Saumon
                                case 0: color = "#32CD32"; break;  // Vert lime
                                case 1: color = "#4169E1"; break;  // Bleu royal
                                case 2: color = "#1E90FF"; break;  // Bleu dodger
                                default: color = "#808080";        // Gris
                            }
                            etatRobotDiv.style.backgroundColor = color;
                            etatRobotDiv.textContent = "État : " + etat + " Vitesse : " + speed;
                        });
                });
        }

        // Mettre à jour les informations de jeu
        function updateGameInfo() {
            fetch('/elapsed_time')
                .then(response => response.text())
                .then(elapsedTime => {
                    document.getElementById('elapsed-time').textContent = elapsedTime;
                })
                .catch(error => console.error("Erreur lors de la récupération du temps écoulé :", error));
    
            fetch('/penalties')
                .then(response => response.text())
                .then(penalties => {
                    document.getElementById('penalties').textContent = penalties;
                })
                .catch(error => console.error("Erreur lors de la récupération des pénalités :", error));
    
            fetch('/total_score')
                .then(response => response.text())
                .then(totalScore => {
                    document.getElementById('total-score').textContent = totalScore;
                })
                .catch(error => console.error("Erreur lors de la récupération du score total :", error));
        }

        document.addEventListener('DOMContentLoaded', function() {
            console.log("Script chargé et DOM prêt !");
            document.querySelectorAll('.panneau').forEach(panneau => {
                panneau.addEventListener('click', function() {
                    this.classList.toggle('encadre');
                    encadrerPanneau(this.id);
                    console.log("Click detecte !");
                });
            });       
            updateEtatRobot();
            updateGameInfo();
            setInterval(updateGameInfo, 1000); 
        });
        
        
        // Mise à jour périodique
        // setInterval(updateGameInfo, 1000); 
"""

# ==========  Gestion des requêtes HTTP et lancement du serveur

# --- Gestion des requêtes HTTP ---
def handle_request(server, request, conn):
    global etat_robot
    m = re.match(r"GET ([^ ]*) HTTP", request)
    if not m:
        conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
        return False

    # print("my handle request=", m.group(1))
    path = m.group(1)
    if "/static/" in path:
        # print("static file")
        f = path.split("/static/")[1].split()[0]
        try:
            with open(f"/static/{f}", "rb") as f:
                conn.send("HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n")
                conn.send(f.read())
        except OSError as e:
            # print(f"Erreur: {e}")
            conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
    elif path.startswith("/detect?"):
        sign_id = path.split("id=")[1].split()[0]
        robot.detect_sign(sign_id)
        print("detect=", sign_id)
        if sign_id == "p07":
            robot.start_game()
        elif sign_id == "p06":
            robot.stop_game()
        conn.send("HTTP/1.1 200 OK\r\n\r\n")
    elif path.startswith("/command?cmd"):
        cmd = path.split("cmd=")[1].split()[0]
        if cmd == "forward":
            robot.set_etat(1)
        elif cmd == "backward":
            robot.set_etat(-1)
        elif cmd == "speed1":
            robot.set_speed(1)
        elif cmd == "speed2":
            robot.set_speed(2)
        elif cmd == "stop":
            robot.set_etat(0)
            robot.stop_game()
        print("commande=", cmd)
        conn.send("HTTP/1.1 200 OK\r\n\r\n")
    elif path == "/etat":
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{robot.get_etat()}")
    elif path == "/speed":
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{robot.get_speed()}")
    elif path == "/elapsed_time":
        elapsed_time = int(robot.get_elapsed_time())
        # print(f"Temps écoulé : {elapsed_time}")
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{elapsed_time}")
    elif path == "/penalties":
        # print(f"Pénalités : {robot.penalties}")
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{robot.penalties}")
    elif path == "/total_score":
        total_score = int(robot.get_total_score())
        # print(f"Score total : {total_score}")
        conn.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{total_score}")
    elif path == "/reset_game":
        robot.stop_game()
        conn.send("HTTP/1.1 200 OK\r\n\r\n")
    else:
        etat_robot = robot.show_etat()
        response = server.html().replace("{etat_robot}", etat_robot)
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


