from app.services.evidence import find_evidence, split_sentences


def test_split_sentences_drops_short_fragments():
    assert split_sentences("Short. This sentence is long enough to keep.") == [
        "This sentence is long enough to keep."
    ]


def test_ielts_sentence_is_found_by_keyword():
    opportunity = {
        "requirements_text": "Applicants need a strong academic record. IELTS 6.5 or equivalent is required.",
        "description": None,
        "funding": None,
    }
    evidence = find_evidence(opportunity, use_semantic=False)
    assert "IELTS" in evidence["IELTS"]["sentence"]
    assert evidence["IELTS"]["method"] == "keyword"
    assert evidence["IELTS"]["source"] == "requirements_text"


def test_missing_evidence_is_none_not_guessed():
    opportunity = {
        "requirements_text": "Apply online before the deadline.",
        "description": None,
        "funding": None,
    }
    evidence = find_evidence(opportunity, use_semantic=False)
    assert evidence["CGPA"]["sentence"] is None
    assert evidence["IELTS"]["sentence"] is None