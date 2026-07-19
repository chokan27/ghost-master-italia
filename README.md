# Ghost Master Italia

Sito statico che raccoglie link promozionali Coin Master e accetta soltanto domini verificati.

## Aggiornamento automatico

Il workflow `.github/workflows/update-rewards.yml` esegue ogni ora `scripts/update_rewards.py`.
Lo script legge LOLVVV e LEVVVEL, estrae soltanto codici premio validi, elimina i duplicati e
conserva gli ultimi tre giorni in `outputs/rewards-data.js`. Se trova cambiamenti, GitHub crea
automaticamente un commit; Netlify collegato al repository pubblica quindi la nuova versione.

L'aggiornamento può essere avviato anche manualmente da GitHub: **Actions → Aggiorna premi
Coin Master → Run workflow**.
