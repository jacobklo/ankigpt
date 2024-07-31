import csv

from openai import OpenAI

from constants import ANKI_FLASHCARD_SUMMARIZER_ASSISTANT_ID, HTML_CLOZE_CREATOR, PYTHON_CODE_CREATOR
from break_html_into_sections import save_to_fashcards_csv
from create_chatgpt_assistant import submit_message, wait_on_run



def run_gen_flascards_from_gpt():
    with open('output_list_of_htmls\stdtypes.csv', 'r', encoding='utf-8') as f:
        csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

        client = OpenAI()
        thread = client.beta.threads.create()
        results = []

        for i, c in enumerate(csv_text):
            if i == 0: continue # skip csv header line

            header, flashcards, tables, code = c
            flashcard_response_message, cloze_tables_message, cloze_code_message = None, None, None

            if len(flashcards) > 5:
                run = submit_message(client, ANKI_FLASHCARD_SUMMARIZER_ASSISTANT_ID, thread, user_message=f"""

    [Information]:
    ```html
    {flashcards}
    ```

    [Result 1 Flashcard]:
    ```html
    """)
                run = wait_on_run(client, run, thread)


                flashcard_response = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
                flashcard_response_message = flashcard_response.data[0].content[0].text.value

            if len(tables) > 5:
                run = submit_message(client, HTML_CLOZE_CREATOR, thread, user_message=f"""
    [Information]:
    ```html
    {tables}
    ```

    [Result]:
    ```html
    """)
                run = wait_on_run(client, run, thread)
                cloze_tables_response = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
                cloze_tables_message = cloze_tables_response.data[0].content[0].text.value
            
            if len(code) > 5:
                run = submit_message(client, PYTHON_CODE_CREATOR, thread, user_message=f"""
    [Information]:
    ```python
    {code}
    ```

    [Result]:
    ```python
    """)
                run = wait_on_run(client, run, thread)
                cloze_code_response = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
                cloze_code_message = cloze_code_response.data[0].content[0].text.value

            results.append([header, flashcards, flashcard_response_message, tables, cloze_tables_message, code, cloze_code_message])
            print(f'Processed {i}, {header}')

            save_to_fashcards_csv(results, 'flashcards_with_chatgpt\stdtypes', ['Header', 'Flashcard', 'ClozeFlash', 'Table', 'ClozeTable', 'Code', 'ClozeCode'])




if __name__ == "__main__":
    run_gen_flascards_from_gpt()

        



            
        

