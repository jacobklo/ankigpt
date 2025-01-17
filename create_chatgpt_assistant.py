
"""
This will create a new OpenAI chatGPT assistant.
You only need to run this once to create the assistant.
"""
from openai import OpenAI
from openai.types.beta.thread import Thread
from openai.types.beta.threads import Run


import os, time

import constants as local_vars


anki_flashcard_summarizer = """
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

"""



html_cloze_creator = """
The user wants to create some cloze deletion flashcards.

Given the [Information] in HTML code, re-write the html code with Anki's Cloze Delete fields, for the information to remember.
                   
Please add a lot of Anki's Cloze Delete fields, split the content into 3 cloze fields, with the format {{c1::Things_to_remember}}, {{c2::Things_to_remember}}, {{c3::Things_to_remember}}

Use double open curly braces `{{` and double close curly braces `}}` for cloze fields.

Example output:
[Information]:
```html
<table>
<thead>
<tr><th><p>Representation</p></th>
<th><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr><td><p><code><span>\n</span></code></p></td>
<td><p>Line Feed</p></td>
</tr>
<tr><td><p><code><span>\r</span></code></p></td>
<td><p>Carriage Return</p></td>
</tr>
<tr><td><p><code><span>\r\n</span></code></p></td>
<td><p>Carriage Return + Line Feed</p></td>
</tr>
<tr><td><p><code><span>\v</span></code> or <code><span>\x0b</span></code></p></td>
<td><p>Line Tabulation</p></td>
</tr>
<tr><td><p><code><span>\f</span></code> or <code><span>\x0c</span></code></p></td>
<td><p>Form Feed</p></td>
</tr>
</tbody>
</table>
```

[Result]:
```html
<table>
<thead>
<tr><th><p>Representation</p></th>
<th><p>Description</p></th>
</tr>
</thead>
<tbody>
<tr><td><p><code><span>\n</span></code></p></td>
<td><p>{{c1::Line Feed}}</p></td>
</tr>
<tr><td><p><code><span>\r</span></code></p></td>
<td><p>{{c1::Carriage Return}}</p></td>
</tr>
<tr><td><p><code><span>\r\n</span></code></p></td>
<td><p>{{c2::Carriage Return}} + {{c2::Line Feed}}</p></td>
</tr>
<tr><td><p><code><span>\v</span></code> or <code><span>\x0b</span></code></p></td>
<td><p>{{c2::Line Tabulation}}</p></td>
</tr>
<tr><td><p><code><span>\f</span></code> or <code><span>\x0c</span></code></p></td>
<td><p>{{c3::Form Feed}}</p></td>
</tr>
</tbody>
</table>
```
"""



python_cloze_creator = """
The user wants to create some cloze deletion flashcards for studying sample Python code.

Given the [Information] in Python code, re-write the Python code with Anki's Cloze Delete fields, for the information to remember.
                   
Please add a lot of Anki's Cloze Delete fields, split the content into 3 cloze fields, with the format {{c1::Things_to_remember}}, {{c2::Things_to_remember}}, {{c3::Things_to_remember}}

Use double open curly braces `{{` and double close curly braces `}}` for cloze fields.

Do not cloze delete:
1. Code comments like `# This is a comment`, `'''This is a docstring'''`, `\* This is a comment *\`.
2. Strings like `"This is a string"`, `'This is a string'`.
3. Variable names like `my_variable`, `myFunction`.
4. Keywords like `if`, `else`, `for`, `while`, `def`, `class`, `import`, `from`, `as`, `return`, `yield`, `raise`, `try`, `except`, `finally`, `with`, `assert`, `lambda`, `nonlocal`, `global`, `and`, `or`, `not`, `in`, `is`, `True`, `False`, `None`.
5. function parameters like `def my_function(param1, param2):`.
6. cloze delete only the right side of the operators, like `left_index < {{c2::len(left)}}`, `merged = {{c2::[]}}`, `len(arr) // {{c1::2}}`.

Example of a Python console session:
[Information]:
```python
>>> list(range(10))
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
>>> list(range(1, 11))
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
>>> list(range(0, 30, 5))
[0, 5, 10, 15, 20, 25]
>>> list(range(0, 10, 3))
[0, 3, 6, 9]
```

[Result]:
```python
>>> list(range(10))
{{c1::[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}}
>>> list(range(1, 11))
{{c1::[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}}
>>> list(range(0, 30, 5))
{{c2::[0, 5, 10, 15, 20, 25]}}
>>> list(range(0, 10, 3))
{{c3::[0, 3, 6, 9]}}
```

Example of a Python script snippet:
[Information]:
```python
def merge_sort(arr):
    # Base case
    if len(arr) <= 1:
        return arr

    # Recursive case: divide the array into halves
    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid])
    right_half = merge_sort(arr[mid:])

    # Merge the sorted halves
    return merge(left_half, right_half)

def merge(left, right):
    merged = []
    left_index, right_index = 0, 0

    # Merge by comparing elements of both halves
    while left_index < len(left) and right_index < len(right):
        if left[left_index] < right[right_index]:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    # Append remaining elements
    merged.extend(left[left_index:])
    merged.extend(right[right_index:])

    return merged

# Example usage:
# arr = [34, 7, 23, 32, 5, 62]
# sorted_arr = merge_sort(arr)
# print(sorted_arr)  # Output will be the sorted array
```

[Result]:
```python
def merge_sort(arr):
    # Base case
    if len(arr) <= {{c1::1}}:
        return arr

    # Recursive case: divide the array into halves
    mid = len(arr) // {{c1::2}}
    left_half = {{c1::merge_sort(arr[:mid])}}
    right_half = {{c1::merge_sort(arr[mid:])}}

    # Merge the sorted halves
    return merge({{c1::left_half}}, {{c1::right_half}})

def merge(left, right):
    merged = {{c2::[]}}
    left_index, right_index = {{c2::0}}, {{c2::0}}

    # Merge by comparing elements of both halves
    while left_index < {{c2::len(left)}} and right_index < {{c2::len(right)}}:
        if left[left_index] < {{c3::right[right_index]}}:
            {{c3::merged.append(left[left_index])}}
            left_index += {{c3::1}}
        else:
            {{c3::merged.append(right[right_index])}}
            right_index += {{c3::1}}

    # Append remaining elements
    merged.extend({{c3::left[left_index:]}})
    merged.extend({{c3::right[right_index:]}})

    return merged

# Example usage:
# arr = [34, 7, 23, 32, 5, 62]
# sorted_arr = merge_sort(arr)
# print(sorted_arr)  # Output will be the sorted array
```
"""


def create_assistant(name, instructions):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model="gpt-4o",
    )
    print(assistant)
    print(f"Remember to save the assistant id: {assistant.id}")
    return assistant


def wait_on_run(client: OpenAI, run: Run, thread: Thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        print(f"Run status: {run.id} - {run.status}")
        time.sleep(5)
        # if run.status not in ["queued", "in_progress", "completed"]:
        #     print(run)
        #     raise Exception(f"Run status: {run.status}")
    return run


def submit_message(client: OpenAI, assistant_id: str, thread: Thread, user_message: str):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )



if __name__ == "__main__":
    # create_assistant("Anki Flashcard summarizer", anki_flashcard_summarizer)
    # create_assistant("HTML Cloze Creator", html_cloze_creator)
    create_assistant("Python Cloze Creator", python_cloze_creator)
