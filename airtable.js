/**
 * Append one record to Airtable (passed applicants from OpenAI flow).
 * Requires: AIRTABLE_API_KEY, AIRTABLE_BASE_ID in .env
 * Optional: AIRTABLE_TABLE_NAME (default "Chatters")
 *
 * Fields: Name, Email, Phone, Telegram Username, Telegram User ID, Application notes, Status
 */

const https = require('https');

function request(path, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const req = https.request(
      {
        hostname: 'api.airtable.com',
        path: path.startsWith('/') ? path : `/${path}`,
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.AIRTABLE_API_KEY}`,
          'Content-Type': 'application/json',
        },
      },
      (res) => {
        let raw = '';
        res.on('data', (chunk) => { raw += chunk; });
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(raw ? JSON.parse(raw) : {});
          } else {
            reject(new Error(`Airtable ${res.statusCode}: ${raw}`));
          }
        });
      }
    );
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function appendApplicant(row) {
  const baseId = process.env.AIRTABLE_BASE_ID;
  const apiKey = process.env.AIRTABLE_API_KEY;
  const tableName = process.env.AIRTABLE_TABLE_NAME || 'Chatters';

  if (!apiKey || !baseId) {
    throw new Error('Missing Airtable config. Set AIRTABLE_API_KEY and AIRTABLE_BASE_ID in .env');
  }

  const tableEncoded = encodeURIComponent(tableName);
  const path = `/v0/${baseId}/${tableEncoded}`;

  const fields = {
    Name: row.fullName || '',
    Email: row.email || '',
    Phone: row.phone || '',
    'Telegram Username': row.telegramUsername || '',
    'Telegram User ID': row.telegramUserId || '',
    'Application notes': row.applicationNotes || '',
    Status: 'Passed',
  };

  await request(path, { fields });
}

module.exports = { appendApplicant };
