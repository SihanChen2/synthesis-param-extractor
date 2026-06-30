
# synth-extractor

small script I put together to pull structured synthesis params out of nanomaterial
papers using an LLM. mostly wanted to play around with structured output / schema
validation instead of just trusting whatever json a model spits out.

## the problem

synthesis details (reagents, temp, time, solvent...) are basically always just
buried in a paragraph of prose in papers. fine for a human reading one paper,
annoying if you actually want a dataset out of a hundred of them. so the idea
here is just: feed it the paragraph, get back clean json, validate it, done.

## how it works

- uses groq's api to call llama 3.3 70b (free, fast, no cc needed for the key)
- prompt tells the model exactly what fields to return
- does a quick check that the response actually has those fields before I trust
  it - didn't want to pull in a whole schema library for this, a plain dict +
  a list of required keys is enough to catch the model skipping something
- dumps everything to `extraction_results.json` at the end

## running it

```bash
pip install groq
export GROQ_API_KEY="gsk_..."     # free, get one at console.groq.com
python synth_extractor.py
```

it'll run on 3 demo paragraphs I pulled from open-access gold nanocluster /
nanoparticle papers (Au25(SG)18 synthesis, the classic Turkevich citrate method,
and a BSA-encapsulated AuNC prep) and print a summary for each, plus save the
full structured output to json.

sample output:

```
=================================================================
  Sample 1  |  Jin et al. (open access) - Au25(SG)18 synthesis
=================================================================
  Material       : Au25(SG)18 nanoclusters
  Method         : one-pot reduction
  Temperature    : 0 → 25 °C
  Time           : 24 h
  Solvent        : methanol/water (1:1 v/v)
  Atmosphere     : N2

  Reagents:
    • HAuCl4·3H2O  0.1 mmol  [gold precursor]
    • Glutathione   0.3 mmol  [ligand]
    • NaBH4         0.2 M, 0.5 mL  [reducing agent]
```

## things I might add later

- swap in real paper abstracts via a literature search api instead of hardcoded text
- batch mode for running over a whole folder/csv of papers
- try other models (groq has a few open ones) and compare extraction accuracy
- maybe a confidence/uncertainty field if the model isn't sure about something

## stack

just `groq` for the api call. no schema library, no extra deps - a plain dict
and a required-fields check do the job here, didn't feel worth adding pydantic
for something this small.
