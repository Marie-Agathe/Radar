# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 11:32:17 2024

@author: Magathe
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
from matplotlib.colors import LinearSegmentedColormap

# Lecture du fichier audio
fs, Y = wavfile.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_wav", 'longue_distance.wav'))
#fs, Y = wavfile.read('longue_distance.wav')
# Constantes
c = 3e8  # Vitesse de la lumière (m/s)

# Paramètres radar
Tp = 0.05#20e-3  # Temps d'impulsion (s)
N = int(Tp * fs)  # Nombre d'échantillons par impulsion
fstart = 2260e6  # Fréquence de départ LFM (Hz)
fstop = 2590e6   # Fréquence de fin LFM (Hz)
BW = fstop - fstart  # Largeur de bande transmise
f = np.linspace(fstart, fstop, N // 2)  # Fréquence d'émission instantanée

# Résolution en distance
rr = c / (2 * BW)
max_range = rr * N / 2
#print(max_range)
# Inversion du signal
trig = -1 * Y[:, 0]  # Canal de déclenchement
s = -1 * Y[:, 0]  # Signal

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
zpad = 1 * N
# Fonction pour convertir en décibels
def dbv(in_signal, offset=1e-6):
    return 20 * np.log10(np.abs(in_signal) + offset)

# Tracé RTI avec annulation d’impulsions à 2 échantillons
sif2 = sif[1:] - sif[:-1]  # Soustraction des impulsions
v = np.fft.ifft(sif2, n=zpad, axis=1)
S = dbv(v[:, :v.shape[1] // 2])
m = np.max(S)
min_S = np.min(S)
moy_S = np.mean(S)
print(m)
print(min_S)
print(moy_S)

N_pixel = 51
Nb_ligne = np.matrix(S)
Nb_ligne = Nb_ligne.shape
N_ligne_av_ap = N_pixel//2
#print(Nb_ligne[0])
result = [row[:] for row in S]

for i in range(N_ligne_av_ap,Nb_ligne[0]-N_ligne_av_ap):
    result[i] = np.mean(S[i-N_ligne_av_ap:i+N_ligne_av_ap], axis=0)
    
cleaned_data = [[float(value) for value in row] for row in result]
#print(cleaned_data)
# Convertir cleaned_data en un tableau NumPy pour faciliter les calculs
cleaned_data_array = np.array(cleaned_data)
# Calculer la différence absolue entre lignes consécutives
diff = np.abs(cleaned_data_array[:-1] - cleaned_data_array[1:])

# print (diff)
m_diff = np.max(diff)
min_diff = np.min(diff)
moy_diff = np.mean(diff)
print(m_diff)
print(min_diff)
print(moy_diff)
# Création de l'axe de distance
#R = np.linspace(0, max_range, zpad)

plt.figure(1)
plt.imshow(diff - m_diff, aspect='auto', extent=[0, max_range, time[-1], time[1]],vmin=0, vmax=0.2, cmap='plasma')
plt.colorbar()
plt.ylabel('Temps (s)')
plt.xlabel('Distance (m)')
plt.title('Différence')

plt.figure(2)
plt.imshow(S - m, aspect='auto', extent=[0, max_range, time[-1], time[0]],vmin=-80,vmax=0, cmap='plasma')
plt.colorbar()
plt.ylabel('Temps (s)')
plt.xlabel('Distance (m)')
plt.title('Spectrogramme normal')

plt.show()