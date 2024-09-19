import os
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
import time


def get_random_chrome_user_agent():
    user_agent = UserAgent(browsers='chrome', os='windows', platforms='pc')
    return user_agent.random


def create_driver(user_id=1):
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_directory = os.path.join(script_dir, 'users')
    user_directory = os.path.join(base_directory, f'user_{user_id}')

    options.add_argument(f'user-data-dir={user_directory}')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options)
    ua = get_random_chrome_user_agent()
    stealth(driver=driver,
            user_agent=ua,
            languages=["ru-RU", "ru"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            run_on_insecure_origins=True
            )

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver


def search_and_get_product_info(driver, product_name, url, keys):
    # Переход на сайт Wildberries
    driver.get(f'{url}')
    time.sleep(5)
    # Находим самый дешевый товар
    products = driver.find_elements(By.CLASS_NAME, keys[0])
    if products:
        cheapest_price = products[0].find_element(By.CLASS_NAME, keys[1]).text

        return {
            'title': product_name,
            'price': cheapest_price,
        }
    else:
        return None


def main_login(data, user_id=1):
    url = data[0]
    print(url, '\n')
    driver = create_driver(user_id)
    index_e = url[::-1].index('=')
    product_info = search_and_get_product_info(driver, url[-index_e:], url, data[1])
    if product_info:
        print(product_info)
    else:
        print("Товар не найден.")
    driver.quit()



if __name__ == '__main__':
    product_list = ['копье', 'дуршлаг', 'красные носки', 'леска для спиннинга']
    links = ['https://www.wildberries.ru/catalog/0/search.aspx?page=1&sort=priceup&search=',
             'https://www.ozon.ru/search/?from_global=true&sorting=price&text=',
             'https://market.yandex.ru/search?how=aprice&text=']
    class_name = [['product-card-list',  'product-card__price'], ['j3y_23', 'c3015-a0'], ['_6MQNc', 'WptiC']]

    for i in range(len(links)):
        for product in product_list:
            main_login((f"{links[i]}{product}", class_name[i]))
