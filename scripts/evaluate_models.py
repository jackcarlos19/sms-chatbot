#!/usr/bin/env python3
import os
import re
import json
import time
import uuid
import httpx
import asyncio
import subprocess
from datetime import datetime

MODELS = [
    "openai/gpt-4.1-mini",
    "deepseek/deepseek-v3.2",
    "google/gemini-2.5-flash",
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4-5",
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4-20250514"
]

SCENARIOS = [
    {"id": "01_standard_booking", "description": "Standard multi-turn booking", "messages": ["Hi, I need an appointment", "1", "yes"]},
    {"id": "02_cancel", "description": "Standard cancel", "messages": ["Cancel my appointment", "yes"]},
    {"id": "03_reschedule", "description": "Standard reschedule", "messages": ["I need to reschedule", "2", "yes"]},
    {"id": "04_faq_pricing", "description": "FAQ about pricing", "messages": ["How much does it cost?", "I want to book", "1", "yes"]},
    {"id": "05_direct_book", "description": "Directly requests a specific slot index", "messages": ["Book slot 1", "yes"]},
    {"id": "06_typos_heavy", "description": "Heavy typos", "messages": ["i wnt to bkoo an apntment", "frist one", "yep"]},
    {"id": "07_angry_customer", "description": "Angry/hostile customer", "messages": ["Your service is terrible, cancel my damn appointment now!", "YES!"]},
    {"id": "08_switch_intent_book_to_cancel", "description": "Starts booking, changes to cancel", "messages": ["Book an appointment", "Wait, no, cancel my current appointment instead."]},
    {"id": "09_spanish", "description": "Non-english (Spanish)", "messages": ["Hola, quiero una cita", "1"]},
    {"id": "10_emojis_only", "description": "Emoji heavy", "messages": ["👋 I need 📅", "1️⃣", "👍"]},
    {"id": "11_verbose", "description": "Extremely verbose", "messages": ["Hello there! I hope you are having a wonderful day. I was wondering if it might be possible for me to schedule an appointment with your team sometime soon?", "I think the first option you provided would be absolutely perfect for my schedule. Thank you!"]},
    {"id": "12_short", "description": "One-word replies", "messages": ["book", "1", "y"]},
    {"id": "13_ambiguous_time", "description": "Ambiguous slot selection", "messages": ["I want an appointment", "The afternoon one"]},
    {"id": "14_faq_location", "description": "FAQ about location", "messages": ["Where are you located?"]},
    {"id": "15_rude_refusal", "description": "Rude refusal of confirmation", "messages": ["Book an appointment", "1", "NO I SAID I WANT A DIFFERENT ONE"]},
    {"id": "16_multiple_intents", "description": "Multiple intents in one message", "messages": ["Can you tell me your prices and also book an appointment for me?"]},
    {"id": "17_out_of_bounds_slot", "description": "Selects slot not in list", "messages": ["Book", "99"]},
    {"id": "18_ignore_bot", "description": "Ignores bot prompt completely", "messages": ["Book", "What is the weather like?"]},
    {"id": "19_thanks_only", "description": "Just saying thanks", "messages": ["Thank you!"]},
    {"id": "20_all_caps", "description": "All caps shouting", "messages": ["I NEED AN APPOINTMENT RIGHT NOW", "1"]},
    {"id": "21_sarcasm", "description": "Sarcastic response", "messages": ["Oh great, a robot. Book me an appointment I guess.", "1"]},
    {"id": "22_long_delay", "description": "Simulates long delay (just typical turn)", "messages": ["Hey", "Book"]},
    {"id": "23_number_word", "description": "Spells out the number", "messages": ["Book", "I will take the second option", "yes"]},
    {"id": "24_ordinal", "description": "Uses ordinal indicator", "messages": ["Book", "1st one"]},
    {"id": "25_day_name", "description": "Uses day name", "messages": ["Book", "The Monday slot"]},
    {"id": "26_date_specific", "description": "Uses specific date", "messages": ["I need an appointment on the 23rd", "yes"]},
    {"id": "27_unrelated_bot", "description": "Treating bot like ChatGPT", "messages": ["Write me a poem about plumbing."]},
    {"id": "28_confirm_no", "description": "Says no to confirmation", "messages": ["Cancel appointment", "no"]},
    {"id": "29_book_then_cancel", "description": "Books then immediately cancels", "messages": ["Book", "1", "yes", "Actually cancel it", "yes"]},
    {"id": "30_gibberish", "description": "Gibberish text", "messages": ["asdfqwerzxcv", "book"]},
    {"id": "31_french", "description": "French", "messages": ["Je voudrais prendre rendez-vous", "1"]},
    {"id": "32_cancel_typo", "description": "Cancel with typo", "messages": ["cancek", "ys"]},
    {"id": "33_reschedule_to_book", "description": "Wants to reschedule but has no appointment (treated as book)", "messages": ["Reschedule", "1"]},
    {"id": "34_polite_refusal", "description": "Politely says no", "messages": ["Cancel my appointment", "Actually I changed my mind, don't cancel it."]},
    {"id": "35_asking_for_human", "description": "Wants to speak to a human", "messages": ["Can I talk to a real person?", "Book an appointment"]},
    {"id": "36_slot_range", "description": "Asks for a range of slots", "messages": ["Book", "What do you have next week?"]},
    {"id": "37_vulgar", "description": "Vulgar language", "messages": ["This f***ing app sucks, just book me.", "1", "yes"]},
    {"id": "38_partial_cancel", "description": "Vague cancel", "messages": ["I can't make it", "yes"]},
    {"id": "39_question_mark", "description": "Just a question mark", "messages": ["?"]},
    {"id": "40_empty_string_sim", "description": "Whitespace", "messages": ["   ", "book", "1", "y"]}
]

