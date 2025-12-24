# Modello Dati Inferito - Tilby - Sala.mp4

## Tavolo
Un elemento dell'interfaccia che rappresenta un tavolo fisico.

### Campi
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| forma | enum | Forma del tavolo |
| numero_posti | number | Numero massimo di persone |
| nome | string | Etichetta del tavolo |
| comanda_tipo | enum | Tipo di comanda (singola o multipla) |

## Sala
Rappresenta una stanza nel ristorante dove sono posizionati i tavoli.

### Campi
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| layout | relation | Configurazione della disposizione dei tavoli |
