#!/usr/bin/env python3
"""Fetch S&P 500 companies from Wikipedia and generate YAML config."""

import pandas as pd
import yaml
from collections import defaultdict
import urllib.request

# Fetch S&P 500 list from Wikipedia with user agent
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    html = response.read()

tables = pd.read_html(html)
sp500_table = tables[0]

# Map GICS Sector to our sector names
sector_mapping = {
    "Information Technology": "Information Technology",
    "Health Care": "Health Care",
    "Financials": "Financials",
    "Consumer Discretionary": "Consumer Discretionary",
    "Communication Services": "Communication Services",
    "Industrials": "Industrials",
    "Consumer Staples": "Consumer Staples",
    "Energy": "Energy",
    "Utilities": "Utilities",
    "Real Estate": "Real Estate",
    "Materials": "Materials",
}

# Group companies by sector
companies_by_sector = defaultdict(list)

for _, row in sp500_table.iterrows():
    ticker = row['Symbol']
    company_name = row['Security']
    gics_sector = row['GICS Sector']
    
    # Map to our sector names
    sector = sector_mapping.get(gics_sector, "Other")
    
    # Create search terms: ticker, company name, and common abbreviations
    search_terms = [ticker, company_name]
    
    # Add common abbreviations
    if "Inc." in company_name:
        search_terms.append(company_name.replace("Inc.", "").strip())
    if "Corporation" in company_name:
        search_terms.append(company_name.replace("Corporation", "Corp").strip())
        search_terms.append(company_name.replace("Corporation", "").strip())
    if "Company" in company_name:
        search_terms.append(company_name.replace("Company", "Co").strip())
    if "Technologies" in company_name:
        search_terms.append(company_name.replace("Technologies", "Tech").strip())
    
    companies_by_sector[sector].append({
        "ticker": ticker,
        "name": company_name,
        "search_terms": list(set(search_terms))  # Remove duplicates
    })

# Convert to YAML structure
output = {
    "sp500_companies": {}
}

for sector in sorted(companies_by_sector.keys()):
    output["sp500_companies"][sector] = companies_by_sector[sector]

# Write to YAML file
output_path = "../config/sp500_companies.yml"
with open(output_path, 'w') as f:
    yaml.dump(output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"✅ Generated {output_path}")
print(f"📊 Total companies: {sum(len(v) for v in companies_by_sector.values())}")
print(f"📁 Sectors: {len(companies_by_sector)}")
for sector, companies in sorted(companies_by_sector.items()):
    print(f"  - {sector}: {len(companies)} companies")
