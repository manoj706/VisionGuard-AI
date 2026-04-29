from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import authenticate, verify_token
from storage.models import AuthRequest, CameraConfig, SearchFilters


router = APIRouter(prefix="/api")
limiter = Limiter(key_func=get_remote_address)


@router.post("/auth/login")
async def login(payload: AuthRequest):
    return authenticate(payload)


@router.get("/cameras", dependencies=[Depends(verify_token)])
async def list_cameras(request: Request):
    store = request.app.state.event_store
    cameras = await store.list_cameras()
    persons = await store.get_persons()
    counts: dict[str, int] = {}
    for person in persons:
        counts[person.camera_id] = counts.get(person.camera_id, 0) + 1
    enriched = []
    for camera in cameras:
        enriched.append(camera.model_copy(update={"persons_tracked": counts.get(camera.id, 0)}))
    return enriched


@router.post("/cameras", dependencies=[Depends(verify_token)])
async def register_camera(camera: CameraConfig, request: Request):
    return await request.app.state.event_store.upsert_camera(camera)


@router.get("/cameras/{camera_id}/persons", dependencies=[Depends(verify_token)])
async def get_camera_persons(camera_id: str, request: Request):
    return await request.app.state.event_store.get_persons(camera_id)


@router.get("/persons", dependencies=[Depends(verify_token)])
async def get_all_persons(request: Request):
    return await request.app.state.event_store.get_persons()


@router.get("/persons/{global_id}", dependencies=[Depends(verify_token)])
async def get_person(global_id: str, request: Request):
    store = request.app.state.event_store
    person = await store.get_person(global_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"person": person, "journey": await store.get_journey(global_id)}


@router.get("/incidents", dependencies=[Depends(verify_token)])
async def list_incidents(request: Request):
    return await request.app.state.event_store.list_incidents()


@router.get("/incidents/{incident_id}", dependencies=[Depends(verify_token)])
async def get_incident(incident_id: str, request: Request):
    incident = await request.app.state.event_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/incidents/{incident_id}/acknowledge", dependencies=[Depends(verify_token)])
async def acknowledge_incident(incident_id: str, request: Request):
    incident = await request.app.state.event_store.acknowledge_incident(incident_id, "operator")
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/search", dependencies=[Depends(verify_token)])
@limiter.limit("10/minute")
async def search(request: Request, filters: SearchFilters):
    return await request.app.state.event_store.search(filters)


@router.get("/search/export", dependencies=[Depends(verify_token)])
@limiter.limit("5/minute")
async def export_search(request: Request):
    csv_content = await request.app.state.event_store.export_last_search_csv()
    response = PlainTextResponse(content=csv_content, media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="visionguard_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv"'
    )
    return response


@router.get("/crowd/heatmap", dependencies=[Depends(verify_token)])
async def crowd_heatmap(request: Request):
    return request.app.state.latest_heatmap


@router.get("/stats", dependencies=[Depends(verify_token)])
async def stats(request: Request):
    return await request.app.state.event_store.get_stats()


@router.get("/health", dependencies=[Depends(verify_token)])
async def health(request: Request):
    return await request.app.state.event_store.get_health()
