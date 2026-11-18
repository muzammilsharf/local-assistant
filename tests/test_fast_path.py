from unittest.mock import patch

from local_assistant.agent import detect_document_request, run_task


def test_detect_document_request_matches():
    # 1. about with multiple words
    res = detect_document_request("create a document about photosynthesis with 3 key points")
    assert res == (
        "Photosynthesis With 3 Key Points",
        "create a document about photosynthesis with 3 key points",
    )

    # 2. called with double quotes
    res = detect_document_request("write a report called \"Q3 Financials\"")
    assert res == ("Q3 Financials", "write a report called \"Q3 Financials\"")

    # 3. called without quotes, stopping before 'with'
    res = detect_document_request("write a report called Q3 Financials with highlights")
    assert res == ("Q3 Financials", "write a report called Q3 Financials with highlights")

    # 4. titled without quotes
    res = detect_document_request("make a doc titled Project Roadmap")
    assert res == ("Project Roadmap", "make a doc titled Project Roadmap")

    # 5. named with single quotes
    res = detect_document_request("create an odt named 'Meeting Minutes'")
    assert res == ("Meeting Minutes", "create an odt named 'Meeting Minutes'")

    # 6. on with multiple words
    res = detect_document_request("generate an essay on artificial intelligence ethics")
    assert res == (
        "Artificial Intelligence Ethics",
        "generate an essay on artificial intelligence ethics",
    )

    # 7. draft + summary + about
    res = detect_document_request("draft a summary about renewable energy sources")
    assert res == (
        "Renewable Energy Sources",
        "draft a summary about renewable energy sources",
    )

    # 8. prepare + notes + on
    res = detect_document_request("prepare notes on organic chemistry exam")
    assert res == (
        "Organic Chemistry Exam",
        "prepare notes on organic chemistry exam",
    )

    # 9. write + document (no topic or title, fallback to Document)
    res = detect_document_request("write a document")
    assert res == ("Document", "write a document")

    # 10. max 6 words limit for about
    res = detect_document_request(
        "make notes about python programming tips and tricks for beginners"
    )
    assert res == (
        "Python Programming Tips And Tricks For",
        "make notes about python programming tips and tricks for beginners",
    )

    # 11. draft + report + on
    res = detect_document_request("draft a report on climate change")
    assert res == ("Climate Change", "draft a report on climate change")

    # 12. prepare + summary fallback
    res = detect_document_request("prepare a summary")
    assert res == ("Document", "prepare a summary")

    # 13. create + doc + on
    res = detect_document_request("create a doc on quantum computing")
    assert res == ("Quantum Computing", "create a doc on quantum computing")

    # 14. generate + notes + titled with quotes
    res = detect_document_request("generate notes titled \"Lab Results\"")
    assert res == ("Lab Results", "generate notes titled \"Lab Results\"")

    # 15. make + essay + about
    res = detect_document_request("make an essay about space exploration")
    assert res == ("Space Exploration", "make an essay about space exploration")


def test_detect_document_request_non_matches():
    # 16. open my documents folder (no creation verb)
    assert detect_document_request("open my documents folder") is None

    # 17. what is a report (no creation verb)
    assert detect_document_request("what is a report") is None

    # 18. make coffee (no document word)
    assert detect_document_request("make coffee") is None

    # 19. write an email to alice (no document word)
    assert detect_document_request("write an email to alice") is None

    # 20. open downloads (no creation verb, no doc word)
    assert detect_document_request("open downloads") is None

    # 21. pause music (Spotify command)
    assert detect_document_request("pause music") is None

    # 22. read the notes (no creation verb)
    assert detect_document_request("read the notes") is None

    # 23. delete this document (no creation verb)
    assert detect_document_request("delete this document") is None

    # 24. how do I draft a contract (contract is not a doc word)
    assert detect_document_request("how do I draft a contract") is None

    # 25. empty string
    assert detect_document_request("") is None


def test_run_task_fast_path():
    with patch("local_assistant.agent.create_document", return_value="Created doc.odt") as mock_create, \
         patch("local_assistant.agent.ask_with_tools") as mock_llm:
        res = run_task("create a document about photosynthesis with 3 key points")
        assert res == "Created doc.odt"
        mock_create.assert_called_once_with(
            "Photosynthesis With 3 Key Points",
            "create a document about photosynthesis with 3 key points",
        )
        mock_llm.assert_not_called()
