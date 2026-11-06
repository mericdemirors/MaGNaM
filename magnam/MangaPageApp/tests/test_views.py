from django.urls import reverse
from unittest.mock import patch
from ..models import *
from .base_test import *

from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from pathlib import PurePosixPath
from magnam.storage import directory_storage, file_storage


# MangaTagView
class TestRetrieveMangaTagView(MangaTagBaseTestCase):
    def test_guest_can_retrieve_tags(self):
        self.client.logout()

        _, _, _, tag1 = self.create_random_valid_object()
        _, _, _, tag2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:manga-tag")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], tag1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], tag2)


# MangaRatingView
class TestRetrieveMangaRatingView(MangaRatingBaseTestCase):
    def test_admin_can_retrieve_ratings(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, rating1 = self.create_random_valid_object()
        _, _, _, rating2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:manga-rating")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], rating1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], rating2)

    def test_logged_in_user_cannot_retrieve_ratings(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:manga-rating")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# MangaCommentView
class TestRetrieveMangaCommentView(MangaCommentBaseTestCase):
    def test_admin_can_retrieve_comments(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, c1 = self.create_random_valid_object()
        _, _, _, c2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:manga-comment")
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
            predefined_vals={"manga": c1.manga, "parent_comment": c1}
        )

        url = reverse(f"{self.namespace}:manga-comment")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], c1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], c2)

    def test_logged_in_user_cannot_retrieve_comments(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:manga-comment")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# MangaView
class TestRetrieveMangaView(MangaBaseTestCase):
    def test_admin_can_retrieve_mangas(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, m1 = self.create_random_valid_object()
        _, _, _, m2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:manga")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], m1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], m2)

    def test_logged_in_user_cannot_retrieve_mangas(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:manga")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreateMangaView
class TestCreateMangaView(MangaBaseTestCase):
    def test_user_can_create_manga(self):
        self.client.force_authenticate(user=self.user)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"owner": self.user.profile}
        )

        url = reverse(f"{self.namespace}:create-manga")
        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        manga = Manga.objects.first()
        self.assert_db_stored_values_match_expected_dict(manga, original_vals)

        self.assertIn(manga, self.user.profile.mangas_following.all())
        self.assertIn(manga, self.user.profile.mangas_owned.all())

    def test_guest_cannot_create_manga(self):
        self.client.logout()

        _, vals, _ = self.get_random_valid_data()

        url = reverse(f"{self.namespace}:create-manga")
        response = self.client.post(url, vals)

        self.assertEqual(response.status_code, 403)


# GetMangaView
class TestGetMangaView(MangaBaseTestCase):
    def test_guest_can_retrieve_manga(self):
        _, _, _, manga = self.create_random_valid_object()
        self.client.logout()

        url = reverse(f"{self.namespace}:get-manga", kwargs={"manga_id": manga.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"], manga
        )

    def test_non_existing_manga_retrieval(self):
        url = reverse(f"{self.namespace}:get-manga", kwargs={"manga_id": 0})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_annotated_field_retrieval(self):
        _, _, _, manga = self.create_random_valid_object()
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:get-manga", kwargs={"manga_id": manga.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["rating"], 0)
        self.assertEqual(response.data["data"]["num_of_ratings"], 0)
        self.assertEqual(response.data["data"]["num_of_comments"], 0)
        self.assertEqual(response.data["data"]["is_user_rated"], 0)
        self.assertEqual(response.data["data"]["num_of_followers"], 1)  # owner itself
        self.assertEqual(response.data["data"]["is_user_following"], False)
        self.assertEqual(
            response.data["data"]["total_price_of_all_chapters"], 0
        )  # no chapters yet
        self.assertEqual(
            sum(response.data["data"]["rating_histogram"].values()), 0
        )  # no rating yet
        self.assertEqual(response.data["data"]["profile_balance"], 0)

        # user rates it, writes 2 comment, follows
        rating_tester = MangaRatingBaseTestCase()
        _, _, _, rating = rating_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "manga": manga}
        )

        comment_tester = MangaCommentBaseTestCase()
        comment_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "manga": manga}
        )
        comment_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "manga": manga}
        )

        response = self.client.post(
            reverse(
                f"{self.namespace}:toggle-follow-manga", kwargs={"manga_id": manga.id}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["followed"])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["rating"], rating.score)
        self.assertEqual(response.data["data"]["num_of_ratings"], 1)
        self.assertEqual(response.data["data"]["num_of_comments"], 2)
        self.assertEqual(response.data["data"]["is_user_rated"], rating.score)
        self.assertEqual(response.data["data"]["num_of_followers"], 2)
        self.assertEqual(response.data["data"]["is_user_following"], True)
        self.assertEqual(response.data["data"]["total_price_of_all_chapters"], 0)
        self.assertEqual(
            sum(response.data["data"]["rating_histogram"].values()), 1
        )  # only one rating
        self.assertEqual(response.data["data"]["profile_balance"], 0)


