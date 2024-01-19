from playwright.sync_api import sync_playwright
import pandas as pd

def scrape_hotels_on_page(page):
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
        hotel_dict['image_links'] = image if image else None

        # Get hotel URL
        hotel_link = hotel.locator('//a[@data-testid="availability-cta-btn"]').get_attribute("href")
        hotel_dict['hotel_url'] = hotel_link

        hotels_list.append(hotel_dict)
    return hotels_list

def main():
    with sync_playwright() as p:
        language = 'es'
        city = 'Montevideo'
        checkin_date = '2024-01-23'
        checkout_date = '2024-01-24'

        base_url = f'https://www.booking.com/searchresults.{language}.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD&ss={city}&ssne={city}&ssne_untouched={city}&lang={language}&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'

        browser = p.chromium.launch(headless=True)
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/69.0.3497.100 Safari/537.36"
        )
        page = browser.new_page(user_agent=ua)

        hotels_list = []  # Initialize outside the loop

        # Adjust the range to get more pages if needed
        for page_number in range(1, 2):  # Change 4 to the desired number of pages
            page_url = f'{base_url}&offset={25 * (page_number - 1)}'
            page.goto(page_url, timeout=60000)

            hotels_list.extend(scrape_hotels_on_page(page))

            print(f'Page {page_number}: There are {len(hotels_list)} hotels.')

        df = pd.DataFrame(hotels_list)
        df.to_excel('hotels_list.xlsx', index=False)
        df.to_csv('hotels_list.csv', index=False)

        browser.close()

if __name__ == '__main__':
    main()
