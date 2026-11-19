import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Glossy For Her",page_icon="💄", layout="wide")
st.markdown(
"""
<div style="background-color: #7B1E3A; padding: 20px; border-radius: 10px; color: white; text-align: center;">
<h1 style="margin: 0;">💄 Glossy For Her - Decision Dashboard</h1>
<p style="margin: 5px 0 0 0;">Inventory Diagnostics, Supplier Analytics & Restock Planner</p>
</div>

"""
,
unsafe_allow_html=True,

)
@st.cache_data
def load_data():
 sales = pd.read_csv("data/processed/cleaned_sales_invoices.csv")
 items = pd.read_csv("data/processed/cleaned_sales_items.csv")
 products = pd.read_csv("data/processed/cleaned_products.csv")
 purchases = pd.read_csv("data/processed/cleaned_purchase_invoices.csv")
 returns = pd.read_csv("data/processed/cleaned_sales_returns_invoices.csv")
 accounts = pd.read_csv("data/processed/cleaned_accounts.csv")
 return sales, items, products, purchases, returns, accounts


sales, items, products, purchases, returns, accounts = load_data()

st.sidebar.header("🔍 Control Filters")
retail_only = st.sidebar.checkbox("Retail Sales Only (Exclude Internal)",value=True)
categories = ["All"]+ sorted(products["product_category"].dropna().unique().tolist())
selected_cat = st.sidebar.selectbox("Product Category:",categories)

sales_details = items.merge(
products[["item_code","product_category","total_qty","is_out_of_stock"]], on="item_code", how="left",

)
if retail_only:
 filtered_sales = sales[sales["is_retail_sale"]==1].copy()
 filtered_returns = returns[returns["is_retail_sale"]==1].copy()
else:
 filtered_sales = sales.copy()
 filtered_returns = returns.copy()   

filtered_details = sales_details[sales_details["invoice_no"].isin(filtered_sales["invoice_no"])]

if selected_cat !="All":
 filtered_details= filtered_details[filtered_details["product_category"]==selected_cat]

gross_sales = filtered_sales["final_total"].sum()
returns_total = filtered_returns["final_total"].sum()
net_sales = gross_sales + returns_total
gross_profit = filtered_sales["profit"].sum()
net_profit = gross_profit + filtered_returns["profit"].sum()
net_margin = (net_profit / net_sales*100) if net_sales> 0 else 0
col1, col2, col3,col4 = st.columns(4)
col1.metric("💰 Net Sales", f"{net_sales:,.0f} EGP")
col2.metric("📈 Net Profit", f"{net_profit:,.0f} EGP")
col3.metric("📊 Net Margin", f"{net_margin:.2f}%")
col4.metric("🧾 Total Invoices", f"{len(filtered_sales):,}")

st.markdown("---")
chart_col1, chart_col2 =st.columns(2)
with chart_col1:
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
      "Top 8 Suppliers (Total Purchases in EGP)", fontsize=11, fontweight="bold"
  )
  ax1.set_xlabel("Purchase Amount (EGP)")
  ax1.grid(axis="x", linestyle="--", alpha=0.5)
  plt.tight_layout()
  st.pyplot(fig1)
with chart_col2:
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


st.markdown("---")
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
  st.subheader("📦 Units Sold by Category")
  cat_sales = (
      filtered_details.groupby("product_category")["qty"]
      .sum()
      .sort_values(ascending=False)
  )

  
  fig3, ax3 = plt.subplots(figsize=(6, 4.5))
  bars = ax3.bar(cat_sales.index, cat_sales.values, color="#7B1E3A", width=0.55)
  ax3.set_title("Total Units Sold per Category", fontsize=11, fontweight="bold")
  ax3.set_ylabel("Units Sold")
  ax3.grid(axis="y", linestyle="--", alpha=0.5)
  plt.xticks(rotation=30, ha="right", fontsize=8)
  plt.tight_layout()
  st.pyplot(fig3)

with chart_col4:
  st.subheader("🏆 Top 10 Best-Selling Products")
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

st.markdown("---")
st.subheader("🚨 Priority Restock List (Out-of-Stock Best Sellers)")
sales_velocity= (
filtered_details.groupby("item_code")["qty"].sum().reset_index().rename(columns={"qty": "total_sold"})
 
)

out_of_stock_item= products[products["is_out_of_stock"]==1].copy()
if selected_cat != "All":
 out_of_stock_item= out_of_stock_item[out_of_stock_item["product_category"]==selected_cat]

restock_table=out_of_stock_item.merge(sales_velocity,on="item_code",how="left")
restock_table["total_sold"]=restock_table["total_sold"].fillna(0).astype(int)
restock_table= restock_table.sort_values(by="total_sold",ascending=False)
display_cols = ["item_code","item_name","product_category","total_sold","total_qty",]

final_table = restock_table[display_cols].rename(columns={"item_code": "Item Code","item_name": "Product Name","product_category": "Category","total_sold": "Units Sold", "total_qty": "Current Stock",})
st.dataframe(final_table, use_container_width=True, hide_index=True)
csv_data = final_table.to_csv(index=False).encode("utf-8-sig")
st.download_button(
label="📥 Download Restock Order (CSV)",
    data=csv_data,
    file_name="glossy_restock_list.csv",
    mime="text/csv",
 
)