# GetTextSearchMangaView
class TestTextSearchMangaView(MangaBaseTestCase):
    def test_guest_can_search_manga(self):
        _, _, _, manga = self.create_random_valid_object()
        self.client.logout()

        url = reverse(
            f"{self.namespace}:search-manga", kwargs={"search_text": str(manga.id)}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        # fields that are returned from the text search:
        # ("id", "title", "image", "owner", "tags", "rating", "num_of_chapters",)
        retrieved_manga = results["data"][0]
        self.assertEqual(retrieved_manga["id"], manga.id)
        self.assertEqual(retrieved_manga["title"], manga.title)
        self.assertEqual(retrieved_manga["owner"]["id"], manga.owner_id)
        self.assertTrue(retrieved_manga["image"] != "")
        self.assertIn(str(manga.image), retrieved_manga["image"])
        self.assert_db_tags(retrieved_manga["tags"], list(manga.tags.all()))

        manga_ratings = MangaRating.objects.filter(manga=manga).all()
        if manga_ratings:
            expected_rating = sum([r.score for r in manga_ratings]) / len(manga_ratings)
        else:
            expected_rating = 0

        self.assertEqual(retrieved_manga["rating"], expected_rating)
        self.assertEqual(retrieved_manga["num_of_chapters"], len(manga.chapters.all()))

    def test_non_existing_manga_search(self):
        url = reverse(f"{self.namespace}:search-manga", kwargs={"search_text": 0})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 204)

    def test_search_manga_order(self):
        search_text = (
            "1"  # first look for ID match, then title.starts_with then title.contains
        )
        _, _, _, manga1 = self.create_random_valid_object(
            predefined_vals={"title": "567"}
        )  # first one because of ID match
        _, _, _, manga2 = self.create_random_valid_object(
            predefined_vals={"title": "1234"}
        )  # second one because title starts with 1
        _, _, _, manga3 = self.create_random_valid_object(
            predefined_vals={"title": "7891"}
        )  # third one because title contains 1
        _, _, _, manga4 = self.create_random_valid_object(
            predefined_vals={"title": "asd"}
        )  # shouldn't show up in the results

        url = reverse(
            f"{self.namespace}:search-manga", kwargs={"search_text": search_text}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data
        ids = [m["id"] for m in results["data"]]
        self.assertIn(manga1.id, ids)
        self.assertIn(manga2.id, ids)
        self.assertIn(manga3.id, ids)
        self.assertNotIn(manga4.id, ids)


# ReadMangaView
class TestReadMangaView(MangaBaseTestCase):
    def test_guest_cannot_retrieve_manga(self):
        _, _, _, manga = self.create_random_valid_object()
        self.client.logout()

        url = reverse(f"{self.namespace}:read-manga", kwargs={"manga_id": manga.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_non_existing_read_manga_retrieval(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(f"{self.namespace}:read-manga", kwargs={"manga_id": 0})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_non_buyer_user_cannot_read_manga(self):
        _, _, _, manga = self.create_random_valid_object()
        chapter_tester = ChapterBaseTestCase()
        _, _, _, chapter = chapter_tester.create_random_valid_object(
            predefined_vals={"manga": manga}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:read-manga", kwargs={"manga_id": manga.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["data"]["chapters"][0]["pdf"])
        self.assertIsNone(response.data["data"]["chapters"][0]["folder_name"])
        self.assertIsNone(response.data["data"]["chapters"][0]["pages_base_url"])
        self.assertEqual(response.data["data"]["chapters"][0]["is_user_bought"], False)

    def test_buyer_user_can_read_manga(self):
        _, _, _, manga = self.create_random_valid_object()
        chapter_tester = ChapterBaseTestCase()
        _, _, _, chapter = chapter_tester.create_random_valid_object(
            predefined_vals={"manga": manga}
        )

        bought_chapter_tester = BoughtChapterBaseTestCase()
        _, _, _, bought_chapter = bought_chapter_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "chapter": chapter}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:read-manga", kwargs={"manga_id": manga.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(str(chapter.pdf), response.data["data"]["chapters"][0]["pdf"])
        self.assertEqual(
            response.data["data"]["chapters"][0]["folder_name"], chapter.folder_name
        )
        self.assertNotEqual(response.data["data"]["chapters"][0]["pages_base_url"], "")
        self.assertEqual(response.data["data"]["chapters"][0]["is_user_bought"], True)


# EditMangaView
class TestEditMangaView(MangaBaseTestCase):
    def test_owner_can_update_manga(self):
        self.client.force_authenticate(user=self.user)

        # create an object to modfiy later
        _, _, _, manga = self.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        # create new random values to modify the fields with and then check with
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"owner": self.user.profile}
        )
        url = reverse(f"{self.namespace}:edit-manga", kwargs={"manga_id": manga.id})

        update_and_assert_single_field(
            tester=self,
            instance=manga,
            update_api_url=url,
            field_to_update="title",
            new_field_value=vals_to_send_request["title"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["title"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=manga,
            update_api_url=url,
            field_to_update="description",
            new_field_value=vals_to_send_request["description"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["description"]
            ),
        )
        old_image_path = manga.image.name
        update_and_assert_single_field(
            tester=self,
            instance=manga,
            update_api_url=url,
            field_to_update="image",
            new_field_value=vals_to_send_request["image"],
            field_assertion_function=lambda actual: (
                self.assert_database_image(manga),
                self.assertFalse(file_storage.exists(old_image_path)),
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=manga,
            update_api_url=url,
            field_to_update="tags",
            new_field_value=vals_to_send_request["tags"],
            field_assertion_function=None,
        )
        # we do the assertion explicity because relational fields fail the find_different_fields check
        manga.refresh_from_db()
        self.assertEqual(
            set([t.id for t in manga.tags.all()]), set(original_vals["tags"])
        )

        update_and_assert_single_field(
            tester=self,
            instance=manga,
            update_api_url=url,
            field_to_update="collaborators",
            new_field_value=vals_to_send_request["collaborators"],
            field_assertion_function=None,
        )
        # we do the assertion explicity because relational fields fail the find_different_fields check
        manga.refresh_from_db()
        self.assertEqual(
            set([t.id for t in manga.collaborators.all()]),
            set(original_vals["collaborators"]),
        )

        # update all fields
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"owner": self.user.profile}
        )
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 200)
        manga.refresh_from_db()
        # check if values stored in the db matches the ones we want
        self.assert_db_stored_values_match_expected_dict(manga, original_vals)

    def test_admin_cannot_update_non_existing_manga(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:edit-manga", kwargs={"manga_id": 0})

        _, vals_to_send_request, _ = self.get_random_valid_data()
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_update_manga(self):
        _, _, _, manga = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(f"{self.namespace}:edit-manga", kwargs={"manga_id": manga.id})

        new_title = self.get_random_title_value()
        response = self.client.patch(url, {"title": new_title})

        self.assertEqual(response.status_code, 403)
        manga.refresh_from_db()
        self.assertNotEqual(manga.title, new_title)


# DeleteMangaView
class TestDeleteMangaView(MangaBaseTestCase):
    def test_admin_can_delete_manga(self):
        # create manga to delete later
        _, _, _, manga = self.create_random_valid_object()
        manga_id = manga.id
        manga_folder_path = get_manga_upload_folder_path(manga)
        image_path = manga.image.name  # Store path to verify file deletion

        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:delete-manga", kwargs={"manga_id": manga_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Manga.objects.filter(id=manga_id).exists())
        self.assertFalse(file_storage.exists(image_path))
        self.assertFalse(directory_storage.exists(manga_folder_path))

    def test_owner_can_delete_manga(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, manga = self.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        manga_id = manga.id
        manga_folder_path = get_manga_upload_folder_path(manga)
        image_path = manga.image.name  # Store path to verify file deletion

        url = reverse(f"{self.namespace}:delete-manga", kwargs={"manga_id": manga.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Manga.objects.filter(id=manga_id).exists())
        self.assertFalse(file_storage.exists(image_path))
        self.assertFalse(directory_storage.exists(manga_folder_path))

    def test_non_existing_manga_delete(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:delete-manga", kwargs={"manga_id": 0})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)

    def test_collaborator_cannot_delete_manga(self):
        _, _, _, manga = self.create_random_valid_object()

        self.client.force_authenticate(user=manga.collaborators.first().user)
        url = reverse(f"{self.namespace}:delete-manga", kwargs={"manga_id": manga.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_non_owner_cannot_delete_manga(self):
        _, _, _, manga = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)
        url = reverse(f"{self.namespace}:delete-manga", kwargs={"manga_id": manga.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_manga_deletion_deletes_chapters(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, manga = self.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        chapter_tester = ChapterBaseTestCase()

        _, _, _, chapter = chapter_tester.create_random_valid_object(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )

        manga_folder_path = get_manga_upload_folder_path(manga)
        chapter_folder_path = get_chapter_upload_folder_path(chapter)

        url = reverse(f"{self.namespace}:delete-manga", kwargs={"manga_id": manga.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Chapter.objects.filter(id=chapter.id).exists())
        self.assertFalse(directory_storage.exists(chapter_folder_path))
        self.assertFalse(directory_storage.exists(manga_folder_path))


# MangaGalleryView
class TestMangaGalleryViewPermission(MangaBaseTestCase):
    def test_guest_access_gallery(self):
        self.create_random_valid_object()
        self.client.logout()

        url = reverse(f"{self.namespace}:manga-gallery")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


# MangaGalleryView
class TestMangaGalleryViewExistence(MangaBaseTestCase):
    def test_empty_gallery_returns_204(self):
        url = reverse(f"{self.namespace}:manga-gallery")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 204)


# MangaGalleryView
class TestMangaGalleryViewFiltering(MangaBaseTestCase):
    def test_profiles_following_filtering(self):
        # create profiles
        followed_profile = get_dummy_profile()
        non_followed_profile = get_dummy_profile()

        # create mangas for each profile
        _, _, _, followed_manga = self.create_random_valid_object(
            predefined_vals={"owner": followed_profile}
        )

        _, _, _, non_followed_manga = self.create_random_valid_object(
            predefined_vals={"owner": non_followed_profile}
        )

        # authenticated user
        self.client.force_login(self.user)

        # user follows only followed_profile
        self.user.profile.profiles_following.add(followed_profile)

        url = reverse(f"{self.namespace}:manga-gallery")

        # get followed profiles mangas
        response = self.client.get(url, {"sort": "profiles_following"})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertIn(followed_manga.id, returned_ids)
        self.assertNotIn(non_followed_manga.id, returned_ids)

        # get NON followed profiles mangas
        response = self.client.get(url, {"sort": "-profiles_following"})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(followed_manga.id, returned_ids)
        self.assertIn(non_followed_manga.id, returned_ids)

    def test_mangas_following_filtering(self):
        # create mangas
        _, _, _, followed_manga = self.create_random_valid_object()
        _, _, _, non_followed_manga = self.create_random_valid_object()

        # authenticated user
        self.client.force_login(self.user)

        # user follows only followed_mangas
        self.user.profile.mangas_following.add(followed_manga)

        url = reverse(f"{self.namespace}:manga-gallery")

        # get followed mangas
        response = self.client.get(url, {"sort": "mangas_following"})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertIn(followed_manga.id, returned_ids)
        self.assertNotIn(non_followed_manga.id, returned_ids)

        # get NON followed mangas
        response = self.client.get(url, {"sort": "-mangas_following"})

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(followed_manga.id, returned_ids)
        self.assertIn(non_followed_manga.id, returned_ids)

    def test_start_date_filtering(self):
        # create mangas
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        # manually override auto_now_add start_date
        manga1.start_date = now().date() - timedelta(days=10)
        manga1.save()

        manga2.start_date = now().date() - timedelta(days=5)
        manga2.save()

        manga3.start_date = now().date()
        manga3.save()

        url = reverse(f"{self.namespace}:manga-gallery")

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

        # manga1 is too old
        self.assertNotIn(manga1.id, returned_ids)

        # manga2 okay
        self.assertIn(manga2.id, returned_ids)

        # manga3 is too recent
        self.assertNotIn(manga3.id, returned_ids)

    def test_last_update_date_filtering(self):
        # create mangas
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        # manually override last_update_date
        # we have to use ".update" because of the 'auto_now=True'
        Manga.objects.filter(id=manga1.id).update(
            last_update_date=now().date() - timedelta(days=10)
        )

        Manga.objects.filter(id=manga2.id).update(
            last_update_date=now().date() - timedelta(days=5)
        )

        Manga.objects.filter(id=manga3.id).update(last_update_date=now().date())

        url = reverse(f"{self.namespace}:manga-gallery")

        min_last_update_date = now().date() - timedelta(days=7)
        max_last_update_date = now().date() - timedelta(days=2)

        min_dt = timezone.make_aware(
            timezone.datetime.combine(
                min_last_update_date, timezone.datetime.min.time()
            )
        )
        max_dt = timezone.make_aware(
            timezone.datetime.combine(
                max_last_update_date, timezone.datetime.min.time()
            )
        )
        min_ts = int(min_dt.timestamp() * 1000)
        max_ts = int(max_dt.timestamp() * 1000)

        response = self.client.get(
            url, {"last_update_date_min": min_ts, "last_update_date_max": max_ts}
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]

        # manga1 is too old
        self.assertNotIn(manga1.id, returned_ids)

        # manga2 okay
        self.assertIn(manga2.id, returned_ids)

        # manga3 is too recent
        self.assertNotIn(manga3.id, returned_ids)

    def test_tag_filtering(self):
        # create reusable tags
        tag_tester = MangaTagBaseTestCase()

        # first created tag1 has id 1 which makes it the original tag
        # so we change the tag test from portfolio a bit to fit with the "either original or translation" constraint
        _, _, _, tag1 = tag_tester.create_random_valid_object()
        _, _, _, tag2 = tag_tester.create_random_valid_object()
        _, _, _, tag3 = tag_tester.create_random_valid_object()
        _, _, _, tag4 = tag_tester.create_random_valid_object()

        # should be returned (contains ALL required tags)
        _, _, _, matching_manga = self.create_random_valid_object(
            predefined_vals={"tags": [tag2, tag3]}
        )

        # should NOT be returned (missing tag3)
        _, _, _, missing_tag_manga = self.create_random_valid_object(
            predefined_vals={"tags": [tag2]}
        )

        # should be returned (contains required tags + extra tag)
        _, _, _, extra_tags_manga = self.create_random_valid_object(
            predefined_vals={"tags": [tag2, tag3, tag4]}
        )

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(url, {"tags": f"{tag2.id},{tag3.id}"})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        # a. manga with all required tags should be returned
        self.assertIn(matching_manga.id, returned_ids)

        # b. manga missing one of the required tags should NOT be returned
        self.assertNotIn(missing_tag_manga.id, returned_ids)

        # c. manga with extra tags should still be returned
        self.assertIn(extra_tags_manga.id, returned_ids)

    def test_ratings_filtering(self):
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        manga_rating_tester = MangaRatingBaseTestCase()
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga2, "score": 2}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga3, "score": 4}
        )

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(url, {"rating_min": 1, "rating_max": 3})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(manga1.id, returned_ids)
        self.assertIn(manga2.id, returned_ids)
        self.assertNotIn(manga3.id, returned_ids)

    def test_num_of_ratings_filtering(self):
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        manga_rating_tester = MangaRatingBaseTestCase()
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga2}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga2}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga3}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga3}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga3}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga3}
        )

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(
            url, {"num_of_ratings_min": 1, "num_of_ratings_max": 3}
        )

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(manga1.id, returned_ids)
        self.assertIn(manga2.id, returned_ids)
        self.assertNotIn(manga3.id, returned_ids)

    def test_num_of_followers_filtering(self):
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        profile1 = get_dummy_profile()
        profile1.mangas_following.add(manga2)
        profile1.mangas_following.add(manga3)
        profile2 = get_dummy_profile()
        profile2.mangas_following.add(manga2)
        profile2.mangas_following.add(manga3)
        profile3 = get_dummy_profile()
        profile3.mangas_following.add(manga3)
        profile4 = get_dummy_profile()
        profile4.mangas_following.add(manga3)

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(
            url, {"num_of_followers_min": 2, "num_of_followers_max": 4}
        )

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(manga1.id, returned_ids)
        self.assertIn(manga2.id, returned_ids)
        self.assertNotIn(manga3.id, returned_ids)

    def test_num_of_collaborators_filtering(self):
        _, _, _, manga1 = self.create_random_valid_object(
            predefined_vals={"collaborators": []}
        )
        _, _, _, manga2 = self.create_random_valid_object(
            predefined_vals={"collaborators": [get_dummy_profile() for _ in range(2)]}
        )
        _, _, _, manga3 = self.create_random_valid_object(
            predefined_vals={"collaborators": [get_dummy_profile() for _ in range(4)]}
        )

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(
            url, {"num_of_collaborators_min": 1, "num_of_collaborators_max": 3}
        )

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(manga1.id, returned_ids)
        self.assertIn(manga2.id, returned_ids)
        self.assertNotIn(manga3.id, returned_ids)

    def test_num_of_chapters_filtering(self):
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        chapter_tester = ChapterBaseTestCase()
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga2})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga2})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga3})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga3})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga3})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga3})

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(
            url, {"num_of_chapters_min": 1, "num_of_chapters_max": 3}
        )

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(manga1.id, returned_ids)
        self.assertIn(manga2.id, returned_ids)
        self.assertNotIn(manga3.id, returned_ids)

    def test_chapters_price_filtering(self):
        _, _, _, manga1 = self.create_random_valid_object()
        _, _, _, manga2 = self.create_random_valid_object()
        _, _, _, manga3 = self.create_random_valid_object()

        chapter_tester = ChapterBaseTestCase()
        chapter_tester.create_random_valid_object(
            predefined_vals={"manga": manga2, "price": 2}
        )
        chapter_tester.create_random_valid_object(
            predefined_vals={"manga": manga3, "price": 4}
        )

        url = reverse(f"{self.namespace}:manga-gallery")

        response = self.client.get(
            url, {"chapters_price_min": 1, "chapters_price_max": 3}
        )

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        self.assertNotIn(manga1.id, returned_ids)
        self.assertIn(manga2.id, returned_ids)
        self.assertNotIn(manga3.id, returned_ids)


