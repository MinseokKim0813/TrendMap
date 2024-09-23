import requests
from bs4 import BeautifulSoup

# Function to scrape the first 10 company names from the website
def scrape_companies():
    url = 'https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/'
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the company names (update this if necessary depending on the HTML structure)
        companies = soup.find_all('div', class_='company-name', limit=10)
        
        # Extract and print the first 10 company names
        for idx, company in enumerate(companies, start=1):
            company_name = company.text.strip()
            print(f"{idx}. {company_name}")
    else:
        print("Failed to retrieve the website. Status code:", response.status_code)

# Call the function to scrape and print company names
scrape_companies()
