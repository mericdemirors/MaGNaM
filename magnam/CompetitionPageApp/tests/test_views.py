from django.urls import reverse
from ..models import *
from .base_test import *

from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from magnam.storage import file_storage


# CompetitionTagView
class TestRetrieveCompetitionTagView(CompetitionTagBaseTestCase):
    def test_guest_can_retrieve_tags(self):
        self.client.logout()

        _, _, _, tag1 = self.create_random_valid_object()
        _, _, _, tag2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:competition-tag")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], tag1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], tag2)


# CompetitionView
class TestRetrieveCompetitionView(CompetitionBaseTestCase):
    def test_admin_can_retrieve_competitions(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, p1 = self.create_random_valid_object()
        _, _, _, p2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:competition")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], p1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], p2)

    def test_logged_in_user_cannot_retrieve_competitions(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:competition")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreateCompetitionView
class TestCreateCompetitionView(CompetitionBaseTestCase):
    def test_admin_can_create_competition(self):
        self.client.force_authenticate(user=self.admin)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        url = reverse(f"{self.namespace}:create-competition")
        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        competition = Competition.objects.first()
        self.assert_db_stored_values_match_expected_dict(competition, original_vals)

    def test_logged_in_user_cannot_create_competition(self):
        self.client.force_authenticate(user=self.user)

        _, vals, _ = self.get_random_valid_data(predefined_vals=fast_creation_dict)

        url = reverse(f"{self.namespace}:create-competition")
        response = self.client.post(url, vals)

        self.assertEqual(response.status_code, 403)


# GetCompetitionView
class TestGetCompetitionView(CompetitionBaseTestCase):
    def test_guest_can_retrieve_competition(self):
        _, _, _, competition = self.create_random_valid_object()
        self.client.logout()

        url = reverse(
            f"{self.namespace}:get-competition",
            kwargs={"competition_id": competition.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"], competition
        )

    def test_non_existing_competition_retrieval(self):
        url = reverse(f"{self.namespace}:get-competition", kwargs={"competition_id": 0})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_annotated_field_retrieval(self):
        original_vals, _, _, competition = self.create_random_valid_object()
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:get-competition",
            kwargs={"competition_id": competition.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["num_of_chapter_submits"],
            len(original_vals["chapter_submits"]),
        )
        self.assertEqual(
            response.data["data"]["num_of_portfolio_submits"],
            len(original_vals["portfolio_submits"]),
        )
        self.assertEqual(response.data["data"]["user_submitted_item"], "")
        self.assertEqual(response.data["data"]["profile_balance"], 0)
        # in this test we only test the base annotated fields and returned basic balance etc
        # we do the submissions etc from another view


# EditCompetitionView
class TestEditCompetitionView(CompetitionBaseTestCase):
    def test_admin_can_update_competition(self):
        self.client.force_authenticate(user=self.admin)

        # create an object to modfiy later
        _, _, _, competition = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        # create new random values to modify the fields with and then check with
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )
        url = reverse(
            f"{self.namespace}:edit-competition",
            kwargs={"competition_id": competition.id},
        )

        # check single field updates
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="title",
            new_field_value=vals_to_send_request["title"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["title"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="description",
            new_field_value=vals_to_send_request["description"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["description"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="links",
            new_field_value=vals_to_send_request["links"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["links"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="start_date",
            new_field_value=vals_to_send_request["start_date"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["start_date"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="price",
            new_field_value=vals_to_send_request["price"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["price"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="end_date",
            new_field_value=vals_to_send_request["end_date"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["end_date"]
            ),
        )
        old_image_path = competition.image.name
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="image",
            new_field_value=vals_to_send_request["image"],
            field_assertion_function=lambda actual: (
                self.assert_database_image(competition),
                self.assertFalse(file_storage.exists(old_image_path)),
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=competition,
            update_api_url=url,
            field_to_update="tags",
            new_field_value=vals_to_send_request["tags"],
            field_assertion_function=None,
        )
        # we do the assertion explicity because relational fields fail the find_different_fields check
        competition.refresh_from_db()
        self.assertEqual(
            set([t.id for t in competition.tags.all()]), set(original_vals["tags"])
        )

        # update all fields
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 200)
        competition.refresh_from_db()
        # check if values stored in the db matches the ones we want
        self.assert_db_stored_values_match_expected_dict(competition, original_vals)

    def test_admin_update_non_existing_competition(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(
            f"{self.namespace}:edit-competition", kwargs={"competition_id": 0}
        )

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 404)

    def test_logged_in_user_cannot_edit_competition(self):
        # create a competition to edit later
        _, _, _, competition = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        self.client.force_authenticate(user=self.user)
        url = reverse(
            f"{self.namespace}:edit-competition",
            kwargs={"competition_id": competition.id},
        )

        new_title = self.get_random_title_value()
        response = self.client.patch(url, {"title": new_title})

        self.assertEqual(response.status_code, 403)
        competition.refresh_from_db()
        self.assertNotEqual(competition.title, new_title)


# DeleteCompetitionView
class TestDeleteCompetitionView(CompetitionBaseTestCase):
    def test_admin_can_delete_competition(self):
        self.client.force_authenticate(user=self.admin)

        # create competition to delete later
        _, _, _, competition = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        competition_id = competition.id
        image_path = competition.image.name  # Store path to verify file deletion

        url = reverse(
            f"{self.namespace}:delete-competition",
            kwargs={"competition_id": competition_id},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Competition.objects.filter(id=competition_id).exists())
        self.assertFalse(file_storage.exists(image_path))

    def test_admin_delete_non_existing_competition(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(
            f"{self.namespace}:delete-competition", kwargs={"competition_id": 0}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_logged_in_user_cannot_delete_competition(self):
        # create a competition to delete later
        _, _, _, competition = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        self.client.force_authenticate(user=self.user)
        url = reverse(
            f"{self.namespace}:delete-competition",
            kwargs={"competition_id": competition.id},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Competition.objects.filter(id=competition.id).exists())


# CompetitionGalleryView
class TestCompetitionGalleryViewPermission(CompetitionBaseTestCase):
    def test_guest_access_gallery(self):
        self.create_random_valid_object()
        self.client.logout()

        url = reverse(f"{self.namespace}:competition-gallery")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


# CompetitionGalleryView
class TestCompetitionGalleryViewExistence(CompetitionBaseTestCase):
    def test_empty_gallery_returns_204(self):
        url = reverse(f"{self.namespace}:competition-gallery")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 204)


# CompetitionGalleryView
class TestCompetitionGalleryViewFiltering(CompetitionBaseTestCase):
    def test_start_date_filtering(self):
        # create competitions
        _, _, _, competition1 = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        _, _, _, competition2 = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        _, _, _, competition3 = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        # manually override start_date
        competition1.start_date = now().date() - timedelta(days=10)
        competition1.save()

        competition2.start_date = now().date() - timedelta(days=5)
        competition2.save()

        competition3.start_date = now().date()
        competition3.save()

        url = reverse(f"{self.namespace}:competition-gallery")

        min_start_date = now().date() - timedelta(days=7)
        max_start_date = now().date() - timedelta(days=2)

        min_dt = timezone.make_aware(
            timezone.datetime.combine(min_start_date, timezone.datetime.min.time())
        )
        max_dt = timezone.make_aware(
            timezone.datetime.combine(max_start_date, timezone.datetime.min.time())
        )
        min_ts = int(min_dt.timestamp() * 1000)
        max_ts = int(max_dt.timestamp() * 1000)

        response = self.client.get(
            url, {"start_date_min": min_ts, "start_date_max": max_ts}
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(competition1.id, returned_ids)
        self.assertIn(competition2.id, returned_ids)
        self.assertNotIn(competition3.id, returned_ids)

    def test_end_date_filtering(self):
        # create competitions
        _, _, _, competition1 = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        _, _, _, competition2 = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        _, _, _, competition3 = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        # manually override end_date
        competition1.end_date = now().date() + timedelta(days=20)
        competition1.save()

        competition2.end_date = now().date() + timedelta(days=25)
        competition2.save()

        competition3.end_date = now().date() + timedelta(days=30)
        competition3.save()

        url = reverse(f"{self.namespace}:competition-gallery")

        min_end_date = now().date() + timedelta(days=23)
        max_end_date = now().date() + timedelta(days=28)

        min_dt = timezone.make_aware(
            timezone.datetime.combine(min_end_date, timezone.datetime.min.time())
        )
        max_dt = timezone.make_aware(
            timezone.datetime.combine(max_end_date, timezone.datetime.min.time())
        )
        min_ts = int(min_dt.timestamp() * 1000)
        max_ts = int(max_dt.timestamp() * 1000)

        response = self.client.get(
            url, {"end_date_min": min_ts, "end_date_max": max_ts}
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(competition1.id, returned_ids)
        self.assertIn(competition2.id, returned_ids)
        self.assertNotIn(competition3.id, returned_ids)

    def test_price_filtering(self):
        _, _, _, competition1 = self.create_random_valid_object(
            predefined_vals={"price": 1, **fast_creation_dict}
        )
        _, _, _, competition2 = self.create_random_valid_object(
            predefined_vals={"price": 5, **fast_creation_dict}
        )
        _, _, _, competition3 = self.create_random_valid_object(
            predefined_vals={"price": 10, **fast_creation_dict}
        )

        url = reverse(f"{self.namespace}:competition-gallery")

        response = self.client.get(url, {"price_min": 2, "price_max": 7})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(competition1.id, returned_ids)
        self.assertIn(competition2.id, returned_ids)
        self.assertNotIn(competition3.id, returned_ids)

    def test_num_of_portfolio_submits_filtering(self):
        predefined_portfolio = self.get_random_portfolio_submits_value(count=4)

        _, _, _, competition1 = self.create_random_valid_object(
            predefined_vals={
                "portfolio_submits": [],
                "chapter_submits": [],
                "portfolio_wins": [],
                "chapter_wins": [],
            }
        )
        _, _, _, competition2 = self.create_random_valid_object(
            predefined_vals={
                "portfolio_submits": predefined_portfolio[:2],
                "chapter_submits": [],
                "portfolio_wins": predefined_portfolio[:2],
                "chapter_wins": [],
            }
        )
        _, _, _, competition3 = self.create_random_valid_object(
            predefined_vals={
                "portfolio_submits": predefined_portfolio[:4],
                "chapter_submits": [],
                "portfolio_wins": predefined_portfolio[:4],
                "chapter_wins": [],
            }
        )

        url = reverse(f"{self.namespace}:competition-gallery")

        response = self.client.get(
            url, {"num_of_portfolio_submits_min": 1, "num_of_portfolio_submits_max": 3}
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(competition1.id, returned_ids)
        self.assertIn(competition2.id, returned_ids)
        self.assertNotIn(competition3.id, returned_ids)

    def test_num_of_chapter_submits_filtering(self):
        predefined_chapter = self.get_random_chapter_submits_value(count=4)

        _, _, _, competition1 = self.create_random_valid_object(
            predefined_vals={
                "chapter_submits": [],
                "portfolio_submits": [],
                "chapter_wins": [],
                "portfolio_wins": [],
            }
        )
        _, _, _, competition2 = self.create_random_valid_object(
            predefined_vals={
                "chapter_submits": predefined_chapter[:2],
                "portfolio_submits": [],
                "chapter_wins": predefined_chapter[:2],
                "portfolio_wins": [],
            }
        )
        _, _, _, competition3 = self.create_random_valid_object(
            predefined_vals={
                "chapter_submits": predefined_chapter[:4],
                "portfolio_submits": [],
                "chapter_wins": predefined_chapter[:4],
                "portfolio_wins": [],
            }
        )

        url = reverse(f"{self.namespace}:competition-gallery")

        response = self.client.get(
            url, {"num_of_chapter_submits_min": 1, "num_of_chapter_submits_max": 3}
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(competition1.id, returned_ids)
        self.assertIn(competition2.id, returned_ids)
        self.assertNotIn(competition3.id, returned_ids)

    def test_tag_filtering(self):
        # create reusable tags
        tag_tester = CompetitionTagBaseTestCase()

        _, _, _, tag1 = tag_tester.create_random_valid_object()
        _, _, _, tag2 = tag_tester.create_random_valid_object()
        _, _, _, tag3 = tag_tester.create_random_valid_object()

        # should be returned (contains ALL required tags)
        _, _, _, matching_competition = self.create_random_valid_object(
            predefined_vals={"tags": [tag1, tag2], **fast_creation_dict}
        )

        # should NOT be returned (missing tag2)
        _, _, _, missing_tag_competition = self.create_random_valid_object(
            predefined_vals={"tags": [tag1], **fast_creation_dict}
        )

        # should be returned (contains required tags + extra tag)
        _, _, _, extra_tags_competition = self.create_random_valid_object(
            predefined_vals={"tags": [tag1, tag2, tag3], **fast_creation_dict}
        )

        url = reverse(f"{self.namespace}:competition-gallery")

        response = self.client.get(url, {"tags": f"{tag1.id},{tag2.id}"})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertIn(matching_competition.id, returned_ids)
        self.assertNotIn(missing_tag_competition.id, returned_ids)
        self.assertIn(extra_tags_competition.id, returned_ids)


# CompetitionGalleryView
class TestCompetitionGalleryViewSorting(CompetitionBaseTestCase):
    def setUp(self):
        super().setUp()

        predefined_chapter = self.get_random_chapter_submits_value(count=2)
        predefined_portfolio = self.get_random_portfolio_submits_value(count=2)

        _, _, _, self.competition1 = self.create_random_valid_object(
            predefined_vals={
                "price": 1,
                "start_date": now().date() - timedelta(days=10),
                "end_date": now().date() - timedelta(days=7),
                "chapter_submits": [],
                "portfolio_submits": [],
                "chapter_wins": [],
                "portfolio_wins": [],
            }
        )

        _, _, _, self.competition2 = self.create_random_valid_object(
            predefined_vals={
                "price": 5,
                "start_date": now().date() - timedelta(days=5),
                "end_date": now().date() - timedelta(days=3),
                "chapter_submits": predefined_chapter[:1],
                "portfolio_submits": predefined_portfolio[:1],
                "chapter_wins": predefined_chapter[:1],
                "portfolio_wins": predefined_portfolio[:1],
            }
        )

        _, _, _, self.competition3 = self.create_random_valid_object(
            predefined_vals={
                "price": 10,
                "start_date": now().date(),
                "end_date": now().date() + timedelta(days=5),
                "chapter_submits": predefined_chapter[:2],
                "portfolio_submits": predefined_portfolio[:2],
                "chapter_wins": predefined_chapter[:2],
                "portfolio_wins": predefined_portfolio[:2],
            }
        )

        self.url = reverse(f"{self.namespace}:competition-gallery")

    def get_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.data["results"]]

    def test_gallery_sorts(self):
        response = self.client.get(self.url, {"sort": "price"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition3.id, self.competition2.id, self.competition1.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-price"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition1.id, self.competition2.id, self.competition3.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_portfolio_submits"})

        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition3.id, self.competition2.id, self.competition1.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_portfolio_submits"})

        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition1.id, self.competition2.id, self.competition3.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_chapter_submits"})

        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition3.id, self.competition2.id, self.competition1.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_chapter_submits"})

        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition1.id, self.competition2.id, self.competition3.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "start_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition3.id, self.competition2.id, self.competition1.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-start_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition1.id, self.competition2.id, self.competition3.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "end_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition3.id, self.competition2.id, self.competition1.id]
        )

        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-end_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it
            for x in [self.competition1.id, self.competition2.id, self.competition3.id]
        )

        self.assertTrue(is_order_preserved)

    def test_gallery_multi_sort(self):
        _, _, _, competition4 = self.create_random_valid_object(
            predefined_vals={
                "price": 100,
                "start_date": now().date(),
                "chapter_submits": [],
                "portfolio_submits": [],
                "chapter_wins": [],
                "portfolio_wins": [],
            }
        )

        response = self.client.get(self.url, {"sort": "start_date,price"})

        ids = self.get_ids(response)

        it = iter(ids)

        is_order_preserved = all(
            x in it
            for x in [
                competition4.id,
                self.competition3.id,
                self.competition2.id,
                self.competition1.id,
            ]
        )

        self.assertTrue(is_order_preserved)


# CompetitionGalleryView
class TestCompetitionGalleryViewRandomnessTest(CompetitionBaseTestCase):
    def test_random_sort(self):
        # create 3 competitions
        for _ in range(3):
            _, _, _, _ = self.create_random_valid_object(
                predefined_vals=fast_creation_dict
            )

        url = reverse(f"{self.namespace}:competition-gallery")

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

        self.assertTrue(True)


# CompetitionGalleryView
class TestCompetitionGalleryViewPaginationTest(CompetitionBaseTestCase):
    def test_pagination_with_next_link(self):
        competitions = []

        for i in range(6):
            _, _, _, competition = self.create_random_valid_object(
                predefined_vals={"price": i, **fast_creation_dict}
            )
            competitions.append(competition)

        # sort by price
        competitions_sorted = sorted(competitions, key=lambda x: x.price, reverse=True)

        url = reverse(f"{self.namespace}:competition-gallery")

        # get the first page
        response1 = self.client.get(url, {"sort": "price", "page_size": 3})
        self.assertEqual(response1.status_code, 200)

        # check if first page consists of the first 3 competitions
        ids_page1 = [item["id"] for item in response1.data["results"]]
        expected_page1 = [t.id for t in competitions_sorted[:3]]
        self.assertEqual(ids_page1, expected_page1)

        # use 'next' field in the response to get the second page
        next_url = response1.data["next"]
        self.assertIsNotNone(next_url)
        response2 = self.client.get(next_url)
        self.assertEqual(response2.status_code, 200)

        # check if second page consists of the second 3 competitions
        ids_page2 = [item["id"] for item in response2.data["results"]]
        expected_page2 = [t.id for t in competitions_sorted[3:6]]
        self.assertEqual(ids_page2, expected_page2)


# CompetitionGalleryView
class TestCompetitionGalleryViewFields(CompetitionBaseTestCase):
    def test_gallery_fields_consistency(self):
        competitions = []

        predefined_chapter = self.get_random_chapter_submits_value(count=2)
        predefined_portfolio = self.get_random_portfolio_submits_value(count=2)

        for i in range(3):
            _, _, _, competition = self.create_random_valid_object(
                predefined_vals={
                    "chapter_submits": predefined_chapter[:i],
                    "portfolio_submits": predefined_portfolio[:i],
                    "chapter_wins": predefined_chapter[:i],
                    "portfolio_wins": predefined_portfolio[:i],
                }
            )
            competitions.append(competition)

        competition1, competition2, competition3 = competitions

        response = self.client.get(
            reverse(f"{self.namespace}:competition-gallery"), {"sort": "-start_date"}
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        expected_competition_ids = {competition1.id, competition2.id, competition3.id}

        filtered_results = [
            item for item in results if item["id"] in expected_competition_ids
        ]

        for retrieved_item in filtered_results:
            competition = next(c for c in competitions if c.id == retrieved_item["id"])

            self.assert_gallery_retrieved_dict_match_db_stored_values(
                retrieved_item, competition
            )

            expected_num_of_portfolio_submits = competition.portfolio_submits.count()

            expected_num_of_chapter_submits = competition.chapter_submits.count()

            self.assertEqual(
                retrieved_item["num_of_portfolio_submits"],
                expected_num_of_portfolio_submits,
            )

            self.assertEqual(
                retrieved_item["num_of_chapter_submits"],
                expected_num_of_chapter_submits,
            )


# SubmitCompetitionItemView
class TestSubmitCompetitionItemView(CompetitionBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.competition = self.create_random_valid_object(
            predefined_vals={
                "start_date": now().date() - timedelta(days=1),
                "end_date": now().date() + timedelta(days=1),
                "price": 100,
                **fast_creation_dict,
            }
        )

        self.url = lambda item_string: reverse(
            f"{self.namespace}:submit-competition-item",
            kwargs={"competition_id": self.competition.id, "item_string": item_string},
        )

    def test_submit_to_ended_competition_fails(self):
        self.competition.end_date = now().date() - timedelta(days=1)
        self.competition.save()

        self.client.force_login(self.user)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 400)

    def test_submit_to_not_started_competition_fails(self):
        self.competition.start_date = now().date() + timedelta(days=1)
        self.competition.save()

        self.client.force_login(self.user)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 400)

    def test_guest_cannot_submit(self):
        portfolio = self.get_random_portfolio_submits_value(count=1)[0]

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 403)

    def test_invalid_item_format_for_submit(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url("invalid"))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url("chapter_invalid"))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url("invalid_1"))
        self.assertEqual(response.status_code, 400)

    def test_invalid_submission_item_for_submit(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url("chapter_0"))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(self.url("portfolio_0"))
        self.assertEqual(response.status_code, 404)

    def test_invalid_submission_permission(self):
        other_profile = get_dummy_profile()

        chapter = self.get_random_chapter_submits_value(count=1)[0]
        chapter.manga.owner = other_profile
        chapter.manga.save()
        chapter.owner = other_profile
        chapter.save()

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = other_profile
        portfolio.save()

        self.client.force_login(self.user)

        response = self.client.post(self.url(f"chapter_{chapter.id}"))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 403)

    def test_invalid_submission_repeat(self):
        self.client.force_login(self.user)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        self.user.profile.wallet = 1000
        self.user.profile.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 400)

    def test_invalid_submission_not_enough_money(self):
        self.client.force_login(self.user)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        self.user.profile.wallet = 0
        self.user.profile.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 400)

    def test_valid_submission_admin_without_money(self):
        self.admin.profile.wallet = 0
        self.admin.profile.save()

        self.client.force_login(self.admin)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.admin.profile
        portfolio.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()

        self.assertIn(portfolio, self.competition.portfolio_submits.all())

    def test_valid_chapter_submission_for_submit(self):
        self.client.force_login(self.user)

        self.user.profile.wallet = 1000
        self.user.profile.save()

        chapter = self.get_random_chapter_submits_value(count=1)[0]
        chapter.manga.owner = self.user.profile
        chapter.manga.save()
        chapter.owner = self.user.profile
        chapter.save()
        chapter.refresh_from_db()

        response = self.client.post(self.url(f"chapter_{chapter.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertIn(chapter, self.competition.chapter_submits.all())

        self.assertEqual(self.user.profile.wallet, 900)

    def test_valid_portfolio_submission_for_submit(self):
        self.client.force_login(self.user)

        self.user.profile.wallet = 1000
        self.user.profile.save()

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()
        portfolio.refresh_from_db()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertIn(portfolio, self.competition.portfolio_submits.all())

        self.assertEqual(self.user.profile.wallet, 900)


# SubmitCompetitionWinnerView
class TestSubmitCompetitionWinnerView(CompetitionBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.competition = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        self.url = lambda item_string: reverse(
            f"{self.namespace}:submit-competition-winner",
            kwargs={"competition_id": self.competition.id, "item_string": item_string},
        )

    def test_permissions_for_winner(self):
        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        self.competition.portfolio_submits.add(portfolio)

        self.client.force_login(self.user)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.admin)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

    def test_invalid_item_format_for_winner(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url("invalid"))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url("chapter_invalid"))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url("invalid_1"))
        self.assertEqual(response.status_code, 400)

    def test_invalid_submission_item_for_winner(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url("chapter_0"))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(self.url("portfolio_0"))
        self.assertEqual(response.status_code, 404)

    def test_invalid_submission_item_not_submitted_for_winner(self):
        self.client.force_login(self.admin)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 400)

    def test_valid_chapter_submission_for_winner(self):
        self.client.force_login(self.admin)

        chapter = self.get_random_chapter_submits_value(count=1)[0]
        chapter.manga.owner = self.user.profile
        chapter.manga.save()
        chapter.owner = self.user.profile
        chapter.save()
        chapter.refresh_from_db()

        self.competition.chapter_submits.add(chapter)

        response = self.client.post(self.url(f"chapter_{chapter.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()

        self.assertIn(chapter, self.competition.chapter_wins.all())

        self.assertEqual(response.data["data"]["winner"]["id"], chapter.id)

        self.assertEqual(response.data["data"]["winner"]["title"], chapter.title)

        self.assertEqual(response.data["data"]["winner"]["no"], chapter.no)

        self.assertEqual(response.data["data"]["winner"]["manga_id"], chapter.manga.id)

        self.assertEqual(
            response.data["data"]["winner"]["manga_title"], chapter.manga.title
        )

        self.assertTrue(response.data["data"]["winner"]["manga_image"])

    def test_valid_portfolio_submission_for_winner(self):
        self.client.force_login(self.admin)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()
        portfolio.refresh_from_db()

        self.competition.portfolio_submits.add(portfolio)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()

        self.assertIn(portfolio, self.competition.portfolio_wins.all())

        self.assertEqual(response.data["data"]["winner"]["id"], portfolio.id)

        self.assertEqual(response.data["data"]["winner"]["title"], portfolio.title)

        self.assertTrue(response.data["data"]["winner"]["image"])


# SubmitCompetitionLoserView
class TestSubmitCompetitionLoserView(CompetitionBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.competition = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        self.url = lambda item_string: reverse(
            f"{self.namespace}:submit-competition-loser",
            kwargs={"competition_id": self.competition.id, "item_string": item_string},
        )

    def test_permissions_for_loser(self):
        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        self.competition.portfolio_wins.add(portfolio)

        self.client.force_login(self.user)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.admin)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

    def test_invalid_item_format_for_loser(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url("invalid"))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url("chapter_invalid"))
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.url("invalid_1"))
        self.assertEqual(response.status_code, 400)

    def test_invalid_submission_item_for_loser(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url("chapter_0"))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(self.url("portfolio_0"))
        self.assertEqual(response.status_code, 404)

    def test_invalid_submission_item_not_winner_for_loser(self):
        self.client.force_login(self.admin)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 400)

    def test_valid_chapter_submission_for_loser(self):
        self.client.force_login(self.admin)

        chapter = self.get_random_chapter_submits_value(count=1)[0]
        chapter.manga.owner = self.user.profile
        chapter.manga.save()
        chapter.owner = self.user.profile
        chapter.save()
        chapter.refresh_from_db()

        self.competition.chapter_wins.add(chapter)

        response = self.client.post(self.url(f"chapter_{chapter.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()

        self.assertNotIn(chapter, self.competition.chapter_wins.all())

        self.assertEqual(response.data["data"]["loser"]["id"], chapter.id)

        self.assertEqual(response.data["data"]["loser"]["title"], chapter.title)

        self.assertEqual(response.data["data"]["loser"]["no"], chapter.no)

        self.assertEqual(response.data["data"]["loser"]["manga_id"], chapter.manga.id)

        self.assertEqual(
            response.data["data"]["loser"]["manga_title"], chapter.manga.title
        )

        self.assertTrue(response.data["data"]["loser"]["manga_image"])

    def test_valid_portfolio_submission_for_loser(self):
        self.client.force_login(self.admin)

        portfolio = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio.owner = self.user.profile
        portfolio.save()
        portfolio.refresh_from_db()

        self.competition.portfolio_wins.add(portfolio)

        response = self.client.post(self.url(f"portfolio_{portfolio.id}"))
        self.assertEqual(response.status_code, 200)

        self.competition.refresh_from_db()

        self.assertNotIn(portfolio, self.competition.portfolio_wins.all())

        self.assertEqual(response.data["data"]["loser"]["id"], portfolio.id)

        self.assertEqual(response.data["data"]["loser"]["title"], portfolio.title)

        self.assertTrue(response.data["data"]["loser"]["image"])


class TestCompetitionSubmitScenarios(CompetitionBaseTestCase):
    def test_submission_scenarios(self):
        competition_price = 100

        _, _, _, competition = self.create_random_valid_object(
            predefined_vals={
                "price": competition_price,
                "start_date": now().date() - timedelta(days=1),
                "end_date": now().date() + timedelta(days=1),
                "portfolio_submits": [],
                "chapter_submits": [],
                "portfolio_wins": [],
                "chapter_wins": [],
            }
        )

        self.client.force_login(self.user)

        # give user enough balance
        self.user.profile.wallet = 1000
        self.user.profile.save()

        # create user items
        portfolio1 = self.get_random_portfolio_submits_value(count=1)[0]
        portfolio2 = self.get_random_portfolio_submits_value(count=1)[0]
        chapter1 = self.get_random_chapter_submits_value(count=1)[0]

        # ensure ownership
        portfolio1.owner = self.user.profile
        portfolio1.save()

        portfolio2.owner = self.user.profile
        portfolio2.save()

        chapter1.manga.owner = self.user.profile
        chapter1.manga.save()
        chapter1.owner = self.user.profile
        chapter1.save()

        submit_url = lambda item_string: reverse(
            f"{self.namespace}:submit-competition-item",
            kwargs={"competition_id": competition.id, "item_string": item_string},
        )

        winner_url = lambda item_string: reverse(
            f"{self.namespace}:submit-competition-winner",
            kwargs={"competition_id": competition.id, "item_string": item_string},
        )

        # 1- submit portfolio1
        response = self.client.post(submit_url(f"portfolio_{portfolio1.id}"))
        self.assertEqual(response.status_code, 200)

        competition.refresh_from_db()
        self.user.profile.refresh_from_db()

        # competition state
        self.assertIn(portfolio1, competition.portfolio_submits.all())

        self.assertEqual(competition.portfolio_submits.count(), 1)

        # balance check
        self.assertEqual(self.user.profile.wallet, 1000 - competition_price)

        # return data
        self.assertEqual(response.data["data"]["submitted"]["id"], portfolio1.id)

        self.assertFalse(response.data["data"]["removed"])

        self.assertEqual(
            response.data["data"]["profile_balance"], 1000 - competition_price
        )

        # 2- submit portfolio2
        response = self.client.post(submit_url(f"portfolio_{portfolio2.id}"))
        self.assertEqual(response.status_code, 200)

        competition.refresh_from_db()
        self.user.profile.refresh_from_db()

        # competition state
        self.assertNotIn(portfolio1, competition.portfolio_submits.all())

        self.assertIn(portfolio2, competition.portfolio_submits.all())

        self.assertEqual(competition.portfolio_submits.count(), 1)

        # balance check (half price deducted)
        self.assertEqual(
            self.user.profile.wallet,
            1000 - competition_price - (competition_price // 2),
        )

        # return data
        self.assertEqual(response.data["data"]["submitted"]["id"], portfolio2.id)

        self.assertEqual(response.data["data"]["removed"]["id"], portfolio1.id)

        self.assertEqual(
            response.data["data"]["profile_balance"],
            1000 - competition_price - (competition_price // 2),
        )

        # 3- admin selects portfolio2 as winner
        self.client.force_login(self.admin)

        response = self.client.post(winner_url(f"portfolio_{portfolio2.id}"))
        self.assertEqual(response.status_code, 200)

        competition.refresh_from_db()

        self.assertIn(portfolio2, competition.portfolio_wins.all())

        # 4- user submits chapter1
        self.client.force_login(self.user)

        response = self.client.post(submit_url(f"chapter_{chapter1.id}"))
        self.assertEqual(response.status_code, 200)

        competition.refresh_from_db()
        self.user.profile.refresh_from_db()

        # portfolio2 should be removed from submits
        self.assertNotIn(portfolio2, competition.portfolio_submits.all())

        # portfolio2 should also be removed from wins
        self.assertNotIn(portfolio2, competition.portfolio_wins.all())

        # chapter1 should now exist in chapter submits
        self.assertIn(chapter1, competition.chapter_submits.all())

        # balance check (another half price deducted)
        expected_balance = (
            1000
            - competition_price
            - (competition_price // 2)
            - (competition_price // 2)
        )

        self.assertEqual(self.user.profile.wallet, expected_balance)

        # return data
        self.assertEqual(response.data["data"]["submitted"]["id"], chapter1.id)

        self.assertEqual(response.data["data"]["removed"]["id"], portfolio2.id)

        self.assertEqual(response.data["data"]["profile_balance"], expected_balance)
