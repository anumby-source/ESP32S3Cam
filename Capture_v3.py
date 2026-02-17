import network
import socket
import camera
import time
import gc
import os
import json

SSID = "Capture"
PASSWORD = "12345678"

DATASET_DIR = "/dataset"
INDEX_FILE = "/dataset/index.txt"

busy = False
server_running = True
last_saved_file = ""
series_total = 0
series_done = 0
series_running = False

index = {}


# ------------------
# CAMERA
# ------------------
def camera_init():
    camera.deinit()
    camera.init(0,
                d0=11, d1=9, d2=8, d3=10, d4=12, d5=18, d6=17, d7=16,
                format=camera.JPEG,
                framesize=camera.FRAME_QVGA,
                xclk_freq=camera.XCLK_10MHz,
                href=7, vsync=6, reset=-1, pwdn=-1,
                sioc=5, siod=4, xclk=15, pclk=13,
                fb_location=camera.PSRAM
                )
    camera.quality(12)
    print("Camera OK")


# ---------------- WIFI ----------------
def connect_wifi():
    # AP
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD, authmode=3)

    print("1")
    # Attendre que l'AP soit actif
    while ap.active() == False:
        time.sleep(0.5)

    print("2")

    # Attendre qu'une IP soit assignÃƒÂ©e
    time.sleep(2)

    print("3")

    print("Config:", ap.ifconfig())

    print("Connecte :", ap.ifconfig()[0])
    return ap.ifconfig()[0]


# ------------------
# FILES
# ------------------
def ensure_dir(path):
    try:
        os.mkdir(path)
    except:
        pass


def load_index():
    data = {}
    try:
        with open(INDEX_FILE) as f:
            for line in f:
                k, v = line.strip().split("=")
                data[k] = int(v)
    except:
        pass
    return data


def save_index(data):
    with open(INDEX_FILE, "w") as f:
        for k in data:
            f.write("%s=%d\n" % (k, data[k]))


def save_image(label, buf):
    global index
    global last_saved_file

    ensure_dir(DATASET_DIR)
    path = DATASET_DIR + "/" + label
    ensure_dir(path)

    if label not in index:
        index[label] = 0

    index[label] += 1

    filename = "%s/photo_%s_%04d.jpg" % (path, label, index[label])

    with open(filename, "wb") as f:
        f.write(buf)

    save_index(index)

    last_saved_file = filename

    print("Saved:", filename)


# ------------------
# HTTP UTILS
# ------------------
def get_param(req, name, default=None):
    try:
        path = req.split(" ")[1]
        if "?" in path:
            params = path.split("?")[1]
            for p in params.split("&"):
                k, v = p.split("=")
                if k == name:
                    return v
    except:
        pass
    return default


# ------------------
# STREAM
# ------------------
def handle_stream(cl):
    global busy

    cl.send("HTTP/1.1 200 OK\r\n")
    cl.send("Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n")

    try:
        while True:
            while busy:
                time.sleep(0.1)
                continue

            gc.collect()
            buf = camera.capture()

            cl.send("--frame\r\n")
            cl.send("Content-Type: image/jpeg\r\n\r\n")
            cl.send(buf)
            cl.send("\r\n")
    except:
        pass

    cl.close()


# ------------------
# CAPTURE
# ------------------
def handle_capture(label):
    global busy
    busy = True

    gc.collect()
    buf = camera.capture()
    save_image(label, buf)

    busy = False


def handle_serie(label, n, dt):
    global busy
    global series_total
    global series_done
    global series_running

    busy = True
    series_running = True
    series_total = n
    series_done = 0

    for i in range(n):
        gc.collect()
        buf = camera.capture()
        save_image(label, buf)

        series_done += 1
        time.sleep(dt / 1000)

    series_running = False
    busy = False


def handle_stop(cl):
    global server_running

    server_running = False

    cl.send("HTTP/1.1 200 OK\r\n")
    cl.send("Connection: close\r\n\r\n")
    cl.send("Server stopped")
    cl.close()

    time.sleep(1)
    machine.reset()


