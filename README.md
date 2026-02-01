# API Web Scraping Dataset Project

## Project Overview

This project gathers real-time data from three main sources:

1. **New York Times API** - to collect article headlines mentioning specific companies.
2. **Static Web Scraping** - to extract the top N most profitable American companies from [companiesmarketcap.com](https://companiesmarketcap.com/usa/most-profitable-american-companies/) (N is chosen by you when you run the program).
3. **Dynamic Web Scraping** - to gather additional company details such as industry and state from SEC EDGAR Search Webpage.

The data collected includes the names of the top companies, the number of media mentions they receive in New York Times articles over a user-defined period (e.g., 7 days), as well as industry and state information from SEC EDGAR.

From this data, the trend in media mentions for industries and states can be analyzed.

## Why This Website Was Chosen

Initially, I considered using the **Fortune 500 2024 data** for this project. However, I realized that this static dataset would become outdated quickly, requiring frequent updates to stay relevant. Instead, I chose to use real-time data from [companiesmarketcap.com](https://companiesmarketcap.com/usa/most-profitable-american-companies/), which provides constantly updated information on the most profitable American companies.

## Value of the Dataset

This dataset provides real-time insights into which companies, industries, and states are receiving the most media attention based on mentions in the New York Times.

## Key Benefits

- **Investor Insights**: Investors can use this dataset to analyze which companies are being discussed the most in financial media. This could be an indicator of market trends or public interest in these companies.
- **Geographical and Sectoral Trends**: The dataset tracks media mentions alongside industry and state data, allowing users to identify which geographical regions or sectors are gaining the most media attention.
- **Up-to-Date Information**: The dataset pulls from real-time sources, meaning users always have access to the most current information, unlike static datasets like Fortune 500.

## Why This Dataset Isn’t Freely Available

While some financial datasets are available, combining real-time profitability data with media mentions and additional details such as industry and state makes this dataset unique. Most similar datasets are behind paywalls or require subscriptions, especially those that provide up-to-date and integrated information. The challenge of gathering data from multiple sources, such as APIs and web scraping, further adds to why this dataset isn’t freely available.

## How to Run This Project

### Prerequisites

Ensure that you have the following installed:

- Python 3.x
- pip (Python package manager)

### Environment variables

The app reads configuration from a `.env` file. Use the sample file as a template:

**Expected `.env` format:**

| Variable  | Required | Description                                                                                                                                           |
| --------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nyt`     | Yes      | New York Times API key. Get one at [developer.nytimes.com](https://developer.nytimes.com/get-started).                                                |
| `agentID` | Yes      | Contact for SEC API (e.g. your email). SEC requires this in the User-Agent or requests may be blocked. Format: `your-email@domain.com` or `YourName`. |

**Example `.env` (use your own values):**

```env
nyt=your-nyt-api-key-here
agentID=your-email@example.com
```

### Steps to Run

1. Clone the repository.
2. Install the required packages: `pip install -r requirements.txt`.
3. Create your `.env` from `.env.example` and add your NYT API key and contact (see above).
4. Run: `python main.py`.

When you run the program, it will:

- **Explain** what it does (fetch top companies, search NYT articles, look up SEC data, save to CSV).
- **Prompt you for two values:**
  - **Days to search** – How many days back to search for NYT articles (e.g. `7` for the past week).
  - **Number of top companies** – How many of the most profitable US companies to include (e.g. `10`).

It will then scrape that many companies, collect article headlines from the New York Times over that period, and retrieve industry and state information from SEC EDGAR. Higher values for days or companies take longer to run.

### Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```