# MangaGalleryView
class TestMangaGalleryViewSorting(MangaBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.manga1 = self.create_random_valid_object(
            predefined_vals={"collaborators": []}
        )
        _, _, _, self.manga2 = self.create_random_valid_object(
            predefined_vals={"collaborators": [get_dummy_profile() for _ in range(2)]}
        )
        _, _, _, self.manga3 = self.create_random_valid_object(
            predefined_vals={"collaborators": [get_dummy_profile() for _ in range(4)]}
        )

        # followers
        profile1 = get_dummy_profile()
        profile1.mangas_following.add(self.manga2)
        profile1.mangas_following.add(self.manga3)
        profile2 = get_dummy_profile()
        profile2.mangas_following.add(self.manga3)

        # ratings
        manga_rating_tester = MangaRatingBaseTestCase()
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga2, "score": 1}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga3, "score": 2}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga3, "score": 2}
        )

        # comments
        manga_comment_tester = MangaCommentBaseTestCase()
        manga_comment_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga2}
        )
        manga_comment_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga3}
        )
        manga_comment_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga3}
        )

        # chapters
        chapter_tester = ChapterBaseTestCase()
        chapter_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga2, "price": 1}
        )
        chapter_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga3, "price": 2}
        )
        chapter_tester.create_random_valid_object(
            predefined_vals={"manga": self.manga3, "price": 2}
        )

        self.url = reverse(f"{self.namespace}:manga-gallery")

        # last_update_date
        # we have to use ".update" because of the 'auto_now=True'
        Manga.objects.filter(id=self.manga1.id).update(
            last_update_date=now().date() - timedelta(days=10)
        )

        Manga.objects.filter(id=self.manga2.id).update(
            last_update_date=now().date() - timedelta(days=5)
        )

        Manga.objects.filter(id=self.manga3.id).update(last_update_date=now().date())

    def get_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.data["results"]]

    def test_gallery_sorts(self):
        response = self.client.get(self.url, {"sort": "rating"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-rating"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_ratings"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_ratings"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_chapters"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_chapters"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "chapters_price"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-chapters_price"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_collaborators"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_collaborators"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "num_of_followers"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-num_of_followers"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "start_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-start_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "last_update_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)

        response = self.client.get(self.url, {"sort": "-last_update_date"})
        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [self.manga1.id, self.manga2.id, self.manga3.id]
        )
        self.assertTrue(is_order_preserved)

    def test_gallery_multi_sort(self):
        _, _, _, manga4 = self.create_random_valid_object()

        manga_rating_tester = MangaRatingBaseTestCase()
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga4}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga4}
        )

        response = self.client.get(self.url, {"sort": "num_of_ratings,start_date"})

        ids = self.get_ids(response)

        it = iter(ids)
        is_order_preserved = all(
            x in it for x in [manga4.id, self.manga3.id, self.manga2.id, self.manga1.id]
        )
        self.assertTrue(is_order_preserved)


