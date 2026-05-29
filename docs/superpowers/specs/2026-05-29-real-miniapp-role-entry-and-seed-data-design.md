# Real Miniapp Role Entry And Seed Data Design

## Goal

Clean up the customer miniapp entry experience and make the remaining role entry page use real backend data. The miniapp test home is only a simulator for choosing which seeded WeChat test account is scanning the default store QR code. After entry, all pages use real backend APIs and real database records.

## Scope

- Keep `customer-miniapp/src/pages/test-home/index.vue` as the simulator entry page.
- Remove unused flow verification, event simulator, scenario expansion, and status log UI from the customer entry page.
- Seed a complete default store dataset in the real backend database.
- Check the merchant admin build and real backend endpoints after the data changes.
- Deploy the backend/admin/customer builds to the existing `hd.yxck3d.tech` deployment target.

## Miniapp Role Entry

The first miniapp page remains `pages/test-home/index`. It displays role entry buttons for seeded accounts:

- Customer: `openid_customer_001`
- Boss: `openid_boss_001`
- Staff: `openid_staff_001`
- Kitchen: `openid_kitchen_001`
- Cashier: `openid_cashier_001`

Clicking an entry calls the real backend role/login flow for that OpenID and default store `store_id=1`. The returned profile is stored through the existing role profile storage helper, then the app navigates to the matched real page:

- Customer goes to `/pages/detail/detail?store_id=1&number=A018`.
- Boss goes to `/pages/boss/index?store_id=1`.
- Staff goes to `/pages/staff/index?store_id=1`.
- Kitchen goes to `/pages/kitchen/index?store_id=1`.
- Cashier goes to `/pages/cashier/index?store_id=1`.

No fake API, local-only data branch, or special test endpoint is introduced for the miniapp flow.

## Customer Entry Cleanup

`pages/index/index.vue` becomes a normal customer landing and binding page. It keeps real store catalog loading, number input, and navigation into number detail. It removes the previous internal verification UI:

- flow step timeline
- event simulator
- scenario expansion cards
- manual state machine
- fake order status logs
- validation-only payment QR state

## Seed Data

The backend gets an idempotent seed command for the real SQL database. It creates or updates:

- Store `1`, `川香麻辣烫（中山店）`, open for business.
- Staff for boss, manager, cashier, cook, and service roles.
- WeChat test role bindings by OpenID for customer, boss, staff, kitchen, and cashier.
- Dishes across recommended, meat, vegetable, staple, and drink categories.
- Meal sessions covering active operational states: occupied, preparing, called, dining, checkout requested, paid, skipped, and cancelled.
- At least one pending service call and several operation logs so admin screens have visible real data.

The seed is safe to run multiple times. It updates known demo records by stable store, number, and OpenID identifiers instead of blindly duplicating data.

## Admin And Deployment

Before deployment:

- Backend tests are run.
- Customer miniapp builds for WeChat.
- Merchant admin builds for production.
- Real API checks confirm the default store catalog, queue, cashier pending list, and role resolution/login data load.

Deployment uses the existing `deploy/hd/deploy.sh` target and writes the seeded dataset into the production database configured by the deployment environment.

## Non-Goals

- Do not add a fake miniapp test API.
- Do not make a separate backend testing interface.
- Do not replace real admin pages with mock data.
- Do not remove the simulator entry page; it remains the convenient way to choose seeded accounts during miniapp testing.
