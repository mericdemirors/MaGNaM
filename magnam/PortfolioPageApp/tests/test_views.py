from django.urls import reverse
from unittest.mock import patch
from ..models import *
from .base_test import *

from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from magnam.file_extension_globals import *
from pathlib import PurePosixPath


# PortfolioTagView
class TestRetrievePortfolioTagView(PortfolioTagBaseTestCase):
    def test_guest_can_retrieve_tags(self):
        self.client.logout()

        _, _, _, tag1 = self.create_random_valid_object()
        _, _, _, tag2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:portfolio-tag")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], tag1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], tag2)


# PortfolioLikeView
class TestRetrievePortfolioLikeView(PortfolioLikeBaseTestCase):
    def test_admin_can_retrieve_likes(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, like1 = self.create_random_valid_object()
        _, _, _, like2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:portfolio-like")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], like1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], like2)

    def test_logged_in_user_cannot_retrieve_likes(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:portfolio-like")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# PortfolioCommentView
class TestRetrievePortfolioCommentView(PortfolioCommentBaseTestCase):
    def test_admin_can_retrieve_comments(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, c1 = self.create_random_valid_object()
        _, _, _, c2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:portfolio-comment")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], c1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], c2)

    def test_admin_can_retrieve_comments_with_parent(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, c1 = self.create_random_valid_object()
        _, _, _, c2 = self.create_random_valid_object(
            predefined_vals={"portfolio": c1.portfolio, "parent_comment": c1}
        )

        url = reverse(f"{self.namespace}:portfolio-comment")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], c1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], c2)

    def test_logged_in_user_cannot_retrieve_comments(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:portfolio-comment")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# PortfolioView
class TestRetrievePortfolioView(PortfolioBaseTestCase):
    def test_admin_can_retrieve_portfolios(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, p1 = self.create_random_valid_object()
        _, _, _, p2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:portfolio")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], p1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], p2)

    def test_logged_in_user_cannot_retrieve_portfolios(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:portfolio")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreatePortfolioView
class TestCreatePortfolioView(PortfolioBaseTestCase):
    def test_user_can_create_portfolio(self):
        self.client.force_authenticate(user=self.user)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"owner": self.user.profile}
        )

        url = reverse(f"{self.namespace}:create-portfolio")
        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        portfolio = Portfolio.objects.first()
        self.assert_db_stored_values_match_expected_dict(portfolio, original_vals)

    def test_guest_cannot_create_portfolio(self):
        self.client.logout()

        _, vals, _ = self.get_random_valid_data()

        url = reverse(f"{self.namespace}:create-portfolio")
        response = self.client.post(url, vals)

        self.assertEqual(response.status_code, 403)


# GetPortfolioView
class TestGetPortfolioView(PortfolioBaseTestCase):
    def test_guest_can_retrieve_portfolio(self):
        _, _, _, portfolio = self.create_random_valid_object()
        self.client.logout()

        url = reverse(
            f"{self.namespace}:get-portfolio", kwargs={"portfolio_id": portfolio.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"], portfolio
        )

    def test_non_existing_portfolio_retrieval(self):
        url = reverse(f"{self.namespace}:get-portfolio", kwargs={"portfolio_id": 0})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_annotated_field_retrieval(self):
        _, _, _, portfolio = self.create_random_valid_object()
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:get-portfolio", kwargs={"portfolio_id": portfolio.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["num_of_likes"], 0)
        self.assertEqual(response.data["data"]["num_of_comments"], 0)
        self.assertEqual(response.data["data"]["is_user_liked"], False)

        # user likes it, writes 2 comment
        like_tester = PortfolioLikeBaseTestCase()
        like_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "portfolio": portfolio}
        )

        comment_tester = PortfolioCommentBaseTestCase()
        comment_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "portfolio": portfolio}
        )
        comment_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "portfolio": portfolio}
        )
        url = reverse(
            f"{self.namespace}:get-portfolio", kwargs={"portfolio_id": portfolio.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["num_of_likes"], 1)
        self.assertEqual(response.data["data"]["num_of_comments"], 2)
        self.assertEqual(response.data["data"]["is_user_liked"], True)


# EditPortfolioView
class TestEditPortfolioView(PortfolioBaseTestCase):
    def test_owner_can_update_portfolio(self):
        self.client.force_authenticate(user=self.user)

        # create an object to modfiy later
        _, _, _, portfolio = self.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        # create new random values to modify the fields with and then check with
        original_vals, vals_to_send_request, _ = self.get_random_valid_data()
        url = reverse(
            f"{self.namespace}:edit-portfolio", kwargs={"portfolio_id": portfolio.id}
        )

        update_and_assert_single_field(
            tester=self,
            instance=portfolio,
            update_api_url=url,
            field_to_update="title",
            new_field_value=vals_to_send_request["title"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["title"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=portfolio,
            update_api_url=url,
            field_to_update="description",
            new_field_value=vals_to_send_request["description"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["description"]
            ),
        )
        old_image_path = portfolio.image.name
        update_and_assert_single_field(
            tester=self,
            instance=portfolio,
            update_api_url=url,
            field_to_update="image",
            new_field_value=vals_to_send_request["image"],
            field_assertion_function=lambda actual: (
                self.assert_database_image(portfolio),
                self.assertFalse(file_storage.exists(old_image_path)),
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=portfolio,
            update_api_url=url,
            field_to_update="tags",
            new_field_value=vals_to_send_request["tags"],
            field_assertion_function=None,
        )
        # we do the assertion explicity because relational fields fail the find_different_fields check
        portfolio.refresh_from_db()
        self.assertEqual(
            set([t.id for t in portfolio.tags.all()]), set(original_vals["tags"])
        )

        # update all fields
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"owner": self.user.profile}
        )
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 200)
        portfolio.refresh_from_db()
        # check if values stored in the db matches the ones we want
        self.assert_db_stored_values_match_expected_dict(portfolio, original_vals)

    def test_admin_cannot_update_non_existing_portfolio(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:edit-portfolio", kwargs={"portfolio_id": 0})

        _, vals_to_send_request, _ = self.get_random_valid_data()
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_update_portfolio(self):
        _, _, _, portfolio = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(
            f"{self.namespace}:edit-portfolio", kwargs={"portfolio_id": portfolio.id}
        )

        new_title = self.get_random_title_value()
        response = self.client.patch(url, {"title": new_title})

        self.assertEqual(response.status_code, 403)
        portfolio.refresh_from_db()
        self.assertNotEqual(portfolio.title, new_title)


# DeletePortfolioView
class TestDeletePortfolioView(PortfolioBaseTestCase):
    def test_admin_can_delete_portfolio(self):
        # create portfolio to delete later
        _, _, _, portfolio = self.create_random_valid_object()
        portfolio_id = portfolio.id
        portfolio_folder_path = get_portfolio_upload_folder_path(portfolio)
        image_path = portfolio.image.name  # Store path to verify file deletion

        self.client.force_authenticate(user=self.admin)

        url = reverse(
            f"{self.namespace}:delete-portfolio", kwargs={"portfolio_id": portfolio_id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Portfolio.objects.filter(id=portfolio_id).exists())
        self.assertFalse(file_storage.exists(image_path))
        self.assertFalse(directory_storage.exists(portfolio_folder_path))

    def test_owner_can_delete_portfolio(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, portfolio = self.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        portfolio_id = portfolio.id
        portfolio_folder_path = get_portfolio_upload_folder_path(portfolio)
        image_path = portfolio.image.name  # Store path to verify file deletion

        url = reverse(
            f"{self.namespace}:delete-portfolio", kwargs={"portfolio_id": portfolio.id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Portfolio.objects.filter(id=portfolio_id).exists())
        self.assertFalse(file_storage.exists(image_path))
        self.assertFalse(directory_storage.exists(portfolio_folder_path))

    def test_non_existing_portfolio_delete(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:delete-portfolio", kwargs={"portfolio_id": 0})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_delete_portfolio(self):
        _, _, _, portfolio = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(
            f"{self.namespace}:delete-portfolio", kwargs={"portfolio_id": portfolio.id}
        )

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_portfolio_deletion_deletes_works(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, portfolio = self.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        work_tester = WorkBaseTestCase()

        _, _, _, work_png = work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio}
        )

        _, _, _, work_pdf = work_tester.create_random_valid_object(
            predefined_vals={
                "portfolio": portfolio,
                "work_file": work_tester.get_random_file_value(ext="pdf"),
            }
        )

        portfolio_folder_path = get_portfolio_upload_folder_path(portfolio)
        work_pdf_folder_path = get_work_upload_folder_path(work_pdf)

        url = reverse(
            f"{self.namespace}:delete-portfolio", kwargs={"portfolio_id": portfolio.id}
        )

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(directory_storage.exists(portfolio_folder_path))
        self.assertFalse(Work.objects.filter(id=work_pdf.id).exists())
        self.assertFalse(Work.objects.filter(id=work_png.id).exists())
        self.assertFalse(file_storage.exists(work_pdf.work_file.name))
        self.assertFalse(directory_storage.exists(work_pdf_folder_path))
        self.assertFalse(file_storage.exists(work_png.work_file.name))


# PortfolioGalleryView
class TestPortfolioGalleryViewPermission(PortfolioBaseTestCase):
    def test_guest_can_access_gallery(self):
        self.create_random_valid_object()
        self.client.logout()

        url = reverse(f"{self.namespace}:portfolio-gallery")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


# PortfolioGalleryView
class TestPortfolioGalleryViewExistence(PortfolioBaseTestCase):
    def test_empty_gallery_returns_204(self):
        url = reverse(f"{self.namespace}:portfolio-gallery")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 204)


# PortfolioGalleryView
class TestPortfolioGalleryViewFiltering(PortfolioBaseTestCase):
    def test_profiles_following_filtering(self):
        # create profiles
        followed_profile = self.get_random_owner_value()
        non_followed_profile = self.get_random_owner_value()

        # create portfolios for each profile
        _, _, _, followed_portfolio = self.create_random_valid_object(
            predefined_vals={"owner": followed_profile}
        )

        _, _, _, non_followed_portfolio = self.create_random_valid_object(
            predefined_vals={"owner": non_followed_profile}
        )

        # authenticated user
        self.client.force_login(self.user)

        # user follows only followed_profile
        self.user.profile.profiles_following.add(followed_profile)

        url = reverse(f"{self.namespace}:portfolio-gallery")

        # get followed profiles portfolios
        response = self.client.get(url, {"sort": "profiles_following"})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertIn(followed_portfolio.id, returned_ids)
        self.assertNotIn(non_followed_portfolio.id, returned_ids)

        # get NON followed profiles portfolios
        response = self.client.get(url, {"sort": "-profiles_following"})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(followed_portfolio.id, returned_ids)
        self.assertIn(non_followed_portfolio.id, returned_ids)

    def test_date_filtering(self):
        # create portfolios
        _, _, _, portfolio1 = self.create_random_valid_object()
        _, _, _, portfolio2 = self.create_random_valid_object()
        _, _, _, portfolio3 = self.create_random_valid_object()

        # manually override auto_now_add dates
        portfolio1.date = now().date() - timedelta(days=10)
        portfolio1.save()

        portfolio2.date = now().date() - timedelta(days=5)
        portfolio2.save()

        portfolio3.date = now().date()
        portfolio3.save()

        url = reverse(f"{self.namespace}:portfolio-gallery")

        min_date = now().date() - timedelta(days=7)
        max_date = now().date() - timedelta(days=2)

        min_dt = timezone.make_aware(
            timezone.datetime.combine(min_date, timezone.datetime.min.time())
        )
        max_dt = timezone.make_aware(
            timezone.datetime.combine(max_date, timezone.datetime.min.time())
        )
        min_ts = int(min_dt.timestamp() * 1000)
        max_ts = int(max_dt.timestamp() * 1000)

        response = self.client.get(url, {"date_min": min_ts, "date_max": max_ts})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        # portfolio1 is too old
        self.assertNotIn(portfolio1.id, returned_ids)

        # portfolio2 okay
        self.assertIn(portfolio2.id, returned_ids)

        # portfolio3 is too recent
        self.assertNotIn(portfolio3.id, returned_ids)

    def test_tag_filtering(self):
        # create reusable tags
        tag_tester = PortfolioTagBaseTestCase()

        _, _, _, tag1 = tag_tester.create_random_valid_object()
        _, _, _, tag2 = tag_tester.create_random_valid_object()
        _, _, _, tag3 = tag_tester.create_random_valid_object()

        # should be returned (contains ALL required tags)
        _, _, _, matching_portfolio = self.create_random_valid_object(
            predefined_vals={"tags": [tag1, tag2]}
        )

        # should NOT be returned (missing tag2)
        _, _, _, missing_tag_portfolio = self.create_random_valid_object(
            predefined_vals={"tags": [tag1]}
        )

        # should be returned (contains required tags + extra tag)
        _, _, _, extra_tags_portfolio = self.create_random_valid_object(
            predefined_vals={"tags": [tag1, tag2, tag3]}
        )

        url = reverse(f"{self.namespace}:portfolio-gallery")

        response = self.client.get(url, {"tags": f"{tag1.id},{tag2.id}"})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        # a. portfolio with all required tags should be returned
        self.assertIn(matching_portfolio.id, returned_ids)

        # b. portfolio missing one of the required tags should NOT be returned
        self.assertNotIn(missing_tag_portfolio.id, returned_ids)

        # c. portfolio with extra tags should still be returned
        self.assertIn(extra_tags_portfolio.id, returned_ids)

    def test_num_of_likes_filtering(self):
        _, _, _, portfolio1 = self.create_random_valid_object()
        _, _, _, portfolio2 = self.create_random_valid_object()
        _, _, _, portfolio3 = self.create_random_valid_object()

        portfolio_like_tester = PortfolioLikeBaseTestCase()
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio2}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio2}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )

        url = reverse(f"{self.namespace}:portfolio-gallery")

        response = self.client.get(url, {"num_of_likes_min": 1, "num_of_likes_max": 3})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(portfolio1.id, returned_ids)
        self.assertIn(portfolio2.id, returned_ids)
        self.assertNotIn(portfolio3.id, returned_ids)

    def test_num_of_works_filtering(self):
        _, _, _, portfolio1 = self.create_random_valid_object()
        _, _, _, portfolio2 = self.create_random_valid_object()
        _, _, _, portfolio3 = self.create_random_valid_object()

        work_tester = WorkBaseTestCase()
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio2}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio2}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )

        url = reverse(f"{self.namespace}:portfolio-gallery")

        response = self.client.get(url, {"num_of_works_min": 1, "num_of_works_max": 3})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(portfolio1.id, returned_ids)
        self.assertIn(portfolio2.id, returned_ids)
        self.assertNotIn(portfolio3.id, returned_ids)


