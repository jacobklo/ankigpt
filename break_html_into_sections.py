from collections import deque
from typing import List
import copy, os, csv

import bs4


from simplify_html import simplify_html

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
    os.makedirs(output_name, exist_ok=True)
    with open(f'{output_name}.csv', 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)
        writer.writerow(csv_headers)

        for s in list_of_htmls:
            writer.writerow(s)

    
    with open(f'{output_name}.csv', 'r', encoding='utf-8') as f:
        csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

        with open(f'{output_name}.html', 'w', encoding='utf-8') as html_file:
            
            for c in csv_text:
                header, flashcards, flashcard_response_message, tables, cloze_tables_message, code, cloze_code_message,  = c
                html_file.write(header)
                html_file.write(f'<div style="background-color: #bfff00">{flashcards}</div>')
                html_file.write(f'<div style="background-color: ##e0e0e0">{flashcard_response_message}</div>')
                html_file.write(f'<div style="background-color: #ff00ff">{tables}</div>')
                html_file.write(f'<div style="background-color: #ff8000">{cloze_tables_message}</div>')
                html_file.write(f'<div style="background-color: #ff0080">{code}</div>')
                html_file.write(f'<div style="background-color: #ff8080">{cloze_code_message}</div>')


def run_create_lists_of_htmls():
    list_of_htmls = divide_html_file('stdtypes.html')
    save_to_fashcards_csv(list_of_htmls, 'output_list_of_htmls\stdtypes', ['Header', 'Flashcards', 'Tables', 'Code'])



if __name__ == "__main__":
    run_create_lists_of_htmls()

        