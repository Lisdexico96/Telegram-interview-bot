"""
Response scoring logic based on OnlyFans chatting agency rubric
Philosophy: "Make me yours" through subtle encouragement, not begging.
No free content. Fans spend when they feel chosen.

Key Principles:
- Relationship building is valuable even without immediate sales push
- Setting up for sales subtly (not pushing directly) is good
- Overpushing/overselling damages relationships and scores poorly
- Timing matters - not every response needs to monetize
- Natural conversation flow with appropriate pacing scores well
"""


def analyze_response(text: str, response_time: float) -> tuple[int, int]:
    """
    Score response based on OnlyFans chatting agency rubric (0-10 scale):
    1. Fan Control & Power (0-2) - Confidence, not neediness, emotional intelligence
    2. Emotional Investment Building (0-2) - Relationship building, making fan feel special
    3. Monetization Trajectory (0-2) - Subtle sales setup, NOT overpushing
    4. Rebuttal Skill (0-2) - Handling objections calmly, reframing
    5. Pacing & Realism (0-2) - Natural conversation flow, human-like
    
    Important Notes:
    - Relationship building is valuable even without sales push
    - Setting up sales subtly (future framing) scores well
    - Overpushing/overselling (multiple sales words) scores poorly
    - Timing matters - not every response needs to monetize
    
    Returns:
        tuple: (score, ai_score) both 0-10
    """
    score = 0
    ai_score = 0
    lower = text.lower()
    words = text.split()
    word_count = len(words)

    # 1. FAN CONTROL & POWER (0-2 points)
    score += _score_fan_control(text, lower)

    # 2. EMOTIONAL INVESTMENT BUILDING (0-2 points)
    score += _score_emotional_investment(lower)

    # 3. MONETIZATION TRAJECTORY (0-2 points)
    score += _score_monetization(lower)

    # 4. REBUTTAL SKILL (0-2 points)
    score += _score_rebuttal(lower, word_count)

    # 5. PACING & REALISM (0-2 points)
    score += _score_pacing(lower, word_count)

    # AI DETECTION (flag but don't auto-fail)
    ai_score = _detect_ai_indicators(text, lower, word_count, response_time)

    # Cap scores appropriately
    score = min(score, 10)
    ai_score = min(ai_score, 10)

    return score, ai_score


def _score_fan_control(text: str, lower: str) -> int:
    """Score fan control and power (0-2 points). More lenient scoring."""
    control_score = 0
    
    confident_phrases = ["i want", "i'd love", "i can", "when you", "if you", "for me", "i'd like"]
    needy_phrases = ["please", "i need", "i hope", "maybe", "i guess", "i think so"]
    submissive_phrases = ["sorry", "apologies", "i apologize", "my fault", "i'm so sorry"]
    
    has_confidence = any(phrase in lower for phrase in confident_phrases)
    has_needy = any(phrase in lower for phrase in needy_phrases)
    has_submissive = any(phrase in lower for phrase in submissive_phrases)
    
    # More lenient: Give points if not overly needy/submissive
    if has_confidence and not has_needy and not has_submissive:
        control_score = 2
    elif has_confidence or (not has_needy and not has_submissive):
        control_score = 1
    elif not has_needy:  # Give partial credit if not needy
        control_score = 1
    
    # Only penalize excessive apologizing (3+ times)
    if text.lower().count("sorry") >= 3:
        control_score = max(0, control_score - 1)
    
    return control_score


def _score_emotional_investment(lower: str) -> int:
    """
    Score emotional investment building (0-2 points).
    Relationship building is valuable even without immediate monetization.
    The right moment for sales isn't always now - building rapport counts.
    """
    emotional_score = 0
    
    # Relationship building indicators
    chosen_phrases = ["for you", "special", "only you", "just for you", "you're different", "you're unique"]
    curiosity_phrases = ["imagine", "what if", "think about", "picture", "later", "when", "someday"]
    personal_phrases = ["i love", "i'm into", "i'm drawn to", "you make me", "you're", "i feel", "i appreciate"]
    connection_phrases = ["miss you", "think about you", "remember", "wish", "understand", "get you", "hear you"]
    completion_phrases = ["i love you", "i'm yours", "forever", "always", "promise"]
    
    # Building rapport/relationship (even without sales setup)
    has_chosen = any(phrase in lower for phrase in chosen_phrases)
    has_curiosity = any(phrase in lower for phrase in curiosity_phrases)
    has_personal = any(phrase in lower for phrase in personal_phrases)
    has_connection = any(phrase in lower for phrase in connection_phrases)
    
    # Negative: Over-giving without relationship building
    over_giving = "free" in lower and ("pic" in lower or "photo" in lower or "video" in lower)
    
    # Check if overpushing sales (negative indicator for emotional building)
    sales_pressure_words = ["buy", "pay", "tip now", "send money", "purchase", "order"]
    is_overpushing = sum(1 for word in sales_pressure_words if word in lower) >= 2
    
    # Strong emotional building: Makes fan feel special + creates connection/curiosity
    # Relationship building itself is valuable, even without sales setup
    # More lenient: Give points for any relationship building indicator
    if (has_chosen or has_curiosity) and (has_personal or has_connection) and not any(phrase in lower for phrase in completion_phrases):
        emotional_score = 2  # Strong relationship building
    elif (has_chosen or has_curiosity or has_personal or has_connection) and not over_giving and not is_overpushing:
        emotional_score = 1  # Moderate relationship building
    elif (has_personal or has_connection) and not over_giving:  # Give partial credit for basic connection
        emotional_score = 1
    
    # Penalties
    if over_giving:
        emotional_score = 0  # Over-giving kills relationship dynamic
    if is_overpushing:
        emotional_score = max(0, emotional_score - 1)  # Overpushing damages emotional connection
    
    return emotional_score