# PortfolioGalleryView
class TestPortfolioGalleryViewSorting(PortfolioBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.portfolio1 = self.create_random_valid_object()
        _, _, _, self.portfolio2 = self.create_random_valid_object()
        _, _, _, self.portfolio3 = self.create_random_valid_object()

        # likes
        portfolio_like_tester = PortfolioLikeBaseTestCase()
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio2}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio3}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio3}
        )

        # comments
        portfolio_comment_tester = PortfolioCommentBaseTestCase()
        portfolio_comment_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio2}
        )
        portfolio_comment_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio3}
        )
        portfolio_comment_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio3}
        )

        # works
        work_tester = WorkBaseTestCase()
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio2}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio3}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": self.portfolio3}
        )

        self.url = reverse(f"{self.namespace}:portfolio-gallery")

    def get_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.data["results"]]

    def test_gallery_sorts(self):
        response = self.client.get(self.url, {"sort": "num_of_likes"})
        ids = self.get_ids(response)

        # IDs received (because we create new portfolios while generating comments etc)
        # - [1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 2, 3]
        # what we want (but we cant just do equals between two lists)
        # + [1, 2, 3]
        # so we iterate over the first one using the second ones elements
        # iterating checks the order because it 'consumes' the items that come before the one that's being iterated to
        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.portfolio3.id, self.portfolio2.id, self.portfolio1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_likes"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.portfolio1.id, self.portfolio2.id, self.portfolio3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_works"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.portfolio3.id, self.portfolio2.id, self.portfolio1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_works"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.portfolio1.id, self.portfolio2.id, self.portfolio3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.portfolio3.id, self.portfolio2.id, self.portfolio1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.portfolio1.id, self.portfolio2.id, self.portfolio3.id]
        )
        self.assertTrue(is_order_preserved)

    def test_gallery_multi_sort(self):
        _, _, _, portfolio4 = self.create_random_valid_object()

        portfolio_like_tester = PortfolioLikeBaseTestCase()
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio4}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio4}
        )

        response = self.client.get(self.url, {"sort": "num_of_likes,date"})

        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [
                portfolio4.id,
                self.portfolio3.id,
                self.portfolio2.id,
                self.portfolio1.id,
            ]
        )
        self.assertTrue(is_order_preserved)


