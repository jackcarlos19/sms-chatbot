# AI Model Evaluation Report
**Date:** 2026-02-22 19:22:42

This report contains the results of 40 distinct conversational scenarios run against 7 different LLMs.
The goal is to evaluate the reliability, tone, and accuracy of each model's intent classification and response generation.

---

## Model: `openai/gpt-4.1-mini`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.39s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.88s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.91s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.47s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.05s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.46s*

**User:** 2
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 0.94s*

**User:** yes
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.15s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** Could you please specify which service or product you're asking about? That way, I can provide the most accurate pricing information for you.
*State: `awaiting_info` | Latency: 1.4s*

**User:** I want to book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.03s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.89s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.98s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.52s*

**User:** yes
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.78s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.4s*

**User:** frist one
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.86s*

**User:** yep
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.39s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.48s*

**User:** YES!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.0s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.4s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 2.0s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.65s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.03s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.41s*

**User:** 1️⃣
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.9s*

**User:** 👍
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 8:00 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 1.33s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.57s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.95s*


### One-word replies
**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:00 AM
2) Mon Feb 23, 8:30 AM
3) Mon Feb 23, 9:00 AM
4) Mon Feb 23, 9:30 AM
5) Mon Feb 23, 10:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.03s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.92s*

**User:** y
**Bot:** Sorry, that slot was just booked by someone else.
Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.91s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.95s*

**User:** The afternoon one
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.18s*


### FAQ about location
**User:** Where are you located?
**Bot:** Acme Services is located in New York City. How can I assist you with scheduling or other services today?
*State: `idle` | Latency: 1.77s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.01s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.95s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.3s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** Our prices vary depending on the service you need. Could you please specify which service you're interested in? Also, let me know your preferred date and time for the appointment booking.
*State: `awaiting_info` | Latency: 1.28s*


### Selects slot not in list
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.14s*

**User:** 99
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.64s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.08s*

**User:** What is the weather like?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.57s*


### Just saying thanks
**User:** Thank you!
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.34s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.04s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.87s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.05s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.36s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Hi! How can I assist you with your Acme Services scheduling today?
*State: `idle` | Latency: 0.83s*

**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.37s*


### Spells out the number
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.98s*

**User:** I will take the second option
**Bot:** Great, should I book Mon Feb 23, 9:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.08s*

**User:** yes
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 9:00 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 1.14s*


### Uses ordinal indicator
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.02s*

**User:** 1st one
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.71s*


### Uses day name
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.02s*

**User:** The Monday slot
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 2.03s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.06s*

**User:** yes
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.62s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** Here's a short poem about plumbing for you:

Pipes that twist and turn below,
Water's path begins to flow.
Fixing leaks with steady hand,
Plumbers work to meet demand.
From faucets drip to drains that clear,
Silent heroes, always near.
*State: `idle` | Latency: 1.71s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.26s*

**User:** no
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.08s*


### Books then immediately cancels
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.02s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.95s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.82s*

**User:** Actually cancel it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.53s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.1s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** I didn't quite get that. How can I assist you with scheduling or managing your appointments at Acme Services?
*State: `awaiting_info` | Latency: 1.01s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:30 AM
3) Mon Feb 23, 10:00 AM
4) Mon Feb 23, 10:30 AM
5) Mon Feb 23, 11:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.09s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:00 AM
3) Mon Feb 23, 9:30 AM
4) Mon Feb 23, 10:00 AM
5) Mon Feb 23, 10:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.01s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.95s*


### Cancel with typo
**User:** cancek
**Bot:** It seems like you want to cancel something. Could you please specify what you'd like to cancel? For example, an appointment or a service booking.
*State: `awaiting_info` | Latency: 1.04s*

**User:** ys
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.96s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.03s*

**User:** 1
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.01s*


### Politely says no
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.18s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.0s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** I understand you'd like to talk to a real person. While I'm here to assist with scheduling and info, I can help connect you to a representative if needed. How can I assist you today?
*State: `idle` | Latency: 1.21s*

**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:30 AM
3) Mon Feb 23, 10:00 AM
4) Mon Feb 23, 10:30 AM
5) Mon Feb 23, 11:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.96s*


