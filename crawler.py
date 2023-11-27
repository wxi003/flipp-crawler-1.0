
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import json

class Product:
    def __init__(self, name, price, image):
        self.name = name
        self.price = price
        self.image = image

class WebScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])  # developer mode
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service,options=self.options)
        self.url = 'https://flipp.com'
        self.api_key = '87EC23E8E747F2A23B0D702B35920F01'
        self.storeLinkList = []
        self.productLinkList = []
        self.productList = []
        self.protocol = self.url.split('/')[0]
        self.domain = self.url.split('/')[2]


    def get_postal_code(self):
        try:
            response = requests.get('https://geoip.mxtrans.net/json')
            ip = json.loads(response.text)['ip']
            response = requests.get(f'https://api.ip2location.io/?key={self.api_key}&ip={ip}')
            postal_code = json.loads(response.text)['zip_code'].replace(' ', '')
            return postal_code
        except Exception as e:
            print(f"Error getting postal code: {e}")
            return None

    # function to scroll to an element and wait for the <a> element to be loaded
    def scroll_to_element_and_wait(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'a'))
        )
        # add a short delay to ensure all content is loaded
        time.sleep(2)

    def scrape_products(self, category):
        postal_code = self.get_postal_code()
        if not postal_code:
            return []

        category_url = f'{self.url}/flyers?postal_code={postal_code}'
        self.driver.get(category_url)
        self.driver.implicitly_wait(10)

        try:
            category_element = self.driver.find_element(By.XPATH, f'//span[contains(text(), "{category}")]')
            category_link = category_element.find_element(By.XPATH, '..').get_attribute('href')
            self.driver.get(f'{self.url}{category_link}')
            self.driver.implicitly_wait(10)

            products = self.extract_product_info()

            return products
        except Exception as e:
            print(f"Error scraping products: {e}")
            return []

    def extract_product_info(self):

        store_sections = self.driver.find_elements(By.TAG_NAME, 'flipp-flyer-listing-item')

        for store in store_sections:
            self.scroll_to_element_and_wait(store)
            storeLink = store.find_element(By.TAG_NAME, 'a').get_attribute('href')
            storeLink = self.url + storeLink
            print(storeLink)
            self.storeLinkList.append(storeLink)

        for eachStore in self.storeLinkList:
            self.driver.get(eachStore)
            self.driver.implicitly_wait(10)
            storeName = self.driver.find_element(By.XPATH, '//h1/span').text

            print(storeName)
            print('-------------------')

            # select canvas tag from page
            canvas = self.driver.find_element(By.XPATH, '//canvas')

            # get links from canvas tag
            productLinks = canvas.find_elements(By.TAG_NAME, 'a')

            for link in productLinks:
                productName = link.get_attribute('aria-label')
                productLink = link.get_attribute('href')
                if productName is None or productName.lower() == storeName.lower() or productName.lower() == storeName.strip().lower() or "view more" in productName.lower():
                    continue
                if productLink is not None:
                    productLink = self.protocol + '//' + self.domain + productLink
                    self.productLinkList.append(productLink)

            for product in self.productLinkList:
                productPrice = ''
                self.driver.get(product)
                self.driver.implicitly_wait(10)
                productName = self.driver.find_element(By.XPATH, '//h2/span').text
                priceElement = self.driver.find_elements(By.XPATH, '//flipp-price/span')
                productPrice = priceElement[0].text + '.' + priceElement[1].text
                imageElement = self.driver.find_element(By.XPATH, '//div[contains(@class, "item-info-image")]')
                productImage = imageElement.find_element(By.TAG_NAME, 'img').get_attribute('src')
                productObj = Product(productName, productPrice, productImage)
                self.productList.append(productObj)
                print("[" + productName + "]" + " $" + productPrice + " (" + productImage + ")")


    def close(self):
        self.driver.quit()

def main():
    scraper = WebScraper()

    products = scraper.scrape_products("Groceries")
    for product in products:
        print(product.name, product.price, product.image)
    scraper.close()

if __name__ == "__main__":
    main()
