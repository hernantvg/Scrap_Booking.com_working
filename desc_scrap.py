import requests
from bs4 import BeautifulSoup
import csv

def scrape_hotel_description(hotel_url):
    try:
        response = requests.get(hotel_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            description_element = soup.find('p', class_='a53cbfa6de b3efd73f69')
            if description_element:
                return description_element.get_text(strip=True)
            else:
                return "Descripción no encontrada en la página."
        else:
            return "Error al acceder a la página del hotel."
    except Exception as e:
        return f"Error: {str(e)}"

# Leer el archivo CSV
with open('hotels_list.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        hotel_name = row['hotel']
        hotel_url = row['hotel_url']
        
        # Obtener la descripción del hotel mediante web scraping
        description = scrape_hotel_description(hotel_url)
        
        # Imprimir o guardar la descripción como desees
        print(f"Hotel: {hotel_name}\nDescripción: {description}\n{'-'*50}")