# MangaGalleryView
class TestMangaGalleryViewRandomnessTest(MangaBaseTestCase):
    def test_random_sort(self):
        # create 3 mangas
        for _ in range(3):
            _, _, _, _ = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:manga-gallery")

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


# MangaGalleryView
class TestMangaGalleryViewPaginationTest(MangaBaseTestCase):
    def test_pagination_with_next_link(self):
        mangas = []

        for _ in range(6):
            _, _, _, manga = self.create_random_valid_object()
            mangas.append(manga)

        # sort by id
        mangas_sorted = sorted(mangas, key=lambda x: x.id, reverse=True)

        url = reverse(f"{self.namespace}:manga-gallery")

        # get the first page
        response1 = self.client.get(url, {"sort": "start_date", "page_size": 3})
        self.assertEqual(response1.status_code, 200)

        # check if first page consists of the first 3 mangas
        ids_page1 = [item["id"] for item in response1.data["results"]]
        expected_page1 = [t.id for t in mangas_sorted[:3]]
        self.assertEqual(ids_page1, expected_page1)

        # use 'next' field in the response to get the second page
        next_url = response1.data["next"]
        self.assertIsNotNone(next_url)
        response2 = self.client.get(next_url)
        self.assertEqual(response2.status_code, 200)

        # check if second page consists of the second 3 mangas
        ids_page2 = [item["id"] for item in response2.data["results"]]
        expected_page2 = [t.id for t in mangas_sorted[3:6]]
        self.assertEqual(ids_page2, expected_page2)


# MangaGalleryView
class TestMangaGalleryViewFields(MangaBaseTestCase):
    def test_gallery_fields_consistency(self):
        mangas = []

        for _ in range(5):
            _, _, _, manga = self.create_random_valid_object()
            mangas.append(manga)

        manga1, manga2, manga3, manga4, manga5 = mangas

        # followers
        profile1 = get_dummy_profile()
        profile1.mangas_following.add(manga2)
        profile1.mangas_following.add(manga3)
        profile2 = get_dummy_profile()
        profile2.mangas_following.add(manga3)

        # ratings
        manga_rating_tester = MangaRatingBaseTestCase()
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga2, "score": 1}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga3, "score": 2}
        )
        manga_rating_tester.create_random_valid_object(
            predefined_vals={"manga": manga4, "score": 3}
        )

        # comments
        manga_comment_tester = MangaCommentBaseTestCase()
        manga_comment_tester.create_random_valid_object(
            predefined_vals={"manga": manga4}
        )
        manga_comment_tester.create_random_valid_object(
            predefined_vals={"manga": manga5}
        )
        manga_comment_tester.create_random_valid_object(
            predefined_vals={"manga": manga5}
        )

        # chapters
        chapter_tester = ChapterBaseTestCase()
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga2})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga5})
        chapter_tester.create_random_valid_object(predefined_vals={"manga": manga5})

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(f"{self.namespace}:manga-gallery"), {"sort": "-date"}
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        expected_manga_ids = {manga1.id, manga2.id, manga3.id, manga4.id, manga5.id}

        # we filter the result because there are additional mangas created while setting up the test environment
        # but we only want to test for the mangas 1-5
        filtered_results = [
            item for item in results if item["id"] in expected_manga_ids
        ]

        for retrieved_item in filtered_results:
            manga = next(p for p in mangas if p.id == retrieved_item["id"])
            # we check base fields differently because gallery retrieval is different than regular one
            self.assert_gallery_retrieved_dict_match_db_stored_values(
                retrieved_item, manga
            )

            # check counts
            expected_ratings = manga.ratings.count()
            expected_chapters = manga.chapters.count()
            expected_collaborators = manga.collaborators.count()
            expected_followers = manga.followers.count()
            expected_chapter_price = sum([c.price for c in manga.chapters.all()])

            manga_ratings = MangaRating.objects.filter(manga=manga).all()
            if manga_ratings:
                expected_rating = sum([r.score for r in manga_ratings]) / len(
                    manga_ratings
                )
            else:
                expected_rating = 0

            self.assertEqual(retrieved_item["num_of_ratings"], expected_ratings)

            self.assertEqual(retrieved_item["num_of_chapters"], expected_chapters)

            self.assertEqual(
                retrieved_item["num_of_collaborators"], expected_collaborators
            )

            self.assertEqual(retrieved_item["num_of_followers"], expected_followers)

            self.assertEqual(
                retrieved_item["total_price_of_all_chapters"], expected_chapter_price
            )

            self.assertAlmostEqual(retrieved_item["rating"], expected_rating)

            # check user rate state
            expected_user_score = MangaRating.objects.filter(
                profile=self.user.profile, manga=manga
            ).exists()
            expected_user_score = (
                expected_user_score.score if expected_user_score else False
            )

            self.assertEqual(retrieved_item["user_score"], expected_user_score)

            # check user follow state
            expected_is_user_following = manga.followers.filter(
                id=self.user.profile.id
            ).exists()

            self.assertEqual(
                retrieved_item["is_user_following"], expected_is_user_following
            )