### Asks for a range of slots
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:30 AM
3) Mon Feb 23, 10:00 AM
4) Mon Feb 23, 10:30 AM
5) Mon Feb 23, 11:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.07s*

**User:** What do you have next week?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.66s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:30 AM
3) Mon Feb 23, 10:00 AM
4) Mon Feb 23, 10:30 AM
5) Mon Feb 23, 11:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.95s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.86s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.93s*


### Vague cancel
**User:** I can't make it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.09s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.09s*


### Just a question mark
**User:** ?
**Bot:** Hi! How can I assist you with your Acme Services scheduling today?
*State: `awaiting_info` | Latency: 0.81s*


### Whitespace
**User:**    
**Bot:** Hi! How can I assist you with your Acme Services scheduling today?
*State: `awaiting_info` | Latency: 0.89s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 8:30 AM
2) Mon Feb 23, 9:30 AM
3) Mon Feb 23, 10:00 AM
4) Mon Feb 23, 10:30 AM
5) Mon Feb 23, 11:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.23s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 8:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.9s*

**User:** y
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 8:30 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 1.12s*


## Model: `deepseek/deepseek-v3.2`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 11.23s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 2.08s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 1.38s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.65s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.23s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 6.77s*

**User:** 2
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 7.38s*

**User:** yes
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 2.51s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** Our standard service pricing starts at $49 for basic appointments. Would you like to know pricing for a specific service or schedule a consultation?
*State: `idle` | Latency: 3.34s*

**User:** I want to book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 8.79s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 4.74s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 6.83s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 15.29s*

**User:** yes
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 9.43s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 12.01s*

**User:** frist one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 8.51s*

**User:** yep
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 5.95s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.46s*

**User:** YES!
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 8.42s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 11.99s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 16.87s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 4.16s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 11.52s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 3.83s*

**User:** 1️⃣
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 3.51s*

**User:** 👍
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 2.94s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 3.86s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 9.21s*


### One-word replies
**User:** book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 6.41s*

**User:** 1
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 5.76s*

**User:** y
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 16.21s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 5.65s*

**User:** The afternoon one
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 16.08s*


### FAQ about location
**User:** Where are you located?
**Bot:** I can help you schedule appointments with Acme Services! However, I don't have specific location information available in my system. You might want to check our website or contact customer service directly for location details.
*State: `awaiting_info` | Latency: 13.77s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 14.22s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 19.31s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** No problem. Reply with another slot number when ready.
*State: `showing_slots` | Latency: 2.81s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** I can help you book an appointment! For pricing details, I'll need to know which service you're interested in. Could you tell me what type of appointment you'd like to schedule?
*State: `awaiting_info` | Latency: 6.13s*


### Selects slot not in list
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 4.69s*

**User:** 99
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 5.44s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 5.38s*

**User:** What is the weather like?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 4.69s*


### Just saying thanks
**User:** Thank you!
**Bot:** You're welcome! Is there anything else I can help you with today?
*State: `idle` | Latency: 5.55s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 4.06s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 17.43s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 23.39s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 11.91s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 2.47s*

**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 5.98s*


### Spells out the number
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 16.62s*

**User:** I will take the second option
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 5.49s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 4.83s*


### Uses ordinal indicator
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 5.56s*

**User:** 1st one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 18.42s*


### Uses day name
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 7.36s*

**User:** The Monday slot
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 14.7s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 6.25s*

**User:** yes
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 9.52s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 7.21s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 21.58s*

**User:** no
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 4.29s*


### Books then immediately cancels
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 4.17s*

**User:** 1
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 5.65s*

**User:** yes
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 13.45s*

**User:** Actually cancel it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 14.33s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.67s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** I didn't understand that. Could you please tell me what you'd like to do? You can book, cancel, reschedule, or ask about appointments.
*State: `idle` | Latency: 6.18s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 10.28s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 3.66s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 10.22s*


### Cancel with typo
**User:** cancek
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 4.59s*

**User:** ys
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 6.43s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 3.74s*

**User:** 1
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 6.17s*


### Politely says no
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.37s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 5.97s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** I'm an automated assistant for Acme Services. For immediate human assistance, please call our customer service line at 1-800-555-ACME during business hours (9am-5pm EST).
*State: `idle` | Latency: 7.19s*

