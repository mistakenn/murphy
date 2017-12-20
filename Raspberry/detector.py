
from PIL import Image
from socket import *
import numpy as np
import threading
import argparse
import serial
import time
import sys
import cv2
import os

classes = [
    'background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle',
    'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog',
    'horse', 'motorbike', 'person', 'pottedplant', 'sheep',
    'sofa', 'train', 'tvmonitor'
]

objects = {
    'aviao': 'aeroplane',
    'bicicleta': 'bicycle',
    'passaro': 'bird',
    'canoa': 'boat',
    'garrafa': 'bottle',
    'onibus': 'bus',
    'carro': 'car',
    'gato': 'cat',
    'cadeira': 'chair',
    'vaca': 'cow',
    'mesa': 'diningtable',
    'cachorro': 'dog',
    'cavalo': 'horse',
    'motocicleta': 'motorbike', 'moto': 'motorbike',
    'pessoa': 'person', 'humano': 'person',
    'planta': 'pottedplant',
    'ovelha': 'sheep',
    'sofa': 'sofa',
    'trem': 'train',
    'tv': 'tvmonitor', 'televisao': 'tvmonitor', 'monitor': 'tvmonitor'
}

arduino_cmds = {
    'forward': '1',
    'turn_right': '2',
    'turn_left': '3',
    'backward': '4',
    'beep': '5',
    'find': '6'
}

colors = np.random.uniform(0, 255, size=(len(classes), 3))
socket_num = 3000
arduin_com = serial.Serial('/dev/ttyACM0', 9600)
msecs_per_pixel_lft = 1.5
msecs_per_pixel_rgt = 1.7
msecs_per_unit = 10

def log(message):
    log_file = open('/home/pi/Robotics/ObjDetector/report.log', 'a')
    log_file.write(message+'\n')
    log_file.close()

def predict(image, net, obj):
    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    log('[NET] Starting predict')
    net.setInput(blob)
    detections = net.forward()
    log('[NET RESULTS] Starting to verify results: ' + str(detections.shape[2]) + ' of them')
    for i in np.arange(0, detections.shape[2]):
        log('[NET RESULTS] Verifying result of index: ' + str(i))
    	confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            idx = int(detections[0, 0, i, 1])
            if idx >= len(classes):
                log('[ERROR] Index error on predict')
                continue
            if classes[idx] == obj:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                coords = list(box.astype('int')) # Xi, Yi, Xf, Yf
                for j in range(0, 4):
                    coords[j] = max(0, min(300, coords[j]))
                log('[NET RESULTS] Object found at ' + str(coords))
                return coords
    log('[NET RESULTS] Object not found')
    return False

def capture_predict(obj):
    net = cv2.dnn.readNetFromCaffe('/home/pi/Robotics/ObjDetector/MobileNetSSD_deploy.prototxt', '/home/pi/Robotics/ObjDetector/MobileNetSSD_deploy.caffemodel')
    log('[WEBCAM] Taking photo')
    os.system('fswebcam -r 299x299 --jpeg 85 -S 10 -q /home/pi/Robotics/ObjDetector/teste.jpg')
    image = cv2.imread('/home/pi/Robotics/ObjDetector/teste.jpg')
    return predict(image, net, obj)

def arduino_move(action, msecs):
    units = int(round(float(msecs) / msecs_per_unit))
    while units > 0:
        arduin_com.write(arduino_cmds[action] + str(min(9, units-1)))
        units -= min(10, units)
    time.sleep((msecs * 1.05) / 1000.0)

def arduino_beep(times):
    arduin_com.write('5' + str(min(9, max(0, times-1))))

def arduino_run():
    arduin_com.write('6')

def centralize(bounding_box):
    diff = 150 - (bounding_box[0] + bounding_box[2]) // 2
    action = 'turn_right' if diff < 0 else 'turn_left'
    msecs = abs(diff) * (msecs_per_pixel_lft if action == 'turn_left' else msecs_per_pixel_rgt)
    arduino_move(action, msecs)