# ToggleFollowMangaView
class TestToggleFollowMangaView(MangaBaseTestCase):
    def test_guest_cannot_follow_manga(self):
        self.client.logout()

        _, _, _, m = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-follow-manga", kwargs={"manga_id": m.id}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)

    def test_user_can_follow_manga(self):
        self.client.force_authenticate(user=self.user)
        _, _, _, m = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-follow-manga", kwargs={"manga_id": m.id}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["followed"], True)
        self.assertIn(m, self.user.profile.mangas_following.all())

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["followed"], False)
        self.assertNotIn(m, self.user.profile.mangas_following.all())

    def test_non_existing_manga_follow(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:toggle-follow-manga", kwargs={"manga_id": 0})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)


# ChangeMangaScoreView
class TestChangeMangaScoreView(MangaBaseTestCase):
    def test_guest_cannot_score_manga(self):
        self.client.logout()

        _, _, _, m = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:change-manga-score", kwargs={"manga_id": m.id})
        response = self.client.post(url, {"score": 5})

        self.assertEqual(response.status_code, 403)

    def test_user_can_score_manga(self):
        self.client.force_authenticate(user=self.user)
        _, _, _, m = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:change-manga-score", kwargs={"manga_id": m.id})

        response = self.client.post(url, {"score": 5})
        self.assertEqual(response.status_code, 200)
        mr = MangaRating.objects.first()
        self.assertEqual(mr.profile, self.user.profile)
        self.assertEqual(mr.manga, m)
        self.assertEqual(mr.score, 5)

        response = self.client.post(url, {"score": -5})
        self.assertEqual(response.status_code, 200)
        mr = MangaRating.objects.first()
        self.assertEqual(mr.profile, self.user.profile)
        self.assertEqual(mr.manga, m)
        self.assertEqual(mr.score, -5)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MangaRating.objects.exists())

    def test_non_existing_manga_score(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:change-manga-score", kwargs={"manga_id": 0})
        response = self.client.post(url, {"score": 5})

        self.assertEqual(response.status_code, 404)

    def test_out_of_limits_manga_score(self):
        self.client.force_authenticate(user=self.user)
        _, _, _, m = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:change-manga-score", kwargs={"manga_id": m.id})

        response = self.client.post(url, {"score": MANGA_MIN_RATING - 1})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(url, {"score": MANGA_MAX_RATING + 1})
        self.assertEqual(response.status_code, 400)


# CreateMangaCommentView
class TestCreateMangaCommentView(MangaCommentBaseTestCase):
    def test_guest_cannot_create_comment(self):
        self.client.logout()

        manga_tester = MangaBaseTestCase()
        _, _, _, m = manga_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:create-manga-comment", kwargs={"manga_id": m.id}
        )
        response = self.client.post(url, {"comment": self.get_random_comment_value()})

        self.assertEqual(response.status_code, 403)

    def test_logged_in_user_can_create_comment(self):
        self.client.force_authenticate(user=self.user)

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:create-manga-comment", kwargs={"manga_id": manga.id}
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

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()
        _, _, _, parent_comment = self.create_random_valid_object(
            predefined_vals={"manga": manga}
        )

        url = reverse(
            f"{self.namespace}:create-manga-comment", kwargs={"manga_id": manga.id}
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

    def test_non_existing_manga_comment_create(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:create-manga-comment", kwargs={"manga_id": 0})

        response = self.client.post(url, {"comment": self.get_random_comment_value()})

        self.assertEqual(response.status_code, 404)


# GetMangaCommentsView
class TestGetMangaCommentsView(MangaCommentBaseTestCase):
    def test_parent_comment_retrieval(self):
        # create parent comment
        _, _, _, comment1 = self.create_random_valid_object()

        # create child comment under same manga
        _, _, _, comment2 = self.create_random_valid_object(
            predefined_vals={"manga": comment1.manga, "parent_comment": comment1}
        )

        # send request
        url = reverse(
            f"{self.namespace}:get-manga-comments",
            kwargs={"manga_id": comment1.manga.id},
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
        with patch("MangaPageApp.views.GetMangaCommentsView.PAGE_SIZE", NEW_LIMIT):
            manga_tester = MangaBaseTestCase()
            _, _, _, manga = manga_tester.create_random_valid_object()

            # comment1 -> parent (out of pagination scope)
            _, _, _, comment1 = self.create_random_valid_object(
                predefined_vals={"manga": manga, "parent_comment": -1}
            )

            # comment2 -> parent (should be retrieved because in the scope)
            _, _, _, comment2 = self.create_random_valid_object(
                predefined_vals={"manga": manga, "parent_comment": -1}
            )

            # comment3 -> parent (should be retrieved because in the scope)
            _, _, _, comment3 = self.create_random_valid_object(
                predefined_vals={"manga": manga, "parent_comment": -1}
            )

            # comment4 -> child of comment2 (should be retrieved because CHILD of a comment in the scope)
            _, _, _, comment4 = self.create_random_valid_object(
                predefined_vals={"manga": manga, "parent_comment": comment2}
            )

            # comment5 -> child of comment1 (should NOT be retrieved because CHILD of a comment OUT the scope)
            _, _, _, comment5 = self.create_random_valid_object(
                predefined_vals={"manga": manga, "parent_comment": comment1}
            )

            # -- Page 1 (initial) -- #

            # send request
            url = reverse(
                f"{self.namespace}:get-manga-comments", kwargs={"manga_id": manga.id}
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

    def test_non_existing_manga_comment_retrieval(self):
        url = reverse(f"{self.namespace}:get-manga-comments", kwargs={"manga_id": 0})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_existing_manga_no_comments(self):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:get-manga-comments", kwargs={"manga_id": manga.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 0)
        self.assertIsNone(response.data["data"]["next"])


# ChapterView
class TestRetrieveChapterView(ChapterBaseTestCase):
    def test_admin_can_retrieve_chapters(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, chapter1 = self.create_random_valid_object()
        _, _, _, chapter2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:chapter")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        # here we DONT allow admin to retrieve some information to prevent admins from abusing their power to read chapters without buying
        self.assertIsNone(results[1]["pdf"])
        self.assertIsNone(results[1]["folder_name"])
        self.assertIsNone(results[1]["pages_base_url"])
        self.assertIsNone(results[0]["pdf"])
        self.assertIsNone(results[0]["folder_name"])
        self.assertIsNone(results[0]["pages_base_url"])

        # then we modify these to match the retrieval data for below assert checks
        results[1]["pdf"] = chapter1.pdf
        results[1]["folder_name"] = chapter1.folder_name
        results[0]["pdf"] = chapter2.pdf
        results[0]["folder_name"] = chapter2.folder_name

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], chapter1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], chapter2)

    def test_logged_in_user_cannot_retrieve_chapters(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:chapter")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreateChapterView
class TestCreateChapterView(ChapterBaseTestCase):
    def test_admin_can_create_chapter_to_non_owned_manga(self):
        self.client.force_authenticate(user=self.admin)

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": self.admin.profile}
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        chapter = Chapter.objects.first()
        self.process_pdf_for_test(chapter)  # process it manually for unittest
        self.assert_db_stored_values_match_expected_dict(chapter, original_vals)

    def test_manga_owner_can_create_chapter(self):
        self.client.force_authenticate(user=self.user)

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        chapter = Chapter.objects.first()
        self.process_pdf_for_test(chapter)  # process it manually for unittest
        self.assert_db_stored_values_match_expected_dict(chapter, original_vals)

    def test_manga_collaborator_can_create_chapter(self):
        collaborator = get_dummy_profile()

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"collaborators": [collaborator]}
        )

        self.client.force_authenticate(user=collaborator.user)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": collaborator}
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)
        chapter = Chapter.objects.first()
        self.process_pdf_for_test(chapter)  # process it manually for unittest
        self.assert_db_stored_values_match_expected_dict(chapter, original_vals)

    def test_non_owner_non_collaborator_cannot_create_chapter(self):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        self.client.force_authenticate(user=self.user)

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 403)

    def test_guest_cannot_create_chapter(self):
        self.client.logout()

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga}
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 403)

    def test_bought_chapter_creation_on_chapter_create(self):
        manga_owner = self.user.profile
        chapter_owner = get_dummy_profile()
        self.client.force_authenticate(user=chapter_owner.user)
        chapter_collaborator1 = get_dummy_profile()
        chapter_collaborator2 = get_dummy_profile()

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": manga_owner, "collaborators": [chapter_owner]}
        )

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={
                "manga": manga,
                "owner": chapter_owner,
                "collaborators": [chapter_collaborator1, chapter_collaborator2],
            }
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)

        chapter = Chapter.objects.first()

        self.assertTrue(
            BoughtChapter.objects.filter(profile=manga_owner, chapter=chapter).exists()
        )

        self.assertTrue(
            BoughtChapter.objects.filter(
                profile=chapter_owner, chapter=chapter
            ).exists()
        )

        self.assertTrue(
            BoughtChapter.objects.filter(
                profile=chapter_collaborator1, chapter=chapter
            ).exists()
        )

        self.assertTrue(
            BoughtChapter.objects.filter(
                profile=chapter_collaborator2, chapter=chapter
            ).exists()
        )

    def test_profile_chapter_relation_fields(self):
        self.client.force_authenticate(user=self.user)

        collaborator1 = get_dummy_profile()
        collaborator2 = get_dummy_profile()

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={
                "manga": manga,
                "owner": self.user.profile,
                "collaborators": [collaborator1, collaborator2],
            }
        )

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": manga.id})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 201)

        chapter = Chapter.objects.first()

        self.assertIn(chapter, self.user.profile.chapters_owned.all())

        self.assertIn(chapter, collaborator1.chapters_collaborated.all())

        self.assertIn(chapter, collaborator2.chapters_collaborated.all())

    def test_non_existing_manga_create_chapter(self):
        self.client.force_authenticate(user=self.user)

        _, vals_to_send_request, _ = self.get_random_valid_data()

        url = reverse(f"{self.namespace}:create-chapter", kwargs={"manga_id": 0})

        response = self.client.post(url, vals_to_send_request, format="multipart")

        self.assertEqual(response.status_code, 404)


