import sounddevice as sd
import soundfile as sf

# Paramètres de l'enregistrement
filename = "enregistrement.wav"
samplerate = 44100  # Fréquence d'échantillonnage
duration = 5  # Durée en secondes
channels = 1  # Nombre de canaux (1 pour mono, 2 pour stéréo)

print("Enregistrement en cours...")
# Enregistrement audio dans un tableau numpy
audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')
sd.wait()  # Attendre la fin de l'enregistrement

# Sauvegarde du fichier audio
sf.write(filename, audio_data, samplerate)
print(f"Enregistrement terminé. Fichier sauvegardé sous '{filename}'.")