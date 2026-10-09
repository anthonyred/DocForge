import mistune
from mistune.plugins.table import table

md = mistune.create_markdown(renderer='ast', plugins=[table])
text = """```python
def hello():
    print("world")
```
"""
res = md(text)
print("Mistune AST result:")
print(res)
