"""Bhutan uses the shared Himalayan lifecycle, with independent state and IDs.

Run after Nepal. Thimphu1456 is the sole province in installed1933/bhutan.inc.
9398210-16 checked against authored/installed event trees on2026-09-10.
Initial60%/grand75% odds and original5MP/-1dissent merger rewards are preserved.
Funded retry80%; same expensive retry/integration costs and elapsed delays as Nepal.
Native inheritance, British-master consequences and queued delivery unverified.
"""
from aubm_redesign_nepal import BHUTAN, transform_country

NEW_EVENT_IDS = frozenset(range(BHUTAN.base, BHUTAN.base+7))


def transform(files):
    return transform_country(files, BHUTAN)
