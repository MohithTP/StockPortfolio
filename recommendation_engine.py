from decimal import Decimal
import psycopg2
from psycopg2 import extras

DB_CONFIG = {
    "host": "127.0.0.1",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": 5400
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def analyze_portfolio(user_id):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        
        # 1. Fetch User Cash & Total Holdings
        cur.execute('SELECT cash_balance FROM "User" WHERE user_id = %s', (user_id,))
        res_cash = cur.fetchone()
        cash_balance = float(res_cash[0]) if res_cash else 0.0

        query = """
            SELECT p.total_quantity, s.current_price, s.sector, s.symbol, s.stock_id, p.avg_buy_price
            FROM Portfolio p
            JOIN Stock s ON p.stock_id = s.stock_id
            WHERE p.user_id = %s AND p.total_quantity > 0
        """
        cur.execute(query, (user_id,))
        holdings = cur.fetchall()
        
        # 2. Calculate Total Value and Sector Allocation
        total_value = 0.0
        sector_values = {}
        for h in holdings:
            val = float(h['total_quantity']) * float(h['current_price'])
            section = h['sector'] or 'Unclassified'
            total_value += val
            sector_values[section] = sector_values.get(section, 0.0) + val
            
        # 3. Analyze Balance
        if total_value == 0:
            return {
                "status": "empty",
                "message": "Portfolio is empty. Begin with a foundation in Technology or Finance using your cash reserves."
            }
            
        # V2 Strategic Targets
        targets = {
            "Technology": 25, "Finance": 25,
            "Healthcare": 15, "Energy": 15,
            "Consumer": 10, "Unclassified": 10
        }
        
        messages = []
        action = "HOLD"
        suggested_stock = "ETF"
        suggested_sector = None
        amount = 0

        # Overweight Check
        overweight_sector = None
        highest_divergence = 0
        for sector, target_pct in targets.items():
            current_pct = (sector_values.get(sector, 0) / total_value) * 100
            if current_pct > (target_pct + 15):
                div = current_pct - target_pct
                if div > highest_divergence:
                    highest_divergence = div
                    overweight_sector = sector

        if overweight_sector:
            cur.execute("""
                SELECT s.symbol, b.lot_id, b.buy_date
                FROM BuyLot b
                JOIN Stock s ON b.stock_id = s.stock_id
                WHERE s.sector = %s AND b.user_id = %s AND b.remaining_quantity > 0
                ORDER BY b.buy_date ASC LIMIT 1
            """, (overweight_sector, user_id))
            target_lot = cur.fetchone()
            if target_lot:
                from datetime import date
                is_long_term = (date.today() - target_lot['buy_date']).days > 365
                tax_msg = " (LTCG Eligible - Tax Efficient)" if is_long_term else ""
                messages.append(f"Strategic Trim: Portfolio is {highest_divergence:.1f}% overweight in {overweight_sector}.")
                messages.append(f"Consider scaling back **{target_lot['symbol']}**{tax_msg} to rebalance.")

        # Underweight Check
        underweight_sector = None
        max_gap = 0
        for sector, target_pct in targets.items():
            current_pct = (sector_values.get(sector, 0) / total_value) * 100
            gap = target_pct - current_pct
            if gap > 10:
                if gap > max_gap:
                    max_gap = gap
                    underweight_sector = sector

        if underweight_sector and cash_balance > 25000:
            cur.execute("""
                SELECT symbol, name, current_price, day_change 
                FROM Stock 
                WHERE sector = %s 
                AND stock_id NOT IN (SELECT stock_id FROM Portfolio WHERE user_id = %s)
                ORDER BY momentum_score DESC LIMIT 1
            """, (underweight_sector, user_id))
            pick = cur.fetchone()
            if pick:
                suggested_stock = f"{pick['name']} ({pick['symbol']})"
                suggested_sector = underweight_sector
                action = "BUY"
                amount = min(cash_balance - 10000, 50000)
                messages.append(f"Strategic Entry: {underweight_sector} is underweight by {max_gap:.1f}%.")
                messages.append(f"With ₹{cash_balance:,.0f} cash available, **{suggested_stock}** is a top momentum candidate.")
        elif cash_balance <= 25000 and underweight_sector:
            messages.append(f"Allocation for {underweight_sector} is low, but maintaining cash reserves (₹{cash_balance:,.0f}) is prioritized.")

        final_msg = " ".join(messages) if messages else "Portfolio is optimally aligned with Strategic V2 Targets."
        
        return {
            "status": "success",
            "action": action,
            "sector": suggested_sector,
            "suggested_stock": suggested_stock,
            "amount": amount,
            "reason": final_msg
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()
