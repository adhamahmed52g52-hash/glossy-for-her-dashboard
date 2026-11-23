import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Glossy For Her", page_icon="💄", layout="wide")

# Header
st.markdown(
    """
<div style="background-color: #7B1E3A; padding: 20px; border-radius: 10px; color: white; text-align: center;">
<h1 style="margin: 0;">💄 Glossy For Her - Decision Dashboard</h1>
<p style="margin: 5px 0 0 0;">Executive Analytics, Profitability, Customer Behavior & Inventory Planner</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
  sales = pd.read_csv("data/processed/cleaned_sales_invoices.csv")
  items = pd.read_csv("data/processed/cleaned_sales_items.csv")
  products = pd.read_csv("data/processed/cleaned_products.csv")
  purchases = pd.read_csv("data/processed/cleaned_purchase_invoices.csv")
  returns = pd.read_csv("data/processed/cleaned_sales_returns_invoices.csv")
  return_items = pd.read_csv("data/processed/cleaned_sales_returns_items.csv")
  accounts = pd.read_csv("data/processed/cleaned_accounts.csv")
  return sales, items, products, purchases, returns, return_items, accounts


sales, items, products, purchases, returns, return_items, accounts = load_data()

# ==================== SIDEBAR FILTERS ====================
st.sidebar.header("🔍 Control Filters")
retail_only = st.sidebar.checkbox(
    "Retail Sales Only (Exclude Internal)", value=True
)
categories = ["All"] + sorted(
    products["product_category"].dropna().unique().tolist()
)
selected_cat = st.sidebar.selectbox("Product Category:", categories)

# Merge sales items with product info (بدون تكرار item_name)
sales_details = items.merge(
    products[
        ["item_code", "product_category", "total_qty", "is_out_of_stock"]
    ],
    on="item_code",
    how="left",
)

# Apply Retail Filter
if retail_only:
  filtered_sales = sales[sales["is_retail_sale"] == 1].copy()
  filtered_returns = returns[returns["is_retail_sale"] == 1].copy()
else:
  filtered_sales = sales.copy()
  filtered_returns = returns.copy()

filtered_details = sales_details[
    sales_details["invoice_no"].isin(filtered_sales["invoice_no"])
].copy()

if selected_cat != "All":
  filtered_details = filtered_details[
      filtered_details["product_category"] == selected_cat
  ]

# ==================== TOP EXECUTIVE KPIs ====================
gross_sales = filtered_sales["final_total"].sum()
returns_total = filtered_returns["final_total"].sum()
net_sales = gross_sales + returns_total
gross_profit = filtered_sales["profit"].sum()
net_profit = gross_profit + filtered_returns["profit"].sum()
net_margin = (net_profit / net_sales * 100) if net_sales > 0 else 0
avg_order_value = (
    (gross_sales / len(filtered_sales)) if len(filtered_sales) > 0 else 0
)
return_rate = (
    (abs(returns_total) / gross_sales * 100) if gross_sales > 0 else 0
)

st.markdown("###")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("💰 Net Sales", f"{net_sales:,.0f} EGP")
k2.metric("📈 Net Profit", f"{net_profit:,.0f} EGP")
k3.metric("📊 Net Margin", f"{net_margin:.2f}%")
k4.metric("🧾 Total Invoices", f"{len(filtered_sales):,}")
k5.metric("🛒 Avg Invoice", f"{avg_order_value:,.1f} EGP")
k6.metric("↩️ Return Rate", f"{return_rate:.2f}%")

st.markdown("---")

# ==================== 4 DASHBOARD TABS ====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive & Sales Patterns",
    "🏷️ Products & Profitability",
    "👥 Customers & Basket Size",
    "📦 Inventory, Dead Stock & Restock",
])

# -------------------- TAB 1: EXECUTIVE & SALES PATTERNS --------------------
with tab1:
  c1, c2 = st.columns(2)

  with c1:
    st.subheader("📈 Monthly Sales Trend")
    date_col = [col for col in filtered_sales.columns if "date" in col.lower()]
    if date_col:
      temp_sales = filtered_sales.copy()
      temp_sales["dt"] = pd.to_datetime(temp_sales[date_col[0]], errors="coerce")
      monthly = (
          temp_sales.dropna(subset=["dt"])
          .groupby(temp_sales["dt"].dt.to_period("M"))["final_total"]
          .sum()
      )
      monthly.index = monthly.index.astype(str)

      fig_m, ax_m = plt.subplots(figsize=(6, 4))
      ax_m.plot(
          monthly.index,
          monthly.values,
          marker="o",
          color="#7B1E3A",
          linewidth=2.5,
      )
      ax_m.fill_between(
          monthly.index, monthly.values, color="#7B1E3A", alpha=0.12
      )
      ax_m.set_title(
          "Gross Sales by Month (EGP)", fontsize=11, fontweight="bold"
      )
      ax_m.set_ylabel("Sales (EGP)")
      ax_m.grid(True, linestyle="--", alpha=0.5)
      plt.xticks(rotation=30, ha="right", fontsize=8)
      plt.tight_layout()
      st.pyplot(fig_m)
    else:
      st.info("Date column not found for monthly trend.")

  with c2:
    st.subheader("🚚 Top Suppliers by Purchase Volume")
    top_suppliers = (
        purchases.groupby("account")["final_total"]
        .sum()
        .sort_values(ascending=True)
        .tail(8)
    )
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.barh(top_suppliers.index, top_suppliers.values, color="#7B1E3A")
    ax1.set_title(
        "Top 8 Suppliers (Total Purchases in EGP)",
        fontsize=11,
        fontweight="bold",
    )
    ax1.set_xlabel("Purchase Amount (EGP)")
    ax1.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig1)

  st.markdown("---")
  c3, c4 = st.columns([2, 1])

  with c3:
    st.subheader("🔥 Peak Shopping Hours Heatmap (Day vs Hour)")
    if date_col:
      temp_sales = filtered_sales.copy()
      temp_sales["dt"] = pd.to_datetime(temp_sales[date_col[0]], errors="coerce")
      temp_sales = temp_sales.dropna(subset=["dt"])
      if temp_sales["dt"].dt.hour.nunique() > 1:
        temp_sales["Day"] = temp_sales["dt"].dt.day_name()
        temp_sales["Hour"] = temp_sales["dt"].dt.hour
        days_order = [
            "Saturday",
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]
        pivot_hm = pd.pivot_table(
            temp_sales,
            values="invoice_no",
            index="Day",
            columns="Hour",
            aggfunc="count",
            fill_value=0,
        )
        pivot_hm = pivot_hm.reindex(
            [d for d in days_order if d in pivot_hm.index]
        )
        st.dataframe(
            pivot_hm.style.background_gradient(cmap="Reds", axis=None),
            use_container_width=True,
        )
      else:
        day_counts = temp_sales["dt"].dt.day_name().value_counts()
        fig_d, ax_d = plt.subplots(figsize=(7, 3.5))
        ax_d.bar(
            day_counts.index, day_counts.values, color="#7B1E3A", width=0.5
        )
        ax_d.set_title(
            "Invoices Count by Day of Week", fontsize=11, fontweight="bold"
        )
        ax_d.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        st.pyplot(fig_d)

  with c4:
    st.subheader("💳 Payment Methods")
    pay_col = [
        col
        for col in filtered_sales.columns
        if "pay" in col.lower() or "type" in col.lower()
    ]
    if pay_col:
      pay_dist = filtered_sales[pay_col[0]].value_counts()
      fig_p, ax_p = plt.subplots(figsize=(4, 3.5))
      colors = ["#7B1E3A", "#D98A9C", "#F2C6D0", "#4A0E20"]
      ax_p.pie(
          pay_dist.values,
          labels=pay_dist.index,
          autopct="%1.1f%%",
          colors=colors[: len(pay_dist)],
          wedgeprops={"width": 0.45},
      )
      ax_p.set_title(
          "Invoices by Payment Type", fontsize=11, fontweight="bold"
      )
      plt.tight_layout()
      st.pyplot(fig_p)
    else:
      st.info("Payment column not available in dataset.")

# -------------------- TAB 2: PRODUCTS & PROFITABILITY --------------------
with tab2:
  p1, p2 = st.columns(2)

  with p1:
    st.subheader("🏆 Top 10 Best-Selling Products (Units)")
    prod_sales = filtered_details.groupby("item_code")["qty"].sum().reset_index()
    prod_sales = prod_sales.merge(
        products[["item_code", "item_name"]], on="item_code", how="left"
    )
    top_prods = prod_sales.sort_values(by="qty", ascending=True).tail(10)

    fig4, ax4 = plt.subplots(figsize=(6, 4.5))
    ax4.hlines(
        y=top_prods["item_name"],
        xmin=0,
        xmax=top_prods["qty"],
        color="#7B1E3A",
        linewidth=2,
    )
    ax4.scatter(
        top_prods["qty"], top_prods["item_name"], color="#7B1E3A", s=65, zorder=3
    )
    ax4.set_title(
        "Top 10 Products by Units Sold", fontsize=11, fontweight="bold"
    )
    ax4.set_xlabel("Units Sold")
    ax4.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig4)

  with p2:
    st.subheader("💎 Top 10 Most Profitable Products (EGP)")
    profit_col = [
        col for col in filtered_details.columns if "profit" in col.lower()
    ]
    total_col = [
        col
        for col in filtered_details.columns
        if "total" in col.lower() and "qty" not in col.lower()
    ]
    target_metric = (
        profit_col[0] if profit_col else (total_col[0] if total_col else "qty")
    )

    prod_prof = (
        filtered_details.groupby("item_code")[target_metric].sum().reset_index()
    )
    prod_prof = prod_prof.merge(
