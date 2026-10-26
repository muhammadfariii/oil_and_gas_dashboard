import streamlit as st
from databricks import sql
import pandas as pd
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="Alberta Energy & Oil Analytics Dashboard", page_icon="📊", layout="wide")

st.title("📊 Alberta Energy, Licencing & Crude Properties Analytics")
st.markdown("Visualizing multi-source energy data from Databricks Unity Catalog (`gold` schema).")

# Initialize Databricks Connection using Streamlit Secrets
@st.cache_resource
def init_connection():
    db_secrets = st.secrets["connections"]["databricks"]
    return sql.connect(
        server_hostname=db_secrets["server_hostname"],
        http_path=db_secrets["http_path"],
        access_token=db_secrets["access_token"]
    )

connection = init_connection()

# Load Data from Gold Layer Tables
@st.cache_data(ttl=600)
def load_licence_data():
    return pd.read_sql("SELECT * FROM dataengineeringdemo.gold.fct_licence_summary", connection)

@st.cache_data(ttl=600)
def load_padd_data():
    return pd.read_sql("SELECT * FROM dataengineeringdemo.gold.fct_padd_summary", connection)

@st.cache_data(ttl=600)
def load_oil_properties_data():
    return pd.read_sql("SELECT * FROM dataengineeringdemo.gold.fct_oil_summary", connection)

try:
    # Navigation Tabs for Clean Multi-Source Organization
    tab1, tab2, tab3 = st.tabs(["🏗️ Facility Licences", "🛢️ PADD Oil Volumes", "🧪 Crude Oil Properties"])

    # ----------------------------------------------------
    # TAB 1: FACILITY LICENCES
    # ----------------------------------------------------
    with tab1:
        st.header("Facility Licence Insights")
        df_licence = load_licence_data()
        
        selected_status = st.sidebar.multiselect(
            "Select Licence Status",
            options=df_licence["licence_status"].unique(),
            default=df_licence["licence_status"].unique(),
            key="licence_status_filter"
        )
        
        filtered_licence = df_licence[df_licence["licence_status"].isin(selected_status)]

        col1, col2 = st.columns(2)
        col1.metric("Total Licences", f"{filtered_licence['total_licences'].sum():,}")
        col2.metric("Unique Licence Types", filtered_licence["licence_type"].nunique())

        st.markdown("---")
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Licences by Year")
            yearly_df = filtered_licence.groupby("licence_year")["total_licences"].sum().reset_index()
            fig_year = px.bar(yearly_df, x="licence_year", y="total_licences", title="Total Licences per Year", color="total_licences")
            st.plotly_chart(fig_year, use_container_width=True)

        with col_b:
            st.subheader("Licences by Type")
            type_df = filtered_licence.groupby("licence_type")["total_licences"].sum().reset_index()
            fig_type = px.pie(type_df, names="licence_type", values="total_licences", title="Distribution by Licence Type", hole=0.4)
            st.plotly_chart(fig_type, use_container_width=True)

        with st.expander("View Raw Licence Gold Data"):
            st.dataframe(filtered_licence, use_container_width=True)

    # ----------------------------------------------------
    # TAB 2: PADD OIL VOLUMES
    # ----------------------------------------------------
    with tab2:
        st.header("PADD Crude Oil Volumes Analysis")
        df_padd = load_padd_data()

        selected_regions = st.sidebar.multiselect(
            "Select PADD Region",
            options=df_padd["padd_region"].unique(),
            default=df_padd["padd_region"].unique(),
            key="padd_region_filter"
        )

        filtered_padd = df_padd[df_padd["padd_region"].isin(selected_regions)]

        col3, col4 = st.columns(2)
        col3.metric("Average Daily Volume ($m^3/d$)", f"{filtered_padd['avg_volume_m3'].mean():,.2f}")
        col4.metric("Average Daily Volume (bbl/d)", f"{filtered_padd['avg_volume_bbl'].mean():,.2f}")

        st.markdown("---")
        col_c, col_d = st.columns(2)

        with col_c:
            st.subheader("Mean Volume by PADD Region")
            padd_region_df = filtered_padd.groupby("padd_region")["avg_volume_m3"].mean().reset_index()
            fig_padd = px.bar(padd_region_df, x="padd_region", y="avg_volume_m3", title="Average Daily Volume ($m^3/d$) by Region", color="padd_region")
            st.plotly_chart(fig_padd, use_container_width=True)

        with col_d:
            st.subheader("Volume Trend Across Years")
            trend_df = filtered_padd.groupby("volume_year")["avg_volume_bbl"].mean().reset_index()
            fig_trend = px.line(trend_df, x="volume_year", y="avg_volume_bbl", title="Annual Average Volume Trend (bbl/d)", markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)

        with st.expander("View Raw PADD Gold Data"):
            st.dataframe(filtered_padd, use_container_width=True)

    # ----------------------------------------------------
    # TAB 3: CRUDE OIL PROPERTIES
    # ----------------------------------------------------
    with tab3:
        st.header("Crude Oil & Petroleum Product Properties")
        df_oil = load_oil_properties_data()

        selected_origins = st.sidebar.multiselect(
            "Select Crude Origin",
            options=df_oil["origin"].unique(),
            default=df_oil["origin"].unique(),
            key="oil_origin_filter"
        )

        filtered_oil = df_oil[df_oil["origin"].isin(selected_origins)]

        col5, col6 = st.columns(2)
        col5.metric("Total Oil Assays / Records", f"{filtered_oil['total_measurements'].sum():,}")
        col6.metric("Unique Crude Origins", filtered_oil["origin"].nunique())

        st.markdown("---")
        col_e, col_f = st.columns(2)

        with col_e:
            st.subheader("Average Property Value by Origin")
            origin_df = filtered_oil.groupby("origin")["average_value"].mean().reset_index()
            fig_origin = px.bar(origin_df, x="origin", y="average_value", title="Average Property Value by Origin", color="origin")
            st.plotly_chart(fig_origin, use_container_width=True)

        with col_f:
            st.subheader("Property Measurements Distribution")
            prop_df = filtered_oil.groupby("property_name")["total_measurements"].sum().reset_index()
            fig_prop = px.pie(prop_df, names="property_name", values="total_measurements", title="Measurements by Property Type", hole=0.4)
            st.plotly_chart(fig_prop, use_container_width=True)

        with st.expander("View Raw Crude Properties Gold Data"):
            st.dataframe(filtered_oil, use_container_width=True)

except Exception as e:
    st.error(f"Error connecting to Databricks or loading data: {e}")