"""
Router: /api/statistics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import MonthlyStats
from .. import service

router = APIRouter(prefix="/api/statistics", tags=["Statistics"])


@router.get("/monthly", response_model=MonthlyStats,
            summary="Monatsstatistiken abrufen")
def monthly_stats(db: Session = Depends(get_db)):
    """
    **GET /api/statistics/monthly**
    Gibt aggregierte Statistiken zurück:
    - Gesamtanzahl Aufgaben
    - Abgeschlossene / Aktive / Archivierte
    - Überfällige
    - Längste Check-in-Serie
    - Gewohnheits-Fortschritt (für Donut-Charts)
    - Monatliche Check-in-Aggregation (für Balkendiagramm)
    """
    return service.get_monthly_stats(db)
