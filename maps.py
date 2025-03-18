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
import sys

region_shape_level = sys.argv[1]
metric = sys.argv[2]
agg_type = sys.argv[3]

uk_postcode_areas = gpd.read_file("uk_postcode_areas.csv")
uk_postcodes = pd.read_csv("uk_postcodes.csv")
uk_postcodes["POSTCODE_AREA"] = uk_postcodes["POSTCODE"].apply(extract_postcode_area)

uk_postcode_with_areas = pd.merge(
    uk_postcodes, uk_postcode_areas, on="POSTCODE_AREA", how="left"
)

customer_dummy = generate_dummy_data()
assert metric in customer_dummy.columns, f"{metric} not in customer_dummy columns"

customers_join_pc = pd.merge(
    customer_dummy, uk_postcode_with_areas, on="POSTCODE", how="left"
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
    customers_region_spatial_join_agg_regions_gdf, "REGION_NAME", f"{metric}_{agg_type}"
).update_layout(
    margin=dict(l=10, r=10, t=10, b=10)  # Removes extra white space around the map
)

map_fig.show()

save_figure = input("Do you want to save the map figure? (Y/N): ").strip().upper()
if save_figure == "Y":
    filename = input("Enter the filename: ").strip()
    map_fig.write_html(f"outputs/{filename}.html")
    print(f"Map saved as '{filename}'")
else:
    print("Map not saved.")
