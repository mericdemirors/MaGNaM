import random
from django.test import TransactionTestCase, override_settings
from utils.test_utils import *
from ..globals import *
from ..models import *


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class KanbanTaskTagBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "KanbanTaskPageApp")

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
        tag = KanbanTaskTag.objects.create(**vals_to_create_from)
        return original_vals, vals_to_send_request, vals_to_create_from, tag

    def assert_db_stored_values_match_expected_dict(
        self, tag: KanbanTaskTag, original_vals: dict
    ):
        self.assertEqual(tag.label, original_vals["label"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_tag: dict, tag: KanbanTaskTag
    ):
        self.assertEqual(retrieved_tag["id"], tag.id)
        self.assertEqual(retrieved_tag["label"], tag.label)


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class KanbanTaskBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "KanbanTaskPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_creator_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_description_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_tags_value(self, count=3, seed=None):
        tag_tester = KanbanTaskTagBaseTestCase()

        tags = []
        for i in range(count):
            _, _, _, tag = tag_tester.create_random_valid_object(
                seed=seed + i if seed else None
            )
            tags.append(tag)
        return tags

    def get_random_importance_value(self, seed=None):
        return random.Random(seed).randint(KANBAN_MIN_IMPORTANCE, KANBAN_MAX_IMPORTANCE)

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        creator = (
            predefined_vals["creator"]
            if "creator" in predefined_vals
            else self.get_random_creator_value(seed=seed)
        )
        description = predefined_vals.get(
            "description", self.get_random_description_value(seed=seed)
        )
        tags = (
            predefined_vals["tags"]
            if "tags" in predefined_vals
            else self.get_random_tags_value(seed=seed)
        )
        importance = predefined_vals.get(
            "importance", self.get_random_importance_value(seed=seed)
        )

        original_vals = {
            "creator": creator.id,
            "description": description,
            "tags": [tag.id for tag in tags],
            "importance": importance,
        }

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["creator"] = creator
        vals_to_create_from["tags"] = tags

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        # pop the tag objects because we set the M2M fiels after creating the instance
        tags = vals_to_create_from.pop("tags")
        # create the instance
        task = KanbanTask.objects.create(**vals_to_create_from)
        # set the M2M field references
        task.tags.set(tags)
        task.save()

        # re-add the popped field before returning
        vals_to_create_from["tags"] = tags

        return original_vals, vals_to_send_request, vals_to_create_from, task

    def assert_db_stored_values_match_expected_dict(
        self, task: KanbanTask, original_vals: dict
    ):
        # we can check the creator directly like this instead of using the id field
        # because task.creator is a db object
        # and original_vals["creator"] is also a Profile object instead of an id
        # normally original_vals should be ideally ids (as it is with the tags)
        # but creator is not
        self.assertEqual(task.creator.id, original_vals["creator"])
        self.assertEqual(task.description, original_vals["description"])
        self.assertEqual(task.importance, original_vals["importance"])
        # here tags we fetch from the task.tags.all() call are db objects
        # but original_vals["tags"] are ids of these tags
        self.assertEqual(
            set([t.id for t in task.tags.all()]), set(original_vals["tags"])
        )

    def assert_db_tags(self, retrieved_task_tags, expected_task_tags):
        tester = KanbanTaskTagBaseTestCase()
        self.assertEqual(len(retrieved_task_tags), len(expected_task_tags))

        for retrieved_tag in retrieved_task_tags:
            # Find the expected_tag (handling both instances and raw IDs)
            expected_tag = next(
                (e for e in expected_task_tags if e.id == retrieved_tag["id"]), None
            )
            self.assertIsNotNone(expected_tag)
            tester.assert_db_retrieved_dict_match_db_stored_values(
                retrieved_tag, expected_tag
            )

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_task: dict, task: KanbanTask
    ):
        self.assertEqual(retrieved_task["id"], task.id)
        # here we check the creator_id instead of creator
        # because database returns the instance with ReturnKanbanTaskSerializer or ReturnKanbanTaskGallerySerializer
        # which both computes creator_id from the creator relations
        self.assertEqual(retrieved_task["creator_id"], task.creator_id)
        self.assertEqual(retrieved_task["description"], task.description)
        self.assertEqual(retrieved_task["importance"], task.importance)
        # in the above function we only compared the tag ids since our instance had db objects but original_vals didnt
        # reason for that setup is we configure the original_vals to simulate the frontend request
        # we only send the tag ids, not the actual objects
        # but here our retrieved_task["tags"] is a list of db objects because its what frontend receives: ids, labels everything
        # and our task.tags.all() call also return db objects so we dont use only ids, but we look deeper
        self.assert_db_tags(retrieved_task["tags"], list(task.tags.all()))


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class KanbanTaskVoteBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "KanbanTaskPageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_voter_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_task_value(self, seed=None):
        task_creator = KanbanTaskBaseTestCase()
        _, _, _, task = task_creator.create_random_valid_object(seed=seed)
        return task

    def get_random_vote_value(self, seed=None):
        return random.Random(seed).choice([True, False])

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        voter = (
            predefined_vals["voter"]
            if "voter" in predefined_vals
            else self.get_random_voter_value(seed=seed)
        )
        task = (
            predefined_vals["task"]
            if "task" in predefined_vals
            else self.get_random_task_value(seed=seed)
        )
        vote = predefined_vals.get("vote", self.get_random_vote_value(seed=seed))

        original_vals = {"voter": voter.id, "task": task.id, "vote": vote}

        vals_to_send_request = original_vals.copy()

        vals_to_create_from = original_vals.copy()
        vals_to_create_from["voter"] = voter
        vals_to_create_from["task"] = task

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )
        vote = KanbanTaskVote.objects.create(**vals_to_create_from)
        return original_vals, vals_to_send_request, vals_to_create_from, vote

    def assert_db_stored_values_match_expected_dict(
        self, vote: KanbanTaskVote, original_vals: dict
    ):
        self.assertEqual(vote.voter.id, original_vals["voter"])
        self.assertEqual(vote.task.id, original_vals["task"])
        self.assertEqual(vote.vote, original_vals["vote"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_vote: dict, vote: KanbanTaskVote
    ):
        # here we check the voter_id and task_id instead of voter and task
        # because database returns the instance with ReturnKanbanTaskVoteSerializer which computes these fields from the voter and task relations
        self.assertEqual(retrieved_vote["id"], vote.id)
        self.assertEqual(retrieved_vote["voter_id"], vote.voter_id)
        self.assertEqual(retrieved_vote["task_id"], vote.task_id)
        self.assertEqual(retrieved_vote["vote"], vote.vote)
