import csv
from pathlib import Path

from openai import OpenAI

from constants import ANKI_FLASHCARD_SUMMARIZER_ASSISTANT_ID, HTML_CLOZE_CREATOR, PYTHON_CODE_CREATOR
from break_html_into_sections import save_to_fashcards_csv
from create_chatgpt_assistant import submit_message, wait_on_run


def get_summerizer_info(flashcards):
  if len(flashcards) <= 5: return ''
  return  f"""
[Information]:
```html
{flashcards}
```

[Result 1 Flashcard]:
```html
"""

def get_table_info(tables):
  if len(tables) <= 5: return ''
  return f"""
[Information]:
```html
{tables}
```

[Result]:
```html
"""

def get_code_info(code):
    if len(code) <= 5: return ''
    return f"""
[Information]:
```python
{code}
```

[Result]:
```python
"""


def run_chatGPT(client: OpenAI, info: str, assistant_id: str) -> str:
  result_response = ''

  if len(info) > 5:
    while not result_response:
      thread = client.beta.threads.create(timeout=60)
      run = submit_message(client, assistant_id, thread, user_message=info)
      run = wait_on_run(client, run, thread)
      response = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
      result_response = response.data[0].content[0].text.value

      if run.status != "completed":
        client.beta.threads.runs.cancel(run_id=run.id, thread_id=thread.id)
      client.beta.threads.delete(thread_id=thread.id)
      
  return result_response


def run_gen_flascards_from_gpt():
  for csv_file in Path('output_list_of_htmls').glob('*.csv'):
    print(f'-----Processing {csv_file.stem}')

    with open(csv_file, 'r', encoding='utf-8') as f:
      csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

      client = OpenAI()
      
      results = []

      for i, c in enumerate(csv_text):
        if i == 0: continue # skip csv header line

        header, flashcards, tables, code = c

        flashcard_response_message = run_chatGPT(client, get_summerizer_info(flashcards), ANKI_FLASHCARD_SUMMARIZER_ASSISTANT_ID)
        cloze_tables_message = run_chatGPT(client, get_table_info(tables), HTML_CLOZE_CREATOR)
        cloze_code_message = run_chatGPT(client, get_code_info(code), PYTHON_CODE_CREATOR)

        results.append([header, flashcards, flashcard_response_message, tables, cloze_tables_message, code, cloze_code_message])
        print(f'Processed {i}, {header}')

        save_to_fashcards_csv(results, f'output_flashcards_with_chatgpt\{csv_file.stem}', ['Header', 'Flashcard', 'ClozeFlash', 'Table', 'ClozeTable', 'Code', 'ClozeCode'])

    print(f'-----Finished {csv_file.stem}')

if __name__ == "__main__":
  run_gen_flascards_from_gpt()

        



            
        

