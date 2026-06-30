# syn_extract

Pulls structured synthesis parameters out of nanomaterial chemistry papers using an LLM. Sends a text excerpt to Groq's API (Llama 3.3 70B), asks for a JSON response, and validates the schema before accepting it.

## What it extracts

| Field | Description |
|---|---|
| `material` | Synthesised material (e.g. Au25 nanocluster) |
| `method` | Synthesis method (e.g. reduction, heating) |
| `reagents` | List of reagents with name, concentration, volume/mass, and role |
| `temperature_C` | Reaction temperature in °C |
| `time_hours` | Reaction time converted to hours |
| `solvent` | Solvent system used |
| `atmosphere` | Reaction atmosphere (e.g. N2, air) |
| `yield_or_purity` | Yield or purity if reported |
| `special_conditions` | Any other notable conditions (pH, stirring speed, etc.) |

## Setup

**1. Install dependencies**

```bash
pip install groq python-dotenv
```

**2. Get a free Groq API key**

Sign up at [console.groq.com](https://console.groq.com) — no credit card required.

**3. Create a `.env` file**

```bash
echo 'GROQ_API_KEY=gsk_...' > .env
```

The `.env` file is listed in `.gitignore` and will not be committed.

## Usage

```bash
python3 python
```

The script runs against three built-in demo excerpts from open-access gold nanocluster / nanoparticle papers and prints a formatted summary for each, then writes all results to `extraction_results.json`.

**Example output:**

```
=================================================================
  Sample 2  |  Turkevich / Frens method (classic, public domain)
=================================================================
  Material       : gold nanoparticles
  Method         : heating
  Temperature    : 100 °C
  Time           : 0.33 h
  Solvent        : —
  Atmosphere     : —
  Yield/Purity   : —
  Special notes  : vigorous stirring

  Reagents:
    • HAuCl4  1 mM  100 mL  [precursor]
    • sodium citrate  38.8 mM  10 mL  [reducing agent]
```

## Swapping the model or provider

The extraction logic in `extract_parameters()` is provider-agnostic. To switch to OpenAI or Anthropic, replace the `Groq` client and model name in `main()` — nothing else needs to change.

## Files

```
.
├── python                  # main script (synth_extractor.py)
├── .env                    # your API key (not committed)
├── .gitignore
└── extraction_results.json # output, generated on run
```
