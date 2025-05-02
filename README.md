# GuestGuard – Domain Risk Auditor for Entra ID Guests

## Overview

### Context
GuestGuard was developed as part of the 2025 SecurityScorecard Hackathon. 

### Problem:
Organizations increasingly collaborate with external users via Microsoft Entra ID (formerly Azure AD) guest accounts. However, many do not assess the security posture of the domains these guest accounts originate from. This oversight creates blind spots that adversaries could exploit, especially when those domains belong to third-party vendors or service providers with poor security hygiene.

### Goal:
GuestGuard helps organizations assess the risk of guest domains within their Entra tenant by leveraging the SecurityScorecard API. It enables users to quantify exposure and take action on the most concerning third-party domains.

## Key Features:
- Imports a CSV file of guest user email addresses (downloaded via the Entra portal or another source).
- Utilizes the SecurityScorecard API to evaluate the security posture of each unique guest domain (creating a temporary portfolio for analysis).
- Outputs reports in either CSV or HTML format with various levels of detail (basic or detailed).

## Analysis Levels:
- **Basic**: A summary report featuring information on the industry, company size, summary score/grade, and the number of guest email addresses identified for each domain.
- **Detailed**: Includes all basic-level data, along with additional information from the incident and company endpoints. This level provides detailed factor scores and any associated incident details.

## How to Use:

You can use GuestGuard with a pre-prepared CSV file containing email addresses (downloaded from the Entra portal or another source).

1. Populate the `config.json` file with your API key (an example is provided).
2. Run `guestguard.py`, specifying the required arguments:
   
   ```bash
   python guestguard.py --csv 'sample_data/input.csv' --outputmode 'html' --outputname 'test.html' --analysis 'detailed'
   ````

3. Review the generated HTML/CSV output and take necessary actions based on the findings.

##  Future potential improvements
- **MS Graph API Integration**: Directly pull guest user details from Microsoft Graph.
- **Alerting**: Set up notifications when new domains are detected or when a guest domain's score crosses a predefined threshold. 
- **Additional API Integrations**: Integrate with external services like "Have I Been Pwned" to check if email addresses have been exposed in data breaches.
