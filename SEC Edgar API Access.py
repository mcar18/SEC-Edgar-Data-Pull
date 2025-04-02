import requests
import spacy
from transformers import pipeline
import time
from bs4 import BeautifulSoup

# Global headers for SEC EDGAR requests (update with your valid contact information)
HEADERS = {
    "User-Agent": "Matt carlson (mattcarlson39@gmail.com)",  # Replace with your info
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": "https://www.sec.gov/"
}
#test
def get_filings(cik, form_types=["10-K", "10-Q"]):
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    with requests.Session() as session:
        session.headers.update(HEADERS)
        response = session.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve data for CIK {cik}. Status code: {response.status_code}")
        return None
    
    data = response.json()
    filings_data = data.get('filings', {}).get('recent', {})
    if not filings_data:
        print("No filings found.")
        return None
    
    filtered_filings = []
    for i, form in enumerate(filings_data.get('form', [])):
        if form in form_types:
            filing = {
                "form": form,
                "accessionNumber": filings_data.get('accessionNumber', [])[i],
                "filingDate": filings_data.get('filingDate', [])[i],
                "primaryDocument": filings_data.get('primaryDocument', [])[i]
            }
            filtered_filings.append(filing)
    return filtered_filings

def download_filing(url):
    try:
        with requests.Session() as session:
            session.headers.update(HEADERS)
            response = session.get(url)
        response.raise_for_status()  # Raises exception for 4xx/5xx responses
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading filing: {e}")
        return None

def clean_html(html_text):
    """
    Remove HTML tags and extract the text content.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def analyze_with_spacy(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

def chunk_text(text, chunk_size=500):
    """
    Split text into chunks of roughly `chunk_size` words.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def summarize_chunks(chunks, max_length=150, min_length=40):
    summarizer = pipeline("summarization")
    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"Error during summarization of a chunk: {e}")
    # Optionally, join the chunk summaries together and summarize further if needed
    return " ".join(summaries)

if __name__ == "__main__":
    # Example: Using Apple Inc. CIK "0000320193"
    cik = "0000320193"
    filings = get_filings(cik)
    
    if filings:
        print(f"Found {len(filings)} filings for CIK {cik}:")
        for filing in filings:
            print(f"Form: {filing['form']}, Filing Date: {filing['filingDate']}")
            accession_no = filing['accessionNumber'].replace('-', '')
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no}/{filing['primaryDocument']}"
            print(f"Downloading filing from: {filing_url}")
            filing_text = download_filing(filing_url)
            
            if filing_text:
                # Clean the HTML to extract meaningful text
                clean_text = clean_html(filing_text)
                
                print("\n=== Performing NLP Analysis using spaCy ===")
                entities = analyze_with_spacy(clean_text)
                print("Named Entities:")
                for ent_text, ent_label in entities:
                    print(f"{ent_text} ({ent_label})")
                
                print("\n=== Generating Summary with Transformers ===")
                # Chunk the clean text to meet the summarizer's token limit
                text_chunks = chunk_text(clean_text, chunk_size=500)
                summary = summarize_chunks(text_chunks)
                if summary:
                    print("Summary:")
                    print(summary)
                
                # Process only the first successful filing for demonstration
                break
            
            time.sleep(1)  # Rate limiting