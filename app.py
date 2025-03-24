import requests
from bs4 import BeautifulSoup
import re
import openai
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# 1. Scrape Google search results (Requires a User-Agent to avoid blocking)
def scrape_google_search(query, num_results=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.google.com/search?q={query}&num={num_results}"
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for g in soup.find_all('div', class_='tF2Cxc'):
        link = g.find('a', href=True)
        if link:
            links.append(link['href'])
    
    return links

# 2. Extract keywords from content (Basic NLP Processing)
def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())  # Extract words with 4+ letters
    return list(set(words))  # Return unique words

# 3. AI-Powered Keyword Clustering
def cluster_keywords(keywords, num_clusters=5):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(keywords)

    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)

    clustered_keywords = {i: [] for i in range(num_clusters)}
    for i, keyword in enumerate(keywords):
        clustered_keywords[clusters[i]].append(keyword)

    return clustered_keywords

# 4. Store keywords in SQLite Database
def store_keywords_in_db(keyword_clusters):
    conn = sqlite3.connect("seo_keywords.db")
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS keywords (cluster INTEGER, keyword TEXT)")
    for cluster, keywords in keyword_clusters.items():
        for keyword in keywords:
            cursor.execute("INSERT INTO keywords (cluster, keyword) VALUES (?, ?)", (cluster, keyword))

    conn.commit()
    conn.close()

# Main Execution
if __name__ == "__main__":
    search_query = "best SEO strategies 2025"
    
    print("Scraping Google search results...")
    links = scrape_google_search(search_query)

    all_keywords = []
    for link in links:
        try:
            page = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(page.text, "html.parser")
            text = soup.get_text()
            keywords = extract_keywords(text)
            all_keywords.extend(keywords)
        except Exception as e:
            print(f"Skipping {link} due to error: {e}")

    print("Clustering keywords...")
    keyword_clusters = cluster_keywords(list(set(all_keywords)))

    print("Storing in database...")
    store_keywords_in_db(keyword_clusters)

    print("Keyword clustering complete. Data saved to 'seo_keywords.db'.")