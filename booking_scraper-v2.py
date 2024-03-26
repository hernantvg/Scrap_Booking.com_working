import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from backoff import on_exception, expo
from requests.exceptions import HTTPError, ConnectionError

# Configuración de logging
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
LOG_FILE = 'hotel_scraping.log'
logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, encoding='utf-8')

# Eliminar el manejador de consola predeterminado si existe
root_logger = logging.getLogger()
if root_logger.handlers:
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

# Crear un manejador de archivo
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Agregar el manejador de archivo al registro
root_logger.addHandler(file_handler)

# Crear un manejador de consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Agregar el manejador de consola al registro
root_logger.addHandler(console_handler)

# Función decorada para reintentos con backoff exponencial en caso de errores de conexión o HTTP


@on_exception(expo, (ConnectionError, HTTPError), max_tries=3)
def safe_request(url, session):
    response = session.get(url)
    response.raise_for_status()
    return response

# Función para obtener la descripción de un hotel con reintento


def scrape_hotel_description_with_retry(hotel_url, max_retries=3):
    for retry in range(max_retries):
        try:
            response = requests.get(hotel_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                description_element = soup.find(
                    'p', class_='a53cbfa6de b3efd73f69')
                if description_element:
                    return description_element.get_text(strip=True)
                else:
                    return "Descripción no encontrada en la página."
            else:
                return "Error al acceder a la página del hotel."
        except Exception as e:
            logging.error(f"Error en el intento {retry + 1}: {str(e)}")
    return "Error: Se ha excedido el número máximo de intentos."

# Función para obtener el texto de un elemento con reintento


def get_element_text_with_retry(element, selector, max_retries=3):
    for retry in range(max_retries):
        try:
            return element.locator(selector).inner_text(timeout=5000)
        except TimeoutError:
            logging.error(
                f"Timeout en el intento {retry + 1}. Reintentando...")
    return "No disponible (timeout)"

# Función para obtener las instalaciones populares de un hotel con reintento


def scrape_popular_facilities_with_retry(hotel_url, max_retries=3):
    for retry in range(max_retries):
        try:
            response = requests.get(hotel_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                facilities_elements = soup.find_all(
                    'span', class_='a5a5a75131')
                facilities_list = [facility.get_text(
                    strip=True) for facility in facilities_elements]
                return facilities_list
            else:
                return ["Error al acceder a la página del hotel."]
        except Exception as e:
            logging.error(f"Error en el intento {retry + 1}: {str(e)}")
    return ["Error: Se ha excedido el número máximo de intentos."]

# Función para extraer los datos de los hoteles en una página


def scrape_hotels_on_page(page, city, country):
    try:
        hotels = page.locator('//div[@data-testid="property-card"]').all()
    except Exception as e:
        logging.error(f"Error al obtener los hoteles en la página: {str(e)}")
        return []  # Retorna una lista vacía si hay un error

    hotels_list = []
    for hotel in hotels:
        logging.info("Procesando un nuevo hotel...")
        hotel_dict = {}
        hotel_dict['hotel'] = get_element_text_with_retry(hotel, '//div[@data-testid="title"]')

        try:
            hotel_dict['price'] = get_element_text_with_retry(hotel, '//span[@data-testid="price-and-discounted-price"]')
        except Exception as e:
            logging.error(f"Error al obtener el precio: {str(e)}")
            hotel_dict['price'] = "ver precio"

        try:
            hotel_dict['score'] = get_element_text_with_retry(
                hotel, '//div[@data-testid="review-score"]/div[1]')
        except Exception as e:
            logging.error(f"Error al obtener la puntuación: {str(e)}")
            hotel_dict['score'] = "ver..."

        try:
            hotel_dict['avg_review'] = get_element_text_with_retry(
                hotel, '//div[@data-testid="review-score"]/div[2]/div[1]')
        except Exception as e:
            logging.error(f"Error al obtener la revisión promedio: {str(e)}")
            hotel_dict['avg_review'] = ""

        try:
            hotel_dict['reviews_count'] = get_element_text_with_retry(
                hotel, '//div[@data-testid="review-score"]/div[2]/div[2]').split()[0]
        except Exception as e:
            logging.error(
                f"Error al obtener la cantidad de revisiones: {str(e)}")
            hotel_dict['reviews_count'] = "ver..."

        image = hotel.locator(
            '//a[@data-testid="property-card-desktop-single-image"]/img').get_attribute("src")
        if image:
            image = image.replace("square200", "max1024x768")
        hotel_dict['image_links'] = image if image else None

        hotel_link_element = hotel.locator(
            '//a[@data-testid="availability-cta-btn"]')
        if hotel_link_element:
            hotel_link = hotel_link_element.get_attribute("href")
            if hotel_link:
                hotel_link = f"{hotel_link.split('.html')[0]}.html?aid=2410095"
                hotel_dict['hotel_url'] = hotel_link

        popular_facilities = scrape_popular_facilities_with_retry(hotel_link)
        hotel_dict['popular_facilities'] = ', '.join(set(popular_facilities))

        hotel_dict['city'] = city
        hotel_dict['country'] = country

        hotels_list.append(hotel_dict)

    return hotels_list

# Función para leer las líneas procesadas


def read_processed_lines():
    try:
        with open('processed_lines.txt', 'r', encoding='utf-8') as processed_file:
            processed_lines = processed_file.read().splitlines()
        return set(processed_lines)
    except FileNotFoundError:
        return set()

# Función para escribir una línea procesada


def write_processed_line(line):
    with open('processed_lines.txt', 'a', encoding='utf-8') as processed_file:
        processed_file.write(line + '\n')

# Función principal del script


def main():
    language = 'es'

    with open('city.txt', 'r', encoding='utf-8') as file:
        city_lines = file.readlines()
    processed_lines = read_processed_lines()
    logging.info("Líneas procesadas cargadas: %s", processed_lines)
    
    today = datetime.now()
    checkin_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
    checkout_date = (today + timedelta(days=11)).strftime('%Y-%m-%d')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"

        for city_line in city_lines:
            city_country = city_line.strip().split(', ')
            if len(city_country) == 2:
                city, country = city_country
            else:
                logging.error(f"Formato incorrecto en la línea: '{city_line}'. Debe ser 'city, country'. Saltando esta línea.")
                continue
            
            if city_line.strip() in processed_lines:
                logging.info(f"Línea ya procesada: '{city_line}'. Saltando esta línea.")
                continue

            try:
                base_url = f'https://www.booking.com/searchresults.{language}.html?&checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city},{country}&ssne={city},{country}&ssne_untouched={city},{country}&lang={language}&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'

                page = browser.new_page(user_agent=ua)

                hotels_list = scrape_all_pages(page, base_url, city, country)
                logging.info(f'Total de hoteles para {city}, {country}: {len(hotels_list)}')

                write_processed_line(city_line.strip())

                for hotel in hotels_list:
                    hotel['description'] = scrape_hotel_description_with_retry(hotel['hotel_url'])

                df = pd.DataFrame(hotels_list)
                df.to_csv(f'data/{city}-{country}.csv', index=False)

            except TimeoutError as e:
                logging.error("Error de tiempo de espera: %s", e)
                logging.error("Continuando con la siguiente ciudad...")
                write_processed_line(city_line.strip())  # Agregar la línea al archivo de procesados si hay un error de timeout
            except Exception as e:
                logging.error("Error inesperado: %s", e)
                write_processed_line(city_line.strip())  # Agregar la línea al archivo de procesados si hay otro tipo de error


# Función para procesar todas las páginas de resultados de búsqueda


def scrape_all_pages(page, base_url, city, country):
    hotels_list = []

    for page_number in range(1, 10):
        page_url = f'{base_url}&offset={25 * (page_number - 1)}'
        logging.info(f'Visitando la página: {page_url}')
        page.goto(page_url, timeout=5000)

        hotels_list.extend(scrape_hotels_on_page(page, city, country))
        logging.info(
            f'Página {page_number} procesada. Total de hoteles hasta ahora: {len(hotels_list)}')

    return hotels_list


if __name__ == '__main__':
    main()
