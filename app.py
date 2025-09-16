import time
import threading
import pandas as pd
from flask import Flask, render_template_string, Response

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)

latest_df = pd.DataFrame()
previous_df = pd.DataFrame()
interval = 180  # scrape every 3 minutes

# =========================
# Headless Selenium Setup
# =========================
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")

    # If chromedriver is in PATH, no need to specify Service path
    return webdriver.Chrome(options=chrome_options)

driver = init_driver()

# =========================
# Sector Map (shortened – extend as needed)
# =========================
sector_map = {
    # Energy
    "ADANIGREEN": "Energy","IOC": "Energy","POWERGRID": "Energy","CGPOWER": "Energy",
    "ADANIENSOL": "Energy","NHPC": "Energy","BPCL": "Energy","IGL": "Energy",
    "JSWENERGY": "Energy","NTPC": "Energy","PETRONET": "Energy","BDL": "Energy",
    "ONGC": "Energy","SOLARINDS": "Energy","GMRAIRPORT": "Energy","INOXWIND": "Energy",
    "COALINDIA": "Energy","IREDA": "Energy","TORNTPOWER": "Energy","MAZDOCK": "Energy",
    "OIL": "Energy","BLUESTARCO": "Energy","RELIANCE": "Energy","TATAPOWER": "Energy",

    # Realty
    "OBEROIRLTY": "Realty","NBCC": "Realty","GODREJPROP": "Realty","DLF": "Realty",
    "PHOENIXLTD": "Realty","NCC": "Realty","PRESTIGE": "Realty","LODHA": "Realty",

    # Auto
    "SONACOMS": "Auto","BOSCHLTD": "Auto","BAJAJ-AUTO": "Auto","ASHOKLEY": "Auto",
    "TVSMOTOR": "Auto","EICHERMOT": "Auto","UNOMINDA": "Auto","TATAMOTORS": "Auto",
    "M&M": "Auto","MARUTI": "Auto","TIINDIA": "Auto","BHARATFORG": "Auto",
    "EXIDEIND": "Auto","HEROMOTOCO": "Auto","MOTHERSON": "Auto","TITAGARH": "Auto",

    # IT
    "OFSS": "IT","KPITTECH": "IT","TAMS": "IT","PERSISTENT": "IT",
    "HFCL": "IT","MPHASIS": "IT","CYIENT": "IT","TATAELXSI": "IT",
    "TATATECH": "IT","LTIM": "IT","TECHM": "IT","WIPRO": "IT",
    "COFORGE": "IT","TCS": "IT","HCLTECH": "IT","INFY": "IT",
    "LTTS": "IT","KAYNES": "IT",

    # Pharma
    "AUROPHARMA": "Pharma","GLENMARK": "Pharma","LUPIN": "Pharma","ALKEM": "Pharma",
    "LAURUSLABS": "Pharma","BIOCON": "Pharma","ZYDUSLIFE": "Pharma","TORNTPHARM": "Pharma",
    "FORTIS": "Pharma","DIVISLAB": "Pharma","SUNPHARMA": "Pharma","DRREDDY": "Pharma",
    "MANKIND": "Pharma","CIPLA": "Pharma","PPLPHARMA": "Pharma",

    # Pvt Bank
    "AXISBANK": "Pvt_Bank","FEDERALBNK": "Pvt_Bank","KOTAKBANK": "Pvt_Bank",
    "BANDHANBNK": "Pvt_Bank","INDUSINDBK": "Pvt_Bank","IDFCFIRSTB": "Pvt_Bank",
    "ICICIBANK": "Pvt_Bank","RBLBANK": "Pvt_Bank","HDFCBANK": "Pvt_Bank",

    # Fin Service
    "ANGELONE": "Fin_Service","BSE": "Fin_Service","SHRIRAMFIN": "Fin_Service",
    "CHOLAFIN": "Fin_Service","ICICIPRULI": "Fin_Service","SBICARD": "Fin_Service",
    "POLICYBZR": "Fin_Service","CDSL": "Fin_Service","SBILIFE": "Fin_Service",
    "PAYTM": "Fin_Service","ICICIGI": "Fin_Service","IIFL": "Fin_Service",
    "HDFCLIFE": "Fin_Service","IRFC": "Fin_Service","BAJAJFINSV": "Fin_Service",

    # FMCG
    "BRITANNIA": "FMCG","ETERNAL": "FMCG","HINDUNILVR": "FMCG","PATANJALI": "FMCG",
    "SUPREMEIND": "FMCG","COLPAL": "FMCG","DMART": "FMCG","UNITDSPR": "FMCG",
    "MARICO": "FMCG","ITC": "FMCG","TATACONSUM": "FMCG","NESTLEIND": "FMCG",
    "DABUR": "FMCG","KALYANKJIL": "FMCG","NYKAA": "FMCG","VBL": "FMCG","GODREJCP": "FMCG",

    # Cement
    "AMBUJACEM": "Cement","SHREECEM": "Cement","ULTRACEMCO": "Cement","DALBHARAT": "Cement",

    # Nifty Mid Select
    "HINDPETRO": "NiftyMidSel","FEDERALBNK": "NiftyMidSel","LUPIN": "NiftyMidSel",
    "POLYCAB": "NiftyMidSel","CONCOR": "NiftyMidSel","VOLTAS": "NiftyMidSel",
    "ASHOKLEY": "NiftyMidSel","PIIND": "NiftyMidSel","PERSISTENT": "NiftyMidSel",
    "INDHOTEL": "NiftyMidSel","JUBLFOOD": "NiftyMidSel","MPHASIS": "NiftyMidSel",
    "ASTRAL": "NiftyMidSel","RVNL": "NiftyMidSel","GODREJPROP": "NiftyMidSel",
    "PAGEIND": "NiftyMidSel","HDFCAMC": "NiftyMidSel","AUROPHARMA": "NiftyMidSel",

    # Metal
    "NATIONALUM": "Metal","ADANIENT": "Metal","HINDZINC": "Metal","NMDC": "Metal",
    "SAIL": "Metal","APLAPOLLO": "Metal","JSWSTEEL": "Metal","VEDL": "Metal",
    "JINDALSTEL": "Metal","TATASTEEL": "Metal","HINDALCO": "Metal",

    # PSU Bank
    "BANKINDIA": "Psu_Bank","UNIONBANK": "Psu_Bank","PNB": "Psu_Bank",
    "CANBK": "Psu_Bank","BANKBARODA": "Psu_Bank","INDIANB": "Psu_Bank","SBIN": "Psu_Bank",
}

