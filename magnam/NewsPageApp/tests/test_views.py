from django.urls import reverse
from ..models import *
from .base_test import NewsBaseTestCase
from utils.test_utils import update_and_assert_single_field
from magnam.storage import file_storage

# NewsView
# GetNewsView
# NewsCarouselView
class TestRetrieveNews(NewsBaseTestCase):
    def test_guest_can_retrieve_single_news(self):
        _, _, _, news = self.create_random_valid_object()
        self.client.logout()  # guest should be able to retrieve

        url = reverse(f"{self.namespace}:get-news", kwargs={"news_id": news.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"], news
        )

    def test_guest_can_retrieve_news_carousel(self):
        # Create a second news item for carousel len check
        _, _, _, news1 = self.create_random_valid_object()
        _, _, _, news2 = self.create_random_valid_object()

        self.client.logout()  # guest should be able to retrieve
        url = reverse(f"{self.namespace}:news-carousel")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data
        self.assertEqual(len(results), 2)

        self.assert_db_retrieved_dict_match_db_stored_values(results[1], news1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], news2)

    def test_admin_can_retrieve_news_list(self):
        self.client.force_authenticate(user=self.admin)

        # 2. Create a second news item to verify it retrieves total of 2 news
        _, _, _, news1 = self.create_random_valid_object()
        _, _, _, news2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:news")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        results = response.data
        self.assertEqual(len(results), 2)

        self.assert_db_retrieved_dict_match_db_stored_values(results[1], news1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], news2)

    def test_logged_in_user_cannot_retrieve_news_list(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:news")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreateNewsView
class TestCreateNewsView(NewsBaseTestCase):
    def test_admin_can_create_news(self):
        self.client.force_authenticate(user=self.admin)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data()

        url = reverse(f"{self.namespace}:create-news")
        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)

        # check if values stored in the db matches the ones we want
        news = News.objects.first()
        self.assert_db_stored_values_match_expected_dict(news, original_vals)

    def test_logged_in_user_cannot_create_news(self):
        self.client.force_authenticate(user=self.user)

        _, vals_to_send_request, _ = self.get_random_valid_data()
        url = reverse(f"{self.namespace}:create-news")
        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(News.objects.count(), 0)


# EditNewsView
class TestEditNewsView(NewsBaseTestCase):
    def test_admin_can_update_news(self):
        self.client.force_authenticate(user=self.admin)

        # create an object to modfiy later
        _, _, _, news = self.create_random_valid_object()
        # create new random values to modify the fields with and then check with
        original_vals, vals_to_send_request, _ = self.get_random_valid_data()
        url = reverse(f"{self.namespace}:edit-news", kwargs={"news_id": news.id})

        # check single field updates
        update_and_assert_single_field(
            tester=self,
            instance=news,
            update_api_url=url,
            field_to_update="title",
            new_field_value=vals_to_send_request["title"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["title"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=news,
            update_api_url=url,
            field_to_update="description",
            new_field_value=vals_to_send_request["description"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["description"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=news,
            update_api_url=url,
            field_to_update="links",
            new_field_value=vals_to_send_request["links"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["links"]
            ),
        )
        old_image_path = news.image.name
        update_and_assert_single_field(
            tester=self,
            instance=news,
            update_api_url=url,
            field_to_update="image",
            new_field_value=vals_to_send_request["image"],
            field_assertion_function=lambda actual: (
                self.assert_database_image(news),
                self.assertFalse(file_storage.exists(old_image_path)),
            ),
        )
        # update all fields
        original_vals, vals_to_send_request, _ = self.get_random_valid_data()
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 200)
        news.refresh_from_db()
        # check if values stored in the db matches the ones we want
        self.assert_db_stored_values_match_expected_dict(news, original_vals)

    def test_admin_cannot_update_non_existing_news(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:edit-news", kwargs={"news_id": 0})

        _, vals_to_send_request, _ = self.get_random_valid_data()
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 404)

    def test_logged_in_user_cannot_edit_news(self):
        # create a news to edit later
        _, _, _, news = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(f"{self.namespace}:edit-news", kwargs={"news_id": news.id})

        new_title = self.get_random_title_value()
        response = self.client.patch(url, {"title": new_title})

        self.assertEqual(response.status_code, 403)
        news.refresh_from_db()
        self.assertNotEqual(news.title, new_title)


# DeleteNewsView
class TestDeleteNewsView(NewsBaseTestCase):
    def test_admin_can_delete_news(self):
        self.client.force_authenticate(user=self.admin)

        # create news to delete later
        _, _, _, news = self.create_random_valid_object()
        news_id = news.id
        image_path = news.image.name  # Store path to verify file deletion

        url = reverse(f"{self.namespace}:delete-news", kwargs={"news_id": news_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(News.objects.filter(id=news_id).exists())
        self.assertFalse(file_storage.exists(image_path))

    def test_admin_cannot_delete_non_existing_news(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:delete-news", kwargs={"news_id": 0})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_logged_in_user_cannot_delete_news(self):
        # create a news to delete later
        _, _, _, news = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(f"{self.namespace}:delete-news", kwargs={"news_id": news.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(News.objects.filter(id=news.id).exists())
