# -*- coding:utf-8 -*-
import requests
import json
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# 気象庁データの取得
jma_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/260000.json"
jma_json = requests.get(jma_url).json()
def clean_data(data):#'[\n    "2024-11-27T00:00:00+09:00",\n    "2024-12-03T00:00:00+09:00"\n]'を綺麗にします
    data = data.split()
    data = data[1:len(data)-1]
    data = [d.strip('"') for d in data]
    return data
date = clean_data(json.dumps(jma_json[1]['timeSeries'][0]['timeDefines'], indent=4, ensure_ascii=False))
weather = clean_data(json.dumps(jma_json[1]['timeSeries'][0]['areas'][0]['weatherCodes'], indent=4, ensure_ascii=False))
tempMin = clean_data(json.dumps(jma_json[1]['timeSeries'][1]['areas'][0]['tempsMin'], indent=4, ensure_ascii=False))
tempMax = clean_data(json.dumps(jma_json[1]['timeSeries'][1]['areas'][0]['tempsMax'], indent=4, ensure_ascii=False))
date = [datetime.fromisoformat(d.strip('",')).date().strftime('%m/%d')  for d in date]
today = datetime.fromisoformat(json.dumps(jma_json[0]['reportDatetime'], indent=4, ensure_ascii=False).split()[0].strip('"')).date().strftime('%m/%d')
to_weather = json.dumps(jma_json[0]['timeSeries'][0]['areas'][0]['weathers'][0], indent=4, ensure_ascii=False).split()[0].strip('"')
to_temp = clean_data(json.dumps(jma_json[0]['timeSeries'][2]['areas'][0]['temps'][:2], indent=4, ensure_ascii=False))
to_temp = [d.strip('",') for d in to_temp]
wc = pd.read_csv('Weather code filename',header=None)
wc_dict = dict(zip(wc[0].astype(int),wc[1]))
wc = [today+' '+to_weather+' '+to_temp[0].strip('",')+'°c〜'+to_temp[1].strip('",')+'°c']
wc = wc + [d+' '+wc_dict[int(weather[i].strip('",'))]+' '+tempMin[i].strip('",')+'°c〜'+tempMax[i].strip('",')+'°c'  for i,d in enumerate(date) if i<3]

'''
jrw
'''

# WebDriver のパスを指定（適宜変更してください）
CHROMEDRIVER_PATH = ''  # ここにChromeDriverのパスを設定
# WebDriver の設定
service = Service(CHROMEDRIVER_PATH)
options = Options()
options.add_argument('--headless')  # ヘッドレスモード（ブラウザを表示しない）

driver = webdriver.Chrome(service=service,options=options)
def get_jrw_info():
    target_lines = [
    "欲しい路線名を入力"
    ]
    url = "https://trafficinfo.westjr.co.jp/kinki.html"
    driver.get(url)
    results = []
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "jisyo")))
    # 運行情報の抽出
    sections = driver.find_elements(By.CLASS_NAME, "jisyo")
    for section in sections:
        # 路線名を抽出
        line_element = section.find_element(By.CLASS_NAME, "jisyo_title").text
        # 京阪神エリアの対象か判定
        if any(line in line_element for line in target_lines):
            # 更新日時を抽出
            update_time = section.find_element(By.CLASS_NAME, "jisyo_date").text

            # 概要を抽出
            summary_element = section.find_element(By.CLASS_NAME, "gaiyo").text.replace("\n", "").strip()

            # 再開見込み情報を抽出
            try:
                restart_time = section.find_element(By.CLASS_NAME, "mikomi").text.strip()
            except:
                restart_time = "再開見込み情報なし"

            # 結果を保存
            
            results.append(line_element+summary_element+restart_time+update_time)

    return results

jrw_result = get_jrw_info()
if len(jrw_result)>4:
    jrw_result = jrw_result[:4]
elif len(jrw_result)==0:
    jrw_result.append('お知らせはありません')
while len(jrw_result)<4:
    jrw_result.append('')

'''
新幹線
'''
# WebDriver の設定
service = Service(CHROMEDRIVER_PATH)
options = Options()
options.add_argument('--headless')  # ヘッドレスモード（ブラウザを表示しない）
driver = webdriver.Chrome(service=service,options=options)
def get_tokaido_shinkansen_info():
    url = "https://traininfo.jr-central.co.jp/shinkansen/pc/ja/index.html"
    driver.get(url)
    results = []
    message_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "message"))
    )
    result = []
    try:
        result.append(message_element.text)
    except Exception as e:
        print(f"エラー: {e}")
    try:
        info_messages = driver.find_elements(By.CLASS_NAME, "info-message")
        print(info_messages)
        for i, message in enumerate(info_messages, start=1):
            if message.is_displayed():
                content = message.text.strip()
                result.append('[要確認]'+content)
            else:
                result.append('内容が空です')
    except NoSuchElementException:
        print("Info Message: 要素が存在しません")
    return result

# 東海道新幹線の情報取得
shin_result = get_tokaido_shinkansen_info()
print(shin_result)
shin_result = [ n for n in shin_result if n!='内容が空です']
if len(jrw_result)>4:
    jrw_result = jrw_result[:4]
elif len(jrw_result)==0:
    jrw_result.append('お知らせはありません')
while len(shin_result)<4:
    shin_result.append('')
driver.quit()

#  スコープと認証情報を設定
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('json file PATH', scope)
client = gspread.authorize(creds)
# スプレッドシートを開く
spreadsheet = client.open('spread sheet file name')
worksheet = spreadsheet.worksheet('sheet name')
data  =[wc,jrw_result,shin_result]

worksheet.update("B1:D9", data)