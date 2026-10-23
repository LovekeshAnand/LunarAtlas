"""Listing 1 of the manuscript, verbatim. Set LUNARATLAS_API to target a local/staging server instead."""
import os

import requests

url = os.environ.get("LUNARATLAS_API", "https://apis.lunaratlas.in") + "/api/v1/spectrum"
params = {"measurement_id": "FI-20230825-104221-00-3",
          "lambda_min": 240.0, "lambda_max": 450.0,
          "zoom_level": 2, "als": True, "savgol": True}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
data = r.json()
for pt in data["data"][:5]:
    print(pt["wavelength_nm"], pt["intensity"])
