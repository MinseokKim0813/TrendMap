import requests
from datetime import datetime, timedelta

# Function to fetch articles from the NYT API
def fetch_nyt_articles(query, days):
    # Set up the NYT API key and base URL
    api_key = 'IvO8usKBicu4cnuNlKTF3069zi6aKoSp'  # Replace with your actual API key
    secret = 'tqcZSbkNv9P6tyqQ'
    base_url = 'https://api.nytimes.com/svc/search/v2/articlesearch.json'
    
    # Calculate the date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format the dates in 'YYYYMMDD' format for the API query
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    # Define the query parameters
    params = {
        'q': query,
        'begin_date': start_date_str,
        'end_date': end_date_str,
        'api-key': api_key
    }

    # Make the request to the NYT API
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        articles = data['response']['docs']
        headlines = [article['headline']['main'] for article in articles]
        return headlines
    else:
        print("Error fetching data from NYT API:", response.status_code)
        return []

# Example usage
query = "Apple"
days = 7
headlines = fetch_nyt_articles(query, days)

print(f"Headlines mentioning '{query}' in the last {days} days:")
for headline in headlines:
    print(headline)
