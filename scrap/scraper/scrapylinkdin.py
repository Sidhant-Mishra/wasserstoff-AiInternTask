import requests
import re
import time
import pandas as pd
from bs4 import BeautifulSoup


class TechCompanyScraper:
    def __init__(self, api_key, search_query, num_pages=5, min_companies=100):
        self.api_key = api_key
        self.search_query = search_query
        self.num_pages = num_pages
        self.min_companies = min_companies
        self.google_search_url = "https://api.scrapingdog.com/google"
        
    def load_existing_data(self, csv_file=None):
        """Load existing company data to avoid duplicates"""
        if not csv_file or not os.path.exists(csv_file):
            return set()
            
        existing_data = set()
        try:
            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header row
                for row in reader:
                    if len(row) > 1:
                        existing_data.add(row[1])  # Store websites to avoid duplicates
            print(f"Loaded {len(existing_data)} existing records.")
        except Exception as e:
            print(f"Error loading existing data: {str(e)}")
            
        return existing_data
    
    def get_google_search_results(self):
        """Fetches search results from Google using the ScrapingDog API"""
        companies = []
        attempts = 0
        max_attempts = 3  # Maximum number of batches to try

        while len(companies) < self.min_companies and attempts < max_attempts:
            attempts += 1
            print(f"Fetching batch {attempts} of search results...")
            
            for page in range(1, self.num_pages + 1):
                params = {
                    "api_key": self.api_key,
                    "query": self.search_query,
                    "country": "IN",
                    "page": page
                }
                
                try:
                    response = requests.get(self.google_search_url, params=params)
                    if response.status_code == 200:
                        results = response.json().get("organic_results", [])
                        for result in results:
                            if result.get("title") and result.get("link"):
                                companies.append({
                                    "name": result["title"],
                                    "website": result["link"]
                                })
                    else:
                        print(f"Failed to get page {page}: Status code {response.status_code}")
                except Exception as e:
                    print(f"Error fetching page {page}: {str(e)}")
                    
                # Delay to avoid hitting API limits
                time.sleep(2)
                
            print(f"Found {len(companies)} companies so far.")
            
            # If we still don't have enough companies, adjust the search query slightly
            if len(companies) < self.min_companies:
                original_terms = self.search_query.split()
                if "OR" in original_terms:
                    idx = original_terms.index("OR")
                    if idx > 0 and idx < len(original_terms) - 1:
                        # Swap the terms around the OR to get different results
                        original_terms[idx-1], original_terms[idx+1] = original_terms[idx+1], original_terms[idx-1]
                        self.search_query = " ".join(original_terms)
        
        return companies
    
    def scrape_contact_info(self, website_url):
        """Extracts contact information from a website"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(website_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return "N/A", "N/A"
            
            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text(" ", strip=True)
            
            # Extract email
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            email_matches = email_pattern.findall(page_text)
            
            # Filter out common false positives
            filtered_emails = [email for email in email_matches if not (
                "example" in email or 
                "your" in email or 
                "domain" in email or 
                "@example" in email or 
                "@sample" in email
            )]
            
            email = filtered_emails[0] if filtered_emails else "N/A"
            
            # Extract phone number (Indian format)
            phone_pattern = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}")
            phone_matches = phone_pattern.findall(page_text)
            phone = phone_matches[0] if phone_matches else "N/A"
            
            # Check contact page if no email found
            if email == "N/A":
                contact_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    text = link.text.lower()
                    if href and ('contact' in href.lower() or 'contact' in text):
                        if href.startswith('/'):
                            href = website_url.rstrip('/') + href
                        elif not href.startswith(('http://', 'https://')):
                            href = website_url.rstrip('/') + '/' + href.lstrip('/')
                        contact_links.append(href)
                
                # Try to scrape email from contact page
                for contact_url in contact_links[:1]:  # Limit to first contact page
                    try:
                        contact_response = requests.get(contact_url, headers=headers, timeout=10)
                        if contact_response.status_code == 200:
                            contact_soup = BeautifulSoup(contact_response.text, "html.parser")
                            contact_text = contact_soup.get_text(" ", strip=True)
                            contact_emails = email_pattern.findall(contact_text)
                            filtered_contact_emails = [email for email in contact_emails if not (
                                "example" in email or 
                                "your" in email or 
                                "domain" in email or 
                                "@example" in email or 
                                "@sample" in email
                            )]
                            if filtered_contact_emails:
                                email = filtered_contact_emails[0]
                    except:
                        continue
            
            return email, phone
        except Exception as e:
            print(f"Error scraping {website_url}: {str(e)}")
            return "N/A", "N/A"
    
    def run_scraping(self, existing_csv=None):
        """Main function to run the complete scraping process"""
        # Load existing data to avoid duplicates
        existing_data = self.load_existing_data(existing_csv) if existing_csv else set()
        
        # Get list of companies from search results
        companies = self.get_google_search_results()
        print(f"Found {len(companies)} total companies. Starting contact extraction...")
        
        # Scrape contact information for each company
        results = []
        for i, company in enumerate(companies):
            if company["website"] in existing_data:
                print(f"Skipping duplicate: {company['name']}")
                continue
                
            print(f"Processing {i+1}/{len(companies)}: {company['name']}")
            email, phone = self.scrape_contact_info(company["website"])
            
            # Only include companies where we found contact information
            if email != "N/A" or phone != "N/A":
                results.append({
                    "Company Name": company["name"],
                    "Website": company["website"],
                    "Contact Email": email,
                    "Phone Number": phone
                })
                print(f"Added {company['name']} with email: {email}, phone: {phone}")
            else:
                print(f"No contact info found for {company['name']}")
                
            # Small delay between requests
            time.sleep(1)
        
        print(f"Completed processing with {len(results)} companies with contact info")
        # Create DataFrame from results
        return pd.DataFrame(results)