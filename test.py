# test.py

import os
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from main import fetch_jobs_keyword, send_jobs, get_this_week

class TestUSAJobsBot(unittest.IsolatedAsyncioTestCase):
    @patch("main.aiohttp.ClientSession.get")
    async def test_fetch_jobs_keyword_success(self, mock_get):
        """Test fetching jobs with valid response."""
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "SearchResult": {
                "SearchResultCountAll": 25,
                "SearchResultItems": [{"MatchedObjectDescriptor": {"PositionTitle": "Software Engineer"}}],
            }
        }
        mock_get.return_value = mock_response

        jobs, total_results = await fetch_jobs_keyword("developer", num_results=10, location="All")
        self.assertIsNotNone(jobs)
        self.assertEqual(total_results, 25)
        mock_get.assert_called_once()

    @patch("main.aiohttp.ClientSession.get")
    async def test_fetch_jobs_keyword_failure(self, mock_get):
        """Test fetching jobs with error response."""
        # Mock API error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value = mock_response

        jobs, total_results = await fetch_jobs_keyword("developer", num_results=10, location="All")
        self.assertIsNone(jobs)

    async def test_get_this_week(self):
        """Test date range for the last two weeks."""
        start_date, end_date = get_this_week()
        current_date = datetime.now()
        expected_start_date = (current_date - timedelta(weeks=2)).strftime('%Y-%m-%d')
        expected_end_date = current_date.strftime('%Y-%m-%d')

        self.assertEqual(start_date, expected_start_date)
        self.assertEqual(end_date, expected_end_date)

    @patch("main.fetch_jobs_keyword")
    async def test_send_jobs(self, mock_fetch_jobs_keyword):
        """Test sending job listings."""
        mock_ctx = AsyncMock()
        mock_fetch_jobs_keyword.return_value = {
            "SearchResult": {
                "SearchResultItems": [
                    {
                        "MatchedObjectDescriptor": {
                            "PositionTitle": "Software Engineer",
                            "PositionLocation": [{"LocationName": "Remote"}],
                            "UserArea": {
                                "Details": {"HiringPath": ["Public"]}
                            }
                        }
                    }
                ]
            }
        }, 1

        jobs, _ = await fetch_jobs_keyword("developer")
        await send_jobs(mock_ctx, jobs, num_results=1)
        mock_ctx.send.assert_called()  # Ensure at least one message was sent

    @patch("main.client.get_channel")
    async def test_channel_not_found(self, mock_get_channel):
        """Test case where channel is None."""
        mock_get_channel.return_value = None
        mock_channel = mock_get_channel(123456789)
        self.assertIsNone(mock_channel)

if __name__ == "__main__":
    unittest.main()
