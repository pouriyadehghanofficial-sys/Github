from fastapi import FastAPI
from src.user_service import user_router
from src.data_service import data_router
from src.analytics_service import analytics_router
from src.export_service import export_router

app = FastAPI()

app.include_router(user_router)
app.include_router(data_router)
app.include_router(analytics_router)
app.include_router(export_router)