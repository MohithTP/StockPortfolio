import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": 5400
}

COMMANDS = [
    "DROP TABLE IF EXISTS RealizedGain CASCADE",
    "DROP TABLE IF EXISTS BuyLot CASCADE",
    "DROP TABLE IF EXISTS Transaction CASCADE",
    "DROP TABLE IF EXISTS Portfolio CASCADE",
    "DROP TABLE IF EXISTS Stock CASCADE",
    "DROP TABLE IF EXISTS \"User\" CASCADE",
    
    # Users
    """
    CREATE TABLE "User" (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        cash_balance DECIMAL(15, 2) DEFAULT 1000000.00
    )
    """,
    # Stock
    """
    CREATE TABLE Stock (
        stock_id SERIAL PRIMARY KEY,
        symbol VARCHAR(10) UNIQUE NOT NULL,
        name VARCHAR(100),
        sector VARCHAR(50),
        current_price DECIMAL(10, 2) NOT NULL
    )
    """,
    # Portfolio
    """
    CREATE TABLE Portfolio (
        user_id INTEGER REFERENCES "User"(user_id),
        stock_id INTEGER REFERENCES Stock(stock_id),
        total_quantity INTEGER DEFAULT 0,
        avg_buy_price DECIMAL(10, 2),
        PRIMARY KEY (user_id, stock_id)
    )
    """,
    # Transaction
    """
    CREATE TABLE Transaction (
        txn_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES "User"(user_id),
        stock_id INTEGER REFERENCES Stock(stock_id),
        txn_type VARCHAR(10) NOT NULL,
        quantity INTEGER NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        txn_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # BuyLot
    """
    CREATE TABLE BuyLot (
        lot_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES "User"(user_id),
        stock_id INTEGER REFERENCES Stock(stock_id),
        buy_date DATE NOT NULL,
        buy_price DECIMAL(10, 2) NOT NULL,
        initial_quantity INTEGER NOT NULL,
        remaining_quantity INTEGER NOT NULL
    )
    """,
    # RealizedGain (For Tax Analysis)
    """
    CREATE TABLE RealizedGain (
        gain_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES "User"(user_id),
        stock_id INTEGER REFERENCES Stock(stock_id),
        buy_lot_id INTEGER REFERENCES BuyLot(lot_id),
        quantity INTEGER NOT NULL,
        buy_date DATE NOT NULL,
        sell_date DATE NOT NULL,
        buy_price DECIMAL(10, 2) NOT NULL,
        sell_price DECIMAL(10, 2) NOT NULL,
        total_gain DECIMAL(15, 2) NOT NULL,
        term VARCHAR(10) NOT NULL -- 'SHORT' or 'LONG'
    )
    """,
    # Seeds
    """
    INSERT INTO Stock (symbol, sector, current_price) VALUES
        ('RELIANCE', 'Energy', 2950.00),
        ('TCS', 'Technology', 3850.00),
        ('HDFCBANK', 'Finance', 1650.00),
        ('INFY', 'Technology', 1520.00),
        ('BHARTIARTL', 'Telecom', 1200.00),
        ('ICICIBANK', 'Finance', 1080.00)
    ON CONFLICT (symbol) DO NOTHING
    """
]

def init_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Connected to DB on port 5400.")
        
        for i, cmd in enumerate(COMMANDS):
            print(f"Executing command {i+1}...")
            cur.execute(cmd)
        
        conn.commit()
        print("Database initialized successfully!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
