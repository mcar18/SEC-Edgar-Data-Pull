import os
import requests
import pandas as pd
from datetime import datetime
#test
# Function to get CIK from SEC API based on ticker
def get_cik_from_api(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Print the entire data to debug
        print(f"Full response from SEC API for {ticker}: {data}")
        
        cik = data.get(ticker)
        if cik:
            return cik
    return None

# Function to fetch 10-K or 10-Q filing from the SEC EDGAR API for a given CIK
def fetch_filings_from_api(cik, filing_type="10-K", count=5):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        filings = []
        for filing in data['filings']['recent']:
            if filing['form'] == filing_type:
                filings.append(filing)
            if len(filings) >= count:
                break
        return filings
    else:
        print(f"Error fetching filings for CIK {cik}")
        return []

# Function to process and extract relevant data from filings
def process_filings(filings):
    data = []
    for filing in filings:
        filing_data = {
            'CIK': filing['cik'],
            'Date Filed': filing['filingDate'],
            'Form Type': filing['form'],
            'URL': filing['url']
        }
        data.append(filing_data)
    
    # Convert to DataFrame for easy manipulation
    return pd.DataFrame(data)

# Main function to process tickers and collect filings
def main():
    tickers = ["MSFT", "PLTR"]  # List of tickers to process
    all_data = []
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        
        # Fetch the CIK using SEC API
        cik = get_cik_from_api(ticker)
        
        if cik:
            print(f"CIK found for {ticker}: {cik}")
            
            # Fetch 10-K filings for the given CIK
            filings = fetch_filings_from_api(cik, filing_type="10-K")
            if filings:
                print(f"Found {len(filings)} 10-K filings for {ticker}.")
                ticker_data = process_filings(filings)
                all_data.append(ticker_data)
            else:
                print(f"No 10-K filings found for {ticker}.")
        else:
            print(f"CIK not found for {ticker}, skipping.")
    
    if all_data:
        # Concatenate all data into a single DataFrame
        final_data = pd.concat(all_data, ignore_index=True)
        print(f"All data columns before processing growth rates: {final_data.columns}")
        
        # Optionally, process growth rates or further analysis here
        print("Processed data:")
        print(final_data.head())
    else:
        print("No data collected, exiting.")

if __name__ == "__main__":
    main()