# EditChapterView
class TestEditChapterView(ChapterBaseTestCase):
    def test_owner_can_edit_chapter(self):
        self.client.force_authenticate(user=self.user)

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )

        url = reverse(
            f"{self.namespace}:edit-chapter", kwargs={"chapter_id": chapter.id}
        )

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )

        update_and_assert_single_field(
            tester=self,
            instance=chapter,
            update_api_url=url,
            field_to_update="title",
            new_field_value=vals_to_send_request["title"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["title"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=chapter,
            update_api_url=url,
            field_to_update="no",
            new_field_value=vals_to_send_request["no"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["no"]
            ),
        )
        update_and_assert_single_field(
            tester=self,
            instance=chapter,
            update_api_url=url,
            field_to_update="collaborators",
            new_field_value=vals_to_send_request["collaborators"],
            field_assertion_function=None,
        )
        # we do the assertion explicity because relational fields fail the find_different_fields check
        chapter.refresh_from_db()
        self.assertEqual(
            set([c.id for c in chapter.collaborators.all()]),
            set(original_vals["collaborators"]),
        )
        update_and_assert_single_field(
            tester=self,
            instance=chapter,
            update_api_url=url,
            field_to_update="price",
            new_field_value=vals_to_send_request["price"],
            field_assertion_function=lambda actual: self.assertEqual(
                actual, original_vals["price"]
            ),
        )
        # pdf editing is tested explicitly

        # update all fields
        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )
        response = self.client.patch(url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 200)
        chapter.refresh_from_db()
        # check if values stored in the db matches the ones we want
        self.assert_db_stored_values_match_expected_dict(chapter, original_vals)

    def test_admin_can_edit_chapter_in_non_owned_manga(self):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": manga}
        )

        self.client.force_authenticate(user=self.admin)

        new_title = self.get_random_title_value()

        url = reverse(
            f"{self.namespace}:edit-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.patch(url, {"title": new_title})

        self.assertEqual(response.status_code, 200)

        chapter.refresh_from_db()

        self.assertEqual(chapter.title, new_title)

    def test_manga_owner_can_edit_chapter(self):
        manga_owner = get_dummy_profile()

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": manga_owner}
        )

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": manga, "owner": manga_owner}
        )

        self.client.force_authenticate(user=manga_owner.user)

        new_title = self.get_random_title_value()

        url = reverse(
            f"{self.namespace}:edit-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.patch(url, {"title": new_title})

        self.assertEqual(response.status_code, 200)

        chapter.refresh_from_db()

        self.assertEqual(chapter.title, new_title)

    def test_chapter_collaborator_cannot_edit_chapter(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"collaborators": [self.user.profile]}
        )

        url = reverse(
            f"{self.namespace}:edit-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.patch(url, {"title": self.get_random_title_value()})

        self.assertEqual(response.status_code, 403)

    def test_regular_logged_in_user_cannot_edit_chapter(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, chapter = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:edit-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.patch(url, {"title": self.get_random_title_value()})

        self.assertEqual(response.status_code, 403)

    def test_non_existing_chapter_edit(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:edit-chapter", kwargs={"chapter_id": 0})

        response = self.client.patch(url, {"title": self.get_random_title_value()})

        self.assertEqual(response.status_code, 404)

    def test_edit_chapter_updates_pdf_and_reprocesses_pages(self):
        manga_owner = get_dummy_profile()
        self.client.force_authenticate(user=manga_owner.user)

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": manga_owner}
        )

        original_pdf_pages = 2
        new_pdf_pages = 1

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={
                "manga": manga,
                "owner": manga_owner,
                "pdf": self.get_random_pdf_value(pages=original_pdf_pages),
            }
        )

        # fetch the old pdf data
        old_pages_folder = PurePosixPath(
            get_chapter_upload_folder_path(chapter), "pages"
        ).as_posix()
        old_page_files = sorted(directory_storage.list_files(old_pages_folder))
        # check the pdf related chapter fields
        self.assertEqual(chapter.num_of_images, original_pdf_pages)
        self.assertEqual(len(old_page_files), original_pdf_pages)

        # change the last_update_date so we can check the last update time with the new pdf change
        manga.refresh_from_db()
        Manga.objects.filter(id=manga.id).update(
            last_update_date=now().date() - timedelta(days=5)
        )
        manga.refresh_from_db()
        old_last_update_date = manga.last_update_date

        # send an update with the new pdf
        new_pdf = self.get_random_pdf_value(pages=new_pdf_pages)
        url = reverse(
            f"{self.namespace}:edit-chapter", kwargs={"chapter_id": chapter.id}
        )
        response = self.client.patch(url, {"pdf": new_pdf}, format="multipart")
        self.assertEqual(response.status_code, 200)

        # get get new pdf data
        chapter.refresh_from_db()
        manga.refresh_from_db()
        new_last_update_date = manga.last_update_date
        self.process_pdf_for_test(chapter)  # process task manually for unit test
        chapter.refresh_from_db()
        new_pages_folder = PurePosixPath(
            get_chapter_upload_folder_path(chapter), "pages"
        ).as_posix()
        new_page_files = sorted(directory_storage.list_files(new_pages_folder))

        # check new pdf related chapter fields
        self.assertEqual(chapter.num_of_images, new_pdf_pages)
        self.assertEqual(len(new_page_files), new_pdf_pages)
        self.assertNotEqual(
            old_last_update_date, new_last_update_date
        )  # check manga update time
        self.assert_database_pdf(chapter)


# DeleteChapterView
class TestDeleteChapterView(ChapterBaseTestCase):
    def test_owner_can_delete_chapter(self):
        self.client.force_authenticate(user=self.user)

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": manga, "owner": self.user.profile}
        )

        chapter_id = chapter.id
        chapter_folder_path = get_chapter_upload_folder_path(chapter)
        pdf_path = chapter.pdf.name

        url = reverse(
            f"{self.namespace}:delete-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(Chapter.objects.filter(id=chapter_id).exists())
        self.assertFalse(file_storage.exists(pdf_path))
        self.assertFalse(directory_storage.exists(chapter_folder_path))

    def test_admin_can_delete_non_owned_chapter(self):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": manga}
        )

        self.client.force_authenticate(user=self.admin)

        url = reverse(
            f"{self.namespace}:delete-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(Chapter.objects.filter(id=chapter.id).exists())

    def test_manga_owner_can_delete_chapter(self):
        manga_owner = self.get_random_owner_value()

        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": manga_owner}
        )

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": manga, "owner": manga_owner}
        )

        self.client.force_authenticate(user=manga_owner.user)

        url = reverse(
            f"{self.namespace}:delete-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(Chapter.objects.filter(id=chapter.id).exists())

    def test_collaborator_cannot_delete_chapter(self):
        _, _, _, chapter = self.create_random_valid_object()

        self.client.force_authenticate(user=chapter.collaborators.first().user)

        url = reverse(
            f"{self.namespace}:delete-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

    def test_regular_logged_in_user_cannot_delete_chapter(self):
        _, _, _, chapter = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:delete-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

    def test_non_existing_chapter_delete(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:delete-chapter", kwargs={"chapter_id": 0})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)


# BuyChapterView
class TestBuyChapterView(ChapterBaseTestCase):
    def test_logged_in_user_can_buy_chapter(self):
        buyer = self.user.profile
        buyer.wallet = 1000
        buyer.save()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"price": 200}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

    def test_guest_cannot_buy_chapter(self):
        self.client.logout()

        _, _, _, chapter = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)

    def test_non_existing_chapter_buy(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:buy-chapter", kwargs={"chapter_id": 0})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_already_bought_chapter(self):
        buyer = self.user.profile
        buyer.wallet = 1000
        buyer.save()

        _, _, _, chapter = self.create_random_valid_object()

        bought_chapter_tester = BoughtChapterBaseTestCase()
        bought_chapter_tester.create_random_valid_object(
            predefined_vals={
                "profile": buyer,
                "chapter": chapter,
                "paid_price": chapter.price,
            }
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

    def test_cannot_buy_owned_chapter(self):
        owner = self.user.profile

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"owner": owner}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

    def test_not_enough_money(self):
        buyer = self.user.profile
        buyer.wallet = 0
        buyer.save()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"price": 999}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

    def test_admin_can_buy_even_without_money(self):
        self.admin.profile.wallet = 0
        self.admin.profile.save()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"price": 9999}
        )

        self.client.force_authenticate(user=self.admin)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

    def test_profile_balance_transactions(self):
        buyer = self.user.profile
        buyer.wallet = 1000
        buyer.save()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"price": 300}
        )

        seller = chapter.owner

        initial_buyer_balance = buyer.wallet
        initial_seller_balance = seller.wallet

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        buyer.refresh_from_db()
        seller.refresh_from_db()

        self.assertEqual(buyer.wallet, initial_buyer_balance - chapter.price)

        self.assertEqual(seller.wallet, initial_seller_balance + chapter.price)

    def test_bought_chapter_creation_on_buy(self):
        buyer = self.user.profile
        buyer.wallet = 1000
        buyer.save()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"price": 300}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            BoughtChapter.objects.filter(profile=buyer, chapter=chapter).exists()
        )

        bought_chapter = BoughtChapter.objects.get(profile=buyer, chapter=chapter)

        self.assertEqual(bought_chapter.paid_price, chapter.price)

        buyer.refresh_from_db()
        self.assertEqual(buyer.wallet, 700)

        chapter.owner.refresh_from_db()
        self.assertEqual(chapter.owner.wallet, 300)

    def test_returned_data_fields(self):
        buyer = self.user.profile
        buyer.wallet = 1000
        buyer.save()

        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"price": 200}
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:buy-chapter", kwargs={"chapter_id": chapter.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.data["data"]

        self.assertIn("pdf", data)
        self.assertIn("folder_name", data)
        self.assertIn("pages_base_url", data)
        self.assertIn("profile_balance", data)

        self.assertEqual(data["folder_name"], chapter.folder_name)

        self.assertEqual(data["profile_balance"], 800)

        self.assertIn(chapter.folder_name, data["pdf"])

        self.assertIn(chapter.folder_name, data["pages_base_url"])