**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 10.47s*


### Asks for a range of slots
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 11.86s*

**User:** What do you have next week?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 19.95s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 4.71s*

**User:** 1
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.0s*

**User:** yes
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 22.41s*


### Vague cancel
**User:** I can't make it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.11s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 5.1s*


### Just a question mark
**User:** ?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 4.79s*


### Whitespace
**User:**    
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `idle` | Latency: 3.23s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 8.93s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 6.63s*

**User:** y
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 11.07s*


## Model: `google/gemini-2.5-flash`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Hello! I can help with that. What day and time are you looking for?
*State: `awaiting_info` | Latency: 1.09s*

**User:** 1
**Bot:** What day and time are you looking for?
*State: `awaiting_info` | Latency: 1.17s*

**User:** yes
**Bot:** I'm sorry, I don't understand. Could you please tell me what day and time you are looking for?
*State: `awaiting_info` | Latency: 0.92s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.25s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.75s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.24s*

**User:** 2
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.86s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.65s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** I can help with that. What service are you interested in?
*State: `awaiting_info` | Latency: 1.15s*

**User:** I want to book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.64s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.98s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.88s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.4s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.77s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.05s*

**User:** frist one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.64s*

**User:** yep
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.78s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.85s*

**User:** YES!
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `idle` | Latency: 0.64s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.4s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.54s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.25s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `idle` | Latency: 0.93s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Hello! I can help with scheduling. What date are you looking for?
*State: `awaiting_info` | Latency: 1.18s*

**User:** 1️⃣
**Bot:** I'm sorry, I can't understand "1️⃣". Could you please tell me the date you are looking for?
*State: `awaiting_info` | Latency: 0.9s*

**User:** 👍
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.69s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 11.08s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.88s*


### One-word replies
**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.75s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.89s*

**User:** y
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.85s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.03s*

**User:** The afternoon one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.48s*


### FAQ about location
**User:** Where are you located?
**Bot:** I'm a virtual assistant, so I don't have a physical location. How can I help you today?
*State: `idle` | Latency: 0.98s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.7s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.73s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.73s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.02s*


### Selects slot not in list
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.7s*

**User:** 99
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.89s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.77s*

**User:** What is the weather like?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.7s*


### Just saying thanks
**User:** Thank you!
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.61s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.73s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.77s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.01s*

**User:** 1
**Bot:** I'm sorry, I can only understand if you want to book, reschedule, cancel, or ask a question. Could you please clarify?
*State: `idle` | Latency: 1.02s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Hello! How can I help you today?
*State: `idle` | Latency: 0.75s*

**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.93s*


### Spells out the number
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.84s*

**User:** I will take the second option
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.76s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.19s*


### Uses ordinal indicator
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.83s*

**User:** 1st one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.55s*


### Uses day name
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.62s*

**User:** The Monday slot
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.38s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** What time on the 23rd?
*State: `awaiting_info` | Latency: 0.54s*

**User:** yes
**Bot:** I can help you book an appointment for February 23rd. What time works best for you?
*State: `awaiting_info` | Latency: 0.87s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** I'm sorry, I'm not able to write poems. I can help with scheduling SMS messages for Acme Services. What can I do for you?
*State: `idle` | Latency: 0.87s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.7s*

**User:** no
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.81s*


### Books then immediately cancels
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.71s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.69s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.84s*

**User:** Actually cancel it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.53s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.81s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** I'm sorry, I don't understand. Can you please rephrase your request?
*State: `idle` | Latency: 0.63s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.88s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 0.79s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.21s*


### Cancel with typo
**User:** cancek
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.54s*

**User:** ys
**Bot:** I'm sorry, I don't understand. Could you please clarify?
*State: `idle` | Latency: 0.63s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 0.89s*

**User:** 1
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.74s*


### Politely says no
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.67s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.69s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** I am an automated assistant, but I can help you schedule, cancel, or reschedule appointments. What can I help you with?
*State: `idle` | Latency: 1.25s*

**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.0s*


### Asks for a range of slots
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.62s*

**User:** What do you have next week?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.14s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.82s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.98s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.18s*


### Vague cancel
**User:** I can't make it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.98s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.67s*