def _score_monetization(lower: str) -> int:
    """
    Score monetization trajectory (0-2 points).
    Setting up for sales subtly is good. Overpushing/overselling is bad.
    Timing matters - not every response needs to push sales.
    Relationship building can be more valuable than immediate monetization.
    """
    monetization_score = 0
    
    # Subtle setup keywords (desire-based, not pushy)
    desire_keywords = ["spoil", "treat", "unlock", "exclusive", "special", "premium", "vip"]
    future_ppv_keywords = ["later", "next time", "when you", "if you want", "custom", "personal", "whenever you're ready"]
    subtle_sales = ["tip", "appreciate", "support", "help me", "for me", "when you're feeling generous"]
    
    # Direct pressure/begging (BAD - automatic 0)
    pressure_phrases = ["buy now", "pay me", "send money", "give me", "i need money", "hurry", "limited time"]
    
    # Overpushing indicators (multiple sales words = too pushy)
    # More lenient: Require 4+ sales words to be considered overpushing
    sales_words = ["buy", "pay", "tip", "purchase", "order", "send"]
    sales_word_count = sum(1 for word in sales_words if word in lower)
    is_overpushing = sales_word_count >= 4  # Multiple sales words = overpushing (increased threshold)
    
    begging = any(phrase in lower for phrase in pressure_phrases)
    has_desire = any(kw in lower for kw in desire_keywords)
    has_future_setup = any(kw in lower for kw in future_ppv_keywords)
    has_subtle = any(phrase in lower for phrase in subtle_sales)
    
    # Strong setup: Subtle desire-based language + future framing, NOT pushy
    # More lenient: Give points for any monetization indicators (not just perfect combinations)
    if (has_desire or has_subtle) and has_future_setup and not begging and not is_overpushing:
        monetization_score = 2  # Perfect subtle setup
    elif (has_desire or has_subtle or has_future_setup) and not begging and not is_overpushing:
        monetization_score = 1  # Good setup without being pushy
    elif (has_desire or has_subtle) and not begging:  # Give partial credit for basic monetization
        monetization_score = 1
    
    # Penalties
    if begging:
        monetization_score = 0  # Direct begging = automatic 0
    if is_overpushing:
        monetization_score = 0  # Overpushing = automatic 0 (damages relationship)
    
    # Note: If no monetization setup but good relationship building, 
    # that's fine - relationship building is scored separately in emotional investment
    
    return monetization_score


def _score_rebuttal(lower: str, word_count: int) -> int:
    """Score rebuttal skill (0-2 points)."""
    rebuttal_score = 0
    
    objection_words = ["free", "expensive", "why", "but", "can't afford", "no money", "cheaper"]
    has_objection_context = any(word in lower for word in objection_words)
    
    if has_objection_context:
        reframing_phrases = ["i understand", "see it as", "think of it as", "it's more like", "you're worth"]
        calm_phrases = ["no worries", "totally get it", "that's okay", "i hear you"]
        argument_phrases = ["you're wrong", "that's not true", "no you", "you should"]
        
        has_reframe = any(phrase in lower for phrase in reframing_phrases)
        has_calm = any(phrase in lower for phrase in calm_phrases)
        has_argument = any(phrase in lower for phrase in argument_phrases)
        
        if (has_reframe or has_calm) and not has_argument:
            rebuttal_score = 2
        elif has_reframe or has_calm:
            rebuttal_score = 1
        
        if has_argument or "defend" in lower:
            rebuttal_score = 0
    else:
        # Maintain conversation momentum
        momentum_words = ["yes", "yeah", "sure", "absolutely", "definitely", "of course"]
        if any(word in lower for word in momentum_words) or word_count > 5:
            rebuttal_score = 1
    
    return rebuttal_score


