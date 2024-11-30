import sounddevice as sd

print(sd.query_devices())  # Affiche tous les périphériques audio disponibles
print("Périphérique par défaut:", sd.default.device)  # Affiche le périphérique par défaut
