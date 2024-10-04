import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load data
order_items = pd.read_csv('Cleaned/order_items.csv')
orders_cleaned = pd.read_csv('Cleaned/orders_cleaned.csv')
products_cleaned = pd.read_csv('Cleaned/products_cleaned.csv')
order_reviews_cleaned = pd.read_csv('Cleaned/order_reviews_cleaned.csv')

# Convert relevant columns to datetime and numeric
orders_cleaned['order_purchase_timestamp'] = pd.to_datetime(orders_cleaned['order_purchase_timestamp'])
orders_cleaned['shipping_time'] = pd.to_numeric(orders_cleaned['shipping_time'], errors='coerce')

# Centered header using HTML
st.markdown("<h1 style='text-align: center;'>E-Commerce Data Dashboard</h1>", unsafe_allow_html=True)

# Centered subheader for sidebar section
st.sidebar.markdown("<h2 style='text-align: center;'>Interactive Filters</h2>", unsafe_allow_html=True)

# Sidebar filters
# Filter: Top N categories
top_n = st.sidebar.slider('Select number of top categories to display', min_value=1, max_value=20, value=10)

# Filter: Specific product categories with "All Categories" option
unique_categories = products_cleaned['product_category_name_english'].unique()
category_options = ['All Categories'] + list(unique_categories)
selected_categories = st.sidebar.multiselect('Select specific categories', options=category_options, default='All Categories')

# Apply category filter to products
if 'All Categories' in selected_categories:
    filtered_products = products_cleaned
else:
    filtered_products = products_cleaned[products_cleaned['product_category_name_english'].isin(selected_categories)]

# Filter: Shipping time range
min_shipping_time = int(orders_cleaned['shipping_time'].min())
max_shipping_time = int(orders_cleaned['shipping_time'].max())
shipping_time_range = st.sidebar.slider('Select shipping time range (days)', min_shipping_time, max_shipping_time, (min_shipping_time, max_shipping_time))

# Filter: Review score range
review_score_range = st.sidebar.slider('Select review score range', 1, 5, (1, 5))

# Since we are removing the order status filter, apply all orders
filtered_orders = orders_cleaned

# Centered header for visualizations section
st.markdown("<h2 style='text-align: center;'>Visualizations</h2>", unsafe_allow_html=True)

# Function to plot Top N Product Categories by Revenue
def plot_revenue_per_category(order_items, filtered_products, filtered_orders):
    order_items_products = order_items.merge(filtered_products, on='product_id')
    order_items_products = order_items_products.merge(filtered_orders[['order_id']], on='order_id')
    
    revenue_per_category = order_items_products.groupby('product_category_name_english')['price'].sum().sort_values(ascending=False)
    
    # Centered subheader
    st.markdown(f"<h3 style='text-align: center;'>Top {top_n} Product Categories by Revenue</h3>", unsafe_allow_html=True)
    
    if not revenue_per_category.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        revenue_per_category.head(top_n).plot(kind='bar', color='skyblue', ax=ax)
        ax.set_title(f'Top {top_n} Product Categories by Revenue')
        ax.set_ylabel('Total Revenue')
        ax.set_xlabel('Product Category')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        st.pyplot(fig)
    else:
        st.write("No revenue data available for the selected filters.")

# Function to plot Revenue Trend Over Time
def plot_revenue_trend(order_items, filtered_products, filtered_orders):
    # Centered subheader
    st.markdown("<h3 style='text-align: center;'>Revenue Trend Over Time by Top Product Categories</h3>", unsafe_allow_html=True)
    
    order_items_products = order_items.merge(filtered_products, on='product_id')
    order_items_products_time = order_items_products.merge(filtered_orders[['order_id', 'order_purchase_timestamp']], on='order_id')
    
    order_items_products_time['purchase_month'] = order_items_products_time['order_purchase_timestamp'].dt.to_period('M')
    revenue_trend = order_items_products_time.groupby(['purchase_month', 'product_category_name_english'])['price'].sum().unstack().fillna(0)
    top_categories = revenue_trend.sum().sort_values(ascending=False).head(top_n).index
    
    if not revenue_trend.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        revenue_trend[top_categories].plot(ax=ax)
        ax.set_title('Revenue Trend Over Time by Top Product Categories')
        ax.set_ylabel('Revenue')
        ax.set_xlabel('Purchase Month')
        ax.set_xticklabels(ax.get_xticks(), rotation=45)
        ax.legend(title='Product Category')
        st.pyplot(fig)
    else:
        st.write("No trend data available for the selected filters.")

