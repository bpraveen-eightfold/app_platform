import inverted_index

idx = inverted_index.InvertedIndex("test")
assert idx.add_doc_to_index("foo bar")
assert idx.add_doc_to_index("bar baz")
assert idx.query("foo bar") == [(1, "foo bar"), (2, "bar baz")]
assert idx.query("baz bar") == [(2, "bar baz"), (1, "foo bar")]
assert idx.query("bar asdf") == [(2, "bar baz"), (1, "foo bar")]
assert idx.query("BAr asdf") == [(2, "bar baz"), (1, "foo bar")]
