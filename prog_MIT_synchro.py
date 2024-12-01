# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 11:32:17 2024

@author: Magathe
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from matplotlib.colors import LinearSegmentedColormap

# Lecture du fichier audio
fs, Y = wavfile.read('running_outside_20ms.wav')

# Constantes
c = 3e8  # Vitesse de la lumière (m/s)

# Paramètres radar
Tp = 20e-3  # Temps d'impulsion (s)
N = int(Tp * fs)  # Nombre d'échantillons par impulsion
fstart = 2260e6  # Fréquence de départ LFM (Hz)
fstop = 2590e6   # Fréquence de fin LFM (Hz)
BW = fstop - fstart  # Largeur de bande transmise
f = np.linspace(fstart, fstop, N // 2)  # Fréquence d'émission instantanée

# Résolution en distance
rr = c / (2 * BW)
max_range = rr * N / 2

# Inversion du signal
trig = -1 * Y[:, 0]  # Canal de déclenchement
s = -1 * Y[:, 1]  # Signal

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
#zpad = 8 * N // 2
zpad = 2 * N
# Fonction pour convertir en décibels
def dbv(in_signal, offset=1e-6):
    return 20 * np.log10(np.abs(in_signal) + offset)

# Tracé RTI sans élimination de clutter
v = dbv(np.fft.ifft(sif, n=zpad, axis=1))
S = v[:, :v.shape[1] // 2]
m = np.max(S)
plt.figure(10)
plt.imshow(S - m, aspect='auto', extent=[0, max_range, time[-1], time[0]], vmin=-80, vmax=0, cmap='plasma')
plt.colorbar()
plt.ylabel('Temps (s)')
plt.xlabel('Distance (m)')
plt.title('RTI sans élimination de clutter')

# Tracé RTI avec annulation d’impulsions à 2 échantillons
sif2 = sif[1:] - sif[:-1]  # Soustraction des impulsions
v = np.fft.ifft(sif2, n=zpad, axis=1)
S = dbv(v[:, :v.shape[1] // 2])
m = np.max(S)

# Création de l'axe de distance
R = np.linspace(0, max_range, zpad)

plt.figure(20)
plt.imshow(S - m, aspect='auto', extent=[0, max_range, time[-1], time[0]], vmin=-80, vmax=0, cmap='plasma')
plt.colorbar()
plt.ylabel('Temps (s)')
plt.xlabel('Distance (m)')
plt.title('RTI avec élimination de clutter à 2 impulsions')

plt.show()