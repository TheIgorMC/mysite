# Gestione Posti Ranking

## Descrizione
Il file `ranking_positions.csv` definisce il numero di posti disponibili per ogni ranking, classe e divisione.
Questo file viene caricato manualmente e aggiornato circa 4 volte all'anno.

## Formato CSV

```csv
qualifica,classe_gara,categoria,posti_disponibili
RegionaleIndoor2026Veneto,Senior Maschile,Arco Olimpico,24
RegionaleIndoor2026Veneto,Senior Maschile,Arco Compound,24
...
```

## Campi

- **qualifica**: Codice della qualifica (es. `RegionaleIndoor2026Veneto`, `NazionaleIndoor2026`)
- **classe_gara**: Nome della classe (es. `Senior Maschile`, `Master Femminile`)
- **categoria**: Nome della divisione (es. `Arco Olimpico`, `Arco Compound`, `Arco Nudo`)
- **posti_disponibili**: Numero intero di posti disponibili per il ranking

## Come Aggiornare

### Metodo 1: Upload tramite SCP/SFTP
1. Modifica il file `ranking_positions.csv` localmente
2. Carica il file sul server nella directory: `site01/app/data/ranking_positions.csv`
3. Ricarica i dati tramite API (richiede admin):
   ```bash
   POST /archery/api/ranking/positions/reload
   ```

### Metodo 2: Modifica Diretta sul Server
1. Accedi al server via SSH
2. Modifica il file:
   ```bash
   nano /path/to/site01/app/data/ranking_positions.csv
   ```
3. Salva e ricarica tramite API

## Utilizzo nell'Applicazione

Quando un utente visualizza un ranking, il sistema:
1. Recupera i dati del ranking dall'API Orion
2. Cerca nel CSV il numero di posti per quella specifica combinazione (qualifica, classe, categoria)
3. Mostra la posizione come "X/Y" dove:
   - **X** = posizione attuale dell'atleta
   - **Y** = numero totale di posti disponibili

### Esempio
Se un atleta è 5° in un ranking che ha 24 posti, verrà mostrato: **5/24**

## Squadre

I ranking squadra sono identificati dal suffisso **"SQ"** nel codice qualifica.

### Esempi:
- Individuale: `RegionaleIndoor2026Veneto`
- Squadra: `RegionaleIndoor2026VenetoSQ`

### Interfaccia Utente
Se esistono entrambe le varianti (individuale e squadra) per lo stesso campionato, l'interfaccia mostra un selector "Tipo" con le opzioni:
- **Individuale**
- **Squadra**

Il selector filtra automaticamente le qualifiche disponibili in base alla selezione.

## Note Tecniche

- Il CSV viene caricato all'avvio dell'applicazione
- La classe `RankingPositions` in `app/ranking_positions.py` gestisce il parsing
- I dati sono cachati in memoria per performance
- La funzione `reload()` permette di ricaricare senza restart dell'app
- Se una combinazione non è presente nel CSV, la posizione viene mostrata senza il denominatore (es. "5" invece di "5/24")
