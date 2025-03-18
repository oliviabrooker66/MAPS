from shapely.geometry import mapping
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import re
import random
import geopandas as gpd
from shapely.wkt import loads
import yaml
import plotly.express as px
import plotly.graph_objects as go


def generate_dummy_data(n=500000):
    uk_postcodes = pd.read_csv("location_data/uk_postcodes.csv")
    random_valid_postcode = lambda: random.choice(uk_postcodes["POSTCODE"])
    data = {
        "MEMBER_ID": [_ for _ in range(1000, 1000 + n)],
        "POSTCODE": [random_valid_postcode() for _ in range(n)],
        "BALANCE": [
            round(random.uniform(0, 100000), 2) for _ in range(n)
        ],  # Random balance between 0-100k
    }
    df = pd.DataFrame(data)
    return df


def extract_postcode_area(postcode):
    # Match the first 1 or 2 letters
    match = re.match(r"^([A-Z]{1,2})", postcode)
    if match:
        return match.group(0)
    return None


def create_px_heat_map_layer(
    gdf_colour: pd.DataFrame,
    region_level: str,
    colour_metric: str,
    colour_scale: str = "Plasma",
    log: bool = False,
    scale_tick_no: int = 6,
    geojson_dict: dict = None,
    numerical_columns: list = [],
) -> go.Figure:
    """
    Create a heat map layer using Plotly.

    Args:
        gdf_colour (pd.DataFrame): The dataframe containing data for coloring the map.
        region_level (str): The level of regions in the map.
        colour_metric (str): The metric to color the map by.
        colour_scale (str): The color scale to use for the map. Default is "Plasma".
        log (bool): Whether to apply logarithmic scaling to the colour metric. Default is False.
        scale_tick_no (int): Number of ticks to use for the color scale. Default is 6.
        geojson_dict (dict): The GeoJSON dictionary for the map.

    Returns:
        go.Figure: The Plotly figure representing the heat map layer.
    """

    gdf_colour[numerical_columns] = gdf_colour[numerical_columns].apply(
        pd.to_numeric, errors="coerce"
    )

    if log:
        gdf_colour[colour_metric] = gdf_colour[colour_metric].replace(
            0, np.nan
        )  # Avoid log(0)
        gdf_colour[f"log_{colour_metric}"] = np.log10(gdf_colour[colour_metric])
        color_metric_log = f"log_{colour_metric}"
    else:
        color_metric_log = colour_metric

    # Generate representative ticks for the color bar
    min_value = gdf_colour[colour_metric].min()
    max_value = gdf_colour[colour_metric].max()
    representative_ticks = np.linspace(min_value, max_value, scale_tick_no)

    tickvals = np.log10(representative_ticks) if log else representative_ticks
    ticktext = [int(vlu) for vlu in representative_ticks]
    ticktext = [sigfig_round(number, sigfigs=2) for number in ticktext]

    colourmap_trace = px.choropleth_mapbox(
        gdf_colour.round(2),
        geojson=construct_geojson_dict(df=gdf_colour, metric=colour_metric),
        locations="REGION_NAME",
        color=color_metric_log,
        mapbox_style="open-street-map",
        featureidkey="properties.region",
        color_continuous_scale=colour_scale,
        opacity=0.5,
        center=dict(lat=55, lon=-2.6),
        labels={"location": "LOCATION_NAME"},
        zoom=3,
        hover_data=gdf_colour.drop(columns=["GEOMETRY"]).columns,
    )

    colourmap_trace.update_layout(
        coloraxis_colorbar=dict(
            title=colour_metric.replace("_", " ").title(),
            tickvals=tickvals,
            ticktext=ticktext,
            x=-0.1,
        )
    )

    return colourmap_trace


def construct_geojson_dict(
    df: pd.DataFrame,
    region_name: str = "REGION_NAME",
    metric: str = "IAGL_MEMBER_ID_BAEC_COUNT",
) -> dict:
    """
    Construct a GeoJSON dictionary from a DataFrame.

    Args:
        df (pd.DataFrame): The dataframe containing the data to be converted to GeoJSON.
        region_name (str): The column name for region names. Default is "REGION_NAME".
        metric (str): The column name for the metric to include in the GeoJSON properties. Default is "IAGL_MEMBER_ID_BAEC_COUNT".

    Returns:
        dict: A dictionary in GeoJSON format representing the features in the dataframe.
    """

    features = []
    for index, row in df.iterrows():
        # Convert the shapely.geometry.Polygon object to GeoJSON-compatible dictionary
        geometry = mapping(row["GEOMETRY"])

        # Construct a GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "region": row[region_name],
                metric: row[metric],
                # other properties as needed
            },
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}

    return geojson


def sigfig_round(number: float, sigfigs: int):
    """
    Round the number to the specified significant figures.

    Args:
        number (float): The number to be rounded.
        sigfigs (int): The number of significant figures to round to.

    Returns:
        float: The rounded number.
    """
    if number == 0:
        return 0
    else:
        return round(number, -int(np.floor(np.log10(abs(number))) - (sigfigs - 1)))
