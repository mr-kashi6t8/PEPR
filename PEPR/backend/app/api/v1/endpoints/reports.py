from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.infrastructure.database import get_db
from app.models.reports import GeneratedReport
from app.schemas.reports import ReportResponse, ReportDetail
from app.services.reports.generator import report_generator

router = APIRouter()

@router.post("/generate")
async def trigger_report_generation(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Manually triggers the report generation process in the background.
    """
    background_tasks.add_task(report_generator.generate_weekly_report)
    return {"message": "Report generation triggered successfully. It will be available shortly."}

@router.post("/{report_id}/regenerate")
async def trigger_report_regeneration(report_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Manually triggers regeneration of an existing report, creating a new version.
    """
    report = await db.get(GeneratedReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    background_tasks.add_task(report_generator.regenerate_report, report_id)
    return {"message": f"Report regeneration triggered for {report_id}."}

@router.get("/", response_model=List[ReportResponse])
async def list_reports(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
    List all generated reports with their status.
    """
    result = await db.execute(select(GeneratedReport).order_by(GeneratedReport.created_at.desc()).offset(skip).limit(limit))
    reports = result.scalars().all()
    return reports

@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the details and structured JSON of a specific report.
    """
    report = await db.get(GeneratedReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/{report_id}/pdf")
async def download_report_pdf(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Download the generated PDF for a specific report.
    """
    report = await db.get(GeneratedReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.status != "COMPLETED" or not report.pdf_path:
        raise HTTPException(status_code=400, detail="Report PDF is not ready yet or generation failed.")
        
    if not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk.")
        
    return FileResponse(
        path=report.pdf_path, 
        filename=f"PEPR_Weekly_Report_{report.report_date}.pdf",
        media_type="application/pdf"
    )

@router.delete("/{report_id}")
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a generated report record from the database and removes physical PDF/HTML files from disk.
    """
    report = await db.get(GeneratedReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Clean up physical files from disk
    if report.pdf_path and os.path.exists(report.pdf_path):
        try:
            os.remove(report.pdf_path)
        except Exception:
            pass

    if report.html_path and os.path.exists(report.html_path):
        try:
            os.remove(report.html_path)
        except Exception:
            pass

    await db.delete(report)
    await db.commit()
    return {"message": f"Report {report_id} deleted successfully."}
