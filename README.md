# OpportunityAI

OpportunityAI is a lightweight Python tool for discovering business automation opportunities from real job listings. Its DeepSeek AI Brain looks for repeated manual work, estimates whether a low-cost tool, bot, or agent is feasible, and checks how many distinct employers appear to need similar work.

It has two modes:
- **Free Check:** the first collection uses no search keyword and sorts the newest available listings first. The Brain then suggests ideas and runs focused validation searches.
- **Targeted Check:** the Brain converts an industry/task request into a focused first search, then validates ideas with related job searches.

The Brain's default sources are general-purpose listings, not a remote-only feed: Dev Global Jobs and Arbeitnow's Europe/UK feeds. Remote-focused sources remain available for the classic collector, but are not used by the Brain by default. Coverage is incomplete; listings are signals to investigate, not proof of willingness to buy.

## Quick start

Requires Python 3.10+ and a DeepSeek API key. The code uses only the Python standard library; no package installation or database is needed.

Set your key as an environment variable (do not commit it):
- Windows PowerShell: $env:DEEPSEEK_API_KEY="your-key"
- macOS/Linux: export DEEPSEEK_API_KEY="your-key"

Optional model setting: OPPORTUNITY_BRAIN_MODEL=deepseek-flash.

~~~bash
# Free Check: first scan is keyword-free
python opportunity_ai.py --mode free --request "Find simple, low-cost automations for Nigerian small businesses" --count 5 --min-companies 5

# Targeted Check: initial search is focused on an industry/task
python opportunity_ai.py --mode targeted --request "Private schools in Nigeria" --count 5 --min-companies 5

# Faster, more constrained run
python opportunity_ai.py --mode targeted --request "Clinic admin tasks in Nigeria" --days 10 --location Nigeria --count 3 --min-companies 4 --max-rounds 1
~~~

Options:
- count: how many different qualified ideas to seek (default 5; max 20).
- min-companies: minimum distinct named employers in the validation results (default 5).
- days and location: explicit overrides; otherwise the Brain infers sensible values from your request (default timeframe is 14 days).
- max-rounds: number of proposal batches (default 2; hard maximum 4).
- max-difficulty: highest acceptable build difficulty (default 3/5).

Qualified opportunities must meet a rule enforced by Python: enough distinct employers, estimated difficulty 3/5 or less, low/medium resources, and a non-technical-friendly workflow. If only three ideas meet the criteria, the tool returns three rather than inventing extra opportunities. The Brain's estimates are hypotheses; talk to real businesses before building.

The report is saved to opportunity_report.json; newly qualified ideas are added to opportunity_memory.json. These local files are ignored by Git. Repeated names are excluded from later runs to reduce redundant research.

## How the Brain stays bounded

- Uses one broad initial scan, a small candidate batch, and targeted checks only for each candidate.
- Uses a 100-listing page for the general feed, limited pagination for regional feeds, and the existing local cache.
- Checks ideas in batches, with a configurable round limit and a maximum of 6 proposed ideas per round.
- Uses AI to plan and judge ideas, but Python counts unique employers and enforces qualification rules.
- Retains source links and names; verify each listing is still current.

## Classic job search CLI

The original opportunity.py collector remains available. It can search with a keyword or browse newest jobs with no keyword:

~~~bash
python opportunity.py --help
python opportunity.py
python opportunity.py "data entry" --days 14 --location Nigeria
python opportunity.py "customer support" --days 5 --source arbeitnow-eu
~~~

The collector supports additional remote-focused feeds as optional sources, so it remains useful for its original job-search use case. Source coverage, rate limits, caching, dates, and location eligibility affect results.

## Sources and terms

The AI Brain's default search list:
- [Dev Global Jobs API](https://devglobaljobs.com/developers) — general international roles; public no-key API, one 100-listing page per query. Its published terms allow internal/non-commercial use without extra permission; preserve the original listing link and attribution.
- [Arbeitnow](https://blog.arbeitnow.com/blog/job-board-api) — general Europe and UK listings; public no-key feeds with limited pagination.

Other source adapters in opportunity.py include remote-focused feeds (Himalayas, Jobicy, Remote OK, RemoteJobs.org, We Work Remotely, and Remotive). They are not part of the AI Brain's default source list.

## Important limitations

Job ads do not prove that an employer wants to buy automation. Different listings can describe one employer's single need, and similar job titles can hide different tasks. Employer counts are deduplicated by company name, which is helpful but not perfect. The Brain is not permitted to fabricate demand; low evidence should result in fewer qualified ideas.

The Dev Global Jobs API's published terms restrict free API use to internal/non-commercial use unless permission is obtained. This implementation is intended for private research; review the provider's current terms before using it as part of a commercial service or redistributing its data. Other providers also have their own policies and limits.

## Tests

~~~bash
python -m py_compile opportunity.py opportunity_ai.py tests/test_opportunity.py tests/test_opportunity_ai.py
python -m unittest discover -s tests -v
~~~
