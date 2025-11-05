import os
import streamlit as st
import requests
import pandas as pd

# ---------------------------------------------------
# STREAMLIT PAGE SETUP
# ---------------------------------------------------
st.set_page_config(page_title="Apollo Bulk Company Enrichment", layout="centered")
st.title("🚀 Apollo Bulk Company Enrichment Tool")

# ---------------------------------------------------
# LOAD API KEY SECURELY
# ---------------------------------------------------
api_key = os.getenv("APOLLO_API_KEY") or st.secrets.get("APOLLO_API_KEY")

if not api_key:
    st.warning("⚠️ Apollo API key not found. Please set APOLLO_API_KEY in your environment or Streamlit Secrets.")
else:
    st.info("✅ API key loaded securely")

# ---------------------------------------------------
# INPUT SECTION
# ---------------------------------------------------
st.subheader("Enter domains (one per line or upload a CSV)")

# Option 1: Text input
domains_input = st.text_area(
    "Enter one domain per line (e.g. hubspot.com, zoom.us)",
    placeholder="example.com\nanotherdomain.com"
)

# Option 2: CSV upload
uploaded_file = st.file_uploader("Or upload a CSV file with a 'domain' column", type=["csv"])

# ---------------------------------------------------
# PARSE INPUT
# ---------------------------------------------------
domains = []

if uploaded_file:
    try:
        df_upload = pd.read_csv(uploaded_file)
        if "domain" in df_upload.columns:
            domains = df_upload["domain"].dropna().astype(str).tolist()
        else:
            st.error("❌ CSV must contain a column named 'domain'.")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
elif domains_input.strip():
    domains = [d.strip() for d in domains_input.split("\n") if d.strip()]

# ---------------------------------------------------
# FETCH DATA BUTTON
# ---------------------------------------------------
if st.button("Fetch Data"):
    if not api_key:
        st.error("Missing API key. Please set it first.")
    elif not domains:
        st.error("Please enter or upload at least one domain.")
    else:
        st.info(f"Fetching company data for {len(domains)} domains...")
        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, domain in enumerate(domains):
            status.text(f"Fetching data for {domain}... ({i+1}/{len(domains)})")

            url = "https://api.apollo.io/v1/companies/enrich"
            headers = {"Content-Type": "application/json"}
            payload = {"api_key": api_key, "domain": domain}

            try:
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 401:
                    results.append({"domain": domain, "error": "Unauthorized — invalid or limited API key"})
                    continue

                data = response.json()

                if response.status_code != 200:
                    results.append({"domain": domain, "error": data.get("message", response.text)})
                    continue

                company = data.get("company")
                if not company:
                    results.append({"domain": domain, "error": "No company found"})
                    continue

                results.append({
                    "domain": domain,
                    "name": company.get("name", ""),
                    "website": company.get("website_url", ""),
                    "industry": company.get("industry", ""),
                    "location": f"{company.get('city', '')}, {company.get('country', '')}",
                    "employee_count": company.get("estimated_num_employees", ""),
                    "founded_year": company.get("founded_year", ""),
                    "linkedin": company.get("linkedin_url", ""),
                    "last_updated": company.get("last_updated_at", "")
                })

            except Exception as e:
                results.append({"domain": domain, "error": str(e)})

            progress.progress((i + 1) / len(domains))

        # ---------------------------------------------------
        # DISPLAY RESULTS
        # ---------------------------------------------------
        df = pd.DataFrame(results)
        st.success("✅ Data fetched successfully!")
        st.dataframe(df)

        # ---------------------------------------------------
        # DOWNLOAD BUTTON
        # ---------------------------------------------------
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="apollo_company_data.csv",
            mime="text/csv"
        )

        status.text("Done ✅")