# PortfolioGalleryView
class TestPortfolioGalleryViewRandomnessTest(PortfolioBaseTestCase):
    def test_random_sort(self):
        # create 3 portfolios
        for _ in range(3):
            _, _, _, _ = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:portfolio-gallery")

        results_list = []

        for _ in range(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            ids = [item["id"] for item in response.data["results"]]
            results_list.append(ids)

        # check if all results are identical
        all_same = all(r == results_list[0] for r in results_list)

        if all_same:
            print("randomness test failed, this is expected, so no problem")
            return  # test passes

        # if not all same: randomness works
        self.assertTrue(True)


# PortfolioGalleryView
class TestPortfolioGalleryViewPaginationTest(PortfolioBaseTestCase):
    def test_pagination_with_next_link(self):
        portfolios = []

        for i in range(6):
            _, _, _, portfolio = self.create_random_valid_object()
            portfolios.append(portfolio)

        # sort by id
        portfolios_sorted = sorted(portfolios, key=lambda x: x.id, reverse=True)

        url = reverse(f"{self.namespace}:portfolio-gallery")

        # get the first page
        response1 = self.client.get(url, {"sort": "date", "page_size": 3})
        self.assertEqual(response1.status_code, 200)

        # check if first page consists of the first 3 portfolios
        ids_page1 = [item["id"] for item in response1.data["results"]]
        expected_page1 = [t.id for t in portfolios_sorted[:3]]
        self.assertEqual(ids_page1, expected_page1)

        # use 'next' field in the response to get the second page
        next_url = response1.data["next"]
        self.assertIsNotNone(next_url)
        response2 = self.client.get(next_url)
        self.assertEqual(response2.status_code, 200)

        # check if second page consists of the second 3 portfolios
        ids_page2 = [item["id"] for item in response2.data["results"]]
        expected_page2 = [t.id for t in portfolios_sorted[3:6]]
        self.assertEqual(ids_page2, expected_page2)


# PortfolioGalleryView
class TestPortfolioGalleryViewFields(PortfolioBaseTestCase):
    def test_gallery_fields_consistency(self):
        portfolios = []

        for _ in range(5):
            _, _, _, portfolio = self.create_random_valid_object()
            portfolios.append(portfolio)

        portfolio1, portfolio2, portfolio3, portfolio4, portfolio5 = portfolios

        # likes
        portfolio_like_tester = PortfolioLikeBaseTestCase()
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio3}
        )
        portfolio_like_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio5, "profile": self.user.profile}
        )

        # comments
        portfolio_comment_tester = PortfolioCommentBaseTestCase()
        portfolio_comment_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio4}
        )
        portfolio_comment_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio5}
        )
        portfolio_comment_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio5}
        )

        # works
        work_tester = WorkBaseTestCase()
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio2}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio5}
        )
        work_tester.create_random_valid_object(
            predefined_vals={"portfolio": portfolio5}
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(f"{self.namespace}:portfolio-gallery"), {"sort": "-date"}
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        expected_portfolio_ids = {
            portfolio1.id,
            portfolio2.id,
            portfolio3.id,
            portfolio4.id,
            portfolio5.id,
        }

        # we filter the result because there are additional portfolios created while setting up the test environment
        # but we only want to test for the portfolios 1-5
        filtered_results = [
            item for item in results if item["id"] in expected_portfolio_ids
        ]

        for retrieved_item in filtered_results:
            portfolio = next(p for p in portfolios if p.id == retrieved_item["id"])
            # we check base fields differently because gallery retrieval is different than regular one
            self.assert_gallery_retrieved_dict_match_db_stored_values(
                retrieved_item, portfolio
            )

            # check counts
            expected_likes = portfolio.likes.count()
            expected_works = portfolio.works.count()

            self.assertEqual(retrieved_item["num_of_likes"], expected_likes)

            self.assertEqual(retrieved_item["num_of_works"], expected_works)

            # check user liked state
            expected_is_user_liked = portfolio.likes.filter(
                profile=self.user.profile
            ).exists()

            self.assertEqual(retrieved_item["is_user_liked"], expected_is_user_liked)


# TogglePortfolioLikeView
class TestTogglePortfolioLikeView(PortfolioBaseTestCase):
    def test_toggle(self):
        self.client.force_authenticate(user=self.user)
        # create portfolio to like
        _, _, _, p = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-portfolio-like", kwargs={"portfolio_id": p.id}
        )

        res1 = self.client.post(url)
        self.assertTrue(res1.data["data"]["liked"])
        # check if it's created correctly
        like = PortfolioLike.objects.first()
        like_id = like.id
        self.assertTrue(like.profile, self.user.profile)
        self.assertTrue(like.portfolio, p)

        res2 = self.client.post(url)
        self.assertFalse(res2.data["data"]["liked"])
        # check if its deleted
        self.assertFalse(PortfolioLike.objects.filter(id=like_id).exists())

    def test_non_existing_portfolio_like(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:toggle-portfolio-like", kwargs={"portfolio_id": 0}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_like(self):
        self.client.logout()

        _, _, _, p = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-portfolio-like", kwargs={"portfolio_id": p.id}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)


# CreatePortfolioCommentView
class TestCreatePortfolioCommentView(PortfolioCommentBaseTestCase):
    def test_guest_cannot_create_comment(self):
        self.client.logout()

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, p = portfolio_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:create-portfolio-comment", kwargs={"portfolio_id": p.id}
        )
        response = self.client.post(url, {"comment": self.get_random_comment_value()})

        self.assertEqual(response.status_code, 403)

    def test_logged_in_user_can_create_comment(self):
        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:create-portfolio-comment",
            kwargs={"portfolio_id": portfolio.id},
        )

        comment_text = self.get_random_comment_value()
        response = self.client.post(
            url, {"comment": comment_text, "parent_comment_id": -1}
        )

        self.assertEqual(response.status_code, 200)
        # we dont have the ground truth comment object so we are checking it like this
        self.assertEqual(
            response.data["data"]["profile_name"], self.user.profile.profile_name
        )
        self.assertEqual(response.data["data"]["comment"], comment_text)
        self.assertEqual(response.data["data"]["parent_comment_id"], None)

    def test_logged_in_user_can_reply(self):
        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object()
        _, _, _, parent_comment = self.create_random_valid_object(
            predefined_vals={"portfolio": portfolio}
        )

        url = reverse(
            f"{self.namespace}:create-portfolio-comment",
            kwargs={"portfolio_id": portfolio.id},
        )

        comment_text = self.get_random_comment_value()
        response = self.client.post(
            url, {"comment": comment_text, "parent_comment_id": parent_comment.id}
        )

        self.assertEqual(response.status_code, 200)
        # we dont have the ground truth comment object so we are checking it like this
        self.assertEqual(
            response.data["data"]["profile_name"], self.user.profile.profile_name
        )
        self.assertEqual(response.data["data"]["comment"], comment_text)
        self.assertEqual(response.data["data"]["parent_comment_id"], parent_comment.id)

    def test_non_existing_portfolio_comment_create(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:create-portfolio-comment", kwargs={"portfolio_id": 0}
        )

        response = self.client.post(url, {"comment": self.get_random_comment_value()})

        self.assertEqual(response.status_code, 404)


