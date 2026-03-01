# Immo-Scanner Freiburg

Automatische Immobilien-Suche fuer Freiburg + 30km Umgebung mit Immocation Bierdeckelrechnung.

## Was es macht

- Scrapt taeglich ImmobilienScout24, Immowelt, Kleinanzeigen (kein API-Key noetig)
- - Filtert nach deinen Kriterien: 1-4 Zimmer, max 110k/Zimmer, kein Erbbaurecht/Neubau/Versteigerung
  - - Berechnet Bierdeckelrechnung nach Immocation-Methode
    -   - Normalvermietung: mind. 5% Bruttomietrendite
        -   - WG-Vermietung: mind. 6% Bruttomietrendite
            - - Schreibt Ergebnisse ins Google Sheet (farbcodiert)
              - - Sendet Twilio SMS um 16:00 Uhr mit Top-5 Objekten
               
                - ## Bierdeckelrechnung
               
                - ```
                  Bruttomietrendite = (Jahreskaltmiete / Kaufpreis) * 100

                  Normalvermietung (12 EUR/m²):  mind. 5%  -> Kaufpreisfaktor max 20x
                  WG-Vermietung (420 EUR/Zimmer): mind. 6%  -> Kaufpreisfaktor max 16.7x

                  Kaufnebenkosten BW ohne Makler: ~7%
                  Kaufnebenkosten BW mit Makler:  ~10.57%
                  ```

                  ## Setup

                  ### 1. Google Apps Script einrichten

                  1. Oeffne dein Google Sheet
                  2. 2. Erweiterungen -> Apps Script
                     3. 3. Inhalt von `apps_script.js` einfuegen
                        4. 4. Ausfuehren -> `testDoPost` (Sheet wird erstellt + Testdaten eingefuegt)
                           5. 5. Bereitstellen -> Neue Bereitstellung
                              6.    - Typ: Web-App
                                    -    - Ausfuehren als: Ich
                                         -    - Zugriff: Jeder
                                              - 6. URL kopieren
                                               
                                                7. ### 2. GitHub Secrets einrichten
                                               
                                                8. Unter: Settings -> Secrets and variables -> Actions
                                               
                                                9. | Secret | Beschreibung |
                                                10. |--------|-------------|
                                                11. | `TWILIO_ACCOUNT_SID` | Twilio Account SID |
                                                12. | `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
                                                13. | `TWILIO_FROM_NUMBER` | Twilio Telefonnummer (z.B. +1234567890) |
                                                14. | `TWILIO_TO_NUMBER` | Deine Handynummer (z.B. +491711234567) |
                                                15. | `GOOGLE_SHEETS_WEBAPP_URL` | Apps Script Web-App URL aus Schritt 1 |
                                               
                                                16. ### 3. Erster Test
                                               
                                                17. GitHub Actions -> Workflow -> Run workflow
                                               
                                                18. ## Suchkriterien (config.yaml)
                                               
                                                19. - Standort: Freiburg im Breisgau + 30km Radius
                                                    - - Zimmer: 1-4
                                                      - - Max. Kaufpreis: 440.000 EUR (4 Zi. * 110k)
                                                        - - Max. Preis/Zimmer: 110.000 EUR
                                                          - - Ausgeschlossen: Erbbaurecht, Zwangsversteigerung, Neubau, Erstbezug
                                                           
                                                            - ## Zeitplan
                                                           
                                                            - GitHub Actions Cron: `30 14 * * *` = 14:30 UTC = 15:30 MEZ / 16:30 MESZ
                                                           
                                                            - ## Kosten
                                                           
                                                            - | Komponente | Kosten |
                                                            - |-----------|--------|
                                                            - | GitHub Actions | Kostenlos (2000 Min/Monat) |
                                                            - | Google Sheets | Kostenlos |
                                                            - | Twilio SMS | ~0.07 EUR/SMS |
                                                            - 
