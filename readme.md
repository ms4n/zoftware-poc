# Zoftware POC

A web scraping and product management platform with FastAPI backend, React frontend, and Scrapy-based scrapers.

## Index

- [API Setup](#api-setup)
- [Dashboard Client Setup](#dashboard-client-setup)
- [Scraper Setup](#scraper-setup)
- [Known Blockers](#known-blockers)

## API Setup

1. **Create and activate virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API:**
   ```bash
   cd api
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Dashboard Client Setup

1. **Install dependencies:**

   ```bash
   cd client
   npm install
   ```

2. **Run the development server:**
   ```bash
   npm run dev
   ```

The client will be available at `http://localhost:5173`

## Scraper Setup

1. **Create and activate virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   > **Note**: If you already installed packages in the API setup step, no need to install again.

3. **Configure proxies (optional):**

   If using rotating proxies, create `scraper/proxies_formatted.csv` with format:

   ```csv
   ip_address,port,username,password
   192.168.1.100,8080,user123,pass456
   10.0.0.50,3128,proxy_user,proxy_pass
   ```

4. **Run scrapers from project root:**

   **G2 Scraper:**

   ```bash
   python -m scraper.engine.main g2
   ```

   **Capterra Scraper:**

   ```bash
   python -m scraper.engine.main capterra
   ```

## Known Blockers

### Cloudflare Enterprise Protection

**Problem**: Capterra uses advanced Cloudflare protection that blocks automation attempts.

**Evidence**: Simple requests return "Attention Required! | Cloudflare" page.

**Solution**: Use `undetected-chromedriver` instead of Playwright for complete bypass.

### Headless Mode Detection

**Problem**: Cloudflare applies stricter detection for headless browsers.

**Solution**: Use headful mode (visible browser) for successful scraping.
