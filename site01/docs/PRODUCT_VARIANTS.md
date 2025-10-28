# Product Variants System

## Overview
The product variants system allows you to offer simple product options (like length, color, material) without requiring the full customizer interface.

## Use Cases

### 1. **Pre-Made Strings** (Non-Custom)
- Users can select length: 66", 68", 70", 72"
- Fixed price with optional length-based modifiers
- No full customization needed

### 2. **3D Prints**
- Material choice: PLA, PETG, ABS
- Color choice: Black, White, Red, Blue, etc.
- Price adjustments based on material

### 3. **Electronics**
- Size options
- Color variants
- Accessory bundles

## Database Structure

### Products Table
Added column:
- `variant_config` (TEXT/JSON): Configuration for variant options

### Product_Variants Table
New table:
- `id`: Primary key
- `product_id`: Foreign key to products
- `attributes`: JSON object of variant values (e.g., `{"length": "68", "color": "black"}`)
- `price_modifier`: Price difference from base (can be negative)
- `sku`: Optional SKU for inventory
- `stock_quantity`: Available quantity for this variant
- `in_stock`: Availability flag

## Variant Configuration Format

The `variant_config` field stores a JSON object defining available options:

```json
{
  "length": {
    "type": "select",
    "label_en": "String Length",
    "label_it": "Lunghezza Corda",
    "options": ["66", "68", "70", "72"],
    "unit": "inches",
    "required": true
  },
  "material": {
    "type": "select",
    "label_en": "Material",
    "label_it": "Materiale",
    "options": ["PLA", "PETG", "ABS"],
    "required": true
  },
  "color": {
    "type": "color",
    "label_en": "Color",
    "label_it": "Colore",
    "options": {
      "black": "#000000",
      "white": "#FFFFFF",
      "red": "#FF0000",
      "blue": "#0000FF"
    },
    "required": true
  }
}
```

### Field Types

#### `select`
Standard dropdown selection
```json
{
  "type": "select",
  "label_en": "Size",
  "label_it": "Taglia",
  "options": ["Small", "Medium", "Large"]
}
```

#### `color`
Color picker with predefined options
```json
{
  "type": "color",
  "label_en": "Color",
  "options": {
    "black": "#000000",
    "white": "#FFFFFF"
  }
}
```

#### `number`
Numeric input with min/max
```json
{
  "type": "number",
  "label_en": "Quantity",
  "min": 1,
  "max": 10,
  "step": 1
}
```

## Setting Up Variants

### Example 1: B55 String (Pre-Made)

**Product Setup:**
- Name: "B55 Recurve String"
- Base Price: €10.00
- Category: archery
- `is_custom_string`: false
- `variant_config`:
```json
{
  "length": {
    "type": "select",
    "label_en": "String Length",
    "label_it": "Lunghezza",
    "options": ["66", "68", "70", "72"],
    "unit": "inches",
    "required": true
  }
}
```

**Variants (optional price modifiers):**
- 66" → price_modifier: 0.00
- 68" → price_modifier: 0.00
- 70" → price_modifier: 0.50 (longer = slightly more expensive)
- 72" → price_modifier: 0.50

### Example 2: 3D Print

**Product Setup:**
- Name: "Custom Archery Sight"
- Base Price: €15.00
- Category: 3dprinting
- `variant_config`:
```json
{
  "material": {
    "type": "select",
    "label_en": "Material",
    "label_it": "Materiale",
    "options": ["PLA", "PETG", "ABS"],
    "required": true
  },
  "color": {
    "type": "color",
    "label_en": "Color",
    "label_it": "Colore",
    "options": {
      "black": "#000000",
      "white": "#FFFFFF",
      "red": "#FF0000",
      "blue": "#0000FF",
      "green": "#00FF00"
    },
    "required": true
  }
}
```

**Variants:**
- PLA + Black → price_modifier: 0.00
- PLA + White → price_modifier: 0.00
- PETG + Black → price_modifier: 3.00 (PETG more expensive)
- PETG + White → price_modifier: 3.00
- ABS + any color → price_modifier: 5.00

## Frontend Implementation

### Product Detail Page
When a product has `variant_config`:
1. Parse the JSON configuration
2. Display variant selectors (dropdowns, color swatches, etc.)
3. Calculate final price based on selected variant
4. Update "Add to Cart" to include variant selection
5. Validate that required variants are selected

### Cart System
Cart items with variants store:
```json
{
  "productId": 123,
  "variantId": 456,  // Optional if pre-defined variant exists
  "variantSelection": {
    "length": "68",
    "color": "black"
  },
  "price": 10.50
}
```

## Comparison: Variants vs Full Customization

| Feature | Variants | Full Customization |
|---------|----------|-------------------|
| **Use Case** | Pre-made products with options | Fully custom builds |
| **Complexity** | Simple (select from options) | Complex (many steps) |
| **Example** | "B55 String - choose length" | "Custom 8125 String - choose everything" |
| **UI** | Dropdowns on product page | Dedicated customizer page |
| **Pricing** | Base + modifier | Complex calculation |
| **Inventory** | Can track per variant | N/A (made to order) |

## Migration Steps

1. **Run migration:**
   ```bash
   sqlite3 instance/mysite.db < migrations/add_product_variants.sql
   ```

2. **Update existing products:**
   - For B55 strings: Add variant_config for length selection
   - For pre-made products: Add appropriate variant options
   - Custom strings keep `is_custom_string=true` and NO variants

3. **Update frontend:**
   - Product detail page: Show variant selectors
   - Cart: Handle variant selections
   - Admin panel: Variant management UI

## Admin Panel TODO

Create interface for:
- Configuring variant_config (JSON editor or form builder)
- Managing variants (add/edit/delete specific variant combinations)
- Setting price modifiers per variant
- Tracking stock per variant
- Bulk variant creation (e.g., "create all length combinations")

## API Endpoints (Future)

```python
# Get product with variants
GET /api/products/{id}/variants

# Create variant
POST /api/products/{id}/variants
{
  "attributes": {"length": "68"},
  "price_modifier": 0.50,
  "stock_quantity": 10
}

# Update variant
PATCH /api/variants/{id}

# Delete variant
DELETE /api/variants/{id}
```

## Notes

- Variants are **optional** - products without `variant_config` work as before
- Custom products (is_custom_string/is_custom_print) should NOT use variants
- You can mix: Some products with variants, some with full customization, some with neither
- Variant stock tracking is optional (can be null if made to order)