### Just a question mark
**User:** ?
**Bot:** I'm sorry, I don't understand. Can you please rephrase your question?
*State: `idle` | Latency: 0.65s*


### Whitespace
**User:**    
**Bot:** Hello! I'm the Acme Services scheduling assistant. How can I help you today?
*State: `idle` | Latency: 0.64s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 11.04s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.4s*

**User:** y
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 0.76s*


## Model: `openai/gpt-4o-mini`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.98s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.13s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.17s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.85s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.78s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 2.14s*

**User:** 2
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.15s*

**User:** yes
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.35s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** Could you please specify what service you are inquiring about? This will help me provide you with accurate pricing information.
*State: `awaiting_info` | Latency: 1.68s*

**User:** I want to book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.76s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.22s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.06s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.29s*

**User:** yes
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.05s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.99s*

**User:** frist one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.31s*

**User:** yep
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.03s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.62s*

**User:** YES!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.81s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.66s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.67s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.22s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.01s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Hi there! How can I assist you with scheduling today?
*State: `awaiting_info` | Latency: 2.11s*

**User:** 1️⃣
**Bot:** Could you please provide more details about what you need help with regarding scheduling?
*State: `awaiting_info` | Latency: 1.68s*

**User:** 👍
**Bot:** Great! How can I assist you with scheduling?
*State: `awaiting_info` | Latency: 1.17s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Hello! I'm here to help you schedule an appointment. Could you please provide me with your preferred date and time, or any specific services you need?
*State: `awaiting_info` | Latency: 1.83s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.4s*


### One-word replies
**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.32s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.26s*

**User:** y
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.01s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.61s*

**User:** The afternoon one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.8s*


### FAQ about location
**User:** Where are you located?
**Bot:** Acme Services operates in various locations. If you need specific information about a location or service, please let me know!
*State: `idle` | Latency: 1.52s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.16s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.3s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** No problem. Reply with another slot number when ready.
*State: `showing_slots` | Latency: 0.92s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** I can help with booking an appointment! However, I don't have access to pricing information. Please check our website or contact customer service for details on prices.
*State: `awaiting_info` | Latency: 1.82s*


### Selects slot not in list
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.61s*

**User:** 99
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.98s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.48s*

**User:** What is the weather like?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.7s*


### Just saying thanks
**User:** Thank you!
**Bot:** You're welcome! How can I assist you today?
*State: `idle` | Latency: 0.91s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** I can help you schedule an appointment! What type of service do you need, and do you have a preferred date and time?
*State: `awaiting_info` | Latency: 1.58s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.06s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.25s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.34s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Hello! How can I assist you today?
*State: `idle` | Latency: 0.82s*

**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.26s*


### Spells out the number
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.65s*

**User:** I will take the second option
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.45s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.06s*


### Uses ordinal indicator
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.24s*

**User:** 1st one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.14s*


### Uses day name
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.22s*

**User:** The Monday slot
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 3.09s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** Could you please specify the time you would like for your appointment on the 23rd?
*State: `awaiting_info` | Latency: 1.29s*

**User:** yes
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.35s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** Here's a fun poem about plumbing:

In the walls where pipes do flow,
A hidden world, a tale to show.
With wrenches, tools, and steady hands,
Plumbers work to meet demands.

Water dances, drains away,
In every home, it finds its way.
From leaky taps to toilets' flush,
They fix it all, no need to rush.

So here's to those who toil and sweat,
In every drip, a job well met.
With every pipe and every seam,
They keep our lives running like a dream!
*State: `idle` | Latency: 4.44s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.23s*

**User:** no
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.52s*


### Books then immediately cancels
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.17s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.11s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.1s*

**User:** Actually cancel it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 2.17s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.85s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.05s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.27s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.26s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.98s*


### Cancel with typo
**User:** cancek
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.24s*

**User:** ys
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.27s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.25s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.12s*


### Politely says no
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.99s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.73s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** I'm here to assist you with scheduling! If you need to speak with a real person, please call our customer service line. How can I help you today?
*State: `idle` | Latency: 1.89s*

**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.23s*


### Asks for a range of slots
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.86s*

**User:** What do you have next week?
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 3.33s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.95s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.21s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.01s*


