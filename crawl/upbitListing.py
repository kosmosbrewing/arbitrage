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

import pandas as pd

class TrailingStop:
    def __init__(self, trailing_stop_percent):
        self.trailing_stop_percent = trailing_stop_percent
        self.max_price = 0
        self.stop_price = 0
        self.position_open = False

    def update_price(self, current_price):
        if not self.position_open:
            # 포지션 오픈 시 초기화
            self.max_price = current_price
            self.stop_price = current_price * (1 - self.trailing_stop_percent)
            self.position_open = True
        else:
            # 새로운 최대 가격 업데이트
            if current_price > self.max_price:
                self.max_price = current_price
                self.stop_price = current_price * (1 - self.trailing_stop_percent)
            # 스탑 가격에 도달했는지 확인
            if current_price < self.stop_price:
                self.position_open = False
                return "Sell"
        return "Hold"


if __name__ == "__main__":
    # 샘플 데이터 (예: 하루 동안의 가격 데이터)
    price_data = [3.1, 2.7, 3.2, 3.3, 3.7, 3.8, 3.6, 3.5, 3.1, 3.2]

    # 트레일링 스탑 인스턴스 생성 (예: 5% 트레일링 스탑)
    trailing_stop = TrailingStop(trailing_stop_percent=0.05)

    # 가격 데이터를 순회하며 트레일링 스탑 업데이트
    for price in price_data:
        action = trailing_stop.update_price(price)
        print(f"Current Price: {price}, Action: {action}")
