Source firmware ESP32S3-Cam :

https://github.com/Freenove/Freenove_ESP32_S3_WROOM_Board/tree/main/Python/Python_Codes/05.1_Camera_WebServer

Pour le Camera_WebServer, voir le tuto Freenove "Python_Tutorial.pdf".

Attention :
 - les pins 35, 36, 37 sont indisponibles a cause de la PSRAM (?) (marquées * sur la board)
 - quand on utilise le module avec une SDcard, les pins 38, 39, 40 sont indisponibles (marquées ~ sur la board)
 - quand on utilise la caméra, les pins 4 à 18 (sauf14) sont indisponibles (soulignées sur la board)
 - la pin 48 est utilisées par la neopixel

Le firmware contient le driver pour le st7789
