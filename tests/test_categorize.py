"""Tests for the scoring categorizer.

Every regression case here is a real misfiling observed in a 90-artifact
library after three months of daily use — see tasks/v0.8-usage-fixes.md.
The old categorizer matched keywords as bare substrings and returned the
first category in dict order, which produced all of them.
"""
import pytest

from artifold import config, scan

CATS = config.DEFAULT_CATEGORIES


def cat(name="", intent="", body=""):
    return scan._categorize(
        {"name": name, "intent": intent, "body": body}, CATS)


# --- word boundaries -------------------------------------------------------

@pytest.mark.parametrize("body, trap", [
    ("chicago can wait until saturday", "'ai' inside 'wait'"),
    ("the chairman said so", "'ai' inside 'chairman'"),
    ("ctrl+alt+heal", "'rl' inside 'ctrl'"),
    ("index.html rendering notes", "'ml ' inside 'html '"),
    ("a preview of the post", "'review' inside 'preview'"),
    ("the same history repeats", "'story' inside 'history'"),
])
def test_substrings_no_longer_fire(body, trap):
    assert cat(body=body) == "Other", trap


def test_whole_word_two_letter_keywords_still_match():
    # Boundaries kill the false positives without disarming short keywords.
    assert cat(name="ml-theory-cheatsheet") == "Engineering"
    assert cat(name="rl-vs-sft-ppo-dpo") == "Engineering"


def test_phrase_keywords_match_as_phrases():
    assert cat(name="credit-card-strategy") == "Finance"
    # ...and the bare word no longer drags unrelated artifacts into Finance
    assert cat(name="scalp-routine-card") == "Health"


# --- best match wins, not first dict key -----------------------------------

def test_strongest_signal_wins_over_dict_order():
    # 'ml'/'engineer' used to win purely because Engineering was declared
    # before Career, filing the user's own resume under Engineering.
    assert cat(name="resume resume", body="Shubham Goel · ML Engineer",
               intent="Visual resume page, senior ML engineer, job search") \
        == "Career"


def test_repeats_reinforce():
    assert cat(name="health-plan-audit",
               body="health plan comparison health plan audit") == "Health"


# --- field weighting -------------------------------------------------------

def test_path_outranks_a_metaphor_in_the_body():
    # "with engineering analogies" is how the page explains itself, not what
    # it is about. The directory names the subject.
    assert cat(name="health-plan how-rhapsido-works",
               intent="Visual explainer of how Rhapsido blocks mast cell "
                      "activation, with engineering analogies") == "Health"


def test_directory_carries_generically_named_files():
    assert cat(name="strength-training tracker") == "Health"
    assert cat(name="sf-apartment-hunt report") == "Housing"
    assert cat(name="interview-prep index") == "Career"


# --- format words are not subjects -----------------------------------------

@pytest.mark.parametrize("name, expected", [
    ("ml-job-application-tracker", "Career"),    # was Health, via 'tracker'
    ("supplement-review", "Health"),             # was Career, via 'review'
    ("premature-greying-scalp-plan", "Health"),  # was Personal, via 'story'
    ("chicago-uiuc-st-louis-itinerary", "Travel"),
])
def test_shape_words_do_not_decide_category(name, expected):
    assert cat(name=name) == expected


# --- intent feeds the decision ---------------------------------------------

def test_intent_is_used_when_the_name_is_opaque():
    assert cat(name="2026-07-06-abc-xyz") == "Other"
    assert cat(name="2026-07-06-abc-xyz",
               intent="Six-day road trip itinerary as a postcard set") \
        == "Travel"


def test_conceit_and_intent_share_the_intent_field():
    # scan.py concatenates provenance intent + conceit into one field.
    assert cat(name="untitled",
               intent=" vLLM is a tiny operating system for the GPU") \
        == "Engineering"


# --- degenerate input ------------------------------------------------------

def test_no_signal_is_other():
    assert cat() == "Other"
    assert cat(name="", intent="", body="") == "Other"
    assert cat(name="2026-07-06-wc26-sticker-album") == "Other"


def test_empty_and_punctuation_only_keywords_are_ignored():
    assert scan._categorize({"name": "anything"}, {"Bogus": ["", "  ", "--"]}) \
        == "Other"


def test_missing_fields_do_not_raise():
    assert scan._categorize({}, CATS) == "Other"
    assert scan._categorize({"name": None}, CATS) == "Other"


def test_user_categories_merge_over_defaults():
    cats = {**CATS, "Legal": ["visa", "immigration", "green card"]}
    assert scan._categorize({"name": "eb1-or-bust green-card-process"},
                            cats) == "Legal"


# --- scoring internals -----------------------------------------------------

def test_longer_keywords_outweigh_shorter_ones():
    assert scan._kw_weight(["ml"]) < scan._kw_weight(["engineer"])


def test_phrases_score_above_a_single_word_of_the_same_length():
    assert scan._kw_weight(["credit", "card"]) > scan._kw_weight(["creditcard"])


def test_occurrences_counts_whole_phrases_only():
    toks = ["a", "credit", "card", "b", "credit", "card"]
    assert scan._occurrences(toks, ["credit", "card"]) == 2
    assert scan._occurrences(toks, ["card", "credit"]) == 0   # order matters
    assert scan._occurrences(toks, ["cred"]) == 0             # not a prefix match
    assert scan._occurrences(["a"], ["a", "b"]) == 0
    assert scan._occurrences([], ["a"]) == 0
