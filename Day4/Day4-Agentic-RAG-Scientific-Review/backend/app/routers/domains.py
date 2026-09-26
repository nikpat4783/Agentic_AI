from fastapi import APIRouter, Depends

from app.domains.config import list_domains
from app.models import User
from app.schemas import DomainOut
from app.security import get_current_user

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[DomainOut])
def get_domains(_current_user: User = Depends(get_current_user)):
    return [
        DomainOut(
            id=d.id,
            name=d.name,
            description=d.description,
            example_questions=d.example_questions,
        )
        for d in list_domains()
    ]