### Vague cancel
**User:** I can't make it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.13s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.39s*


### Just a question mark
**User:** ?
**Bot:** How can I assist you today?
*State: `idle` | Latency: 0.88s*


### Whitespace
**User:**    
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `idle` | Latency: 0.93s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.07s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.05s*

**User:** y
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.14s*


## Model: `anthropic/claude-haiku-4-5`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Great! I'd be happy to help you book an appointment with Acme Services. To get started, could you please tell me: 1) What service do you need? 2) What date works best for you? 3) Do you have a preferred time?
*State: `awaiting_info` | Latency: 3.12s*

**User:** 1
**Bot:** I'm not sure what you mean by "1". Could you tell me which service you need? For example: plumbing, electrical, HVAC, or general maintenance?
*State: `awaiting_info` | Latency: 1.5s*

**User:** yes
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 4.05s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.83s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 2.5s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.94s*

**User:** 2
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 2.11s*

**User:** yes
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.42s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** Great question! I don't have specific pricing info in our system. Could you tell me which service you're interested in? Once I know, I can help you schedule or get you more details!
*State: `awaiting_info` | Latency: 3.21s*

**User:** I want to book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.93s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.64s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.52s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 2.34s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.65s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 3.42s*

**User:** frist one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.87s*

**User:** yep
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 3.3s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 2.49s*

**User:** YES!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.67s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.83s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 3.06s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 3.28s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 2.35s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Hi! 👋 I'd be happy to help you schedule an appointment with Acme Services! 📅 

Could you tell me:
• What service do you need?
• What date/time works best for you?

Let's get you booked! 😊
*State: `awaiting_info` | Latency: 3.26s*

**User:** 1️⃣
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 2.33s*

**User:** 👍
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 2.21s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Hi there! Thanks for reaching out! 😊 I'd be happy to help you schedule an appointment with Acme Services. To get you booked, could you please let me know: 1) What service do you need? 2) What dates/times work best for you? 3) Any other details I should know?
*State: `awaiting_info` | Latency: 2.05s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 2.35s*


### One-word replies
**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.31s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.54s*

**User:** y
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 3.67s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Great! I'd be happy to help you book an appointment with Acme Services. To get started, could you please tell me: 1) What service do you need? 2) What date works best for you? 3) What time would you prefer?
*State: `awaiting_info` | Latency: 3.05s*

**User:** The afternoon one
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 2.19s*


### FAQ about location
**User:** Where are you located?
**Bot:** I'm Acme Services' SMS scheduling assistant! I'm here to help you book, reschedule, or cancel appointments via text. I don't have a physical location—I'm available 24/7 to assist with your scheduling needs. How can I help you today?
*State: `idle` | Latency: 1.39s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.92s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.57s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.7s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** I'd be happy to help! For pricing details, please visit our website or contact our main office. To book an appointment, I'll need a few details: What service do you need, and what date/time works best for you?
*State: `awaiting_info` | Latency: 2.64s*


### Selects slot not in list
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.87s*

**User:** 99
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.38s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.61s*

**User:** What is the weather like?
**Bot:** I'm a scheduling assistant for Acme Services and can't help with weather info. I'm here to help you book, reschedule, or cancel appointments. What can I do for you?
*State: `idle` | Latency: 1.88s*


### Just saying thanks
**User:** Thank you!
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.58s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.77s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.63s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.33s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.36s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.31s*

**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.39s*


### Spells out the number
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.89s*

**User:** I will take the second option
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 2.79s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.29s*


### Uses ordinal indicator
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.49s*

**User:** 1st one
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.48s*


### Uses day name
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 3.39s*

**User:** The Monday slot
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.65s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** Great! I can help you book an appointment on February 23rd. To find the perfect time slot, could you let me know what time works best for you?
*State: `awaiting_info` | Latency: 1.58s*

**User:** yes
**Bot:** I'd be happy to book your appointment for Feb 23rd! What time would work best for you? (e.g., 9am, 2pm, etc.)
*State: `awaiting_info` | Latency: 2.15s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** Here's a poem about plumbing for you:

**Pipes and Purpose**

Water flows through hidden veins,
Through copper, PVC, and drains,
A plumber's hands know every bend,
Where leaks begin and repairs end.

