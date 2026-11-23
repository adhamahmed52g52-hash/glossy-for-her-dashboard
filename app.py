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

# Merge sales items with product info
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
    st.subheader("🔥 Shopping Activity by Day of Week")
    if date_col:
      temp_sales = filtered_sales.copy()
      temp_sales["dt"] = pd.to_datetime(temp_sales[date_col[0]], errors="coerce")
      temp_sales = temp_sales.dropna(subset=["dt"])
      days_order = [
          "Saturday",
          "Sunday",
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
      ]
      day_counts = (
          temp_sales["dt"]
          .dt.day_name()
          .value_counts()
          .reindex(days_order)
          .dropna()
      )
      fig_d, ax_d = plt.subplots(figsize=(7, 3.8))
      ax_d.bar(day_counts.index, day_counts.values, color="#7B1E3A", width=0.5)
      ax_d.set_title(
          "Invoices Count by Day of Week", fontsize=11, fontweight="bold"
      )
      ax_d.set_ylabel("Invoices")
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
      fig_p, ax_p = plt.subplots(figsize=(4, 3.8))
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
    st.subheader("💎 Top 10 Highest Revenue Products (EGP)")
    num_cols = filtered_details.select_dtypes(include="number").columns.tolist()
    val_candidates = [
        c
        for c in num_cols
        if any(k in c.lower() for k in ["profit", "total", "amount", "net"])
        and "qty" not in c.lower()
        and "code" not in c.lower()
        and "no" not in c.lower()
    ]
    metric_col = val_candidates[0] if val_candidates else "qty"

    prod_rev = (
        filtered_details.groupby("item_code")[metric_col].sum().reset_index()
    )
    prod_rev = prod_rev.merge(
        products[["item_code", "item_name"]], on="item_code", how="left"
    )
    top_rev = prod_rev.sort_values(by=metric_col, ascending=True).tail(10)

    fig_pr, ax_pr = plt.subplots(figsize=(6, 4.5))
    ax_pr.barh(top_rev["item_name"], top_rev[metric_col], color="#7B1E3A")
    ax_pr.set_title(
        f"Top 10 Products by {metric_col.replace('_', ' ').title()}",
        fontsize=11,
        fontweight="bold",
    )
    ax_pr.set_xlabel("Value (EGP)")
    ax_pr.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig_pr)

  st.markdown("---")
  st.subheader("📦 Category Performance: Units Sold")
  cat_sales = (
      filtered_details.groupby("product_category")["qty"]
      .sum()
      .sort_values(ascending=False)
  )
  fig3, ax3 = plt.subplots(figsize=(10, 3.8))
  ax3.bar(cat_sales.index, cat_sales.values, color="#7B1E3A", width=0.5)
  ax3.set_title("Total Units Sold per Category", fontsize=11, fontweight="bold")
  ax3.set_ylabel("Units Sold")
  ax3.grid(axis="y", linestyle="--", alpha=0.5)
  plt.xticks(rotation=25, ha="right", fontsize=9)
  plt.tight_layout()
  st.pyplot(fig3)

# -------------------- TAB 3: CUSTOMERS & BASKET SIZE --------------------
with tab3:
  cu1, cu2 = st.columns(2)

  with cu1:
    st.subheader("🛍️ Invoice Value Distribution (Basket Size)")
    bins = [0, 50, 100, 200, 500, float("inf")]
    labels = [
        "<= 50 EGP",
        "51 - 100 EGP",
        "101 - 200 EGP",
        "201 - 500 EGP",
        "> 500 EGP",
    ]
    basket_cats = pd.cut(filtered_sales["final_total"], bins=bins, labels=labels)
    basket_counts = basket_cats.value_counts().reindex(labels)

    fig_b, ax_b = plt.subplots(figsize=(6, 4))
    ax_b.bar(
        basket_counts.index, basket_counts.values, color="#7B1E3A", width=0.55
    )
    ax_b.set_title(
        "Number of Invoices per Spending Tier", fontsize=11, fontweight="bold"
    )
    ax_b.set_ylabel("Number of Invoices")
    ax_b.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig_b)

  with cu2:
    st.subheader("👥 Retail vs Internal / Other Accounts")
    if "is_retail_sale" in sales.columns:
      seg_sales = sales.groupby("is_retail_sale")["final_total"].sum()
      seg_labels = [
          "Retail Walk-in Customers"
          if idx == 1
          else "Internal / Partners / Staff"
          for idx in seg_sales.index
      ]
      fig_s, ax_s = plt.subplots(figsize=(6, 4))
      ax_s.pie(
          seg_sales.values,
          labels=seg_labels,
          autopct="%1.1f%%",
          colors=["#7B1E3A", "#D98A9C"],
          wedgeprops={"width": 0.45},
      )
      ax_s.set_title(
          "Total Sales Split by Customer Segment", fontsize=11, fontweight="bold"
      )
      plt.tight_layout()
      st.pyplot(fig_s)

