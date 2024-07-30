import bs4


def remove_code_styles(tag: bs4.Tag) -> bs4.Tag:
    # Remove all attrs first
    for t in tag.find_all(True):
        t.attrs = {}
        if 'style' in t.attrs:
            del t.attrs['style']
        if 'class' in t.attrs:
            del t.attrs['class']

    # Then, remove the <span> manually to keep the text, space and nextline characters
    raw_html = str(tag)
    raw_html = raw_html.replace('<span>', '').replace('</span>', '')
    
    # Replace the <div> with the plain text
    tag.replace_with(bs4.BeautifulSoup(f'{raw_html}', 'html.parser'))
    return tag

    
def simplify_html(soup: bs4.Tag) -> bs4.Tag:
  
    # Remove all styles that highlight the Python code examples
    for tag in soup.find_all('div', class_='highlight'):
        tag = remove_code_styles(tag)

    for tag in soup.find_all(True):
        tag.attrs = {}
        if 'style' in tag.attrs:
            del tag.attrs['style']
        if 'class' in tag.attrs:
            del tag.attrs['class']
    
    return soup

if __name__ == "__main__":
    with open('stdtypes.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    sim_html = simplify_html(html)

    with open('simplify.html', 'w', encoding='utf-8') as f:
        f.write(sim_html)
