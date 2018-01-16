import os

from spidercommon.util.storage import HashedFile


def test_write_str(tmpdir):
    test_data = "Eggs are cool."
    test_file = HashedFile.from_data(test_data, tmpdir)

    assert test_file.file_hash == "9869f747a4061295811444e4cc238c2ae40c91dc2a1a8533799eaffac6539a41"
    assert test_file.read() == test_data


def test_write_bytes(tmpdir):
    test_data = os.urandom(420)
    test_file = HashedFile.from_data(test_data, tmpdir)

    assert test_file.read() == test_data


def test_same_path_same_data(tmpdir):
    test_data = os.urandom(420)
    test_file1 = HashedFile.from_data(test_data, tmpdir)
    test_file2 = HashedFile.from_data(test_data, tmpdir)

    assert test_file1.full_path == test_file2.full_path
    assert test_file1.read() == test_file2.read()