# ------------------
# PAGE
# ------------------
def send_page(cl):
    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
    cl.send("""
<html>
<body>
<h3>ESP32 Dataset</h3>
<img src="/stream" width="320"><br>
Label: <input id="label" value="01"><br>
Nombre:<input id="n" value="10">  delai(ms):<input id="dt" value="1000"><br><br>

<button onclick="f_capture()">Capture</button><br>
<button onclick="f_serie()">Serie</button><br>
<button onclick="f_stop()">Stop</button><br>

<h3>Dernière image :</h3>
<div id="lastfile">Aucune</div>

<h3>Compteurs par classe</h3>
<div id="counts">-</div>

<h3>Progression série</h3>
<progress id="prog" value="0" max="100"></progress>
<div id="progtext">0 / 0</div>

<script>

function f_capture(){
  let l = document.getElementById("label").value;
  fetch("/capture?label="+l);
}

function f_serie(){
  let l = document.getElementById("label").value;
  let n = document.getElementById("n").value;
  let dt = document.getElementById("dt").value;
  fetch("/serie?label="+l+"&n="+n+"&dt="+dt);
}

function updateLastFile(){
    fetch("/lastfile")
    .then(r => r.text())
    .then(t => {
        if(t){
            document.getElementById("lastfile").innerText = t;
        }
    });
}

function f_stop(){
  fetch("/stop");
}

function updateStatus(){
    fetch("/status")
    .then(r => r.json())
    .then(s => {

        // Dernier fichier
        document.getElementById("last").innerText = s.last;

        // Compteurs par classe
        let txt = "";
        for (let k in s.counts){
            txt += k + " : " + s.counts[k] + "<br>";
        }
        document.getElementById("counts").innerHTML = txt;

        // Progression série
        if(s.series_total > 0){
            let pct = 100 * s.series_done / s.series_total;
            document.getElementById("prog").value = pct;
            document.getElementById("progtext").innerText =
                s.series_done + " / " + s.series_total;
        }
    });
}

setInterval(updateLastFile, 500);

</script>
</body>
</html>
""")


# ------------------
# SERVER
# ------------------
def start_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    while True:
        try:
            s = socket.socket()
            s.bind(addr)
            s.listen(5)
            print("Ouvre : http://%s" % ip)
            break
        except:
            pass

    while server_running:
        try:
            cl, addr = s.accept()
        except OSError:
            continue  # timeout → on recheck server_running

        try:
            req = cl.recv(1024).decode()

            if "/stream" in req:
                handle_stream(cl)
                continue

            if "/status" in req:
                status = {
                    "last": last_saved_file,
                    "series_total": series_total,
                    "series_done": series_done,
                    "running": series_running,
                    "counts": index
                }

                cl.send("HTTP/1.1 200 OK\r\n")
                cl.send("Content-Type: application/json\r\n")
                cl.send("Connection: close\r\n\r\n")
                cl.send(json.dumps(status))
                cl.close()
                continue

            if "/capture" in req:
                label = get_param(req, "label", "default")
                handle_capture(label)
                cl.send("HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nOK")
                cl.close()
                continue

            if "/serie" in req:
                label = get_param(req, "label", "default")
                n = int(get_param(req, "n", "10"))
                dt = int(get_param(req, "dt", "1000"))
                handle_serie(label, n, dt)
                cl.send("HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nOK")
                cl.close()
                continue
            if "/lastfile" in req:
                cl.send("HTTP/1.1 200 OK\r\n")
                cl.send("Content-Type: text/plain\r\n")
                cl.send("Connection: close\r\n\r\n")
                cl.send(last_saved_file)
                cl.close()
                continue
            if "/stop" in req:
                handle_stop(cl)
                continue

            send_page(cl)
            cl.close()

        except Exception as e:
            print("Client error:", e)

        # print("Server stopping...")
        # s.close()
        # print("Server stopped")


# ------------------
# MAIN
# ------------------
camera_init()
ip = connect_wifi()
ensure_dir(DATASET_DIR)
index = load_index()
start_server(ip)


