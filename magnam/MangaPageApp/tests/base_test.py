from pathlib import Path
from django.test import TransactionTestCase, override_settings

from utils.test_utils import *

from ..globals import *
from ..models import *
from ..tasks import process_pdf
from magnam.storage import file_storage, directory_storage


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class MangaTagBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "MangaPageApp")

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

        tag = MangaTag.objects.create(**vals_to_create_from)

        return original_vals, vals_to_send_request, vals_to_create_from, tag

    def assert_db_stored_values_match_expected_dict(
        self, tag: MangaTag, original_vals: dict
    ):
        self.assertEqual(tag.label, original_vals["label"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_tag: dict, tag: MangaTag
    ):
        self.assertEqual(retrieved_tag["id"], tag.id)
        self.assertEqual(retrieved_tag["label"], tag.label)


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class MangaBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.get_random_tags_value(
            count=2
        )  # unsure that we have original and translation tags ready
        prepare_independent_test_space(self, "MangaPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_title_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_description_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_image_value(
        self,
        W=MANGA_IMAGE_MIN_W,
        H=MANGA_IMAGE_MIN_H,
        target_size_bytes=MANGA_IMAGE_MAX_SIZE / 10,
        ext="png",
        seed=None,
    ):
        return get_dummy_file(
            W=W, H=H, target_size_bytes=target_size_bytes, ext=ext, seed=seed
        )

    def get_random_owner_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_collaborators_value(self, count=2, seed=None):
        collaborators = []

        for i in range(count):
            collaborators.append(
                get_dummy_profile(seed=seed + i if seed is not None else None)
            )

        return collaborators

    def get_random_tags_value(self, count=3, seed=None):
        tag_tester = MangaTagBaseTestCase()

        tags = []

        for i in range(count):
            _, _, _, tag = tag_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )
            tags.append(tag)

        return tags

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        title = predefined_vals.get("title", self.get_random_title_value(seed=seed))

        description = predefined_vals.get(
            "description", self.get_random_description_value(seed=seed)
        )

        image = predefined_vals.get("image", self.get_random_image_value(seed=seed))

        owner = (
            predefined_vals["owner"]
            if "owner" in predefined_vals
            else self.get_random_owner_value(seed=seed)
        )

        collaborators = (
            predefined_vals["collaborators"]
            if "collaborators" in predefined_vals
            else self.get_random_collaborators_value(seed=seed)
        )

        tags = (
            predefined_vals["tags"]
            if "tags" in predefined_vals
            else self.get_random_tags_value(seed=seed)
        )
        # each manga needs to be original or translation
        # we put original tag forcefuly during creation if tags are invalid
        original_tag = MangaTag.objects.get(id=1)
        translation_tag = MangaTag.objects.get(id=2)
        if original_tag not in tags and translation_tag not in tags:
            tags = tags + [original_tag]
        if original_tag in tags and translation_tag in tags:
            tags = [t for t in tags if t != translation_tag]

        original_vals = {
            "title": title,
            "description": description,
            "image": image,
            "owner": owner.id,
            "collaborators": [c.id for c in collaborators],
            "tags": [t.id for t in tags],
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()

        vals_to_create_from["owner"] = owner
        vals_to_create_from["collaborators"] = collaborators
        vals_to_create_from["tags"] = tags

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        collaborators = vals_to_create_from.pop("collaborators")
        tags = vals_to_create_from.pop("tags")

        manga = Manga.objects.create(**vals_to_create_from)

        manga.collaborators.set(collaborators)
        manga.tags.set(tags)
        manga.save()

        manga.owner.mangas_following.add(manga)
        manga.owner.mangas_owned.add(manga)

        vals_to_create_from["collaborators"] = collaborators
        vals_to_create_from["tags"] = tags

        return original_vals, vals_to_send_request, vals_to_create_from, manga

    def assert_database_image(self, manga: Manga):
        self.assertTrue(file_storage.exists(manga.image.name))
        self.assertTrue(
            manga.image.name.startswith(
                f"{settings.MANGAS_MEDIA_FOLDERNAME}/{manga.folder_name}/"
            )
        )

    def assert_db_tags(self, retrieved_tags, expected_tags):
        tag_tester = MangaTagBaseTestCase()

        self.assertEqual(len(retrieved_tags), len(expected_tags))

        for retrieved_tag in retrieved_tags:
            expected_tag = next(
                (e for e in expected_tags if e.id == retrieved_tag["id"]), None
            )

            self.assertIsNotNone(expected_tag)

            tag_tester.assert_db_retrieved_dict_match_db_stored_values(
                retrieved_tag, expected_tag
            )

    def assert_db_collaborators(self, retrieved_collaborators, expected_collaborators):
        self.assertEqual(
            set([c["id"] for c in retrieved_collaborators]),
            set([c.id for c in expected_collaborators]),
        )

    def assert_db_chapters(self, retrieved_chapters, expected_chapters):
        chapter_tester = ChapterBaseTestCase()

        self.assertEqual(len(retrieved_chapters), len(expected_chapters))

        for retrieved_chapter in retrieved_chapters:
            expected_chapter = next(
                (e for e in expected_chapters if e.id == retrieved_chapter["id"]), None
            )

            self.assertIsNotNone(expected_chapter)

            chapter_tester.assert_db_retrieved_dict_match_db_stored_values(
                retrieved_chapter, expected_chapter
            )

    def assert_db_stored_values_match_expected_dict(
        self, manga: Manga, original_vals: dict
    ):
        self.assertEqual(manga.title, original_vals["title"])
        self.assertEqual(manga.description, original_vals["description"])
        self.assertEqual(manga.owner.id, original_vals["owner"])

        self.assertEqual(
            set([c.id for c in manga.collaborators.all()]),
            set(original_vals["collaborators"]),
        )

        self.assertEqual(
            set([t.id for t in manga.tags.all()]), set(original_vals["tags"])
        )

        self.assert_database_image(manga)

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_manga: dict, manga: Manga
    ):
        self.assertEqual(retrieved_manga["id"], manga.id)
        self.assertEqual(retrieved_manga["title"], manga.title)
        self.assertEqual(retrieved_manga["description"], manga.description)

        self.assertEqual(retrieved_manga["owner"]["id"], manga.owner_id)

        self.assertEqual(retrieved_manga["folder_name"], manga.folder_name)

        self.assertTrue(retrieved_manga["image"] != "")
        self.assertIn(str(manga.image), retrieved_manga["image"])

        self.assert_db_tags(retrieved_manga["tags"], list(manga.tags.all()))

        self.assert_db_collaborators(
            retrieved_manga["collaborators"], list(manga.collaborators.all())
        )

        self.assert_db_chapters(retrieved_manga["chapters"], list(manga.chapters.all()))

    def assert_gallery_retrieved_dict_match_db_stored_values(
        self, retrieved_manga: dict, manga: Manga
    ):
        self.assertEqual(retrieved_manga["id"], manga.id)
        self.assertEqual(retrieved_manga["title"], manga.title)

        self.assertTrue(retrieved_manga["image"] != "")
        self.assertIn(str(manga.image), retrieved_manga["image"])

        self.assertEqual(retrieved_manga["start_date"], str(manga.start_date))

        self.assertEqual(
            retrieved_manga["last_update_date"], str(manga.last_update_date)
        )

        self.assert_db_tags(retrieved_manga["tags"], list(manga.tags.all()))


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class MangaRatingBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "MangaPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_profile_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_manga_value(self, seed=None):
        manga_tester = MangaBaseTestCase()

        _, _, _, manga = manga_tester.create_random_valid_object(seed=seed)

        return manga

    def get_random_score_value(self, seed=None):
        return random.Random(seed).randint(MANGA_MIN_RATING, MANGA_MAX_RATING)

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        profile = (
            predefined_vals["profile"]
            if "profile" in predefined_vals
            else self.get_random_profile_value(seed=seed)
        )
        manga = (
            predefined_vals["manga"]
            if "manga" in predefined_vals
            else self.get_random_manga_value(seed=seed)
        )
        score = predefined_vals.get("score", self.get_random_score_value())

        original_vals = {"profile": profile.id, "manga": manga.id, "score": score}

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()

        vals_to_create_from["profile"] = profile
        vals_to_create_from["manga"] = manga

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        rating = MangaRating.objects.create(**vals_to_create_from)

        return original_vals, vals_to_send_request, vals_to_create_from, rating

    def assert_db_stored_values_match_expected_dict(
        self, rating: MangaRating, original_vals: dict
    ):
        self.assertEqual(rating.profile.id, original_vals["profile"])
        self.assertEqual(rating.manga.id, original_vals["manga"])
        self.assertEqual(rating.score, original_vals["score"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_rating: dict, rating: MangaRating
    ):
        self.assertEqual(retrieved_rating["id"], rating.id)
        self.assertEqual(retrieved_rating["profile"], rating.profile_id)
        self.assertEqual(retrieved_rating["manga"], rating.manga_id)
        self.assertEqual(retrieved_rating["score"], rating.score)


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class MangaCommentBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "MangaPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_profile_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_manga_value(self, seed=None):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(seed=seed)
        return manga

    def get_random_comment_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_existing_parent_comment(self, manga):
        return MangaComment.objects.filter(manga=manga).first()

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        profile = (
            predefined_vals["profile"]
            if "profile" in predefined_vals
            else self.get_random_profile_value(seed=seed)
        )
        manga = (
            predefined_vals["manga"]
            if "manga" in predefined_vals
            else self.get_random_manga_value(seed=seed)
        )
        comment = predefined_vals.get(
            "comment", self.get_random_comment_value(seed=seed)
        )

        # defaults to no parent
        parent_comment = -1
        # we set a parent if its given
        if "parent_comment" in predefined_vals:
            parent_comment = predefined_vals["parent_comment"]
        # else randomly sample
        elif random.Random(seed).random() < 0.5:
            parent_comment = self.get_existing_parent_comment(manga)

        original_vals = {
            "profile": profile.id,
            "manga": manga.id,
            "comment": comment,
            "parent_comment_id": (
                parent_comment.id if isinstance(parent_comment, MangaComment) else -1
            ),
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["profile"] = profile
        vals_to_create_from["manga"] = manga
        vals_to_create_from["parent_comment"] = (
            parent_comment if isinstance(parent_comment, MangaComment) else None
        )

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )
        del vals_to_create_from["parent_comment_id"]
        comment = MangaComment.objects.create(**vals_to_create_from)

        return original_vals, vals_to_send_request, vals_to_create_from, comment

    def assert_db_stored_values_match_expected_dict(
        self, comment: MangaComment, original_vals: dict
    ):
        self.assertEqual(comment.profile.id, original_vals["profile"])
        self.assertEqual(comment.manga.id, original_vals["manga"])
        self.assertEqual(comment.comment, original_vals["comment"])
        self.assertEqual(
            comment.parent_comment_id, original_vals.get("parent_comment_id")
        )

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_comment: dict, comment: MangaComment
    ):
        self.assertEqual(retrieved_comment["id"], comment.id)

        self.assertEqual(
            retrieved_comment["profile_name"], comment.profile.profile_name
        )

        self.assertEqual(retrieved_comment["comment"], comment.comment)

        self.assertEqual(
            retrieved_comment["parent_comment_id"], comment.parent_comment_id
        )


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class ChapterBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "MangaPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_title_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_no_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_manga_value(self, seed=None):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object(seed=seed)
        return manga

    def get_random_owner_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_collaborators_value(self, count=2, seed=None):
        collaborators = []

        for i in range(count):
            collaborators.append(
                get_dummy_profile(seed=seed + i if seed is not None else None)
            )

        return collaborators

    def get_random_pdf_value(
        self, target_size_bytes=CHAPTER_PDF_MAX_SIZE / 2, pages=1, seed=None
    ):
        return get_dummy_file(
            ext="pdf", target_size_bytes=target_size_bytes, pages=pages, seed=seed
        )

    def get_random_price_value(self, seed=None):
        return random.Random(seed).randint(1, 1000)

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        title = predefined_vals.get("title", self.get_random_title_value(seed=seed))

        no = predefined_vals.get("no", self.get_random_no_value(seed=seed))

        manga = (
            predefined_vals["manga"]
            if "manga" in predefined_vals
            else self.get_random_manga_value(seed=seed)
        )

        owner = (
            predefined_vals["owner"]
            if "owner" in predefined_vals
            else manga.owner  # for data to be valid, chapter owner needs to be manga owner or collaborator
        )

        collaborators = (
            predefined_vals["collaborators"]
            if "collaborators" in predefined_vals
            else self.get_random_collaborators_value(seed=seed)
        )

        pdf = predefined_vals.get("pdf", self.get_random_pdf_value(seed=seed))

        price = predefined_vals.get("price", self.get_random_price_value(seed=seed))

        original_vals = {
            "title": title,
            "no": no,
            "manga": manga.id,
            "owner": owner.id,
            "collaborators": [c.id for c in collaborators],
            "pdf": pdf,
            "price": price,
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()

        vals_to_create_from["manga"] = manga
        vals_to_create_from["owner"] = owner
        vals_to_create_from["collaborators"] = collaborators

        return original_vals, vals_to_send_request, vals_to_create_from

    def process_pdf_for_test(self, chapter: Chapter):
        process_pdf(chapter.id)
        chapter.refresh_from_db()  # to update the num of pages stuff

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        collaborators = vals_to_create_from.pop("collaborators")

        chapter = Chapter.objects.create(**vals_to_create_from)
        chapter.collaborators.set(collaborators)
        chapter.save()
        folder_path = get_chapter_upload_folder_path(chapter)
        directory_storage.create(folder_path)
        self.process_pdf_for_test(chapter)

        BoughtChapter.objects.create(
            profile=chapter.owner, chapter=chapter, paid_price=0
        )
        chapter.owner.chapters_owned.add(chapter)

        for collaborator in chapter.collaborators.all():
            BoughtChapter.objects.create(
                profile=collaborator, chapter=chapter, paid_price=0
            )
            collaborator.chapters_collaborated.add(chapter)

        # if manga owner is not the creator or in the collaborators of the manga, he needs to have the chapter
        # we use get_or_create to not create the same BoughtChapter if manga owner was chapter owner or in collaborators
        _ = BoughtChapter.objects.get_or_create(
            profile=chapter.manga.owner, chapter=chapter, paid_price=0
        )

        vals_to_create_from["collaborators"] = collaborators

        return original_vals, vals_to_send_request, vals_to_create_from, chapter

    def assert_database_pdf(self, chapter: Chapter):
        self.assertTrue(file_storage.exists(chapter.pdf.name))

        self.assertTrue(
            chapter.pdf.name.startswith(
                f"{settings.MANGAS_MEDIA_FOLDERNAME}/{chapter.manga.folder_name}/{chapter.folder_name}/"
            )
        )

        chapter_folder = Path(
            settings.MANGAS_MEDIA_FOLDERNAME,
            chapter.manga.folder_name,
            chapter.folder_name,
        ).as_posix()
        self.assertTrue(
            file_storage.exists(PurePosixPath(chapter_folder, "original.pdf").as_posix())
        )
        self.assertTrue(
            directory_storage.exists(PurePosixPath(chapter_folder, "pages").as_posix())
        )

        self.assertNotEqual(chapter.folder_name, "")

    def assert_db_collaborators(self, retrieved_collaborators, expected_collaborators):
        self.assertEqual(
            set([c["id"] for c in retrieved_collaborators]),
            set([c.id for c in expected_collaborators]),
        )

    def assert_db_stored_values_match_expected_dict(
        self, chapter: Chapter, original_vals: dict
    ):
        self.assertEqual(chapter.title, original_vals["title"])
        self.assertEqual(chapter.no, original_vals["no"])

        self.assertEqual(chapter.manga.id, original_vals["manga"])
        self.assertEqual(chapter.owner.id, original_vals["owner"])

        self.assertEqual(
            set([c.id for c in chapter.collaborators.all()]),
            set(original_vals["collaborators"]),
        )

        self.assertEqual(chapter.price, original_vals["price"])

        self.assert_database_pdf(chapter)

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_chapter: dict, chapter: Chapter
    ):
        self.assertEqual(retrieved_chapter["id"], chapter.id)
        self.assertEqual(retrieved_chapter["title"], chapter.title)
        self.assertEqual(retrieved_chapter["no"], chapter.no)

        self.assertEqual(retrieved_chapter["manga"], chapter.manga_id)

        self.assertEqual(retrieved_chapter["owner"]["id"], chapter.owner_id)

        self.assertEqual(retrieved_chapter["folder_name"], chapter.folder_name)

        self.assertEqual(retrieved_chapter["num_of_images"], chapter.num_of_images)

        self.assertEqual(retrieved_chapter["price"], chapter.price)

        # returned field is <FieldFile> so we get the .name
        self.assertTrue(retrieved_chapter["pdf"].name != "")
        self.assertIn(str(chapter.pdf), retrieved_chapter["pdf"].name)

        self.assert_db_collaborators(
            retrieved_chapter["collaborators"], list(chapter.collaborators.all())
        )


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class BoughtChapterBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "MangaPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_profile_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_chapter_value(self, seed=None):
        chapter_tester = ChapterBaseTestCase()
        _, _, _, chapter = chapter_tester.create_random_valid_object(seed=seed)
        return chapter

    def get_random_paid_price_value(self, seed=None):
        return random.Random(seed).randint(0, 1000)

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        profile = (
            predefined_vals["profile"]
            if "profile" in predefined_vals
            else self.get_random_profile_value(seed=seed)
        )
        chapter = (
            predefined_vals["chapter"]
            if "chapter" in predefined_vals
            else self.get_random_chapter_value(seed=seed)
        )
        paid_price = predefined_vals.get(
            "paid_price", self.get_random_paid_price_value(seed=seed)
        )

        original_vals = {
            "profile": profile.id,
            "chapter": chapter.id,
            "paid_price": paid_price,
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()

        vals_to_create_from["profile"] = profile
        vals_to_create_from["chapter"] = chapter

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        bought_chapter = BoughtChapter.objects.create(**vals_to_create_from)

        return (
            original_vals,
            vals_to_send_request,
            vals_to_create_from,
            bought_chapter,
        )

    def assert_db_stored_values_match_expected_dict(
        self, bought_chapter: BoughtChapter, original_vals: dict
    ):
        self.assertEqual(bought_chapter.profile.id, original_vals["profile"])

        self.assertEqual(bought_chapter.chapter.id, original_vals["chapter"])

        self.assertEqual(bought_chapter.paid_price, original_vals["paid_price"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_bought_chapter: dict, bought_chapter: BoughtChapter
    ):
        self.assertEqual(retrieved_bought_chapter["id"], bought_chapter.id)

        self.assertEqual(retrieved_bought_chapter["profile"], bought_chapter.profile_id)

        self.assertEqual(retrieved_bought_chapter["chapter"], bought_chapter.chapter_id)

        self.assertEqual(
            retrieved_bought_chapter["paid_price"], bought_chapter.paid_price
        )
