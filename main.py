# FastAPI backend logic
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import math
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/calculate")
async def calculate(file: UploadFile = File(...), mode: str = Form(...)):
    contents = await file.read()
    monthly_kwh = extract_kwh_from_pdf(contents)
    if not monthly_kwh:
        return JSONResponse(status_code=400, content={"error": "Could not find kWh usage in PDF."})

    daily_kwh = monthly_kwh / 30.0
    battery_size, units = recommend_battery(daily_kwh)

    result = {
        "dailyUsage": round(daily_kwh, 2),
        "batterySize": battery_size,
        "units": units
    }

    if mode == "solar":
        panel_count = math.ceil((daily_kwh / 4.5) * 1000 / 470)
        result["panelCount"] = panel_count

    return result

def extract_kwh_from_pdf(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.splitlines():
                    if "kWh" in line.lower():
                        numbers = [float(s.replace(",", "")) for s in line.split() if s.replace(",", "").replace(".", "").isdigit()]
                        for n in numbers:
                            if 100 < n < 5000:
                                return n
    return None

def recommend_battery(daily_kwh):
    sizes = [8, 16, 24, 32]
    for size in sizes:
        if daily_kwh <= size:
            return size, 1
    units = math.ceil(daily_kwh / 32)
    return 32, units