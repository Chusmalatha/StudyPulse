"""
Service for generating, prioritizing, and managing material-grounded study recommendations.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.db.database import get_database
from app.models.growth_recommendation import RecommendationModel, MaterialReferenceModel
from app.schemas.growth_recommendation import RecommendationResponse, MaterialReferenceSchema
from app.services.project_service import get_project
from app.services.growth_analysis_service import GrowthAnalysisService

logger = logging.getLogger(__name__)


class RecommendationService:
    """Generates material-grounded, prioritized recommendations based on real learning signals."""

    def __init__(self, db=None, growth_service: Optional[GrowthAnalysisService] = None):
        self.db = db or get_database()
        self.growth_service = growth_service or GrowthAnalysisService(self.db)

    async def generate_recommendations(
        self,
        project_id: str,
        user_id: str
    ) -> List[RecommendationResponse]:
        """
        Generates actionable, grounded study recommendations for a project.
        Evaluates growth analysis, repeated mistakes, learning goals, available PDF materials,
        and prior recommendations to prevent duplicates.
        """
        if self.db is None:
            raise RuntimeError("Database not initialized")

        await get_project(project_id, user_id)

        # 1. Run Growth Analysis to get concept states
        growth_summary = await self.growth_service.analyze_project_growth(project_id, user_id)

        # 2. Fetch project materials
        mat_cursor = self.db["materials"].find({"project_id": project_id, "user_id": user_id, "status": "READY"})
        if hasattr(mat_cursor, "to_list"):
            ready_materials = await mat_cursor.to_list(length=50)
        else:
            ready_materials = [m async for m in mat_cursor]

        # 3. Fetch project learning goal & user persistent goals
        project_doc = await self.db["projects"].find_one({"_id": ObjectId(project_id)})
        learning_goal = project_doc.get("learning_goal", "") if project_doc else ""

        # 4. Fetch existing active recommendations to prevent duplicate pending recommendations
        existing_cursor = self.db["recommendations"].find({
            "project_id": project_id,
            "user_id": user_id,
            "status": {"$in": ["PENDING", "IN_PROGRESS"]}
        })
        if hasattr(existing_cursor, "to_list"):
            existing_recs = await existing_cursor.to_list(length=100)
        else:
            existing_recs = [r async for r in existing_cursor]

        existing_keys = {(r.get("concept_id"), r.get("type")) for r in existing_recs}

        now = datetime.now(timezone.utc)

        # 5. Evaluate candidates for concepts requiring attention or low mastery
        for snapshot in growth_summary.snapshots:
            cid = snapshot.concept_id
            cname = snapshot.concept_name
            cat = snapshot.category

            # Target concepts needing attention or stable with low mastery
            if cat in ["REQUIRING_ATTENTION", "STABLE"] or (snapshot.current_mastery < 60.0 and snapshot.evidence_count > 0):
                # Candidate 1: Review Material (Grounded in PDF chunks)
                if ("REVIEW_MATERIAL" not in {t for c, t in existing_keys if c == cid}) and ready_materials:
                    # Ground page number by searching chunks for concept
                    chk = await self.db["chunks"].find_one({"project_id": project_id, "concept_ids": cid})
                    if not chk:
                        chk = await self.db["chunks"].find_one({"project_id": project_id, "chunk_text": {"$regex": cname, "$options": "i"}})

                    mat_refs = []
                    if chk:
                        mat_refs.append(
                            MaterialReferenceModel(
                                material_id=str(chk.get("material_id", "")),
                                filename=str(chk.get("filename", "Material.pdf")),
                                page_number=int(chk.get("page_number", 1))
                            )
                        )
                    elif ready_materials:
                        mat_refs.append(
                            MaterialReferenceModel(
                                material_id=str(ready_materials[0]["_id"]),
                                filename=ready_materials[0].get("filename", "Material.pdf"),
                                page_number=1
                            )
                        )

                    mat_title = f"Review Material for {cname}"
                    page_desc = f"Read page {mat_refs[0].page_number} in {mat_refs[0].filename}" if mat_refs else "Review source materials"
                    rec_doc = RecommendationModel(
                        user_id=user_id,
                        project_id=project_id,
                        concept_id=cid,
                        type="REVIEW_MATERIAL",
                        title=mat_title,
                        description=f"Your understanding of {cname} needs attention ({snapshot.explanation}).",
                        reason=snapshot.explanation,
                        action=f"Open {mat_refs[0].filename} and review page {mat_refs[0].page_number} to strengthen core concepts." if mat_refs else f"Review project materials for {cname}.",
                        material_references=mat_refs,
                        priority="HIGH" if cat == "REQUIRING_ATTENTION" else "MEDIUM",
                        status="PENDING",
                        created_at=now,
                        updated_at=now
                    )
                    r_dict = rec_doc.model_dump(by_alias=True, exclude={"id"})
                    await self.db["recommendations"].insert_one(r_dict)
                    existing_keys.add((cid, "REVIEW_MATERIAL"))

                # Candidate 2: Targeted Practice Quiz
                if ("PRACTICE_QUIZ" not in {t for c, t in existing_keys if c == cid}) and ready_materials:
                    rec_doc = RecommendationModel(
                        user_id=user_id,
                        project_id=project_id,
                        concept_id=cid,
                        type="PRACTICE_QUIZ",
                        title=f"Take Practice Quiz on {cname}",
                        description=f"Test your knowledge of {cname} to improve mastery score from {round(snapshot.current_mastery, 1)}%.",
                        reason=f"Current mastery is {round(snapshot.current_mastery, 1)}%. Targeted practice builds score confidence.",
                        action=f"Take a 5-question practice quiz targeting {cname}.",
                        material_references=[],
                        priority="HIGH" if snapshot.current_mastery < 50.0 else "MEDIUM",
                        status="PENDING",
                        created_at=now,
                        updated_at=now
                    )
                    r_dict = rec_doc.model_dump(by_alias=True, exclude={"id"})
                    await self.db["recommendations"].insert_one(r_dict)
                    existing_keys.add((cid, "PRACTICE_QUIZ"))

        # 6. Fetch and return active recommendations
        return await self.get_project_recommendations(project_id, user_id, auto_generate=False)

    async def get_project_recommendations(
        self,
        project_id: str,
        user_id: str,
        auto_generate: bool = True
    ) -> List[RecommendationResponse]:
        """Fetch all non-dismissed recommendations for a project."""
        if self.db is None:
            return []

        await get_project(project_id, user_id)

        cursor = self.db["recommendations"].find({
            "project_id": project_id,
            "user_id": user_id,
            "status": {"$in": ["PENDING", "IN_PROGRESS", "COMPLETED"]}
        }).sort("created_at", -1)

        if hasattr(cursor, "to_list"):
            raw_recs = await cursor.to_list(length=50)
        else:
            raw_recs = [r async for r in cursor]

        # Auto-generate initial recommendations if empty
        if not raw_recs and auto_generate:
            mat_ready = await self.db["materials"].find_one({"project_id": project_id, "user_id": user_id, "status": "READY"})
            if mat_ready:
                await self.generate_recommendations(project_id, user_id)
                return await self.get_project_recommendations(project_id, user_id, auto_generate=False)

        results: List[RecommendationResponse] = []
        for r in raw_recs:
            r_id = str(r["_id"])
            refs = [
                MaterialReferenceSchema(
                    material_id=str(ref.get("material_id", "")),
                    filename=ref.get("filename", ""),
                    page_number=ref.get("page_number", 1)
                )
                for ref in r.get("material_references", [])
            ]
            results.append(
                RecommendationResponse(
                    id=r_id,
                    project_id=str(r["project_id"]),
                    concept_id=str(r.get("concept_id")) if r.get("concept_id") else None,
                    type=r.get("type", "PRACTICE_QUIZ"),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    reason=r.get("reason", ""),
                    action=r.get("action", ""),
                    material_references=refs,
                    priority=r.get("priority", "MEDIUM"),
                    status=r.get("status", "PENDING"),
                    created_at=r.get("created_at"),
                    completed_at=r.get("completed_at")
                )
            )

        return results

    async def complete_recommendation(
        self,
        recommendation_id: str,
        project_id: str,
        user_id: str
    ) -> RecommendationResponse:
        """Mark a recommendation as COMPLETED."""
        if self.db is None:
            raise RuntimeError("Database not initialized")

        await get_project(project_id, user_id)
        now = datetime.now(timezone.utc)

        result = await self.db["recommendations"].find_one_and_update(
            {"_id": ObjectId(recommendation_id), "project_id": project_id, "user_id": user_id},
            {"$set": {"status": "COMPLETED", "completed_at": now, "updated_at": now}},
            return_document=True
        )

        if not result:
            raise ValueError("Recommendation not found")

        refs = [
            MaterialReferenceSchema(
                material_id=str(ref.get("material_id", "")),
                filename=ref.get("filename", ""),
                page_number=ref.get("page_number", 1)
            )
            for ref in result.get("material_references", [])
        ]

        return RecommendationResponse(
            id=str(result["_id"]),
            project_id=str(result["project_id"]),
            concept_id=str(result.get("concept_id")) if result.get("concept_id") else None,
            type=result.get("type", "PRACTICE_QUIZ"),
            title=result.get("title", ""),
            description=result.get("description", ""),
            reason=result.get("reason", ""),
            action=result.get("action", ""),
            material_references=refs,
            priority=result.get("priority", "MEDIUM"),
            status="COMPLETED",
            created_at=result.get("created_at"),
            completed_at=now
        )

    async def dismiss_recommendation(
        self,
        recommendation_id: str,
        project_id: str,
        user_id: str
    ) -> bool:
        """Dismiss a recommendation."""
        if self.db is None:
            raise RuntimeError("Database not initialized")

        await get_project(project_id, user_id)
        now = datetime.now(timezone.utc)

        res = await self.db["recommendations"].update_one(
            {"_id": ObjectId(recommendation_id), "project_id": project_id, "user_id": user_id},
            {"$set": {"status": "DISMISSED", "updated_at": now}}
        )

        return res.modified_count > 0