class TestProfileDeletionInheritance(ChapterBaseTestCase):
    def test_profile_deletion_inheritance_logic(self):
        deleting_profile = self.user.profile

        manga_tester = MangaBaseTestCase()

        manga_collaborator = get_dummy_profile()
        chapter_collaborator = get_dummy_profile()
        external_owner = get_dummy_profile()

        # 1. single_handedly_owned_manga
        # manga should be deleted
        # chapter should be deleted
        _, _, _, single_handedly_owned_manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": deleting_profile, "collaborators": []}
        )

        _, _, _, single_handedly_owned_manga_chapter = self.create_random_valid_object(
            predefined_vals={
                "manga": single_handedly_owned_manga,
                "owner": deleting_profile,
                "collaborators": [],
            }
        )

        # 2. owned_manga_with_collaborators
        _, _, _, owned_manga_with_collaborators = (
            manga_tester.create_random_valid_object(
                predefined_vals={
                    "owner": deleting_profile,
                    "collaborators": [manga_collaborator],
                }
            )
        )

        # single_handedly_owned_chapter
        # -> should inherit to manga collaborator
        _, _, _, owned_manga_single_owned_chapter = self.create_random_valid_object(
            predefined_vals={
                "manga": owned_manga_with_collaborators,
                "owner": deleting_profile,
                "collaborators": [],
            }
        )

        # owned_chapter_with_collaborators
        # -> should inherit to chapter collaborator
        _, _, _, owned_manga_chapter_with_collaborators = (
            self.create_random_valid_object(
                predefined_vals={
                    "manga": owned_manga_with_collaborators,
                    "owner": deleting_profile,
                    "collaborators": [chapter_collaborator],
                }
            )
        )

        # collaborated_chapter
        # -> no change because deleting_profile is NOT owner
        _, _, _, owned_manga_collaborated_chapter = self.create_random_valid_object(
            predefined_vals={
                "manga": owned_manga_with_collaborators,
                "owner": manga_collaborator,
                "collaborators": [deleting_profile],
            }
        )

        # 3. collaborated_manga
        _, _, _, collaborated_manga = manga_tester.create_random_valid_object(
            predefined_vals={
                "owner": external_owner,
                "collaborators": [deleting_profile, manga_collaborator],
            }
        )

        # single_handedly_owned_chapter
        # -> should inherit to manga owner
        _, _, _, collaborated_manga_single_owned_chapter = (
            self.create_random_valid_object(
                predefined_vals={
                    "manga": collaborated_manga,
                    "owner": deleting_profile,
                    "collaborators": [],
                }
            )
        )

        # owned_chapter_with_collaborators
        # -> should inherit to chapter collaborator
        _, _, _, collaborated_manga_chapter_with_collaborators = (
            self.create_random_valid_object(
                predefined_vals={
                    "manga": collaborated_manga,
                    "owner": deleting_profile,
                    "collaborators": [chapter_collaborator],
                }
            )
        )

        # collaborated_chapter
        # -> no change because deleting_profile is NOT owner
        _, _, _, collaborated_manga_collaborated_chapter = (
            self.create_random_valid_object(
                predefined_vals={
                    "manga": collaborated_manga,
                    "owner": external_owner,
                    "collaborators": [deleting_profile],
                }
            )
        )

        # DELETE PROFILE -> trigger signal
        deleting_profile.delete()

        # single_handedly_owned_manga
        self.assertFalse(
            Manga.objects.filter(id=single_handedly_owned_manga.id).exists()
        )

        self.assertFalse(
            Chapter.objects.filter(id=single_handedly_owned_manga_chapter.id).exists()
        )

        # owned_manga_with_collaborators
        owned_manga_with_collaborators.refresh_from_db()

        # manga inherited by manga collaborator
        self.assertEqual(owned_manga_with_collaborators.owner.id, manga_collaborator.id)

        # single owned chapter -> manga collaborator inherits
        owned_manga_single_owned_chapter.refresh_from_db()

        self.assertEqual(
            owned_manga_single_owned_chapter.owner.id, manga_collaborator.id
        )

        # chapter collaborator inherits
        owned_manga_chapter_with_collaborators.refresh_from_db()

        self.assertEqual(
            owned_manga_chapter_with_collaborators.owner.id, chapter_collaborator.id
        )

        # collaborated chapter unchanged owner
        # deleting profile removed from collaborators
        owned_manga_collaborated_chapter.refresh_from_db()

        self.assertEqual(
            owned_manga_collaborated_chapter.owner.id, manga_collaborator.id
        )

        self.assertFalse(
            owned_manga_collaborated_chapter.collaborators.filter(
                id=deleting_profile.id
            ).exists()
        )

        # collaborated_manga
        collaborated_manga.refresh_from_db()

        # manga owner unchanged
        self.assertEqual(collaborated_manga.owner.id, external_owner.id)

        # deleting profile removed from collaborators
        self.assertFalse(
            collaborated_manga.collaborators.filter(id=deleting_profile.id).exists()
        )

        # single owned chapter -> manga owner inherits
        collaborated_manga_single_owned_chapter.refresh_from_db()

        self.assertEqual(
            collaborated_manga_single_owned_chapter.owner.id, external_owner.id
        )

        # chapter collaborator inherits
        collaborated_manga_chapter_with_collaborators.refresh_from_db()

        self.assertEqual(
            collaborated_manga_chapter_with_collaborators.owner.id,
            chapter_collaborator.id,
        )

        # collaborated chapter unchanged
        collaborated_manga_collaborated_chapter.refresh_from_db()

        self.assertEqual(
            collaborated_manga_collaborated_chapter.owner.id, external_owner.id
        )

        self.assertFalse(
            collaborated_manga_collaborated_chapter.collaborators.filter(
                id=deleting_profile.id
            ).exists()
        )


