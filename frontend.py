import streamlit as st
import requests

# Backend API URL
API_URL = "http://127.0.0.1:5000/scrape"

# Streamlit UI
st.title("🔍 SEO Automation Tool")
st.subheader("Enter a search query to analyze SEO keywords")

# User input
query = st.text_input("Enter Search Query")

# Button to trigger processing
if st.button("Analyze SEO"):
    if query.strip() == "":
        st.error("❌ Please enter a valid search query!")
    else:
        st.info("⏳ Processing... Please wait.")

        try:
            # Send request to backend
            response = requests.post(API_URL, json={"query": query}, timeout=30)

            # Handle response
            if response.status_code == 200:
                data = response.json()
                clusters = data.get("clusters", {})

                st.success("✅ Scraping & Clustering Complete!")
                
                # Display results
                for cluster, keywords in clusters.items():
                    st.subheader(f"Cluster {int(cluster) + 1}")  # 🔥 Fixed TypeError
                    st.write(", ".join(keywords))  # Display keywords

            else:
                st.error(f"❌ Backend Error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to backend: {e}")
