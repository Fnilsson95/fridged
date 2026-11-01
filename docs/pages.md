# fridged: v1 website pages

The pages below use only what the v1 tables provide (see [data-model.md](data-model.md)). Anything that needs expiry, batches, shopping or price history comes later.

## Navigation

Mobile-first bottom tab bar with four tabs: **Home, Stock, Unknown, History**. The Unknown tab shows a badge with the number of unknown items. The Product page has no tab and is reached from list rows.

## Pages

### Home (`/`)
- This week and this month: **Spent, Used, Gap**, each with the change versus the previous period.
- A 12-week chart of Spent versus Used.
- Top 5 products (by money spent).
- An amber banner when unknown items exist: "N unknown items, excluded from totals", linking to Unknown.
- Empty state: "Scan something in IN mode".

### Stock (`/inventory`) - the known register
- Known products with stock > 0: name, brand, size, **units**, and estimated value (units x current price).
- Search by name or brand, and a toggle to show all known products including those with no stock.
- Unknown products that have stock appear with an amber "Unknown" badge linking to their form.
- Tapping a row opens the Product page.

### Unknown (`/unknown`) - the unknown register
- Every product with `status = 'unknown'`: barcode (large), first seen, number of scans, current stock.
- A form per item: **name, brand, price** (required), size and image URL (optional). Price accepts `12,50` or `12.50`.
- On save the item moves to the known register and the totals update.
- Empty state: "No unknown items".

### History (`/history`)
- Newest-first list of events: time, product (or barcode if unknown), type badge (IN / OUT / STOCKTAKE), price.
- Filter by type. Reverted events are greyed out with a strikethrough.
- An **Undo** button per row, with a confirm dialog first.

### Product (`/products/:id`)
- Stock, current price and the product's recent events.
- Edit name, brand, size, image URL and price. A price change affects future events only.
- Undo from the product's event list.

## API

| Endpoint | Used by |
|---|---|
| `GET /api/summary?period=week\|month` | Home totals and change |
| `GET /api/summary/weekly?weeks=12` | Home chart |
| `GET /api/products?status=&search=&in_stock=` | Stock and Unknown (returns `stock`, `value_ore`, scan count) |
| `GET /api/products/:id` | Product page |
| `PATCH /api/products/:id` | Handle an unknown item, edit fields, set the price |
| `GET /api/events?type=&product_id=&cursor=` | History and Product page |
| `POST /api/events/:id/revert` | Undo |
| `POST /api/scans` | The device only |

The frontend never calculates stock or money. It only formats öre as `12,50 kr`.

## UX rules

- Tap targets at least 44 px, and confirm before reverts.
- UI text in English. Calm utility look: dark teal accent, amber for items that need attention.
- Money stays in öre until display. Pages are thin and use one data hook per need.

## Build order

1. Home with mock data in the feature-based structure.
2. Stock, Unknown, History, Product.
3. Replace mock data with the real API once the backend M1 exists.

## Open questions

1. Manual +1 / -1 on the Product page, for fixing stock from the website (for example after handling an item that was only seen via OUT scans)? Proposed, not decided.
2. Top 5 ranked by money spent (proposed) or by number of scans?
3. Should the Stock page hide products with no stock by default (proposed)?
