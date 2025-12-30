from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_container_service
from app.models.containers import Container, ContainerCreate, ContainerUpdate
from app.service.containers import ContainerService


router = APIRouter(prefix="/containers", tags=["containers"])


@router.get("/", response_model=list[Container])
async def get_containers(
    is_active: Optional[bool] = Query(None),
    service: ContainerService = Depends(get_container_service)
):
    """Получить список доступных коробок"""
    return await service.get_containers(is_active)


@router.get("/{container_id}", response_model=Container)
async def get_container(
    container_id: int,
    service: ContainerService = Depends(get_container_service)
):
    """Получить информацию о конкретной коробке"""
    container = await service.get_container(container_id)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container


@router.post("/", response_model=Container, status_code=201)
async def create_container(
    container: ContainerCreate,
    service: ContainerService = Depends(get_container_service)
):
    """Создать новую запись о коробке"""
    return await service.create_container(container)


@router.put("/{container_id}", response_model=Container)
async def update_container(
    container_id: int,
    container: ContainerUpdate,
    service: ContainerService = Depends(get_container_service)
):
    """Обновить информацию о коробке"""
    updated = await service.update_container(container_id, container)
    if not updated:
        raise HTTPException(status_code=404, detail="Container not found")
    return updated


@router.delete("/{container_id}")
async def delete_container(
    container_id: int,
    service: ContainerService = Depends(get_container_service)
):
    """Удалить коробку (деактивировать)"""
    success = await service.delete_container(container_id)
    if not success:
        raise HTTPException(status_code=404, detail="Container not found")
    return {"message": "Container deleted successfully"}
