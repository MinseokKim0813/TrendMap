import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from yahooquery import search
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta

# NYT API key
nyt_api_key = 'IvO8usKBicu4cnuNlKTF3069zi6aKoSp'

# Function to scrape the first 10 company names from the website
def scrape_companies():
    url = 'https://companiesmarketcap.com/usa/most-profitable-american-companies/'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        companies = soup.find_all('div', class_='company-name', limit=10)
        
        company_names = []
        print("Top 10 companies by earnings:")
        for idx, company in enumerate(companies, start=1):
            company_name = company.text.strip()
            company_names.append(company_name)
            print(f"{idx}. {company_name}")
        
        return company_names
    else:
        print("Failed to retrieve the website. Status code:", response.status_code)
        return []

# Function to fetch articles from the NYT API with pagination
def fetch_nyt_articles(query, days, max_pages=5):
    base_url = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    all_headlines = []
    print(f"Searching in New York Times articles for {query}...")
    for page in range(max_pages):
        params = {
            'q': query,
            'begin_date': start_date_str,
            'end_date': end_date_str,
            'page': page,
            'api-key': nyt_api_key
        }
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            articles = data['response']['docs']
            headlines = [article['headline']['main'] for article in articles]
            all_headlines.extend(headlines)
            if len(articles) < 10:
                break
        else:
            print(f"Error fetching data for {query} from NYT API:", response.status_code)
            break
        time.sleep(12)
    
    return all_headlines

# Function to count company mentions in the headlines
def count_company_mentions(company_names, days):
    mention_counts = {}
    for company in company_names:
        headlines = fetch_nyt_articles(company, days)
        time.sleep(12)
        mention_count = len(headlines)
        mention_counts[company] = mention_count
    return mention_counts

# Function to search EDGAR database using a ticker symbol
def search_edgar_with_ticker(ticker_symbol):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get('https://www.sec.gov/edgar/searchedgar/legacy/companysearch.html')
    time.sleep(2)

    cik_field = driver.find_element(By.ID, 'cik')
    cik_field.send_keys(ticker_symbol)
    submit_button = driver.find_element(By.NAME, 'Find')
    submit_button.click()
    time.sleep(2)
    
    ident_info = driver.find_element(By.CLASS_NAME, 'identInfo').text
    industry = ident_info.split('SIC:')[1].split(' - ')[1].split('\n')[0]
    state = ident_info.split('State location: ')[1].split(' | ')[0]

    driver.quit()

    return industry, state

# Function to search for ticker symbol from company name
def get_ticker_symbol(company_name):
    cleaned_name = re.sub(r'\(.*?\)', '', company_name).strip()
    search_result = search(cleaned_name)
    if search_result['quotes']:
        return search_result['quotes'][0]['symbol']
    return "Ticker not found"

# Main function to run the entire process and generate a dataset
def main():
    company_names = scrape_companies()
    days = 7
    mention_counts = count_company_mentions(company_names, days)

    data = []
    industry_counts = {}
    state_counts = {}

    for company, count in mention_counts.items():
        if count > 0:
            ticker_symbol = get_ticker_symbol(company)
            if ticker_symbol != "Ticker not found":
                industry, state = search_edgar_with_ticker(ticker_symbol)
                data.append([company, ticker_symbol, industry, state, count])

                industry_counts[industry] = industry_counts.get(industry, 0) + count
                state_counts[state] = state_counts.get(state, 0) + count

    # Convert data to a pandas DataFrame
    df = pd.DataFrame(data, columns=['Company', 'Ticker Symbol', 'Industry', 'State', 'Mention Count'])
    print("\nCompany Data:")
    print(df)

    # Append industry and state mention counts
    industry_df = pd.DataFrame(list(industry_counts.items()), columns=['Industry', 'Total Mentions'])
    state_df = pd.DataFrame(list(state_counts.items()), columns=['State', 'Total Mentions'])

    print("\nIndustry Mention Counts:")
    print(industry_df)

    print("\nState Mention Counts:")
    print(state_df)

    # Optionally save to a file or display in any other way
    # df.to_csv('company_data.csv', index=False)

# Run the program
if __name__ == "__main__":
    main()
