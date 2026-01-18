import psycopg2
from psycopg2 import extras
import random

# Database Config
DB_CONFIG = {
    "host": "127.0.0.1",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": 5400
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# Stock Data: 20 companies per sector
sectors_data = {
    "Technology": [
        ("TCS", "Tata Consultancy Services", 3850.00), ("INFY", "Infosys Ltd", 1520.00), ("HCLTECH", "HCL Technologies", 1600.00),
        ("WIPRO", "Wipro Ltd", 480.00), ("LTIM", "LTIMindtree", 5100.00), ("TECHM", "Tech Mahindra", 1300.00),
        ("MPHASIS", "Mphasis Ltd", 2400.00), ("COFORGE", "Coforge Ltd", 6200.00), ("PERSISTENT", "Persistent Systems", 7800.00),
        ("OFSS", "Oracle Financial Services", 8500.00), ("KPITTECH", "KPIT Technologies", 1500.00), ("TATAELXSI", "Tata Elxsi", 7500.00),
        ("CYIENT", "Cyient Ltd", 1900.00), ("ZENSARTECH", "Zensar Technologies", 600.00), ("SONATSOFTW", "Sonata Software", 750.00),
        ("BIRLASOFT", "Birlasoft Ltd", 700.00), ("INTELLECT", "Intellect Design", 1000.00), ("BSOFT", "Birlasoft Ltd", 720.00),
        ("MASTEK", "Mastek Ltd", 2800.00), ("NEWGEN", "Newgen Software", 850.00)
    ],
    "Finance": [
        ("HDFCBANK", "HDFC Bank Ltd", 1650.00), ("ICICIBANK", "ICICI Bank Ltd", 1080.00), ("SBIN", "State Bank of India", 770.00),
        ("AXISBANK", "Axis Bank Ltd", 1100.00), ("KOTAKBANK", "Kotak Mahindra Bank", 1820.00), ("BAJFINANCE", "Bajaj Finance Ltd", 6500.00),
        ("BAJAJFINSV", "Bajaj Finserv Ltd", 1600.00), ("INDUSINDBK", "IndusInd Bank", 1500.00), ("HDFCLIFE", "HDFC Life Insurance", 630.00),
        ("SBILIFE", "SBI Life Insurance", 1500.00), ("CHOLAFIN", "Cholamandalam Inv", 1250.00), ("MUTHOOTFIN", "Muthoot Finance", 1600.00),
        ("SHRIRAMFIN", "Shriram Finance", 2400.00), ("M&MFIN", "M&M Financial Services", 280.00), ("LICHSGFIN", "LIC Housing Finance", 650.00),
        ("IDFCFIRSTB", "IDFC First Bank", 80.00), ("FEDERALBNK", "Federal Bank", 160.00), ("AUBANK", "AU Small Finance Bank", 600.00),
        ("BANDHANBNK", "Bandhan Bank", 190.00), ("PNB", "Punjab National Bank", 120.00)
    ],
    "Healthcare": [
        ("SUNPHARMA", "Sun Pharmaceutical", 1550.00), ("DRREDDY", "Dr Reddys Labs", 6200.00), ("CIPLA", "Cipla Ltd", 1450.00),
        ("APOLLOHOSP", "Apollo Hospitals", 6200.00), ("DIVISLAB", "Divis Laboratories", 3700.00), ("MAXHEALTH", "Max Healthcare", 800.00),
        ("MANKIND", "Mankind Pharma", 2200.00), ("ZYDUSLIFE", "Zydus Lifesciences", 950.00), ("TORNTPHARM", "Torrent Pharma", 2600.00),
        ("LUPIN", "Lupin Ltd", 1600.00), ("AUROPHARMA", "Aurobindo Pharma", 1100.00), ("ALKEM", "Alkem Laboratories", 5200.00),
        ("ABBOTINDIA", "Abbott India", 28000.00), ("BIOCON", "Biocon Ltd", 280.00), ("IPCALAB", "Ipca Laboratories", 1300.00),
        ("GLENMARK", "Glenmark Pharma", 900.00), ("LAURUSLABS", "Laurus Labs", 420.00), ("SYNGENE", "Syngene International", 750.00),
        ("FORTIS", "Fortis Healthcare", 450.00), ("GRANULES", "Granules India", 430.00)
    ],
    "Energy": [
        ("RELIANCE", "Reliance Industries", 2950.00), ("ONGC", "Oil & Natural Gas Corp", 270.00), ("NTPC", "NTPC Ltd", 350.00),
        ("POWERGRID", "Power Grid Corp", 280.00), ("COALINDIA", "Coal India Ltd", 450.00), ("BPCL", "Bharat Petroleum", 600.00),
        ("IOC", "Indian Oil Corp", 170.00), ("GAIL", "GAIL (India) Ltd", 190.00), ("ADANIGREEN", "Adani Green Energy", 1800.00),
        ("ADANITRANS", "Adani Energy Solutions", 1100.00), ("TATAPOWER", "Tata Power", 430.00), ("JSWENERGY", "JSW Energy", 650.00),
        ("RECLTD", "REC Ltd", 500.00), ("PFC", "Power Finance Corp", 450.00), ("NHPC", "NHPC Ltd", 95.00),
        ("SJVN", "SJVN Ltd", 125.00), ("IREDA", "IREDA Ltd", 180.00), ("OIL", "Oil India Ltd", 630.00),
        ("HPCL", "Hindustan Petroleum", 500.00), ("GUJGASLTD", "Gujarat Gas Ltd", 550.00)
    ],
    "Consumer": [
        ("HUL", "Hindustan Unilever", 2400.00), ("ITC", "ITC Ltd", 410.00), ("TITAN", "Titan Company", 3600.00),
        ("ASIANPAINT", "Asian Paints", 2850.00), ("NESTLEIND", "Nestle India", 2500.00), ("TATACONSUM", "Tata Consumer Products", 1100.00),
        ("BRITANNIA", "Britannia Industries", 4800.00), ("VBL", "Varun Beverages", 1450.00), ("PIDILITIND", "Pidilite Industries", 3000.00),
        ("GODREJCP", "Godrej Consumer Products", 1250.00), ("DABUR", "Dabur India", 530.00), ("MARICO", "Marico Ltd", 520.00),
        ("COLPAL", "Colgate-Palmolive India", 2800.00), ("PGHH", "P&G Hygiene", 17000.00), ("UBL", "United Breweries", 1800.00),
        ("MCDOWELL-N", "United Spirits", 1150.00), ("EMAMILTD", "Emami Ltd", 450.00), ("JYOTHYLAB", "Jyothy Labs", 450.00),
        ("NYKAA", "FSN E-Commerce (Nykaa)", 160.00), ("HONAUT", "Honeywell Automation", 48000.00)
    ]
}

def populate_db():
    conn = get_connection()
    cur = conn.cursor()
    
    print("Starting database population with Indian Stocks...")
    
    try:
        # 1. Schema Migration: Add 'name' column if it doesn't exist
        print("Checking/Updating schema...")
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                WHERE table_name='stock' AND column_name='name') THEN 
                    ALTER TABLE Stock ADD COLUMN name VARCHAR(100); 
                END IF; 
            END $$;
        """)
        
        # 2. Populate Data
        cur.execute("SELECT symbol FROM Stock")
        existing_symbols = {row[0] for row in cur.fetchall()}
        
        count = 0
        for sector, stocks in sectors_data.items():
            for symbol, name, price in stocks:
                final_price = price + random.uniform(-price*0.02, price*0.02) # 2% variation

                if symbol not in existing_symbols:
                    cur.execute("""
                        INSERT INTO Stock (symbol, name, sector, current_price)
                        VALUES (%s, %s, %s, %s)
                    """, (symbol, name, sector, round(final_price, 2)))
                    count += 1
                else:
                    # Update price and name for existing symbols
                    cur.execute("""
                        UPDATE Stock SET name = %s, current_price = %s, sector = %s
                        WHERE symbol = %s
                    """, (name, round(final_price, 2), sector, symbol))
        
        conn.commit()
        print(f"Successfully processed database. Added {count} new stocks.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    populate_db()