def update_env_model(model_name: str):
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    with open(env_path, "r") as f:
        content = f.read()
    
    if "AI_MODEL=" in content:
        content = re.sub(r"AI_MODEL=.*", f"AI_MODEL={model_name}", content)
    else:
        content += f"\nAI_MODEL={model_name}\n"
        
    with open(env_path, "w") as f:
        f.write(content)

async def wait_for_health():
    async with httpx.AsyncClient() as client:
        for _ in range(30):
            try:
                r = await client.get("http://localhost:8000/api/health", headers={"X-API-Key": "change-this-admin-key"})
                if r.status_code == 200 and r.json().get("status") == "green":
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
    return False

def restart_docker():
    cwd = os.path.dirname(os.path.dirname(__file__))
    subprocess.run(["docker", "compose", "rm", "-sf", "app", "worker"], cwd=cwd, check=True)
    subprocess.run(["docker", "compose", "up", "-d", "app", "worker"], cwd=cwd, check=True)

async def simulate_conversation(client: httpx.AsyncClient, phone: str, scenario: dict, sem: asyncio.Semaphore):
    async with sem:
        results = []
        current_state = "idle"
        
        for msg in scenario["messages"]:
            start_time = time.monotonic()
            try:
                r = await client.post(
                    "http://localhost:8000/api/simulate/inbound",
                    json={"phone_number": phone, "message": msg},
                    headers={"X-API-Key": "change-this-admin-key"},
                    timeout=30.0
                )
                r.raise_for_status()
                data = r.json()
                latency = time.monotonic() - start_time
                
                results.append({
                    "user": msg,
                    "bot": data.get("responses", []),
                    "state": data.get("conversation_state"),
                    "latency_sec": round(latency, 2)
                })
                current_state = data.get("conversation_state")
                
            except Exception as e:
                results.append({
                    "user": msg,
                    "bot": [f"ERROR: {str(e)}"],
                    "state": current_state,
                    "latency_sec": round(time.monotonic() - start_time, 2)
                })
                
        return scenario, results

async def run_evaluation():
    report_lines = [
        "# AI Model Evaluation Report",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\nThis report contains the results of 40 distinct conversational scenarios run against 7 different LLMs.",
        "The goal is to evaluate the reliability, tone, and accuracy of each model's intent classification and response generation.",
        "\n---"
    ]
    
    # Run 10 scenarios concurrently to speed up the process while avoiding rate limits
    sem = asyncio.Semaphore(10)
    
    for model in MODELS:
        print(f"\n==========================================")
        print(f"Testing model: {model}")
        print(f"==========================================")
        
        update_env_model(model)
        restart_docker()
        
        print("Waiting for health...")
        is_healthy = await wait_for_health()
        if not is_healthy:
            print("Failed to reach healthy state, skipping model.")
            report_lines.append(f"\n## Model: {model}")
            report_lines.append("❌ Failed to initialize (Health check timeout)")
            continue
            
        report_lines.append(f"\n## Model: `{model}`")
        
        async with httpx.AsyncClient() as client:
            print("Running 40 scenarios concurrently...")
            tasks = []
            for scenario in SCENARIOS:
                phone = f"+1555{str(uuid.uuid4().int)[:7]}"
                tasks.append(simulate_conversation(client, phone, scenario, sem))
                
            completed_scenarios = await asyncio.gather(*tasks)
            
            # Sort back by original scenario id to keep report ordered
            completed_scenarios.sort(key=lambda x: x[0]["id"])
            
            for scenario, conv_results in completed_scenarios:
                report_lines.append(f"\n### {scenario['description']}")
                for turn in conv_results:
                    report_lines.append(f"**User:** {turn['user']}")
                    for br in turn['bot']:
                        report_lines.append(f"**Bot:** {br}")
                    report_lines.append(f"*State: `{turn['state']}` | Latency: {turn['latency_sec']}s*")
                    report_lines.append("")
        
        print(f"Finished {model}.")
                
    report_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model-evaluation-results.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
        
    print(f"\nEvaluation complete! Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
