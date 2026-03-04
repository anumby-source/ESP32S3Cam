import server

s = server.Server("ABCD")

s.set_style ("""
.start { background:green; color:white; }
""")

s.set_script("""
function start() {
    if (runningVideo) return;
    startTime = Date.now();
}
""")

s.set_body ("""
<button class="start" onclick="start()">Start</button>
""")
s.run()
