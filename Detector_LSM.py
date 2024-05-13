import cv2 as cv
import time
import speech_recognition as sr
import pyttsx3
import numpy as np
import tkinter as tk
import sqlite3

# Función para crear la tabla de usuarios si no existe
def create_users_table():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password TEXT
                    )''')
    conn.commit()
    conn.close()

# Función para agregar un nuevo usuario a la base de datos
def add_user(username, password):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO usuarios (username, password) VALUES (?, ?)''', (username, password))
    conn.commit()
    conn.close()

# Función para verificar las credenciales del usuario
def verify_user(username, password):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM usuarios WHERE username = ? AND password = ?''', (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return True
    else:
        return False

def login():
    username = entry_username.get()
    password = entry_password.get()
    if verify_user(username, password):
        root.destroy()  # Cerrar la ventana de inicio de sesión
        run_main_program()  # Ejecutar el programa principal
    else:
        label_message.config(text="Credenciales incorrectas")

def create_new_user():
    new_username = entry_new_username.get()
    new_password = entry_new_password.get()
    if new_username and new_password:
        add_user(new_username, new_password)
        label_new_message.config(text="Usuario creado correctamente")
    else:
        label_new_message.config(text="Por favor ingresa un nombre de usuario y contraseña")

def run_main_program():
    # Inicializar el reconocedor de voz
    recognizer = sr.Recognizer()
    # Inicializar el motor de síntesis de voz
    engine = pyttsx3.init()

    Conf_threshold = 0.70
    NMS_threshold = 0.4
    COLORS = [(0, 255, 0), (0, 0, 255), (255, 0, 0),
            (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    class_name = []
    with open('C:/Users/USER/Documents/4-N/Base de datos/DLS LSM Python-20231113T064249Z-001/clases.txt', 'r') as f:
        class_name = [cname.strip() for cname in f.readlines()]

    net = cv.dnn.readNet('C:/Users/USER/Documents/4-N/Base de datos/DLS LSM Python-20231113T064249Z-001/LSM.weights', 'C:/Users/USER/Documents/4-N/Base de datos/DLS LSM Python-20231113T064249Z-001/LSM.cfg')
    net.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
    net.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA_FP16)

    # Inicializar variable para almacenar el texto detectado
    texto_detectado = ""

    model = cv.dnn_DetectionModel(net)
    model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

    cap = cv.VideoCapture(0)
    starting_time = time.time()
    frame_counter = 0

    # Inicializar el interruptor de audio y volumen
    audio_activado = True
    volumen = 1.0

    def toggle_audio(event, x, y, flags, param):
        global audio_activado
        if event == cv.EVENT_LBUTTONDOWN:
            # Verificar si el clic está dentro del área del botón de activar/desactivar audio
            button_pos = (frame.shape[1] - button_size[0] - 20, frame.shape[0] - button_size[1] - 20)
            if x >= button_pos[0] and x <= button_pos[0] + button_size[0] and y >= button_pos[1] and y <= button_pos[1] + button_size[1]:
                audio_activado = not audio_activado

    cv.namedWindow('frame')
    cv.setMouseCallback('frame', toggle_audio)

    while True:
        ret, frame = cap.read()
        frame_counter += 1
        if ret:
            classes, scores, boxes = model.detect(frame, Conf_threshold, NMS_threshold)
            for (classid, score, box) in zip(classes, scores, boxes):
                color = COLORS[int(classid) % len(COLORS)]
                label = "%s : %f" % (class_name[classid], score)
                cv.rectangle(frame, box, color, 1)
                cv.putText(frame, label, (box[0], box[1]-10),
                        cv.FONT_HERSHEY_COMPLEX, 4.3, color, 1)
                # Convertir la letra detectada en texto
                detected_letter = class_name[classid]
                # Agregar la letra detectada al texto detectado
                texto_detectado += detected_letter
                # Reproducir la letra detectada solo si el audio está activado
                if audio_activado:
                    engine.say(detected_letter)
                    engine.setProperty('rate', 110)  # Disminuir la velocidad
                    engine.setProperty('volume', volumen)  # Ajustar el volumen
                    voices = engine.getProperty('voices')
                    # Establecer la voz por su ID
                    engine.setProperty('voice', 'desired_voice_id')
                    engine.runAndWait()
                # Si se detecta una palabra completa (por ejemplo, si se detecta un espacio), reiniciar el texto detectado para la próxima palabra
                if detected_letter == " ":
                    texto_detectado = ""

            endingTime = time.time() - starting_time
            fps = frame_counter/endingTime
            cv.putText(frame, f'FPS: {fps}', (20, 50),
                    cv.FONT_HERSHEY_COMPLEX, 0.7 , (0, 255, 0), 2)
            
            # Dibujar el botón para desactivar el audio en la parte inferior derecha del video
            button_text = "Desactivar Audio" if audio_activado else "Activar Audio"
            button_color = (0, 0, 255) if audio_activado else (0, 255, 0)
            button_size = cv.getTextSize(button_text, cv.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv.rectangle(frame, (frame.shape[1] - button_size[0] - 20, frame.shape[0] - button_size[1] - 20),
                        (frame.shape[1] - 10, frame.shape[0] - 10), button_color, cv.FILLED)
            cv.putText(frame, button_text, (frame.shape[1] - button_size[0] - 15, frame.shape[0] - 15),
                    cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv.imshow('frame', frame)
            if cv.waitKey(1) & 0xFF == ord('x'):
                break

    cap.release()
    cv.destroyAllWindows()
    pass

# Crear la ventana de inicio de sesión
root = tk.Tk()
root.title("Inicio de Sesión")
root.geometry("300x150")  # Establecer el tamaño de la ventana

# Etiquetas y campos de entrada para usuario y contraseña
label_username = tk.Label(root, text="Usuario:")
label_username.pack()
entry_username = tk.Entry(root)
entry_username.pack()

label_password = tk.Label(root, text="Contraseña:")
label_password.pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

# Botón de inicio de sesión
button_login = tk.Button(root, text="Iniciar Sesión", command=login)
button_login.pack()

# Etiqueta para mostrar mensajes de error
label_message = tk.Label(root, text="")
label_message.pack()

# Ventana para agregar nuevo usuario
new_user_window = tk.Toplevel(root)
new_user_window.title("Crear Nuevo Usuario")
new_user_window.geometry("300x150")  # Establecer el tamaño de la ventana

label_new_username = tk.Label(new_user_window, text="Nuevo Usuario:")
label_new_username.pack()
entry_new_username = tk.Entry(new_user_window)
entry_new_username.pack()

label_new_password = tk.Label(new_user_window, text="Contraseña:")
label_new_password.pack()
entry_new_password = tk.Entry(new_user_window, show="*")
entry_new_password.pack()

button_create_user = tk.Button(new_user_window, text="Crear Usuario", command=create_new_user)
button_create_user.pack()

label_new_message = tk.Label(new_user_window, text="")
label_new_message.pack()

root.mainloop()