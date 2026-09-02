"""Pytest collection policy for retained historical verification programs."""

# This file is itself retained byte-for-byte as S1 evidence. Its tests replay a
# staged-index transition against the historical f8b32ef base and therefore are
# not a valid live-tree trial on the S2 candidate. The adjacent historical test
# verifies its bytes, schema, package, and canonical recorded aggregates.
collect_ignore = ["test_dark_medium_response_atlas_successor_overlay.py"]
