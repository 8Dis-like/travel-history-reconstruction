# Sprint 3 Kickoff & Final Deliverables Sync (Agenda)

**Project:** Travel History Reconstruction from Travel Documents  
**Meeting Type:** Sprint Kickoff & Sync  
**Duration:** 30 min  
**Date/Time:** August 3, 2026, 7:00 p.m. PST 
**Participants:** Hao Zhang (Zagho), Zuyan Tao (Benjamin), Wilson Tee  

---

## 1. Sprint 2 Reflection (What We Achieved)

### 1.1 Technical Milestones Reached
- **Multi-Rotation Strategy:** Successfully implemented and integrated. YOLO detection recall jumped from 0% on rotated/raw passport pages to 100% by forcing the image through 4 rotations dynamically.
- **VLM Pipeline Integration:** Re-architected the backend to support dynamic swapping between Cloud APIs (Gemini/Claude) and Local Offline Models (Qwen2-VL). 
- **System Testing & Benchmarking:** Conducted extensive end-to-end testing on synthetic scenes. Proved that Cloud APIs yield 100% accuracy, while the 2B local offline model drops to ~21% timeline accuracy due to hardware constraints on noisy data.
- **End-to-End Connectivity:** The pipeline from Frontend (React) -> API (FastAPI) -> Detection (YOLO) -> Extraction (VLM) -> Timeline (Linked List) is structurally complete and operational on `master`.

### 1.2 Lessons Learned
- Real-world data is significantly noisier than synthetic data; the system relies heavily on the VLM's zero-shot reasoning capabilities to bridge the gap.
- API rate limits (e.g., Gemini `429 Resource Exhausted`) are pipeline killers. We must prepare a stable, authenticated environment for the final demo.

---

## 2. Sprint 3 Objectives (The Final Push)

As we enter Sprint 3, our primary focus shifts from **core technical development** to **system polish and final deliverables**. 

### 2.1 Final VLM Decision for Demo
- Agree to use the **Cloud API (Gemini/Claude)** for the live Capstone demo to guarantee high accuracy and reliability.
- The **Local VLM (Qwen2-VL)** capability will be heavily featured in the final report as a technical achievement for "offline/secure" environments, even if not run live due to VRAM limits.

### 2.2 Final Deliverables
- **The Final Report:** A comprehensive documentation of our methodology, architecture, and testing results.
- **The Capstone Presentation:** Slides detailing the problem, our solution, and our engineering journey.
- **The Live Demo:** A polished, fully functional web application reconstructing a travel history in real-time.

### 2.3 Open Issues & Discussion Points
- **Final Analytical Report Output:** According to the initial proposal, the final system must output a "Detailed analytical report with extracted data, timeline reconstruction, unreadable or uncertain items, and data quality observations". We need to discuss how this will be presented to the end-user (e.g., downloadable PDF vs. interactive dashboard) and how to best flag "unreadable or uncertain items".

---

## 3. Work Split (Final Deliverables & Report Authority)

To ensure all final deliverables are completed efficiently, responsibilities are split as follows:

*   **Hao Zhang (Zagho) — Final Capstone Report & QA:**
    *   **Report Authority:** Take full ownership of drafting and consolidating the entire Final Capstone Report to ensure general integrity and cohesive flow across all sections (System Architecture, UX, Reliability, etc.).
    *   **Review Management:** Encourage and coordinate with Benjamin and Wilson to check, monitor, and suggest revisions to the report drafts.
*   **Zuyan Tao (Benjamin) — Backend Finalization & Demo Prep:**
    *   **Backend Polish:** Finalize API endpoints, linked-list timeline logic, and VLM integration stability.
    *   **Demo Prep:** Prepare the live demo backend environments, secure API keys, and ensure it runs flawlessly on presentation day without rate limits.
*   **Wilson Tee — Frontend Polish & Presentation Design:**
    *   **Frontend Upgrade:** Polish the React frontend (CSS/UI flows) to provide a "wow" factor for the live demo. 
    *   **Presentation:** Lead the design, visual assets, and structure of the Capstone Presentation slides.

---

## 4. Sprint 3 Logistics & Milestones

- **Environment Freeze:** Avoid massive architectural changes to `master` to ensure stability for the demo.
- **Milestone 1:** Complete drafts of individual report sections by **August 18**.
- **Milestone 2:** Frontend/Demo freeze and presentation slide draft by **August 23**.
- **Milestone 3:** Full Team Presentation Drill on **August 24**.

---

## 5. Action Items & Next Steps

| # | Action Item | Owner | Due |
|---|---|---|---|
| 1 | Upgrade frontend UI for the final demo (interactive timeline) | Wilson | Aug 9 |
| 2 | Clean up backend API and ensure it runs flawlessly on demo data | Benjamin | Aug 9 |
| 3 | Secure API keys/quota to prevent rate limits during the live demo | Benjamin | Aug 9 |
| 4 | Finished sections for the Final Capstone Report | Hao | Aug 16 |
| 5 | Compile initial draft of the Capstone Presentation Slides | Wilson | Aug 20 |
| 6 | Lead Presentation Drill | Hao | Aug 23 |

---

*Agenda drafted for Sprint 3 Kickoff. Minutes to be appended post-meeting.*
