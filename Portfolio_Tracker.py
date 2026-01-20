import streamlit as st
import pandas as pd
import yfinance as yf
import os

st.title("Portfolio Tracker")

PORTFOLIO_FILE = "portfolio.csv"

def normalize_symbol(symbol):
    if not isinstance(symbol, str):
        return None
    symbol = symbol.strip().upper()
    if symbol == "":
        return None
    if not symbol.endswith(".NS"):
        symbol += ".NS"
    return symbol


def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    return pd.DataFrame(columns=["Symbol", "Average Price", "Quantity"])


st.subheader("You would love to upload CSV or Manually Enter your Holdings?")

mode = st.radio("Choose one option:",["Upload CSV", "Enter Manually"])

if mode == "Upload CSV":
    uploaded_file = st.file_uploader("Upload your portfolio CSV",type=["csv"])

    if uploaded_file:
        portfolio = pd.read_csv(uploaded_file)
        save_portfolio(portfolio)
        st.success("CSV uploaded and loaded successfully.")
    else:
        st.info("Please upload a CSV file.")
        st.stop()

else:
    portfolio = load_portfolio()
    st.info("Enter holdings manually below.")

st.subheader("Enter Your Holdings Manyally")

portfolio = st.data_editor(
    portfolio,
    num_rows="dynamic",
    use_container_width=True
)

if st.button("Save Portfolio"):
    portfolio["Symbol"] = portfolio["Symbol"].apply(normalize_symbol)
    portfolio["Average Price"] = pd.to_numeric(portfolio["Average Price"], errors="coerce")
    portfolio["Quantity"] = pd.to_numeric(portfolio["Quantity"], errors="coerce")

    portfolio = portfolio.dropna(subset=["Symbol", "Average Price", "Quantity"])

    save_portfolio(portfolio)

    st.success("Portfolio saved successfully!")

if st.button("Analyze Portfolio"):

    if portfolio.empty:
        st.warning("Portfolio is empty.")
        st.stop()

    symbols = portfolio["Symbol"].unique().tolist()

    with st.spinner("Fetching live prices..."):
        data = yf.download(symbols, period="1d", group_by="ticker", progress=False)

    price_map = {}
    for symbol in symbols:
        try:
            if len(symbols) == 1:
                price_map[symbol] = data["Close"].iloc[-1]
            else:
                price_map[symbol] = data[symbol]["Close"].iloc[-1]
        except:
            price_map[symbol] = None

    portfolio["Current Price"] = portfolio["Symbol"].map(price_map)
    portfolio["Invested Value"] = portfolio["Average Price"] * portfolio["Quantity"]
    portfolio["Current Value"] = portfolio["Current Price"] * portfolio["Quantity"]
    portfolio["P&L"] = portfolio["Current Value"] - portfolio["Invested Value"]
    portfolio["P&L %"] = (portfolio["P&L"] / portfolio["Invested Value"]) * 100

    st.subheader("Portfolio Analysis")
    st.dataframe(portfolio, use_container_width=True)

    total_invested = portfolio["Invested Value"].sum()
    total_current = portfolio["Current Value"].sum()
    total_pnl = portfolio["P&L"].sum()
    total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Invested", f"₹{total_invested:,.2f}")
    with c2:
        st.metric("Current Value", f"₹{total_current:,.2f}")
    with c3:
        st.metric("Total P&L", f"₹{total_pnl:,.2f}")
    with c4:
        st.metric("Return %", f"{total_pnl_pct:.2f}%")
