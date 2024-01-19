import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def obtener_imagenes_principales(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        imagenes = soup.find_all('img', {'class': 'js-lazy-image'})

        for img in imagenes:
            imagen_url = img.get('data-src')
            if imagen_url:
                imagen_url = urljoin(url, imagen_url)
                print("URL de imagen:", imagen_url)

    else:
        print("Error al obtener la página:", response.status_code)

# URL de ejemplo de Booking.com
url_booking = 'https://www.booking.com/district/es/granada/granada-centro.es.html'

obtener_imagenes_principales(url_booking)