# rotate 300ms right per frame (3900ms = ~360dg)
def search(obj):
    log('[SEARCH] Searching for ' + obj)
    arduino_beep(2)
    bounding_box = False
    for i in range(0, 13):
        bounding_box = capture_predict(obj)
        if bounding_box:
            break
        arduino_move('turn_right', 300)
    if bounding_box:
        arduino_beep(2)
        centralize(bounding_box)
    	arduino_run()
    else:
        arduino_beep(1)
    log('[SEARCH] Finished searching for ' + obj)

def panoramic():
    for i in range(0, 13):
    	os.system('fswebcam -r 299x299 --jpeg 85 -S 10 -q img' + str(i+1) + '.jpg')
    	arduino_move('turn_right', 300)

def receive(rcv_socket):
    data = rcv_socket.recv(2048)
    cmd = list(str(data.decode('utf-8')).lower())
    cmd = ''.join([c for c in cmd if c != '\x00'])
    words = cmd.split(' ')
    asked_objs = [obj for obj in objects if obj in words]
    log('[COMMAND] Received cmd: ' + cmd)
    if 'nao' in words:
        pass
    elif len(asked_objs) == 1 and any(word in words for word in [ 'cade', 'pegue', 'encontre', 'ache', 'procure' ]):
        search(objects[asked_objs[0]])
    elif cmd in [ 'va para frente', 'siga em frente', 'va reto', 'va em frente', 'taca-le pau', 'taca-lhe pau', 'tacale pau' ]:
        arduino_move('forward', 3000)
    elif cmd in [ 'vire para direita', 'vire para a direita' ]:
        arduino_move('turn_right', 1900)
    elif cmd in [ 'vire para esquerda', 'vire para a esquerda' ]:
        arduino_move('turn_left', 1900)
    elif cmd in [ 'va para tras', 'volte', 'recue', 'volte atras' ]:
        arduino_move('backward', 2500)
    elif cmd in [ 'faca barulho', 'apite', 'alerte', 'grite', 'seja insuportavel' ]:
        arduino_beep(3)
    elif cmd in [ 'mostre todas as funcionalidades', 'se apresente', 'se exiba', 'mostre tudo o que sabe fazer', 'mostre quem e o bonzao', 'ulte', 'solte o ultimate', 'aperta o r', 'aperta o q', 'aperta esse errre', 'aperta esse r' ]:
        arduino_move('forward', 3000)
        arduino_move('turn_left', 1900)
        arduino_move('turn_right', 1900)
        arduino_move('backward', 2500)
        arduino_beep(3)
    elif cmd in [ 'corre berg', 'ande ate nao dar mais', 'va para frente ate ser bloqueado', 'va pra frente ate ser bloqueado', 'ao infinito e alem' ]:
        arduino_run()
    elif cmd in [ 'morre diabo', 'desativar', 'desligar' ]:
        arduino_beep(1)
        time.sleep(1)
        os.system('sudo shutdown -h 0')
    elif cmd in [ 'reinicie o sistema', 'reinicie' ]:
        arduino_beep(1)
        time.sleep(1)
        os.system('sudo reboot')
    rcv_socket.send('ack'.encode(encoding='utf-8', errors='ignore'))
    rcv_socket.close()

def wait_cmd(my_socket):
    while True:
    	rcv_socket, addr = my_socket.accept()
    	new_thread = threading.Thread(target=receive, args=(rcv_socket,))
    	new_thread.start()
    my_socket.close()

def init():
    my_socket = socket(AF_INET,SOCK_STREAM)
    my_socket.bind(('',socket_num))
    my_socket.listen(1)
    time.sleep(2)
    arduino_beep(2)
    wait_cmd(my_socket)

init()

def test_centralize():
    res = capture_predict('person')
    if res:
	centralize(res)
        res = capture_predict('person')
        if res:
            print (res[0] + res[2]) // 2
        else:
            print 'fail second'
    else:
        print 'fail'
