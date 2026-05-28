# Queue Calling Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the initial full-stack scaffold for a multi-merchant queue calling and light cashier platform.

**Architecture:** The backend owns business state transitions for meal-session numbers and exposes REST APIs. Vue admin and uni-app customer clients start as runnable shells with route maps and UI tokens aligned to the supplied prototypes.

**Tech Stack:** Python 3.8, FastAPI, SQLAlchemy, MySQL-ready configuration, Redis-ready configuration, Vue 3, Vite, Element Plus, uni-app.

---

### Task 1: Backend Domain Scaffold

**Files:**
- Create: `backend/app/domain/queue.py`
- Create: `backend/tests/test_queue_domain.py`
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`

- [ ] **Step 1: Write failing domain tests**

Test queue number lifecycle: occupied, preparing, called, dining, checkout requested, paid, completed, and adding items before payment.

- [ ] **Step 2: Run backend tests**

Run: `python -m pytest backend/tests/test_queue_domain.py -v`
Expected: fail because `backend.app.domain.queue` does not exist.

- [ ] **Step 3: Implement queue domain**

Define `QueueStatus`, `LineItem`, `MealSession`, and transition methods with validation.

- [ ] **Step 4: Run backend tests again**

Run: `python -m pytest backend/tests/test_queue_domain.py -v`
Expected: all tests pass.

### Task 2: API Skeleton

**Files:**
- Create: `backend/app/api/routes.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_api_health.py`

- [ ] **Step 1: Write API health test**

Test `GET /health` returns `{"status": "ok"}`.

- [ ] **Step 2: Run API test**

Run: `python -m pytest backend/tests/test_api_health.py -v`
Expected: fail until API route is wired.

- [ ] **Step 3: Add FastAPI app and health route**

Wire router in `backend/app/main.py`.

- [ ] **Step 4: Run API test again**

Run: `python -m pytest backend/tests/test_api_health.py -v`
Expected: pass.

### Task 3: Frontend Shells

**Files:**
- Create: `merchant-admin/package.json`
- Create: `merchant-admin/src/App.vue`
- Create: `merchant-admin/src/main.ts`
- Create: `merchant-admin/src/styles.css`
- Create: `customer-miniapp/package.json`
- Create: `customer-miniapp/src/App.vue`
- Create: `customer-miniapp/src/main.js`

- [ ] **Step 1: Create runnable Vue admin shell**

Build dashboard shell with sidebar modules from the prototype.

- [ ] **Step 2: Create uni-app customer shell**

Build customer home shell with store card, current number card, progress and quick actions.

- [ ] **Step 3: Install dependencies and build**

Run admin and customer build commands when dependencies are available.

