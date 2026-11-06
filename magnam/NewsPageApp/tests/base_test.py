import json

from django.test import TransactionTestCase, override_settings
from utils.test_utils import *
from ..globals import *
from ..models import *
from magnam.storage import file_storage


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class NewsBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "NewsPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_title_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_description_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_image_value(
        self,
        W=NEWS_IMAGE_MIN_W,
        H=NEWS_IMAGE_MIN_H,
        target_size_bytes=NEWS_IMAGE_MAX_SIZE / 10,
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

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        title = predefined_vals.get("title", self.get_random_title_value(seed=seed))
        description = predefined_vals.get(
            "description", self.get_random_description_value(seed=seed)
        )
        image = predefined_vals.get("image", self.get_random_image_value(seed=seed))
        links = predefined_vals.get("links", self.get_random_links_value(seed=seed))

        original_vals = {
            "title": title,
            "description": description,
            "image": image,
            "links": links,
        }
        vals_to_send_request = original_vals.copy()
        vals_to_send_request["links"] = json.dumps(vals_to_send_request["links"])

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["links"] = json.dumps(vals_to_create_from["links"])

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )
        news = News.objects.create(**vals_to_create_from)
        return (original_vals, vals_to_send_request, vals_to_create_from, news)

    def assert_database_image(self, news):
        self.assertTrue(file_storage.exists(news.image.name))
        self.assertTrue(
            news.image.name.startswith(f"{settings.NEWS_MEDIA_FOLDERNAME}/")
        )

    # this is used when test is id-irrelevant in cases such as:
    # creating a new object, we only want to check if fields are same with the data we expect
    # updating an object and checking the updated fields of news.refresh_from_db() object
    #   we already know its the same object since call is done via refresh_from_db, we just want to check the fields
    # in short, this checks the 'processing' of the database, it checks if 'news' db row fields matches the inputted fields
    # should be used to check if db state matches the data we want it to be stored (original_vals is ground truth)
    def assert_db_stored_values_match_expected_dict(
        self, news: News, original_vals: dict
    ):
        self.assertEqual(news.title, original_vals["title"])
        self.assertEqual(news.description, original_vals["description"])
        self.assertEqual(news.links, original_vals["links"])
        self.assert_database_image(news)

    # this is used when we want to check if retrieved object is the expected one, such as:
    # we create an object, and then we retrieve it with a carousel view
    # we create an object, and then we retrieve it with a list view
    # in short, this checks the 'retrieval' of the database, it checks if 'retrieved_news' arguman is correct
    # should be used to check if frontend state matches the data stored in the db (news is ground truth)
    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_news: dict, news: News
    ):
        self.assertEqual(retrieved_news["id"], news.id)
        self.assertEqual(retrieved_news["title"], news.title)
        self.assertEqual(retrieved_news["description"], news.description)
        self.assertEqual(retrieved_news["links"], news.links)
        # check if we retrieved an image path and correct path is inside the uri
        # we do the 'assertIn' check since
        # str(news.image) --> "settings.NEWS_MEDIA_FOLDERNAME/ca515ddadf994a2d9d46f56b4e5d7fee.png"
        # retrieved_news["image"] --> http://testserver/media/settings.NEWS_MEDIA_FOLDERNAME/ca515ddadf994a2d9d46f56b4e5d7fee.png
        self.assertTrue(retrieved_news["image"] != "")
        self.assertIn(str(news.image), retrieved_news["image"])
