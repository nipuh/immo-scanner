# CLAUDE.md

## Workflow-Regeln

### Branching & Deployment

- Nie direkt auf main pushen. Main ist der Production-Branch und wird automatisch von Vercel deployed.
- Für jedes Feature oder jeden Fix einen neuen Branch erstellen: `feature/kurze-beschreibung` oder `fix/kurze-beschreibung`.
- Alle Änderungen auf dem Feature-Branch committen, dann einen PR nach main erstellen.
- PRs über GitHub CLI (`gh pr create`) erstellen.

### Commits

- Commit-Messages auf Deutsch oder Englisch, klar und beschreibend.
- Kleine, logische Commits — nicht alles in einen einzigen Commit packen.
- Vor dem Commit sicherstellen, dass der Code läuft und keine offensichtlichen Fehler hat.

### Code-Qualität

- Code muss lauffähig sein, bevor ein PR erstellt wird.
- Keine hardgecodeten API-Keys oder Secrets im Code — immer Environment Variables nutzen.
- Bestehende Projektstruktur und Patterns beibehalten.

### Kommunikation

- Bei Unklarheiten nachfragen, bevor du loslegst.
- Nach Abschluss eines Features eine kurze Zusammenfassung geben: was wurde gemacht, was wurde geändert, was muss der User wissen.
