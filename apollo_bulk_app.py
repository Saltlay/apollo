import os, requests, pandas as pd, streamlit as st

st.set_page_config(page_title="Apollo Bulk Company Enrichment", layout="centered")
st.title("🚀 Apollo Bulk Company Enrichment")

api_key = os.getenv("APOLLO_API_KEY") or st.secrets.get("APOLLO_API_KEY")
if not api_key:
    st.warning("Set APOLLO_API_KEY in environment or Streamlit Secrets.")
else:
    st.info("✅ API key loaded")

text = st.text_area("Enter domains (one per line)", "hubspot.com\nzoom.us")
file = st.file_uploader("Or upload CSV with a 'domain' column", type=["csv"])

domains = []
if file:
    try:
        df = pd.read_csv(file)
        domains = df["domain"].dropna().astype(str).tolist()
    except Exception as e:
        st.error(f"CSV error: {e}")
elif text.strip():
    domains = [d.strip() for d in text.splitlines() if d.strip()]

if st.button("Fetch Data") and domains:
    results = []
    bar = st.progress(0)
    for i, d in enumerate(domains):
        try:
            r = requests.post(
                "https://api.apollo.io/v1/companies/enrich",
                json={"api_key": api_key, "domain": d},
                headers={"Content-Type": "application/json"},
                timeout=20,
            )
            if r.status_code == 401:
                results.append({"domain": d, "error": "401 Unauthorized – invalid key or plan"})
                continue
            if r.status_code != 200:
                results.append({"domain": d, "error": f"{r.status_code}: {r.text[:80]}"})
                continue
            data = r.json()
            c = data.get("company")
            if not c:
                results.append({"domain": d, "error": "No company found"})
                continue
            results.append({
                "domain": d,
                "name": c.get("name",""),
                "website": c.get("website_url",""),
                "industry": c.get("industry",""),
                "location": f"{c.get('city','')}, {c.get('country','')}",
                "employees": c.get("estimated_num_employees",""),
                "linkedin": c.get("linkedin_url","")
            })
        except Exception as e:
            results.append({"domain": d, "error": str(e)})
        bar.progress((i+1)/len(domains))
    df = pd.DataFrame(results)
    st.dataframe(df)
    st.download_button("📥 Download CSV", df.to_csv(index=False), "apollo_results.csv", "text/csv")
