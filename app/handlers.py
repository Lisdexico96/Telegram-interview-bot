"""
Telegram bot handlers for interview process
"""

import time
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import clear_database, get_cursor, get_connection
from app.questions import get_random_questions, QUESTIONS_PER_INTERVIEW
from app.scoring import analyze_response, determine_decision
from app.utils import generate_feedback, notify_admin

logger = logging.getLogger(__name__)

PURGE_CONFIRM_CALLBACK = "admin_purge_confirm"
PURGE_CANCEL_CALLBACK = "admin_purge_cancel"


def _build_replies_text(cur, user_id: int) -> str:
    """Build 'Q: ... A: ...' text from responses table for this user."""
    cur.execute(
        "SELECT question_number, question_text, response_text FROM responses WHERE user_id = ? ORDER BY question_number",
        (user_id,),
    )
    rows = cur.fetchall()
    parts = []
    for qnum, qtext, rtext in rows:
        parts.append(f"Q{qnum + 1}: {qtext or ''}\nA{qnum + 1}: {rtext or ''}")
    return "\n\n".join(parts) if parts else ""


def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    try:
        import sys
        if 'bot' in sys.modules:
            bot_module = sys.modules['bot']
            admin_ids = getattr(bot_module, 'ADMIN_IDS', [])
        else:
            import bot
            admin_ids = getattr(bot, 'ADMIN_IDS', [])
        result = user_id in admin_ids
        logger.info(f"Admin check for user {user_id}: ADMIN_IDS={admin_ids}, is_admin={result}")
        return result
    except (ImportError, AttributeError, Exception) as e:
        logger.error(f"Failed to get ADMIN_IDS for user {user_id}: {e}, defaulting to False", exc_info=True)
        return False


