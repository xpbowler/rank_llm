import unittest
from unittest.mock import patch, MagicMock

from src.rank_llm.result import Result
from src.rank_llm.retrieve.pyserini_retriever import PyseriniRetriever, RetrievalMethod


# Mocking Hits object
class MockHit:
    def __init__(self, docid, rank, score):
        self.docid = docid
        self.rank = rank
        self.score = score


class TestPyseriniRetriever(unittest.TestCase):
    def test_get_index(self):
        # Creating PyseriniRetriever instance
        retriever = PyseriniRetriever("dl19", RetrievalMethod.BM25)

        # Testing for a valid dataset
        index = retriever._get_index()
        self.assertEqual(index, "msmarco-v1-passage")

        # Testing for an invalid dataset
        with self.assertRaises(ValueError):
            retriever._dataset = "invalid_dataset"
            retriever._retrieval_method = RetrievalMethod.BM25_RM3
            retriever._get_index()

    @patch("src.rank_llm.retrieve.pyserini_retriever.IndexReader")
    @patch("src.rank_llm.retrieve.pyserini_retriever.json.loads")
    def test_retrieve_query(self, mock_json_loads, mock_index_reader):
        # Mocking json.loads to return a predefined content
        mock_json_loads.return_value = {"title": "Sample Title", "text": "Sample Text"}

        # Mocking IndexReader
        mock_index_reader_instance = MagicMock()
        mock_index_reader.from_prebuilt_index.return_value = mock_index_reader_instance

        # Mocking hits
        mock_hits = MagicMock(spec=list[MockHit])
        mock_hits.__iter__.return_value = [MockHit("d1", 1, 0.5), MockHit("d2", 2, 0.4)]
        # Setting up PyseriniRetriever instance
        retriever = PyseriniRetriever("dl19", RetrievalMethod.BM25)

        # Mocking the search method to return mock_hits
        retriever._searcher.search = MagicMock(return_value=mock_hits)

        # Creating lists to store expected and actual results
        expected_results = [
            Result(
                query="Sample Query",
                hits=[
                    {
                        "content": "Title: Sample Title Content: Sample Text",
                        "qid": None,
                        "docid": "d1",
                        "rank": 1,
                        "score": 0.5,
                    },
                    {
                        "content": "Title: Sample Title Content: Sample Text",
                        "qid": None,
                        "docid": "d2",
                        "rank": 2,
                        "score": 0.4,
                    },
                ],
            )
        ]
        actual_results = []

        # Calling the _retrieve_query method
        retriever._retrieve_query("Sample Query", actual_results, 2)

        # Asserting that Hits object is called with the correct query and k
        retriever._searcher.search.assert_called_once_with("Sample Query", k=2)

        # Asserting the actual results match the expected results
        self.assertEqual(actual_results.__repr__(), expected_results.__repr__())

        # Reset the mocks for clean-up
        mock_json_loads.reset_mock()
        retriever._searcher.search.reset_mock()

    @patch("src.rank_llm.retrieve.pyserini_retriever.get_topics")
    def test_num_queries(self, mock_get_topics):
        # Mocking get_topics method to return a predefined number of queries
        mock_get_topics.return_value = {
            "query1": {"title": "Sample Title 1"},
            "query2": {"title": "Sample Title 2"},
            "query3": {"title": "Sample Title 3"},
        }

        # Creating PyseriniRetriever instance
        retriever = PyseriniRetriever("dl19", RetrievalMethod.BM25)

        # Asserting the number of queries
        self.assertEqual(retriever.num_queries(), 3)

        # Reset the mock for clean-up
        mock_get_topics.reset_mock()


if __name__ == "__main__":
    unittest.main()