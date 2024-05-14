import logging
import cloudscraper
import requests
from bs4 import BeautifulSoup

def get_currency_data():
    # 크롤링할 웹 페이지의 URL
    #url = 'https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=all'
    url = 'https://feed.bithumb.com/notice'

    scraper = cloudscraper.create_scraper()
    html = scraper.get(url).content

    #response = requests.get(url)
    #soup = BeautifulSoup(response.text, 'html.parser')

    soup = BeautifulSoup(html, 'html.parser')
    #usd_price_class = soup.find(attrs={"data-test": "instrument-price-last"})
    print(soup)

    #table = soup.select("text-5xl/9 font-bold md:text-[42px] md:leading-[60px] text-[#232526]")
    #print(f"TEST!!!\n {usd_price_class}")


    ##scraper.close()


