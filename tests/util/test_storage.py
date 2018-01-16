from spidercommon.util.storage import HashedFile
import os

def test_write_str(tmpdir):
    test_data = "Eggs are cool."
    test_file = HashedFile.from_data(test_data, tmpdir)

    assert "9869f747a4061295811444e4cc238c2ae40c91dc2a1a8533799eaffac6539a41" == test_file.file_hash
    assert test_file.read() == test_data


def test_write_bytes(tmpdir):
    test_data = os.urandom(420)
    test_file = HashedFile.from_data(test_data, tmpdir)

    assert test_file.read() == test_data
