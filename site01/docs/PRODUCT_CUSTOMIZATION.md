# Product Customization & Variants System

## Overview
Il sistema supporta già le varianti di prodotto attraverso il modello `ProductVariant`. Questa guida spiega come utilizzare e estendere questa funzionalità.

## Database Structure

### ProductVariant Model
- **attributes** (JSON): Attributi flessibili (colore, lunghezza, materiale, etc.)
- **price_modifier** (Float): Differenza di prezzo rispetto al prodotto base (può essere negativo)
- **sku** (String): Codice SKU opzionale per tracking inventario
- **stock_quantity** (Integer): Quantità disponibile
- **in_stock** (Boolean): Disponibilità

## Use Cases Implementabili

### 1. Opzioni per Moduli di Comunicazione
**Esempio**: Modulo Bluetooth con varie opzioni
- Base: Modulo standard (€50)
- +Antenna esterna: +€15
- +Custodia protettiva: +€10
- +Cavo USB lungo: +€5

```python
# Variante 1: Solo modulo
{
    "attributes": {"configuration": "standard"},
    "price_modifier": 0.0
}

# Variante 2: Con antenna esterna
{
    "attributes": {"configuration": "standard", "antenna": "external"},
    "price_modifier": 15.0
}

# Variante 3: Pacchetto completo
{
    "attributes": {"configuration": "complete", "antenna": "external", "case": "protective", "cable": "long"},
    "price_modifier": 25.0  # Sconto pacchetto invece di 30
}
```

### 2. Cavo Venduto al Metro
**Esempio**: Cavo per sensori

```python
# Varianti per diverse lunghezze
{
    "attributes": {"length_meters": "1"},
    "price_modifier": 0.0  # Prezzo base per 1m
}

{
    "attributes": {"length_meters": "5"},
    "price_modifier": 15.0  # €3/metro extra
}

{
    "attributes": {"length_meters": "10"},
    "price_modifier": 25.0  # €2.50/metro extra (sconto quantità)
}
```

### 3. Pacchetti All-Inclusive
**Esempio**: Kit completo per tiro con l'arco

```python
# Pacchetto base
product = {
    "name": "Kit Principiante Arco",
    "price": 150.0
}

# Varianti come upgrade
{
    "attributes": {"package": "standard"},
    "price_modifier": 0.0
}

{
    "attributes": {"package": "intermediate", "includes": ["better_arrows", "finger_tab", "armguard"]},
    "price_modifier": 50.0
}

{
    "attributes": {"package": "complete", "includes": ["premium_arrows", "finger_tab", "armguard", "quiver", "case"]},
    "price_modifier": 120.0
}
```

### 4. Personalizzazione Corde
**Esempio**: Corda custom con opzioni

```python
{
    "attributes": {
        "length": "68",
        "strands": "16",
        "color_main": "black",
        "color_serving": "red",
        "serving_type": "premium",
        "custom_text": "yes"
    },
    "price_modifier": 5.0  # Serving premium +3, text +2
}
```

## Implementation Steps

### Phase 1: Admin Interface per Varianti
Creare interfaccia in admin panel per:
1. Aggiungere/modificare varianti per ogni prodotto
2. Definire attributi e modificatori di prezzo
3. Gestire stock per variante

### Phase 2: Frontend Product Display
Modificare `product_detail.html` per:
1. Mostrare opzioni disponibili come dropdown/radio buttons
2. Calcolare prezzo dinamicamente in base a selezioni
3. Aggiungere al carrello con variante specifica

### Phase 3: Cart & Checkout
Estendere carrello per:
1. Memorizzare variante selezionata
2. Visualizzare attributi nel carrello
3. Passare informazioni variante al sistema ordini

## Example UI Flow

### Product Page con Varianti
```html
<div class="product-options">
    <h3>Configurazione</h3>
    
    <!-- Base Product -->
    <div class="base-price">
        Prezzo base: €50.00
    </div>
    
    <!-- Options -->
    <div class="option-group">
        <label>Antenna</label>
        <select name="antenna" data-price-modifier="0">
            <option value="internal" data-price="0">Interna (inclusa)</option>
            <option value="external" data-price="15">Esterna (+€15.00)</option>
        </select>
    </div>
    
    <div class="option-group">
        <label>Custodia</label>
        <input type="checkbox" name="case" data-price="10">
        Custodia protettiva (+€10.00)
    </div>
    
    <!-- Total -->
    <div class="total-price">
        <strong>Totale:</strong> <span id="calculated-price">€50.00</span>
    </div>
</div>
```

### JavaScript per Calcolo Prezzo
```javascript
function calculatePrice() {
    let basePrice = parseFloat(product.price);
    let totalModifier = 0;
    
    // Sum all selected modifiers
    document.querySelectorAll('[data-price-modifier]').forEach(el => {
        if (el.type === 'checkbox') {
            if (el.checked) totalModifier += parseFloat(el.dataset.price || 0);
        } else {
            const selected = el.options[el.selectedIndex];
            totalModifier += parseFloat(selected.dataset.price || 0);
        }
    });
    
    document.getElementById('calculated-price').textContent = 
        `€${(basePrice + totalModifier).toFixed(2)}`;
}
```

## Database Queries Examples

### Get Product with Variants
```python
product = Product.query.get(product_id)
variants = ProductVariant.query.filter_by(product_id=product_id).all()

for variant in variants:
    attrs = json.loads(variant.attributes)
    print(f"Variant: {attrs}, Price: {product.price + variant.price_modifier}")
```

### Create New Variant
```python
variant = ProductVariant(
    product_id=product_id,
    attributes=json.dumps({
        "length": "10",
        "color": "black"
    }),
    price_modifier=25.0,
    sku="CABLE-10M-BLK",
    stock_quantity=50
)
db.session.add(variant)
db.session.commit()
```

## Next Steps

1. **Admin UI**: Creare interfaccia per gestione varianti
2. **Product Display**: Implementare selezione varianti su product_detail.html
3. **Cart Integration**: Estendere cart.js per gestire varianti
4. **Testing**: Testare con prodotti reali (moduli, cavi, kit)

## Notes

- Il sistema è già pronto a livello di database
- Serve solo implementare l'interfaccia utente
- Molto flessibile grazie al JSON per attributi
- Supporta sconti su pacchetti (price_modifier negativo)
