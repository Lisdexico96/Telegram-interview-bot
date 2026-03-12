"""
Utility functions for feedback generation and admin notifications
"""

import logging
from app.questions import QUESTIONS_PER_INTERVIEW

logger = logging.getLogger(__name__)


def generate_feedback(score: int, ai_score: int, decision: str) -> str:
    """
    Generate user-friendly feedback message.
    Never mention AI detection, scoring, or technical details to users.
    """
    if decision == "APPROVED":
        return (
            "Thank you for completing the interview! 🎉\n\n"
            "We're pleased to let you know that we'd like to move forward with your application. "
            "You demonstrated strong emotional control, escalation skills, and understanding of monetization strategy.\n\n"
            "Next steps:\n"
            "• You'll receive onboarding information within the next 24-48 hours\n"
            "• Our team will reach out with training details and access credentials\n"
            "• Please keep an eye on your messages for further instructions\n\n"
            "Welcome to the team! We're excited to work with you."
        )
    elif decision == "BORDERLINE":
        return (
            "Thank you for completing the interview! 👋\n\n"
            "You showed good potential in your responses. While we're not moving forward immediately, "
            "we'd like to keep your application on file for future opportunities.\n\n"
            "Your communication style shows promise, but may benefit from additional training in pacing or objection handling.\n\n"
            "We appreciate your interest and wish you the best in your search."
        )
    else:
        return (
            "Thank you for completing the interview!\n\n"
            "Your answers have been automatically reviewed and based on that initial screening, "
            "the fit doesn't seem quite right at this time.\n\n"
            "That said, we personally review every application — so if anything changes or we see "
            "a good opportunity for you, we'll reach out to you directly on Telegram.\n\n"
            "We appreciate you taking the time and wish you the best."
        )


async def notify_admin(user_id: int, context, cur, admin_ids):
    """Notify admin about completed interview."""
    try:
        cur.execute("SELECT username, name, score, ai_score, decision FROM candidates WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            logger.warning(f"No data found for user {user_id} when trying to notify admin")
            return
        
        username, candidate_name, score, ai_score, decision = row
        display_name = candidate_name if candidate_name else f"@{username}" if username else f"User {user_id}"

        # Get all responses
        cur.execute("""
        SELECT question_number, question_text, response_text, response_time 
        FROM responses 
        WHERE user_id = ? 
        ORDER BY question_number
        """, (user_id,))
        responses = cur.fetchall()

        max_score = QUESTIONS_PER_INTERVIEW * 10
        percentage = (score / max_score * 100) if max_score > 0 else 0

        ai_note = (
            "Low AI risk." if ai_score <= 3 else
            "Moderate AI risk." if ai_score <= 6 else
            "High AI risk."
        )

        if decision == "APPROVED":
            feedback = (
                f"Candidate demonstrates strong emotional control, escalation skills, and monetization understanding. "
                f"Score: {score}/{max_score} ({percentage:.1f}%). {ai_note} "
                f"Recommend onboarding and training."
            )
        elif decision == "BORDERLINE":
            feedback = (
                f"Candidate shows good potential but needs training in pacing or rebuttals. "
                f"Score: {score}/{max_score} ({percentage:.1f}%). {ai_note} "
                f"Consider for future opportunities after additional training."
            )
        else:
            feedback = (
                f"Candidate lacks control, realism, or monetization logic. "
                f"Score: {score}/{max_score} ({percentage:.1f}%). {ai_note}"
            )

        # Build response summary
        response_summary = "\n\n📝 Responses:\n"
        for q_num, q_text, r_text, r_time in responses:
            response_summary += f"\nQ{q_num+1}: {q_text}\n"
            response_summary += f"A: {r_text[:100]}{'...' if len(r_text) > 100 else ''}\n"
            response_summary += f"Response time: {r_time:.1f}s\n"

        message = (
            f"📋 Interview Evaluation\n\n"
            f"Candidate: {display_name}\n"
            f"Username: @{username or 'N/A'}\n"
            f"User ID: {user_id}\n"
            f"Decision: {decision}\n"
            f"Score: {score}\n"
            f"AI Assessment: {ai_note}\n\n"
            f"Feedback:\n{feedback}"
            f"{response_summary}"
        )

        for admin in admin_ids:
            try:
                if len(message) > 4000:
                    summary_msg = (
                        f"📋 Interview Evaluation\n\n"
                        f"Candidate: {display_name}\n"
                        f"Username: @{username or 'N/A'}\n"
                        f"User ID: {user_id}\n"
                        f"Decision: {decision}\n"
                        f"Score: {score}\n"
                        f"AI Assessment: {ai_note}\n\n"
                        f"Feedback:\n{feedback}\n\n"
                        f"See detailed responses in log file or use view_results.py script."
                    )
                    await context.bot.send_message(chat_id=admin, text=summary_msg)
                else:
                    await context.bot.send_message(chat_id=admin, text=message)
                logger.info(f"Notification sent to admin {admin}")
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin}: {e}")
        
        # Log to file
        logger.info(f"COMPLETED INTERVIEW - Candidate: {display_name} (@{username or 'N/A'}, ID: {user_id}), Decision: {decision}, Score: {score}, AI Score: {ai_score}")
        for q_num, q_text, r_text, r_time in responses:
            logger.info(f"  Q{q_num+1}: {q_text} | Response: {r_text} | Time: {r_time:.1f}s")
    except Exception as e:
        logger.error(f"Error in notify_admin: {e}", exc_info=True)
