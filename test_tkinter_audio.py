import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import soundfile as sf

def enregistrer():
    # Récupérer le nom du fichier depuis l'input
    filename = entry_filename.get()

    # Ajouter l'extension .wav si elle n'est pas présente
    if not filename.lower().endswith(".wav"):
        filename += ".wav"

    # Récupérer le nombre de canaux sélectionné (1 ou 2)
    channels = var_channels.get()

    # Récupérer la durée depuis l'entrée
    try:
        duration = int(entry_duration.get())  # Convertir la durée en entier
    except ValueError:
        messagebox.showerror("Erreur", "Veuillez entrer une durée valide en secondes.")
        return

    # Paramètres de l'enregistrement
    samplerate = 44100  # Fréquence d'échantillonnage

    try:
        # Démarrer l'enregistrement
        print("Enregistrement en cours...")
        audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')
        sd.wait()  # Attendre que l'enregistrement se termine

        # Sauvegarder le fichier
        sf.write(filename, audio_data, samplerate)
        print(f"Enregistrement terminé. Fichier sauvegardé sous '{filename}'.")

        # Afficher un message de succès
        messagebox.showinfo("Succès", f"Enregistrement terminé et sauvegardé sous '{filename}'")
        # Fermer la fenêtre Tkinter après l'enregistrement
        root.quit()
        root.destroy()
    except Exception as e:
        # Afficher un message d'erreur si quelque chose échoue
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")
        root.quit()
        root.destroy()

# Créer la fenêtre principale
root = tk.Tk()
root.title("Enregistrement Audio")

# Créer un label et une entrée pour le nom du fichier
label_filename = tk.Label(root, text="Entrez le nom du fichier :")
label_filename.pack(pady=10)

entry_filename = tk.Entry(root, width=30)
entry_filename.pack(pady=5)

# Créer un label pour choisir le nombre de canaux
label_channels = tk.Label(root, text="Choisir le nombre de canaux :")
label_channels.pack(pady=10)

# Variable pour stocker le nombre de canaux (1 ou 2)
var_channels = tk.IntVar()
var_channels.set(1)  # Valeur par défaut (mono)

# Créer les boutons radio pour 1 ou 2 canaux
radio_button_1 = tk.Radiobutton(root, text="1 Canal (Mono)", variable=var_channels, value=1)
radio_button_1.pack(pady=5)

radio_button_2 = tk.Radiobutton(root, text="2 Canaux (Stéréo)", variable=var_channels, value=2)
radio_button_2.pack(pady=5)

# Créer un label et un champ pour saisir la durée
label_duration = tk.Label(root, text="Durée de l'enregistrement (en secondes) :")
label_duration.pack(pady=10)

entry_duration = tk.Entry(root, width=10)
entry_duration.pack(pady=5)
entry_duration.insert(0, "5")  # Valeur par défaut (5 secondes)

# Créer un bouton pour lancer l'enregistrement
button_enregistrer = tk.Button(root, text="Lancer l'enregistrement", command=enregistrer)
button_enregistrer.pack(pady=20)

# Lancer l'interface graphique
root.mainloop()
