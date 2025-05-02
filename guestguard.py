import json
import requests
import argparse
import csv
from collections import defaultdict
import time

# Load API key from file
with open("config.json") as f:
    config = json.load(f)

SSC_API_KEY = config.get("security_scorecard_api_key")
headers = {
        "accept": "application/json; charset=utf-8",
        "Authorization": "Token "+SSC_API_KEY
    }

# Function to get emails from csv file if provided - assumes that there is an 'email' columm
def get_guest_users_from_csv(file_path):
    with open(file_path, newline='') as f:
        return [row['email'] for row in csv.DictReader(f)]
    
# Function to split email domain from address
def get_domain(email):
    return email.split('@')[-1].lower()

# Function to convert email list to domain list including volumes that each domain appears
def get_domains_with_counts(emails):
    domain_counts = defaultdict(int)
    for email in emails:
        domain = get_domain(email)
        domain_counts[domain] += 1
    return domain_counts

# Function to create a portfolio - temporarily done to avoid a 403 error when looking up company data
def create_portfolio(portfolio_name):
    url = "https://api.securityscorecard.io/portfolios"

    payload = {
        "name": portfolio_name,
        "description": "Temporary ortfolio for guest users' domains"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Portfolio '{portfolio_name}' created successfully.")
        return response.json()  # Return the portfolio info including its ID
    else:
        print(f"Failed to create portfolio: {response.text}")
        return None

# Function to add collected domains to temporary portfolio - temporarily done to avoid a 403 error when looking up company data
def add_domains_to_portfolio(portfolio_id, domains):
    url = "https://api.securityscorecard.io/portfolios/companies/bulk-upload"
    payload = {
        "portfolios": [portfolio_id],
        "companies": list(domains.keys())
    }
    response = requests.put(url, json=payload, headers=headers)

    if response.status_code != 400:
        print("Domains added to portfolio")
        return response.json()
    else:
        print(f"Failed to create portfolio: {response.text}")
        return None

# Function to clear up temporary portfolio
def delete_portfolio(portfolio_id):
    url = "https://api.securityscorecard.io/portfolios/"+portfolio_id
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return True

# Function to add collected domains to temporary portfolio
def json_object_to_csv(json_data, domain_counts, csv_file):
    if not json_data:
        print("JSON data is empty")
        return
    for entry in json_data: 
        domain = entry.get("domain","").lower()
        entry['email_count'] = domain_counts.get(domain,0)
    with open(csv_file, 'w', newline='', encoding='utf-8') as csv_f:
        # Use DictWriter to write dictionaries to CSV
        writer = csv.DictWriter(csv_f, fieldnames=json_data[0].keys())
        
        # Write the header
        writer.writeheader()
        
        # Write the rows
        writer.writerows(json_data)

    print(f"CSV file saved to {csv_file}")

# Function to get security scorecard domain score for a given domain 
def get_portfolio_details(portfolio_id):
    url = "https://api.securityscorecard.io/portfolios/"+portfolio_id+"/companies"
    r = requests.get(url, headers=headers)
    if r.status_code == 404:
        return None
    data = r.json()
    
    for entry in data['entries']:
            # Extract the desired fields using .get() for safety
            # Provides 'N/A' if a key is missing in a specific entry
        domain = entry.get('domain', 'N/A')
        uuid = entry.get('uuid', 'N/A')
        name = entry.get('name', 'N/A')
        score = entry.get('score', 'N/A')
        grade = entry.get('grade', 'N/A')
        industry = entry.get('industry', 'N/A')
        size = entry.get('size', 'N/A')


    # Print the extracted information for the current company
        print(f"Domain: {domain}")
        print(f"Name: {name}")
        print(f"Name: {industry}")
        print(f"Size: {size}")
        print(f"Score: {score}")
        print(f"Grade: {grade}")
        print("-" * 20) # Print a separator line for readability
    return data['entries']

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--csv', help="Path to CSV file with guest emails")
    parser.add_argument('--domain-output', default="domain_results.csv", help="Output CSV file for domain summary report")
    parser.add_argument('--pwned-output', default="pwned_results.csv", help="Output CSV file for HIBP email report")
    args = parser.parse_args()

    emails = get_guest_users_from_csv(args.csv) 
    domain_counts = get_domains_with_counts(emails)
    portfolio = create_portfolio("GuestGuard")
    if not portfolio:
        return
    portfolio_id = portfolio["id"]
    try:
        add_domains_to_portfolio(portfolio_id, domain_counts)
        details = get_portfolio_details(portfolio_id)
        json_object_to_csv(details, domain_counts, args.output)
    finally:
        delete_portfolio(portfolio_id)
    

if __name__ == "__main__":
    main()