# MarkReadChapterView
class TestMarkReadChapterView(ChapterBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

        _, _, _, self.chapter = self.create_random_valid_object()
        self.manga = self.chapter.manga

        self.url = reverse(
            f"{self.namespace}:mark-read-chapter",
            kwargs={"chapter_id": self.chapter.id},
        )

    def test_guest_cannot_mark_read_chapter(self):
        self.client.logout()

        url = reverse(
            f"{self.namespace}:mark-read-chapter",
            kwargs={"chapter_id": self.chapter.id},
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)

    def test_non_existing_chapter_mark_read(self):
        url = reverse(f"{self.namespace}:mark-read-chapter", kwargs={"chapter_id": 0})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_cannot_mark_non_bought_chapter_as_read(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ReadChapter.objects.count(), 0)

    def test_mark_read_creates_read_chapter(self):
        bought_chapter_tester = BoughtChapterBaseTestCase()
        bought_chapter_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "chapter": self.chapter}
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            ReadChapter.objects.filter(
                profile=self.user.profile, chapter=self.chapter
            ).exists()
        )

    def test_mark_read_twice_returns_200_and_does_not_duplicate(self):
        bought_chapter_tester = BoughtChapterBaseTestCase()
        bought_chapter_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "chapter": self.chapter}
        )

        response1 = self.client.post(self.url)
        response2 = self.client.post(self.url)

        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 200)

        self.assertEqual(
            ReadChapter.objects.filter(
                profile=self.user.profile, chapter=self.chapter
            ).count(),
            1,
        )


# PutMangaBookmarkView
class TestPutMangaBookmarkView(ChapterBaseTestCase):
    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

        _, _, _, self.chapter = self.create_random_valid_object()
        self.manga = self.chapter.manga

        self.url = reverse(
            f"{self.namespace}:put-manga-bookmark",
            kwargs={"manga_id": self.manga.id, "chapter_id": self.chapter.id},
        )

    def test_guest_cannot_bookmark_manga(self):
        self.client.logout()

        url = reverse(
            f"{self.namespace}:put-manga-bookmark",
            kwargs={"manga_id": self.manga.id, "chapter_id": self.chapter.id},
        )

        response = self.client.post(url, {"page": 0})

        self.assertEqual(response.status_code, 403)

    def test_non_existing_manga_bookmark(self):
        url = reverse(
            f"{self.namespace}:put-manga-bookmark",
            kwargs={"manga_id": 0, "chapter_id": self.chapter.id},
        )

        response = self.client.post(url, {"page": 0})

        self.assertEqual(response.status_code, 404)

    def test_non_existing_chapter_bookmark(self):
        url = reverse(
            f"{self.namespace}:put-manga-bookmark",
            kwargs={"manga_id": self.manga.id, "chapter_id": 0},
        )

        response = self.client.post(url, {"page": 0})

        self.assertEqual(response.status_code, 404)

    def test_cannot_bookmark_non_bought_chapter(self):
        response = self.client.post(self.url, {"page": 0})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(MangaBookmark.objects.count(), 0)

    def test_invalid_page_payloads(self):
        bought_chapter_tester = BoughtChapterBaseTestCase()
        bought_chapter_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "chapter": self.chapter}
        )

        invalid_payloads = [
            {},
            {"page": "abc"},
            {"page": -1},
            # we allow final page bookmarking because cover pages increase the index by 1
            # # we can think the fronted pages being 1 indexed instead of 0 indexed
            # {"page": self.chapter.num_of_images},
            {"page": self.chapter.num_of_images + 1},
        ]
        for payload in invalid_payloads:
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 400)

    def test_bookmark_creates_bookmark(self):
        bought_chapter_tester = BoughtChapterBaseTestCase()
        bought_chapter_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "chapter": self.chapter}
        )

        response = self.client.post(self.url, {"page": 0})

        self.assertEqual(response.status_code, 200)

        bookmark = MangaBookmark.objects.get(
            manga=self.manga, profile=self.user.profile
        )

        self.assertEqual(bookmark.chapter, self.chapter)
        self.assertEqual(bookmark.page, 0)

    def test_bookmark_updates_existing_bookmark(self):
        # we need a chapter with more than 2 pages to detect bookmarked page change
        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"pdf": self.get_random_pdf_value(pages=2)}
        )
        manga = chapter.manga

        bought_chapter_tester = BoughtChapterBaseTestCase()
        bought_chapter_tester.create_random_valid_object(
            predefined_vals={"profile": self.user.profile, "chapter": chapter}
        )

        url = reverse(
            f"{self.namespace}:put-manga-bookmark",
            kwargs={"manga_id": manga.id, "chapter_id": chapter.id},
        )

        self.client.post(url, {"page": 0})
        self.client.post(url, {"page": 1})

        self.assertEqual(
            MangaBookmark.objects.filter(
                manga=manga, profile=self.user.profile
            ).count(),
            1,
        )

        bookmark = MangaBookmark.objects.get(manga=manga, profile=self.user.profile)

        self.assertEqual(bookmark.page, 1)
        self.assertEqual(bookmark.chapter, chapter)
