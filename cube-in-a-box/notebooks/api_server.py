from fastapi import FastAPI
from pydantic import BaseModel
from datacube import Datacube
from typing import List, Tuple, Optional
from datetime import datetime
import uvicorn

app = FastAPI()
dc = Datacube(app="rainfall_api")

# Define a model for the request parameters
class RainfallRequest(BaseModel):
    bbox: List[float]  # Example: [104.7765, 10.1846, 105.574, 10.9622]
    geometry: dict     # GeoJSON-like structure
    start_time: str    # Example: "2021-01-01"
    end_time: str      # Example: "2021-12-31"
    dataset_type: str  # Example: "imerg_e_10KM_daily"
    layer_name: str

# Endpoint to get rainfall data
@app.post("/rainfall")
async def get_rainfall(request: RainfallRequest):
    # Parse input data
    start_time = datetime.fromisoformat(request.start_time)
    end_time = datetime.fromisoformat(request.end_time)
    layer_name = request.layer_name
    dataset_type = request.dataset_type  # Specify the dataset type
    bbox = request.bbox

    # Define the search parameters using bbox and dataset type
    query = {
        "product": dataset_type,  # Use the dataset_type parameter
        "time": (start_time, end_time),
        "longitude": (bbox[0], bbox[2]),  # Min lon, Max lon
        "latitude": (bbox[1], bbox[3]),   # Min lat, Max lat
    }

    # Load the data
    data = dc.load(**query)

    if data is None or len(data.dims) == 0:
        return {"error": "No data found for the specified parameters."}

    # Assume rainfall data is in 'rainfall' variable
    total_rainfall = data["rainfall"].sum().item()

    return {
        "total_rainfall": total_rainfall,
        "bbox": request.bbox,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "dataset_type": request.dataset_type
    }

# Run the API
uvicorn.run(app, host="0.0.0.0", port=8000)
