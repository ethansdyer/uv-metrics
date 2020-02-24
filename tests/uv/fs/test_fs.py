"""Tests for the filesystem reader and reporter."""

import string
import uuid
from contextlib import closing

import hypothesis.strategies as st
from hypothesis import given
from uv.fs.reader import FSReader
from uv.fs.reporter import FSReporter

import pytest


def test_fs_invalid():
  """Argument must be a string or a filesystem instance."""
  with pytest.raises(ValueError):
    FSReporter(100)

  with pytest.raises(ValueError):
    FSReporter(None)


def test_fs_roundtrip(tmpdir):
  dir_path = str(tmpdir)
  with closing(FSReporter(dir_path).stepped()) as reporter:
    with closing(reporter.reader()) as reader:
      with closing(FSReader(dir_path)) as reader2:

        reporter.report_all(0, {"a": 1})
        reporter.report_all(1, {"a": 2, "b": 3})
        reporter.report_all(2, {"b": 4})

        a_entries = [{"step": 0, "value": 1}, {"step": 1, "value": 2}]
        b_entries = [{"step": 1, "value": 3}, {"step": 2, "value": 4}]

        assert reader.read("a") == a_entries
        assert reader.read("b") == b_entries

        assert reader.read_all(["a", "b"]) == {"a": a_entries, "b": b_entries}

        # Opening a reader directly has the same effect as calling reader() on
        # the reporter.
        assert reader.read_all(["a", "b"]) == reader2.read_all(["a", "b"])

        # Checking for a key that doesn't exist returns an empty list.
        assert reader.read("face") == []


@given(
    st.dictionaries(st.text(alphabet=list(string.ascii_lowercase +
                                          string.digits),
                            min_size=1),
                    st.integers(),
                    max_size=100))
def test_fs_many(tmpdir, m):
  tmp = tmpdir.mkdir(str(uuid.uuid1()))
  dir_path = str(tmp)

  with closing(FSReporter(dir_path).stepped()) as reporter:
    with closing(reporter.reader()) as reader:
      reporter.report_all(0, m)

      # round-tripping keys
      expected = {}
      for k, v in m.items():
        expected.setdefault(k, []).append({"step": 0, "value": v})

      # check that the reader returns everything in the map written to the fs.
      assert reader.read_all(list(m.keys())) == expected

      # Check that the reader has all the goods!
      assert set(reader.keys()) == set(m.keys())