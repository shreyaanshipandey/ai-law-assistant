from fastapi import APIRouter, Query

router = APIRouter(prefix="/helplines", tags=["Helpline Directory"])

HELPLINES = [
    {"name": "National Cybercrime Helpline", "number": "1930", "category": "Cybercrime",
     "description": "Report online financial fraud and cybercrime incidents.", "available": "24x7"},
    {"name": "Women Helpline (All India)", "number": "1091", "category": "Women Safety",
     "description": "Assistance for women in distress.", "available": "24x7"},
    {"name": "Emergency Response Support System", "number": "112", "category": "Emergency",
     "description": "Unified emergency number for police, fire, and medical emergencies.", "available": "24x7"},
    {"name": "NALSA Legal Aid Helpline", "number": "15100", "category": "Free Legal Aid",
     "description": "National Legal Services Authority — free legal aid and advice.", "available": "24x7"},
    {"name": "Child Helpline", "number": "1098", "category": "Child Safety",
     "description": "Support and rescue for children in distress.", "available": "24x7"},
    {"name": "Senior Citizen Helpline", "number": "14567", "category": "Senior Citizens",
     "description": "Assistance and grievance redressal for elderly citizens.", "available": "24x7"},
    {"name": "Domestic Violence Helpline", "number": "181", "category": "Women Safety",
     "description": "Women's helpline for domestic abuse and harassment cases.", "available": "24x7"},
    {"name": "Anti-Human Trafficking Helpline", "number": "1098", "category": "Human Trafficking",
     "description": "Report suspected trafficking or bonded labour cases.", "available": "24x7"},
    {"name": "Railway Protection Helpline", "number": "139", "category": "Travel Safety",
     "description": "Security assistance on Indian Railways.", "available": "24x7"},
    {"name": "National Human Rights Commission", "number": "011-23385368", "category": "Human Rights",
     "description": "Report human-rights violations to the NHRC.", "available": "Business hours"},
]


@router.get("/")
async def get_helplines(category: str | None = Query(default=None), q: str | None = Query(default=None)):
    results = HELPLINES
    if category:
        results = [h for h in results if h["category"].lower() == category.lower()]
    if q:
        q_lower = q.lower()
        results = [
            h for h in results
            if q_lower in h["name"].lower() or q_lower in h["description"].lower()
        ]
    return {"count": len(results), "helplines": results}


@router.get("/categories")
async def get_categories():
    return sorted({h["category"] for h in HELPLINES})
