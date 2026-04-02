import os

import httpx
import pandas as pd
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000/prices")
FAVICON_URL = os.getenv(
    "FAVICON_URL", "https://alexmroberts.net/assets/images/favicon.png"
)

with st.sidebar:
    st.page_link(
        "http://projects.alexmroberts.net",
        label="Back to Projects page",
    )
    st.divider()


st.set_page_config(
    page_title="Heating Oil Prices",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon=FAVICON_URL,
)


@st.cache_data(ttl=300)
def get_market_data():
    try:
        with httpx.Client() as client:
            response = client.get(API_URL, params={"limit": 500})
            response.raise_for_status()
            df = pd.DataFrame(response.json()["data"])
            if df.empty:
                return df

            df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True).dt.tz_convert(
                "US/Eastern"
            )
            return df
    except Exception as e:
        st.error(f"Data Connection Error: {e}")
        return pd.DataFrame()


st.title("Heating Oil Market Overview")
full_df = get_market_data()

if not full_df.empty:
    available_quantities = sorted(full_df["min_quantity"].unique(), reverse=True)
    selected_qty = st.sidebar.selectbox("Select Min Quantity:", available_quantities)

    snapshot = full_df[full_df["min_quantity"] == selected_qty].copy()
    current_market = snapshot.sort_values("scraped_at", ascending=False)

    if not current_market.empty:
        low_row = current_market.loc[current_market["price_per_gallon"].idxmin()]
        high_row = current_market.loc[current_market["price_per_gallon"].idxmax()]
        median_price = current_market["price_per_gallon"].median()

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Lowest Price",
            f"${low_row['price_per_gallon']:.3f}",
        )
        col1.caption(f"Supplier: **{low_row['supplier_name']}**")
        col2.metric("Median Price", f"${median_price:.3f}")
        col3.metric(
            "Highest Price",
            f"${high_row['price_per_gallon']:.3f}",
        )
        col3.caption(f"Supplier: **{high_row['supplier_name']}**")

        st.divider()

        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Daily Market Range (Min/Max)")

            range_df = full_df[full_df["min_quantity"] == selected_qty].copy()
            range_df["date"] = range_df["scraped_at"].dt.date

            daily_stats = (
                range_df.groupby("date")["price_per_gallon"]
                .agg(["min", "max"])
                .reset_index()
            )

            daily_stats = daily_stats.rename(
                columns={"min": "Cheapest", "max": "Most Expensive"}
            )

            st.line_chart(
                data=daily_stats.set_index("date")[["Cheapest", "Most Expensive"]],
                color=["#2ecc71", "#e74c3c"],
            )

        with right_col:
            st.subheader("Market Price Trend")
            history_df = full_df[full_df["min_quantity"] == selected_qty].copy()

            trend_data = (
                history_df.groupby("scraped_at")["price_per_gallon"]
                .median()
                .reset_index()
            )

            st.line_chart(data=trend_data, x="scraped_at", y="price_per_gallon")

        with st.expander("View Full Market Table"):
            st.dataframe(
                current_market[
                    ["supplier_name", "price_per_gallon", "scraped_at"]
                ].sort_values("price_per_gallon"),
                width="stretch",
                hide_index=True,
            )
else:
    st.info("Awaiting scraper data...")
