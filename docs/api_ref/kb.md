---
layout: default
title: Knowledge Base
parent: API Reference
nav_order: 12
---

<a id="benchmate.knowledge_base"></a>

# benchmate.knowledge\_base

<a id="benchmate.knowledge_base.knowledge_base"></a>

# benchmate.knowledge\_base.knowledge\_base

<a id="benchmate.knowledge_base.knowledge_base.KnowledgeBase"></a>

## KnowledgeBase Objects

```python
class KnowledgeBase()
```

<a id="benchmate.knowledge_base.knowledge_base.KnowledgeBase.__init__"></a>

#### \_\_init\_\_

```python
def __init__(engine)
```

basic db constructor, will create the tables if it doesn't exist but we assume that the database is already created

**Arguments**:

- `engine`: sqlalchemy engine created from sqlalchemy.create_engine()

<a id="benchmate.knowledge_base.tables"></a>

