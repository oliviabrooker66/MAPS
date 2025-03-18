import streamlit as st
import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
import pandas as pd
import geopandas as gpd
import snowflake.connector
import shapely
import re
import random
from shapely.wkt import loads
from shapely.geometry import mapping
from utils import *


# Function to load CSV
def load_csv():
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    return None


# Function to query database
def query_db():
    query = st.text_area("Enter your SQL query")
    if st.button("Run Query"):
        conn = sqlite3.connect("your_database.db")  # Change for your DB
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    return None


def create_map():
    uk_postcode_areas = gpd.read_file("uk_postcode_areas.csv")
    uk_postcodes = pd.read_csv("uk_postcodes.csv")
    uk_postcodes["POSTCODE_AREA"] = uk_postcodes["POSTCODE"].apply(
        extract_postcode_area
    )

    uk_postcode_with_areas = pd.merge(
        uk_postcodes, uk_postcode_areas, on="POSTCODE_AREA", how="left"
    )
    customers_join_pc = pd.merge(
        customer_df, uk_postcode_with_areas, on="POSTCODE", how="left"
    )
    customers_join_pc.dropna(inplace=True)
    customers_join_pc["GEOMETRY"] = customers_join_pc["GEOMETRY"].apply(loads)
    customers_join_pc = gpd.GeoDataFrame(
        customers_join_pc, geometry="GEOMETRY", crs="EPSG:4326"
    )

    uk_region_shapes = gpd.read_file(f"uk_{region_shape_level.lower()}_shapes.csv")
    uk_region_shapes["GEOMETRY"] = uk_region_shapes["GEOMETRY"].apply(loads)
    uk_region_shapes = gpd.GeoDataFrame(
        uk_region_shapes, geometry="GEOMETRY", crs="EPSG:4326"
    )

    if not isinstance(customers_join_pc, gpd.GeoDataFrame):
        raise TypeError("insure gdf_within is a geopandas df")

    if not isinstance(uk_region_shapes, gpd.GeoDataFrame):
        raise TypeError("insure gdf_region_shapes is a geopandas df")

    customers_region_spatial_join = gpd.sjoin(
        customers_join_pc, uk_region_shapes, how="right", predicate="within"
    )

    customers_region_spatial_join_agg = (
        customers_region_spatial_join.groupby(["REGION_NAME", "GEOMETRY"])
        .agg(
            SUM=(metric, "sum"),
            AVG=(metric, "mean"),
            MEMBER_COUNT=("MEMBER_ID", "count"),
        )
        .reset_index()
    )

    customers_region_spatial_join_agg.rename(
        {"SUM": f"{metric}_SUM", "AVG": f"{metric}_AVG"}, axis=1, inplace=True
    )
    print(customers_region_spatial_join_agg.shape)
    customers_region_spatial_join_agg_regions_gdf = gpd.GeoDataFrame(
        customers_region_spatial_join_agg, geometry="GEOMETRY", crs="EPSG:4326"
    )
    print(customers_region_spatial_join_agg_regions_gdf)

    map_fig = create_px_heat_map_layer(
        customers_region_spatial_join_agg_regions_gdf,
        "REGION_NAME",
        f"{metric}_{agg_type}",
    ).update_layout(
        margin=dict(l=10, r=10, t=10, b=10)  # Removes extra white space around the map
    )

    return map_fig, customers_region_spatial_join_agg_regions_gdf


# Select data source
st.title("Generate Geo Heat Maps")
st.subheader("Upload CSV or Query Database")
data_source = st.radio("Select Data Source", ["Upload CSV", "Query Database"])

customer_df = None
if data_source == "Upload CSV":
    customer_df = load_csv()
elif data_source == "Query Database":
    customer_df = query_db()

if customer_df is not None:
    st.write("Preview of Data:", customer_df.head())

    # Select columns
    st.subheader("Select Inputs for Mapping")
    customer_metrics = [
        x for x in customer_df.columns if x not in ["MEMBER_ID", "POSTCODE"]
    ]
    metric = st.radio("Pick the Customer Metric", customer_metrics)
    agg_type = st.radio("Pick the Aggregation Type", ["SUM", "MEAN", "COUNT"])
    region_shape_level = st.radio(
        "Pick a Region Shape Level", ["County", "District", "Region"]
    )
    if st.button("Create Map"):
        map_fig, map_df = create_map()

        st.plotly_chart(map_fig)
        st.dataframe(
            map_df.drop(columns="GEOMETRY").sort_values(
                by=f"{metric}_{agg_type}", ascending=False
            )
        )
