import re
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from yahooquery import search
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta


load_dotenv()
nyt = os.getenv('nyt')
agentID = os.getenv('agentID')

# SEC requires a User-Agent with company name and contact (see https://www.sec.gov/os/webmaster-faq#user-agent)
# Use format "CompanyName AdminContact@domain.com" or requests may be blocked with 403
SEC_HEADERS = {
    'User-Agent': 'TrendMap ' + agentID,
    'Accept-Encoding': 'gzip, deflate',
}


# Max NYT API pages per company (10 articles/page)
NYT_MAX_PAGES = 10
# NYT: 5 requests/minute. Use 15s between requests (~4/min) to stay under limit.
NYT_REQUEST_DELAY_SEC = 15
# Wait this long on 429 before retrying (let rate-limit window reset).
NYT_RATE_LIMIT_BACKOFF_SEC = 65
NYT_RATE_LIMIT_MAX_RETRIES = 2

# Function to prompt user for days and number of top companies
def get_user_input():
    while True:
        try:
            days_str = input("How many days back should we search for NYT articles? (e.g. 7): ").strip()
            days = int(days_str)
            if days < 1:
                print("Please enter a positive number of days.")
                continue
            break
        except ValueError:
            print("Please enter a valid whole number.")

    while True:
        try:
            limit_str = input("How many top companies (by earnings) should we include? (e.g. 10): ").strip()
            limit = int(limit_str)
            if limit < 1:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid whole number.")

    return days, limit

# Function to scrape company names from the website
def scrape_companies(limit):
    url = 'https://companiesmarketcap.com/usa/most-profitable-american-companies/'
    response = requests.get(url)

    # Error Handling: Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        companies = soup.find_all('div', class_='company-name', limit=limit)

        company_names = []
        print(f"\nTop {limit} companies by earnings:")
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
def fetch_nyt_articles(query, days, max_pages=None):
    if max_pages is None:
        max_pages = NYT_MAX_PAGES
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
        for retry in range(NYT_RATE_LIMIT_MAX_RETRIES + 1):
            response = requests.get(base_url, params=params)
            if response.status_code != 429:
                break
            if retry < NYT_RATE_LIMIT_MAX_RETRIES:
                print(f"Rate limited (429). Waiting {NYT_RATE_LIMIT_BACKOFF_SEC}s before retry...")
                time.sleep(NYT_RATE_LIMIT_BACKOFF_SEC)
            else:
                print(f"Rate limited (429) for {query}. Skipping remaining pages for this company.")
                return all_headlines

        # Error Handling: Check if the API request was successful
        if response.status_code == 200:
            data = response.json()
            response_obj = data.get('response')
            articles = response_obj.get('docs') if response_obj else None
            if articles is None:
                # NYT returns docs=null when past the 100-result limit (page 10+). That's normal.
                if response_obj and response_obj.get('metadata'):
                    break
                # Otherwise treat as API error (e.g. rate limit, bad key)
                fault = data.get('fault', {}) or (response_obj or {})
                msg = fault.get('faultstring') or fault.get('message') or response.text[:200]
                print(f"NYT API returned unexpected response for {query}: {msg}")
                break
            headlines = [article['headline']['main'] for article in articles]
            all_headlines.extend(headlines)

            # Stop when this page has fewer than 10 results (no more pages)
            if len(articles) < 10:
                break
        else:
            # Error Handling: If API request fails, print an error message
            print(f"Error fetching data for {query} from NYT API:", response.status_code)
            break

        # NYT: 5 requests/minute. Sleep so we stay under the limit.
        time.sleep(NYT_REQUEST_DELAY_SEC)

    return all_headlines

# Function to count company mentions in the headlines
def count_company_mentions(company_names, days):
    mention_counts = {}
    for company in company_names:
        headlines = fetch_nyt_articles(company, days)
        # NYT API Rate Limiting: wait between companies to stay under 5 requests/minute
        time.sleep(NYT_REQUEST_DELAY_SEC)
        mention_count = len(headlines)
        mention_counts[company] = mention_count
    return mention_counts

# Get CIK from ticker using SEC company_tickers.json
def get_cik_from_ticker(ticker_symbol):
    url = 'https://www.sec.gov/files/company_tickers.json'
    response = requests.get(url, headers=SEC_HEADERS)
    if response.status_code != 200:
        raise ValueError(
            f"SEC request failed (status {response.status_code}). "
            "SEC requires a User-Agent with company name and contact; see SEC_HEADERS in main.py."
        )
    data = response.json()
    # Normalize ticker for comparison (e.g. BRK-B vs BRK.B)
    ticker_upper = ticker_symbol.upper().replace('.', '-')
    for entry in data.values():
        if entry.get('ticker', '').upper().replace('.', '-') == ticker_upper:
            return entry.get('cik_str')
    return None


# Function to get company details (industry, state) from SEC EDGAR via API
def search_edgar_with_ticker(ticker_symbol):
    cik = get_cik_from_ticker(ticker_symbol)
    if cik is None:
        raise ValueError(f"CIK not found for ticker: {ticker_symbol}")
    cik_padded = str(cik).zfill(10)
    url = f'https://data.sec.gov/submissions/CIK{cik_padded}.json'
    response = requests.get(url, headers=SEC_HEADERS)
    if response.status_code != 200:
        raise ValueError(f"SEC API error for CIK {cik_padded}: {response.status_code}")
    data = response.json()
    industry = data.get('sicDescription') or data.get('sic', '')
    if isinstance(industry, int):
        industry = str(industry)
    state = data.get('stateOfIncorporation') or data.get('addresses', {}).get('business', {}).get('stateOrCountry') or ''
    return industry or 'N/A', state or 'N/A'

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
    days, limit = get_user_input()
    company_names = scrape_companies(limit)
    mention_counts = count_company_mentions(company_names, days)

    data = []
    industry_counts = {}
    state_counts = {}

    # Process each company to extract ticker, industry, state, and mention count
    for company, count in mention_counts.items():
        if count > 0:
            ticker_symbol = get_ticker_symbol(company)
            if ticker_symbol != "Ticker not found":
                try:
                    industry, state = search_edgar_with_ticker(ticker_symbol)
                    data.append([company, ticker_symbol, industry, state, count])
                    industry_counts[industry] = industry_counts.get(industry, 0) + count
                    state_counts[state] = state_counts.get(state, 0) + count
                except (ValueError, requests.RequestException) as e:
                    print(f"Skipping {company} ({ticker_symbol}): {e}")

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

    # Save everything to a  CSV file
    df.to_csv('company_data_with_mentions.csv', index=False)

# Run the program
if __name__ == "__main__":
    main()