Beneath the walls and under floors,
A network serves our daily chores,
From kitchen sink to shower's spray,
These pipes work hard both night and day.

With wrench in hand and steady skill,
They fix what's broken, bend their will,
To keep our water running clear,
A trade we nee...
*State: `idle` | Latency: 3.03s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.26s*

**User:** no
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 2.29s*


### Books then immediately cancels
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.59s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.36s*

**User:** yes
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.56s*

**User:** Actually cancel it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.43s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.29s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 2.3s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.17s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Bonjour! Je serais ravi de vous aider à prendre rendez-vous. Pouvez-vous me dire quel service vous intéresse et votre date/heure préférée?
*State: `awaiting_info` | Latency: 1.38s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.27s*


### Cancel with typo
**User:** cancek
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.31s*

**User:** ys
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.66s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 2.39s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.6s*


### Politely says no
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.58s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.23s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** I'm an SMS assistant for Acme Services. For immediate help from a real person, please call our customer service team during business hours or visit acmeservices.com. How can I help you schedule a service today?
*State: `idle` | Latency: 1.44s*

**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.46s*


### Asks for a range of slots
**User:** Book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.45s*

**User:** What do you have next week?
**Bot:** I'd be happy to help! To show you available slots for next week (Feb 24 - Mar 2), I need a bit more info: What service do you need, and what days/times work best for you?
*State: `awaiting_info` | Latency: 2.62s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 2.11s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 3.72s*

**User:** yes
**Bot:** Please reply YES to confirm this slot or NO to choose another.
*State: `confirming_booking` | Latency: 1.71s*


### Vague cancel
**User:** I can't make it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.5s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.25s*


### Just a question mark
**User:** ?
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 2.14s*


### Whitespace
**User:**    
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 1.0s*

**User:** book
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.4s*

**User:** 1
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.7s*

**User:** y
**Bot:** Could you clarify if you want to book, reschedule, cancel, or ask a question?
*State: `awaiting_info` | Latency: 1.41s*


## Model: `openai/gpt-4o`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.18s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.82s*

**User:** yes
**Bot:** Sorry, that slot was just booked by someone else.
Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.83s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 2.07s*

**User:** yes
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.26s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.19s*

**User:** 2
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 0.7s*

**User:** yes
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 2.09s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** Could you please specify what service or product you're inquiring about?
*State: `awaiting_info` | Latency: 1.26s*

**User:** I want to book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.07s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.9s*

**User:** yes
**Bot:** Sorry, that slot was just booked by someone else.
Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.59s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.11s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.7s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.19s*

**User:** frist one
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.46s*

**User:** yep
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 9:30 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 0.89s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.82s*

**User:** YES!
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.11s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.35s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.6s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.2s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.61s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Hi there! How can I assist you with scheduling?
*State: `idle` | Latency: 0.94s*

**User:** 1️⃣
**Bot:** Could you please provide more details about what you need help with?
*State: `awaiting_info` | Latency: 0.68s*

**User:** 👍
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.3s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.73s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.85s*


### One-word replies
**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 9:30 AM
2) Mon Feb 23, 10:00 AM
3) Mon Feb 23, 10:30 AM
4) Mon Feb 23, 11:00 AM
5) Mon Feb 23, 11:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.8s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 9:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.62s*

**User:** y
**Bot:** Sorry, that slot was just booked by someone else.
Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.75s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.89s*

**User:** The afternoon one
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.35s*


### FAQ about location
**User:** Where are you located?
**Bot:** Acme Services is located in New York City, NY.
*State: `idle` | Latency: 1.0s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.85s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.9s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** No problem. Reply with another slot number when ready.
*State: `showing_slots` | Latency: 1.88s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** I can help with booking an appointment. For pricing details, please visit our website or contact our support team. Let me know your preferred date and time for the appointment.
*State: `awaiting_info` | Latency: 0.93s*


### Selects slot not in list
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.26s*

**User:** 99
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.93s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.74s*

**User:** What is the weather like?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.2s*


### Just saying thanks
**User:** Thank you!
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.83s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.85s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.86s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.07s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.03s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Hello! How can I assist you today?
*State: `idle` | Latency: 0.66s*

**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.12s*


### Spells out the number
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.09s*

