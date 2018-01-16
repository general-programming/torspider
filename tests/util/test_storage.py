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


def test_non_existent_hash_then_make_it_real(tmpdir):
    # 34707c3f40dfa20c3902b807b627d420d6d474d9d98066ba637953d1cfd6b914 == egg

    test_file_1 = HashedFile.from_hash("34707c3f40dfa20c3902b807b627d420d6d474d9d98066ba637953d1cfd6b914", tmpdir)
    test_content_1 = test_file_1.read()
    assert test_content_1 != "egg"

    test_file_2 = HashedFile.from_data("egg", tmpdir)
    assert test_file_1.file_hash == test_file_2.file_hash
    assert test_file_1.full_path == test_file_2.full_path
    assert test_content_1 != test_file_2.read()

