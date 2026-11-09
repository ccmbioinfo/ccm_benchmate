import warnings
from contextlib import contextmanager
from typing import Any, Callable, BinaryIO
import gzip
import io


class DataIntegrityError(Exception):
    pass

class ProjectNameError(Exception):
    pass


def warn_for_status(response, message):
    """
    Check the status of a response and issue a warning if the status code is not 200. I should not be holding hands but i might as well
    """
    if response.status_code != 200:
        warnings.warn("Response status code: {}, status message {}".format(response.status_code, message))
        return None
    else:
        return response.content.decode().strip()


def binary_data_transformer(data_bytes, binary_stream):
    """
    simpgle transformer that just writes the bytes to the stream, when in doubt use this for the compressed_stream_manager
    :param data_bytes:
    :param binary_stream:
    :return:
    """
    # No extra wrapping needed; just write bytes
    binary_stream.write(data_bytes)


@contextmanager
def compressed_stream_manager(obj: Any, transformer: Callable[[Any, io.IOBase], None]):
    """

    :param obj:
    :param transformer:
    :return:
    """
    buffer = io.BytesIO()
    try:
        # We only manage the lifecycle of the Gzip wrapper and the buffer
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
            transformer(obj, gz)
        yield buffer.getvalue()

    finally:
        buffer.close()

@contextmanager
def decompressed_stream_manager(compressed_bytes: bytes,
                                reconstructor: Callable[[BinaryIO], Any]):
    """
    Generic manager to decompress bytes and yield the reconstructed object.

    :param compressed_bytes: The raw gzipped bytes from the DB.
    :param reconstructor: A function that takes a binary stream and returns an object.
    """
    # 1. Wrap the raw bytes in a stream
    raw_stream = io.BytesIO(compressed_bytes)

    try:
        # 2. Layer the decompression
        with gzip.GzipFile(fileobj=raw_stream, mode='rb') as gz:
            # 3. Yield the result of the reconstructor
            yield reconstructor(gz)
    finally:
        raw_stream.close()

def check_annotations(item, is_class):
    if hasattr(item, "annotations"):
        if type(item.info.annotations) is not dict:
            raise TypeError(f"The annotations for this {item.__class__.__name__()} has to be a dict")

