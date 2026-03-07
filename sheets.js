const { google } = require('googleapis');

/**
 * Append one row to your Google Sheet (passed applicants).
 * Requires: GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON in .env
 * Optional: GOOGLE_SHEET_TAB_NAME (default "Sheet1")
 *
 * Row order: Full Name, Email, Phone, Telegram Username, Telegram User ID, Application / Notes
 */
async function appendApplicant(row) {
  const sheetId = process.env.GOOGLE_SHEET_ID;
  const credentialsJson = process.env.GOOGLE_SERVICE_ACCOUNT_JSON;
  const tabName = process.env.GOOGLE_SHEET_TAB_NAME || 'Sheet1';

  if (!sheetId || !credentialsJson) {
    throw new Error(
      'Missing Google Sheet config. Set GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON in .env'
    );
  }

  let credentials;
  try {
    credentials = typeof credentialsJson === 'string' ? JSON.parse(credentialsJson) : credentialsJson;
  } catch {
    throw new Error('GOOGLE_SERVICE_ACCOUNT_JSON must be valid JSON.');
  }

  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const sheets = google.sheets({ version: 'v4', auth });
  const range = `${tabName}!A:F`;

  await sheets.spreadsheets.values.append({
    spreadsheetId: sheetId,
    range,
    valueInputOption: 'USER_ENTERED',
    insertDataOption: 'INSERT_ROWS',
    requestBody: {
      values: [[
        row.fullName || '',
        row.email || '',
        row.phone || '',
        row.telegramUsername || '',
        row.telegramUserId || '',
        row.applicationNotes || '',
      ]],
    },
  });
}

module.exports = { appendApplicant };
