import requests
from bs4 import BeautifulSoup
import logging

def scrape_popular_facilities_with_retry(hotel_url, max_retries=3):
    for retry in range(max_retries):
        try:
            response = requests.get(hotel_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                facilities_elements = soup.find_all('span', class_='e39ce2c19b')
                facilities_list = [facility.get_text(strip=True) for facility in facilities_elements]
                return facilities_list
            else:
                return ["Error al acceder a la página del hotel."]
        except Exception as e:
            logging.error(f"Error en el intento {retry + 1}: {str(e)}")
    
    return ["Error: Se ha excedido el número máximo de intentos."]

# Ejemplo de uso:
hotel_url = 'https://www.booking.com/hotel/th/cher-hostel-bangkok.es.html?aid=2410095'
facilities = scrape_popular_facilities_with_retry(hotel_url)
print(facilities)
