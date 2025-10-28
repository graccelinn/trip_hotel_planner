import streamlit as st
import pandas as pd

st.set_page_config(page_title="Trip Hotel Planner", layout="wide")
st.title("🏨 Trip Hotel Planner (Brisbane → Gold Coast → Coffs → Sydney)")
st.caption("Data source: TriptoBrisbane20252026.html")

@st.cache_data
def load_hotels():
    tables = pd.read_html("TriptoBrisbane20252026.html", header=None)

    cities = ["Brisbane", "Gold Coast", "Coffs Harbor/Newcastle/Forster", "Sydney"]
    date_ranges = [
        "2025/12/28 - 12/29",
        "2025/12/29 - 12/31",
        "2025/12/31 - 2026/01/01",
        "2026/01/01 - 01/02"
    ]

    df_list = []
    for city, dr, t in zip(cities, date_ranges, tables):
        # First row are headers
        t.columns = t.iloc[0].tolist()
        t = t.drop(0).reset_index(drop=True)

        # Normalize columns
        t.columns = [str(c).strip().replace("Dist. to ", "Distance to ") for c in t.columns]
        for col in t.columns:
            if col.startswith("Distance"):
                t.rename(columns={col: "Distance"}, inplace=True)

        # Detect Price column
        price_col = next((col for col in t.columns if "price" in col.lower()), None)
        if price_col:
            t.rename(columns={price_col: "Price"}, inplace=True)
            t["Price"] = (
                t["Price"]
                .astype(str)
                .str.replace(r"[^\d.]", "", regex=True)
                .replace("", "0")
                .astype(float)
            )
        else:
            st.warning(f"No 'Price' column found for {city}. Columns: {t.columns.tolist()}")

        t["City"] = city
        t["Date Range"] = dr
        df_list.append(t)

    return pd.concat(df_list, ignore_index=True)


# Load
df = load_hotels()

# --- Sidebar ---
city = st.sidebar.selectbox("🌆 Choose City", sorted(df["City"].unique()))
sort_option = st.sidebar.selectbox("🔢 Sort by", ["Price (Low → High)", "Price (High → Low)"])
breakfast_filter = st.sidebar.checkbox("☕ Only show hotels with breakfast options")
parking_filter = st.sidebar.checkbox("🚗 Only show hotels with available parking")
view_mode = st.sidebar.radio("🧭 Display Mode", ["Table", "Cards"])

# --- Filters ---
filtered = df[df["City"] == city].copy()

if breakfast_filter:
    filtered = filtered[filtered["Breakfast"].astype(str).str.contains("Yes|\\+|\\d", na=False)]
if parking_filter:
    filtered = filtered[filtered["Parking"].astype(str).str.contains("Yes|\\+|Free", na=False)]

if "Price" in filtered.columns:
    ascending = True if "Low" in sort_option else False
    filtered = filtered.sort_values("Price", ascending=ascending)
else:
    st.warning("⚠️ Price column missing — sorting disabled.")

# --- Display ---
st.subheader(f"🏙️ {city} Hotels ({filtered['Date Range'].iloc[0] if len(filtered)>0 else ''})")

if view_mode == "Table":
    st.dataframe(filtered, use_container_width=True)
else:
    for _, row in filtered.iterrows():
        price_text = f"${row['Price']:.0f}" if "Price" in row else "N/A"
        st.markdown(f"""
        ### 🏨 {row['Name']}
        **Room:** {row['Room Type']}  
        **Breakfast:** {row['Breakfast']} | **Parking:** {row['Parking']}  
        **Distance:** {row.get('Distance', 'N/A')} | **Price:** {price_text}  
        ---
        """)

if "Price" in filtered.columns and not filtered.empty:
    best = filtered.loc[filtered["Price"].idxmin()]
    st.success(f"💡 Best deal: **{best['Name']} (${best['Price']:.0f})** in {city}")

