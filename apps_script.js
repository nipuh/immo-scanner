/**
 * Immo-Scanner Google Apps Script
 * 
 * Setup:
 * 1. Dieses Script in Google Sheet einfuegen (Erweiterungen -> Apps Script)
 * 2. Bereitstellen -> Neue Bereitstellung -> Web-App
 *    - Ausfuehren als: Ich
 *    - Zugriff: Jeder
 * 3. URL kopieren und als GitHub Secret GOOGLE_SHEETS_WEBAPP_URL eintragen
 */

const SHEET_NAME = "Neue Objekte";

// Spalten-Header
const HEADERS = [
    "Datum",
    "Plattform", 
    "Titel",
    "Preis (EUR)",
    "Zimmer",
    "m²",
    "Adresse",
    "Rendite Normal",
    "OK Normal",
    "Rendite WG",
    "OK WG",
    "Kauf-Faktor",
    "Score",
    "Leerstand",
    "WG-geeignet",
    "Link"
  ];

/**
 * GET Handler - Test ob Script erreichbar
 */
function doGet(e) {
    return ContentService
      .createTextOutput(JSON.stringify({
              status: "ok",
              message: "Immo-Scanner Webapp laeuft",
              sheet: SHEET_NAME,
              timestamp: new Date().toISOString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
}

/**
 * POST Handler - Empfaengt Listings vom Python-Skript
 */
function doPost(e) {
    try {
          const payload = JSON.parse(e.postData.contents);
          const listings = payload.listings || [];

      if (listings.length === 0) {
              return ContentService
                .createTextOutput(JSON.stringify({status: "ok", added: 0}))
                .setMimeType(ContentService.MimeType.JSON);
      }

      const sheet = getOrCreateSheet();

      let added = 0;
          for (const listing of listings) {
                  appendListing(sheet, listing);
                  added++;
          }

      // Formatierung anwenden
      formatSheet(sheet);

      return ContentService
            .createTextOutput(JSON.stringify({
                      status: "ok", 
                      added: added,
                      timestamp: new Date().toISOString()
            }))
            .setMimeType(ContentService.MimeType.JSON);

    } catch (err) {
          return ContentService
            .createTextOutput(JSON.stringify({
                      status: "error",
                      message: err.toString()
            }))
            .setMimeType(ContentService.MimeType.JSON);
    }
}

/**
 * Sheet holen oder erstellen
 */
function getOrCreateSheet() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
        sheet = ss.insertSheet(SHEET_NAME);

      // Header-Zeile
      const headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
        headerRange.setValues([HEADERS]);
        headerRange.setBackground("#1a73e8");
        headerRange.setFontColor("#ffffff");
        headerRange.setFontWeight("bold");
        headerRange.setFontSize(10);

      // Spaltenbreiten
      sheet.setColumnWidth(1, 90);   // Datum
      sheet.setColumnWidth(2, 110);  // Plattform
      sheet.setColumnWidth(3, 280);  // Titel
      sheet.setColumnWidth(4, 100);  // Preis
      sheet.setColumnWidth(5, 60);   // Zimmer
      sheet.setColumnWidth(6, 55);   // m2
      sheet.setColumnWidth(7, 160);  // Adresse
      sheet.setColumnWidth(8, 100);  // Rendite Normal
      sheet.setColumnWidth(9, 80);   // OK Normal
      sheet.setColumnWidth(10, 100); // Rendite WG
      sheet.setColumnWidth(11, 70);  // OK WG
      sheet.setColumnWidth(12, 90);  // Kauf-Faktor
      sheet.setColumnWidth(13, 60);  // Score
      sheet.setColumnWidth(14, 80);  // Leerstand
      sheet.setColumnWidth(15, 90);  // WG-geeignet
      sheet.setColumnWidth(16, 200); // Link

      // Zeile einfrieren
      sheet.setFrozenRows(1);

      Logger.log("Sheet '" + SHEET_NAME + "' erstellt");
  }

  return sheet;
}

/**
 * Listing als Zeile einfuegen
 */
function appendListing(sheet, listing) {
    const row = [
          listing.datum || new Date().toISOString().split('T')[0],
          listing.platform || '',
          listing.titel || '',
          listing.preis || 0,
          listing.zimmer || '',
          listing.qm || '',
          listing.adresse || '',
          listing.rendite_normal || '',
          listing.ok_normal || '',
          listing.rendite_wg || '',
          listing.ok_wg || '',
          listing.kauf_faktor || '',
          listing.score || 0,
          listing.leerstand || '',
          listing.wg_geeignet || '',
          listing.url || ''
        ];

  sheet.appendRow(row);
}

/**
 * Farbliche Formatierung basierend auf Score + OK-Status
 */
function formatSheet(sheet) {
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return;

  // Nur letzte eingefuegte Zeilen formatieren (letzte 20 zur Sicherheit)
  const startRow = Math.max(2, lastRow - 19);

  for (let row = startRow; row <= lastRow; row++) {
        const scoreCell = sheet.getRange(row, 13); // Score-Spalte
      const score = scoreCell.getValue();

      let rowColor = "#ffffff";

      if (score >= 70) {
              rowColor = "#d4edda"; // Gruen - sehr gut
      } else if (score >= 50) {
              rowColor = "#fff3cd"; // Gelb - gut
      } else if (score >= 30) {
              rowColor = "#ffeeba"; // Orange - okay
      } else {
              rowColor = "#f8d7da"; // Rot - schlecht
      }

      sheet.getRange(row, 1, 1, HEADERS.length).setBackground(rowColor);

      // OK-Zellen einfaerben
      const okNormalCell = sheet.getRange(row, 9);  // OK Normal
      const okWgCell = sheet.getRange(row, 11);     // OK WG

      if (okNormalCell.getValue() === "OK") {
              okNormalCell.setBackground("#28a745").setFontColor("#ffffff").setFontWeight("bold");
      } else {
              okNormalCell.setBackground("#dc3545").setFontColor("#ffffff");
      }

      if (okWgCell.getValue() === "OK") {
              okWgCell.setBackground("#28a745").setFontColor("#ffffff").setFontWeight("bold");
      } else {
              okWgCell.setBackground("#dc3545").setFontColor("#ffffff");
      }

      // Link als Hyperlink
      const urlCell = sheet.getRange(row, 16);
        const url = urlCell.getValue();
        const titleCell = sheet.getRange(row, 3);
        const title = titleCell.getValue();

      if (url && url.startsWith('http')) {
              urlCell.setFormula('=HYPERLINK("' + url + '","Link oeffnen")');
              urlCell.setFontColor("#1a73e8");
      }
  }
}

/**
 * Test-Funktion: Direkt ausfuehren um Sheet zu erstellen
 */
function testDoPost() {
    const testData = {
          listings: [
            {
                      datum: new Date().toISOString().split('T')[0],
                      platform: "ImmobilienScout24",
                      titel: "TEST: 3-Zimmer-Wohnung Freiburg-Wiehre",
                      preis: 320000,
                      zimmer: 3,
                      qm: 78,
                      adresse: "79102 Freiburg, Wiehre",
                      rendite_normal: "5.4%",
                      ok_normal: "OK",
                      rendite_wg: "5.9%",
                      ok_wg: "NEIN",
                      kauf_faktor: 18.5,
                      score: 72,
                      leerstand: "Ja",
                      wg_geeignet: "Ja",
                      url: "https://www.immobilienscout24.de/expose/test"
            }
                ]
    };

  const mockEvent = {
        postData: {
                contents: JSON.stringify(testData)
        }
  };

  const result = doPost(mockEvent);
    Logger.log("Test-Ergebnis: " + result.getContent());

  SpreadsheetApp.getUi().alert(
        "Test erfolgreich!\n\n" +
        "Sheet '" + SHEET_NAME + "' wurde erstellt/aktualisiert.\n\n" +
        "Naechster Schritt:\n" +
        "Bereitstellen -> Neue Bereitstellung -> Web-App\n" +
        "(Ausfuehren als: Ich, Zugriff: Jeder)"
      );
}