# Function to plot Average Shipping Time per Category (Top 5 and Bottom 5)
def plot_avg_shipping_time(order_items, filtered_products, filtered_orders):
    st.markdown("<h3 style='text-align: center;'>Average Shipping Time per Product Category</h3>", unsafe_allow_html=True)

    # Merge data to calculate average shipping time
    order_items_products = order_items.merge(filtered_products, on='product_id')
    shipping_data = order_items_products.merge(filtered_orders[['order_id', 'shipping_time']], on='order_id')
    
    # Apply shipping time filter correctly
    shipping_data = shipping_data[(shipping_data['shipping_time'] >= shipping_time_range[0]) & 
                                  (shipping_data['shipping_time'] <= shipping_time_range[1])]
    
    # Calculate average shipping time per product category
    avg_shipping_time_per_category = shipping_data.groupby('product_category_name_english')['shipping_time'].mean().sort_values()

    if not avg_shipping_time_per_category.empty:
        # Top 5 categories with the fastest shipping times
        st.markdown("<h4 style='text-align: center;'>Top 5 Categories with Fastest Shipping</h4>", unsafe_allow_html=True)
        top_5_fastest = avg_shipping_time_per_category.head(5)
        fig, ax = plt.subplots(figsize=(10, 6))
        top_5_fastest.plot(kind='barh', color='lightblue', ax=ax)
        ax.set_title('Top 5 Categories with Fastest Shipping')
        ax.set_xlabel('Average Shipping Time (days)')
        ax.set_ylabel('Product Category')
        st.pyplot(fig)

        # Top 5 categories with the slowest shipping times
        st.markdown("<h4 style='text-align: center;'>Top 5 Categories with Slowest Shipping</h4>", unsafe_allow_html=True)
        top_5_slowest = avg_shipping_time_per_category.tail(5)
        fig, ax = plt.subplots(figsize=(10, 6))
        top_5_slowest.plot(kind='barh', color='lightcoral', ax=ax)
        ax.set_title('Top 5 Categories with Slowest Shipping')
        ax.set_xlabel('Average Shipping Time (days)')
        ax.set_ylabel('Product Category')
        st.pyplot(fig)
    else:
        st.write("No shipping data available for the selected filters.")

# Function to plot Shipping Time vs Review Score with proper filtering
def plot_shipping_time_vs_review(order_items, filtered_products, filtered_orders, order_reviews_cleaned):
    st.markdown("<h3 style='text-align: center;'>Shipping Time vs Customer Review Score</h3>", unsafe_allow_html=True)
    
    # Merge order items and products to get the shipping data
    order_items_products = order_items.merge(filtered_products, on='product_id')
    shipping_data = order_items_products.merge(filtered_orders[['order_id', 'shipping_time']], on='order_id')
    
    # Apply shipping time filter
    shipping_data = shipping_data[(shipping_data['shipping_time'] >= shipping_time_range[0]) & 
                                  (shipping_data['shipping_time'] <= shipping_time_range[1])]
    
    # Merge with review data
    shipping_review_data = shipping_data.merge(order_reviews_cleaned[['order_id', 'review_score']], on='order_id')
    shipping_review_relation = shipping_review_data.groupby('shipping_time')['review_score'].mean()
    
    if not shipping_review_relation.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(shipping_review_relation.index, shipping_review_relation.values, marker='o', color='purple')
        ax.set_title('Shipping Time vs Customer Review Score')
        ax.set_xlabel('Shipping Time (days)')
        ax.set_ylabel('Average Review Score')
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.write("No review data available for the selected filters.")

# Function to plot Top Categories by Refund
def plot_refund_per_category(filtered_products, filtered_orders):
    st.markdown("<h3 style='text-align: center;'>Product Categories with Highest Refunds</h3>", unsafe_allow_html=True)
    
    order_items_products = order_items.merge(filtered_products, on='product_id')
    refund_orders = filtered_orders[filtered_orders['order_status'] == 'canceled']
    refund_data = refund_orders.merge(order_items_products, on='order_id')
    refund_per_category = refund_data.groupby('product_category_name_english').size().sort_values(ascending=False)

    if not refund_per_category.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        refund_per_category.head(top_n).plot(kind='bar', color='tomato', ax=ax)
        ax.set_title('Product Categories with Highest Refunds')
        ax.set_xlabel('Product Category')
        ax.set_ylabel('Number of Refunds')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        st.pyplot(fig)
    else:
        st.write("No refund data available for the selected filters.")

# Function to plot Review Scores for Returned Products
def plot_refund_review_distribution(filtered_products, filtered_orders, order_reviews_cleaned):
    st.markdown("<h3 style='text-align: center;'>Review Scores for Returned Products</h3>", unsafe_allow_html=True)
    
    order_items_products = order_items.merge(filtered_products, on='product_id')
    refund_orders = filtered_orders[filtered_orders['order_status'] == 'canceled']
    refund_data = refund_orders.merge(order_items_products, on='order_id')
    refund_reviews = refund_data.merge(order_reviews_cleaned[['order_id', 'review_score']], on='order_id')
    
    # Apply review score filter
    refund_reviews = refund_reviews[(refund_reviews['review_score'] >= review_score_range[0]) & 
                                    (refund_reviews['review_score'] <= review_score_range[1])]
    
    refund_review_distribution = refund_reviews['review_score'].value_counts().sort_index()

    if not refund_review_distribution.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        refund_review_distribution.plot(kind='bar', color='darkgreen', ax=ax)
        ax.set_title('Review Score Distribution for Returned Products')
        ax.set_xlabel('Review Score')
        ax.set_ylabel('Count')
        st.pyplot(fig)
    else:
        st.write("No review data available for the selected filters.")

# Main function to generate dashboard layout
def generate_dashboard():
    
    # Render individual visualizations with the filtered data
    plot_revenue_per_category(order_items, filtered_products, filtered_orders)
    plot_revenue_trend(order_items, filtered_products, filtered_orders)
    plot_avg_shipping_time(order_items, filtered_products, filtered_orders)
    plot_shipping_time_vs_review(order_items, filtered_products, filtered_orders, order_reviews_cleaned)
    plot_refund_per_category(filtered_products, filtered_orders)
    plot_refund_review_distribution(filtered_products, filtered_orders, order_reviews_cleaned)

# Call the function to create the dashboard
generate_dashboard()
