import hashlib, csv
from typing import List

import genanki


DefaultFrontTemplate = '''<div class="front">{{cloze:Front}}</div>'''

DefaultBackTemplate = '''
<!-- HACK: Dynamically load JavaScript files, as Anki does not support static load -->
<script>

var script3 = document.createElement('script');
script3.src = 'highlight.js';
script3.async = false;
document.head.appendChild(script3);
document.head.removeChild(script3);


var coll_button = document.getElementById("collapsible");
coll_button.addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
});


setTimeout(() => {
	hljs.highlightAll();
}, 100);

</script>

<link rel="stylesheet" href="monokai-sublime.css">

<div class="back">
{{cloze:Front}}
<button type="button" id="collapsible">Original Doc</button>
<div class="content">
{{Back}}
</div>
</div>
'''

DefaultStyle = '''
.cloze {
    font-weight: bold;
    color: blue;
    background-color: pink;
    font-size: 24px;
}


.back {
    font-family: arial;
    font-size: 20px;
    text-align: left;
    color: white;
    background-color: black;
}

.front {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: white;
    background-color: black;
}

#collapsible {
  background-color: #777;
  color: white;
  cursor: pointer;
  padding: 18px;
  width: 100%;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
}

.active, #collapsible:hover {
  background-color: #555;
}

.content {
  padding: 0 18px;
  display: none;
  overflow: hidden;
}
'''


def chatgpt_response_cleanup(response: str) -> str:
    return response.replace('[Result]:', '').replace('[Information]:', '').replace('```html', '').replace('```python', '').replace('```', '').replace('\u3002', '')


def csv_to_notes(csv_files: List[str], model: genanki.Model) -> List[genanki.Note]:
    result_notes = []
    
    for c_file in csv_files:
        with open(c_file, 'r', encoding='utf-8') as f:
            csv_text = csv.reader(f, delimiter='\uFF0C', quotechar='\u3001', quoting=csv.QUOTE_MINIMAL, lineterminator='\u3002\n', doublequote=False)

            for i, c in enumerate(csv_text):
                if i == 0: continue # skip csv header line

                _, flashcards, flashcard_response_message, _, cloze_tables_message, _, cloze_code_message = c

                if flashcard_response_message:
                    result_notes += [genanki.Note(model=model, fields=[chatgpt_response_cleanup(flashcard_response_message), flashcards])]
                if cloze_tables_message:
                    result_notes += [genanki.Note(model=model, fields=[chatgpt_response_cleanup(cloze_tables_message), flashcards])]
                if cloze_code_message:
                    result_notes += [genanki.Note(model=model, fields=[f'<pre><code>{chatgpt_response_cleanup(cloze_code_message)}</code></pre>', flashcards])]
    
    return result_notes
                



def create_anki_package(name: str, model: genanki.Model, notes: List[genanki.Note] ):
    
    deck = genanki.Deck(deck_id=abs(hash(name)) % (10 ** 10), name=name)

    for n in notes:
      deck.add_note(n)

    # img_path = Path(r'image').glob('**/*')
    # images = ['image/'+x.name for x in img_path if x.is_file()]

    deck.add_note(genanki.Note(model=model,
        fields=['Dummy card for {{c1::javascript}} file', '<img src="highlight.js" style="display:none"><img src="monokai-sublime.css" style="display:none">']
    ))
    images = ['data/highlight.js', 'data/monokai-sublime.css'] # A hack to include Javascript file

    anki_output = genanki.Package(deck)
    anki_output.media_files = images
    anki_output.write_to_file(f'{name}.apkg')



if __name__ == "__main__":
    name = 'PythonDocs'
    hash_object = hashlib.sha1(name.encode('utf-8'))
    hex_dig = int(hash_object.hexdigest(), 16) % (10 ** 10)
    front_html = DefaultFrontTemplate
    back_html = DefaultBackTemplate

    templates = [{
      'name': f'{name}Cloze',
      'qfmt': front_html,
      'afmt': back_html,
    }]
    model = genanki.Model(model_id=hex_dig, model_type=genanki.Model.CLOZE, name=name, fields=[{'name': 'Front'},{'name': 'Back'}], templates=templates, css=DefaultStyle)
    notes = csv_to_notes(['output_flashcards_with_chatgpt\stdtypes.csv'], model=model)
    create_anki_package(name, model, notes)