def _score_pacing(lower: str, word_count: int) -> int:
    """
    Score pacing and realism (0-2 points).
    Natural conversation flow without overpushing sales.
    Relationship building has natural pacing.
    """
    pacing_score = 0
    
    contractions = ["i'm", "i've", "don't", "can't", "won't", "it's", "that's", "you're", "we're"]
    has_contractions = any(cont in lower for cont in contractions)
    casual_words = ["yeah", "yep", "hmm", "mm", "haha", "lol", "omg", "tbh", "fr"]
    has_casual = any(cw in lower for cw in casual_words)
    
    corporate_phrases = ["i understand", "i appreciate", "thank you for", "i would be happy to"]
    salesy_phrases = ["limited time", "act now", "don't miss out", "buy today", "hurry up"]
    
    # Overpushing indicators (multiple sales pushes = bad pacing)
    # More lenient: Require 4+ sales words to be considered overpushing
    sales_push_words = ["buy", "pay", "tip", "purchase", "order", "send", "money"]
    sales_push_count = sum(1 for word in sales_push_words if word in lower)
    is_overpushing = sales_push_count >= 4  # Multiple sales words = overpushing (increased threshold)
    
    has_corporate = any(phrase in lower for phrase in corporate_phrases)
    has_salesy = any(phrase in lower for phrase in salesy_phrases)
    
    appropriate_length = 5 <= word_count <= 60
    
    # Natural pacing: Human tone + appropriate length + NOT overpushing
    if (has_contractions or has_casual) and appropriate_length and not has_corporate and not has_salesy and not is_overpushing:
        pacing_score = 2  # Perfect natural pacing
    elif (has_contractions or has_casual or appropriate_length) and not has_salesy and not is_overpushing:
        pacing_score = 1  # Good pacing
    
    # Penalties for overpushing
    if has_salesy:
        pacing_score = 0  # Salesy phrases = automatic 0
    if is_overpushing:
        pacing_score = 0  # Overpushing = automatic 0 (ruins natural flow)
    
    return pacing_score


def _detect_ai_indicators(text: str, lower: str, word_count: int, response_time: float) -> int:
    """Detect AI use indicators (0-10 scale, higher = more AI-like). More lenient detection."""
    ai_score = 0
    
    # Overly polished grammar (more lenient thresholds)
    if text.count(",") > 6:  # Increased from 4 to 6
        ai_score += 2
    if text.count(".") > 7:  # Increased from 5 to 7
        ai_score += 1
    
    # Generic customer support phrases (only flag if multiple)
    generic_phrases = ["i understand", "i appreciate", "i would be happy", "thank you for"]
    generic_count = sum(1 for phrase in generic_phrases if phrase in lower)
    if generic_count >= 2:  # Only flag if 2+ generic phrases
        ai_score += 2
    
    # Repetitive sentence structure (more lenient)
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sentences) > 3:  # Increased from 2 to 3
        lengths = [len(s.split()) for s in sentences]
        if lengths:
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            if variance < 3:  # More strict variance check (decreased from 5 to 3)
                ai_score += 2
    
    # No contractions when they should be used (more lenient)
    contractions = ["i'm", "i've", "don't", "can't", "won't", "it's", "that's", "you're", "we're"]
    has_contractions = any(cont in lower for cont in contractions)
    if word_count > 15 and not has_contractions:  # Increased from 10 to 15
        ai_score += 1
    
    # Corporate/customer support tone (only flag multiple)
    corporate_words = ["certainly", "absolutely", "furthermore", "moreover", "additionally"]
    corporate_count = sum(1 for cw in corporate_words if cw in lower)
    if corporate_count >= 2:  # Only flag if 2+ corporate words
        ai_score += 2
    
    # Very fast response (likely copy-paste) - more lenient
    if response_time < 1:  # Increased from 2 to 1 second (more strict)
        ai_score += 1
    
    # Too long (overly verbose, AI tendency) - more lenient
    if word_count > 100:  # Increased from 80 to 100
        ai_score += 1
    
    return ai_score


def determine_decision(score: int, ai_score: int) -> str:
    """
    Determine final decision based on scores.
    Difficulty reduced by 30% - more lenient thresholds for approval.
    
    Max score is 50 (10 points per question x 5 questions)
    
    Returns:
        str: "APPROVED", "BORDERLINE", or "NOT ELIGIBLE"
    """
    # Lowered thresholds for easier approval (reduced difficulty by 30%):
    # APPROVED: 17+ (34%) with reasonable AI score (was 24+/48%)
    # BORDERLINE: 13+ (26%) with higher AI tolerance (was 18+/36%)
    if score >= 17 and ai_score <= 8:
        return "APPROVED"
    elif score >= 13 and ai_score <= 10:
        return "BORDERLINE"
    else:
        return "NOT ELIGIBLE"
