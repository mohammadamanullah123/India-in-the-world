<p align="center">
  <img src="src/public/favicons/india_favicon.png" alt="India in the World" width="150">
</p>

# India in the World

An interactive dashboard for exploring and comparing global statistics across countries and years, with a special focus on visualizing India's position in the global context. Visualize relationships between economic, social, and governance indicators through scatterplots, timelines, maps, and data tables. 

This project also features an AI-powered Insights Panel powered by **Google Gemini AI**, which provides instant analytical context for selected country data.

## Data Sources

All data is aggregated from authoritative international sources.

Read more on http://dataofthe.world/indicators

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

## Collecting Data

Data collection scripts are in `data_collection/`. You need Python with Jupyter and pandas.

1. **Run the notebooks** (in any order):
   ```
   data_collection/world_bank.ipynb
   data_collection/our_world_in_data.ipynb
   data_collection/reporters_without_borders.ipynb
   ```
   These fetch data and save JSON files to `data_collection/data/`.

2. **Build the database**:
   ```bash
   python data_collection/create_database.py
   ```
   This creates `dataoftheworld.db` SQLite database from the collected JSON files.

## Setup & Running Locally

Before running the application, make sure to set up your `.env` file in the `src` folder:
```bash
# src/.env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Option 1: Running with Docker Compose (Recommended)

1. Ensure your `.env` file is created in the `src` folder.
2. Run the following command from the root directory:
```bash
docker-compose up -d --build
```
The application will run securely in the background on port `8004`.

### Option 2: Running Locally with Node.js

1. Navigate to the `src` directory:
   ```bash
   cd src
   ```
2. Install the dependencies:
   ```bash
   npm install
   ```
3. Start the server:
   ```bash
   npm start
   ```
The app will be accessible at `http://localhost:8004`.

## Deployment

To deploy this project to a VPS (Virtual Private Server like DigitalOcean, AWS EC2, or Hostinger):
1. **Connect** to your VPS via SSH.
2. **Clone** this repository to the server.
3. **Configure Environment**: Create the `.env` file in the `src/` directory with your actual `GEMINI_API_KEY`.
4. **Deploy**: Run `docker-compose up -d --build`.

*(Note: The `.env` file is safely ignored during the Docker build process via `.dockerignore` to prevent leaking API keys, and is read via the `docker-compose.yml` `env_file` setting at runtime.)*

## Tech Stack

- **Backend:** Node.js, Express, SQLite3
- **Frontend:** HTML/CSS/JS, D3.js
- **AI Integration:** Google Gemini AI
- **Data Collection:** Python, Jupyter, pandas
