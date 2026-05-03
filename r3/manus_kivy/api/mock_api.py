from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI()

# Mock Data
users = {"vega": "vega"}
rfid_tags = []
inventories = []
locations = []
inspections = []

class LoginRequest(BaseModel):
    username: str
    password: str

class RFIDTagCreate(BaseModel):
    rfid_code: str

class InventoryCreate(BaseModel):
    rfid_tag: int # ID of RFIDTag
    name: str
    detail: Optional[str] = ""

class LocationCreate(BaseModel):
    rfid_tag: int # ID of RFIDTag
    name: str
    description: Optional[str] = ""

class InspectionCreate(BaseModel):
    location_rfid: str
    found_rfids: List[str]

@app.post("/api/login/")
async def login(req: LoginRequest):
    if users.get(req.username) == req.password:
        return {"token": "mock-token-123"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/RFIDTags/")
async def create_rfid(req: RFIDTagCreate):
    tag = {"id": len(rfid_tags) + 1, "rfid_code": req.rfid_code}
    rfid_tags.append(tag)
    return tag

@app.get("/api/RFIDTags/")
async def list_rfids():
    return rfid_tags

@app.post("/api/inventory/")
async def create_inventory(req: InventoryCreate):
    item = {"id": len(inventories) + 1, **req.dict()}
    inventories.append(item)
    return item

@app.post("/api/Locations/")
async def create_location(req: LocationCreate):
    loc = {"id": len(locations) + 1, **req.dict()}
    locations.append(loc)
    return loc

@app.post("/api/inspections/")
async def create_inspection(req: InspectionCreate):
    insp = {"id": len(inspections) + 1, "message": "ตรวจสอบสำเร็จ", "missing_count": 0}
    inspections.append(insp)
    return insp

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
