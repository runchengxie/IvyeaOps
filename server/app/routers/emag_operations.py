from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from app.core.security import require_admin
from app.services import emag_operations as service
from app.services import emag_workspace, emag_jobs

router=APIRouter(dependencies=[Depends(require_admin)])


class Draft(BaseModel):
    model_config=ConfigDict(extra='forbid')
    snapshot_id:str
    kind:str
    product_id:str=''
    title:str=Field(min_length=1,max_length=200)
    body:str=Field(min_length=1,max_length=40000)


@router.get('/stores/{store_id}/workspace')
def workspace(store_id:str):
    try:return emag_workspace.view(store_id)
    except (OSError,ValueError) as exc:raise HTTPException(404,str(exc)) from exc


@router.post('/stores/{store_id}/drafts')
def draft(store_id:str,body:Draft,actor=Depends(require_admin)):
    try:return emag_workspace.save_draft(store_id,**body.model_dump(),actor=str(actor))
    except (OSError,ValueError) as exc:raise HTTPException(409,str(exc)) from exc


@router.get('/stores/{store_id}/job')
def job(store_id:str):
    try:return emag_jobs.latest(store_id)
    except (OSError,ValueError) as exc:raise HTTPException(404,str(exc)) from exc


class Update(BaseModel):
    model_config=ConfigDict(extra='forbid')
    snapshot_id:str
    state:str
    revision:int=Field(ge=0)
    note:str=Field(min_length=1,max_length=4000)
    review_snapshot_id:str|None=None


@router.get('/stores')
def stores():
    return service.stores()


@router.get('/stores/{store_id}')
def board(store_id:str):
    try:
        return service.board(store_id)
    except (OSError,ValueError) as exc:
        raise HTTPException(404,str(exc)) from exc


@router.post('/stores/{store_id}/issues/{issue_id}')
def update(store_id:str,issue_id:str,body:Update,actor=Depends(require_admin)):
    try:
        return service.transition(store_id,body.snapshot_id,issue_id,body.state,body.revision,body.note,str(actor),body.review_snapshot_id)
    except (OSError,ValueError) as exc:
        raise HTTPException(409,str(exc)) from exc
