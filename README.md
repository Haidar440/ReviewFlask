# 🖼️ Web Image Scraper

A **Flask + Selenium-based Web Scraper** that fetches images from the web based on user queries and displays them in a clean UI.  
The project is also deployed on **Azure App Service**.

---

## 🔗 Project Link
👉 [Live Demo on Azure](https://scapper-bye5cuhhcjgpaub2.canadacentral-01.azurewebsites.net/)

---

## 📸 Screenshot
### 🔹 Homepage
<img width="1918" height="875" alt="image" src="https://github.com/user-attachments/assets/39d161d9-72b2-4a33-a3f2-92057bb1473e" />

### 🔹 Results Page
<img width="1885" height="870" alt="image" src="https://github.com/user-attachments/assets/2a32ada5-b57e-4315-9a56-7b7a2032e290" />



---

## 📖 Description
This project is a simple **Web Scraper** built with **Python, Flask, Selenium, and MongoDB (Cloud)**.  
It allows users to:
- Enter a keyword (e.g., "cats", "cars").
- Fetch multiple image URLs.
- Store and retrieve data from **MongoDB Atlas**.
- Display results in a web interface.

---

## ✨ Features
- 🔍 Search and scrape review automatically.  
- 🌐 Deployed on **Azure Web App**.  
- 🎨 User-friendly UI with **HTML + CSS + DataTables**.  
- 🖥️ Works both locally and on the cloud.  

---

## 🛠️ Technologies Used
- **Python** (Flask, Selenium, Requests, Dotenv)  
- **Azure App Service** (Deployment)  
- **HTML, CSS, JavaScript, jQuery, DataTables**  
- **ChromeDriver (Selenium WebDriver)**  

---

## ⚙️ Setup Instructions (Run Locally)

Follow these steps to run the project on your local machine:

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Haidar440/ReviewFlask.git
cd ReviewFlask
```
### 2️⃣ Create Virtual Environment
```bash
# Using Conda
conda create -n scraper-env python=3.12 -y
conda activate scraper-env

# OR using venv
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```
### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
### 4️⃣ Run the Application
```bash
python app.py
```
🚀 The app will run at:
👉 http://127.0.0.1:8000/

### ✅ For File / Folder Structure
```plaintext
web-image-scraper/
│── static/              # CSS, JS, Images
│── templates/           # HTML Templates
│── app.py               # Flask main app
│── scraper.py           # Image scraping logic
│── requirements.txt     # Dependencies
│── .env                 # Environment variables
│── README.md
```


