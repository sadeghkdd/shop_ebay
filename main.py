import streamlit as st
import sqlite3
import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    headers = {
        "User-Agent": "Your User Agent",
        "Accept-Language": "en-US, en;q=0.5"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all("div", class_="s-item__info")
    images = soup.find_all("div", class_="s-item__image-wrapper image-treatment")
    
    items = []
    for product, img in zip(products, images):
        title = product.select_one('.s-item__title').text if product.select_one('.s-item__title') else "N/A"
        link = product.select_one('.s-item__link')['href'] if product.select_one('.s-item__link') else "N/A"
        price = product.select_one('.s-item__price').text if product.select_one('.s-item__price') else "N/A"
        img_tag = img.find("img")
        img_url = img_tag['src'] if img_tag else "N/A"
        items.append((link, title, price, img_url))
    return items

def store_data(database, data):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS products')  

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                      link TEXT, 
                      title TEXT, 
                      price TEXT, 
                      img TEXT)''')

    data = data[2:]  
    if data:
        data = [data[0]] + data  
        cursor.executemany('INSERT INTO products (link, title, price, img) VALUES (?,?,?,?)', data)
    conn.commit()
    conn.close()

def fetch_product_data(database='products.db'):
    conn = sqlite3.connect(database)
    query = '''SELECT link, title, price, img FROM products'''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    st.set_page_config(layout="centered")
    st.title("🌐 Online Shop 🌐")
    search_query = st.text_input("Search in eBay 🔎", value="", max_chars=None, placeholder='Search in eBay', key='searchbox', label_visibility='collapsed', help='Search in eBay 🔎').strip()

    if search_query:
        with st.spinner("Fetching data from eBay...🔎"):
            base_url = "https://www.ebay.com/sch/i.html?_nkw="
            url = f"{base_url}{search_query}"
            html = fetch_html(url)
            products = parse_html(html)
            store_data('products.db', products)
            st.success("✅ Data fetched successfully ✅")
    
    try:
        products = fetch_product_data()
    except pd.io.sql.DatabaseError:
        products = pd.DataFrame(columns=['link', 'title', 'price', 'img']) 

    items_per_page = 4
    total_pages = max((len(products) + items_per_page - 1) // items_per_page, 1)
    page_number = st.session_state.get('page_number', 1)

    start_idx = (page_number - 1) * items_per_page
    end_idx = start_idx + items_per_page

    if not products.empty:
        for idx in range(start_idx, min(end_idx, len(products))):
            product = products.iloc[idx]
            col1, col2 = st.columns([2, 5])
            with col1:
                st.image(product['img'], width=200)
            with col2:
                st.markdown(f"### {product['title']}")
                st.markdown(f"**Price:** {product['price']}")
                st.markdown(
                    f'<a target="_blank" href="{product["link"]}" style="text-decoration:none"><div style="display:inline-block;background-color:blue;color:black;padding:10px;border-radius:5px;">View on eBay</div></a>',
                    unsafe_allow_html=True
                )
            st.write("---")  

    st.write("") 

    
    col_blank1, col_prev, col_next, col_blank2 = st.columns([1, 2, 2, 1])

    if total_pages > 1:
        page_number = st.slider("Page", 1, total_pages, page_number, key="slider")

    with col_prev:
        if page_number > 1 and st.button("◀ Previous Page", key="prev"):
            st.session_state.page_number = page_number - 1

    with col_next:
        if page_number < total_pages and st.button("Next Page ▶", key="next"):
            st.session_state.page_number = page_number + 1

    st.write("")  

if __name__ == "__main__":
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1
    main()
