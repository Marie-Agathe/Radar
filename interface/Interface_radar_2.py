# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 17:53:22 2024

@author: Magathe
"""

import tkinter as tk 
from tkinter import ttk
from tkinter import *
from tkinter import filedialog
import shutil
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from scipy.io import wavfile
import threading
import queue
from tkinter import messagebox
import sounddevice as sd
import soundfile as sf
import pyvisa
import time


enregistrement = 'Doppler_11.wav'
spectre = "spectre_doppler.png"
data = 0
mode = 0
zpad_doppler = 100
tp_doppler = 0.5
zpad_synchro = 2
tp_synchro = 0.02
cmap='plasma'
class MyWindow(tk.Tk): 
    
    def __init__(self):
        super().__init__()
        self.arret = threading.Event()
        # File d'attente pour les mises à jour de l'interface
        self.queue_manager = queue.Queue()
        self.after_id = None
        self.running = True
        # Vérifier périodiquement la file d'attente
        self.process_queue()
        # Gestion de la fermeture propre
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # États pour contrôler les threads
        self.spectrogram_thread_running = False
        self.audio_thread_running = False

        """ Paramètres générals interface"""
        largeur_ecran = self.winfo_screenwidth()
        hauteur_ecran = self.winfo_screenheight()
        left_column_width = largeur_ecran //2
        #largeur_ecran = 1000
        #hauteur_ecran = 700
        print(largeur_ecran)
        print(hauteur_ecran)
        self.geometry(f"{largeur_ecran}x{hauteur_ecran}")
        self.state('zoomed')
        self.configure(bg='lightblue')
        self.title("Interface Radar")
        self['bg'] = 'white'
        
        try:
            img = tk.PhotoImage(file="nyquit.gif")
            self.iconphoto(False, img)
        except Exception as e:
            print(f"Error loading icon: {e}")

        left_column_width = largeur_ecran // 4  # Largeur de la colonne de gauche
        middle_column_width = largeur_ecran // 4  # Largeur de la colonne du milieu
        combined_width = left_column_width + middle_column_width  # Largeur combinée des colonnes 1 et 2

        left_canvas_height = hauteur_ecran // 4  # Hauteur d'une ligne de canevas dans les colonnes de gauche et milieu
        right_canvas1_height = hauteur_ecran // 3  # Hauteur du premier canevas de la colonne de droite
        right_canvas2_height = 2 * hauteur_ecran // 3  # Hauteur du deuxième canevas de la colonne de droite

        # Canevas pour les deux premières lignes dans la colonne de gauche
        self.canvas_left_1 = tk.Canvas(self, borderwidth =5, relief="ridge",bg="white", width=left_column_width+50, height=left_canvas_height)
        self.canvas_left_1.place(x=0, y=0)

        self.canvas_left_2 = tk.Canvas(self, borderwidth =5, relief="ridge", bg="white", width=left_column_width+50, height=left_canvas_height)
        self.canvas_left_2.place(x=0, y=left_canvas_height)

        # Canevas pour les deux premières lignes dans la colonne du milieu
        self.canvas_middle_1 = tk.Canvas(self, borderwidth =5, relief="ridge", bg="white", width=middle_column_width-50, height=2*left_canvas_height)
        self.canvas_middle_1.place(x=left_column_width+50, y=0)

        # Canevas pour les deux dernières lignes (colonnes 1 et 2 combinées)
        self.canvas_combined_1 = tk.Canvas(self, bd=5, relief="ridge", bg="white", width=combined_width, height=left_canvas_height)
        self.canvas_combined_1.place(x=0, y=2 * left_canvas_height)

        self.canvas_combined_2 = tk.Canvas(self, bd=5, relief="ridge", bg="white", width=combined_width, height=left_canvas_height)
        self.canvas_combined_2.place(x=0, y=3 * left_canvas_height)

        # Canevas pour la colonne de droite
        self.audio_canvas = tk.Canvas(self, bd=5, relief="ridge", bg="white", width=combined_width, height=right_canvas1_height)
        self.audio_canvas.place(x=combined_width, y=0)

        self.spectrogram_canvas = tk.Canvas(self, bd=5, relief="ridge", bg="white", width=combined_width, height=right_canvas2_height)
        self.spectrogram_canvas.place(x=combined_width, y=right_canvas1_height)


        
        """--------------------Enregistrement d'un fichier audio----------------------------"""
        
        # Créer un label et une entrée pour le nom du fichier
        self.label_filename = tk.Label(self, bg="white", text="Entrez le nom du fichier :")
        self.label_filename.place(x=20, y=30)
        self.entry_filename = tk.Entry(self, width=27)
        self.entry_filename.place(x=20, y=78)
        
        # Créer un label pour choisir le nombre de canaux
        self.label_channels = tk.Label(self, bg="white", text="Choisir le nombre de canaux :")
        self.label_channels.place(x=20, y=115)
        # Variable pour stocker le nombre de canaux (1 ou 2)
        self.var_channels = tk.IntVar()
        self.var_channels.set(1)  # Valeur par défaut (mono)
        # Créer les boutons pour les canaux
        self.radio_button_1 = tk.Radiobutton(self, bg="white", text="1 Canal (Mono)", variable=self.var_channels, value=1)
        self.radio_button_1.place(x=20, y=145)
        self.radio_button_2 = tk.Radiobutton(self, bg="white", text="2 Canaux (Stéréo)", variable=self.var_channels, value=2)
        self.radio_button_2.place(x=20, y=175)
        
        # Créer un label et un champ pour saisir la durée
        self.label_duration = tk.Label(self, bg="white", text="Durée de l'enregistrement (en secondes) :")
        self.label_duration.place(x=200, y=30)
        self.entry_duration = tk.Entry(self, bg="white", width=10)
        self.entry_duration.place(x=280, y=78)
        self.entry_duration.insert(0, "5")  # Valeur par défaut (5 secondes)
        # Ajouter une barre de progression
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self, maximum=100, variable=self.progress_var, length=220, mode="determinate")
        self.progress_bar.place(x=200, y=130)
        # Créer un bouton pour lancer l'enregistrement
        self.button_enregistrer = tk.Button(self, bg="thistle", text="Lancer l'enregistrement", command=lambda: enregistrer(self.entry_filename,self.var_channels,self.entry_duration, self.progress_var , self))
        self.button_enregistrer.place(x=250, y=170)
        

        """------------------------------------Bloc GBF------------------------------------"""

        self.label_gbf = tk.Label(self, bg="white", text="Waveform Generator - Mode :")
        self.label_gbf.place(x=445, y=30)
        self.var_gbf = tk.IntVar()
        self.var_gbf.set(0)  # mode gbf par défaut (doppler)
        self.radio_button_gbf1 = tk.Radiobutton(self, bg="white", text="Doppler", variable=self.var_gbf, value=0, command=self.update_mode)
        self.radio_button_gbf1.place(x=610, y=28)
        self.radio_button_gbf2 = tk.Radiobutton(self, bg="white", text="Synchro", variable=self.var_gbf, value=1, command=self.update_mode)
        self.radio_button_gbf2.place(x=685, y=28)

        # Gestion des voies avec un dictionnaire
        self.channels = {}
        self._widgets_gbf("1",420,25,color_voie="gold",def_fonc="RAMP",def_freq=200,def_volt=4.5,def_offset=2.75,def_load="INF",def_phase=0,def_etat="0")
        self._widgets_gbf("2",420,190,color_voie="lightgreen",def_fonc="SIN",def_freq=0,def_volt=0,def_offset=0,def_load="INF",def_phase=0,def_etat="0")
        
        # Boutons "Enter" pour chaque voie
        self.btn_enter_gbf_voie1 = tk.Button(self, text="Enregistrer", command=lambda: self.save_current_params_for_channel("1"))
        self.btn_enter_gbf_voie1.place(x=620, y=190)
        
        self.btn_enter_gbf_voie2 = tk.Button(self, text="Enregistrer", command=lambda: self.save_current_params_for_channel("2"))
        self.btn_enter_gbf_voie2.place(x=620, y=350)
        # Boutons "Paramètres Défaults" pour Voie 1 et Voie 2
        self.btn_defaut_voie1 = tk.Button(self, text="Default Param", command=lambda: self.reset_to_default("1"))
        self.btn_defaut_voie1.place(x=505, y=72)
        self.btn_defaut_voie2 = tk.Button(self, text="Default Param", command=lambda: self.reset_to_default("2"))
        self.btn_defaut_voie2.place(x=505, y=237)

        self.btn_transmission_param = tk.Button(self, text="Transmission données", bg="lavender", command=self.transmission_param)
        self.btn_transmission_param.place(x=615, y=390)
        # Paramètres par défaut
        self.default_params = {
            0: {  # Mode Doppler
                "1": {"func": "RAMP", "freq": 200, "volt": 4.5, "offset": 2.75, "load": "INF", "phase": 0, "etat": 0},
                "2": {"func": "SIN", "freq": 0, "volt": 0, "offset": 0, "load": "INF", "phase": 0, "etat": 0},
            },
            1: {  # Mode Synchro
                "1": {"func": "RAMP", "freq": 200, "volt": 4.5, "offset": 2.75, "load": "INF", "phase": 0, "etat": 0},
                "2": {"func": "PULS", "freq": 200, "volt": 4.5, "offset": 0, "load": "INF", "phase": 175, "etat": 0},
            },
        }
        # Paramètres actuels
        self.current_params = {0: {"1": self.default_params[0]["1"].copy(), "2": self.default_params[0]["2"].copy()},
            1: {"1": self.default_params[1]["1"].copy(), "2": self.default_params[1]["2"].copy()},}

        # Mise à jour des paramètres en fonction du mode
        self.update_mode()

        """---------------------------------Bloc audio-------------------------------------"""
        
        #-----------Creation de la listbox des fichiers audio-----------
        self.listbox_wav = Listbox(self, height = 9, width = 28)
        self.listbox_wav.place(x=20, y=235)
        self.label_fichier = tk.Label(self, text=f"Fichier par défaut :  {enregistrement}", bg="white")
        self.label_fichier.place(x=200, y=270)
        self.bouton_selection = tk.Button(self,text="Enregistrer selection",bg='lightyellow', command=self.afficher_selection_fichier)
        self.bouton_selection.place(x=200, y=235)
        self.bouton_actualiser = tk.Button(self, text="Actualiser", bg='lightcyan', command=lambda: self.lister_fichiers_wav(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav"), '.wav'))
        self.bouton_actualiser.place(x=20, y=395)
        self.bouton_recherche_audio = tk.Button(self, text="Rechercher audio", command=self.rechercher_audio)
        self.bouton_recherche_audio.place(x=86, y=395)

        #-----------Creation du bouton Run audio----------------
        self.bouton_audio = tk.Button(self, text="Run Audio", bg='lightpink', command=self.run_audio_thread)
        self.bouton_audio.place(x=350, y=350)

        """--------------------------Widgets de la colonne droite--------------------------"""
        self.label_img1 = tk.Label(self, text= "Fichier audio : ")
        self.label_img1.place(x=800,y=260)
        self.label_img2 = tk.Label(self, text= "Fichier audio : ")
        self.label_img2.place(x=800,y=320)
        self.entry_specname = tk.Entry(self, width=30)
        self.entry_specname.place(x=1210, y=320)
        self.bouton_save_img = tk.Button(self, text="Enregistrer sous :", command=self.save_img_spec)
        self.bouton_save_img.place(x=1100,y=320)

        """---------------------------------Bloc spectrogramme-------------------------------------"""

        #-----------Création des radiobutton pour le mode du spectrogramme----------------
        self.var_mode = IntVar()
        self.label_mode = tk.Label(self, text="Mode :                              ",font=("Arial", 13))
        self.label_mode.place(x=20, y=460)
        self.R_doppler = tk.Radiobutton(self, text="Doppler",  variable=self.var_mode, value=0, command=self.select_mode)
        self.R_doppler.place(x=80, y=460)
        self.R_synchro = tk.Radiobutton(self, text="Synchro",  variable=self.var_mode, value=1, command=self.select_mode)
        self.R_synchro.place(x=160, y=460)

        #-----------Creation des radiobutton pour le canal des données----------------
        self.var_data = IntVar()
        self.R1 = tk.Radiobutton(self, text="Left", bg="white", variable=self.var_data, value=0, command=self.select_data)
        self.R1.place(x=60, y=500)
        self.R2 = tk.Radiobutton(self, text="Right", bg="white", variable=self.var_data, value=1, command=self.select_data)
        self.R2.place(x=110, y=500)
        self.label = tk.Label(self, text="Data : ", bg="white")
        self.label.place(x=20, y=500)

        #-----------Creation d'un entry qui permet de modifier zpad----------------
        self.value_zpad = tk.IntVar()
        self.value_zpad.set(100)  # Valeur par défaut de zpad
        self.texte_zpad1 = tk.Label(self, text="zpad :                                               \n *N (nb échantillon par impulsion)", bg="white")
        self.texte_zpad1.place(x=65, y=545)
        self.entry_zpad = tk.Spinbox(self, from_=1, to=200, width=9, textvariable=self.value_zpad)
        self.entry_zpad.place(x=110, y=545)
        self.btn_enter_zpad = tk.Button(self,text="Enter",height=1,command = self.entry_zpad_changed)
        self.btn_enter_zpad.place(x=20, y=550)
        
        #-----------Creation d'un entry qui permet de modifier Tp (temps d'impulsion)----------------
        self.value_Tp = tk.DoubleVar()
        self.value_Tp.set(0.500)  # Valeur par défaut de Tp
        self.texte_Tp1 = tk.Label(self, text="Tp :                          \n Temps d'impulsion", bg="white")
        self.texte_Tp1.place(x=65, y=595)
        self.entry_Tp = tk.Spinbox(self, from_=0.005, to=2, increment=0.005, width=9, textvariable=self.value_Tp)
        self.entry_Tp.place(x=100, y=595)
        self.btn_enter_Tp = tk.Button(self,text="Enter",command = self.entry_Tp_changed)
        self.btn_enter_Tp.place(x=20, y=600)

        #-----------Creation de la listbox colours spectrogrammes----------------
        self.listbox_color = Listbox(self, height =7, width = 19)
        self.listbox_color.insert('end',*['plasma','viridis','inferno','magma','cividis','hsv','Spectral',])
        self.listbox_color.place(x=285, y=450)
        self.label_color = tk.Label(self, text=f"Couleur par défaut :  {cmap}", bg="white")
        self.label_color.place(x=260, y=610)
        self.bouton_selection_color = tk.Button(self,text="Enregistrer selection",bg='lightyellow', command=self.afficher_selection_color)
        self.bouton_selection_color.place(x=285, y=575)

        #-----------Creation du bouton Run spectrogramme----------------
        self.bouton_spectrogram = tk.Button(self, text="Run Spectrogram", bg='lightblue', command=self.run_spectrogram_thread)
        self.bouton_spectrogram.place(x=440, y=450)

        #-----------Creation de la listbox images spectrogrammes----------------
        self.listbox_spectre = Listbox(self, height =7, width = 28)
        self.listbox_spectre.place(x=580, y=450)
        self.bouton_selection_color = tk.Button(self,text="Afficher selection",bg='lightyellow', command=lambda: self.afficher_selection_spectre(self.update_spectrogram_image))
        self.bouton_selection_color.place(x=580, y=610)
        self.bouton_actualiser_spec = tk.Button(self, text="Actualiser", bg='lightcyan', command=lambda: self.lister_spectre_img(os.path.join(os.path.dirname(os.path.abspath(__file__)), "img_spectre"), [".png", ".jpg", ".jpeg", ".bmp", ".gif"]))
        self.bouton_actualiser_spec.place(x=580, y=575)
        self.bouton_recherche_img = tk.Button(self, text="Rechercher fichier", command=self.rechercher_image)
        self.bouton_recherche_img.place(x=646, y=575)

    """------------------Bloc GBF--------------------"""

    def _widgets_gbf(self, channel_name,x_offset,y_offset,color_voie,def_fonc,def_freq,def_volt,def_offset,def_load,def_phase,def_etat):

        self.channels[channel_name] = {}  # Dictionnaire pour stocker les widgets de cette voie
        # Titre de la voie
        self.channels[channel_name]["label_source"] = tk.Label(self, bg=color_voie, text=f"Voie {channel_name} :")
        self.channels[channel_name]["label_source"].place(x=x_offset + 30, y=y_offset + 50)
        # Fonction
        self.channels[channel_name]["label_func"] = tk.Label(self, bg="white", text="Function :")
        self.channels[channel_name]["label_func"].place(x=x_offset + 30, y=y_offset + 80)
        self.channels[channel_name]["combobox_func"] = ttk.Combobox(self, width=10,values=["SIN", "SQU", "RAMP", "PULS", "NOIS", "DC", "PRBS", "ARB"])
        self.channels[channel_name]["combobox_func"].place(x=x_offset + 90, y=y_offset + 80)
        self.channels[channel_name]["combobox_func"].set(def_fonc)
        # Fréquence
        self.channels[channel_name]["label_freq"] = tk.Label(self, bg="white", text="Frequence :                          Hz")
        self.channels[channel_name]["label_freq"].place(x=x_offset + 30, y=y_offset + 110)
        self.channels[channel_name]["value_freq"] = tk.DoubleVar()
        self.channels[channel_name]["value_freq"].set(def_freq)
        self.channels[channel_name]["spinbox_freq"] = tk.Spinbox(self, from_=0, to=1000, increment=10, width=9,textvariable=self.channels[channel_name]["value_freq"])
        self.channels[channel_name]["spinbox_freq"].place(x=x_offset + 100, y=y_offset + 110)
        # Tension
        self.channels[channel_name]["label_volt"] = tk.Label(self, bg="white", text="Tension :                               V")
        self.channels[channel_name]["label_volt"].place(x=x_offset + 30, y=y_offset + 140)
        self.channels[channel_name]["value_volt"] = tk.DoubleVar()
        self.channels[channel_name]["value_volt"].set(def_volt)
        self.channels[channel_name]["spinbox_volt"] = tk.Spinbox(self, from_=0.00, to=10, increment=0.05, width=9,textvariable=self.channels[channel_name]["value_volt"])
        self.channels[channel_name]["spinbox_volt"].place(x=x_offset + 100, y=y_offset + 140)
        # Offset
        self.channels[channel_name]["label_offset"] = tk.Label(self, bg="white", text="Offset :                              V")
        self.channels[channel_name]["label_offset"].place(x=x_offset + 30, y=y_offset + 170)
        self.channels[channel_name]["value_offset"] = tk.DoubleVar()
        self.channels[channel_name]["value_offset"].set(def_offset)
        self.channels[channel_name]["spinbox_offset"] = tk.Spinbox(self, from_=0.00, to=10, increment=0.05, width=7,textvariable=self.channels[channel_name]["value_offset"])
        self.channels[channel_name]["spinbox_offset"].place(x=x_offset + 100, y=y_offset + 170)
        # Charge
        self.channels[channel_name]["label_load"] = tk.Label(self, bg="white", text="Load :                               Ω")
        self.channels[channel_name]["label_load"].place(x=x_offset + 200, y=y_offset + 80)
        self.channels[channel_name]["combobox_load"] = ttk.Combobox(self, width=10, values=["INF", "50"])
        self.channels[channel_name]["combobox_load"].place(x=x_offset + 240, y=y_offset + 80)
        self.channels[channel_name]["combobox_load"].set(def_load)
        # Phase
        self.channels[channel_name]["label_phase"] = tk.Label(self, bg="white", text="Phase :                        °")
        self.channels[channel_name]["label_phase"].place(x=x_offset + 200, y=y_offset + 110)
        self.channels[channel_name]["value_phase"] = tk.DoubleVar()
        self.channels[channel_name]["value_phase"].set(def_phase)
        self.channels[channel_name]["spinbox_phase"] = tk.Spinbox(self, from_=0, to=180, increment=5, width=7,textvariable=self.channels[channel_name]["value_phase"])
        self.channels[channel_name]["spinbox_phase"].place(x=x_offset + 250, y=y_offset + 110)
        # État
        self.channels[channel_name]["label_etat"] = tk.Label(self, bg="white", text="Etat :")
        self.channels[channel_name]["label_etat"].place(x=x_offset + 200, y=y_offset + 140)
        self.channels[channel_name]["var_etat"] = tk.IntVar()
        self.channels[channel_name]["var_etat"].set(def_etat)
        self.channels[channel_name]["radio_button_on"] = tk.Radiobutton(self, bg="white", text="ON", variable=self.channels[channel_name]["var_etat"], value=1)
        self.channels[channel_name]["radio_button_on"].place(x=x_offset + 240, y=y_offset + 138)
        self.channels[channel_name]["radio_button_off"] = tk.Radiobutton(self, bg="white", text="OFF",variable=self.channels[channel_name]["var_etat"], value=0)
        self.channels[channel_name]["radio_button_off"].place(x=x_offset + 280, y=y_offset + 138)
   
    def save_current_params_for_channel(self, channel_name):
        """Sauvegarde les paramètres actuels d'une voie spécifique dans current_params."""
        mode = self.var_gbf.get()

        self.current_params[mode][channel_name]["func"] = self.channels[channel_name]["combobox_func"].get()
        self.current_params[mode][channel_name]["freq"] = self.channels[channel_name]["value_freq"].get()
        self.current_params[mode][channel_name]["volt"] = self.channels[channel_name]["value_volt"].get()
        self.current_params[mode][channel_name]["offset"] = self.channels[channel_name]["value_offset"].get()
        self.current_params[mode][channel_name]["load"] = self.channels[channel_name]["combobox_load"].get()
        self.current_params[mode][channel_name]["phase"] = self.channels[channel_name]["value_phase"].get()
        self.current_params[mode][channel_name]["etat"] = self.channels[channel_name]["var_etat"].get()

        print(f"Paramètres enregistrés pour la voie {channel_name}:")
        print(self.current_params[mode][channel_name])

    def reset_to_default(self, channel_name):
        """Réinitialise les paramètres de la voie au mode par défaut."""
        mode = self.var_gbf.get()
        self.current_params[mode][channel_name] = self.default_params[mode][channel_name].copy()
        # Mise à jour de l'interface uniquement pour cette voie
        params = self.current_params[mode][channel_name]
        # Si la voie spécifiée est "1" ou "2", on modifie uniquement ses widgets
        if channel_name == "1":
            widgets = self.channels["1"]
        elif channel_name == "2":
            widgets = self.channels["2"]
        # Mise à jour des widgets de la voie spécifiée
        widgets["combobox_func"].set(params["func"])
        widgets["value_freq"].set(params["freq"])
        widgets["value_volt"].set(params["volt"])
        widgets["value_offset"].set(params["offset"])
        widgets["combobox_load"].set(params["load"])
        widgets["value_phase"].set(params["phase"])
        widgets["var_etat"].set(params["etat"])

    def update_mode(self):
        """Mise à jour des paramètres selon le mode sélectionné."""
        mode = self.var_gbf.get()
        for channel_name, widgets in self.channels.items():
            params = self.current_params[mode][channel_name]
            widgets["combobox_func"].set(params["func"])
            widgets["value_freq"].set(params["freq"])
            widgets["value_volt"].set(params["volt"])
            widgets["value_offset"].set(params["offset"])
            widgets["combobox_load"].set(params["load"])
            widgets["value_phase"].set(params["phase"])
            widgets["var_etat"].set(params["etat"])

    def transmission_param(self):

        rm = pyvisa.ResourceManager()# Gestion des connexions VISA
        print("Instruments connectés :", rm.list_resources()) # Liste des périphériques connectés
        adresse = rm.list_resources()
        instrument = rm.open_resource(adresse[0])
        instrument.timeout = 10000  # Augmentez le délai d'attente pour éviter les timeouts

        try:
            instrument.write('*RST')
            time.sleep(2)
            response = instrument.query('*IDN?')  # Demander l'identification de l'instrument (juste un exemple)
            print(f"Réponse de l'instrument : {response}")
            # Voie 1 (Canal 1)
            func_voie1 = self.channels["1"]["combobox_func"].get() 
            freq_voie1 = self.channels["1"]["value_freq"].get()   
            volt_voie1 = self.channels["1"]["value_volt"].get()  
            offset_voie1 = self.channels["1"]["value_offset"].get() 
            load_voie1 = self.channels["1"]["combobox_load"].get()
            phase_voie1 = self.channels["1"]["value_phase"].get()
            etat_voie1 = self.channels["1"]["var_etat"].get()
            if(etat_voie1==0):
                etat = "OFF"
            elif(etat_voie1==1):
                etat = "ON"
            # Envoyer les commandes SCPI pour la voie 1
            instrument.write(f'SOUR1:FUNC {func_voie1}; FREQ {freq_voie1}HZ; VOLT {volt_voie1}; VOLT:OFFS {offset_voie1}')
            instrument.write(f'OUTP1:LOAD {load_voie1}') 
            instrument.write(f'SOUR1:PHAS {phase_voie1}')
            instrument.write(f'OUTP1:STAT {etat}')

            func_voie2 = self.channels["2"]["combobox_func"].get() 
            freq_voie2 = self.channels["2"]["value_freq"].get()   
            volt_voie2 = self.channels["2"]["value_volt"].get()  
            offset_voie2 = self.channels["2"]["value_offset"].get() 
            load_voie2 = self.channels["2"]["combobox_load"].get()
            phase_voie2 = self.channels["2"]["value_phase"].get()
            etat_voie2 = self.channels["2"]["var_etat"].get()
            if(etat_voie2==0):
                etat = "OFF"
            elif(etat_voie2==1):
                etat = "ON"
            # Envoyer les commandes SCPI pour la voie 1
            instrument.write(f'SOUR2:FUNC {func_voie2}; FREQ {freq_voie2}HZ; VOLT {volt_voie2}; VOLT:OFFS {offset_voie2}')
            instrument.write(f'OUTP2:LOAD {load_voie2}') 
            instrument.write(f'SOUR2:PHAS {phase_voie2}')
            instrument.write(f'OUTP2:STAT {etat}')

            time.sleep(1)

        except pyvisa.VisaIOError as e:
            print(f"Erreur de communication : {str(e)}")


    """------------------Bloc audio--------------------"""

    def lister_fichiers_wav(self,repertoire, extension):
        self.listbox_wav.delete(0,'end')
        for fichier in os.listdir(repertoire):
            if fichier.endswith(extension):
                #print(fichier)
                self.listbox_wav.insert('end',fichier)

    def afficher_selection_fichier(self):
        global enregistrement
        print("selection")
        selection = self.listbox_wav.curselection()
        if selection:
            index=selection[0]
            enregistrement=self.listbox_wav.get(index)
            print(f"Fichier selectionné : {enregistrement}")
            self.label_fichier.config(text=f"Fichier choisi : {enregistrement}")
        else:
            print("Aucune selection")
            self.label_fichier.config(text="Fichier choisi :  aucune selection")

    def rechercher_audio(self):
        # Ouvrir une fenêtre de sélection de fichier
        fichier = tk.filedialog.askopenfilename(
            title="Sélectionner un audio wav",
            filetypes=[("Fichiers audio", ".wav")]
        )

        if fichier:  # Si un fichier est sélectionné
            try:
                # Ajouter le fichier à la Listbox
                nom_fichier = os.path.basename(fichier)
                self.listbox_spectre.insert(tk.END, nom_fichier)

                script_dir = os.path.dirname(os.path.abspath(__file__))
                #img_spectre_dir = os.path.join(script_dir, "img_spectre")
                chemin_destination = os.path.join(script_dir, nom_fichier)
                shutil.copy(fichier, chemin_destination)

                messagebox.showinfo("Succès", f"Audio ajoutée et enregistrée : {nom_fichier}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")


    def run_audio_thread(self):
        if not self.audio_thread_running:  # Vérifie qu'aucun thread n'est en cours
            self.audio_thread_running = True
            threading.Thread(target=self.affichage_audio_thread, daemon=True).start()
        else:
            print("Un thread audio est déjà en cours.")

    def affichage_audio_thread(self):
        try:
            affichage_audio(enregistrement, self.update_audio_image)
        except Exception as e:
            print(f"Erreur dans le thread audio: {e}")
        finally:
            self.audio_thread_running = False  # Thread terminé 

    def update_audio_image(self, image_path):
        self.after(0, lambda: self.update_canvas_with_image(image_path))
    
    def update_canvas_with_image(self, image_path):
        image = Image.open(image_path)
        
        canvas_width = self.audio_canvas.winfo_width()
        canvas_height = self.audio_canvas.winfo_height()
        
        margin = 50
        image_width, image_height = image.size
        width_with_margin = canvas_width - 2 * margin
        height_with_margin = canvas_height - 2 * margin
        
        image = image.resize((width_with_margin, height_with_margin), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(image=image)
        x_pos = margin
        y_pos = margin
        
        self.audio_canvas.create_image(x_pos, y_pos, anchor="nw", image=img)
        self.audio_canvas.image = img
        self.label_img1.config(text=f"Fichier audio : {enregistrement}")

    def save_img_spec(self):
        global mode
        user_input = self.entry_specname.get()
        spec_name = f"{user_input}.png"
        
        # Obtenir le chemin du dossier du script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Chemin du sous-dossier img_spectre
        img_spectre_dir = os.path.join(script_dir, "img_spectre")
        # Chemin complet pour enregistrer l'image
        save_path = os.path.join(img_spectre_dir, spec_name)
        
        print(spec_name)
        if(mode==0):
            img = Image.open(os.path.join(img_spectre_dir, 'spectre_doppler.png'))
        else:
            img = Image.open(os.path.join(img_spectre_dir, 'spectre_synchro.png'))
        img.save(save_path, format="PNG")
        self.entry_specname.delete(0,'end')

    """-------------Bloc spectrogramme--------------"""

    def select_mode(self):
        global mode
        mode = self.var_mode.get()
        if (mode==0):
            self.value_zpad.set(100)  
            self.value_Tp.set(0.500) 
        else:   
            self.entry_zpad.config(from_=1, to=200)
            self.value_zpad.set(2)  
            self.entry_Tp.config(from_=0.005, to=0.1, increment=0.005)
            self.value_Tp.set(0.020) 

    def select_data(self):
        global data
        data = self.var_data.get()

    def entry_zpad_changed(self):
        global zpad_doppler, zpad_synchro, mode
        if mode==0:
            zpad_doppler = self.value_zpad.get()
            print(zpad_doppler)
        else :
            zpad_synchro = self.value_zpad.get()
            print(zpad_synchro)
        
    def entry_Tp_changed(self):
        global tp_doppler, tp_synchro, mode
        if mode==0:
            tp_doppler = self.value_Tp.get()
            print(tp_doppler)
        else :
            tp_synchro = self.value_Tp.get()
            print(tp_synchro)

    def afficher_selection_color(self):
        global cmap
        print("selection")
        selection = self.listbox_color.curselection()
        if selection:
            index=selection[0]
            cmap=self.listbox_color.get(index)
            print(f"Couleur choisi : {cmap}")
            self.label_color.config(text=f"Couleur choisi : {cmap}", bg="white")
        else:
            print("Aucune selection")
            self.label_color.config(text="Couleur par défaut :  plasma")

    def run_spectrogram_thread(self):
        if not self.spectrogram_thread_running:  # Vérifie qu'aucun thread n'est en cours
            self.spectrogram_thread_running = True
            threading.Thread(target=self.spectrogramme_thread, daemon=True).start()
        else:
            print("Un thread du spectrogramme est déjà en cours.")

    def spectrogramme_thread(self):
        global mode
        try:
            if not self.running:
                return  # Arrêter immédiatement si la fenêtre est fermée
            if(mode==0):
                spectrogramme_doppler(enregistrement, self.update_spectrogram_image,self.queue_manager)
            else:
                spectrogramme_synchro(enregistrement, self.update_spectrogram_image,self.queue_manager)
        except Exception as e:
            print(f"Erreur dans le thread du spectrogramme: {e}")
        finally:
            self.spectrogram_thread_running = False  # Thread terminé

    def update_spectrogram_image(self, spec_name):
        self.after(0, lambda: self.update_spectrogram_canvas(spec_name))

    def update_spectrogram_canvas(self,spec_name):
        # Déterminer le dossier img_spectre
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_spectre_dir = os.path.join(script_dir, "img_spectre")
        # Construire le chemin complet de l'image
        image_path = os.path.join(img_spectre_dir, spec_name)
        image = Image.open(image_path)
        
        canvas_width = self.spectrogram_canvas.winfo_width()
        canvas_height = self.spectrogram_canvas.winfo_height()
        
        margin = 80
        image_width, image_height = image.size
        width_with_margin = canvas_width - 2 * margin
        height_with_margin = canvas_height - 2 * margin
        
        image = image.resize((width_with_margin, height_with_margin), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(image=image)
        x_pos = margin
        y_pos = margin
        
        self.spectrogram_canvas.create_image(x_pos, y_pos, anchor="nw", image=img)
        self.spectrogram_canvas.image = img
        self.label_img2.config(text=f"Fichier audio : {enregistrement}")

    def afficher_selection_spectre(self,callback):
        global spectre
        print("spectre")
        selection = self.listbox_spectre.curselection()
        if selection:
            index=selection[0]
            spectre=self.listbox_spectre.get(index)
            callback(spectre)

    def lister_spectre_img(self, repertoire, extension):
        self.listbox_spectre.delete(0,'end')
        for fichier in os.listdir(repertoire):
            if any(fichier.lower().endswith(ext) for ext in extension):
                #print(fichier)
                self.listbox_spectre.insert('end',fichier)

    def rechercher_image(self):
        # Ouvrir une fenêtre de sélection de fichier
        fichier = tk.filedialog.askopenfilename(
            title="Sélectionner un spectrogramme",
            filetypes=[("Fichiers image", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )

        if fichier:  # Si un fichier est sélectionné
            try:
                # Ajouter le fichier à la Listbox
                nom_fichier = os.path.basename(fichier)
                self.listbox_spectre.insert(tk.END, nom_fichier)

                script_dir = os.path.dirname(os.path.abspath(__file__))
                img_spectre_dir = os.path.join(script_dir, "img_spectre")
                chemin_destination = os.path.join(img_spectre_dir, nom_fichier)
                shutil.copy(fichier, chemin_destination)

                messagebox.showinfo("Succès", f"Image ajoutée et enregistrée : {nom_fichier}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

    def process_queue(self):
        """Met à jour l'interface utilisateur en fonction des messages de la file d'attente"""
        #print("Appel de process_queue, threads actifs :", threading.enumerate())
        try:
            while not self.queue_manager.empty():
                action, value = self.queue_manager.get_nowait()
                print(f"Queue action: {action}, value: {value}")
                if action == "progress":
                    print(f"Progression : {value}")  # Debug en console
                elif action == "error":
                    print(f"Erreur : {value}")
                elif action == "progress_bar":
                    self.progress_var.set(value)
                    #self.progress_bar.update_idletasks()
            # Replanifiez uniquement si l'application est encore ouverte
            if self.running:
                self.after_id = self.after(100, self.process_queue)   
        except queue.Empty:
            pass

    def on_close(self):      
        print("Fermeture de l'application")
        # Annuler les tâches Tkinter planifiées
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        # Signaler l'arrêt des threads secondaires
        self.running = False  
        self.arret.set()
        # Attendre la fin des threads créés
        for thread in threading.enumerate():
            if thread != threading.main_thread() and thread.daemon:
                print(f"Attente de la fin du thread : {thread.name}")
                thread.join(timeout=1)
        # Nettoyer les variables et widgets Tkinter
        self.destroy()  # Détruit proprement la fenêtre Tkinter
        print("Threads actifs à la fermeture :", threading.enumerate())   
        print("Application fermée proprement")

def spectrogramme_doppler(audio,callback, queue_manager):
    
    global data, zpad_doppler, tp_doppler, cmap
    try :
        queue_manager.put(("progress", "Lecture du fichier audio"))
        fs, Y = wavfile.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav", audio))
    
        # Paramètres radar
        c = 3e8  # Vitesse de la lumière (m/s)
        Tp = tp_doppler  # Temps d'impulsion (s)
        N = int(Tp * fs)  # Nombre d'échantillons par impulsion
        fc = 2590e6  # Fréquence centrale (Hz)

        # Sélection du bon canal en fonction du radio bouton data
        queue_manager.put(("progress", "Inversion des données audio"))
        s = -1 * Y[:, data]  # En partant du principe que Y est stéréo

        # Création de l'ensemble de données Doppler vs temps
        queue_manager.put(("progress", "Création des données Doppler"))
        num_pulses = round(len(s) / N) - 1
        sif = np.array([s[i * N:(i + 1) * N] for i in range(num_pulses)])

        # Soustraire le DC moyen
        sif = sif - np.mean(sif, axis=1, keepdims=True)

        # Zero-padding et FFT 
        queue_manager.put(("progress", "Calcul de la FFT"))
        zpad = zpad_doppler * N  # Modifier zpad pour plus ou moins de détails
        v = np.fft.ifft(sif, n=zpad, axis=1)
        v = np.abs(v[:, :v.shape[1] // 2])  # Magnitude et moitié des valeurs

        # Transformation en décibels
        def dbv(in_signal):
            return 20 * np.log10(np.abs(in_signal) + 1e-12)

        v_db = dbv(v)

        # Ajustement de l'échelle des couleurs
        vmin, vmax = -35, 0

        # Calcul de la vitesse et du temps
        delta_f = np.linspace(0, fs / 2, v.shape[1])  # Fréquence en Hz
        lambda_ = c / fc
        velocity = delta_f * lambda_ / 2
        time = np.linspace(0, Tp * num_pulses, num_pulses)  # Temps en secondes

        # Génération du spectrogramme
        queue_manager.put(("progress", "Génération du spectrogramme"))
        plt.figure(figsize=(10, 6))
        plt.imshow(v_db, aspect='auto', extent=[velocity[0], velocity[-1], time[-1], time[0]], vmin=vmin, vmax=vmax, cmap=cmap)
        plt.colorbar(label='Magnitude (dB)')
        plt.xlim([0, 40])
        plt.xlabel('Vitesse (m/sec)')
        plt.ylabel('Temps (sec)')
        plt.title('Doppler vs. Temps')

        # Sauvegarde du spectrogramme
        spec_name = 'spectre_doppler.png'
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_spectre_dir = os.path.join(script_dir, "img_spectre")
        os.makedirs(img_spectre_dir, exist_ok=True)
        save_path = os.path.join(img_spectre_dir, spec_name)
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()

        # Appeler le callback pour mettre à jour l'interface utilisateur
        queue_manager.put(("progress", f"Spectrogramme enregistré : {save_path}"))
        callback(spec_name)

    except Exception as e:
        error_message = f"Erreur dans spectrogramme_doppler : {e}"
        print(error_message)
        queue_manager.put(("error", error_message))

def spectrogramme_synchro(audio, callback, queue_manager):
    
    global data, zpad_synchro, tp_synchro, cmap
    try:
        queue_manager.put(("progress", "Lecture du fichier audio"))
        fs, Y = wavfile.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav", audio))
    
        # Constantes
        c = 3e8  # Vitesse de la lumière (m/s)
    
        # Paramètres radar
        Tp = tp_synchro  # Temps d'impulsion (s)
        N = int(Tp * fs)  # Nombre d'échantillons par impulsion
        fstart = 2260e6  # Fréquence de départ LFM (Hz)
        fstop = 2590e6   # Fréquence de fin LFM (Hz)
        BW = fstop - fstart  # Largeur de bande transmise
        f = np.linspace(fstart, fstop, N // 2)  # Fréquence d'émission instantanée
    
        # Résolution en distance
        rr = c / (2 * BW)
        max_range = rr * N / 2
    
        # Inversion du signal
        queue_manager.put(("progress", "Inversion des données audio"))
        trig = -1 * Y[:, 0]  # Canal de déclenchement
        s = -1 * Y[:, data]  # Signal
        print("inversion")
        # Déclenchement par détection de front montant de l'impulsion de synchronisation
        count = 0
        thresh = 0
        start = (trig > thresh)
        sif = []
        time = []
    
        for ii in range(100, len(start) - N):
            if start[ii] == 1 and np.mean(start[ii - 11:ii]) == 0:
                count += 1
                sif.append(s[ii:ii + N])
                time.append(ii / fs)
    
        sif = np.array(sif)
        time = np.array(time)
    
        # Soustraction de la moyenne
        ave = np.mean(sif, axis=0)
        sif = sif - ave
    
        # Zero-padding
        queue_manager.put(("progress", "Calcul de la FFT"))
        #zpad = 8 * N // 2
        zpad = zpad_synchro * N
        print(zpad)
        # Fonction pour convertir en décibels
        def dbv(in_signal, offset=1e-6):
            return 20 * np.log10(np.abs(in_signal) + offset)
        
        # Tracé RTI avec annulation d’impulsions à 2 échantillons
        sif2 = sif[1:] - sif[:-1]  # Soustraction des impulsions
        v = np.fft.ifft(sif2, n=zpad, axis=1)
        S = dbv(v[:, :v.shape[1] // 2])
        m = np.max(S)
        print("v_db")
        # Création de l'axe de distance
        #R = np.linspace(0, max_range, zpad)
        
        queue_manager.put(("progress", "Génération du spectrogramme"))
        plt.figure(20)
        plt.imshow(S - m, aspect='auto', extent=[0, max_range, time[-1], time[0]], vmin=-80, vmax=0, cmap=cmap)
        plt.colorbar()
        plt.ylabel('Temps (s)')
        plt.xlabel('Distance (m)')
        plt.title('RTI avec élimination de clutter à 2 impulsions')
        print("spectrogramme synchro")
        
        spec_name = 'spectre_synchro.png'
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_spectre_dir = os.path.join(script_dir, "img_spectre")
        save_path = os.path.join(img_spectre_dir, spec_name)
        
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
    
        # Call the callback function to update the GUI
        queue_manager.put(("progress", f"Spectrogramme enregistré : {save_path}"))
        callback(spec_name)
        
    except Exception as e:
        error_message = f"Erreur dans spectrogramme_synchro : {e}"
        print(error_message)
        queue_manager.put(("error", error_message))

def affichage_audio(audio,callback):
    
    fs, Y = wavfile.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav", audio))
    
    #number of samples
    nb_Y = Y.shape[0]
    #audio time duration
    a_fs = nb_Y / fs

    #plot signal versus time
    t = np.linspace(0,a_fs,nb_Y)
    
    plt.figure(figsize=(12, 4))  # proportion de l'image
    
    plt.subplot(2,1,1)
    plt.plot(t,Y[:,0],'turquoise')
    plt.ylabel('Left')

    plt.subplot(2,1,2)
    plt.plot(t,Y[:,1],'mediumorchid')
    plt.ylabel('Right')
    plt.xlabel('Time (s)')
    print("audio")
    
    image_path = 'audio.png'
    plt.savefig(image_path, bbox_inches='tight')
    plt.close()
    
    # Call the callback function to update the GUI
    callback(image_path)

def enregistrer(entry_filename, var_channels, entry_duration, progress_var, fenetre):
    # Récupérer le nom du fichier depuis l'input
    filename = entry_filename.get()

    # Ajouter l'extension .wav si besoin
    if not filename.lower().endswith(".wav"):
        filename += ".wav"

    # Récupérer le nombre de canaux sélectionné (1 ou 2)
    channels = var_channels.get()

    # Récupérer la durée depuis l'entrée
    try:
        duration = int(entry_duration.get())  # Convertir la durée en entier
    except ValueError:
        messagebox.showerror("Erreur", "Entrez une durée valide en secondes.")
        return

    # Paramètres de l'enregistrement
    samplerate = 44100  # Fréquence d'échantillonnage
    
    def update_progress(elapsed_time):
        if not fenetre.winfo_exists():
            return  # Arrête la mise à jour si la fenêtre est détruite
        progress_percentage = int((elapsed_time / duration) * 100)
        progress_var.set(progress_percentage)
        fenetre.progress_bar.update_idletasks()
        
    def recording_task():
        try:
            # Démarrer l'enregistrement
            fenetre.queue_manager.put(("progress", "Enregistrement en cours..."))
            audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')

            # Mettre à jour la barre de progression
            elapsed_time = 0
            time_interval = 0.1  # Intervalle entre chaque mise à jour

            while elapsed_time < duration:
                time.sleep(time_interval)
                elapsed_time += time_interval
                progress_percentage = int((elapsed_time / duration) * 100)
                
                # Envoyer la progression via la queue
                fenetre.queue_manager.put(("progress_bar", progress_percentage))

            sd.wait()  # Attendre que l'enregistrement se termine

            # Sauvegarder le fichier
            chemin_sauvegarde = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav", filename)
            sf.write(chemin_sauvegarde, audio_data, samplerate)
            print(f"Enregistrement terminé. Fichier sauvegardé sous '{filename}'.")

            # Message de succès
            messagebox.showinfo("Succès", f"Enregistrement terminé et sauvegardé sous '{filename}'")
            fenetre.queue_manager.put(("success", f"Enregistrement terminé et sauvegardé sous {filename}"))
        except Exception as e:
            fenetre.queue_manager.put(("error", f"Une erreur est survenue : {e}"))
        finally:
            fenetre.queue_manager.put(("progress_bar", 0))  # Réinitialiser la barre de progression

    # Réinitialiser la barre de progression avant de commencer
    progress_var.set(0)

    # Lancer l'enregistrement dans un thread séparé
    threading.Thread(target=recording_task, daemon=True).start()

def main():
    print("start")
    fenetre = MyWindow()
    fenetre.lister_fichiers_wav(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav"),'.wav')
    fenetre.lister_spectre_img(os.path.join(os.path.dirname(os.path.abspath(__file__)), "img_spectre"), [".png", ".jpg", ".jpeg", ".bmp", ".gif"])
    fenetre.mainloop()
    
            
            
if __name__ == '__main__':
    main()