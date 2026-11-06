import json

from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from utils.test_utils import *

from ..globals import *
from ..models import *
from MangaPageApp.tests.base_test import ChapterBaseTestCase
from PortfolioPageApp.tests.base_test import PortfolioBaseTestCase
from django.conf import settings
from magnam.storage import file_storage


fast_creation_dict = {
    "portfolio_submits": [],
    "chapter_submits": [],
    "portfolio_wins": [],
    "chapter_wins": [],
}


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class CompetitionTagBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "CompetitionPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_label_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        label = predefined_vals.get("label", self.get_random_label_value(seed=seed))

        original_vals = {"label": label}

        vals_to_send_request = original_vals.copy()
        vals_to_create_from = original_vals.copy()

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        tag = CompetitionTag.objects.create(**vals_to_create_from)

        return original_vals, vals_to_send_request, vals_to_create_from, tag

    def assert_db_stored_values_match_expected_dict(
        self, tag: CompetitionTag, original_vals: dict
    ):
        self.assertEqual(tag.label, original_vals["label"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_tag: dict, tag: CompetitionTag
    ):
        self.assertEqual(retrieved_tag["id"], tag.id)
        self.assertEqual(retrieved_tag["label"], tag.label)


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class CompetitionBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "CompetitionPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_title_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_description_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_image_value(
        self,
        W=COMPETITION_IMAGE_MIN_W,
        H=COMPETITION_IMAGE_MIN_H,
        target_size_bytes=COMPETITION_IMAGE_MAX_SIZE / 10,
        ext="png",
        seed=None,
    ):
        return get_dummy_file(
            W=W, H=H, target_size_bytes=target_size_bytes, ext=ext, seed=seed
        )

    def get_random_links_value(self, L=10, seed=None):
        return [
            f"https://{get_dummy_text_string(L=L, seed = seed+i if seed else None)}"
            for i in range(L)
        ]

    def get_random_start_date_value(self, seed=None):
        random_days = random.Random(seed).randint(
            0, 14
        )  # random day from next two week
        return timezone.now().date() + timezone.timedelta(days=random_days)

    def get_random_end_date_value(self, seed=None):
        random_days = random.Random(seed).randint(
            15, 30
        )  # random day from last 2 weeks of next month
        return timezone.now().date() + timezone.timedelta(days=random_days)

    def get_random_price_value(self, seed=None):
        return random.Random(seed).randint(1, 1000)

    def get_random_tags_value(self, count=3, seed=None):
        tag_tester = CompetitionTagBaseTestCase()
        tags = []
        for i in range(count):
            _, _, _, tag = tag_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )
            tags.append(tag)
        return tags

    def get_random_chapter_submits_value(self, count=1, seed=None):
        chapter_tester = ChapterBaseTestCase()
        chapters = []
        for i in range(count):
            _, _, _, chapter = chapter_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )
            chapters.append(chapter)
        return chapters

    def get_random_portfolio_submits_value(self, count=1, seed=None):
        portfolio_tester = PortfolioBaseTestCase()
        portfolios = []
        for i in range(count):
            _, _, _, portfolio = portfolio_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )
            portfolios.append(portfolio)
        return portfolios

    def get_random_chapter_wins_value(self, count=1, seed=None):
        chapter_tester = ChapterBaseTestCase()
        chapters = []
        for i in range(count):
            _, _, _, chapter = chapter_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )
            chapters.append(chapter)
        return chapters

    def get_random_portfolio_wins_value(self, count=1, seed=None):
        portfolio_tester = PortfolioBaseTestCase()
        portfolios = []
        for i in range(count):
            _, _, _, portfolio = portfolio_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )
            portfolios.append(portfolio)
        return portfolios

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        title = predefined_vals.get("title", self.get_random_title_value(seed=seed))
        description = predefined_vals.get(
            "description", self.get_random_description_value(seed=seed)
        )
        image = predefined_vals.get("image", self.get_random_image_value(seed=seed))
        links = predefined_vals.get("links", self.get_random_links_value(seed=seed))
        start_date = predefined_vals.get(
            "start_date", self.get_random_start_date_value()
        )
        end_date = predefined_vals.get("end_date", self.get_random_end_date_value())
        price = predefined_vals.get("price", self.get_random_price_value(seed=seed))
        tags = (
            predefined_vals["tags"]
            if "tags" in predefined_vals
            else self.get_random_tags_value(seed=seed)
        )
        chapter_submits = (
            predefined_vals["chapter_submits"]
            if "chapter_submits" in predefined_vals
            else self.get_random_chapter_submits_value(seed=seed)
        )
        portfolio_submits = (
            predefined_vals["portfolio_submits"]
            if "portfolio_submits" in predefined_vals
            else self.get_random_portfolio_submits_value(seed=seed)
        )
        chapter_wins = (
            predefined_vals["chapter_wins"]
            if "chapter_wins" in predefined_vals
            else self.get_random_chapter_wins_value(seed=seed)
        )
        portfolio_wins = (
            predefined_vals["portfolio_wins"]
            if "portfolio_wins" in predefined_vals
            else self.get_random_portfolio_wins_value(seed=seed)
        )

        original_vals = {
            "title": title,
            "description": description,
            "image": image,
            "links": links,
            "start_date": start_date,
            "end_date": end_date,
            "price": price,
            "tags": [t.id for t in tags],
            "chapter_submits": [c.id for c in chapter_submits],
            "portfolio_submits": [p.id for p in portfolio_submits],
            "chapter_wins": [c.id for c in chapter_wins],
            "portfolio_wins": [p.id for p in portfolio_wins],
        }

        vals_to_send_request = original_vals.copy()
        vals_to_send_request["links"] = json.dumps(vals_to_send_request["links"])

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["links"] = json.dumps(vals_to_create_from["links"])
        vals_to_create_from["tags"] = tags
        vals_to_create_from["chapter_submits"] = chapter_submits
        vals_to_create_from["portfolio_submits"] = portfolio_submits
        vals_to_create_from["chapter_wins"] = chapter_wins
        vals_to_create_from["portfolio_wins"] = portfolio_wins

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        tags = vals_to_create_from.pop("tags")
        chapter_submits = vals_to_create_from.pop("chapter_submits")
        portfolio_submits = vals_to_create_from.pop("portfolio_submits")
        chapter_wins = vals_to_create_from.pop("chapter_wins")
        portfolio_wins = vals_to_create_from.pop("portfolio_wins")

        competition = Competition.objects.create(**vals_to_create_from)

        competition.tags.set(tags)
        competition.chapter_submits.set(chapter_submits)
        competition.portfolio_submits.set(portfolio_submits)
        competition.chapter_wins.set(chapter_wins)
        competition.portfolio_wins.set(portfolio_wins)
        competition.save()

        vals_to_create_from["tags"] = tags
        vals_to_create_from["chapter_submits"] = chapter_submits
        vals_to_create_from["portfolio_submits"] = portfolio_submits
        vals_to_create_from["chapter_wins"] = chapter_wins
        vals_to_create_from["portfolio_wins"] = portfolio_wins

        return (original_vals, vals_to_send_request, vals_to_create_from, competition)

    def assert_database_image(self, competition: Competition):
        self.assertTrue(file_storage.exists(competition.image.name))

        self.assertTrue(
            competition.image.name.startswith(
                f"{settings.COMPETITIONS_MEDIA_FOLDERNAME}/"
            )
        )

    def assert_db_tags(self, retrieved_tags, expected_tags):
        tag_tester = CompetitionTagBaseTestCase()

        self.assertEqual(len(retrieved_tags), len(expected_tags))

        for retrieved_tag in retrieved_tags:
            expected_tag = next(
                (e for e in expected_tags if e.id == retrieved_tag["id"]), None
            )

            self.assertIsNotNone(expected_tag)

            tag_tester.assert_db_retrieved_dict_match_db_stored_values(
                retrieved_tag, expected_tag
            )

    def assert_db_chapters(self, retrieved_chapters, expected_chapters):
        self.assertEqual(
            set([c["id"] for c in retrieved_chapters]),
            set([c.id for c in expected_chapters]),
        )

    def assert_db_portfolios(self, retrieved_portfolios, expected_portfolios):
        self.assertEqual(
            set([p["id"] for p in retrieved_portfolios]),
            set([p.id for p in expected_portfolios]),
        )

    def assert_db_stored_values_match_expected_dict(
        self, competition: Competition, original_vals: dict
    ):
        self.assertEqual(competition.title, original_vals["title"])
        self.assertEqual(competition.description, original_vals["description"])
        self.assertEqual(competition.links, original_vals["links"])
        self.assertEqual(competition.start_date, original_vals["start_date"])
        self.assertEqual(competition.end_date, original_vals["end_date"])
        self.assertEqual(competition.price, original_vals["price"])
        self.assertEqual(
            set([t.id for t in competition.tags.all()]), set(original_vals["tags"])
        )
        self.assertEqual(
            set([c.id for c in competition.chapter_submits.all()]),
            set(original_vals["chapter_submits"]),
        )
        self.assertEqual(
            set([p.id for p in competition.portfolio_submits.all()]),
            set(original_vals["portfolio_submits"]),
        )
        self.assertEqual(
            set([c.id for c in competition.chapter_wins.all()]),
            set(original_vals["chapter_wins"]),
        )
        self.assertEqual(
            set([p.id for p in competition.portfolio_wins.all()]),
            set(original_vals["portfolio_wins"]),
        )

        self.assert_database_image(competition)

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_competition: dict, competition: Competition
    ):
        self.assertEqual(retrieved_competition["id"], competition.id)
        self.assertEqual(retrieved_competition["title"], competition.title)
        self.assertEqual(retrieved_competition["description"], competition.description)
        self.assertEqual(retrieved_competition["links"], competition.links)
        self.assertEqual(
            retrieved_competition["start_date"], str(competition.start_date)
        )
        self.assertEqual(retrieved_competition["end_date"], str(competition.end_date))
        self.assertEqual(retrieved_competition["price"], competition.price)
        self.assertTrue(retrieved_competition["image"] != "")
        self.assertIn(str(competition.image), retrieved_competition["image"])

        self.assert_db_tags(retrieved_competition["tags"], list(competition.tags.all()))

        self.assert_db_chapters(
            retrieved_competition["chapter_submits"],
            list(competition.chapter_submits.all()),
        )
        self.assert_db_portfolios(
            retrieved_competition["portfolio_submits"],
            list(competition.portfolio_submits.all()),
        )
        self.assert_db_chapters(
            retrieved_competition["chapter_wins"], list(competition.chapter_wins.all())
        )
        self.assert_db_portfolios(
            retrieved_competition["portfolio_wins"],
            list(competition.portfolio_wins.all()),
        )

    def assert_gallery_retrieved_dict_match_db_stored_values(
        self, retrieved_competition: dict, competition: Competition
    ):
        self.assertEqual(retrieved_competition["id"], competition.id)
        self.assertEqual(retrieved_competition["title"], competition.title)
        self.assertTrue(retrieved_competition["image"] != "")
        self.assertIn(str(competition.image), retrieved_competition["image"])
        self.assertEqual(
            retrieved_competition["start_date"], str(competition.start_date)
        )
        self.assertEqual(retrieved_competition["end_date"], str(competition.end_date))
        self.assertEqual(retrieved_competition["price"], competition.price)

        self.assert_db_tags(retrieved_competition["tags"], list(competition.tags.all()))

        self.assertEqual(
            retrieved_competition["num_of_chapter_submits"],
            len(list(competition.chapter_submits.all())),
        )
        self.assertEqual(
            retrieved_competition["num_of_portfolio_submits"],
            len(list(competition.portfolio_submits.all())),
        )
