const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

/**
 * Evaluate an applicant's text using GPT-4o-mini.
 * @param {string} text - Applicant's response(s) to evaluate
 * @returns {Promise<{ score: number, decision: string, feedback: string }>}
 */
async function evaluateApplicant(text) {
  const prompt = `
You are hiring OnlyFans chatters.

Evaluate this applicant.

Score these categories:
- English
- Sales ability
- Creativity
- Professionalism

Return JSON only, no markdown or extra text:

{
  "score": number,
  "decision": "PASS" or "REJECT",
  "feedback": "short explanation"
}

Application:
${text}
`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.3,
  });

  const content = response.choices[0]?.message?.content?.trim() || '{}';
  // Remove possible markdown code fences
  const jsonStr = content.replace(/^```(?:json)?\s*|\s*```$/g, '').trim();
  return JSON.parse(jsonStr);
}

module.exports = evaluateApplicant;
