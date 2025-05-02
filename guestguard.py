import json
import requests
import argparse
import csv
from collections import defaultdict

# Load API keys from file
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

# Function to convert email list to domain list
def get_domains(emails):
    domains = set()
    for email in emails: 
        domains.add(get_domain(email))
    return list(domains)
   
# Function to create a portfolio
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
    
def add_domains_to_portfolio(portfolio_id, domains):
    url = "https://api.securityscorecard.io/portfolios/companies/bulk-upload"
    payload = {
        "portfolios": [portfolio_id],
        "companies": domains
    }
    response = requests.put(url, json=payload, headers=headers)

    if response.status_code != 400:
        print("Domains added to portfolio")
        return response.json()
    else:
        print(f"Failed to create portfolio: {response.text}")
        return None

def delete_portfolio(portfolio_id):
    url = "https://api.securityscorecard.io/portfolios/"+portfolio_id
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return True

def json_object_to_csv(json_data, csv_file):
    if not json_data:
        print("JSON data is empty")
        return
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
    parser.add_argument('--output', default="results.csv", help="Output CSV file")
    args = parser.parse_args()

    emails = get_guest_users_from_csv(args.csv) 
    domain_counts = defaultdict(int)
    portfolio = create_portfolio("GuestGuard")
    if portfolio:
        portfolio_id = portfolio['id']
        domains = get_domains(emails)
        add_domains_to_portfolio(portfolio_id, domains)
        details=get_portfolio_details(portfolio_id)
        json_object_to_csv(details,args.output)
        delete_portfolio(portfolio_id)
    

if __name__ == "__main__":
    main()