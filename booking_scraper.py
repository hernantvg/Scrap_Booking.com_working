from playwright.sync_api import sync_playwright
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def scrape_hotel_description_with_retry(hotel_url, max_retries=3):
    for retry in range(max_retries):
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
            print(f"Error en el intento {retry + 1}: {str(e)}")
    return "Error: Se ha excedido el número máximo de intentos."

def get_element_text_with_retry(element, selector, max_retries=3):
    for retry in range(max_retries):
        try:
            return element.locator(selector).inner_text(timeout=5000)
        except playwright._impl._api_types.TimeoutError:
            print(f"Timeout en el intento {retry + 1}. Reintentando...")
    return "No disponible (timeout)"

def scrape_popular_facilities_with_retry(hotel_url, max_retries=3):
    for retry in range(max_retries):
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
            print(f"Error en el intento {retry + 1}: {str(e)}")
    return ["Error: Se ha excedido el número máximo de intentos."]

def scrape_hotels_on_page(page, city, country):
    hotels = page.locator('//div[@data-testid="property-card"]').all()
    hotels_list = []
    for hotel in hotels:
        print("Procesando un nuevo hotel...")
        hotel_dict = {}
        hotel_dict['hotel'] = get_element_text_with_retry(hotel, '//div[@data-testid="title"]')
        hotel_dict['price'] = get_element_text_with_retry(hotel, '//span[@data-testid="price-and-discounted-price"]')
        # Handling exceptions for specific elements
        try:
            hotel_dict['score'] = get_element_text_with_retry(hotel, '//div[@data-testid="review-score"]/div[1]')
        except Exception as e:
            print(f"Error al obtener la puntuación: {str(e)}")
            hotel_dict['score'] = "ver..."

        try:
            hotel_dict['avg_review'] = get_element_text_with_retry(hotel, '//div[@data-testid="review-score"]/div[2]/div[1]')
        except Exception as e:
            print(f"Error al obtener la revisión promedio: {str(e)}")
            hotel_dict['avg_review'] = "ver..."

        try:
            hotel_dict['reviews_count'] = get_element_text_with_retry(hotel, '//div[@data-testid="review-score"]/div[2]/div[2]').split()[0]
        except Exception as e:
            print(f"Error al obtener la cantidad de revisiones: {str(e)}")
            hotel_dict['reviews_count'] = "ver..."

        # Get image link
        image = hotel.locator('//a[@data-testid="property-card-desktop-single-image"]/img').get_attribute("src")
        if image:
            # Modify the URL from "square200" to "max1024x768"
            image = image.replace("square200", "max1024x768")
        hotel_dict['image_links'] = image if image else None

        # Get hotel URL
        hotel_link_element = hotel.locator('//a[@data-testid="availability-cta-btn"]')
        if hotel_link_element:
            hotel_link = hotel_link_element.get_attribute("href")
            if hotel_link:
                # Truncate the link to ".html" and add "?aid=2410095"
                hotel_link = f"{hotel_link.split('.html')[0]}.html?aid=2410095"
                hotel_dict['hotel_url'] = hotel_link

        # Tu código existente para obtener y procesar las instalaciones populares
        popular_facilities = scrape_popular_facilities_with_retry(hotel_link)
        hotel_dict['popular_facilities'] = ', '.join(set(popular_facilities))  # Unir y eliminar duplicados

        # Add city and country information
        hotel_dict['city'] = city
        hotel_dict['country'] = country

        hotels_list.append(hotel_dict)

    return hotels_list

def scrape_all_pages(base_url, page_count, city, country):
    hotels_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/69.0.3497.100 Safari/537.36"
        )
        page = browser.new_page(user_agent=ua)

        for page_number in range(1, page_count + 1):
            page_url = f'{base_url}&offset={25 * (page_number - 1)}'
            print(f'Visitando la página: {page_url}')
            page.goto(page_url, timeout=120000)

            hotels_list.extend(scrape_hotels_on_page(page, city, country))

            print(f'Página {page_number} procesada. Total de hoteles hasta ahora: {len(hotels_list)}')

        browser.close()

    return hotels_list

def main():
    language = 'es'
    country = 'Chile'
    city = 'Santiago'
    # Obtener la fecha actual y calcular las fechas de checkin y checkout
    today = datetime.now()
    checkin_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
    checkout_date = (today + timedelta(days=11)).strftime('%Y-%m-%d')

    base_url = f'https://www.booking.com/searchresults.{language}.html?&checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city}&lang={language}&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'

    # Adjust the range to get more pages if needed
    hotels_list = scrape_all_pages(base_url, page_count=8, city=city, country=country)

    # Add description to each hotel
    for hotel in hotels_list:
        hotel['description'] = scrape_hotel_description_with_retry(hotel['hotel_url'])

    df = pd.DataFrame(hotels_list)
    # df.to_excel(f'data/{city}.xlsx', index=False)
    df.to_csv(f'data/{city}.csv', index=False)

if __name__ == '__main__':
    main()
