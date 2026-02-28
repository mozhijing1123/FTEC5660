# ReAct

## Setup
1. Install Python dependencies:
   ``pip install -r requirements.txt``

2. Configure the LLM endpoint in ``base_config.yaml``:
   - ``llm.api_key``: your API key
   - ``llm.base_url``: your OpenAI-compatible API base URL

3. If you want to run AlfWorld experiments, install ``alfworld`` separately by following the official instructions:
   [https://github.com/alfworld/alfworld](https://github.com/alfworld/alfworld)

4. Some tasks also expect the related datasets to already exist under ``data/``.

## Experiments
Run ``{hotpotqa,fever,alfworld,webshop}.ipynb`` in Jupyter after setup. As HotpotQA and FEVER have large validation sets, the notebooks only run 500 random examples (see notebook code).

You can also run the AlfWorld script directly:
``python test.py``

The repository currently mixes legacy benchmark prompts with a custom OpenAI-compatible endpoint. ``requirements.txt`` pins a compatible ``openai`` SDK version so the notebooks and ``test.py`` use the same API style.


|                    | HotpotQA (500 random dev, EM) | FEVER (500 random dev, EM) | AlfWorld (success rate) | WebShop  (success rate) |
|--------------------|-------------------------------|----------------------------|-------------------------|-------------------------|
| PaLM-540B (paper)  | 29.4                          | 62.2                       | 70.9                    | 40                      |
| GPT-3 (davinci-002) | 30.4                          | 54                         | 78.4                    | 35.8                    |
