from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2 import extras
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from decimal import Decimal
import MarketData

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

@app.route('/')
def home():
    return send_from_directory('frontend', 'landing.html')

@app.route('/app')
def dashboard():
    return send_from_directory('frontend', 'index.html')

@app.route('/news')
def news_page():
    return send_from_directory('frontend', 'news.html')

# --- DATABASE CONFIG ---
# --- DATABASE CONFIG ---
DB_CONFIG = {
    "host": "127.0.0.1",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": 5400
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# Helper function to make Decimal types JSON-serializable
def clean_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

# --- ENDPOINT: AUTHENTICATION ---
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        print(f"Login attempt: {data.get('email')}")
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        try:
            cur.execute('SELECT * FROM "User" WHERE email = %s', (data['email'],))
            user = cur.fetchone()
            if user and check_password_hash(user['password_hash'], data['password']):
                print(f"Login success: {user['user_id']}")
                return jsonify({
                    "status": "success", 
                    "user_id": user['user_id'], 
                    "name": user['name'],
                    "email": user['email'],
                    "cash_balance": float(user['cash_balance'])
                })
            print("Login failed: Invalid credentials")
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        cur.execute('SELECT user_id, name, email, cash_balance FROM "User" WHERE user_id = %s', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return jsonify({
                "user_id": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "cash_balance": float(user['cash_balance'])
            })
        return jsonify({"status": "error", "message": "User not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        # Join with Stock to get symbol
        query = """
            SELECT t.txn_id, t.txn_type, t.quantity, t.price, t.txn_date, s.symbol 
            FROM Transaction t
            JOIN Stock s ON t.stock_id = s.stock_id
            WHERE t.user_id = %s
            ORDER BY t.txn_date DESC
        """
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        txns = []
        for row in rows:
            d = dict(row)
            d['price'] = float(d['price'])
            d['txn_date'] = row['txn_date'].strftime('%Y-%m-%d %H:%M:%S')
            txns.append(d)
        cur.close()
        conn.close()
        return jsonify(txns)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tax_report/<int:user_id>', methods=['GET'])
def get_tax_report(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        query = """
            SELECT r.*, s.symbol 
            FROM RealizedGain r
            JOIN Stock s ON r.stock_id = s.stock_id
            WHERE r.user_id = %s
            ORDER BY r.sell_date DESC
        """
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        report = []
        summary = {"short_term_gain": 0.0, "long_term_gain": 0.0, "tax_liability": 0.0}
        
        for row in rows:
            d = dict(row)
            # Convert Decimals and Dates
            d['buy_price'] = float(d['buy_price'])
            d['sell_price'] = float(d['sell_price'])
            d['total_gain'] = float(d['total_gain'])
            d['buy_date'] = str(d['buy_date'])
            d['sell_date'] = str(d['sell_date'])
            report.append(d)
            
            if d['term'] == 'SHORT':
                summary['short_term_gain'] += d['total_gain']
            else:
                summary['long_term_gain'] += d['total_gain']
        
        # Simple Tax Calc (Example logic: 15% STCG, 10% LTCG)
        # Assuming only positive gains are taxed, but losses offset gains.
        # This is a basic estimation.
        stcg = summary['short_term_gain']
        ltcg = summary['long_term_gain']
        
        tax = (stcg * 0.15) if stcg > 0 else 0
        tax += (ltcg * 0.10) if ltcg > 0 else 0
        summary['tax_liability'] = tax
        
        cur.close()
        conn.close()
        return jsonify({"details": report, "summary": summary})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        print(f"Register attempt: {data.get('email')}")
        hashed_password = generate_password_hash(data['password'])
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO "User" (name, email, password_hash) VALUES (%s, %s, %s)',
                        (data['name'], data['email'], hashed_password))
            conn.commit()
            print("Register success")
            return jsonify({"status": "success", "message": "User registered"})
        except Exception as e:
            conn.rollback()
            print(f"Register DB Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        print(f"Register Endpoint Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT: GET PORTFOLIO ---
@app.route('/api/portfolio/<int:user_id>', methods=['GET'])
def get_portfolio(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    query = """
        SELECT s.stock_id, s.symbol, s.sector, p.total_quantity, p.avg_buy_price, s.current_price
        FROM Portfolio p
        JOIN Stock s ON p.stock_id = s.stock_id
        WHERE p.user_id = %s
    """
    cur.execute(query, (user_id,))
    rows = cur.fetchall()
    holdings = []
    for row in rows:
        d = dict(row)
        d['avg_buy_price'] = float(d['avg_buy_price'])
        d['current_price'] = float(d['current_price'])
        holdings.append(d)
    cur.close()
    conn.close()
    return jsonify(holdings)

# --- ENDPOINT: EXECUTE BUY ---
@app.route('/api/buy', methods=['POST'])
def buy_stock_api():
    data = request.json # Expects user_id, stock_id, quantity, price
    try:
        # Call the core logic function
        execute_buy(data['user_id'], data['stock_id'], data['quantity'], data['price'])
        return jsonify({"status": "success", "message": "Buy trade executed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- ENDPOINT: EXECUTE SELL (FIFO) ---
@app.route('/api/sell', methods=['POST'])
def sell_stock_api():
    data = request.json # Expects user_id, stock_id, quantity, price
    try:
        # Call the core FIFO logic function
        execute_sell_fifo(data['user_id'], data['stock_id'], data['quantity'], data['price'])
        return jsonify({"status": "success", "message": "Sell trade executed via FIFO"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- ENDPOINT: MARKET DATA ---
@app.route('/api/market/refresh', methods=['POST'])
def refresh_market_data():
    try:
        result = MarketData.update_all_prices()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT: GET ALL STOCKS (Market Overview) ---
@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        cur.execute("SELECT * FROM Stock ORDER BY symbol")
        rows = cur.fetchall()
        stocks = []
        for row in rows:
            d = dict(row)
            d['current_price'] = float(d['current_price'])
            stocks.append(d)
        cur.close()
        conn.close()
        return jsonify(stocks)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT: MARKET NEWS ---
@app.route('/api/news', methods=['GET'])
def get_market_news():
    # Mock data for demonstration
    news_items = [
        {
            "id": 1,
            "title": "Tech Stocks Rally on AI Optimism",
            "summary": "Major technology companies saw significant gains today as investor sentiment around artificial intelligence continues to drive market momentum.",
            "source": "MarketWatch",
            "time": "2 hours ago",
            "category": "Technology"
        },
        {
            "id": 2,
            "title": "Fed Signals Potential Rate Cut",
            "summary": "Federal Reserve officials hinted at a possible interest rate cut later this year if inflation data continues to show improvement.",
            "source": "Bloomberg",
            "time": "4 hours ago",
            "category": "Economy"
        },
        {
            "id": 3,
            "title": "Oil Prices Stabilize After Volatile Week",
            "summary": "Crude oil prices found a floor today after a week of volatility driven by geopolitical tensions and supply concerns.",
            "source": "Reuters",
            "time": "5 hours ago",
            "category": "Commodities"
        },
        {
            "id": 4,
            "title": "EV Sales Projected to Record Highs",
            "summary": "New industry reports suggest that electric vehicle sales are on track to hit record highs this quarter, defying earlier skepticism.",
            "source": "CNBC",
            "time": "8 hours ago",
            "category": "Automotive"
        },
         {
            "id": 5,
            "title": "Crypto Markets Flash Green",
            "summary": "Bitcoin and Ethereum surged overnight as institutional interest in digital assets appears to be renewing.",
            "source": "CoinDesk",
            "time": "12 hours ago",
            "category": "Crypto"
        }
    ]
    return jsonify(news_items)

# --- CORE LOGIC FUNCTIONS (Stage 3 Logic) ---

def execute_buy(user_id, stock_id, quantity, buy_price):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check Cash Balance
        total_cost = Decimal(quantity) * Decimal(buy_price)
        cur.execute('SELECT cash_balance FROM "User" WHERE user_id = %s', (user_id,))
        res = cur.fetchone()
        if not res:
            raise Exception("User not found")
        
        balance = res[0]
        if balance < total_cost:
            raise Exception(f"Insufficient funds. Required: ₹{total_cost}, Available: ₹{balance}")

        # Deduct Cash
        cur.execute('UPDATE "User" SET cash_balance = cash_balance - %s WHERE user_id = %s', (total_cost, user_id))

        cur.execute('INSERT INTO Transaction (user_id, stock_id, txn_type, quantity, price) VALUES (%s, %s, %s, %s, %s)',
                    (user_id, stock_id, 'BUY', quantity, buy_price))
        cur.execute('INSERT INTO BuyLot (user_id, stock_id, buy_date, buy_price, initial_quantity, remaining_quantity) VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)',
                    (user_id, stock_id, buy_price, quantity, quantity))
        cur.execute('''
            INSERT INTO Portfolio (user_id, stock_id, total_quantity, avg_buy_price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, stock_id) DO UPDATE SET
                avg_buy_price = ((Portfolio.total_quantity * Portfolio.avg_buy_price) + (EXCLUDED.total_quantity * EXCLUDED.avg_buy_price)) 
                                / (Portfolio.total_quantity + EXCLUDED.total_quantity),
                total_quantity = Portfolio.total_quantity + EXCLUDED.total_quantity
        ''', (user_id, stock_id, quantity, buy_price))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def execute_sell_fifo(user_id, stock_id, qty_to_sell, sell_price):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        cur.execute('SELECT total_quantity FROM Portfolio WHERE user_id = %s AND stock_id = %s', (user_id, stock_id))
        portfolio_record = cur.fetchone()
        if not portfolio_record or portfolio_record['total_quantity'] < qty_to_sell:
            raise Exception("Insufficient total shares.")

        cur.execute('SELECT lot_id, remaining_quantity, buy_price, buy_date FROM BuyLot WHERE user_id = %s AND stock_id = %s AND remaining_quantity > 0 ORDER BY buy_date ASC', 
                    (user_id, stock_id))
        lots = cur.fetchall()
        remaining_to_sell = qty_to_sell
        for lot in lots:
            if remaining_to_sell <= 0: break
            
            # Determine quantity from this lot
            if lot['remaining_quantity'] <= remaining_to_sell:
                qty_consumed = lot['remaining_quantity']
                cur.execute('UPDATE BuyLot SET remaining_quantity = 0 WHERE lot_id = %s', (lot['lot_id'],))
            else:
                qty_consumed = remaining_to_sell
                cur.execute('UPDATE BuyLot SET remaining_quantity = remaining_quantity - %s WHERE lot_id = %s', (remaining_to_sell, lot['lot_id']))
            
            # --- TAX CALCULATION ---
            buy_price = lot['buy_price']
            gain_per_share = Decimal(sell_price) - Decimal(buy_price)
            total_gain = gain_per_share * Decimal(qty_consumed)
            
            # Term (Short vs Long) - Simple 365 day rule
            # buy_date is python date object
            days_held = (datetime.now().date() - lot['buy_date']).days
            term = 'LONG' if days_held > 365 else 'SHORT'
            
            cur.execute('''
                INSERT INTO RealizedGain (user_id, stock_id, buy_lot_id, quantity, buy_date, sell_date, buy_price, sell_price, total_gain, term)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s)
            ''', (user_id, stock_id, lot['lot_id'], qty_consumed, lot['buy_date'], buy_price, sell_price, total_gain, term))
            # -----------------------

            remaining_to_sell -= qty_consumed

        cur.execute('UPDATE Portfolio SET total_quantity = total_quantity - %s WHERE user_id = %s AND stock_id = %s', (qty_to_sell, user_id, stock_id))
        cur.execute('INSERT INTO Transaction (user_id, stock_id, txn_type, quantity, price) VALUES (%s, %s, %s, %s, %s)', (user_id, stock_id, 'SELL', qty_to_sell, sell_price))
        
        # Add Cash
        total_sale = Decimal(qty_to_sell) * Decimal(sell_price)
        cur.execute('UPDATE "User" SET cash_balance = cash_balance + %s WHERE user_id = %s', (total_sale, user_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# --- ENDPOINT: AI RECOMMENDATIONS ---
import recommendation_engine

@app.route('/api/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        rec = recommendation_engine.analyze_portfolio(user_id)
        return jsonify(rec)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- ADMIN: AUTH & VISUALIZER ---
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "password123" # Simple for now as requested
}

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('username') == ADMIN_CREDENTIALS['username'] and data.get('password') == ADMIN_CREDENTIALS['password']:
        # In a real app, use a proper session/token. For this demo, we'll return a success flag
        # The frontend will store this in localStorage for simple gatekeeping.
        return jsonify({"status": "success", "token": "fx_admin_secret_token_2026"})
    return jsonify({"status": "error", "message": "Invalid admin credentials"}), 401

@app.route('/api/admin/tables', methods=['GET'])
def list_tables():
    # Simple token check
    auth_token = request.headers.get('Authorization')
    if auth_token != "fx_admin_secret_token_2026":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(tables)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/table/<string:table_name>', methods=['GET'])
def get_table_data(table_name):
    # Simple token check
    auth_token = request.headers.get('Authorization')
    if auth_token != "fx_admin_secret_token_2026":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        allowed_tables = [row[0] for row in cur.fetchall()]
        
        actual_table_name = table_name
        if table_name.lower() == 'user':
            actual_table_name = '"User"'
        elif table_name not in allowed_tables:
            return jsonify({"status": "error", "message": "Invalid table name"}), 400

        cur.close()
        
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        cur.execute(f"SELECT * FROM {actual_table_name}")
        rows = cur.fetchall()
        
        data = []
        for row in rows:
            d = dict(row)
            for k, v in d.items():
                if isinstance(v, Decimal):
                    d[k] = float(v)
                elif isinstance(v, (date, datetime)):
                    d[k] = v.isoformat()
            data.append(d)
            
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin')
def admin_login_page():
    return send_from_directory('frontend', 'admin_login.html')

@app.route('/admin/explorer')
def admin_explorer_page():
    return send_from_directory('frontend', 'db_visualizer.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)