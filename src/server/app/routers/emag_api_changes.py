"""Admin-only API for separately approved, single-offer price submissions."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.core.security import require_admin
from app.services import emag_api_changes as service

router = APIRouter(prefix='/stores/{store_id}/api-changes', dependencies=[Depends(require_admin)])


class Proposal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    snapshot_id: str
    product_id: str
    changes: dict


class Approval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    digest: str = Field(pattern='^[a-f0-9]{64}$')
    note: str = Field(min_length=1, max_length=2000)


class Execution(BaseModel):
    model_config = ConfigDict(extra='forbid')
    digest: str = Field(pattern='^[a-f0-9]{64}$')
    confirmed: StrictBool


def _call(function, *args):
    try:
        return function(*args)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(409, 'Local evidence or configured credentials are unavailable') from exc


@router.get('')
def listing(store_id: str):
    return _call(service.listing, store_id)


@router.post('')
def prepare(store_id: str, body: Proposal, actor=Depends(require_admin)):
    return _call(service.prepare, store_id, body.snapshot_id, body.product_id, body.changes, str(actor))


@router.post('/{proposal_id}/approve')
def approve(store_id: str, proposal_id: str, body: Approval, actor=Depends(require_admin)):
    return _call(service.approve, store_id, proposal_id, body.digest, body.note, str(actor))


@router.post('/{proposal_id}/execute')
def execute(store_id: str, proposal_id: str, body: Execution, actor=Depends(require_admin)):
    if body.confirmed is not True:
        raise HTTPException(409, 'Explicit confirmation is required')
    return _call(service.live_execute, store_id, proposal_id, body.digest, body.confirmed, str(actor))


@router.post('/{proposal_id}/reconcile')
def reconcile(store_id: str, proposal_id: str, actor=Depends(require_admin)):
    return _call(service.live_reconcile, store_id, proposal_id, str(actor))
