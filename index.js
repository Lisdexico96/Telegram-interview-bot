require('dotenv').config();
const { Telegraf } = require('telegraf');
const evaluateApplicant = require('./evaluateApplicant');
const { appendApplicant } = require('./sheets');

const BOT_TOKEN = process.env.BOT_TOKEN;
const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID;

if (!BOT_TOKEN) {
  console.error('Missing BOT_TOKEN in .env');
  process.exit(1);
}

const bot = new Telegraf(BOT_TOKEN);

// User state: userId -> { phase: 'collecting', step: string, ...fields }
const userState = new Map();

const COLLECT_STEPS = [
  { key: 'name', question: "What is your full name?", fieldName: "Full Name" },
  { key: 'email', question: "What is your email address?", fieldName: "Email" },
  { key: 'phone', question: "What is your phone number?", fieldName: "Phone" },
];

function getNextStep(stepKey) {
  const i = COLLECT_STEPS.findIndex(s => s.key === stepKey);
  return i >= 0 && i < COLLECT_STEPS.length - 1 ? COLLECT_STEPS[i + 1] : null;
}

function getFirstStep() {
  return COLLECT_STEPS[0];
}

bot.start((ctx) => {
  userState.delete(ctx.from.id);
  return ctx.reply(
    'Hello! 👋\n\n' +
    'Please tell us your first name to get started.'
  );
});

bot.on('text', async (ctx) => {
  const userId = ctx.from.id;
  const text = ctx.message.text;
  const username = ctx.from.username ? `@${ctx.from.username}` : '';
  const state = userState.get(userId);

  // If user is in "collecting info" flow (after PASS), collect next field or save to Google Sheet
  if (state && state.phase === 'collecting') {
    const step = COLLECT_STEPS.find(s => s.key === state.step);
    if (!step) {
      userState.delete(userId);
      return ctx.reply('Something went wrong. Please send /start to begin again.');
    }

    state[step.key] = text.trim();
    const next = getNextStep(step.key);
    if (next) {
      state.step = next.key;
      userState.set(userId, state);
      return ctx.reply(next.question);
    }

    // All steps done – save to Google Sheet
    userState.delete(userId);
    if (!process.env.GOOGLE_SHEET_ID || !process.env.GOOGLE_SERVICE_ACCOUNT_JSON) {
      return ctx.reply(
        'Thank you! We have received your details.\n\n' +
        '(Google Sheet is not connected. Add GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON to .env to save applicants.)'
      );
    }
    try {
      await appendApplicant({
        fullName: state.name,
        email: state.email,
        phone: state.phone,
        telegramUsername: username,
        telegramUserId: String(userId),
        applicationNotes: state.evaluationText || '',
      });
      return ctx.reply(
        '✅ Thank you! Your information has been saved. We will be in touch soon.'
      );
    } catch (err) {
      console.error('Google Sheet append error:', err);
      return ctx.reply(
        'We received your details but could not save them to our system. Please try again later or contact support.'
      );
    }
  }

  // Normal flow: AI evaluation
  if (!process.env.OPENAI_API_KEY) {
    return ctx.reply('Evaluation is not configured. Add OPENAI_API_KEY in .env to enable AI review.');
  }

  try {
    const result = await evaluateApplicant(text);
    const msg =
      `📋 Application review\n\n` +
      `Score: ${result.score}\n` +
      `Decision: ${result.decision}\n\n` +
      `Feedback: ${result.feedback}`;
    await ctx.reply(msg);

    if (result.decision === 'PASS') {
      const first = getFirstStep();
      userState.set(userId, {
        phase: 'collecting',
        step: first.key,
        evaluationText: text,
      });
      await ctx.reply(
        '🎉 You passed! To move forward, we need a few details for our records.\n\n' + first.question
      );
    }
  } catch (err) {
    console.error('evaluateApplicant error:', err);
    await ctx.reply('Evaluation failed. Please try again.');
  }
});

bot.launch().then(() => {
  console.log('Bot is running (Telegraf)...');
}).catch((err) => {
  console.error('Bot failed to start:', err);
  process.exit(1);
});

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
