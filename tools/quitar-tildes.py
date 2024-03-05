import unicodedata

def quitar_tildes(texto):
    return ''.join((c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'))

def main():
    # Lee el archivo de entrada
    with open(r'C:/Users/Hernan/Documents/GitHub/Scrap_Booking.com_working/city.txt', 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Elimina los tildes y caracteres especiales
    contenido_sin_tildes = quitar_tildes(contenido)

    # Guarda el resultado en un nuevo archivo
    with open('C:/Users/Hernan/Documents/GitHub/Scrap_Booking.com_working/city_sin_tildes.txt', 'w', encoding='utf-8') as f:
        f.write(contenido_sin_tildes)

if __name__ == "__main__":
    main()