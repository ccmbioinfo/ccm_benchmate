---
layout: default
title: General Utils
parent: API Reference
nav_order: 13
---

<a id="benchmate.utils"></a>

# benchmate.utils

<a id="benchmate.utils.general_utils"></a>

# benchmate.utils.general\_utils

<a id="benchmate.utils.general_utils.warn_for_status"></a>

#### warn\_for\_status

```python
def warn_for_status(response, message)
```

Check the status of a response and issue a warning if the status code is not 200. I should not be holding hands but i might as well

<a id="benchmate.utils.general_utils.binary_data_transformer"></a>

#### binary\_data\_transformer

```python
def binary_data_transformer(data_bytes, binary_stream)
```

simpgle transformer that just writes the bytes to the stream, when in doubt use this for the compressed_stream_manager

**Arguments**:

- `data_bytes`: 
- `binary_stream`: 

<a id="benchmate.utils.general_utils.compressed_stream_manager"></a>

#### compressed\_stream\_manager

```python
@contextmanager
def compressed_stream_manager(obj: Any, transformer: Callable[[Any, io.IOBase],
                                                              None])
```

**Arguments**:

- `obj`: 
- `transformer`: 

<a id="benchmate.utils.general_utils.decompressed_stream_manager"></a>

#### decompressed\_stream\_manager

```python
@contextmanager
def decompressed_stream_manager(compressed_bytes: bytes,
                                reconstructor: Callable[[BinaryIO], Any])
```

Generic manager to decompress bytes and yield the reconstructed object.

**Arguments**:

- `compressed_bytes`: The raw gzipped bytes from the DB.
- `reconstructor`: A function that takes a binary stream and returns an object.

