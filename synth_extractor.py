"""
synth_extractor.py

small script to pull structured synthesis params out of nanomaterial papers using
an LLM. mostly wanted to try out the "ask llm for json, check it's actually what
I asked for" pattern instead of just trusting whatever comes back.

uses groq's api to call llama 3.3 70b (free, fast, no cc needed for the key).
swapping to openai/anthropic later would just mean changing the client + model
name, the rest of the logic doesn't care.

setup:
    pip install groq
    export GROQ_API_KEY="gsk_..."   (free key, no cc needed - console.groq.com)
    python synth_extractor.py
"""

import json
import os
import sys

from groq import Groq

# fields I expect back from the model for every sample. keeping this as a plain
# list instead of some schema class - it's just here so I can sanity check the
# json actually has what I asked for before I trust it.
REQUIRED_FIELDS = [
    "material", "method", "reagents", "temperature_C", "time_hours",
    "solvent", "atmosphere", "yield_or_purity", "special_conditions",
]

# pulled a few real synthesis paragraphs from open-access gold nanocluster /
# nanoparticle papers to use as actual test input instead of making fake text up.
# only using short excerpts as input here, not reposting full papers anywhere.
DEMO_TEXTS = [
    {
        "id": "AuNC_glutathione",
        "ref": "Jin et al. (open access) - Au25(SG)18 synthesis",
        "text": (
            "A solution of HAuCl4·3H2O (0.1 mmol) and glutathione (0.3 mmol) in "
            "methanol/water (1:1 v/v, 10 mL) was stirred for 10 min at 0 °C under N2. "
            "NaBH4 (0.5 mL of a freshly prepared 0.2 M aqueous solution) was added "
            "rapidly under vigorous stirring.  The mixture was allowed to react for 24 h "
            "at room temperature (25 °C).  The resulting dark-brown solution was "
            "centrifuged and the precipitate was washed with methanol three times."
        ),
    },
    {
        "id": "AuNP_citrate",
        "ref": "Turkevich / Frens method (classic, public domain)",
        "text": (
            "Gold nanoparticles were synthesised by heating 100 mL of 1 mM HAuCl4 "
            "solution to 100 °C with vigorous stirring.  A 10 mL aliquot of 38.8 mM "
            "sodium citrate was then added rapidly.  The solution colour changed from "
            "yellow to colourless to dark-blue and finally to wine-red within 5 min, "
            "indicating nanoparticle formation.  Stirring continued for 15 min before "
            "cooling to room temperature."
        ),
    },
    {
        "id": "AuNC_BSA",
        "ref": "Xie et al. 2009 JACS (open excerpt)",
        "text": (
            "BSA-encapsulated gold nanoclusters were prepared by mixing HAuCl4 (5 mL, "
            "10 mM) with BSA solution (5 mL, 50 mg mL−1) at 37 °C under gentle "
            "stirring.  After 2 min, NaOH (0.5 mL, 1 M) was added to adjust the pH to "
            "~12, and the reaction was maintained at 37 °C for 12 h.  The final product "
            "showed strong red fluorescence (emission max ~640 nm)."
        ),
    },
]

# spent a bit of time getting this to reliably output clean json - llama likes to
# add markdown fences or little comments if you don't explicitly tell it not to.
SYSTEM_PROMPT = """You are a chemistry information-extraction assistant specialised in
nanomaterial synthesis.  Extract ALL synthesis parameters from the user-supplied text
and return ONLY a valid JSON object - no prose, no markdown fences - with exactly
these fields:

{
  "material": "string",
  "method": "string or null",
  "reagents": [
    {"name": "string", "concentration": "string or null",
     "volume_or_mass": "string or null", "role": "string or null"}
  ],
  "temperature_C": "string or null",
  "time_hours": "string or null",
  "solvent": "string or null",
  "atmosphere": "string or null",
  "yield_or_purity": "string or null",
  "special_conditions": "string or null"
}

Rules:
- Convert all times to hours (e.g. "15 min" → "0.25").
- If a value is not mentioned, use null.
- Do NOT add keys that are not listed above.
- Return raw JSON only."""


def extract_parameters(client, text, model):
    """sends text to the model, parses the json, does a basic field check.
    temperature=0 since I want consistent extraction, not creative writing."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract synthesis parameters from the following text:\n\n{text}"},
        ],
        temperature=0.0,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()

    # just in case it wraps the json in ```...``` anyway despite being told not to
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)  # blows up loudly if the json is broken

    # quick sanity check instead of a whole schema class - just making sure
    # nothing's missing before I use this data for anything
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ValueError(f"model response is missing fields: {missing}")

    return data


def print_result(idx, ref, data):
    print(f"\n{'='*65}")
    print(f"  Sample {idx}  |  {ref}")
    print(f"{'='*65}")
    print(f"  Material       : {data.get('material') or '—'}")
    print(f"  Method         : {data.get('method') or '—'}")
    print(f"  Temperature    : {data.get('temperature_C') or '—'} °C")
    print(f"  Time           : {data.get('time_hours') or '—'} h")
    print(f"  Solvent        : {data.get('solvent') or '—'}")
    print(f"  Atmosphere     : {data.get('atmosphere') or '—'}")
    print(f"  Yield/Purity   : {data.get('yield_or_purity') or '—'}")
    print(f"  Special notes  : {data.get('special_conditions') or '—'}")
    print(f"\n  Reagents:")
    for r in data.get("reagents", []):
        conc = f"  {r.get('concentration')}" if r.get("concentration") else ""
        vol = f"  {r.get('volume_or_mass')}" if r.get("volume_or_mass") else ""
        role = f"  [{r.get('role')}]" if r.get("role") else ""
        print(f"    • {r.get('name')}{conc}{vol}{role}")


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # not hardcoding a key obviously, you gotta set this yourself
        print(
            "Error: GROQ_API_KEY environment variable not set.\n"
            "Get a free key at https://console.groq.com and run:\n"
            "  export GROQ_API_KEY='gsk_...'\n"
        )
        sys.exit(1)

    client = Groq(api_key=api_key)
    model = "meta-llama/llama-3.3-70b-versatile"  # free tier on groq

    print(f"\nRunning synthesis parameter extraction  (model: {model})\n")

    results = []

    for i, sample in enumerate(DEMO_TEXTS, start=1):
        print(f"Processing sample {i}/{len(DEMO_TEXTS)}: {sample['id']} …", end=" ", flush=True)
        try:
            data = extract_parameters(client, sample["text"], model)
            print("OK")
            print_result(i, sample["ref"], data)
            results.append(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"FAILED: {e}")

    # dump everything to a json file so it's actually usable for something later,
    # not just printed to a terminal and forgotten
    out_path = "extraction_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n\nAll results saved to {out_path}")


if __name__ == "__main__":
    main()
