import unittest
from unittest.mock import patch

import opportunity
import opportunity_ai


class GeneralSourceTests(unittest.TestCase):
    def test_devglobaljobs_preserves_nonremote_details_without_guessing_remote(self):
        job = opportunity._devglobaljobs_job({
            "title": "Office Administrator",
            "organisation": {"name": "Example Clinic"},
            "location": "Abuja, Nigeria",
            "country": "Nigeria",
            "posted_at": "2026-10-18T10:00:00Z",
            "description": "<p>Maintain records and schedule appointments.</p>",
            "salary": "NGN 150,000/month",
            "url": "https://devglobaljobs.com/jobs/office-admin",
        })
        self.assertIsNotNone(job)
        self.assertEqual(job["title"], "Office Administrator")
        self.assertEqual(job["company"], "Example Clinic")
        self.assertEqual(job["location"], "Abuja, Nigeria")
        self.assertEqual(job["remote_status"], "unknown")
        self.assertEqual(job["salary_text"], "NGN 150,000/month")
        self.assertEqual(job["source_id"], "devglobaljobs")

    def test_devglobaljobs_handles_explicit_onsite_role(self):
        job = opportunity._devglobaljobs_job({
            "title": "Receptionist",
            "company": "Example School",
            "location": "Lagos, Nigeria",
            "remote": False,
            "url": "https://devglobaljobs.com/jobs/receptionist",
        })
        self.assertEqual(job["remote_status"], "onsite")

    def test_general_source_is_registered(self):
        self.assertIn("devglobaljobs", opportunity.SOURCE_RUNNERS)
        self.assertEqual(opportunity_ai.GENERAL_SOURCES, ["devglobaljobs", "arbeitnow-eu", "arbeitnow-uk"])


class OpportunityBrainHelperTests(unittest.TestCase):
    def test_distinct_employers_ignores_missing_names_and_duplicates(self):
        jobs = [
            {"company": "Example Limited"},
            {"company": "Example Limited"},
            {"company": "example limited"},
            {"company": "Company not listed"},
            {"company": "Other School"},
        ]
        self.assertEqual(
            opportunity_ai.distinct_employers(jobs),
            ["Example Limited", "Other School"],
        )

    def test_free_mode_never_uses_a_first_scan_keyword(self):
        args = type("Args", (), {
            "mode": "free", "request": "Data entry automation",
            "days": None, "location": None, "count": 5, "min_companies": 5
        })()
        with patch.object(opportunity_ai, "call_brain", return_value={
            "industry_focus": "data entry", "initial_query": "data entry clerk",
            "days": 12, "location": "Nigeria", "goal": "Find automations",
        }):
            plan = opportunity_ai.plan_search(args)
        self.assertEqual(plan["initial_query"], "")
        self.assertEqual(plan["days"], 12)
        self.assertEqual(plan["location"], "Nigeria")

    def test_qualification_uses_computed_employer_count(self):
        idea = {
            "name": "Spreadsheet cleanup assistant",
            "problem": "Repetitive data cleanup",
            "product_idea": "A guided spreadsheet helper",
            "ideal_customer": "Small businesses",
            "validation_query": "spreadsheet data entry",
            "difficulty": 2,
            "resource_level": "low",
            "nontechnical_friendly": True,
            "build_plan": "Upload sheet and validate fields",
            "why_it_may_sell": "Repeated manual workflow",
            "evidence_job_urls": [],
        }
        fake_report = {
            "results": [
                {"company": "Employer A", "job_url": "https://example.com/a"},
                {"company": "Employer B", "job_url": "https://example.com/b"},
                {"company": "Employer C", "job_url": "https://example.com/c"},
            ],
            "sources": [],
        }
        with patch.object(opportunity_ai.opportunity, "search_jobs", return_value=fake_report):
            result = opportunity_ai.validate_idea(
                idea, days=14, location=None, min_companies=3,
                max_difficulty=3, max_results=80,
            )
        self.assertTrue(result["qualification"]["qualified"])
        self.assertEqual(result["distinct_employer_count"], 3)


    def test_batch_review_requires_relevant_targeted_evidence(self):
        result = {
            "name": "Spreadsheet cleanup helper",
            "problem": "Staff manually reconcile spreadsheet records",
            "product_idea": "A guided spreadsheet validation tool",
            "validation_query": "spreadsheet data reconciliation",
            "difficulty": 2,
            "resource_level": "low",
            "nontechnical_friendly": True,
            "distinct_employer_count": 5,
            "distinct_employers": ["A Ltd", "B Ltd", "C Ltd", "D Ltd", "E Ltd"],
            "listing_count": 5,
            "evidence": [
                {"company": "A Ltd", "title": "Data Clerk", "summary": "Reconcile daily spreadsheet records."}
            ],
            "qualification": {
                "qualified": True,
                "employer_threshold_met": True,
                "difficulty_threshold_met": True,
                "resource_threshold_met": True,
                "nontechnical_friendly": True,
            },
            "status": "qualified",
        }
        response = {
            "reviews": [{
                "name": "Spreadsheet cleanup helper",
                "problem_confirmed": True,
                "demand_signal": "moderate",
                "reasoning": "The targeted results repeatedly describe manual record reconciliation.",
                "next_step": "Interview two office managers.",
            }]
        }
        with patch.object(opportunity_ai, "call_brain", return_value=response):
            reviewed = opportunity_ai.review_validation_batch(
                [result], {"industry_focus": "office admin", "location": "Nigeria", "days": 14},
                min_companies=5, max_difficulty=3,
            )
        self.assertTrue(reviewed[0]["qualification"]["qualified"])
        self.assertTrue(reviewed[0]["qualification"]["ai_evidence_review_passed"])

    def test_missing_brain_review_fails_closed(self):
        result = {
            "name": "Spreadsheet cleanup helper",
            "distinct_employer_count": 5,
            "distinct_employers": ["A", "B", "C", "D", "E"],
            "listing_count": 5,
            "evidence": [],
            "qualification": {"qualified": True},
            "status": "qualified",
        }
        with patch.object(opportunity_ai, "call_brain", return_value={"reviews": []}):
            reviewed = opportunity_ai.review_validation_batch(
                [result], {"industry_focus": "admin", "location": None, "days": 14},
                min_companies=5, max_difficulty=3,
            )
        self.assertFalse(reviewed[0]["qualification"]["qualified"])
