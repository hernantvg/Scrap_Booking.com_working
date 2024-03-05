import requests

def traducir(texto):
    url = "https://translate.1hosting.pro/translate"
    payload = {
        "q": texto,
        "source": "auto",
        "target": "es",
        "format": "text"
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('text', texto)
    else:
        print("Error al traducir:", response.status_code)
        return texto

def main():
    # Leer el archivo de ciudades y países
    with open('C:/Users/Hernan/Documents/GitHub/Scrap_Booking.com_working/city.txt', 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Dividir el contenido en líneas y traducir cada línea
    lineas = contenido.split('\n')
    lineas_traducidas = [traducir(linea) for linea in lineas]

    # Unir las líneas traducidas
    contenido_traducido = '\n'.join(lineas_traducidas)

    # Guardar el resultado en un nuevo archivo
    with open('C:/Users/Hernan/Documents/GitHub/Scrap_Booking.com_working/city_traducido.txt', 'w', encoding='utf-8') as f:
        f.write(contenido_traducido)

if __name__ == "__main__":
    main()
