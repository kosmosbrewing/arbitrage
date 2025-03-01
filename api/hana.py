import logging
import traceback
from datetime import datetime
import requests
import pandas as pd

def get_currency_data(currency):
    # 크롤링할 웹 페이지의 URL
    url = 'https://www.kebhana.com/cms/rate/wpfxd651_07i_01.do'

    today_date = datetime.today().strftime('%Y%m%d')

    curCd = currency ## USD, JPY 등
    headers = {
        'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        'Origin': 'https://www.kebhana.com',
        'Host': 'www.kebhana.com',
        'Referer': 'https://www.kebhana.com/cms/rate/index.do?contentUrl=/cms/rate/wpfxd651_01i.do'}

    data = f'ajax=true&curCd={curCd}&inqStrDt={today_date}&pbldDvCd=3&requestTarget=searchContentDiv'
    try:
        response = requests.post(url=url, headers=headers, data=data)

        # 요청이 성공했는지 확인
        if response.status_code == 200:
            ## 2단계 pd.read_html를 통해서 특정 테이블을 df로 바로 가져오기
            df = pd.read_html(response.text)[0]

            df = df[['회차', '시간', '매매 기준율']]

            last_value = float(df.loc[0]['매매 기준율'].values[0])

            return last_value
        else:
            logging.info('페이지를 가져오는 데 문제가 발생했습니다. 상태 코드:', response.status_code)
        response.close()

    except Exception as e:
        logging.info(traceback.format_exc())
        return 0



