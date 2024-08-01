from collections import deque
from typing import List
from pathlib import Path
import copy, os, csv, random

import bs4


from simplify_html import simplify_html


def random_css_color():
    return "#{:06x}".format(random.randint(0x888888, 0xFFFFFF))


def divide_html_file(html_filename: str, html_path: str) -> List:
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

        soup = bs4.BeautifulSoup(html, 'html.parser')

        # Specifically for python docs, remove any "New in version 3.X" or "Changed in version 3.X" sections, i am not interested in them
        for version_section in soup.find_all(lambda tag: tag.name == 'div' and 'class' in tag.attrs and  'versionchanged' in tag.attrs['class']):
            version_section.clear()
        for version_section in soup.find_all(lambda tag: tag.name == 'div' and 'class' in tag.attrs and  'versionadded' in tag.attrs['class']):
            version_section.clear()

        # Handle every element that is this critira
        critira = lambda tag: (tag.name == 'section') or (tag.name == 'dl' and 'class' in tag.attrs and  ('method' in tag.attrs['class'] or 'class' in tag.attrs['class']))

        # Get all the parent section's name
        for tag in soup.find_all(critira):
            parents = []
            current = tag
            while current.parent and current.name != 'body':
                current = current.parent
                if current.get('id'):
                    parents.append(current.get('id'))
            table_of_content = soup.new_tag('p', id='table_of_content')
            table_of_content.string = '>'.join([html_filename] + list(reversed(parents)))
            tag.append(table_of_content)


        pending_sections: deque[bs4.element.Tag] = deque()
        result_sections = []

        # Put every sesstion into a queue
        for section in soup.find_all(critira):
            pending_sections.append(copy.copy(section))
        
        # For every section
        while pending_sections:
            section = pending_sections.popleft()
            header = ''
            tables = []
            code_blocks = []

            
            # Remove child section
            for child_section in section.find_all(critira):
                child_section.decompose()

            # Get header, is just the table of contents calculated from above
            headers = section.find_all('p', id='table_of_content')
            header = str(headers[0]) if headers else ''
            for p in headers:
                p.decompose()

            # Simplify the section code
            section = simplify_html(section)
            
            # Get any tables, and remove from current section
            for table in section.find_all('table'):
                tables.append(copy.copy(table))
                table.decompose()

            # Get any code blocks, and remove from current section
            for code_block in section.find_all('pre'):
                code_blocks.append(copy.copy(code_block))
                code_block.decompose()

            # Combine Tables elements into 1 <div>
            table_div = ''
            if tables:
                table_div = bs4.BeautifulSoup('<div></div>', 'html.parser')
                for table in tables:
                    table_div.div.append(table)
            
            # Combine Code Blocks elements into 1 <div>
            code_block_div = ''
            if code_blocks:
                code_block_div = bs4.BeautifulSoup('<div></div>', 'html.parser')
                for code_block in code_blocks:
                    code_block_div.div.append(code_block)

            result_sections.append([header, str(section), str(table_div), str(code_block_div)])
        
        return result_sections



def save_to_fashcards_csv(list_of_htmls: List, output_name: str, csv_headers: List):
    # os.makedirs(output_name, exist_ok=True)
    with open(f'{output_name}.csv', 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)
        writer.writerow(csv_headers)

        for s in list_of_htmls:
            writer.writerow(s)

    
    with open(f'{output_name}.csv', 'r', encoding='utf-8') as f:
        csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

        with open(f'{output_name}.html', 'w', encoding='utf-8') as html_file:
            colors = []
            for c in csv_text:
                if not colors:
                    colors = [random_css_color() for _ in range(len(c))]
                    html_file.write('<style>')
                    html_file.write('\n')
                    for i, color in enumerate(colors):
                        html_file.write(f'.c{i} {{background-color: {color};}}')
                        html_file.write('\n')
                    html_file.write('</style>')
                for i, ele in enumerate(c):
                    html_file.write(f'<div class="c{i}">{ele}</div>')
                    html_file.write('\n')


def run_create_lists_of_htmls():
    directory_to_scan = ['library', 'reference']

    scan_path = Path('C:/git/python-3.12.3-docs-html')
    for directory in directory_to_scan:
        for file in (scan_path / directory).iterdir():
            if file.suffix == '.html':
                filepath = file.resolve()
                list_of_htmls = divide_html_file(f'{directory}>{file.stem}', filepath)

                save_to_fashcards_csv(list_of_htmls, f'output_list_of_htmls\{directory}_{file.stem}', ['Header', 'Flashcards', 'Tables', 'Code'])



if __name__ == "__main__":
    run_create_lists_of_htmls()

        