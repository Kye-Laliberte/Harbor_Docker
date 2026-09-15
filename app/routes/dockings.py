from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import DockingRead, DockingCreate
from app.services.docking_service import sev_create_docking, DockingService

router = APIRouter(prefix="/dockings", tags=["dockings"])


@router.get("/list", response_model=list[DockingRead],status_code=status.HTTP_200_OK)
def list_dockings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List dockings with optional pagination."""
    return DockingService(db=db,docking_id=None).sev_list_dockings( skip, limit)


@router.post("/create", response_model=DockingRead, status_code=status.HTTP_201_CREATED)
def create_docking(payload: DockingCreate, db: Session = Depends(get_db)):
    """Create a new docking."""
    return sev_create_docking(db, payload)


@router.put("/{docking_id}/arrive/", status_code=status.HTTP_202_ACCEPTED)
def dock_at_port(docking_id:int, db:Session =Depends(get_db)):
    docking = DockingService(db,docking_id=docking_id).status_update(docking_id)
    return {"status": "entered", "docking_id": docking.id}

@router.post("/{docking_id}/approve", response_model=DockingRead, status_code=status.HTTP_200_OK)
def approve_docking(docking_id: int, db: Session = Depends(get_db)):
    """Approve a pending docking before the ship enters."""
    return DockingService(db, docking_id=docking_id).approve()


@router.get("/{docking_id}/get", response_model=DockingRead,status_code=status.HTTP_200_OK)
def get_docking(docking_id: int, db: Session = Depends(get_db)):
    """Retrieve a docking by id."""
    return DockingService(db,docking_id).docking


@router.delete("/{docking_id}/delete", status_code=status.HTTP_204_NO_CONTENT)# dont use unless for cansalaton of a docking 
def delete_docking(docking_id: int, db: Session = Depends(get_db)):
    """Delete a docking by id."""
    dockingsev = DockingService(db,docking_id)

    if dockingsev.docking.departure_date is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="this is the curent docking") 

    dockingsev.sev_delete_docking()
    return None
