import network
import time
import socket
import gc
import machine

SSID = "ESP32-CAM"
PASSWORD = "12345678"
PORT = 80



# =====================
# SERVER
# =====================

class Server:
    def __init__(self, title="ESP32-S3", style = "", script="", body=""):
        self.set_title(title)
        self.set_style(style)
        self.set_script(script)
        self.set_body(body)
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(True)
        self.ap.config(essid=SSID, password=PASSWORD)

        while not self.ap.active():
            time.sleep(0.2)

        print("IP:", self.ap.ifconfig()[0])

        self.s = socket.socket()
        try:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            pass
        self.s.bind(("0.0.0.0", PORT))
        self.s.listen(5)
        self.s.settimeout(2)
        self.running = False

    def set_title(self, title):
        self.title = title

    def set_style(self, style=""):
        self.style = style

    def set_script(self, script=""):
        self.script = script

    def set_body(self, body=""):
        self.body = body

    def stop_server(self):
        self.s.close()
        self.ap.active(False)
        gc.collect()
        time.sleep(1)
        machine.reset()

    def html(self):
        return """HTTP/1.1 200 OK
    Content-Type: text/html

    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>""" + self.title + """</title>

    <style>
    body { background:#111; color:white; text-align:center; font-family:Arial; }
    button { padding:10px 20px; margin:5px; font-size:15px; border:none; border-radius:8px; }
    .exit { background:#900; color:white; }
    .card { background:#222; padding:20px; border-radius:15px; display:inline-block; }
    input { padding:5px; font-size:16px; width:80px; }
    .running { color:orange; font-weight:bold; }
    """ + self.style + """
    </style>

    <script>

    function exitServer() {
        fetch("/exit");
    }
    function testServer() {
        fetch("/test");
    }
    
    """ + self.script + """
    </script>

    </head>

    <body>
    <div class="card">

    <h2>""" + self.title + """</h2>
    <br>""" + self.body + """
    <button class="exit" onclick="exitServer()">Exit</button>

    </div>
    </body>
    </html>
    """

    #     <button class="exit" onclick="testServer()">Test</button>

    def handle_request(self, request, conn):
        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
        conn.close()

    def run(self, my_handle_request=None):
        self.running = True

        while self.running:
            try:
                conn, addr = self.s.accept()
            except OSError:
                continue

            try:
                request = conn.recv(1024).decode()
                # print("server> request", request[0:60])

                if not my_handle_request is None:
                    # print("handling my request", request[0:60])
                    if my_handle_request(self, request, conn):
                        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
                        conn.close()
                        

                if "GET /exit" in request:
                    self.running = False

                    # print("server> exit")

                    # conn.send("HTTP/1.1 200 OK\r\n\r\nBYE")
                    # conn.close()
                    self.stop_server()
                    break

                # elif "GET /test" in request:
                #     conn.send("HTTP/1.1 200 OK\r\n\r\nTEST")

                elif "GET / " in request:
                    conn.send(self.html())
                    conn.close()

                else:
                    conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
                    conn.close()

            except Exception as e:
                # print("Erreur:", e)
                pass

            finally:
                try:
                    conn.close()
                except:
                    break

        print("BYE")

#============================
