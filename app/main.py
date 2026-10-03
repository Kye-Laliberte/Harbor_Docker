from fastapi import Depends, FastAPI

from app.core.security import require_api_key
from app.routes.docks import router as docks_router
from app.routes.dockings import router as dockings_router
from app.routes.harbors import router as harbors_router
from app.routes.ships import router as ships_router
from app.routes.voyages import router as voyages_router

app = FastAPI(title="Harbor API", dependencies=[Depends(require_api_key)])

app.include_router(ships_router)
app.include_router(harbors_router)
app.include_router(docks_router)
app.include_router(dockings_router)
app.include_router(voyages_router)


@app.get("/")
def root():
    return {"message": "Harbor API"}