# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 15:23:40 2024

@author: Magathe
"""
import tkinter as tk 
from tkinter import ttk
from tkinter import *
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

from scipy.io import wavfile
import threading


#enregistrement = 'Enregistrement_1.wav'
enregistrement = 'Doppler_11.wav'
data = 0
zpad_value = 100
tp_value = 0.5
class MyWindow(tk.Tk): 
    
    def __init__(self):
        # On appelle le constructeur parent
        super().__init__()
        
        self.arret = 0
        
        self.grid_rowconfigure(0, weight=4)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # img = tk.PhotoImage(file="nyquit.gif")
        # self.iconphoto(False, img)
        
        try:
            img = tk.PhotoImage(file="nyquit.gif")
            self.iconphoto(False, img)
        except Exception as e:
            print(f"Error loading icon: {e}")
            
        """ Paramètres générals interface"""
        # largeur_ecran = self.winfo_screenwidth()
        # hauteur_ecran = self.winfo_screenheight()
        largeur_ecran = 1000
        hauteur_ecran = 700
        print(largeur_ecran)
        print(hauteur_ecran)
        self.geometry(f"{largeur_ecran}x{hauteur_ecran}")
        
        self.title("Interface Radar")
        self['bg'] = 'white'
        
        """Creation du bouton arrêt programme """
        self.bouton_start_stop = tk.Button(self, text="Stop", bg='slategray1', fg='black', cursor="dotbox", command=self.stop)
        self.bouton_start_stop.place(x=50, y=50)
    #, command=spectrogramme_doppler('Doppler_11.wav')
        self.texte = tk.Label(self, text=" radarrrrrr slayyyy ", bg="white")
        self.texte.place(x=50, y=100)
        
        self.bouton_spectrogram = tk.Button(self, text="Run Spectrogram", bg='lightblue', command=self.run_spectrogram_thread)
        self.bouton_spectrogram.place(x=50, y=150)
        
        self.bouton_audio = tk.Button(self, text="Run Audio", bg='lightpink', command=self.run_audio_thread)
        self.bouton_audio.place(x=50, y=200)
        
    
        # self.bouton_listbox = tk.Button(self, text="Fichiers", bg='lightpink', command=self.lister_fichiers_wav(self.listbox,))
        # self.bouton_listbox.place(x=50, y=200)
        # create listbox object
        
        self.listbox = Listbox(self, height = 10, width = 15)
        self.listbox.place(x=200, y=20)
        self.label_fichier = tk.Label(self, text="Fichier selectionne :  \n       Left = [:,0]  -  Right = [:,1]", bg="white")
        self.label_fichier.place(x=50, y=260)
        self.bouton_selection = tk.Button(self,text="Afficher selection",bg='lightyellow', command=lambda: afficher_selection_fichier(self.listbox,self.label_fichier))
        self.bouton_selection.place(x=200, y=200)
        
        self.var = IntVar()
        self.R1 = tk.Radiobutton(self, text="Left", bg="white", variable=self.var, value=0, command=self.select_data)
        self.R1.place(x=90, y=300)
        self.R2 = tk.Radiobutton(self, text="Right", bg="white", variable=self.var, value=1, command=self.select_data)
        self.R2.place(x=140, y=300)
        self.label = tk.Label(self, text="Data : ", bg="white")
        self.label.place(x=50, y=300)
        
        self.label_img1 = tk.Label(self)
        self.label_img1.grid(column=1, row=0)
        self.label_img2 = tk.Label(self)
        self.label_img2.grid(column=1, row=1)
        
        """Creation d'un entry qui permet de modifier zpad"""
        self.value_zpad = tk.IntVar()
        self.entry_zpad = tk.Entry(self, width=9, textvariable=self.value_zpad)
        self.entry_zpad.place(x=65, y=380)
        self.btn_enter_zpad = tk.Button(self,text="Enter",command = self.entry_zpad_changed)
        self.btn_enter_zpad.place(x=80, y=400)
        #self.entry_zpad.bind("<Return>", self.entry_Blue_changed)
        self.texte_zpad1 = tk.Label(self, text="zpad : ", bg="white")
        self.texte_zpad1.place(x=20, y=380)
        self.texte_zpad2 = tk.Label(self, text="*N (nb échantillon par impulsion)", bg="white")
        self.texte_zpad2.place(x=135, y=380)
        
        """Creation d'un entry qui permet de modifier Tp (temps d'impulsion"""
        self.value_Tp = tk.IntVar()
        self.entry_Tp = tk.Entry(self, width=9, textvariable=self.value_Tp)
        self.entry_Tp.place(x=65, y=480)
        self.btn_enter_Tp = tk.Button(self,text="Enter",command = self.entry_Tp_changed)
        self.btn_enter_Tp.place(x=80, y=500)
        #self.entry_zpad.bind("<Return>", self.entry_Blue_changed)
        self.texte_Tp1 = tk.Label(self, text="Tp : ", bg="white")
        self.texte_Tp1.place(x=20, y=480)
        self.texte_Tp2 = tk.Label(self, text="( Temps d'impulsion )", bg="white")
        self.texte_Tp2.place(x=135, y=480)
        
    def stop(self):
        self.arret=1
        self.destroy()
    
    def run_spectrogram_thread(self):
            # Run spectrogram analysis in a separate thread
            threading.Thread(target=spectrogramme_doppler, args=(enregistrement,self.label_img2,), daemon=True).start()
    def run_audio_thread(self):
            # Run spectrogram analysis in a separate thread
            threading.Thread(target=affichage_audio, args=(enregistrement,self.label_img1,), daemon=True).start()
        
    def select_data(self):
        global data
        data = self.var.get()
   
    def entry_zpad_changed(self):
        global zpad_value
        zpad_value = self.value_zpad.get()
        self.value_zpad.set("")
        
    def entry_Tp_changed(self):
        global tp_value
        tp_value = self.value_Tp.get()
        self.value_Tp.set("")
        
