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

# NYT yek ipa -> reversed for security so people can't search for it
nyt = 'IvO8usKBicu4cnuNlKTF3069zi6aKoSp'

# Function to scrape the first 10 company names from the website
def scrape_companies():
    url = 'https://companiesmarketcap.com/usa/most-profitable-american-companies/'
    response = requests.get(url)

    # Error Handling: Check if the request was successful
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
        # Error Handling: If request fails, print an error message
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
            'api-key': nyt
        }
        response = requests.get(base_url, params=params)
        
        # Error Handling: Check if the API request was successful
        if response.status_code == 200:
            data = response.json()
            articles = data['response']['docs']
            headlines = [article['headline']['main'] for article in articles]
            all_headlines.extend(headlines)

            # Stop pagination if fewer than 10 articles are retrieved
            if len(articles) < 10:
                break
        else:
            # Error Handling: If API request fails, print an error message
            print(f"Error fetching data for {query} from NYT API:", response.status_code)
            break
        
        # NYT API Rate Limiting: 500 requests per day and 5 requests per minute
        # See: https://developer.nytimes.com/faq#a11
        time.sleep(12)  # Wait for 12 seconds between requests to respect rate limiting

    return all_headlines

# Function to count company mentions in the headlines
def count_company_mentions(company_names, days):
    mention_counts = {}
    for company in company_names:
        headlines = fetch_nyt_articles(company, days)
        # NYT API Rate Limiting: Ensure the program waits to stay within the rate limit
        time.sleep(12)
        mention_count = len(headlines)
        mention_counts[company] = mention_count
    return mention_counts

# Function to search EDGAR database using a ticker symbol
def search_edgar_with_ticker(ticker_symbol):
    # Set up the WebDriver for Selenium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get('https://www.sec.gov/edgar/searchedgar/legacy/companysearch.html')
    time.sleep(2)  # Wait for the page to load

    cik_field = driver.find_element(By.ID, 'cik')
    cik_field.send_keys(ticker_symbol)
    submit_button = driver.find_element(By.NAME, 'Find')
    submit_button.click()
    time.sleep(2)  # Wait for results page to load
    
    # Extract company details (industry and state)
    ident_info = driver.find_element(By.CLASS_NAME, 'identInfo').text
    industry = ident_info.split('SIC:')[1].split(' - ')[1].split('\n')[0]
    state = ident_info.split('State location: ')[1].split(' | ')[0]

    driver.quit()  # Close the browser after extraction

    return industry, state

# Function to search for ticker symbol from company name
def get_ticker_symbol(company_name):
    # Remove brackets from company names
    cleaned_name = re.sub(r'\(.*?\)', '', company_name).strip()
    
    # Use YahooQuery to search for the ticker symbol
    search_result = search(cleaned_name)
    
    # Error Handling: Check if the ticker symbol was found
    if search_result['quotes']:
        return search_result['quotes'][0]['symbol']
    return "Ticker not found"

# Main function to run the entire process and generate a dataset
def main():
    company_names = scrape_companies()  # Scrape the top 10 companies
    days = 7  # Set the number of days for the NYT API search
    mention_counts = count_company_mentions(company_names, days)  # Get the mention counts

    data = []
    industry_counts = {}
    state_counts = {}

    # Process each company to extract ticker, industry, state, and mention count
    for company, count in mention_counts.items():
        if count > 0:
            ticker_symbol = get_ticker_symbol(company)
            if ticker_symbol != "Ticker not found":
                industry, state = search_edgar_with_ticker(ticker_symbol)
                data.append([company, ticker_symbol, industry, state, count])

                # Track the total mentions for each industry and state
                industry_counts[industry] = industry_counts.get(industry, 0) + count
                state_counts[state] = state_counts.get(state, 0) + count

    # Convert data to a pandas DataFrame
    df = pd.DataFrame(data, columns=['Company', 'Ticker Symbol', 'Industry', 'State', 'Mention Count'])
    print("\nCompany Data:")
    print(df)

    # Append industry and state mention counts
    industry_df = pd.DataFrame(list(industry_counts.items()), columns=['Industry', 'Total Mentions'])
    state_df = pd.DataFrame(list(state_counts.items()), columns=['State', 'Total Mentions'])

    # Merge the dataframes for industry and state mention counts
    df = pd.concat([df, pd.DataFrame(), industry_df, state_df], axis=0, ignore_index=True)

    print("\nIndustry Mention Counts:")
    print(industry_df)

    print("\nState Mention Counts:")
    print(state_df)

    # Save everything to a CSV file
    df.to_csv('company_data_with_mentions.csv', index=False)

# Run the program
if __name__ == "__main__":
    main()
