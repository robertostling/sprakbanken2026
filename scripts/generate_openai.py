"""Run questions through OpenAI models.

Usage:

    python3 scripts/generate_openai.py */*.json
"""

import json
import sys
import os

from openai import OpenAI

client = OpenAI()

settings = {
        'reasoning-sol-none': {
            'model': 'gpt-5.6-sol',
            'reasoning': {'effort': 'none'}
            },
        'reasoning-luna-none': {
            'model': 'gpt-5.6-luna',
            'reasoning': {'effort': 'none'}
            },
        'reasoning-sol-high': {
            'model': 'gpt-5.6-sol',
            'reasoning': {'effort': 'high'}
            },
        'reasoning-luna-high': {
            'model': 'gpt-5.6-luna',
            'reasoning': {'effort': 'high'}
            },
        }


output_dir = os.path.join('output', 'openai')

for filename in sys.argv[1:]:
    with open(filename) as f:
        data = json.load(f)

        for qa in (data if isinstance(data, list) else [data]):
            questions = qa['questions']
            answers = qa['answers']
            # languages = {question['language'] for question in questions}
            for question in questions:
                system_outputs = {}
                question['system_outputs'] = system_outputs
                for name, setting in settings.items():
                    response = client.responses.create(
                            input=question['question'], **setting)
                    text = response.output_text
                    print(text, flush=True)
                    system_outputs[name] = {
                            'setting': setting,
                            'generations': [text]
                            }

    os.makedirs(os.path.join(output_dir, os.path.dirname(filename)),
                exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w') as f:
        json.dump(data, f, indent=2)

