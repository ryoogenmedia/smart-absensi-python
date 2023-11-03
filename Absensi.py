import tkinter as tk
from tkinter import messagebox
import cv2
import os
from PIL import Image
import numpy as np
import mysql.connector
import requests
import datetime
import time

def rekamDataWajah():
    if entry1.get() == "" or entry2.get() == "" or entry3.get() == "":
        messagebox.showinfo('Result', 'Harap Isi Data Dengan Lengkap')
    else:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="smart_absen"
        )
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * from register_absensi")
        myresult = mycursor.fetchall()
        id = 1
        for x in myresult:
            id += 1
        sql = "insert into register_absensi(id,nama,nis,kelas) values(%s,%s,%s,%s)"
        val = (id, entry1.get(), entry2.get(), entry3.get())
        mycursor.execute(sql, val)
        mydb.commit()

        face_classifier = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        def face_cropped(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                return None
            for (x, y, w, h) in faces:
                cropped_face = img[y:y+h, x:x+w]
            return cropped_face

        cap = cv2.VideoCapture(0)
        img_id = 0

        while True:
            ret, frame = cap.read()
            if face_cropped(frame) is not None:
                img_id += 1
                face = cv2.resize(face_cropped(frame), (200, 200))
                face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                file_name_path = "image/face." + str(id) + "." + str(img_id) + ".jpg"
                cv2.imwrite(file_name_path, face)
                cv2.putText(face, str(img_id), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow("Cropped face", face)
                if cv2.waitKey(1) == 13 or int(img_id) == 30:
                    break
        cap.release()
        cv2.destroyAllWindows()
        messagebox.showinfo('Result', 'Data Siswa Berhasil Terdaftar!!!')

def trainingWajah():
    data_dir = "C:/xampp/htdocs/Smart-Absensi/image"
    path = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
    faces = []
    ids = []

    for image in path:
        img = Image.open(image).convert('L')
        imageNp = np.array(img, 'uint8')
        id = int(os.path.split(image)[1].split(".")[1])

        faces.append(imageNp)
        ids.append(id)
    ids = np.array(ids)

    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    clf.write("classifier.xml")
    messagebox.showinfo('Result', 'Set Data Pelatihan Selesai!!!')

def absensiWajah():
    def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, clf):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        features = classifier.detectMultiScale(gray, scaleFactor, minNeighbors)
        token = '6472014059:AAEJ4WHbm_10vR7Xoo13XAuQmGyBd9OGdPc'
        chat_id = -1002014219797 # ID group Telegram
        coords = []
        for (x, y, w, h) in features:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Ganti warna kotak menjadi hijau
            id, pred = clf.predict(gray[y:y+h, x:x+w])
            confidence = int(100 * (1 - pred / 300))

            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="smart_absen"
            )
            
            mycursor = mydb.cursor()
            mycursor.execute("select nama,nis,kelas from register_absensi where id=" + str(id))
            data = mycursor.fetchone()
            nama, nis, kelas = data  # Memisahkan data menjadi variabel terpisah
            nama = '' + ''.join(nama) # Mengambil data variabel berupa nama untuk di tampilkan ketika wajah terkenali
            time_stamp = datetime.datetime.now().strftime('%H:%M')
            # Warna hijau jika akurasi lebih dari 74
            if confidence > 74:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Ganti warna kotak menjadi hijau jika wajah terkenali
                cv2.putText(img, f"{nama} ({confidence}%)", (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)  # Teks hijau jika wajah terkenali
                cv2.putText(img, "Absen Berhasil", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)  # Teks tambahan untuk pengenalan yang berhasil
                # Simpan gambar wajah yang terdeteksi
                if cv2.waitKey(1) == ord(' '):
                    lebar_target = 300
                    wajah_terdeteksi = img[y:y+h, x:x+w]
                    perubahan = lebar_target / wajah_terdeteksi.shape[1]
                    wajah_terdeteksi = cv2.resize(wajah_terdeteksi, (lebar_target, int(h * perubahan)))
                    # Simpan gambar wajah sebagai file sementara
                    temp_image_path = 'wajah_terdeteksi.jpg'
                    cv2.imwrite(temp_image_path, wajah_terdeteksi)
                    # Kirim gambar wajah ke Telegram
                    with open(temp_image_path, 'rb') as wajah_file:
                        files = {'photo': wajah_file}
                        caption = f'Nama : {nama} \nNIS : {nis} \nKelas : {kelas} \nPukul : {time_stamp}'
                        data = {'chat_id': chat_id, 'caption': caption}
                        response = requests.post(f'https://api.telegram.org/bot{token}/sendPhoto', data=data, files=files)
                    # Hapus file sementara setelah data berhasil di kirim ke telegram
                    os.remove(temp_image_path)
            else:
                 cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Ganti warna kotak menjadi merah jika wajah tidak terkenali
                 cv2.putText(img, f"Wajah tidak di kenali!! ({confidence}%)", (x, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)  # Teks merah jika wajah tidak terkenali
                 coords=[x,y,w,h]
        return coords
    def recognize(img, clf, faceCascade):
                # Membalik gambar horizontal (horizontally flip)
            img = cv2.flip(img, 1)
            coords = draw_boundary(img, faceCascade, 1.1, 10, (255, 255, 255), "Face", clf)
            return img

    faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier.xml")

    video_capture = cv2.VideoCapture(0)

    while True:
        ret, img = video_capture.read()
        img = recognize(img, clf, faceCascade)
        cv2.imshow("face detection", img)
        
        # Hitung jumlah wajah yang terdeteksi
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30))
        total_faces = len(faces)
        cv2.putText(img, f"Jumlah Wajah: {total_faces}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
       
        if cv2.waitKey(1) == 13:
            break

    video_capture.release()
    cv2.destroyAllWindows()


# GUI/Tampilan

root = tk.Tk()
root.title("Smart Absensi")

canvas = tk.Canvas(root, width=700, height=400)
canvas.grid(columnspan=3, rowspan=8)
canvas.configure(bg="black")

judul = tk.Label(root, text="Smart Absensi", font=("Roboto", 34), bg="#242526", fg="white")
canvas.create_window(350, 80, window=judul)

made = tk.Label(root, text="By SDIT-ALHIKMA MAROS", font=("Times New Roman", 13), bg="black", fg="white")
canvas.create_window(360, 20, window=made)

entry1 = tk.Entry(root, font="Roboto")
canvas.create_window(457, 170, height=25, width=411, window=entry1)
label1 = tk.Label(root, text="Nama", font="Roboto", fg="white", bg="black")
canvas.create_window(90, 170, window=label1)

entry2 = tk.Entry(root, font="Roboto")
canvas.create_window(457, 210, height=25, width=411, window=entry2)
label2 = tk.Label(root, text="NIS   ", font="Roboto", fg="white", bg="black")
canvas.create_window(90, 210, window=label2)

entry3 = tk.Entry(root, font="Roboto")
canvas.create_window(457, 250, height=25, width=411, window=entry3)
label3 = tk.Label(root, text="Kelas", font="Roboto", fg="white", bg="black")
canvas.create_window(90, 250, window=label3)

instructions = tk.Label(root, text="", font=("Roboto", 15), fg="white", bg="black")
canvas.create_window(370, 300, window=instructions)


Rekam_text = tk.StringVar()
Rekam_btn = tk.Button(root, textvariable=Rekam_text, font="Roboto", bg="#00ABFF", fg="white", height=1, width=15, command=rekamDataWajah)
Rekam_text.set("Daftar Wajah")
Rekam_btn.grid(column=0, row=7)

Rekam_text1 = tk.StringVar()
Rekam_btn1 = tk.Button(root, textvariable=Rekam_text1, font="Roboto", bg="#00ABFF", fg="white", height=1, width=15, command=trainingWajah)
Rekam_text1.set("Training Wajah")
Rekam_btn1.grid(column=1, row=7)

Rekam_text2 = tk.StringVar()
Rekam_btn2 = tk.Button(root, textvariable=Rekam_text2, font="Roboto", bg="#00ABFF", fg="white", height=1, width=20, command=absensiWajah)
Rekam_text2.set("Absen Wajah")
Rekam_btn2.grid(column=2, row=7)

root.mainloop()
