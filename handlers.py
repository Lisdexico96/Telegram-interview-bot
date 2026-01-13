"""
Telegram bot handlers for interview process
"""

import time
import logging
import json
from telegram import Update
from telegram.ext import ContextTypes

from database import get_cursor, get_connection
from questions import get_random_questions, QUESTIONS_PER_INTERVIEW
from scoring import analyze_response, determine_decision
from utils import generate_feedback, notify_admin

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    # Import at runtime to avoid circular import issues
    try:
        import sys
        # Get the bot module from sys.modules if it's already loaded
        if 'bot' in sys.modules:
            bot_module = sys.modules['bot']
            admin_ids = getattr(bot_module, 'ADMIN_IDS', [])
        else:
            # Import if not loaded yet
            import bot
            admin_ids = getattr(bot, 'ADMIN_IDS', [])
        
        result = user_id in admin_ids
        logger.info(f"Admin check for user {user_id}: ADMIN_IDS={admin_ids}, is_admin={result}")
        return result
    except (ImportError, AttributeError, Exception) as e:
        logger.error(f"Failed to get ADMIN_IDS for user {user_id}: {e}, defaulting to False", exc_info=True)
        return False


def get_user_questions(cur, user_id: int) -> list[str]:
    """
    Get the selected questions for a user from the database.
    If no questions are stored yet, returns None.
    """
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

        # Check if user is admin - admins can retake the test unlimited times
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
            # Admin can restart even after completion
            logger.info(f"Admin {user.id} restarting interview for testing purposes")
            await update.message.reply_text(
                "🛠️ Admin Test Mode: Restarting interview for testing.\n\n"
                "You can retake the interview as many times as needed for testing purposes."
            )

        # Check if interview in progress (admins can restart even if in progress)
        cur.execute("SELECT question_index, name, has_completed_interview FROM candidates WHERE user_id=?", (user.id,))
        row = cur.fetchone()
        
        if row and row[2] == 0 and not is_admin_user:
            current_index, name, _ = row
            user_questions = get_user_questions(cur, user.id)
            if user_questions:
                total = len(user_questions)
                if current_index >= 0 and current_index <= total:
                    await update.message.reply_text(
                        f"You already have an interview in progress.\n\n"
                        f"You're on question {current_index if current_index > 0 else 1} of {total}.\n"
                        f"Please continue by answering the current question."
                    )
                    logger.info(f"User {user.id} tried to restart while interview in progress (question {current_index})")
                    return
        elif row and row[2] == 0 and is_admin_user:
            # Admin can restart even if interview is in progress
            logger.info(f"Admin {user.id} restarting interview that was in progress")
            await update.message.reply_text(
                "🛠️ Admin Test Mode: Restarting interview (previous interview was in progress).\n\n"
                "You can retake the interview as many times as needed for testing purposes."
            )

        # Fresh start - reset all state (admins can always do this)
        cur.execute("SELECT has_completed_interview FROM candidates WHERE user_id=?", (user.id,))
        check_completed = cur.fetchone()
        
        if check_completed and check_completed[0] == 1 and not is_admin_user:
            logger.error(f"CRITICAL: Attempted fresh start for user {user.id} but has_completed_interview=1!")
            await update.message.reply_text(
                "You have already completed the interview. Please contact an administrator if you believe this is an error."
            )
            return

        # Delete old responses
        cur.execute("DELETE FROM responses WHERE user_id = ?", (user.id,))
        conn.commit()
        logger.info(f"[START] Deleted all old responses for user {user.id}")

        # Reset state (force reset for admins, even if previously completed)
        cur.execute("""
        UPDATE candidates 
        SET username = ?, question_index = -1, last_time = ?, completed = 0, 
            score = 0, ai_score = 0, decision = NULL, name = NULL, feedback = NULL, has_completed_interview = 0
        WHERE user_id = ?
        """, (user.username, time.time(), user.id))
        
        if cur.rowcount == 0:
            cur.execute("""
            INSERT INTO candidates 
            (user_id, username, question_index, last_time, completed, score, ai_score, decision, name, feedback, has_completed_interview)
            VALUES (?, ?, -1, ?, 0, 0, 0, NULL, NULL, NULL, 0)
            """, (user.id, user.username, time.time()))
        
        conn.commit()
        logger.info(f"[START] Fresh interview started for user {user.id} {'(ADMIN TEST MODE)' if is_admin_user else ''}")

        # Ask for name (with admin note if applicable)
        if is_admin_user:
            await update.message.reply_text(
                "Hello! 👋 (Admin Test Mode)\n\n"
                "You can retake this interview as many times as needed for testing.\n\n"
                "Please tell us your first name to get started."
            )
        else:
            await update.message.reply_text(
                "Hello! 👋\n\n"
                "Please tell us your first name to get started."
            )
        logger.info(f"Name request sent to user {user.id}")
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

        cur.execute("SELECT question_index, name, last_time, has_completed_interview FROM candidates WHERE user_id=?", (user.id,))
        row = cur.fetchone()
        
        if not row:
            await update.message.reply_text("Please start the bot first by sending /start")
            return

        index, name, last_time, has_completed = row

        # Guard: Check completion lock (admins can bypass)
        is_admin_user = is_admin(user.id)
        if has_completed == 1 and not is_admin_user:
            await update.message.reply_text(
                "You have already completed the interview. Please use /start to see your results."
            )
            return
        elif has_completed == 1 and is_admin_user:
            # Admin can continue even after completion - reset the lock for them
            logger.info(f"Admin {user.id} continuing after completion - resetting lock")
            cur.execute("UPDATE candidates SET has_completed_interview = 0, completed = 0 WHERE user_id = ?", (user.id,))
            conn.commit()

        # Route to state handler
        if index == -1:
            await _handle_name_input(update, text, user.id, cur, conn)
        elif index == 0:
            await _handle_welcome(update, user.id, cur, conn)
        elif index >= 1:
            await _handle_answer(update, text, index, user.id, last_time, cur, conn, context)
        else:
            await update.message.reply_text("Sorry, an error occurred. Please use /start to begin.")
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        try:
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")