def get_user_questions(cur, user_id: int) -> list[str]:
    """Get the selected questions for a user from the database."""
    cur.execute("SELECT selected_questions FROM candidates WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    if result and result[0]:
        try:
            return json.loads(result[0])
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse questions for user {user_id}")
            return None
    return None


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - initialize interview."""
    try:
        user = update.effective_user
        cur = get_cursor()
        conn = get_connection()

        logger.info(f"User {user.id} (@{user.username}) started the bot")

        is_admin_user = is_admin(user.id)
        if is_admin_user:
            logger.info(f"Admin user {user.id} starting test interview - bypassing completion lock")

        # Check if interview already completed (unless admin)
        cur.execute("SELECT has_completed_interview, decision, feedback FROM candidates WHERE user_id=?", (user.id,))
        existing = cur.fetchone()

        if existing and existing[0] == 1 and not is_admin_user:
            has_completed, decision, stored_feedback = existing
            decision = decision or "N/A"
            logger.warning(f"User {user.id} attempted /start after completion - BLOCKED (Decision: {decision})")
            if decision == "APPROVED":
                await update.message.reply_text(
                    "You have already completed the interview and were accepted.\n\n"
                    "Our team will be in touch with onboarding details. "
                    "If you have any questions, please contact an administrator."
                )
            else:
                if stored_feedback:
                    await update.message.reply_text(stored_feedback)
                else:
                    await update.message.reply_text(
                        "You have already completed the interview. "
                        "We appreciate your interest, but we've decided to move forward with other candidates at this time."
                    )
            return
        elif existing and existing[0] == 1 and is_admin_user:
            logger.info(f"Admin {user.id} restarting interview for testing purposes")
            await update.message.reply_text(
                "🛠️ Admin Test Mode: Restarting interview for testing.\n\n"
                "You can retake the interview as many times as needed for testing purposes."
            )

        # Check if interview in progress
        cur.execute("SELECT question_index, has_completed_interview FROM candidates WHERE user_id=?", (user.id,))
        row = cur.fetchone()

        if row and row[1] == 0 and not is_admin_user:
            current_index, _ = row
            user_questions = get_user_questions(cur, user.id)
            if user_questions and 1 <= current_index <= len(user_questions):
                await update.message.reply_text(
                    f"You already have an interview in progress.\n\n"
                    f"You're on question {current_index} of {len(user_questions)}.\n"
                    f"Please continue by answering the current question."
                )
                logger.info(f"User {user.id} tried to restart while interview in progress (question {current_index})")
                return
        elif row and row[1] == 0 and is_admin_user:
            logger.info(f"Admin {user.id} restarting interview that was in progress")
            await update.message.reply_text(
                "🛠️ Admin Test Mode: Restarting interview (previous interview was in progress).\n\n"
                "You can retake the interview as many times as needed for testing purposes."
            )

        # Fresh start
        cur.execute("SELECT has_completed_interview FROM candidates WHERE user_id=?", (user.id,))
        check_completed = cur.fetchone()

        if check_completed and check_completed[0] == 1 and not is_admin_user:
            logger.error(f"CRITICAL: Attempted fresh start for user {user.id} but has_completed_interview=1!")
            await update.message.reply_text(
                "You have already completed the interview. Please contact an administrator if you believe this is an error."
            )
            return

        cur.execute("DELETE FROM responses WHERE user_id = ?", (user.id,))
        conn.commit()
        logger.info(f"[START] Deleted all old responses for user {user.id}")

        # Select questions and reset state
        selected_questions = get_random_questions()
        questions_json = json.dumps(selected_questions)

        cur.execute("""
        UPDATE candidates
        SET username = ?, question_index = 1, last_time = ?, completed = 0,
            score = 0, ai_score = 0, decision = NULL, feedback = NULL,
            has_completed_interview = 0, selected_questions = ?
        WHERE user_id = ?
        """, (user.username, time.time(), questions_json, user.id))

        if cur.rowcount == 0:
            cur.execute("""
            INSERT INTO candidates
            (user_id, username, question_index, last_time, completed, score, ai_score, decision, feedback, has_completed_interview, selected_questions)
            VALUES (?, ?, 1, ?, 0, 0, 0, NULL, NULL, 0, ?)
            """, (user.id, user.username, time.time(), questions_json))

        conn.commit()
        logger.info(f"[START] Fresh interview started for user {user.id} {'(ADMIN TEST MODE)' if is_admin_user else ''}")

        welcome_message = (
            "Hello! 👋\n\n"
            "We're happy to see you're interested in becoming part of our team.\n\n"
            f"We'll now proceed with the interview phase. This consists of {len(selected_questions)} short questions designed to understand "
            "how you communicate, handle different fan situations, and whether your style aligns with what we're looking for.\n\n"
            "There are no trick questions. Just be yourself and answer naturally."
        )
        if is_admin_user:
            welcome_message = "🛠️ Admin Test Mode\n\n" + welcome_message

        await update.message.reply_text(welcome_message)
        await update.message.reply_text(f"(1/{len(selected_questions)}) {selected_questions[0]}")
        logger.info(f"Welcome and first question sent to user {user.id}")
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages - route to appropriate state handler."""
    try:
        user = update.effective_user
        text = update.message.text
        cur = get_cursor()
        conn = get_connection()

        logger.info(f"User {user.id} (@{user.username}) sent message: {text[:50]}...")

        cur.execute("""
            SELECT question_index, last_time, has_completed_interview
            FROM candidates WHERE user_id = ?
        """, (user.id,))
        row = cur.fetchone()

        if not row:
            await update.message.reply_text(
                "👋 Welcome!\n\n"
                "This is the interview bot for our team application process.\n\n"
                "Tap /start to begin your interview."
            )
            return

        index, last_time, has_completed = row

        is_admin_user = is_admin(user.id)
        if has_completed == 1 and not is_admin_user:
            await update.message.reply_text(
                "You have already completed the interview. Please use /start to see your results."
            )
            return
        elif has_completed == 1 and is_admin_user:
            logger.info(f"Admin {user.id} continuing after completion - resetting lock")
            cur.execute("UPDATE candidates SET has_completed_interview = 0, completed = 0 WHERE user_id = ?", (user.id,))
            conn.commit()

        # Route to state handler
        if index >= 1:
            await _handle_answer(update, text, index, user.id, last_time, cur, conn, context)
        else:
            await update.message.reply_text("Sorry, an error occurred. Please use /start to begin.")

    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        try:
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")


async def _handle_answer(update: Update, text: str, index: int, user_id: int,
                         last_time: float, cur, conn, context):
    """Handle answer to question - score and move to next."""
    user_questions = get_user_questions(cur, user_id)
    if not user_questions:
        await update.message.reply_text("Sorry, an error occurred. Please start over with /start")
        logger.error(f"No questions found for user {user_id}")
        return

    previous_question_num = index - 1

    # Check idempotency
    cur.execute("SELECT id FROM responses WHERE user_id = ? AND question_number = ?",
                (user_id, previous_question_num))
    if cur.fetchone():
        logger.warning(f"User {user_id} tried to score question {previous_question_num} AGAIN - moving to next question")
        if index < len(user_questions):
            cur.execute("UPDATE candidates SET question_index = question_index + 1, last_time = ? WHERE user_id = ?",
                        (time.time(), user_id))
            conn.commit()
            await update.message.reply_text(user_questions[index])
        return

    cur.execute("SELECT score, ai_score, has_completed_interview FROM candidates WHERE user_id=?", (user_id,))
    current_state = cur.fetchone()

    if not current_state:
        await update.message.reply_text("Sorry, an error occurred. Please start over with /start")
        return

    current_score, current_ai_score, has_completed_check = current_state

    is_admin_user = is_admin(user_id)
    if has_completed_check == 1 and not is_admin_user:
        await update.message.reply_text("You have already completed the interview. Please use /start to see your results.")
        return
    elif has_completed_check == 1 and is_admin_user:
        logger.info(f"Admin {user_id} answering after completion - resetting lock")
        cur.execute("UPDATE candidates SET has_completed_interview = 0, completed = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

    response_time = time.time() - last_time
    previous_question_text = user_questions[previous_question_num] if 0 <= previous_question_num < len(user_questions) else "Initial message"

    logger.info(f"Scoring response for user {user_id}, question {previous_question_num}")
    score, ai_score = analyze_response(text, response_time)

    cur.execute("""
    INSERT INTO responses (user_id, question_number, question_text, response_text, response_time, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, previous_question_num, previous_question_text, text, response_time, time.time()))
    conn.commit()

    max_possible_score = QUESTIONS_PER_INTERVIEW * 10
    if current_score > max_possible_score:
        logger.error(f"Current score {current_score} exceeds maximum {max_possible_score} for user {user_id}")
        cur.execute("UPDATE candidates SET score = 0, ai_score = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

    if is_admin_user:
        cur.execute("""
        UPDATE candidates
        SET score = score + ?, ai_score = ai_score + ?, question_index = question_index + 1, last_time = ?
        WHERE user_id = ?
        """, (score, ai_score, time.time(), user_id))
    else:
        cur.execute("""
        UPDATE candidates
        SET score = score + ?, ai_score = ai_score + ?, question_index = question_index + 1, last_time = ?
        WHERE user_id = ? AND has_completed_interview = 0
        """, (score, ai_score, time.time(), user_id))

    if cur.rowcount == 0:
        await update.message.reply_text("Sorry, an error occurred. Please contact support.")
        return

    conn.commit()
    logger.info(f"User {user_id}, Question {previous_question_num}: Added score={score}, ai_score={ai_score}")

    if index < len(user_questions):
        await update.message.reply_text(f"({index + 1}/{len(user_questions)}) {user_questions[index]}")
        logger.info(f"Sent question {index} to user {user_id}")
    else:
        await _complete_interview(user_id, cur, conn, update, context)


async def _complete_interview(user_id: int, cur, conn, update, context):
    """Complete interview and determine final decision."""
    is_admin_user = is_admin(user_id)

    cur.execute("SELECT has_completed_interview, score, ai_score FROM candidates WHERE user_id=?", (user_id,))
    final_check = cur.fetchone()

    if not final_check:
        await update.message.reply_text("Sorry, an error occurred. Please contact support.")
        return

    has_completed, final_score, final_ai_score = final_check

    if has_completed == 1 and not is_admin_user:
        await update.message.reply_text("You have already completed the interview. Please use /start to see your results.")
        return
    elif has_completed == 1 and is_admin_user:
        logger.info(f"Admin {user_id} completing interview again (test mode)")

    max_possible_score = QUESTIONS_PER_INTERVIEW * 10
    if final_score > max_possible_score:
        logger.error(f"Final score {final_score} exceeds maximum {max_possible_score} - capping")
        final_score = max_possible_score
        cur.execute("UPDATE candidates SET score = ? WHERE user_id = ?", (final_score, user_id))
        conn.commit()

    decision = determine_decision(final_score, final_ai_score)
    logger.info(f"FINAL DECISION: User {user_id}, Score: {final_score}, AI Score: {final_ai_score}, Decision: {decision}")

    feedback = generate_feedback(final_score, final_ai_score, decision)

    if is_admin_user:
        cur.execute("""
        UPDATE candidates
        SET completed = 1, has_completed_interview = 1, decision = ?, feedback = ?, last_time = ?
        WHERE user_id = ?
        """, (decision, feedback, time.time(), user_id))
    else:
        cur.execute("""
        UPDATE candidates
        SET completed = 1, has_completed_interview = 1, decision = ?, feedback = ?, last_time = ?
        WHERE user_id = ? AND has_completed_interview = 0
        """, (decision, feedback, time.time(), user_id))
    conn.commit()

    if not is_admin_user:
        cur.execute("SELECT has_completed_interview, completed FROM candidates WHERE user_id=?", (user_id,))
        verify_lock = cur.fetchone()
        if verify_lock and (verify_lock[0] != 1 or verify_lock[1] != 1):
            logger.error(f"Completion lock verification failed for user {user_id}")
            cur.execute("UPDATE candidates SET completed = 1, has_completed_interview = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
        else:
            logger.info(f"PERMANENT LOCK VERIFIED: User {user_id}, interview completed")
    else:
        logger.info(f"Interview completed for admin {user_id} (test mode - can retake)")

    if is_admin_user:
        await update.message.reply_text(feedback + "\n\n🛠️ Admin Test Mode: You can retake this interview anytime using /start")
        logger.info(f"Interview completed for admin {user_id} (test mode) - Decision: {decision}")
    else:
        await update.message.reply_text(feedback)
        logger.info(f"Interview completed for user {user_id} - Decision: {decision}")

    if not is_admin_user:
        # Notify admin
        try:
            import bot
            admin_ids = getattr(bot, 'ADMIN_IDS', [])
            await notify_admin(user_id, context, cur, admin_ids)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to get ADMIN_IDS for notification: {e}")

    # Push results to ClickUp (all users including admins)
    cur.execute("SELECT username FROM candidates WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    username = (row[0] or "") if row else ""
    if username:
        try:
            from integrations.clickup import push_interview_results
            replies = _build_replies_text(cur, user_id)
            push_interview_results(username, decision, final_score, replies)
        except LookupError as e:
            logger.warning(f"ClickUp task not found for @{username}: {e}")
        except Exception as e:
            logger.exception(f"Failed to push results to ClickUp for @{username}: {e}")
    else:
        logger.warning(f"No username for user {user_id}, skipping ClickUp push")


async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_ids):
    """Show an admin-only confirmation button before purging the database."""
    try:
        user = update.effective_user
        user_id = user.id if user else None

        if user_id not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            logger.warning(f"User {user_id} attempted to use /purge without permission")
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm purge", callback_data=PURGE_CONFIRM_CALLBACK)],
            [InlineKeyboardButton("Cancel", callback_data=PURGE_CANCEL_CALLBACK)],
        ])
        await update.message.reply_text(
            "This will permanently delete all candidates and responses from the bot database.\n\n"
            "Press Confirm purge only if you are sure.",
            reply_markup=keyboard,
        )
        logger.info(f"Admin {user_id} opened purge confirmation")
    except Exception as e:
        logger.error(f"Error in purge_command: {e}", exc_info=True)
        if update and update.message:
            await update.message.reply_text("❌ Error opening purge confirmation. Check logs.")


async def payment_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks for admin actions."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id if query.from_user else None
    if not user_id:
        return
    data = query.data

    if data == PURGE_CONFIRM_CALLBACK:
        if not is_admin(user_id):
            await query.edit_message_text("You do not have permission to purge the database.")
            logger.warning(f"User {user_id} attempted to confirm purge without permission")
            return
        try:
            clear_database()
            logger.warning(f"Admin {user_id} purged the database")
            await query.edit_message_text("Database purged successfully.")
        except Exception:
            logger.exception("Admin purge failed")
            await query.edit_message_text("Database purge failed. Check the logs.")
        return

    if data == PURGE_CANCEL_CALLBACK:
        if not is_admin(user_id):
            await query.edit_message_text("You do not have permission to manage purge actions.")
            logger.warning(f"User {user_id} attempted to cancel purge without permission")
            return
        logger.info(f"Admin {user_id} cancelled database purge")
        await query.edit_message_text("Database purge cancelled.")
        return


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_ids, stop_bot_func, kill_processes_func):
    """Stop the bot (admin only)."""
    try:
        user = update.effective_user
        user_id = user.id if user else None

        if user_id not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            logger.warning(f"User {user_id} attempted to use /stop command without permission")
            return

        logger.info(f"Admin {user_id} requested bot shutdown")
        await update.message.reply_text("🛑 Stopping bot... Please wait.")

        success = stop_bot_func()

        if success:
            await update.message.reply_text("✅ Bot stopped successfully.")
        else:
            await update.message.reply_text("⚠️ Bot stop initiated, but some errors occurred. Check logs.")

        kill_processes_func()
        import sys
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error in stop_command: {e}", exc_info=True)
        if update and update.message:
            await update.message.reply_text("❌ Error stopping bot. Check logs.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
