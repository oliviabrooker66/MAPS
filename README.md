# MAPS: UK Region Mapping Tool 🗺️

This repository provides tools to visualise and analyse customer data across UK regions using Python, Geopandas, and Streamlit. The project supports creating interactive maps based on customer metrics, either through a Jupyter Notebook, a standalone Python script, or a web-based interface.

## 🌍 Features

- **Geospatial Data Processing**: Uses Geopandas to merge customer data with UK regional shapes.
- **Aggregation and Analysis**: Supports aggregation by sum, average, and member count.
- **Interactive Maps**: Generates heatmaps using Plotly for visualisation.
- **Web Interface**: Streamlit app for an interactive map creation experience.

## 📁 Repository Structure

- `archive/` - Directory for archived files and backups.
- `location_data/` - Contains UK postcode and region shape data.
- `outputs/` - Directory where generated maps are saved.
- `app.py` - Streamlit application for web-based map generation.
- `customer_dummy.csv` - Sample customer dataset.
- `maps.ipynb` - Jupyter Notebook for step-by-step map creation.
- `maps.py` - Python script for automated map generation via command line.
- `requirements.txt` - List of dependencies required to run the project.
- `utils.py` - Utility functions for data processing and visualisation.

## 🛠️ Installation

### Prerequisites

Ensure you have Python 3.8+ installed. Install dependencies using:

```sh
pip install -r requirements.txt
```

## 🚀  Usage

### 1. Command-Line Map Generation

Run the script with required arguments

```sh
python maps.py <region_shape_level> <metric> <agg_type>
```

Example:

```sh
python maps.py county BALANCE SUM
```

### 2. Jupyter Notebook

Navigate to the root directory and open `maps.ipynb` for step-by-step map creation.

### 3. Web App (Streamlit)

Launch the web interface using:

```sh
streamlit run app.py
```

Follow the on-screen instructions to generate interactive maps interactively.

## 💾 Saving Maps

After running the script or using the Streamlit app, maps can be saved as interactive HTML files in the `outputs/` directory.

## 🤝 Contributing

Feel free to submit pull requests to improve functionality, enhance visualisations, or add new features.


