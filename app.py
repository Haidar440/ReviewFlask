from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
from urllib.request import Request
from textblob import TextBlob
from collections import Counter
import re
import os
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36"
}


def analyze_sentiment(text):
    """Return sentiment label and polarity score for a given text."""
    blob = TextBlob(str(text))
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        label = "Positive"
    elif polarity < -0.1:
        label = "Negative"
    else:
        label = "Neutral"
    return label, round(polarity, 2)

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/review',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            req = Request(flipkart_url, headers=HEADERS)

            uClient = uReq(req)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")

            # Find product links directly from <a> tags with href containing /p/ and pid=
            all_links = flipkart_html.find_all("a", href=True)
            product_links = []
            for a in all_links:
                href = a['href']
                if '/p/' in href and 'pid=' in href and href.startswith('/'):
                    product_links.append("https://www.flipkart.com" + href)

            if not product_links:
                return 'No products found for this search'

            # Build the product-reviews URL from the first product link
            first_link = product_links[0]
            match = re.search(r'flipkart\.com(/[^?]+)/p/([^?&]+)', first_link)
            pid_match = re.search(r'pid=([^&]+)', first_link)
            if not match or not pid_match:
                return 'Could not parse the product link'

            path = match.group(1)
            item_id = match.group(2)
            pid = pid_match.group(1)
            review_base_url = f"https://www.flipkart.com{path}/product-reviews/{item_id}?pid={pid}"

            filename = searchString + ".csv"
            fw = open(filename, "w", encoding="utf-8")
            headers_csv = "Product, Customer Name, Rating, Heading, Comment, Sentiment, Polarity \n"
            fw.write(headers_csv)
            fw.close()

            # Initialize SQLite Database
            db_path = 'reviews.db'
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS reviews_data
                         (product text, name text, rating text, comment_head text, comment text, sentiment text, polarity real)''')
            conn.commit()

            reviews = []
            max_pages = 5  # Scrape up to 5 pages (≈50 reviews)

            for page_num in range(1, max_pages + 1):
                try:
                    review_url = f"{review_base_url}&page={page_num}"
                    req = Request(review_url, headers=HEADERS)
                    prodRes = uReq(req)
                    review_page = prodRes.read()
                    prodRes.close()
                    review_html = bs(review_page, "html.parser")

                    # Extract reviews by finding rating divs (text like "5.0", "4.0", etc.)
                    rating_divs = review_html.find_all('div', string=re.compile(r'^[1-5]\.\d$'))

                    if not rating_divs:
                        break  # No more reviews, stop paginating

                    for rating_div in rating_divs:
                        try:
                            # Navigate up 10 levels to get the full review card container
                            review_card = rating_div
                            for _ in range(10):
                                review_card = review_card.parent

                            # Collect all unique text strings from the review card
                            all_texts = []
                            seen = set()
                            for desc in review_card.descendants:
                                if desc.string and desc.string.strip():
                                    text = desc.string.strip()
                                    if text not in seen:
                                        seen.add(text)
                                        all_texts.append(text)

                            # Extract rating
                            rating = all_texts[0] if len(all_texts) > 0 else 'No Rating'

                            # Extract heading (text after bullet)
                            commentHead = 'No Comment Heading'
                            bullet_idx = None
                            for i, t in enumerate(all_texts):
                                if t == '\u2022':
                                    bullet_idx = i
                                    break
                            if bullet_idx is not None and bullet_idx + 1 < len(all_texts):
                                commentHead = all_texts[bullet_idx + 1]

                            # Extract comment and name (after "Review for:..." text)
                            custComment = 'No Comment'
                            name = 'No Name'
                            review_for_idx = None
                            for i, t in enumerate(all_texts):
                                if t.startswith('Review for:'):
                                    review_for_idx = i
                                    break
                            if review_for_idx is not None and review_for_idx + 1 < len(all_texts):
                                custComment = all_texts[review_for_idx + 1]
                            if review_for_idx is not None and review_for_idx + 2 < len(all_texts):
                                name = all_texts[review_for_idx + 2]

                            mydict = {"Product": searchString, "Name": name, "Rating": rating,
                                      "CommentHead": commentHead, "Comment": custComment}

                            # Sentiment analysis on the comment
                            sentiment_text = f"{commentHead} {custComment}"
                            label, polarity = analyze_sentiment(sentiment_text)
                            mydict["Sentiment"] = label
                            mydict["Polarity"] = polarity

                            reviews.append(mydict)

                            try:
                                fw = open(filename, "a", encoding="utf-8")
                                fw.write(f"{searchString},{name},{rating},{commentHead},{custComment},{label},{polarity} \n")
                                fw.close()
                                
                                # Insert into SQLite DB
                                c.execute("INSERT INTO reviews_data VALUES (?,?,?,?,?,?,?)",
                                          (searchString, name, rating, commentHead, custComment, label, polarity))
                                conn.commit()
                            except Exception as e:
                                print("Exception while writing to csv/db: ", e)

                        except Exception as e:
                            print("Exception while parsing review: ", e)

                except Exception as e:
                    print(f"Exception while fetching page {page_num}: ", e)

            # Close SQLite connection after scraping
            conn.close()

            # Compute sentiment summary
            sentiment_counts = Counter(r["Sentiment"] for r in reviews)
            total = len(reviews)
            avg_polarity = round(sum(r["Polarity"] for r in reviews) / total, 2) if total else 0
            summary = {
                "total": total,
                "positive": sentiment_counts.get("Positive", 0),
                "neutral": sentiment_counts.get("Neutral", 0),
                "negative": sentiment_counts.get("Negative", 0),
                "avg_polarity": avg_polarity
            }

            # --- Generate Matplotlib Visualizations ---
            os.makedirs(os.path.join(app.root_path, 'static', 'images'), exist_ok=True)
            
            # 1. Sentiment Bar Chart
            plt.figure(figsize=(6, 4))
            labels = ['Positive', 'Neutral', 'Negative']
            counts = [summary['positive'], summary['neutral'], summary['negative']]
            colors = ['green', 'yellow', 'red']
            plt.bar(labels, counts, color=colors)
            plt.title('Sentiment Analysis Distribution')
            plt.xlabel('Sentiment')
            plt.ylabel('Number of Reviews')
            plt.tight_layout()
            sentiment_img_filename = f'images/{searchString}_sentiment.png'
            plt.savefig(os.path.join(app.root_path, 'static', sentiment_img_filename))
            plt.close()

            # 2. Word Frequency Chart (Top 10 words)
            all_comments = " ".join([r['Comment'] for r in reviews]).lower()
            words = re.findall(r'\b[a-z]{4,}\b', all_comments)
            stopwords = {'this', 'that', 'with', 'from', 'your', 'have', 'they', 'very', 'just', 'good', 'phone', 'product'}
            filtered_words = [w for w in words if w not in stopwords]
            word_counts = Counter(filtered_words).most_common(10)
            
            plt.figure(figsize=(8, 4))
            if word_counts:
                w_labels, w_values = zip(*word_counts)
                plt.bar(w_labels, w_values, color='skyblue')
                plt.title('Top 10 Word Frequencies')
                plt.xlabel('Words')
                plt.ylabel('Frequency')
                plt.xticks(rotation=45)
            else:
                plt.text(0.5, 0.5, 'Not enough data', ha='center', va='center')
            plt.tight_layout()
            wordfreq_img_filename = f'images/{searchString}_wordfreq.png'
            plt.savefig(os.path.join(app.root_path, 'static', wordfreq_img_filename))
            plt.close()

            return render_template('results.html', reviews=reviews, summary=summary, 
                                   searchString=searchString)


        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    # return render_template('results.html')

    else:
        return render_template('index.html')

@app.route('/analysis/<searchString>')
@cross_origin()
def analysis(searchString):
    # Determine image paths directly relative to the 'static' folder expected by url_for
    sentiment_img_filename = f'images/{searchString}_sentiment.png'
    wordfreq_img_filename = f'images/{searchString}_wordfreq.png'
    
    # Retrieve summary from sqlite
    db_path = 'reviews.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT sentiment, polarity FROM reviews_data WHERE product=?", (searchString,))
    rows = c.fetchall()
    conn.close()

    summary = None
    if rows:
        total = len(rows)
        sentiments = [r[0] for r in rows]
        polarities = [r[1] for r in rows]
        sentiment_counts = Counter(sentiments)
        avg_polarity = round(sum(polarities) / total, 2) if total else 0
        summary = {
            "total": total,
            "positive": sentiment_counts.get("Positive", 0),
            "neutral": sentiment_counts.get("Neutral", 0),
            "negative": sentiment_counts.get("Negative", 0),
            "avg_polarity": avg_polarity
        }

    return render_template('analysis.html', searchString=searchString, summary=summary,
                           sentiment_img=sentiment_img_filename, wordfreq_img=wordfreq_img_filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
