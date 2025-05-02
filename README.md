# GuestGuard – Domain Risk Auditor for Entra ID Guests
##  Overview
### Context
This project was created as part of the 2025 SecurityScorecard Hackathon. 

###  Problem:
Organisations increasingly collaborate with external users through Microsoft Entra ID (Azure AD) guest accounts. However, few organisations evaluate the security posture of guest users' source domains, creating blind spots that adversaries can exploit — especially when those domains belong to vendors or third parties with poor security hygiene.

### Goal:
GuestGuard helps organisations identify risky guest domains in their Entra tenant using SecurityScorecard's API, quantify their exposure, and take action on the most concerning third parties.

##  Key features:
* Two Input Modes (CSV or dynamically via Graph API)
* Uses the SecurityScorecard API to evaluate each unique guest domain
* Outputs a summary report with details including score, grade, industry, guest count per domain.

##  How to use:
You can either use this tool with a csv file already prepared of email accounts (downloaded via Entra portal/another source) or you can directly pull in data if you have an MS Graph API token. 