# -------------------- TAB 4: INVENTORY, DEAD STOCK & RESTOCK --------------------
with tab4:
  sales_velocity = (
      filtered_details.groupby("item_code")["qty"]
      .sum()
      .reset_index()
      .rename(columns={"qty": "total_sold"})
  )
  inv_analysis = products.merge(sales_velocity, on="item_code", how="left")
  inv_analysis["total_sold"] = inv_analysis["total_sold"].fillna(0).astype(int)

  total_catalog = len(products)
  in_stock_count = len(products[products["total_qty"] > 0])
  dead_stock_df = inv_analysis[
      (inv_analysis["total_qty"] > 0) & (inv_analysis["total_sold"] == 0)
  ]
  m1, m2, m3 = st.columns(3)
  m1.metric("📚 Total Catalog Items", f"{total_catalog:,}")
  m2.metric("✅ Available In-Stock Items", f"{in_stock_count:,}")
  m3.metric("⚠️ Dead Stock Items (0 Sales)", f"{len(dead_stock_df):,}")

  st.markdown("---")
  i1, i2 = st.columns(2)

  with i1:
    st.subheader("📦 Out-of-Stock Rate by Category (%)")
    stockout_rate = (
        products.groupby("product_category")["is_out_of_stock"].mean() * 100
    ).sort_values(ascending=True)
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.barh(stockout_rate.index, stockout_rate.values, color="#7B1E3A")
    ax2.set_title(
        "Stockout Percentage per Category", fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Out of Stock (%)")
    ax2.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig2)

  with i2:
    st.subheader("↩️ Top 10 Returned Products")
    if "item_code" in return_items.columns and "qty" in return_items.columns:
      ret_merged = (
          return_items.groupby("item_code")["qty"].sum().abs().reset_index()
      )
      ret_merged = ret_merged.merge(
          products[["item_code", "item_name"]], on="item_code", how="left"
      )
      top_ret = ret_merged.sort_values(by="qty", ascending=True).tail(10)

      fig_r, ax_r = plt.subplots(figsize=(6, 4))
      ax_r.barh(top_ret["item_name"], top_ret["qty"], color="#7B1E3A")
      ax_r.set_title(
          "Top 10 Returned Items (Units)", fontsize=11, fontweight="bold"
      )
      ax_r.set_xlabel("Returned Units")
      ax_r.grid(axis="x", linestyle="--", alpha=0.5)
      plt.tight_layout()
      st.pyplot(fig_r)

  st.markdown("---")
  st.subheader("🚨 Priority Restock List (Out-of-Stock Best Sellers)")
  out_of_stock_item = products[products["is_out_of_stock"] == 1].copy()
  if selected_cat != "All":
    out_of_stock_item = out_of_stock_item[
        out_of_stock_item["product_category"] == selected_cat
    ]

  restock_table = out_of_stock_item.merge(
      sales_velocity, on="item_code", how="left"
  )
  restock_table["total_sold"] = restock_table["total_sold"].fillna(0).astype(int)
  restock_table = restock_table.sort_values(by="total_sold", ascending=False)

  display_cols = [
      "item_code",
      "item_name",
      "product_category",
      "total_sold",
      "total_qty",
  ]
  final_table = restock_table[display_cols].rename(
      columns={
          "item_code": "Item Code",
          "item_name": "Product Name",
          "product_category": "Category",
          "total_sold": "Units Sold",
          "total_qty": "Current Stock",
      }
  )

  styled_table = final_table.style.background_gradient(
      subset=["Units Sold"], cmap="Reds"
  )
  st.dataframe(styled_table, use_container_width=True, hide_index=True)

  csv_data = final_table.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      label="📥 Download Restock Order (CSV)",
      data=csv_data,
      file_name="glossy_restock_list.csv",
      mime="text/csv",
  )

  with st.expander("🧊 View Dead Stock Items (Products in Stock with 0 Sales)"):
    dead_display = dead_stock_df[
        ["item_code", "item_name", "product_category", "total_qty"]
    ].sort_values(by="total_qty", ascending=False)
    st.dataframe(dead_display, use_container_width=True, hide_index=True)
