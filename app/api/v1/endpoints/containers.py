from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from app.dependencies import get_container_service, get_info_from_token
from app.models import UserPermissions
from app.models.containers import Container, ContainerCreate, ContainerUpdate
from app.service.containers import ContainerService


router = APIRouter(prefix="/containers", tags=["containers"])


@router.get("/", response_model=list[Container])
async def get_containers(
    is_active: Optional[bool] = Query(None),
    user: UserPermissions = Depends(get_info_from_token),
    service: ContainerService = Depends(get_container_service)
):
    """Получить список доступных коробок"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.get_containers(is_active)


@router.get("/{container_id}", response_model=Container)
async def get_container(
    container_id: int,
    user: UserPermissions = Depends(get_info_from_token),
    service: ContainerService = Depends(get_container_service)
):
    """Получить информацию о конкретной коробке"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    container = await service.get_container(container_id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container


@router.post("/", response_model=Container, status_code=201)
async def create_container(
    container: ContainerCreate,
    user: UserPermissions = Depends(get_info_from_token),
    service: ContainerService = Depends(get_container_service)
):
    """Создать новую запись о коробке"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.create_container(container)


@router.put("/{container_id}", response_model=Container)
async def update_container(
    container_id: int,
    container: ContainerUpdate,
    user: UserPermissions = Depends(get_info_from_token),
    service: ContainerService = Depends(get_container_service)
):
    """Обновить информацию о коробке"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    updated = await service.update_container(container_id, container)
    if not updated:
        raise HTTPException(status_code=404, detail="Container not found")
    return updated


@router.delete("/{container_id}")
async def delete_container(
    container_id: int,
    user: UserPermissions = Depends(get_info_from_token),
    service: ContainerService = Depends(get_container_service)
):
    """Удалить коробку (деактивировать)"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    success = await service.delete_container(container_id)
    if not success:
        raise HTTPException(status_code=404, detail="Container not found")
    return {"message": "Container deleted successfully"}
