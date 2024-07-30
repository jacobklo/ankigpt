from collections import deque
from typing import List
import copy
import csv

from openai import OpenAI
import bs4

import constants as local_vars
from simplify_html import simplify_html


def call_chatgpt(information: str):
    client = OpenAI()
    result = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant that can read HTML code."},
                  {"role": "user", "content":  f"""
The user is a Python developer who is trying to create a Python Docs flashcards.

Given the [Information], summerize the content into 1 flashcard only, mainly use bullet points, with less than 150 words per card.

It is optional to include coding examples, based on the information provided.
                   
Please add a lot of Anki's Cloze Delete fields, split the content into 3 cloze fields, with the format {{c1::Things_to_remember}}, {{c2::Things_to_remember}}, {{c3::Things_to_remember}}

Use double open curly braces `{{` and double close curly braces `}}` for cloze fields.
Example of Cloze Delete:
```html
<div class="flashcard">
  <h2>Comparisons in Python</h2>
  <ul>
    <li>8 comparison operations with the same priority (higher than {{c1::Boolean}} ops).</li>
    <li>Chained comparisons: {{c1::<code>x &lt; y &lt;= z</code>}} equivalent to <code>x &lt; y and y &lt;= z</code>.</li>
    <li>Comparing different types (except numeric) {{c1::always unequal.}}</li>
    <li><code>==</code> always defined; for object types, often same as {{c2::<code>is</code>}}.</li>
    <li><code>&lt;</code>, <code>&lt;=</code>, <code>&gt;</code>, <code>&gt;=</code> defined where meaningful; else raise {{c2::<code>TypeError</code>}}.</li>
    <li>Class instances compare non-equal unless {{c2::<code>__eq__()</code>}} defined.</li>
    <li>Class instances' ordering defined by {{c3::<code>__lt__()</code>}}, {{c3::<code>__le__()</code>}}, {{c3::<code>__gt__()</code>}}, {{c3::<code>__ge__()</code>}}.</li>
    <li><code>is</code> and <code>is not</code>: cannot {{c3::customize}}, no exceptions, any two objects.</li>
    <li><code>in</code> and <code>not in</code>: supported by {{c3::iterable}} types or {{c3::<code>__contains__()</code>}} method.</li>
  </ul>
</div>
```

Return [Result 1 Flashcard] in HTML format.

[Information]:
```html
{information}
```

[Result 1 Flashcard]:
```html
"""}],
        stream=False,
    )
    return result.choices[0].message.content


def divide_html_file(html_path: str) -> List:
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

        soup = bs4.BeautifulSoup(html, 'html.parser')

        # Specifically for python docs, remove any "New in version 3.X" or "Changed in version 3.X" sections, i am not interested in them
        for version_section in soup.find_all(lambda tag: tag.name == 'div' and 'class' in tag.attrs and  'versionchanged' in tag.attrs['class']):
            version_section.clear()
        for version_section in soup.find_all(lambda tag: tag.name == 'div' and 'class' in tag.attrs and  'versionadded' in tag.attrs['class']):
            version_section.clear()


        pending_sections = deque()
        result_sections = []

        # Put every sesstion into a queue
        critira = lambda tag: (tag.name == 'section') or (tag.name == 'dl' and 'class' in tag.attrs and  ('method' in tag.attrs['class'] or 'class' in tag.attrs['class']))

        for section in soup.find_all(critira):
            pending_sections.append(copy.copy(section))
        
        # For every section
        while pending_sections:
            section = pending_sections.popleft()
            header = None
            tables = []
            code_blocks = []

            # Remove child section
            for child_section in section.find_all(critira):
                child_section.decompose()
            
            # Simplify the section code
            section = simplify_html(section)

            # Get header
            headers = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt'])
            header = headers[0] if headers else None
            
            # Get any tables, and remove from current section
            for table in section.find_all('table'):
                tables.append(copy.copy(table))
                table.decompose()

            # Get any code blocks, and remove from current section
            for code_block in section.find_all('pre'):
                code_blocks.append(copy.copy(code_block))
                code_block.decompose()

            # Combine Tables elements into 1 <div>
            table_div = bs4.BeautifulSoup('<div></div>', 'html.parser')
            for table in tables:
                table_div.div.append(table)
            
            # Combine Code Blocks elements into 1 <div>
            code_block_div = bs4.BeautifulSoup('<div></div>', 'html.parser')
            for code_block in code_blocks:
                code_block_div.div.append(code_block)

            result_sections.append([str(header), str(section), str(table_div), str(code_block_div)])
        
        return result_sections
      

def save_to_fashcards_csv(list_of_htmls: List, output_name: str, csv_headers: List):
    with open(f'{output_name}.csv', 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)
        writer.writerow(csv_headers)

        for s in list_of_htmls:
            writer.writerow(s)

    
    with open(f'{output_name}.csv', 'r', encoding='utf-8') as f:
        csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

        with open(f'{output_name}.html', 'w', encoding='utf-8') as html_file:
            
            for c in csv_text:
                for element in c:
                    html_file.write(element)
                    html_file.write('<hr />')



def run_create_lists_of_htmls():
    list_of_htmls = divide_html_file('stdtypes.html')
    save_to_fashcards_csv(list_of_htmls, 'list_of_htmls', ['Header', 'Flashcards', 'Tables', 'Code'])



def run_gen_flascards_from_gpt():
    with open('lists_of_flashcards.csv', 'r', encoding='utf-8') as f:
        csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

        results = []

        for i, c in enumerate(csv_text):
            header, flashcards, tables, code = c
            chatgpt_response = call_chatgpt(flashcards)
            results.append([header, flashcards, chatgpt_response, tables, code])
            print(f'Processed {i}, {header}')

            save_to_fashcards_csv(results, 'flashcards_with_chatgpt', ['Header', 'Flashcards', 'ChatGPT', 'Tables', 'Code'])




if __name__ == "__main__":
    run_create_lists_of_htmls()
    # run_gen_flascards_from_gpt()

        



            
        