**User:** I will take the second option
**Bot:** Great, should I book Mon Feb 23, 10:30 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.07s*

**User:** yes
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 10:30 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 0.92s*


### Uses ordinal indicator
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.22s*

**User:** 1st one
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.63s*


### Uses day name
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.85s*

**User:** The Monday slot
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.67s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.01s*

**User:** yes
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.44s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** Would you like a poem about plumbing?
*State: `idle` | Latency: 0.72s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.06s*

**User:** no
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.95s*


### Books then immediately cancels
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.96s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.72s*

**User:** yes
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 10:00 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 0.76s*

**User:** Actually cancel it
**Bot:** I found You're all set! Your appointment is confirmed for Mon Feb 23 at 10:00 AM. Reply CANCEL to cancel or RESCHEDULE to change.. Reply YES to confirm cancellation or NO to keep it.
*State: `confirming_cancel` | Latency: 0.66s*

**User:** yes
**Bot:** OK, your appointment is still on the books.
*State: `idle` | Latency: 1.08s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** I'm sorry, I didn't understand your message. Could you please provide more details or clarify your request?
*State: `idle` | Latency: 0.8s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 11:00 AM
3) Mon Feb 23, 11:30 AM
4) Tue Feb 24, 4:00 AM
5) Tue Feb 24, 4:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.94s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Here are some available times:
1) Mon Feb 23, 10:00 AM
2) Mon Feb 23, 10:30 AM
3) Mon Feb 23, 11:00 AM
4) Mon Feb 23, 11:30 AM
5) Tue Feb 24, 4:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.82s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 10:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 0.89s*


### Cancel with typo
**User:** cancek
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.89s*

**User:** ys
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.06s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.32s*

**User:** 1
**Bot:** I couldn't find an active appointment to reschedule.
*State: `idle` | Latency: 1.03s*


### Politely says no
**User:** Cancel my appointment
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 0.83s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 0.85s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** Would you like to speak with a customer service representative?
*State: `idle` | Latency: 0.7s*

**User:** Book an appointment
**Bot:** Here are some available times:
1) Mon Feb 23, 11:00 AM
2) Mon Feb 23, 11:30 AM
3) Tue Feb 24, 4:00 AM
4) Tue Feb 24, 4:30 AM
5) Tue Feb 24, 5:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.8s*


### Asks for a range of slots
**User:** Book
**Bot:** Here are some available times:
1) Mon Feb 23, 11:00 AM
2) Mon Feb 23, 11:30 AM
3) Tue Feb 24, 4:00 AM
4) Tue Feb 24, 4:30 AM
5) Tue Feb 24, 5:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 1.06s*

**User:** What do you have next week?
**Bot:** I didn't catch that slot. Reply with the number from the list.
*State: `showing_slots` | Latency: 1.0s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Here are some available times:
1) Mon Feb 23, 11:00 AM
2) Mon Feb 23, 11:30 AM
3) Tue Feb 24, 4:00 AM
4) Tue Feb 24, 4:30 AM
5) Tue Feb 24, 5:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.68s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 11:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.33s*

**User:** yes
**Bot:** You're all set! Your appointment is confirmed for Mon Feb 23 at 11:00 AM. Reply CANCEL to cancel or RESCHEDULE to change.
*State: `idle` | Latency: 1.04s*


### Vague cancel
**User:** I can't make it
**Bot:** I couldn't find an active appointment to cancel.
*State: `idle` | Latency: 1.25s*

**User:** yes
**Bot:** I can help you book, reschedule, or cancel. What would you like to do?
*State: `idle` | Latency: 1.14s*


### Just a question mark
**User:** ?
**Bot:** Could you please provide more details about your question?
*State: `awaiting_info` | Latency: 1.19s*


### Whitespace
**User:**    
**Bot:** I'm here to help with scheduling or managing appointments. Could you please provide more details or specify what you need assistance with?
*State: `awaiting_info` | Latency: 1.18s*

**User:** book
**Bot:** Here are some available times:
1) Mon Feb 23, 11:00 AM
2) Mon Feb 23, 11:30 AM
3) Tue Feb 24, 4:00 AM
4) Tue Feb 24, 4:30 AM
5) Tue Feb 24, 5:00 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.93s*

