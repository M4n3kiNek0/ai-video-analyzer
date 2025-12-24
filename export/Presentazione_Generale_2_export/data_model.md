# Modello Dati Inferito - Presentazione Generale 2.mp4

## Ordine
Rappresenta un ordine cliente singolo.

### Campi
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| id | number | Identificativo univoco dell'ordine |
| data_ordine | date | Data e ora dell'ordine |
| totale | number | Importo totale dell'ordine |

## Pagamento
Dettagli su un metodo di pagamento utilizzato.

### Campi
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| metodo | enum | Metodo di pagamento usato |

## Cliente
Informazioni su un cliente del ristorante.

### Campi
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| nome | string | Nome del cliente |
