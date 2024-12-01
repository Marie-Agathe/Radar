# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 20:25:28 2024

@author: Magathe
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from matplotlib.colors import LinearSegmentedColormap

# Lire le fichier audio
#fs, Y = wavfile.read('doppler_mit.wav')
fs, Y = wavfile.read('Doppler_11.wav')
fs, Y = wavfile.read('test.wav')
#interface
# Constantes
c = 3e8  # Vitesse de la lumière (m/s)

# Paramètres radar
Tp = 0.5 # Temps d'impulsion (s)
N = int(Tp * fs)  # Nombre d'échantillons par impulsion
fc = 2590e6  # Fréquence centrale (Hz)

# Inversion du signal (en prenant le deuxième canal pour stéréo)
# s = -1 * Y[:, 1] if Y.ndim > 1 else -1 * Y  # Utilise la deuxième colonne si elle existe
s = -1 * Y[:, 0]  # Assuming Y is stereo and we are interested in the second channel
#s = -1 * Y[:, 1] pour l'audio du MIT
# Création de l'ensemble de données Doppler vs temps
num_pulses = round(len(s) / N) - 1
sif = np.array([s[i * N:(i + 1) * N] for i in range(num_pulses)])

# Soustraire le DC moyen
sif = sif - np.mean(sif, axis=1, keepdims=True)

# Zero-padding et FFT
zpad = 8 * N // 2                   #Modifier zpad pour plus ou moins de détails
zpad =100 * N
v = np.fft.ifft(sif, n=zpad, axis=1)
v = np.abs(v[:, :v.shape[1] // 2])  # Magnitude et moitié des valeurs

# Transformation en décibels (ajout epsilon pour éviter log(0))
def dbv(in_signal):
    return 20 * np.log10(np.abs(in_signal) + 1e-12)
# def dbv(in_signal, offset=1e-6):
#     return 20 * np.log10(np.abs(in_signal) + offset)

v_db = dbv(v)
# v_db = dbv(v, offset=1e-4)

# # Appliquer un lissage en moyenne mobile
# def moving_average(data, window_size=3):
#     return np.convolve(data, np.ones(window_size) / window_size, mode='same')

# v_db = np.apply_along_axis(moving_average, 1, v_db, window_size=5)

# Ajustement de l'échelle des couleurs
vmin, vmax = -35, 0  # Limite comme en MATLAB

# Calcul de la vitesse et du temps
delta_f = np.linspace(0, fs / 2, v.shape[1])  # Fréquence en Hz
lambda_ = c / fc
velocity = delta_f * lambda_ / 2
time = np.linspace(0, Tp * num_pulses, num_pulses)  # Temps en secondes

# Création d'une palette de couleur personnalisée (du jaune au bleu)
yellow_blue_cmap = LinearSegmentedColormap.from_list("YellowBlue", ["yellow", "blue"])

# Affichage du graphique avec l'échelle de couleur ajustée
plt.figure(figsize=(10, 6))
plt.imshow(v_db, aspect='auto', extent=[velocity[0], velocity[-1], time[-1], time[0]], vmin=vmin, vmax=vmax, cmap='plasma')
plt.colorbar(label='Magnitude (dB)')
plt.xlim([0, 40])  # Limiter l'axe de la vitesse
plt.xlabel('Vitesse (m/sec)')
plt.ylabel('Temps (sec)')
plt.title('Doppler vs. Temps')
plt.show()

