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

Live Demo : https://india-in-the-world.onrender.com/

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
## Data Source
### World Bank
Fetched via REST API (`api.worldbank.org`):
- GDP
- Annual GDP Growth
- GDP per Capita
- GDP per Capita PPP 
- Debt to GDP Ratio
- Population
- Inflation Rate
- Unemployment Rate
- Life Expectancy
- Fertility Rate
- Urbanization Rate
- Gini Coefficient
- Control of Corruption
- Homicide Rate

### Our World in Data
Downloaded as CSV files (`ourworldindata.org`):
- Human Development Index
- The Economist Democracy Index
- Self-Reported Life Satisfaction
- Median Age
- Gender Inequality Index

### Reporters Without Borders
Downloaded as CSV files `rsf.org`:
- Press Freedom Index


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
  <i>Built with ❤️ By Md Amanullah</i>
</div>
