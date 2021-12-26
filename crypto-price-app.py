import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image
import base64
from bs4 import BeautifulSoup
import requests
import json
import time

st.set_page_config(layout = "wide")
image = Image.open('Images/crypto-price-app-logo.jpg')
st.image(image, width = 500)

st.title("CryptoCurrency Price App")
st.markdown("""
This APP retrives cryptocurrency prices for the top 100 cryptocurrencies of the world
""")

#  About section
expander_bar = st.expander("About")
expander_bar.markdown("""
* **Python libraries:** base64, pandas, streamlit
* **Data Source:** [CoinMarketCap](https://www.CoinMarketCap.com). 
* **Credit:** Web scraper adapted fromthe Medium Article [Web Scraping Crypto-Prices With Python](https://twitter.com/tdatascience/status/1278395559288672256?lang=en) written by [Bryan Freg](https://www.linkedin.com/in/bryanfeng)
""")

# Dividing Page into 3 columns (col1 = sidebar, col2 and col3 = page content)
col1 = st.sidebar
col2, col3 = st.columns((2, 1))

# sidebar + main panel
col1.header("Input Options")

# Sidebar - Currency price unit
currency_price_unit = st.sidebar.selectbox('Select currency for price', ('USD', 'BTC', 'ETH'))

# Web scraping of CoinMarketCap data

@st.cache
def load_data():
	cmc = requests.get('https://coinmarketcap.com/all/views/all/')
	soup = BeautifulSoup(cmc.content, 'html.parser')
	print(soup.prettify())
	data = soup.find('script', id = '__NEXT_DATA__', type = "application/json")
	coins = {}

	# using data.contents[0] to remove script tags
	coin_data = json.loads(data.contents[0])
	listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']

	for i in listings:
		coins[str(i['id'])] = i['name']

	coin_name = []
	coin_symbol = []
	market_cap = []
	percent_change_1h = []
	percent_change_24h = []
	percent_change_7d = []
	price =[]
	volume_24h = []

	for i in listings:
		coin_name.append(i['slug'])
		coin_symbol.append(i['symbol'])
		price.append(i['quote'][currency_price_unit]['price'])
		percent_change_1h.append(i['quote'][currency_price_unit]['percentChange1h'])
		percent_change_24h.append(i['quote'][currency_price_unit]['percentChange24h'])
		percent_change_7d.append(i['quote'][currency_price_unit]['percentChange7d'])
		market_cap.append(i['quote'][currency_price_unit]['marketCap'])
		volume_24h.append(i['quote'][currency_price_unit]['volume24h'])

	df = pd.DataFrame(columns = ['coin_name', 'coin_symbol', 'market_cap', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d', 'price', 'volume_24h'])
	df['coin_name'] = coin_name
	df['coin_symbol'] = coin_symbol
	df['market_cap'] = market_cap
	df['percent_change_1h'] = percent_change_1h
	df['percent_change_24h'] = percent_change_24h
	df['percent_change_7d'] = percent_change_7d
	df['price'] = price
	df['volume_24h'] = volume_24h

	return df

df = load_data()

## sidebar- cryptocurrency selection
sorted_coins = df['coin_symbol']
selected_coins = col1.multiselect('CryptoCurrency', sorted_coins, sorted_coins)

## Data Filtering
df_selected_coins = df[df['coin_symbol'].isin(selected_coins)]

# Sidebar - Nunber of Coins to Display
num_coins = col1.slider('Display Top N Coins', 1, 100, 100)
df_num_coins = df_selected_coins[:num_coins]

## Sidebar - Percent change timeframe
percent_timeframe = col1.selectbox('Percent change time frame', ['7d', '24h', '1h'])
percent_dict = {'7d': 'percent_change_7d', '24h': 'percent_change_24h', '1h': 'percent_change_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]
# st.write(selected_percent_timeframe)

## Sidebar - Sorting Values
sort_values = col1.selectbox('Sort Values?', ['Yes', 'No'])

# Display Content col2
col2.subheader('Price Data of selected CryptoCurrency')
col2.write(f'Data Dimensions {df_num_coins.shape[0]} rows and {df_num_coins.shape[1]} columns.')
col2.dataframe(df_num_coins)

## Download Dataframe CSV
def file_download(df):
	csv = df.to_csv(index = False)
	b64 = base64.b64encode(csv.encode()).decode()
	href = f'<a href = "data:file/csv;base64,{b64}" download = "crypto.csv">Download CSV File</a>'
	return href

col2.markdown(file_download(df_num_coins), unsafe_allow_html = True)


#---------------------------------#
# Preparing data for Bar plot of Percentage Price change
col2.subheader('Table of Percentage Price change')
df_change = pd.concat([df_num_coins.coin_symbol, df_num_coins.percent_change_7d, df_num_coins.percent_change_24h, df_num_coins.percent_change_1h], axis =1)
df_change = df_change.set_index('coin_symbol')
df_change["positive_percentage_change_1h"] = df_change['percent_change_1h'] > 0
df_change["positive_percentage_change_24h"] = df_change['percent_change_24h'] > 0
df_change["positive_percentage_change_7d"] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

# Conditional creation of Bar plot (time frame)
col3.subheader('Bar Plot for Percentage Price Change')

if percent_timeframe == '7d':
	if sort_values == 'Yes':
		df_change = df_change.sort_values(by = ['percent_change_7d'])
	col3.write("*7 Days Period*")
	plt.figure(figsize = (5, 25))
	plt.subplots_adjust(top = 1, bottom = 0)
	df_change['percent_change_7d'].plot(kind = "barh", color = df_change.positive_percentage_change_7d.map({True: 'g', False: 'r'}))
	col3.pyplot(plt)
elif percent_timeframe == "24h":
	if sort_values == "Yes":
		df_change = df_change.sort_values(by = ['percent_change_24h'])
	col3.write("*24 Hours Period*")
	plt.figure(figsize = (5, 25))
	plt.subplots_adjust( top = 1, bottom = 0)
	df_change['percent_change_24h'].plot(kind = "barh", color = df_change.positive_percentage_change_24h.map({True: 'g', False: 'r'}))
	col3.pyplot(plt)
else:
	if sort_values == "Yes":
		df_change = df_change.sort_values(by = ['percent_change_1h'])
	col3.write("1 Hour Period")
	plt.figure(figsize = (5, 25))
	plt.subplots_adjust(top = 1, bottom = 0)
	df_change['percent_change_1h'].plot(kind = 'barh', color = df_change.positive_percentage_change_1h.map({True: 'g', False: 'r'}))
	col3.pyplot(plt)
