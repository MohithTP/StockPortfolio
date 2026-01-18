# Finnex | Intelligent Portfolio Management

**Finnex** is a professional-grade stock portfolio management platform designed for the modern investor. It combines real-time market tracking with a **Strategic AI Engine (V2)** to provide institutional-level insights, automated rebalancing, and tax-efficient trade execution.

![Finnex Dashboard](frontend/landing_hero_dashboard.png)

## 🚀 Key Features

### 🧠 Finnex AI Engine (V2)
- **Strategic Asset Allocation**: Automatically targets optimal sector weights (e.g., 25% Tech, 15% Healthcare).
- **Momentum Scoring**: Ranks stocks based on volatility-adjusted momentum to find the best growth candidates.
- **Cash-Aware Logic**: Recommends buys only when safe cash buffers (₹10k+) are maintained.

### ⚖️ Tax Optimization
- **FIFO Accounting**: Tracks every buy/sell lot using First-In-First-Out logic.
- **LTCG Intelligence**: Automatically identifies holdings eligible for **Long Term Capital Gains** tax benefits (held > 1 year) to minimize tax liability when selling.

### 🛡️ Admin Secure Portal
- **Dedicated Console**: Separate, secure login at `/admin`.
- **Database Visualizer**: Full-width, read-only view of all system relations (Users, Stocks, Portfolios, Transactions).

### ⚡ Performance
- **Batch Market Sync**: Updates 50+ stock prices in seconds using batched Yahoo Finance requests.
- **Instant Insights**: AI recommendations load in < 1 second.

## 🛠️ Tech Stack
- **Backend**: Python, Flask
- **Database**: SQLite (Production-ready schema)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (Glassmorphism Design)
- **Data Source**: Yahoo Finance API (`yfinance`)

## 📦 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/finnex.git
   cd finnex
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # OR if using uv
   uv sync
   ```

3. **Initialize the Database**
   ```bash
   python init_db.py
   ```

4. **Seed Market Data**
   ```bash
   python populate_stocks.py
   python MarketData.py
   ```

5. **Run the Server**
   ```bash
   python app.py
   ```

6. **Access the App**
   - **Dashboard**: `http://127.0.0.1:5000`
   - **Admin Portal**: `http://127.0.0.1:5000/admin`

## 🔑 Default Credentials

- **User Portal**:
  - Email: `mohith@example.com`
  - Password: `password123`

- **Admin Portal**:
  - Username: `admin`
  - Security Key: `fox_admin_2026`

## 🎨 Design Philosophy
Finnex features a **Glassmorphism** UI style with:
- Translucent, frosted-glass cards.
- Dynamic gradients and shadows.
- Responsive, mobile-first layout.
- "Outfit" and "Inter" typography for a premium financial feel.

---
&copy; 2026 Finnex Inc. | Dept of AIML