def lister_fichiers_wav(listbox, repertoire, extension):
    for fichier in os.listdir(repertoire):
        if fichier.endswith(extension):
            print(fichier)
            listbox.insert('end',fichier)

def afficher_selection_fichier(listbox,label_fichier):
    global enregistrement
    print("selection")
    selection = listbox.curselection()
    if selection:
        index=selection[0]
        enregistrement=listbox.get(index)
        print(f"Fichier selectionné : {enregistrement}")
        label_fichier.config(text=f"Fichier selectionne : {enregistrement}  \n       Left = [:,0]  -  Right = [:,1]" , bg="white")
    else:
        print("Aucune selection")
        label_fichier.config(text="Fichier selectionne :  aucune selection         \n       Left = [:,0]  -  Right = [:,1]        ")

def spectrogramme_doppler(audio,label_img2):
    
    global data
    global zpad_value
    global tp_value
    fs, Y = wavfile.read(audio)
    
    # Constantes
    c = 3e8  # Vitesse de la lumière (m/s)

    # Paramètres radar
    Tp = tp_value # Temps d'impulsion (s)
    N = int(Tp * fs)  # Nombre d'échantillons par impulsion
    fc = 2590e6  # Fréquence centrale (Hz)

    # Inversion du signal (en prenant le deuxième canal pour stéréo)
    s = -1 * Y[:, data]  # Assuming Y is stereo and we are interested in the second channel
    #s = -1 * Y[:, 1] pour l'audio du MIT
    print("inversion")
    # Création de l'ensemble de données Doppler vs temps
    num_pulses = round(len(s) / N) - 1
    sif = np.array([s[i * N:(i + 1) * N] for i in range(num_pulses)])

    # Soustraire le DC moyen
    sif = sif - np.mean(sif, axis=1, keepdims=True)

    # Zero-padding et FFT
    zpad = 8 * N // 2                   #Modifier zpad pour plus ou moins de détails
    zpad =zpad_value * N
    v = np.fft.ifft(sif, n=zpad, axis=1)
    v = np.abs(v[:, :v.shape[1] // 2])  # Magnitude et moitié des valeurs

    # Transformation en décibels (ajout epsilon pour éviter log(0))
    def dbv(in_signal):
        return 20 * np.log10(np.abs(in_signal) + 1e-12)

    v_db = dbv(v)
    print("v_db")

    # Ajustement de l'échelle des couleurs
    vmin, vmax = -35, 0  # Limite comme en MATLAB

    # Calcul de la vitesse et du temps
    delta_f = np.linspace(0, fs / 2, v.shape[1])  # Fréquence en Hz
    lambda_ = c / fc
    velocity = delta_f * lambda_ / 2
    time = np.linspace(0, Tp * num_pulses, num_pulses)  # Temps en secondes

    # Affichage du graphique avec l'échelle de couleur ajustée
    plt.figure(figsize=(10, 6))
    plt.imshow(v_db, aspect='auto', extent=[velocity[0], velocity[-1], time[-1], time[0]], vmin=vmin, vmax=vmax, cmap='plasma')
    plt.colorbar(label='Magnitude (dB)')
    plt.xlim([0, 40])  # Limiter l'axe de la vitesse
    plt.xlabel('Vitesse (m/sec)')
    plt.ylabel('Temps (sec)')
    plt.title('Doppler vs. Temps')
    # plt.show()
    print("spectrogramme")
    plt.savefig('spectre.png', bbox_inches='tight')
    plt.close()
    image = Image.open('spectre.png')
    img = ImageTk.PhotoImage(image=image)
    # Ajouter l'image dans un label Tkinter
    label_img2.config(image=img)
    label_img2.image = img
    
    # img_2 = Image.open('spectre.png')
    # img_2.show()

def affichage_audio(audio,label_img1):
    
    fs, Y = wavfile.read(audio)
    
    #number of samples
    nb_Y = Y.shape[0]
    #audio time duration
    a_fs = nb_Y / fs

    #plot signal versus time
    t = np.linspace(0,a_fs,nb_Y)

    plt.subplot(2,1,1)
    plt.plot(t,Y[:,0],'turquoise')
    plt.ylabel('Left')

    plt.subplot(2,1,2)
    plt.plot(t,Y[:,1],'mediumorchid')
    plt.ylabel('Right')
    plt.xlabel('Time (s)')

    print("audio")
    plt.savefig('audio.png', bbox_inches='tight')
    plt.close()
    image = Image.open('audio.png')
    img = ImageTk.PhotoImage(image=image)
    # Ajouter l'image dans un label Tkinter
    label_img1.config(image=img)
    label_img1.image = img
    
    # img_1 = Image.open('audio.png')
    # img_1.show()

def main():
    print("start")
    fenetre = MyWindow()
    lister_fichiers_wav(fenetre.listbox, 'D:\_TRAVAIL\Magathe\Documents\GEII3\SAEradar\prog_python', '.wav') 
    print("après liste fichier")
    fenetre.mainloop()
            
            
if __name__ == '__main__':
    main()