# GetPortfolioCommentsView
class TestGetPortfolioCommentsView(PortfolioCommentBaseTestCase):
    def test_parent_comment_retrieval(self):
        # create parent comment
        _, _, _, comment1 = self.create_random_valid_object()

        # create child comment under same portfolio
        _, _, _, comment2 = self.create_random_valid_object(
            predefined_vals={
                "portfolio": comment1.portfolio,
                "parent_comment": comment1,
            }
        )

        # send request
        url = reverse(
            f"{self.namespace}:get-portfolio-comments",
            kwargs={"portfolio_id": comment1.portfolio.id},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        results = response.data["data"]["results"]

        # should retrieve both parent + child comments
        self.assertEqual(len(results), 2)

        # map by id for easier assertions
        retrieved_comments = {c["id"]: c for c in results}

        # validate parent comment integrity
        self.assert_db_retrieved_dict_match_db_stored_values(
            retrieved_comments[comment1.id], comment1
        )

        # validate child comment integrity
        self.assert_db_retrieved_dict_match_db_stored_values(
            retrieved_comments[comment2.id], comment2
        )

        # explicitly verify parent pointer
        self.assertEqual(
            retrieved_comments[comment2.id]["parent_comment_id"], comment1.id
        )

    def test_cursor_and_pagination(self):
        NEW_LIMIT = 2
        with patch(
            "PortfolioPageApp.views.GetPortfolioCommentsView.PAGE_SIZE", NEW_LIMIT
        ):
            portfolio_tester = PortfolioBaseTestCase()
            _, _, _, portfolio = portfolio_tester.create_random_valid_object()

            # comment1 -> parent (out of pagination scope)
            _, _, _, comment1 = self.create_random_valid_object(
                predefined_vals={"portfolio": portfolio, "parent_comment": -1}
            )

            # comment2 -> parent (should be retrieved because in the scope)
            _, _, _, comment2 = self.create_random_valid_object(
                predefined_vals={"portfolio": portfolio, "parent_comment": -1}
            )

            # comment3 -> parent (should be retrieved because in the scope)
            _, _, _, comment3 = self.create_random_valid_object(
                predefined_vals={"portfolio": portfolio, "parent_comment": -1}
            )

            # comment4 -> child of comment2 (should be retrieved because CHILD of a comment in the scope)
            _, _, _, comment4 = self.create_random_valid_object(
                predefined_vals={"portfolio": portfolio, "parent_comment": comment2}
            )

            # comment5 -> child of comment1 (should NOT be retrieved because CHILD of a comment OUT the scope)
            _, _, _, comment5 = self.create_random_valid_object(
                predefined_vals={"portfolio": portfolio, "parent_comment": comment1}
            )

            # -- Page 1 (initial) -- #

            # send request
            url = reverse(
                f"{self.namespace}:get-portfolio-comments",
                kwargs={"portfolio_id": portfolio.id},
            )

            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

            results = response.data["data"]["results"]
            returned_ids = [r["id"] for r in results]

            # limit is 2 -> should only retrieve 2 newest parent comments
            returned_parent_comments = [
                r for r in results if r["parent_comment_id"] is None
            ]
            self.assertEqual(len(returned_parent_comments), 2)

            # should contain comment2 + comment3 parents
            self.assertIn(comment2.id, returned_ids)
            self.assertIn(comment3.id, returned_ids)

            # should contain child of retrieved parent (comment2)
            self.assertIn(comment4.id, returned_ids)

            # should NOT contain old parent outside scope
            self.assertNotIn(comment1.id, returned_ids)

            # should NOT contain child of old parent outside scope
            self.assertNotIn(comment5.id, returned_ids)

            # next cursor should point to min id from current page
            expected_cursor = comment2.id
            self.assertIn("next", response.data["data"])

            next_url = response.data["data"]["next"]
            self.assertIsNotNone(next_url)
            self.assertIn(f"cursor={expected_cursor}", next_url)

            # -- Page 2 (next set of parents) -- #

            # test next page retrieval
            response_2 = self.client.get(next_url)
            self.assertEqual(response.status_code, 200)

            results_2 = response_2.data["data"]["results"]
            returned_ids_2 = [r["id"] for r in results_2]

            # there is only one parent left in the db, should only contain comment1 as parent (comment5 exists in as child)
            returned_parent_comments_2 = [
                r for r in results_2 if r["parent_comment_id"] is None
            ]
            self.assertEqual(len(returned_parent_comments_2), 1)

            # previous ones dont come
            self.assertNotIn(comment2.id, returned_ids_2)
            self.assertNotIn(comment3.id, returned_ids_2)
            self.assertNotIn(comment4.id, returned_ids_2)

            # next pages parent comment1 and its child comment5 should exist
            self.assertIn(comment1.id, returned_ids_2)
            self.assertIn(comment5.id, returned_ids_2)

            next_url = response_2.data["data"]["next"]
            self.assertIsNotNone(next_url)
            # since we succesfuly retrieved another page of comments, we have a cursor
            # because db thinks 'I didnt ran out of comments, there may be more'
            # oldest comment retrieved is comment1, cursor sits on it's id
            self.assertIn(f"cursor={comment1.id}", next_url)

            # -- Page 3 (ran out of comments) -- #

            # test next page retrieval
            response_3 = self.client.get(next_url)
            self.assertEqual(response.status_code, 200)

            # but this time no more comments, and no more next url
            results_3 = response_3.data["data"]["results"]
            self.assertEqual(len(results_3), 0)
            next_url = response_3.data["data"]["next"]
            self.assertIsNone(next_url)

    def test_non_existing_portfolio_comment_retrieval(self):
        url = reverse(
            f"{self.namespace}:get-portfolio-comments", kwargs={"portfolio_id": 0}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_existing_portfolio_no_comments(self):
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:get-portfolio-comments",
            kwargs={"portfolio_id": portfolio.id},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 0)
        self.assertIsNone(response.data["data"]["next"])


# WorkView
class TestRetrieveWorkView(WorkBaseTestCase):
    def test_admin_can_retrieve_works(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, work1 = self.create_random_valid_object()
        _, _, _, work2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:work")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], work1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], work2)

    def test_logged_in_user_cannot_retrieve_works(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:work")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreateWorkView
class TestCreateWorkView(WorkBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, self.portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        self.url = reverse(
            f"{self.namespace}:create-work", kwargs={"portfolio_id": self.portfolio.id}
        )

    def test_owner_can_create_valid_work_files(self):
        # pdf is tested explicity because we have to test folder creation and page parsing
        valid_extensions = (
            list(ALLOWED_VIDEO_EXTENSIONS)
            + list(ALLOWED_AUDIO_EXTENSIONS)
            + list(ALLOWED_IMAGE_EXTENSIONS)
        )

        for ext in valid_extensions:
            original_vals, vals_to_send_request, _ = self.get_random_valid_data(
                predefined_vals={
                    "portfolio": self.portfolio,
                    "work_file": self.get_random_file_value(ext=ext),
                }
            )
            vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

            response = self.client.post(
                self.url, vals_to_send_request, format="multipart"
            )
            self.assertEqual(response.status_code, 201)
            work = Work.objects.first()
            self.process_pdf_for_test(work)
            self.assert_db_stored_values_match_expected_dict(work, original_vals)

    def test_create_work_invalid_fields(self):
        # Explicit check for work file fails because error return key is different
        # big image
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(target_size_bytes=WORK_IMAGE_MAX_SIZE * 2)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # big pdf
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(
                ext="pdf", target_size_bytes=WORK_PDF_MAX_SIZE * 2
            )
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # long pdf
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="pdf", pages=WORK_PDF_MAX_PAGE + 5)
        ]
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)
        errors = response.data["data"]["status"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["index"], 0)

        # big video
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(
                ext="mp4", target_size_bytes=WORK_VIDEO_MAX_SIZE * 2
            )
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # long video
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="mp4", duration=WORK_VIDEO_MAX_DURATION + 10)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # less wide video
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="mp4", W=WORK_VIDEO_MIN_W - 10)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # less high video
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="mp4", H=WORK_VIDEO_MIN_H - 10)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # wider video
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="mp4", W=WORK_VIDEO_MAX_W + 10)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # higher video
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="mp4", H=WORK_VIDEO_MAX_H + 10)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # big audio
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(
                ext="mp3", target_size_bytes=WORK_AUDIO_MAX_SIZE * 2
            )
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

        # long audio
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )
        vals_to_send_request["work_files"] = [
            self.get_random_file_value(ext="mp3", duration=WORK_AUDIO_MAX_DURATION + 10)
        ]
        del vals_to_send_request[
            "work_file"
        ]  # explanation at the bottom of the serializer test code
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_admin_can_create_work(self):
        self.client.force_authenticate(user=self.admin)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(self.url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        work = Work.objects.first()
        self.process_pdf_for_test(work)
        self.assert_db_stored_values_match_expected_dict(work, original_vals)

    def test_owner_can_create_work(self):
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(self.url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        work = Work.objects.first()
        self.process_pdf_for_test(work)
        self.assert_db_stored_values_match_expected_dict(work, original_vals)

    def test_owner_can_create_pdf_work(self):
        page_count = 4
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={
                "portfolio": self.portfolio,
                "work_file": self.get_random_file_value(ext="pdf", pages=page_count),
            }
        )

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(self.url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        work = Work.objects.first()
        self.process_pdf_for_test(work)

        # check if pdf configuration is done correctly
        work.refresh_from_db()
        self.assertNotEqual(work.folder_name, "")
        self.assertEqual(work.num_of_images, page_count)
        self.assertTrue(work.is_pdf)

        self.assert_db_stored_values_match_expected_dict(work, original_vals)

    def test_non_owner_cannot_create_work(self):
        portfolio_tester = PortfolioBaseTestCase()

        _, _, _, portfolio = portfolio_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:create-work", kwargs={"portfolio_id": portfolio.id}
        )

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": portfolio}
        )

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 403)

    def test_guest_cannot_create_work(self):
        self.client.logout()

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"portfolio": self.portfolio}
        )

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(self.url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 403)

    def test_max_work_count_limit(self):
        NEW_LIMIT = 2
        with patch("PortfolioPageApp.views.MAX_WORK_COUNT_PER_PORTFOLIO", NEW_LIMIT):
            for _ in range(NEW_LIMIT):
                self.create_random_valid_object(
                    predefined_vals={"portfolio": self.portfolio}
                )

            _, vals_to_send_request, _ = self.get_random_valid_data(
                predefined_vals={"portfolio": self.portfolio}
            )

            vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

            response = self.client.post(
                self.url, vals_to_send_request, format="multipart"
            )

            self.assertEqual(response.status_code, 400)
            self.assertIn("limit", response.data)

    def test_work_pdf_page_limit_exceeded_with_pdf_check(self):
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={
                "work_file": self.get_random_file_value(
                    ext="pdf", pages=WORK_PDF_MAX_PAGE + 5
                )
            }
        )

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(self.url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 400)
        errors = response.data["data"]["status"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["index"], 0)
        self.assertIn("pdf", errors[0]["error"])

    def test_work_pdf_page_limit_exceeded_with_pdf_parse(self):
        # Use self.assertRaises to catch the expected RuntimeError
        with self.assertRaises(RuntimeError) as context:
            self.create_random_valid_object(
                predefined_vals={
                    "work_file": self.get_random_file_value(
                        ext="pdf", pages=WORK_PDF_MAX_PAGE + 5
                    )
                }
            )

        self.assertIn("dropped due to validation failure", str(context.exception))
        self.assertFalse(Work.objects.filter(id=1).exists())

    def test_non_existing_portfolio_create_work(self):
        url = reverse(f"{self.namespace}:create-work", kwargs={"portfolio_id": 0})

        _, vals_to_send_request, _ = self.get_random_valid_data()

        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 404)

    def test_partial_success_create_work(self):
        valid_file_1 = self.get_random_file_value()

        invalid_file = self.get_random_file_value(
            target_size_bytes=WORK_IMAGE_MAX_SIZE * 2
        )

        valid_file_2 = self.get_random_file_value()

        response = self.client.post(
            self.url,
            {"title": "", "work_files": [valid_file_1, invalid_file, valid_file_2]},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)

        work1 = Work.objects.all()[0]
        self.process_pdf_for_test(work1)

        work2 = Work.objects.all()[1]
        self.process_pdf_for_test(work2)

        works = response.data["data"]["works"]
        errors = response.data["data"]["status"]

        self.assertEqual(len(works), 2)
        self.assertEqual(len(errors), 1)

        self.assertEqual(errors[0]["index"], 1)

        self.assertEqual(Work.objects.count(), 2)


