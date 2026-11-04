"""Keep homepage email exposure limited to the Contact section."""

import unittest

import update_academic_site as site


class ContactUpdateTests(unittest.TestCase):
    def test_homepage_hero_links_to_contact_without_exposing_email(self):
        hero = site.home_body().split("</section>", 1)[0]
        self.assertIn('href="#contact">Contact</a>', hero)
        self.assertNotIn(site.CURRENT_EMAIL, hero)
        self.assertNotIn("mailto:", hero)

    def test_homepage_keeps_one_work_email_with_research_scope(self):
        body = site.home_body()
        contact = body.split('id="contact"', 1)[1]
        self.assertEqual(body.count(f'href="mailto:{site.CURRENT_EMAIL}"'), 1)
        self.assertIn(f'Work email: <a href="mailto:{site.CURRENT_EMAIL}">', contact)
        for topic in ("research collaborations", "academic enquiries", "DFTB",
                      "metal-halide perovskites", "machine-learning interatomic potentials",
                      "or related topics", "collaborations with experimental researchers"):
            self.assertIn(topic, contact)


if __name__ == "__main__":
    unittest.main()
