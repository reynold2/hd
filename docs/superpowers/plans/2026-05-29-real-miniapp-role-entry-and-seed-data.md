# Real Miniapp Role Entry And Seed Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the miniapp role entry use real seeded accounts and real APIs, clean the customer entry UI, seed complete store data, verify admin/backend builds, and deploy.

**Architecture:** Add backend role resolution and WeChat login endpoints backed by real SQLAlchemy data. Keep the miniapp simulator entry as a thin account chooser that calls those real endpoints, stores the returned profile, and navigates to role pages. Add an idempotent Python seed command that writes the complete default store dataset into the configured database.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Vue 3, uni-app, Vite, Node test runner, pytest, existing deploy shell script.

---

### Task 1: Backend Role Login Contract

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/migrations/versions/20260528_0001_initial_schema.py`
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_auth_api.py`

- [ ] **Step 1: Write failing API tests**

Add tests that call `GET /api/roles/resolve?openid=openid_customer_001&store_id=1` and `POST /api/auth/wechat-login` after seeding catalog data. Assert the response includes `openid`, `role`, `store_id`, `store.name`, and `entry_page`.

- [ ] **Step 2: Run tests and verify failure**

Run: `& .\.venv\Scripts\python.exe -m pytest backend\tests\test_auth_api.py -v`

Expected: tests fail because the role endpoints do not exist.

- [ ] **Step 3: Add persisted role bindings and endpoints**

Add `RoleBindingModel` with `user_id`, `display_name`, `role`, `store_id`, `openid`, and `enabled`. Add Pydantic request/response models and two routes:

- `GET /api/roles/resolve`
- `POST /api/auth/wechat-login`

Both routes must use real database records and return an `entry_page` map for `customer`, `boss`, `staff`, `kitchen`, and `cashier`.

- [ ] **Step 4: Run tests and verify pass**

Run: `& .\.venv\Scripts\python.exe -m pytest backend\tests\test_auth_api.py -v`

Expected: all auth API tests pass.

### Task 2: Real Seed Command

**Files:**
- Create: `backend/app/seed_data.py`
- Modify: `backend/scripts/seed.mjs` only if keeping JSON seed compatibility is necessary.
- Test: `backend/tests/test_seed_data.py`

- [ ] **Step 1: Write failing seed tests**

Create a pytest that uses a temporary SQLite database, runs `seed_demo_data(session)`, runs it again, and asserts stable counts and real records for store, dishes, staff, role bindings, meal sessions, service calls, and operation logs.

- [ ] **Step 2: Run tests and verify failure**

Run: `& .\.venv\Scripts\python.exe -m pytest backend\tests\test_seed_data.py -v`

Expected: test fails because `backend/app/seed_data.py` does not exist.

- [ ] **Step 3: Implement idempotent seed data**

Create `seed_demo_data(db)` and CLI `python -m app.seed_data`. Upsert stable data for store `1`, the five miniapp OpenIDs, backend/admin staff, dishes, active queue numbers, service call, and operation logs.

- [ ] **Step 4: Run seed tests and backend tests**

Run: `& .\.venv\Scripts\python.exe -m pytest backend\tests\test_seed_data.py backend\tests\test_auth_api.py -v`

Expected: tests pass.

### Task 3: Miniapp Role Entry And Customer Cleanup

**Files:**
- Modify: `customer-miniapp/src/api.mjs`
- Modify: `customer-miniapp/src/role-auth.mjs`
- Modify: `customer-miniapp/src/pages/test-home/index.vue`
- Replace: `customer-miniapp/src/pages/index/index.vue`
- Test: `customer-miniapp/src/api.test.mjs`
- Test: `customer-miniapp/src/role-auth.test.mjs`

- [ ] **Step 1: Write failing frontend unit tests**

Add tests for role entry URL construction and API calls. Assert customer entry receives `store_id=1&number=A018`, and staff roles receive `store_id=1`.

- [ ] **Step 2: Run tests and verify failure**

Run: `npm.cmd run test:unit`

Expected: tests fail because the helper behavior is missing.

- [ ] **Step 3: Implement real role entry helpers and UI**

Use real `resolveRoleByOpenid` and `wechatLogin` calls from the test-home page. Save the returned profile, then navigate to the role page with the default store and number parameters. Replace the customer index page with a compact real binding page.

- [ ] **Step 4: Run frontend tests**

Run: `npm.cmd run test:unit`

Expected: all miniapp unit tests pass.

### Task 4: Build, Deploy, And Production Seed

**Files:**
- Modify: `deploy/hd/deploy.sh`

- [ ] **Step 1: Add production seed to deploy script**

After migrations and before backend restart, run `python -m app.seed_data` in the deployment environment so the configured production database receives the real demo dataset.

- [ ] **Step 2: Run local verification**

Run:

- `& .\.venv\Scripts\python.exe -m pytest backend\tests -v`
- `npm.cmd run build` in `merchant-admin`
- `npm.cmd run build:mp-weixin` in `customer-miniapp`

Expected: tests and builds exit with code 0.

- [ ] **Step 3: Commit, push, and deploy**

Commit the implementation, push `main`, and run the existing remote deploy command for `hd.yxck3d.tech`.

- [ ] **Step 4: Verify production**

Check:

- `https://hd.yxck3d.tech/health`
- `https://hd.yxck3d.tech/api/stores/1/catalog`
- `https://hd.yxck3d.tech/api/roles/resolve?openid=openid_customer_001&store_id=1`
- admin URL headers at `https://hd.yxck3d.tech/admin/`

Expected: health, catalog, role resolution, and admin asset responses succeed.
