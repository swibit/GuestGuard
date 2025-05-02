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

# Function to enrich portfolio domain detail with guest user counts. 
def enrich_with_email_counts(details, domain_counts):
    enriched = []
    for entry in details:
        domain = entry.get('domain', 'N/A').lower()
        enriched.append({
            "Domain": domain,
            "Name": entry.get('name', 'N/A'),
            "Industry": entry.get('industry', 'N/A'),
            "Company Size": entry.get('size', 'N/A'),
            "Score": entry.get('score', 'N/A'),
            "Grade": entry.get('grade', 'N/A'),
            "Email Count": domain_counts.get(domain, 0)
        })
    return enriched

def save_html_report(data, output_file):
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h2 { color: #333; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #fafafa; }
            .low-score { background-color: #ffe6e6; }  /* red for score < 70 */
            .med-score { background-color: #fff5cc; }  /* yellow for score < 85 */
        </style>
    </head>
    <body>
        <h2>GuestGuard Domain Security Report</h2>
        <table>
            <tr>
                <th>Domain</th>
                <th>Organisation</th>
                <th>Industry</th>
                <th>Company Size</th>
                <th>Score</th>
                <th>Grade</th>
                <th>Email Count</th>
            </tr>
    """

    for row in data:
        print(row)
        score = int(row.get("Score", 0)) if str(row.get("Score")).isdigit() else 0
        score_class = ""
        if score < 70:
            score_class = "low-score"
        elif score < 85:
            score_class = "med-score"

        html += f"""
            <tr class="{score_class}">
                <td>{row['Domain']}</td>
                <td>{row['Name']}</td>
                <td>{row['Industry']}</td>
                <td>{row['Company Size']}</td>
                <td>{row['Score']}</td>
                <td>{row['Grade']}</td>
                <td>{row['Email Count']}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report saved to {output_file}")

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--csv', help="Path to CSV file with guest emails")
    parser.add_argument('--outputname', default="results.csv", help="Output file name")
    parser.add_argument('--outputmode', default="csv", help="Specifies if HTML or CSV output")
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
        enrich_details = enrich_with_email_counts(details,domain_counts)
        if args.outputmode == 'csv':
            json_object_to_csv(enrich_details, args.outputname)
        if args.outputmode == 'html':
            save_html_report(enrich_details, args.outputname)   
    finally:
        delete_portfolio(portfolio_id)
    

if __name__ == "__main__":
    main()