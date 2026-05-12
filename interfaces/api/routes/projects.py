import uuid
from fastapi import APIRouter, HTTPException

from interfaces.api.schemas import ProjectCreate, ProjectResponse
from memory.structured.models import Project, get_session

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(body: ProjectCreate):
    project_id = str(uuid.uuid4())[:8]
    session = get_session()
    project = Project(
        id=project_id,
        name=body.name,
        description=body.description,
        target_audience=body.target_audience,
        brand_voice=body.brand_voice,
    )
    session.add(project)
    session.commit()
    session.close()
    return ProjectResponse(
        id=project_id,
        name=body.name,
        description=body.description,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    session = get_session()
    projects = session.query(Project).order_by(Project.created_at.desc()).limit(50).all()
    session.close()
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    session = get_session()
    project = session.query(Project).filter_by(id=project_id).first()
    session.close()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat() if project.created_at else None,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    session = get_session()
    project = session.query(Project).filter_by(id=project_id).first()
    if not project:
        session.close()
        raise HTTPException(status_code=404, detail="Project not found")
    session.delete(project)
    session.commit()
    session.close()
    return {"status": "deleted", "id": project_id}