# DeleteWorkView
class TestDeleteWorkView(WorkBaseTestCase):
    def test_admin_can_delete_work(self):
        _, _, _, work = self.create_random_valid_object()

        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:delete-work", kwargs={"work_id": work.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Work.objects.filter(id=work.id).exists())

    def test_owner_can_delete_work(self):
        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        _, _, _, work = self.create_random_valid_object(
            predefined_vals={"portfolio": portfolio}
        )

        work_file_path = work.work_file.name

        url = reverse(f"{self.namespace}:delete-work", kwargs={"work_id": work.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Work.objects.filter(id=work.id).exists())
        self.assertFalse(file_storage.exists(work_file_path))

    def test_owner_can_delete_pdf_work(self):
        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        work_file = get_dummy_file(ext="pdf", target_size_bytes=WORK_PDF_MAX_SIZE / 2)
        _, _, _, work = self.create_random_valid_object(
            predefined_vals={"portfolio": portfolio, "work_file": work_file}
        )

        work_file_path = work.work_file.name

        work_pages_folder = PurePosixPath(
            get_work_upload_folder_path(work), "pages"
        ).as_posix()

        url = reverse(f"{self.namespace}:delete-work", kwargs={"work_id": work.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Work.objects.filter(id=work.id).exists())
        self.assertFalse(file_storage.exists(work_file_path))
        self.assertFalse(directory_storage.exists(work_pages_folder))

    def test_owner_can_delete_work_portfolio(self):
        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        _, _, _, work = self.create_random_valid_object(
            predefined_vals={"portfolio": portfolio}
        )

        work_file_path = work.work_file.name

        url = reverse(
            f"{self.namespace}:delete-portfolio", kwargs={"portfolio_id": portfolio.id}
        )

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Work.objects.filter(id=work.id).exists())
        self.assertFalse(file_storage.exists(work_file_path))

    def test_non_existing_work_delete(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:delete-work", kwargs={"work_id": 0})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_delete_work(self):
        _, _, _, work = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(f"{self.namespace}:delete-work", kwargs={"work_id": work.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)


# Portfolio Retrieval with Pdf Works
class PortfolioRetrievalWithPdfWork(WorkBaseTestCase):
    def test_portfolio_retrieval_with_pdf_work(self):
        self.client.force_authenticate(user=self.user)

        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        page_count = 4
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={
                "portfolio": portfolio,
                "work_file": self.get_random_file_value(ext="pdf", pages=page_count),
            }
        )
        vals_to_send_request["work_files"] = [vals_to_send_request.pop("work_file")]

        response = self.client.post(
            reverse(
                f"{self.namespace}:create-work", kwargs={"portfolio_id": portfolio.id}
            ),
            vals_to_send_request,
            format="multipart",
        )

        work = Work.objects.first()
        self.process_pdf_for_test(work)

        url = reverse(
            f"{self.namespace}:get-portfolio", kwargs={"portfolio_id": portfolio.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["works"][0]["num_of_images"], page_count)
        self.assertIn(
            f"{response.data['data']['folder_name']}/{response.data['data']['works'][0]['folder_name']}/pages",
            response.data["data"]["works"][0]["pages_base_url"],
        )
        self.assertIn(
            f"{response.data['data']['folder_name']}/{response.data['data']['works'][0]['folder_name']}/original.pdf",
            response.data["data"]["works"][0]["file_url"],
        )
