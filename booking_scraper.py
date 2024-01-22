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

def scrape_hotels_on_page(page, city, country):
    hotels = page.locator('//div[@data-testid="property-card"]').all()
    hotels_list = []
    for hotel in hotels:
        hotel_dict = {}
        hotel_dict['hotel'] = hotel.locator('//div[@data-testid="title"]').inner_text()
        hotel_dict['price'] = hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
        hotel_dict['score'] = hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
        hotel_dict['avg review'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
        hotel_dict['reviews count'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text().split()[0]

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
        popular_facilities = scrape_popular_facilities(hotel_link)
        hotel_dict['popular_facilities'] = ', '.join(set(popular_facilities))  # Unir y eliminar duplicados

        # Add city and country information
        hotel_dict['city'] = city
        hotel_dict['country'] = country

        hotels_list.append(hotel_dict)

    return hotels_list

def main():
    with sync_playwright() as p:
        language = 'es'
        country = 'Uruguay'
        city = 'Piriápolis'      
        # Obtener la fecha actual y calcular las fechas de checkin y checkout
        today = datetime.now()
        checkin_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
        checkout_date = (today + timedelta(days=11)).strftime('%Y-%m-%d')

        base_url = f'https://www.booking.com/searchresults.{language}.html?&checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city}&lang={language}&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'

        browser = p.chromium.launch(headless=True)
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/69.0.3497.100 Safari/537.36"
        )
        page = browser.new_page(user_agent=ua)

        hotels_list = []  # Initialize outside the loop

        # Adjust the range to get more pages if needed
        for page_number in range(1, 3):
            page_url = f'{base_url}&offset={25 * (page_number - 1)}'
            page.goto(page_url, timeout=120000)

            hotels_list.extend(scrape_hotels_on_page(page, city, country))

            print(f'Page {page_number}: There are {len(hotels_list)} hotels.')

        # Add description to each hotel
        for hotel in hotels_list:
            hotel['description'] = scrape_hotel_description(hotel['hotel_url'])

        df = pd.DataFrame(hotels_list)
        # df.to_excel(f'data/{city}.xlsx', index=False)
        df.to_csv(f'data/{city}.csv', index=False)

        browser.close()

if __name__ == '__main__':
    main()