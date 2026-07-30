<div align="center">
  <img src="src/public/favicons/india_favicon.png" alt="India in the World Logo" width="150" />
  
  # 🌍 India in the World

  <p>
    <strong>An Interactive Dashboard for Global Statistics & Insights</strong>
  </p>

  ![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)
  ![D3.js](https://img.shields.io/badge/D3.js-F9A03C?style=for-the-badge&logo=d3.js&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-14354C?style=for-the-badge&logo=python&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
</div>

<br />

> **India in the World** is an interactive, visually stunning dashboard designed to explore and compare global statistics across countries and years, with a special focus on India's position in the global context. 

## 📖 Short Description

Dive deep into the relationships between economic, social, and governance indicators through dynamic **scatterplots**, **timelines**, and **maps**. This project is supercharged with an **AI-powered Insights Panel** (via Google Gemini AI) that provides instant, analytical context for the data you explore, acting as your personal data analyst.

---

## ✨ Features

- 📊 **Interactive D3.js Visualizations**: Seamlessly compare data using dynamic Timelines, Choropleth Maps, and Scatterplots.
- 🤖 **AI Insights Panel**: Get contextual, real-time insights on any country's stats powered by the Google Gemini API.
- 🌍 **Extensive Datasets**: Deep metrics aggregated from the World Bank, Our World in Data, and Reporters Without Borders.
- 🌓 **Dark/Light Mode**: A beautiful, responsive UI that automatically adapts to your system themes.
- 🐳 **Dockerized Deployments**: Easy to host, build, and manage using Docker Compose.

---

## 🛠️ Tech Stack

### Frontend
- **HTML5 / CSS3 / Vanilla JS**: For a lightweight, lightning-fast UI.
- **D3.js**: The industry standard for complex, data-driven documents and SVGs.

### Backend & AI
- **Node.js & Express.js**: Robust backend server to serve the API and frontend assets.
- **SQLite3**: Lightweight, file-based database for blazingly fast querying.
- **Google Gemini AI**: Next-generation LLM for generating on-the-fly analytical insights.

### Data Collection
- **Python & Pandas**: For scraping, cleaning, and processing raw JSON/CSV files into a structured SQLite database.
- **Jupyter Notebooks**: Step-by-step interactive scripts for data extraction.

---

## 🚀 Installation Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/mohammadamanullah123/India-in-the-world.git
cd India-in-the-world
```

### 2. Configure your Environment
Create a `.env` file inside the `src/` directory and add your Google Gemini API key:
```bash
# src/.env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Choose your Setup Method

#### Option A: Using Docker Compose (Recommended)
This is the easiest way to run the app with all its dependencies out-of-the-box.
```bash
docker-compose up -d --build
```

#### Option B: Using Node.js Locally
If you prefer running the server locally without Docker:
```bash
cd src
npm install
npm start
```

---

## 💻 Usage

1. Once the application is running, open your browser and navigate to **`http://localhost:8004`**.
2. **Navigate via Tabs**: Switch between `Compare`, `Timeline`, and `Map` tabs to visualize different datasets over time.
3. **AI Insights**: Click on any country in the map or scatterplot. On the bottom right, click the **✨ Generate AI Insight** button to receive AI-generated context about that country's statistics globally.

---

## 📂 Project Structure

```text
📦 India-in-the-world
 ┣ 📂 data_collection/        # Python scripts & Notebooks for web scraping
 ┃ ┣ 📜 create_database.py    # Converts raw data to SQLite DB
 ┃ ┗ 📜 ...                   # Source notebooks (World Bank, etc.)
 ┣ 📂 src/                    # Main application source code
 ┃ ┣ 📂 data/                 # Generated SQLite database
 ┃ ┣ 📂 public/               # Frontend assets
 ┃ ┃ ┣ 📂 css/                # Stylesheets (Vanilla CSS)
 ┃ ┃ ┣ 📂 js/                 # Client-side logic & D3 implementations
 ┃ ┃ ┗ 📂 favicons/           # Branding and icons
 ┃ ┣ 📜 server.js             # Node.js backend server
 ┃ ┣ 📜 .env                  # Environment variables (Gemini API key)
 ┃ ┗ 📜 package.json          # Node dependencies
 ┣ 📜 docker-compose.yml      # Docker orchestration
 ┣ 📜 Dockerfile              # Docker image configuration
 ┗ 📜 README.md               # Project documentation
```

<br />

<div align="center">
  <i>Built with ❤️ for Global Data Analysis</i>
</div>
