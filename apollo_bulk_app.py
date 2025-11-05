import os
import streamlit as st
import requests
import pandas as pd

# --------------------------------------------------
# STREAMLIT PAGE SETUP
# --------------------------------------------------
st.set_page_config(page_title="Apollo Bulk Company Fetcher", layout="centered")
st.title("🚀 Apollo Bulk Data Fetcher")

# --------------------------------------------------
# LOAD API KEY SECURELY
# --------------------------------------------------
api_key = os.getenv("APOLLO_API_KEY") or st.secrets.get("APOLLO_API_KEY")

if not api_key:
    st.warning("⚠️ Apollo API key not found. Please set APOLLO_API_KEY in your environment or Streamlit Secrets.")
else:
    st.info("✅ API key loaded securely")

# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------
st.subheader("Enter domains or company names")
domains_input = st.text_area(
    "Enter one per line (e.g., zoom.us, hubspot.com, apollo.io)",
    placeholder="example.com\nanotherdomain.com"
)

fetch_type = st.radio(
    "What do you want to fetch?",
    ["Company data by domain", "Person data by email (coming soon)"]
)

# --------------------------------------------------
# BUTTON TO FETCH
# --------------------------------------------------
if st.button("Fetch Data"):
    if not api_key:
        st.error("Missing API key. Please set it first.")
    elif not domains_input.strip():
        st.error("Please enter at least one domain.")
    else:
        domains = [d.strip() for d in domains_input.split("\n") if d.strip()]
        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, domain in enumerate(domains):
            status.text(f"Fetching data for {domain}... ({i+1}/{len(domains)})")

            url = "https://api.apollo.io/v1/mixed_companies/search"
            headers = {"Cache-Control": "no-cache", "Content-Type": "application/json"}
            payload = {
                "api_key": api_key,
                "q_organization_domains": [domain],
                "page": 1,
                "per_page": 1
            }

            try:
                response = requests.post(url, json=payload, headers=headers)
                data = response.json()

                if response.status_code != 200:
                    results.append({"domain": domain, "error": data.get("message", "Request failed")})
                    continue

                companies = data.get("companies", [])
                if not companies:
                    results.append({"domain": domain, "error": "No company found"})
                    continue

                company = companies[0]

                results.append({
                    "domain": domain,
                    "name": company.get("name", ""),
                    "website": company.get("website_url", ""),
                    "industry": company.get("industry", ""),
                    "location": company.get("city", "") + ", " + company.get("country", ""),
                    "founded_year": company.get("founded_year", ""),
                    "employee_count": company.get("estimated_num_employees", ""),
                    "linkedin": company.get("linkedin_url", "")
                })

            except Exception as e:
                results.append({"domain": domain, "error": str(e)})

            progress.progress((i + 1) / len(domains))

        df = pd.DataFrame(results)
        st.success("✅ Data fetched successfully!")
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv, file_name="apollo_company_data.csv", mime="text/csv")
