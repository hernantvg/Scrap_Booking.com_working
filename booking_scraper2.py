from playwright.sync_api import sync_playwright
import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

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

def scrape_popular_facilities(hotel_url):
    try:
        response = requests.get(hotel_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            facilities_elements = soup.find_all('span', class_='a5a5a75131')
            facilities_list = [facility.get_text(strip=True) for facility in facilities_elements]
            return facilities_list
        else:
            return ["Error al acceder a la página del hotel."]
    except Exception as e:
        return [f"Error: {str(e)}"]

def scrape_hotels_on_page(page, city, country, hotel_name, hotel_url):
    hotel_dict = {}
    hotel_dict['hotel'] = hotel_name
    hotel_dict['city'] = city
    hotel_dict['country'] = country
    hotel_dict['hotel_url'] = hotel_url

    # Tu código existente para obtener y procesar las instalaciones populares
    popular_facilities = scrape_popular_facilities(hotel_url)
    hotel_dict['popular_facilities'] = ', '.join(set(popular_facilities))  # Unir y eliminar duplicados

    # Add description to each hotel
    hotel_dict['description'] = scrape_hotel_description(hotel_url)

    return hotel_dict

def main():
    with sync_playwright() as p:
        language = 'es'
        country = 'Uruguay'

        # Leer las URLs desde el archivo CSV
        csv_file_path = 'input/hotels2.csv'
        hotels_df = pd.read_csv(csv_file_path)

        browser = p.chromium.launch(headless=True)
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/69.0.3497.100 Safari/537.36"
        )
        page = browser.new_page(user_agent=ua)

        hotels_list = []  # Initialize outside the loop

        for index, row in hotels_df.iterrows():
            hotel_name = row['Hotels']
            city = row['City']
            hotel_url = row['URL']

            page.goto(hotel_url, timeout=120000)
            hotel_info = scrape_hotels_on_page(page, city, country, hotel_name, hotel_url)
            hotels_list.append(hotel_info)

        df = pd.DataFrame(hotels_list)
        df.to_csv(f'data/{country}_{city}.csv', index=False)

        browser.close()

if __name__ == '__main__':
    main()