**User:** 1
**Bot:** Great, should I book Mon Feb 23, 11:00 AM? Reply YES to confirm or NO to pick another time.
*State: `confirming_booking` | Latency: 1.07s*

**User:** y
**Bot:** Sorry, that slot was just booked by someone else.
Here are some available times:
1) Mon Feb 23, 11:30 AM
2) Tue Feb 24, 4:00 AM
3) Tue Feb 24, 4:30 AM
4) Tue Feb 24, 5:00 AM
5) Tue Feb 24, 5:30 AM
Reply with a number to book.
*State: `showing_slots` | Latency: 0.83s*


## Model: `anthropic/claude-sonnet-4-20250514`

### Standard multi-turn booking
**User:** Hi, I need an appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.38s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Standard cancel
**User:** Cancel my appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.44s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*


### Standard reschedule
**User:** I need to reschedule
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.39s*

**User:** 2
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*


### FAQ about pricing
**User:** How much does it cost?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.36s*

**User:** I want to book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*


### Directly requests a specific slot index
**User:** Book slot 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.4s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Heavy typos
**User:** i wnt to bkoo an apntment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.36s*

**User:** frist one
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*

**User:** yep
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*


### Angry/hostile customer
**User:** Your service is terrible, cancel my damn appointment now!
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.43s*

**User:** YES!
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Starts booking, changes to cancel
**User:** Book an appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.37s*

**User:** Wait, no, cancel my current appointment instead.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Non-english (Spanish)
**User:** Hola, quiero una cita
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.38s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*


### Emoji heavy
**User:** 👋 I need 📅
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.4s*

**User:** 1️⃣
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** 👍
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Extremely verbose
**User:** Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** I think the first option you provided would be absolutely perfect for my schedule. Thank you!
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*


### One-word replies
**User:** book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.11s*

**User:** y
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*


### Ambiguous slot selection
**User:** I want an appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** The afternoon one
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*


### FAQ about location
**User:** Where are you located?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*


### Rude refusal of confirmation
**User:** Book an appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** NO I SAID I WANT A DIFFERENT ONE
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Multiple intents in one message
**User:** Can you tell me your prices and also book an appointment for me?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Selects slot not in list
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*

**User:** 99
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*


### Ignores bot prompt completely
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*

**User:** What is the weather like?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*


### Just saying thanks
**User:** Thank you!
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*


### All caps shouting
**User:** I NEED AN APPOINTMENT RIGHT NOW
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Sarcastic response
**User:** Oh great, a robot. Book me an appointment I guess.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.11s*


### Simulates long delay (just typical turn)
**User:** Hey
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*


### Spells out the number
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*

**User:** I will take the second option
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Uses ordinal indicator
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*

**User:** 1st one
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Uses day name
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*

**User:** The Monday slot
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Uses specific date
**User:** I need an appointment on the 23rd
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.13s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*


### Treating bot like ChatGPT
**User:** Write me a poem about plumbing.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*


### Says no to confirmation
**User:** Cancel appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.11s*

**User:** no
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Books then immediately cancels
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.11s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** Actually cancel it
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.04s*


### Gibberish text
**User:** asdfqwerzxcv
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.1s*

**User:** book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*


### French
**User:** Je voudrais prendre rendez-vous
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*


### Cancel with typo
**User:** cancek
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*

**User:** ys
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*


### Wants to reschedule but has no appointment (treated as book)
**User:** Reschedule
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Politely says no
**User:** Cancel my appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.07s*

**User:** Actually I changed my mind, don't cancel it.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Wants to speak to a human
**User:** Can I talk to a real person?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*

**User:** Book an appointment
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*


### Asks for a range of slots
**User:** Book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*

**User:** What do you have next week?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.09s*


### Vulgar language
**User:** This f***ing app sucks, just book me.
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.04s*


### Vague cancel
**User:** I can't make it
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*

**User:** yes
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.05s*


### Just a question mark
**User:** ?
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.06s*


### Whitespace
**User:**    
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.08s*

**User:** book
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.04s*

**User:** 1
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.04s*

**User:** y
**Bot:** Sorry, having a brief issue. Please try again in a moment.
*State: `idle` | Latency: 0.04s*
