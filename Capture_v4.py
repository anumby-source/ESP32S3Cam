import socket
import time
import gc
import os
import _thread
from machine import Pin
import camera
import network

socket.setdefaulttimeout(5)

# =============================
# CONFIG
# =============================
PORT = 80
DATASET_DIR = ""   # mettre "" si pas de carte SD

# Etat global
state = {
    "running": False,
    "current_label": "default",
    "count_total": 0,
    "count_done": 0,
    "last_file": "",
    "per_label": {},
    "stop": False
}

server_socket = None


# =============================
# WIFI INIT
# =============================
SSID = "Capture"
PASSWORD = "12345678"


# =============================
# WIFI INIT AP
# =============================
def init_wifi_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD)
    print("AP actif")
    ip = ap.ifconfig()[0]
    print("IP:", ip)
    return ip


# =============================
# WIFI INIT
# =============================
def init_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connexion WiFi...")
        wlan.connect(SSID, PASSWORD)

        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

    if wlan.isconnected():
        print("WiFi connecté")
        print("Adresse IP:", wlan.ifconfig()[0])
    else:
        print("Echec connexion WiFi")

    return wlan


# =============================
# CAMERA INIT
# =============================
def init_camera():
    camera.init(0, format=camera.JPEG)
    camera.framesize(camera.FRAME_VGA)
    camera.quality(10)
    print("Camera ready")


# =============================
# UTILS DATASET
# =============================
def ensure_label_dir(label):
    path = "%s/%s" % (DATASET_DIR, label)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def next_index(label):
    path = ensure_label_dir(label)
    files = os.listdir(path)
    nums = []
    for f in files:
        if f.endswith(".jpg"):
            try:
                nums.append(int(f.split("_")[-1].split(".")[0]))
            except:
                pass
    return max(nums) + 1 if nums else 0


# =============================
# CAPTURE
# =============================
def capture_one(label):
    gc.collect()
    buf = camera.capture()

    idx = next_index(label)
    filename = "%s_%04d.jpg" % (label, idx)
    path = "%s/%s/%s" % (DATASET_DIR, label, filename)

    with open(path, "wb") as f:
        f.write(buf)

    state["last_file"] = filename
    state["per_label"][label] = state["per_label"].get(label, 0) + 1

    return filename


def capture_series(label, total):
    state["running"] = True
    state["count_total"] = total
    state["count_done"] = 0
    state["current_label"] = label
    state["stop"] = False

    for i in range(total):
        if state["stop"]:
            break

        capture_one(label)
        state["count_done"] += 1
        time.sleep(0.5)

    state["running"] = False
    print("Series finished")


# =============================
# HTTP HELPERS
# =============================
def send(cl, data, content_type="text/html"):
    cl.send("HTTP/1.1 200 OK\r\n")
    cl.send("Content-Type: %s\r\n\r\n" % content_type)
    cl.send(data)


def get_param(req, name):
    try:
        part = req.split("?")[1].split(" ")[0]
        params = part.split("&")
        for p in params:
            if name in p:
                return p.split("=")[1]
    except:
        pass
    return ""


# =============================
# PAGE WEB
# =============================
def page():
    label = state["current_label"]
    done = state["count_done"]
    total = state["count_total"]
    percent = int((done / total) * 100) if total else 0
    last = state["last_file"]
    count_label = state["per_label"].get(label, 0)

    html = """
    <html>
    <head>
    <title>ESP32 Dataset</title>
    <script>
    function refresh(){
        fetch('/status').then(r=>r.json()).then(d=>{
            document.getElementById("last").innerHTML = d.last;
            document.getElementById("count").innerHTML = d.count_label;
            document.getElementById("progress").value = d.percent;
            document.getElementById("ptext").innerHTML = d.percent + "%";
        });
    }
    setInterval(refresh, 1000);
    </script>
    </head>

    <body>
    <h2>Dataset IA</h2>

    Label: <input id="label" value="%s"><br><br>

    <button onclick="location='/capture?label='+document.getElementById('label').value">
    Capture 1
    </button>

    <br><br>

    Série:
    <button onclick="location='/series?label='+document.getElementById('label').value+'&n=20'">
    20 images
    </button>

    <button onclick="location='/stop'">STOP</button>

    <h3>Status</h3>
    Dernier fichier: <span id="last">%s</span><br>
    Images classe: <span id="count">%d</span><br><br>

    <progress id="progress" value="%d" max="100"></progress>
    <span id="ptext">%d%%</span>

    </body>
    </html>
    """ % (label, last, count_label, percent, percent)

    return html


# =============================
# STATUS JSON (AJAX)
# =============================
def status_json():
    total = state["count_total"]
    done = state["count_done"]
    percent = int((done / total) * 100) if total else 0
    label = state["current_label"]

    return """{
    "last":"%s",
    "count_label":%d,
    "percent":%d
    }""" % (
        state["last_file"],
        state["per_label"].get(label, 0),
        percent
    )


# =============================
# SERVER
# =============================
def start_server():
    global server_socket

    try:
        server_socket.close()
    except:
        pass

    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen(5)

    ip = network.WLAN(network.STA_IF).ifconfig()[0]
    print("Serveur démarré sur: http://%s" % ip)

    print("Server started")

    while True:
        cl, addr = server_socket.accept()
        req = cl.recv(1024).decode()

        # ROUTES
        if "GET /capture" in req:
            label = get_param(req, "label") or "default"
            capture_one(label)
            send(cl, page())

        elif "GET /series" in req:
            label = get_param(req, "label") or "default"
            n = int(get_param(req, "n") or 10)
            _thread.start_new_thread(capture_series, (label, n))
            send(cl, page())

        elif "GET /stop" in req:
            state["stop"] = True
            send(cl, page())

        elif "GET /status" in req:
            send(cl, status_json(), "application/json")

        else:
            send(cl, page())

        cl.close()


# =============================
# MAIN
# =============================
def main():
    # init_wifi()
    init_wifi_ap()
    init_camera()
    start_server()

main()

