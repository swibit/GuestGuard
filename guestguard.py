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

# Function to get emails from csv file if provided - assumes that there is an 'email' column
def get_guest_users_from_csv(file_path):
    print(f"Loading guest emails from CSV file: {file_path}")
    with open(file_path, newline='') as f:
        return [row['email'] for row in csv.DictReader(f)]
    
# Function to split email domain from address
def get_domain(email):
    return email.split('@')[-1].lower()

# Function to convert email list to domain list including volumes that each domain appears
def get_domains_with_counts(emails):
    print(f"Counting email domains from a list of {len(emails)} emails")
    domain_counts = defaultdict(int)
    for email in emails:
        domain = get_domain(email)
        domain_counts[domain] += 1
    return domain_counts

# Function to create a portfolio - temporarily done to avoid a 403 error when looking up company data
def create_portfolio(portfolio_name):
    print(f"Creating portfolio: {portfolio_name}")
    url = "https://api.securityscorecard.io/portfolios"
    payload = {
        "name": portfolio_name,
        "description": "Temporary portfolio for guest users' domains"
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
    print(f"Adding domains to portfolio with ID {portfolio_id}")
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
        print(f"Failed to add domains: {response.text}")
        return None

# Function to clear up temporary portfolio
def delete_portfolio(portfolio_id):
    print(f"Deleting temporary portfolio with ID {portfolio_id}")
    url = "https://api.securityscorecard.io/portfolios/"+portfolio_id
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    print("Temporary portfolio deleted.")
    return True

# Function to convert enriched JSON data to CSV, including handling of detailed factors and incidents if analysis detailed is used
def json_object_to_csv(json_data, csv_file):
    if not json_data:
        print("JSON data is empty")
        return

    # Flatten the data and extract detailed factors into their own columns
    flattened_data = []
    for row in json_data:
        # Create a base dictionary with the non-factor fields
        flattened_row = {
            "Domain": row.get("Domain", "N/A"),
            "Name": row.get("Name", "N/A"),
            "Industry": row.get("Industry", "N/A"),
            "Company Size": row.get("Company Size", "N/A"),
            "Score": row.get("Score", "N/A"),
            "Grade": row.get("Grade", "N/A"),
            "Email Count": row.get("Email Count", 0)
        }

        # Add detailed factors (if available) as separate columns
        if "Detailed Factors" in row:
            for i, factor in enumerate(row["Detailed Factors"]):
                flattened_row[f"Factor {i+1} Name"] = factor.get("name", "N/A")
                flattened_row[f"Factor {i+1} Score"] = factor.get("score", "N/A")

        # Add incidents if available
        if "Incidents" in row:
            for i, incident in enumerate(row["Incidents"]):
                flattened_row[f"Incident {i+1} Description"] = incident.get("description", "N/A")
                flattened_row[f"Incident {i+1} Severity"] = incident.get("severity", "N/A")

        flattened_data.append(flattened_row)

    # Write the flattened data to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as csv_f:
        # Use DictWriter to write dictionaries to CSV
        fieldnames = flattened_data[0].keys()  # Get the headers from the first row
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
        
        # Write the header
        writer.writeheader()
        
        # Write the rows
        writer.writerows(flattened_data)

    print(f"CSV file saved to {csv_file}")

    # Write the flattened data to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as csv_f:
        # Use DictWriter to write dictionaries to CSV
        fieldnames = flattened_data[0].keys()  # Get the headers from the first row
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
        
        # Write the header
        writer.writeheader()
        
        # Write the rows
        writer.writerows(flattened_data)

    print(f"CSV file saved to {csv_file}")

# Function to get incidents for a given domain to provide context
def get_incidents(domain):
    print(f"Fetching incidents for domain: {domain}")
    url = f"https://api.securityscorecard.io/companies/{domain}/incidents"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[WARN] Failed to get incidents for {domain}: {response.status_code}")
        return []
    incidents_json = response.json()
    incidents = []
    for incident in incidents_json.get("entries", []):
        incidents.append({
            "description": incident.get("description"),
            "severity": incident.get("severity")
        })
    return incidents

# Function to get summary security scorecard domain score for a given portfolio
def get_portfolio_details(portfolio_id):
    print(f"Fetching portfolio details for portfolio ID: {portfolio_id}")
    url = "https://api.securityscorecard.io/portfolios/"+portfolio_id+"/companies"
    r = requests.get(url, headers=headers)
    if r.status_code == 404:
        return None
    data = r.json()
    
    for entry in data['entries']:
        domain = entry.get('domain', 'N/A')
        uuid = entry.get('uuid', 'N/A')
        name = entry.get('name', 'N/A')
        score = entry.get('score', 'N/A')
        grade = entry.get('grade', 'N/A')
        industry = entry.get('industry', 'N/A')
        size = entry.get('size', 'N/A')
    return data['entries']

# Function to get detailed factors for a given domain to provide more granular info
def get_detailed_factors(domain):
    print(f"Fetching detailed factors for domain: {domain}")
    url = "https://api.securityscorecard.io/companies/"+domain+"/factors"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[WARN] Failed to get detailed scores for {domain}: {response.status_code}")
        return {}
    factors_json = response.json()
    factors = []
    for factor in factors_json.get("entries", []):
        factors.append({
            "name": factor.get("name"),
            "score": factor.get("score"),
            "grade": factor.get("grade"),
            "grade_url": factor.get("grade_url")
        })

    return factors

# Function to enrich portfolio domain detail with guest user counts. 
def enrich_with_email_counts(details, domain_counts, analysis_level="basic"):
    print(f"Enriching domain details with email counts. Analysis level: {analysis_level}")
    enriched = []
    for entry in details:
        domain = entry.get('domain', 'N/A').lower()
        enriched_row = {
            "Domain": domain,
            "Name": entry.get('name', 'N/A'),
            "Industry": entry.get('industry', 'N/A'),
            "Company Size": entry.get('size', 'N/A'),
            "Score": entry.get('score', 'N/A'),
            "Grade": entry.get('grade', 'N/A'),
            "Email Count": domain_counts.get(domain, 0)
        }

        if analysis_level == 'detailed':
            factor_scores = get_detailed_factors(domain)
            if isinstance(factor_scores, list):  # ensure it's valid
                enriched_row["Detailed Factors"] = factor_scores

            incidents = get_incidents(domain)
            if isinstance(incidents, list):  # ensure it's valid
                enriched_row["Incidents"] = incidents

        enriched.append(enriched_row)
    return enriched

# Function to save HTML report to file
def save_html_report(enriched_data, output_name):
    print(f"Saving HTML report to: {output_name}")
    html = "<html><head><style>"
    html += "table, th, td { border: 1px solid black; border-collapse: collapse; padding: 5px; }"
    html += "th { background-color: #f2f2f2; }"
    html += "</style></head><body>"

    html += "<h2>Summary Report</h2>"
    html += "<table>"
    headers = ["Domain", "Name", "Industry", "Company Size", "Score", "Grade", "Email Count"]
    html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"

    for row in enriched_data:
        html += "<tr>" + "".join(f"<td>{row.get(h, 'N/A')}</td>" for h in headers) + "</tr>"

        # Detailed factors section if available
        if "Detailed Factors" in row:
            html += "<tr><td colspan='7'>"
            html += "<h4>Detailed Factors</h4>"
            html += "<table style='margin-left: 20px;'>"
            html += "<tr><th>Factor</th><th>Score</th></tr>"
            for factor in row["Detailed Factors"]:
                html += "<tr><td>{}</td><td>{}</td></tr>".format(
                    factor.get("name", "Unknown"),
                    factor.get("score", "N/A")
                )
            html += "</table></td></tr>"

        # Incidents section if available
        if "Incidents" in row:
            html += "<tr><td colspan='7'>"
            html += "<h4>Incidents</h4>"
            html += "<table style='margin-left: 20px;'>"
            html += "<tr><th>Description</th><th>Severity</th></tr>"
            for incident in row["Incidents"]:
                html += "<tr><td>{}</td><td>{}</td></tr>".format(
                    incident.get("description", "Unknown"),
                    incident.get("severity", "N/A")
                )
            html += "</table></td></tr>"

    html += "</table></body></html>"

    with open(output_name, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report saved to {output_name}")

def main():
    print("Starting the process...")
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--csv', help="Path to CSV file with guest emails")
    parser.add_argument('--outputname', default="results.csv", help="Output file name")
    parser.add_argument('--outputmode', default="csv", help="Specifies if HTML or CSV output")
    parser.add_argument('--analysis', default='basic', help="Analysis level")
    args = parser.parse_args()

    emails = get_guest_users_from_csv(args.csv) 
    domain_counts = get_domains_with_counts(emails)
    portfolio = create_portfolio("GuestGuard")
    if not portfolio:
        print("Exiting due to portfolio creation failure.")
        return
    portfolio_id = portfolio["id"]
    try:
        add_domains_to_portfolio(portfolio_id, domain_counts)
        details = get_portfolio_details(portfolio_id)
        enrich_details = enrich_with_email_counts(details, domain_counts, args.analysis)
        if args.outputmode == 'csv':
            json_object_to_csv(enrich_details, args.outputname)
        if args.outputmode == 'html':
            save_html_report(enrich_details, args.outputname)
    finally:
        delete_portfolio(portfolio_id)

if __name__ == "__main__":
    main()
 