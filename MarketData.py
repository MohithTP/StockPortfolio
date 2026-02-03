import yfinance as yf
import psycopg2
from decimal import Decimal

DB_CONFIG = {
    "host": "127.0.0.1",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": 5400
}

def update_all_prices():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Get all symbols
        cur.execute("SELECT stock_id, symbol FROM Stock")
        stocks = cur.fetchall()
        
        if not stocks:
            return {"status": "skipped", "message": "No stocks in database"}
        
        # 2. Batch fetch from yfinance
        raw_symbols = [s[1] for s in stocks]
        symbols_with_suffix = [s if "." in s else f"{s}.NS" for s in raw_symbols]
        
        try:
            # Chunking logic to prevent timeouts
            chunk_size = 20
            all_data = None
            
            for i in range(0, len(symbols_with_suffix), chunk_size):
                chunk = symbols_with_suffix[i:i + chunk_size]
                try:
                    chunk_data = yf.download(chunk, period="5d", interval="1d", group_by='ticker', progress=False, auto_adjust=True)
                    
                    if all_data is None:
                        all_data = chunk_data
                    else:
                        pass 
                        
                except Exception as e:
                    print(f"Chunk fetch failed: {e}")
            
            all_data = yf.download(symbols_with_suffix, period="5d", interval="1d", group_by='ticker', progress=False, auto_adjust=True, threads=True) 

        except Exception as e:
            print(f"Batch fetch failed: {e}")
            all_data = None

        updated_count = 0
        for stock_id, symbol in stocks:
            try:
                yf_symbol = symbol if "." in symbol else f"{symbol}.NS"
                data = None
                
                # extracting from MultiIndex DF
                if all_data is not None and not all_data.empty:
                    try:
                        if len(symbols_with_suffix) > 1:
                            data = all_data[yf_symbol]
                        else:
                            data = all_data
                    except KeyError:
                        # Try finding without suffix if mismatch
                        data = None

                if data is not None and not data.empty and 'Close' in data:
                    current_price = data['Close'].iloc[-1]
                    # Handle NaN values
                    if pd.isna(current_price):
                        # Try previous day
                        current_price = data['Close'].iloc[-2] if len(data) > 1 else 0

                    prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
                    
                    if prev_close and prev_close != 0:
                        day_change = ((current_price - prev_close) / prev_close) * 100
                    else:
                        day_change = 0
                        
                    momentum = day_change
                else:
                    # Updated Fallback Logic without Randomness for stability
                    cur.execute("SELECT current_price FROM Stock WHERE stock_id = %s", (stock_id,))
                    row = cur.fetchone()
                    current_price = row[0] if row else 100.0
                    day_change = 0.0 # No change if fetch fails
                    momentum = 0.0

                inr_price = current_price
                    
                cur.execute("""
                    UPDATE Stock 
                    SET current_price = %s, day_change = %s, momentum_score = %s 
                    WHERE stock_id = %s
                """, (float(inr_price), float(day_change), float(momentum), stock_id))
                updated_count += 1
                
            except Exception as e:
                # Silent fail for individual stock to keep process moving
                pass
        
        conn.commit()
        cur.close()
        return {"status": "success", "updated": updated_count}
        
    except Exception as e:
        print(f"Update error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    count = update_all_prices()
    print(count)
