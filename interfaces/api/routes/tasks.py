from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from interfaces.api.schemas import TaskRequest, TaskResponse
from agent.orchestrator import SEOAgent, AgentContext
from agent.planner import generate_task_id

router = APIRouter(prefix="/tasks", tags=["tasks"])

# In-memory task store (replace with DB for production)
_tasks: dict[str, dict] = {}


@router.post("", response_model=TaskResponse)
async def create_task(body: TaskRequest):
    task_id = generate_task_id()
    _tasks[task_id] = {"status": "pending", "result": None, "error": None}

    try:
        agent = SEOAgent()
        ctx = AgentContext(project_id=body.project_id, user_id=body.user_id, task_id=task_id)
        result = await agent.run(body.task, context=ctx)
        _tasks[task_id] = {"status": "completed", "result": result, "error": None}
    except Exception as e:
        _tasks[task_id] = {"status": "error", "result": None, "error": str(e)}

    return TaskResponse(
        task_id=task_id,
        status=_tasks[task_id]["status"],
        result=_tasks[task_id].get("result"),
        error=_tasks[task_id].get("error"),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    t = _tasks.get(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(task_id=task_id, **t)


@router.get("")
async def list_tasks():
    return {"tasks": [{"task_id": k, **v} for k, v in _tasks.items()]}