async def _handle_name_input(update: Update, text: str, user_id: int, cur, conn):
    """Handle name input state."""
    applicant_name = text.strip()
    
    # Validate name
    if len(applicant_name) < 2:
        await update.message.reply_text("Please provide a valid first name (at least 2 characters).")
        return
    
    if len(applicant_name) > 20:
        await update.message.reply_text("Please provide just your first name (not a long message).")
        return
    
    if "." in applicant_name or "\n" in applicant_name:
        await update.message.reply_text("Please provide just your first name (not a sentence or paragraph).")
        return
    
    # Check completion lock again (admins can bypass)
    is_admin_user = is_admin(user_id)
    cur.execute("SELECT has_completed_interview FROM candidates WHERE user_id=?", (user_id,))
    check_completed = cur.fetchone()
    if check_completed and check_completed[0] == 1 and not is_admin_user:
        await update.message.reply_text("You have already completed the interview. Please use /start to see your results.")
        return
    elif check_completed and check_completed[0] == 1 and is_admin_user:
        # Reset lock for admin
        logger.info(f"Admin {user_id} providing name after completion - resetting lock")
        cur.execute("UPDATE candidates SET has_completed_interview = 0, completed = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
    
    logger.info(f"User {user_id} provided name: {applicant_name}")
    
    # Randomly select 5 questions for this interview
    selected_questions = get_random_questions()
    questions_json = json.dumps(selected_questions)
    
    logger.info(f"Selected {len(selected_questions)} random questions for user {user_id}")
    
    # Store name, selected questions, and transition to welcome state
    # For admins, remove the has_completed_interview restriction
    if is_admin_user:
        cur.execute("""
        UPDATE candidates
        SET name = ?, question_index = 0, last_time = ?, score = 0, ai_score = 0, completed = 0, 
            decision = NULL, feedback = NULL, has_completed_interview = 0, selected_questions = ?
        WHERE user_id = ?
        """, (applicant_name, time.time(), questions_json, user_id))
    else:
        cur.execute("""
        UPDATE candidates
        SET name = ?, question_index = 0, last_time = ?, score = 0, ai_score = 0, completed = 0, 
            decision = NULL, feedback = NULL, has_completed_interview = 0, selected_questions = ?
        WHERE user_id = ? AND has_completed_interview = 0
        """, (applicant_name, time.time(), questions_json, user_id))
    
    if cur.rowcount == 0:
        await update.message.reply_text("Sorry, an error occurred. Please try /start again.")
        return
    
    conn.commit()
    
    # Send welcome message
    welcome_message = (
        f"Hello {applicant_name} 👋\n\n"
        "We're happy to see you're interested in becoming part of our team.\n\n"
        "We'll now proceed with the interview phase. This consists of a few short questions designed to understand "
        "how you communicate, handle different fan situations, and whether your style aligns with what we're looking for.\n\n"
        "There are no trick questions. Just be yourself and answer naturally."
    )
    await update.message.reply_text(welcome_message)
    
    # Send first question (from randomly selected questions)
    await update.message.reply_text(selected_questions[0])
    
    # Move to question 1 (admins can always update)
    is_admin_user = is_admin(user_id)
    if is_admin_user:
        cur.execute("""
        UPDATE candidates
        SET question_index = 1, last_time = ?
        WHERE user_id = ?
        """, (time.time(), user_id))
    else:
        cur.execute("""
        UPDATE candidates
        SET question_index = 1, last_time = ?
        WHERE user_id = ? AND has_completed_interview = 0
        """, (time.time(), user_id))
    conn.commit()
    
    logger.info(f"User {user_id} name stored, welcome sent, question 0 sent, moved to index 1")


async def _handle_welcome(update: Update, user_id: int, cur, conn):
    """Handle welcome state - send first question."""
    # Check if admin - admins can always update
    is_admin_user = is_admin(user_id)
    
    # Get selected questions for this user
    user_questions = get_user_questions(cur, user_id)
    if not user_questions:
        # If no questions selected yet, select them now
        user_questions = get_random_questions()
        questions_json = json.dumps(user_questions)
        if is_admin_user:
            cur.execute("""
            UPDATE candidates
            SET selected_questions = ?
            WHERE user_id = ?
            """, (questions_json, user_id))
        else:
            cur.execute("""
            UPDATE candidates
            SET selected_questions = ?
            WHERE user_id = ? AND has_completed_interview = 0
            """, (questions_json, user_id))
        conn.commit()
        logger.info(f"Selected {len(user_questions)} random questions for user {user_id} in welcome handler")
    
    await update.message.reply_text(user_questions[0])
    
    # Update question index (admins can always update)
    if is_admin_user:
        cur.execute("""
        UPDATE candidates
        SET question_index = 1, last_time = ?
        WHERE user_id = ?
        """, (time.time(), user_id))
    else:
        cur.execute("""
        UPDATE candidates
        SET question_index = 1, last_time = ?
        WHERE user_id = ? AND has_completed_interview = 0
        """, (time.time(), user_id))
    conn.commit()
    
    logger.info(f"Welcome question sent to user {user_id}")


async def _handle_answer(update: Update, text: str, index: int, user_id: int, 
                        last_time: float, cur, conn, context):
    """Handle answer to question - score and move to next."""
    # Get selected questions for this user
    user_questions = get_user_questions(cur, user_id)
    if not user_questions:
        await update.message.reply_text("Sorry, an error occurred. Please start over with /start")
        logger.error(f"No questions found for user {user_id}")
        return
    
    previous_question_num = index - 1
    
    # Check idempotency - has this question been scored?
    cur.execute("SELECT id FROM responses WHERE user_id = ? AND question_number = ?", 
                (user_id, previous_question_num))
    existing_response = cur.fetchone()
    
    if existing_response:
        logger.warning(f"User {user_id} tried to score question {previous_question_num} AGAIN - moving to next question")
        if index < len(user_questions):
            cur.execute("""
            UPDATE candidates
            SET question_index = question_index + 1, last_time = ?
            WHERE user_id = ?
            """, (time.time(), user_id))
            conn.commit()
            await update.message.reply_text(user_questions[index])
        return
    
    # Get current scores
    cur.execute("SELECT score, ai_score, has_completed_interview FROM candidates WHERE user_id=?", (user_id,))
    current_state = cur.fetchone()
    
    if not current_state:
        await update.message.reply_text("Sorry, an error occurred. Please start over with /start")
        return
    
    current_score, current_ai_score, has_completed_check = current_state
    
    # Allow admins to continue even if marked as completed
    is_admin_user = is_admin(user_id)
    if has_completed_check == 1 and not is_admin_user:
        await update.message.reply_text("You have already completed the interview. Please use /start to see your results.")
        return
    elif has_completed_check == 1 and is_admin_user:
        # Reset lock for admin to allow continuing
        logger.info(f"Admin {user_id} answering after completion - resetting lock")
        cur.execute("UPDATE candidates SET has_completed_interview = 0, completed = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
    
    # Score the response
    response_time = time.time() - last_time
    previous_question_text = user_questions[previous_question_num] if previous_question_num >= 0 and previous_question_num < len(user_questions) else "Initial message"
    
    logger.info(f"Scoring response for user {user_id}, question {previous_question_num}")
    score, ai_score = analyze_response(text, response_time)
    
    # Save response first (marks as scored)
    cur.execute("""
    INSERT INTO responses (user_id, question_number, question_text, response_text, response_time, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, previous_question_num, previous_question_text, text, response_time, time.time()))
    conn.commit()
    
    # Verify score doesn't exceed maximum (5 questions * 10 points = 50)
    max_possible_score = QUESTIONS_PER_INTERVIEW * 10
    if current_score > max_possible_score:
        logger.error(f"Current score {current_score} exceeds maximum {max_possible_score} for user {user_id}")
        cur.execute("UPDATE candidates SET score = 0, ai_score = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        current_score = 0
        current_ai_score = 0
    
    # Update scores (admins can update even if completed)
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
    
    # Send next question or complete interview
    if index < len(user_questions):
        await update.message.reply_text(user_questions[index])
        logger.info(f"Sent question {index} to user {user_id}")
    else:
        await _complete_interview(user_id, cur, conn, update, context)


async def _complete_interview(user_id: int, cur, conn, update, context):
    """Complete interview and determine final decision."""
    # Check if user is admin - admins can complete multiple times
    is_admin_user = is_admin(user_id)
    
    cur.execute("SELECT has_completed_interview, score, ai_score FROM candidates WHERE user_id=?", (user_id,))
    final_check = cur.fetchone()
    
    if not final_check:
        await update.message.reply_text("Sorry, an error occurred. Please contact support.")
        return
    
    has_completed, final_score, final_ai_score = final_check
    
    # Allow admins to complete multiple times, but block regular users
    if has_completed == 1 and not is_admin_user:
        await update.message.reply_text("You have already completed the interview. Please use /start to see your results.")
        return
    elif has_completed == 1 and is_admin_user:
        logger.info(f"Admin {user_id} completing interview again (test mode)")
    
    # Cap score at maximum (5 questions * 10 points = 50)
    max_possible_score = QUESTIONS_PER_INTERVIEW * 10
    if final_score > max_possible_score:
        logger.error(f"Final score {final_score} exceeds maximum {max_possible_score} - capping")
        final_score = max_possible_score
        cur.execute("UPDATE candidates SET score = ? WHERE user_id = ?", (final_score, user_id))
        conn.commit()
    
    # Determine decision
    decision = determine_decision(final_score, final_ai_score)
    logger.info(f"FINAL DECISION: User {user_id}, Score: {final_score}, AI Score: {final_ai_score}, Decision: {decision}")
    
    # Generate feedback
    feedback = generate_feedback(final_score, final_ai_score, decision)
    
    # Set completion lock (admins can always update, regular users only if not completed)
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
    
    # Verify lock was set (for regular users, for admins it's okay if it doesn't update)
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
    
    # Send feedback to candidate (add admin note if applicable)
    if is_admin_user:
        admin_note = "\n\n🛠️ Admin Test Mode: You can retake this interview anytime using /start"
        await update.message.reply_text(feedback + admin_note)
        logger.info(f"Interview completed for admin {user_id} (test mode) - Decision: {decision}")
    else:
        await update.message.reply_text(feedback)
        logger.info(f"Interview completed for user {user_id} - Decision: {decision}")
    
    # Notify admin (skip if admin is testing themselves)
    if not is_admin_user:
        # Get ADMIN_IDS at runtime to avoid circular import
        try:
            import bot
            admin_ids = getattr(bot, 'ADMIN_IDS', [])
            await notify_admin(user_id, context, cur, admin_ids)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to get ADMIN_IDS for notification: {e}")
    else:
        logger.info(f"Skipping admin notification for admin user {user_id} (they completed their own test)")


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