# =========================
# Scraper
# =========================
def scrape_intraday_boost():
    url = "https://tradefinder.in/market-pulse"  # 🔴 Replace with actual site URL
    driver.get(url)
    time.sleep(5)  # wait for table to load

    table = driver.find_element(By.ID, "depth_2_intradayboost")
    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        cols = [col.text.strip() for col in cols]
        if cols:
            data.append(cols)
    df = pd.DataFrame(data, columns=["Symbol", "LTP", "PreC", "Perc", "RFac"])
    return df


def process_data(df, prev_df):
    df = df.copy()
    df["Sector"] = df["Symbol"].map(sector_map).fillna("")

    if prev_df.empty:
        df["Old Position"] = "New"
        df["Movement"] = "New"
        return df

    prev_symbols = prev_df["Symbol"].tolist()
    old_positions, movements = [], []

    for idx, sym in enumerate(df["Symbol"], start=1):
        if sym not in prev_symbols:
            old_positions.append("New")
            movements.append("New")
        else:
            old_idx = prev_symbols.index(sym) + 1
            old_positions.append(old_idx)
            if idx < old_idx:
                movements.append("Moved Up")
            elif idx > old_idx:
                movements.append("Moved Down")
            else:
                movements.append("Same")

    df["Old Position"] = old_positions
    df["Movement"] = movements
    return df


def background_scraper():
    global latest_df, previous_df
    while True:
        try:
            raw_df = scrape_intraday_boost()
            processed_df = process_data(raw_df, previous_df)
            previous_df = raw_df
            latest_df = processed_df
            print(f"✅ Scraped at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print("⚠️ Error scraping:", e)
        time.sleep(interval)

# =========================
# Flask Routes
# =========================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Intraday Boost Monitor</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        h1 { text-align: center; }
        .up { background-color: #c6efce; }
        .down { background-color: #ffc7ce; }
        .same { background-color: #d9d9d9; }
        .new { background-color: #bdd7ee; }
    </style>
</head>
<body>
    <h1>📈 Intraday Boost Monitor</h1>
    {% if not df.empty %}
        <p>Last updated: {{ updated }}</p>
        <table>
            <tr>
                {% for col in df.columns %}
                    <th>{{ col }}</th>
                {% endfor %}
            </tr>
            {% for row in df.values %}
                <tr>
                    {% for i, col in enumerate(row) %}
                        {% if df.columns[i] == "Movement" %}
                            {% if col == "Moved Up" %}
                                <td class="up">{{ col }}</td>
                            {% elif col == "Moved Down" %}
                                <td class="down">{{ col }}</td>
                            {% elif col == "Same" %}
                                <td class="same">{{ col }}</td>
                            {% elif col == "New" %}
                                <td class="new">{{ col }}</td>
                            {% else %}
                                <td>{{ col }}</td>
                            {% endif %}
                        {% else %}
                            <td>{{ col }}</td>
                        {% endif %}
                    {% endfor %}
                </tr>
            {% endfor %}
        </table>
    {% else %}
        <p>No data yet...</p>
    {% endif %}
    <br>
    <a href="/download">⬇️ Download CSV</a>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, df=latest_df, updated=time.strftime("%H:%M:%S"))

@app.route("/download")
def download_csv():
    if latest_df.empty:
        return "No data yet"
    csv_data = latest_df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=intraday_boost.csv"}
    )

# =========================
# Run App
# =========================
if __name__ == "__main__":
    t = threading.Thread(target=background_scraper, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
