from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datacube import Datacube
from datetime import datetime, date, timedelta
from shapely.geometry import shape
from datacube.utils.geometry import Geometry
from enum import Enum
import json
import pandas as pd

app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specify allowed origins, e.g., ["https://example.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Adjust to specify allowed HTTP methods
    allow_headers=["*"],  # Adjust to specify allowed headers
)


# Define an Enum for the level parameter
class LevelEnum(str, Enum):
    province = "province"
    district = "district"

# Define an Enum for granularity
class GranularityEnum(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"

# Initialize Open Data Cube instance
dc = Datacube(app="fastapi-odc")

with open("./vietnam-provinces-iso.json") as f:
    geojson_provinces_data = json.load(f)

with open("./vietnam-districts-iso.json") as f:
    geojson_districts_data = json.load(f)


@app.get("/rainfall/detail")
async def get_precipitation(
    layer_name: str = Query('imerg_e_10KM_daily', description="Name of the layer to query"),
    time: date = Query('2024-01-01', description="Date for the precipitation data"),
    geopolygon_id: int = Query(1, description="ID representing a specific polygon in JSON file"),
    level: LevelEnum = Query(LevelEnum.province, description="Level of the query, 'province' or 'district'"),
    output_crs: str = Query("EPSG:4326", description="Output coordinate reference system"),
    resolution_x: float = Query(-0.1, description="Resolution for x-axis (longitude)"),
    resolution_y: float = Query(0.1, description="Resolution for y-axis (latitude)")
):
    try:
        # Select appropriate GeoJSON data based on level
        geojson_data = geojson_provinces_data if level == LevelEnum.province else geojson_districts_data

        # Check if geopolygon_id is valid
        if geopolygon_id < 0 or geopolygon_id >= len(geojson_data["features"]):
            raise HTTPException(status_code=404, detail="Geopolygon ID not found in JSON data")

        # Extract geometry from the JSON file based on the ID
        selected_feature = geojson_data["features"][geopolygon_id]
        hanoi_geometry = shape(selected_feature["geometry"])
        geopolygon = Geometry(hanoi_geometry, crs="EPSG:4326")

        # Query for the specified day
        day_query = {
            "time": (time, time),  # Single date for time range
            "geopolygon": geopolygon,
            "output_crs": output_crs,
            "resolution": (resolution_x, resolution_y),
        }

        daily_dataset = dc.load(
            product=layer_name,
            **day_query,
            measurements=["Precipitation"],
        )

        # Query for the entire month
        start_of_month = time.replace(day=1)
        end_of_month = (time.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        month_query = {
            "time": (start_of_month, end_of_month),  # Entire month
            "geopolygon": geopolygon,
            "output_crs": output_crs,
            "resolution": (resolution_x, resolution_y),
        }

        monthly_dataset = dc.load(
            product=layer_name,
            **month_query,
            measurements=["Precipitation"],
        )

        # Calculate Current Rainfall
        if daily_dataset is not None and "Precipitation" in daily_dataset:
            current_rainfall = daily_dataset["Precipitation"].sum().item()
        else:
            current_rainfall = 0

        # Calculate Month Statistics
        if monthly_dataset is not None and "Precipitation" in monthly_dataset:
            total_rainfall = monthly_dataset["Precipitation"].sum().item()
            highest_rainfall = monthly_dataset["Precipitation"].max().item()
            lowest_rainfall = monthly_dataset["Precipitation"].min().item()
            days_in_month = (end_of_month - start_of_month).days + 1
            month_average_rainfall = total_rainfall / days_in_month
        else:
            total_rainfall = 0
            highest_rainfall = 0
            lowest_rainfall = 0
            month_average_rainfall = 0
            
        return {
            "current_rainfall": current_rainfall,
            "highest_recorded_rainfall": highest_rainfall,
            "lowest_recorded_rainfall": lowest_rainfall,
            "total_rainfall_for_the_month": total_rainfall,
            "month_average_rainfall": month_average_rainfall,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/rainfall/granularity")
async def get_rainfall_by_granularity(
    layer_name: str = Query('imerg_e_10KM_daily', description="Name of the layer to query"),
    start_date: date | None = Query(None, description="Optional start date for the data query"),
    end_date: date | None = Query(None, description="Optional end date for the data query"),
    geopolygon_id: int = Query(1, description="ID representing a specific polygon in JSON file"),
    granularity: GranularityEnum = Query(GranularityEnum.day, description="Granularity of the data"),
    level: LevelEnum = Query(LevelEnum.province, description="Level of the query, 'province' or 'district'"),
    output_crs: str = Query("EPSG:4326", description="Output coordinate reference system"),
    resolution_x: float = Query(-0.1, description="Resolution for x-axis (longitude)"),
    resolution_y: float = Query(0.1, description="Resolution for y-axis (latitude)")
):
    try:
        # Select appropriate GeoJSON data based on level
        geojson_data = geojson_provinces_data if level == LevelEnum.province else geojson_districts_data

        # Validate geopolygon_id
        if geopolygon_id < 0 or geopolygon_id >= len(geojson_data["features"]):
            raise HTTPException(status_code=404, detail="Geopolygon ID not found in JSON data")

        # Extract geometry from GeoJSON
        selected_feature = geojson_data["features"][geopolygon_id]
        geometry_shape = shape(selected_feature["geometry"])
        geopolygon = Geometry(geometry_shape, crs="EPSG:4326")

        # If start_date or end_date is not provided, set to the entire available range
        if start_date is None or end_date is None:
            # Find datasets to determine the time range
            datasets = dc.find_datasets(product=layer_name)  # Get datasets for the layer
            if not datasets:
                raise HTTPException(status_code=404, detail="No data available for the specified layer.")
            
            # Extract the time range (begin and end) from the first dataset
            time_ranges = [d.time for d in datasets if d.time is not None]
            if not time_ranges:
                raise HTTPException(status_code=404, detail="No valid time data found in datasets.")
            
            min_date = min([tr.begin for tr in time_ranges]).strftime('%Y-%m-%d')
            max_date = max([tr.end for tr in time_ranges]).strftime('%Y-%m-%d')
            
            start_date = start_date or min_date
            end_date = end_date or max_date

        # Prepare query for Open Data Cube
        query = {
            "time": (start_date, end_date),
            "geopolygon": geopolygon,
            "output_crs": output_crs,
            "resolution": (resolution_x, resolution_y),
        }

        # Load dataset from Open Data Cube
        dataset = dc.load(
            product=layer_name,
            **query,
            measurements=["Precipitation"],  # Replace with actual measurement name
        )

        # Check if dataset has data
        if dataset is None or dataset["Precipitation"].size == 0:
            return {"message": "No data available for the specified query."}

        # Convert dataset to a Pandas DataFrame
        precipitation = dataset["Precipitation"].to_dataframe().reset_index()

        # Ensure the 'time' column is a datetime object
        precipitation["time"] = pd.to_datetime(precipitation["time"], errors="coerce")

        # Check if there are any invalid dates
        if precipitation["time"].isnull().any():
            raise HTTPException(status_code=500, detail="Invalid time format in dataset.")

        # Aggregate data by granularity
        if granularity == GranularityEnum.day:
            precipitation_grouped = precipitation.groupby(precipitation["time"].dt.date)["Precipitation"].sum()
        elif granularity == GranularityEnum.week:
            precipitation_grouped = precipitation.groupby(precipitation["time"].dt.to_period("W"))["Precipitation"].sum()
        elif granularity == GranularityEnum.month:
            precipitation_grouped = precipitation.groupby(precipitation["time"].dt.to_period("M"))["Precipitation"].sum()
        elif granularity == GranularityEnum.quarter:
            precipitation_grouped = precipitation.groupby(precipitation["time"].dt.to_period("Q"))["Precipitation"].sum()
        elif granularity == GranularityEnum.year:
            precipitation_grouped = precipitation.groupby(precipitation["time"].dt.to_period("Y"))["Precipitation"].sum()

        # Convert grouped data to a dictionary for the response
        result = precipitation_grouped.reset_index()
        result["time"] = result["time"].astype(str)  # Convert time to string for JSON serialization
        response = result.to_dict(orient="records")

        return {"rainfall_data": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
