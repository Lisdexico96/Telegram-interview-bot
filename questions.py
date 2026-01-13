"""
Interview questions bank - Random pool of 49 questions
Each interview randomly selects 5 questions from this pool.
"""

import random

# Question pool - 49 questions total, randomly select 5 from these for each interview
QUESTION_POOL = [
    # FAN PSYCHOLOGY & INTENT READING
    "Fan: I don't usually subscribe to girls like you… but something about you feels different.",
    "A fan is very chatty, flirty, and affectionate, but hasn't spent yet. What signals do you look for before trying to monetize?",
    "Fan: I wish you were real… like actually mine.",
    "A fan goes quiet right after a good conversation. What's your follow-up message and why?",
    "Fan: You're different from other girls, I feel a real connection with you",
    "Fan: Am I special to you or just another customer?",
    "Fan: Do you talk to other guys like this too?",
    
    # MONETIZATION INSTINCT (WITHOUT BEING SALESY)
    "When is the wrong time to push paid content, and how do you recover if you pushed too early?",
    "Fan: I'll buy later, I just want to talk right now.",
    "How do you make a fan feel like spending was their idea?",
    "What's the difference between teasing for engagement and teasing for conversion?",
    "Fan: Why should I pay when I can get girls for free?",
    "Fan: That's too expensive, can you lower the price?",
    "Fan: I don't have money right now, can you send something free?",
    
    # FANTASY MANAGEMENT & BOUNDARIES
    "Fan: If we meet up I'll spoil you better, I promise princess 😏",
    "A fan hints at meeting up but doesn't say it directly. How do you keep the fantasy alive while staying safe?",
    "A fan asks a personal question that's too real or invasive. How do you redirect without sounding cold?",
    "What's more important: maintaining fantasy or being believable? Explain.",
    "If a fan starts getting emotionally dependent, what's your approach?",
    "Fan: What would you do to me right now if I was there?",
    "Fan: Can we meet in person? I'll take care of you 😈",
    "Fan: I wish you were my girlfriend for real",
    
    # ADAPTABILITY & REAL-TIME THINKING
    "A fan reacts badly to a message you sent. What's your next move?",
    "How do you adjust your tone between a new fan and a long-term spender?",
    "What do you do when a conversation feels stuck but not dead?",
    "Describe a situation where you would slow down escalation on purpose.",
    "Fan: You're so perfect, I can't stop thinking about you",
    
    # STYLE, TONE & HUMANNESS
    "What makes a message feel human instead of scripted?",
    "Write one sentence you would send to a fan that feels intimate but safe.",
    "How do you keep conversations feeling natural when you're having many at once?",
    "What's a mistake you see bad chatters make over and over?",
    
    # JUDGMENT & PROFESSIONALISM
    "A fan is rude but spends well. How do you handle that balance?",
    "What would make you stop engaging with a fan entirely?",
    "If you disagree with a model's tone or brand, how do you adapt?",
    "Why do you think some chatters make fans fall in love while others don't?",
    
    # ORIGINAL SCENARIOS (fan messages)
    "Fan: Damn baby you got me so fucking hard right now 😈",
    "Fan: Be honest… do you actually like talking to me?",
    "Fan: Can you send me some free pics? I'm really tight on money right now.",
    "Fan: Come on, we've been talking for a while, you owe me",
    "Fan: Other girls send me free pics, why won't you?",
    "Fan: I've been a subscriber for months, you should appreciate me more",
    "Fan: You make me so horny, I need you right now",
    "Fan: I'm touching myself thinking about you",
    "Fan: I need to see more of you right now",
    "Fan: Why aren't you responding? Are you ignoring me?",
    "Fan: I'm your biggest fan, you should send me something special",
    "Fan: Can you do something just for me? I'll make it worth your while",
    "Fan: You're always busy, are you even real?",
    "Fan: I've been so good, don't I deserve a reward?",
    "Fan: Other girls give me free stuff, why are you different?",
    "Fan: I thought we had a connection, but you just want my money",
    "Fan: You're not like the others, that's why I like you",
    "Fan: Can we be friends? I don't want this to be just transactional"
]

# Number of questions to ask per interview
QUESTIONS_PER_INTERVIEW = 5


def get_random_questions() -> list[str]:
    """
    Randomly select QUESTIONS_PER_INTERVIEW unique questions from the pool.
    
    Returns:
        List of 5 randomly selected questions
    """
    if len(QUESTION_POOL) < QUESTIONS_PER_INTERVIEW:
        # If pool is smaller than needed, just return all questions
        return QUESTION_POOL.copy()
    
    # Randomly sample without replacement
    return random.sample(QUESTION_POOL, QUESTIONS_PER_INTERVIEW)


# For backwards compatibility - but don't use this directly
# Use get_random_questions() instead
QUESTIONS = QUESTION_POOL
