# Athena Gateway Extended - API for Microservice Auto-Registration and Discovery

Scope: Extend the existing FastAPI-based Athena Gateway to support automatic service discovery, batch registration, dynamic routing, health checks, and inter-service dependencies.

Key components:
- Batch service registration endpoint
- Discovery middleware (HTTP-based and file-based fallbacks)
- Service instance management API (view, update, delete)
- Dynamic routing updates and validation
- Load balancing weights and strategies per service
- Dependency management for inter-service calls
- YAML/JSON configuration loading for service definitions
- Health monitoring and alert hooks

API surface (examples):
- POST /api/services/batch_register
- GET /api/services/instances
- PUT /api/services/instances/{inst_id}
- DELETE /api/services/instances/{inst_id}
- GET /api/routes
- POST /api/routes
- PATCH /api/routes/{route_id}
- POST /api/config/load
- POST /api/dependencies
- GET /api/dependencies/{service}
- GET /api/health
- POST /api/health/alerts

Notes:
- All endpoints return a consistent APIResponse envelope with fields: success, data, error, code.
- The implementation uses in-memory registries suitable for development and testing. For production, replace with persistent storage and proper authentication/authorization.
- The extension is designed to be backward compatible with existing gateway APIs; existing features remain functional.

Migration & integration:
- To enable in the current app, import gateway_ext_router from gateway_extended and mount it on the main FastAPI app:
  from gateway_extended import gateway_ext
  app.include_router(gateway_ext)
