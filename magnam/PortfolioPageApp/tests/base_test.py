from pathlib import Path
from django.test import TransactionTestCase, override_settings
from utils.test_utils import *
from ..globals import *
from ..models import *
from ..tasks import process_pdf
from magnam.storage import file_storage, directory_storage


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class PortfolioTagBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "PortfolioPageApp")

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
        tag = PortfolioTag.objects.create(**vals_to_create_from)
        return original_vals, vals_to_send_request, vals_to_create_from, tag

    def assert_db_stored_values_match_expected_dict(
        self, tag: PortfolioTag, original_vals: dict
    ):
        self.assertEqual(tag.label, original_vals["label"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_tag: dict, tag: PortfolioTag
    ):
        self.assertEqual(retrieved_tag["id"], tag.id)
        self.assertEqual(retrieved_tag["label"], tag.label)


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class PortfolioBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "PortfolioPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_owner_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_title_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_description_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_image_value(
        self,
        W=PORTFOLIO_IMAGE_MIN_W,
        H=PORTFOLIO_IMAGE_MIN_H,
        target_size_bytes=PORTFOLIO_IMAGE_MAX_SIZE / 10,
        ext="png",
        seed=None,
    ):
        return get_dummy_file(
            W=W, H=H, target_size_bytes=target_size_bytes, ext=ext, seed=seed
        )

    def get_random_tags_value(self, count=3, seed=None):
        tag_tester = PortfolioTagBaseTestCase()
        tags = []
        for i in range(count):
            _, _, _, tag = tag_tester.create_random_valid_object(
                seed=seed + i if seed else None
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
        tags = (
            predefined_vals["tags"]
            if "tags" in predefined_vals
            else self.get_random_tags_value(seed=seed)
        )

        original_vals = {
            "title": title,
            "description": description,
            "image": image,
            "owner": owner.id,
            "tags": [t.id for t in tags],
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["owner"] = owner
        vals_to_create_from["tags"] = tags

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        tags = vals_to_create_from.pop("tags")
        portfolio = Portfolio.objects.create(**vals_to_create_from)
        portfolio.tags.set(tags)
        portfolio.save()

        vals_to_create_from["tags"] = tags

        return original_vals, vals_to_send_request, vals_to_create_from, portfolio

    def assert_database_image(self, portfolio):
        self.assertTrue(file_storage.exists(portfolio.image.name))
        self.assertTrue(
            portfolio.image.name.startswith(
                f"{settings.PORTFOLIOS_MEDIA_FOLDERNAME}/{portfolio.folder_name}/"
            )
        )

    def assert_db_stored_values_match_expected_dict(
        self, portfolio: Portfolio, original_vals: dict
    ):
        self.assertEqual(portfolio.title, original_vals["title"])
        self.assertEqual(portfolio.description, original_vals["description"])
        self.assertEqual(portfolio.owner.id, original_vals["owner"])
        self.assertEqual(
            set([t.id for t in portfolio.tags.all()]), set(original_vals["tags"])
        )
        self.assert_database_image(portfolio)

    def assert_db_tags(self, retrieved_tags, expected_tags):
        tag_tester = PortfolioTagBaseTestCase()
        self.assertEqual(len(retrieved_tags), len(expected_tags))

        for retrieved_tag in retrieved_tags:
            expected_tag = next(
                (e for e in expected_tags if e.id == retrieved_tag["id"]), None
            )
            self.assertIsNotNone(expected_tag)
            tag_tester.assert_db_retrieved_dict_match_db_stored_values(
                retrieved_tag, expected_tag
            )

    def assert_db_works(self, retrieved_works, expected_works):
        work_tester = WorkBaseTestCase()
        self.assertEqual(len(retrieved_works), len(expected_works))

        for retrieved_work in retrieved_works:
            expected_work = next(
                (e for e in expected_works if e.id == retrieved_work["id"]), None
            )
            self.assertIsNotNone(expected_work)
            work_tester.assert_db_retrieved_dict_match_db_stored_values(
                retrieved_work, expected_work
            )

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_portfolio: dict, portfolio: Portfolio
    ):
        self.assertEqual(retrieved_portfolio["id"], portfolio.id)
        self.assertEqual(retrieved_portfolio["title"], portfolio.title)
        self.assertEqual(retrieved_portfolio["description"], portfolio.description)
        self.assertEqual(retrieved_portfolio["owner"]["id"], portfolio.owner_id)

        self.assert_db_tags(retrieved_portfolio["tags"], list(portfolio.tags.all()))
        self.assert_db_works(retrieved_portfolio["works"], list(portfolio.works.all()))
        self.assertEqual(retrieved_portfolio["folder_name"], portfolio.folder_name)
        self.assertTrue(retrieved_portfolio["image"] != "")
        self.assertIn(str(portfolio.image), retrieved_portfolio["image"])

    def assert_gallery_retrieved_dict_match_db_stored_values(
        self, retrieved_portfolio: dict, portfolio: Portfolio
    ):
        self.assertEqual(retrieved_portfolio["id"], portfolio.id)
        self.assertEqual(retrieved_portfolio["title"], portfolio.title)

        self.assertTrue(retrieved_portfolio["image"] != "")
        self.assertIn(str(portfolio.image), retrieved_portfolio["image"])

        self.assertEqual(retrieved_portfolio["date"], str(portfolio.date))

        self.assert_db_tags(retrieved_portfolio["tags"], list(portfolio.tags.all()))


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class PortfolioLikeBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "PortfolioPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_profile_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_portfolio_value(self, seed=None):
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(seed=seed)
        return portfolio

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        profile = (
            predefined_vals["profile"]
            if "profile" in predefined_vals
            else self.get_random_profile_value(seed=seed)
        )
        portfolio = (
            predefined_vals["portfolio"]
            if "portfolio" in predefined_vals
            else self.get_random_portfolio_value(seed=seed)
        )

        original_vals = {"profile": profile.id, "portfolio": portfolio.id}

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["profile"] = profile
        vals_to_create_from["portfolio"] = portfolio

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )
        like = PortfolioLike.objects.create(**vals_to_create_from)

        return original_vals, vals_to_send_request, vals_to_create_from, like

    def assert_db_stored_values_match_expected_dict(
        self, like: PortfolioLike, original_vals: dict
    ):
        self.assertEqual(like.profile.id, original_vals["profile"])
        self.assertEqual(like.portfolio.id, original_vals["portfolio"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_like: dict, like: PortfolioLike
    ):
        self.assertEqual(retrieved_like["id"], like.id)
        self.assertEqual(retrieved_like["profile"], like.profile_id)
        self.assertEqual(retrieved_like["portfolio"], like.portfolio_id)


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class PortfolioCommentBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "PortfolioPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_profile_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_portfolio_value(self, seed=None):
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(seed=seed)
        return portfolio

    def get_random_comment_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_existing_parent_comment(self, portfolio):
        return PortfolioComment.objects.filter(portfolio=portfolio).first()

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        profile = (
            predefined_vals["profile"]
            if "profile" in predefined_vals
            else self.get_random_profile_value(seed=seed)
        )
        portfolio = (
            predefined_vals["portfolio"]
            if "portfolio" in predefined_vals
            else self.get_random_portfolio_value(seed=seed)
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
            parent_comment = self.get_existing_parent_comment(portfolio)

        original_vals = {
            "profile": profile.id,
            "portfolio": portfolio.id,
            "comment": comment,
            "parent_comment_id": (
                parent_comment.id
                if isinstance(parent_comment, PortfolioComment)
                else -1
            ),
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["profile"] = profile
        vals_to_create_from["portfolio"] = portfolio
        vals_to_create_from["parent_comment"] = (
            parent_comment if isinstance(parent_comment, PortfolioComment) else None
        )

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )
        # in the cases where parent_comment_id ==-1, parent_comment is None
        # and when we pass both in the PortfolioComment.objects.create by doing "**vals_to_create_from"
        # django uses teh "-1" value and writes the database a relation foreign key id "-1"
        # we delete this parent_comment_id value so parent_comment==None is not overwritten by that
        del vals_to_create_from["parent_comment_id"]
        comment = PortfolioComment.objects.create(**vals_to_create_from)

        return original_vals, vals_to_send_request, vals_to_create_from, comment

    def assert_db_stored_values_match_expected_dict(
        self, comment: PortfolioComment, original_vals: dict
    ):
        self.assertEqual(comment.profile.id, original_vals["profile"])
        self.assertEqual(comment.portfolio.id, original_vals["portfolio"])
        self.assertEqual(comment.comment, original_vals["comment"])
        self.assertEqual(comment.parent_comment.id, original_vals["parent_comment"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_comment: dict, comment: PortfolioComment
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
class WorkBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "PortfolioPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_portfolio_value(self, seed=None):
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(seed=seed)
        return portfolio

    def get_random_title_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_file_value(
        self,
        ext="png",
        target_size_bytes=WORK_IMAGE_MAX_SIZE / 2,
        # we use video dimensions also for the images
        # it shoudln't be a problem since we dont have dimensions limits for the work images
        W=WORK_VIDEO_MIN_W,
        H=WORK_VIDEO_MIN_H,
        duration=10,
        pages=2,
        seed=None,
    ):
        return get_dummy_file(
            ext=ext,
            target_size_bytes=target_size_bytes,
            W=W,
            H=H,
            duration=duration,
            pages=pages,
            seed=seed,
        )

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        title = predefined_vals.get("title", self.get_random_title_value(seed=seed))
        portfolio = (
            predefined_vals["portfolio"]
            if "portfolio" in predefined_vals
            else self.get_random_portfolio_value(seed=seed)
        )
        work_file = predefined_vals.get(
            "work_file", self.get_random_file_value(seed=seed)
        )

        original_vals = {
            "title": title,
            "portfolio": portfolio.id,
            # usually serializers and views I use expects a list of files under the 'work_files' field
            # but get_random_valid_data should return the fitting field for the individual Work item so we keep it simple
            # and when needed we add 'work_files' field as [original_vals["work_file"]]
            "work_file": work_file,
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["portfolio"] = portfolio

        return original_vals, vals_to_send_request, vals_to_create_from

    def process_pdf_for_test(self, work: Work):
        # usually this line is called with post_save and a celery catches the assigned task
        # but in test environment we want sequential processing rather than an async celery tasks
        # so we call the base pdf parsing function here explicity
        if getattr(work, "is_pdf", False):
            folder_path = get_work_upload_folder_path(work)
            directory_storage.create(folder_path)

            process_pdf(work.id)
        work.refresh_from_db()  # to update the num of pages stuff
        # differently from the Chapters, having a folder is special to pdf works so we dont do 'directory_storage.create' in the 'create_random_valid_object'
        # folder is only created for the pdf works so it would make more sense to have it next to process_pdf

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        work = Work.objects.create(**vals_to_create_from)
        self.process_pdf_for_test(work)

        return original_vals, vals_to_send_request, vals_to_create_from, work

    def assert_database_work_file(self, work):
        self.assertTrue(file_storage.exists(work.work_file.name))
        if work.is_pdf:
            self.assertTrue(
                work.work_file.name.startswith(
                    f"{settings.PORTFOLIOS_MEDIA_FOLDERNAME}/{work.portfolio.folder_name}/{work.folder_name}/"
                )
            )

            work_folder = Path(
                settings.PORTFOLIOS_MEDIA_FOLDERNAME,
                work.portfolio.folder_name,
                work.folder_name,
            ).as_posix()
            self.assertTrue(
                file_storage.exists(PurePosixPath(work_folder, "original.pdf").as_posix())
            )
            self.assertTrue(
                directory_storage.exists(PurePosixPath(work_folder, "pages").as_posix())
            )

            self.assertNotEqual(work.folder_name, "")
        else:
            self.assertTrue(
                work.work_file.name.startswith(
                    f"{settings.PORTFOLIOS_MEDIA_FOLDERNAME}/{work.portfolio.folder_name}/"
                )
            )
            self.assertEqual(work.folder_name, "")

    def assert_db_stored_values_match_expected_dict(
        self, work: Work, original_vals: dict
    ):
        self.assertEqual(work.title, original_vals["title"])
        self.assertEqual(work.portfolio.id, original_vals["portfolio"])
        self.assert_database_work_file(work)

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_work: dict, work: Work
    ):
        self.assertEqual(retrieved_work["id"], work.id)
        self.assertEqual(retrieved_work["title"], work.title)
        self.assertEqual(retrieved_work["portfolio"], work.portfolio_id)
        self.assertEqual(retrieved_work["folder_name"], work.folder_name)
        self.assertEqual(retrieved_work["num_of_images"], work.num_of_images)
        self.assertEqual(retrieved_work["is_pdf"], work.is_pdf)
        # returned field's name is not work_file but it's 'file_url'
        self.assertTrue(retrieved_work["file_url"] != "")
        self.assertIn(str(work.work_file), retrieved_work["file_url"])
