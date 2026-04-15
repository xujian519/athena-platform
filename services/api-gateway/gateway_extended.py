from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Lightweight, self-contained gateway extension for batch register,
# dynamic routes, health, dependencies and discovery wiring.


# ----------------- Models ------------------
class ServiceRegistration(BaseModel):
    name: str
    host: str
    port: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchRegisterRequest(BaseModel):
    services: list[ServiceRegistration]


class ServiceInstance(BaseModel):
    id: str
    service_name: str
    host: str
    port: int
    weight: int = 1
    status: str = "UP"
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateServiceInstance(BaseModel):
    host: str | None = None
    port: int | None = None
    weight: int | None = None
    metadata: dict[str, Any] | None = None


class RouteRule(BaseModel):
    id: str
    path: str
    target_service: str
    methods: list[str] = Field(default_factory=lambda: ["GET"])
    weight: int = 1


class DependencySpec(BaseModel):
    service: str
    depends_on: list[str] = Field(default_factory=list)


# --------------- In-memory stores ---------------
_registry: dict[str, dict[str, Any]] = {
    "instances": {},  # id -> ServiceInstance
    "routes": {},  # id -> RouteRule
    "dependencies": {},  # service -> [dependencies]
}

gateway_ext = APIRouter(prefix="/api", tags=["Gateway Extended"])


# --------------- Helpers ---------------
def _pick_instance(service_name: str) -> ServiceInstance | None:
    pool: list[ServiceInstance] = [
        i
        for i in _registry["instances"].values()
        if i["service_name"] == service_name and i["status"] == "UP"
    ]  # type: ignore
    if not pool:
        return None
    # Simple round-robin via a static pointer per service
    if not hasattr(_pick_instance, "pointers"):  # type: ignore
        _pick_instance.pointers = {}
    idx = _pick_instance.pointers.get(service_name, 0)
    inst = pool[idx % len(pool)]
    _pick_instance.pointers[service_name] = (idx + 1) % max(1, len(pool))
    return ServiceInstance(**inst)


def _to_api(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.dict()
    if isinstance(obj, dict):
        return obj
    return obj


# --------------- Endpoints ---------------
@gateway_ext.post("/services/batch_register")
async def batch_register(req: BatchRegisterRequest) -> dict[str, Any]:
    results: list[ServiceInstance] = []
    for svc in req.services:
        sid = f"{svc.name}:{svc.host}:{svc.port}:{len(_registry['instances']) + 1}"
        inst = ServiceInstance(
            id=sid, service_name=svc.name, host=svc.host, port=svc.port, metadata=svc.metadata
        )
        _registry["instances"][sid] = inst.dict()
        results.append(inst)
    return {"success": True, "data": [r.dict() for r in results]}


@gateway_ext.get("/services/instances")
async def list_instances() -> dict[str, Any]:
    items = list(_registry["instances"].values())
    return {"success": True, "data": items}


@gateway_ext.get("/services/instances/{inst_id}")
async def get_instance(inst_id: str) -> dict[str, Any]:
    inst = _registry["instances"].get(inst_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    return {"success": True, "data": inst}


@gateway_ext.put("/services/instances/{inst_id}")
async def update_instance(inst_id: str, payload: UpdateServiceInstance) -> dict[str, Any]:
    inst = _registry["instances"].get(inst_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    if payload.host is not None:
        inst["host"] = payload.host
    if payload.port is not None:
        inst["port"] = payload.port
    if payload.weight is not None:
        inst["weight"] = payload.weight
    if payload.metadata is not None:
        inst["metadata"].update(payload.metadata)
    _registry["instances"][inst_id] = inst
    return {"success": True, "data": inst}


@gateway_ext.delete("/services/instances/{inst_id}")
async def delete_instance(inst_id: str) -> dict[str, Any]:
    if inst_id in _registry["instances"]:
        del _registry["instances"][inst_id]
        return {"success": True, "data": {"deleted": inst_id}}
    raise HTTPException(status_code=404, detail="Instance not found")


@gateway_ext.get("/routes")
async def list_routes() -> dict[str, Any]:
    return {"success": True, "data": list(_registry["routes"].values())}


@gateway_ext.post("/routes")
async def create_route(route: RouteRule) -> dict[str, Any]:
    _registry["routes"][route.id] = route.dict()
    return {"success": True, "data": route.dict()}


@gateway_ext.patch("/routes/{route_id}")
async def update_route(route_id: str, route: RouteRule) -> dict[str, Any]:
    if route_id not in _registry["routes"]:
        raise HTTPException(status_code=404, detail="Route not found")
    _registry["routes"][route_id] = route.dict()
    return {"success": True, "data": route.dict()}


@gateway_ext.post("/config/load")
async def load_config(text: str) -> dict[str, Any]:
    # Accept YAML/JSON via text; try YAML first, then JSON
    try:
        import yaml  # type: ignore

        cfg = yaml.safe_load(text)
    except Exception:
        cfg = json.loads(text)
    return {"success": True, "data": cfg}


@gateway_ext.post("/dependencies")
async def set_dependencies(dep: DependencySpec) -> dict[str, Any]:
    service = dep.service
    _registry["dependencies"].setdefault(service, [])
    for d in dep.depends_on:
        if d not in _registry["dependencies"][service]:
            _registry["dependencies"][service].append(d)
    return {
        "success": True,
        "data": {"service": service, "dependencies": _registry["dependencies"][service]},
    }


@gateway_ext.get("/dependencies/{service}")
async def get_dependencies(service: str) -> dict[str, Any]:
    deps = _registry["dependencies"].get(service, [])
    return {"success": True, "data": {"service": service, "dependencies": deps}}


@gateway_ext.get("/health")
async def health() -> dict[str, Any]:
    info = {
        "instances": len(_registry["instances"]),
        "routes": len(_registry["routes"]),
        "dependencies": _registry["dependencies"],
        "status": "UP" if len(_registry["instances"]) > 0 else "NOT_READY",
    }
    return {"success": True, "data": info}


@gateway_ext.post("/health/alerts")
async def health_alert(message: str) -> dict[str, Any]:
    # In real deployment, trigger alerting system
    return {"success": True, "data": {"alert": message}}
