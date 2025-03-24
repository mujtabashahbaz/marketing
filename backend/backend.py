import os
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from duckduckgo_search import DDGS

app = Flask(__name__)

# ✅ DuckDuckGo Search Function
def scrape_duckduckgo_search(query, num_results=10):
    try:
        with DDGS() as search:
            results = list(search.text(query, max_results=num_results))
        links = [result["href"] for result in results if "href" in result]
        return links
    except Exception as e:
        print(f"❌ Error fetching DuckDuckGo results: {e}")
        return []

# ✅ Keyword Extraction Function
def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    return list(set(words))

# ✅ Keyword Clustering Function
def cluster_keywords(keywords, num_clusters=5):
    if not keywords:
        return {"error": "No keywords extracted. Try another search term."}

    vectorizer = TfidfVectorizer()
    try:
        X = vectorizer.fit_transform(keywords)
    except ValueError:
        return {"error": "Not enough unique keywords for clustering."}

    kmeans = KMeans(n_clusters=min(num_clusters, len(keywords)), random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)

    clustered_keywords = {i: [] for i in range(num_clusters)}
    for i, keyword in enumerate(keywords):
        clustered_keywords[clusters[i]].append(keyword)

    return clustered_keywords

# ✅ Store Keywords in SQLite Database
def store_keywords_in_db(keyword_clusters):
    conn = sqlite3.connect("seo_keywords.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS keywords (cluster INTEGER, keyword TEXT)")
    
    for cluster, keywords in keyword_clusters.items():
        for keyword in keywords:
            cursor.execute("INSERT INTO keywords (cluster, keyword) VALUES (?, ?)", (cluster, keyword))

    conn.commit()
    conn.close()

# ✅ Flask API Route
@app.route('/scrape', methods=['POST'])
def scrape_and_cluster():
    data = request.json
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    links = scrape_duckduckgo_search(query, num_results=5)
    if not links:
        return jsonify({"error": "No links found. DuckDuckGo might not have enough data."}), 500
    
    all_keywords = []
    for link in links:
        try:
            page = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            page.raise_for_status()
            soup = BeautifulSoup(page.text, "html.parser")
            text = soup.get_text()
            if len(text) < 500:
                continue
            keywords = extract_keywords(text)
            all_keywords.extend(keywords)
        except Exception as e:
            print(f"❌ Skipping {link} due to error: {e}")

    all_keywords = list(set(all_keywords))
    keyword_clusters = cluster_keywords(all_keywords)
    if "error" in keyword_clusters:
        return jsonify(keyword_clusters), 400
    
    store_keywords_in_db(keyword_clusters)
    return jsonify({"message": "Scraping & clustering complete", "clusters": keyword_clusters})

# ✅ Run Flask Server
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Use the PORT environment variable or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
