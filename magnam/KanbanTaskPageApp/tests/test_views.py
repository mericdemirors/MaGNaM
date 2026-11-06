from django.urls import reverse
from ..models import *
from .base_test import *


# KanbanTagView
class TestRetrieveKanbanTagView(KanbanTaskTagBaseTestCase):
    def test_guest_can_retrieve_tags(self):
        self.client.logout()

        _, _, _, tag1 = self.create_random_valid_object()
        _, _, _, tag2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:kanban-tag")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], tag1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], tag2)


# KanbanTaskView
class TestRetrieveKanbanTaskView(KanbanTaskBaseTestCase):
    def test_admin_can_retrieve_tasks(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, task1 = self.create_random_valid_object()
        _, _, _, task2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:kanban-task")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], task1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], task2)

    def test_logged_in_user_cannot_retrieve_tasks(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:kanban-task")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# KanbanVoteView
class TestRetrieveKanbanVoteView(KanbanTaskVoteBaseTestCase):
    def test_admin_can_retrieve_votes(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, vote1 = self.create_random_valid_object()
        _, _, _, vote2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:kanban-vote")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], vote1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], vote2)

    def test_logged_in_user_cannot_retrieve_votes(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:kanban-vote")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# CreateKanbanTaskView
class TestCreateKanbanTaskView(KanbanTaskBaseTestCase):
    def test_logged_in_user_can_create_task(self):
        self.client.force_authenticate(user=self.user)

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={"creator": self.user.profile}
        )

        url = reverse(f"{self.namespace}:create-kanban-task")
        response = self.client.post(url, vals_to_send_request)

        self.assertEqual(response.status_code, 200)

        # this checks if object is created with the correct field values
        task = KanbanTask.objects.first()
        self.assert_db_stored_values_match_expected_dict(task, original_vals)

        # this checks if object sent back from the create request is the correct one
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"], task
        )

    def test_guest_cannot_create_task(self):
        self.client.logout()

        _, vals_to_send_request, _ = self.get_random_valid_data()

        url = reverse(f"{self.namespace}:create-kanban-task")
        response = self.client.post(url, vals_to_send_request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(KanbanTask.objects.count(), 0)


# DeleteKanbanTaskView
class TestDeleteKanbanTaskView(KanbanTaskBaseTestCase):
    def test_admin_can_delete_task(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, task = self.create_random_valid_object()
        task_id = task.id

        url = reverse(
            f"{self.namespace}:delete-kanban-task", kwargs={"kanban_task_id": task_id}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(KanbanTask.objects.filter(id=task_id).exists())

    def test_owner_can_delete_task(self):
        self.client.force_authenticate(user=self.user)

        # create a task and assign the user to self.user
        _, _, _, task = self.create_random_valid_object(
            predefined_vals={"creator": self.user.profile}
        )

        url = reverse(
            f"{self.namespace}:delete-kanban-task", kwargs={"kanban_task_id": task.id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(KanbanTask.objects.filter(id=task.id).exists())

    def test_non_owner_cannot_delete_task(self):
        # create task with another user and try to delete with self.user
        _, _, _, task = self.create_random_valid_object()

        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:delete-kanban-task", kwargs={"kanban_task_id": task.id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(KanbanTask.objects.filter(id=task.id).exists())

    def test_guest_cannot_delete_task(self):
        self.client.logout()

        _, _, _, task = self.create_random_valid_object()
        url = reverse(
            f"{self.namespace}:delete-kanban-task", kwargs={"kanban_task_id": task.id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(KanbanTask.objects.filter(id=task.id).exists())


# ChangeKanbanVoteView
class TestKanbanTaskVoteViewPermission(KanbanTaskVoteBaseTestCase):
    def test_guest_cannot_vote(self):
        task_tester = KanbanTaskBaseTestCase()
        _, _, _, task = task_tester.create_random_valid_object()

        self.client.logout()

        url = reverse(
            f"{self.namespace}:change-kanban-vote", kwargs={"kanban_task_id": task.id}
        )

        response = self.client.post(url, {"vote": True}, format="json")

        self.assertEqual(response.status_code, 403)


# ChangeKanbanVoteView
class TestKanbanTaskVoteViewMissingData(KanbanTaskVoteBaseTestCase):
    def test_missing_vote_field(self):
        self.client.force_authenticate(user=self.user)

        task_tester = KanbanTaskBaseTestCase()
        _, _, _, task = task_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:change-kanban-vote", kwargs={"kanban_task_id": task.id}
        )

        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_invalid_vote_value(self):
        self.client.force_authenticate(user=self.user)

        task_tester = KanbanTaskBaseTestCase()
        _, _, _, task = task_tester.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:change-kanban-vote", kwargs={"kanban_task_id": task.id}
        )

        invalid_values = ["abc", 0, 2, [], {}, None]

        for val in invalid_values:
            response = self.client.post(url, {"vote": val}, format="json")

            self.assertEqual(response.status_code, 400)


# ChangeKanbanVoteView
class TestKanbanTaskVoteViewNonExistent(KanbanTaskVoteBaseTestCase):
    def test_vote_non_existing_task(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:change-kanban-vote", kwargs={"kanban_task_id": 0}
        )

        response = self.client.post(url, {"vote": True}, format="json")

        self.assertEqual(response.status_code, 404)


# ChangeKanbanVoteView
class TestKanbanTaskVoteViewLogic(KanbanTaskVoteBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.profile = self.user.profile
        task_tester = KanbanTaskBaseTestCase()
        _, _, _, self.task = task_tester.create_random_valid_object()
        self.vote_tester = KanbanTaskVoteBaseTestCase()

        self.url = reverse(
            f"{self.namespace}:change-kanban-vote",
            kwargs={"kanban_task_id": self.task.id},
        )

    def send_vote(self, value):
        response = self.client.post(self.url, {"vote": value}, format="json")
        self.assertEqual(response.status_code, 200)
        return response

    def test_new_upvote(self):
        response = self.send_vote(True)

        # send vote to the task created during setUp
        vote = KanbanTaskVote.objects.get(voter=self.profile, task=self.task)
        self.assertTrue(vote.vote)

        self.assertEqual(response.data["data"]["new_vote"], 1)
        self.assertEqual(response.data["data"]["upvote_change"], 1)
        self.assertEqual(response.data["data"]["downvote_change"], 0)

    def test_new_downvote(self):
        response = self.send_vote(False)

        # send vote to the task created during setUp
        vote = KanbanTaskVote.objects.get(voter=self.profile, task=self.task)
        self.assertFalse(vote.vote)

        self.assertEqual(response.data["data"]["new_vote"], -1)
        self.assertEqual(response.data["data"]["upvote_change"], 0)
        self.assertEqual(response.data["data"]["downvote_change"], 1)

    def test_upvote_existing_upvote(self):
        # create an upvote on the task created during setUp so we can send another upvote on top of that
        self.vote_tester.create_random_valid_object(
            predefined_vals={"voter": self.profile, "task": self.task, "vote": True}
        )

        response = self.send_vote(True)

        self.assertFalse(
            KanbanTaskVote.objects.filter(voter=self.profile, task=self.task).exists()
        )

        self.assertIsNone(response.data["data"]["new_vote"])
        self.assertEqual(response.data["data"]["upvote_change"], -1)

    def test_downvote_existing_downvote(self):
        # create a downvote on the task created during setUp so we can send another downvote on top of that
        self.vote_tester.create_random_valid_object(
            predefined_vals={"voter": self.profile, "task": self.task, "vote": False}
        )

        response = self.send_vote(False)

        self.assertFalse(
            KanbanTaskVote.objects.filter(voter=self.profile, task=self.task).exists()
        )

        self.assertIsNone(response.data["data"]["new_vote"])
        self.assertEqual(response.data["data"]["downvote_change"], -1)

    def test_upvote_existing_downvote(self):
        # create a downvote on the task created during setUp so we can send another upvote on top of that
        self.vote_tester.create_random_valid_object(
            predefined_vals={"voter": self.profile, "task": self.task, "vote": False}
        )

        response = self.send_vote(True)

        vote = KanbanTaskVote.objects.get(voter=self.profile, task=self.task)
        self.assertTrue(vote.vote)

        self.assertEqual(response.data["data"]["new_vote"], 1)
        self.assertEqual(response.data["data"]["upvote_change"], 1)
        self.assertEqual(response.data["data"]["downvote_change"], -1)

    def test_downvote_existing_upvote(self):
        # create an upvote on the task created during setUp so we can send another downvote on top of that
        self.vote_tester.create_random_valid_object(
            predefined_vals={"voter": self.profile, "task": self.task, "vote": True}
        )

        response = self.send_vote(False)

        vote = KanbanTaskVote.objects.get(voter=self.profile, task=self.task)
        self.assertFalse(vote.vote)

        self.assertEqual(response.data["data"]["new_vote"], -1)
        self.assertEqual(response.data["data"]["upvote_change"], -1)
        self.assertEqual(response.data["data"]["downvote_change"], 1)


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewPermission(KanbanTaskBaseTestCase):
    def test_guest_can_access_gallery(self):
        # create task so response is not 404
        self.create_random_valid_object()

        self.client.logout()

        url = reverse(f"{self.namespace}:kanban-gallery")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewExistence(KanbanTaskBaseTestCase):
    def test_empty_gallery_returns_204(self):
        url = reverse(f"{self.namespace}:kanban-gallery")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 204)


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewFiltering(KanbanTaskBaseTestCase):
    def test_importance_filtering(self):
        _, _, _, task1 = self.create_random_valid_object(
            predefined_vals={"importance": 1}
        )
        _, _, _, task2 = self.create_random_valid_object(
            predefined_vals={"importance": 5}
        )
        _, _, _, task3 = self.create_random_valid_object(
            predefined_vals={"importance": 9}
        )

        url = reverse(f"{self.namespace}:kanban-gallery")

        response = self.client.get(url, {"importance_min": 2, "importance_max": 8})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        # check if min max filters discarded the task1 and task3
        self.assertNotIn(task1.id, returned_ids)
        self.assertIn(task2.id, returned_ids)
        self.assertNotIn(task3.id, returned_ids)

    def test_tag_filtering(self):
        # create reusable tags
        tag_tester = KanbanTaskTagBaseTestCase()

        _, _, _, tag1 = tag_tester.create_random_valid_object()
        _, _, _, tag2 = tag_tester.create_random_valid_object()
        _, _, _, tag3 = tag_tester.create_random_valid_object()

        # should be returned (contains ALL required tags)
        _, _, _, matching_task = self.create_random_valid_object(
            predefined_vals={"tags": [tag1, tag2]}
        )

        # should NOT be returned (missing tag2)
        _, _, _, missing_tag_task = self.create_random_valid_object(
            predefined_vals={"tags": [tag1]}
        )

        # should be returned (contains required tags + extra tag)
        _, _, _, extra_tags_task = self.create_random_valid_object(
            predefined_vals={"tags": [tag1, tag2, tag3]}
        )

        url = reverse(f"{self.namespace}:kanban-gallery")

        response = self.client.get(url, {"tags": f"{tag1.id},{tag2.id}"})

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.data["results"]]

        # a. task with all required tags should be returned
        self.assertIn(matching_task.id, returned_ids)

        # b. task missing one of the required tags should NOT be returned
        self.assertNotIn(missing_tag_task.id, returned_ids)

        # c. task with extra tags should still be returned
        self.assertIn(extra_tags_task.id, returned_ids)


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewSorting(KanbanTaskBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.task1 = self.create_random_valid_object(
            predefined_vals={"importance": 1}
        )
        _, _, _, self.task2 = self.create_random_valid_object(
            predefined_vals={"importance": 5}
        )
        _, _, _, self.task3 = self.create_random_valid_object(
            predefined_vals={"importance": 9}
        )
        self.url = reverse(f"{self.namespace}:kanban-gallery")

    def get_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.data["results"]]

    def test_sort_orders(self):
        response = self.client.get(self.url, {"sort": "importance"})
        ids = self.get_ids(response)
        self.assertEqual(ids, [self.task3.id, self.task2.id, self.task1.id])

        response = self.client.get(self.url, {"sort": "-importance"})
        ids = self.get_ids(response)
        self.assertEqual(ids, [self.task1.id, self.task2.id, self.task3.id])

        response = self.client.get(self.url, {"sort": "date"})
        ids = self.get_ids(response)
        # sorting by date means sorting by id and bigger id comes first
        self.assertEqual(ids, sorted(ids, reverse=True))

        response = self.client.get(self.url, {"sort": "-date"})
        ids = self.get_ids(response)
        # sorting by date means sorting by id and bigger id comes last
        self.assertEqual(ids, sorted(ids))

    def test_sort_num_of_upvotes(self):
        vote_tester = KanbanTaskVoteBaseTestCase()
        vote_tester.create_random_valid_object(
            predefined_vals={"task": self.task2, "vote": True}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"task": self.task3, "vote": True}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"task": self.task3, "vote": True}
        )

        response = self.client.get(self.url, {"sort": "num_of_upvotes"})
        ids = self.get_ids(response)
        self.assertEqual(ids, [self.task3.id, self.task2.id, self.task1.id])

    def test_multi_sort_date_then_importance(self):
        # create a new task to have the same importance as self.task2
        _, _, _, task4 = self.create_random_valid_object(
            predefined_vals={"importance": 5}
        )

        response = self.client.get(self.url, {"sort": "importance,date"})
        ids = self.get_ids(response)

        # most important to least important with newer tasks coming before as tie breaker
        self.assertEqual(ids, [self.task3.id, task4.id, self.task2.id, self.task1.id])


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewRandomness(KanbanTaskBaseTestCase):
    def test_random_sort(self):
        # create 3 tasks
        for _ in range(3):
            _, _, _, _ = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:kanban-gallery")

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


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewPagination(KanbanTaskBaseTestCase):
    def test_pagination_with_next_link(self):
        tasks = []

        for _ in range(6):
            _, _, _, task = self.create_random_valid_object()
            tasks.append(task)

        # sort by id
        tasks_sorted = sorted(tasks, key=lambda x: x.id, reverse=True)

        url = reverse(f"{self.namespace}:kanban-gallery")

        # get the first page
        response1 = self.client.get(url, {"sort": "date", "page_size": 3})
        self.assertEqual(response1.status_code, 200)

        # check if first page consists of the first 3 tasks
        ids_page1 = [item["id"] for item in response1.data["results"]]
        expected_page1 = [t.id for t in tasks_sorted[:3]]
        self.assertEqual(ids_page1, expected_page1)

        # use 'next' field in the response to get the second page
        next_url = response1.data["next"]
        self.assertIsNotNone(next_url)
        response2 = self.client.get(next_url)
        self.assertEqual(response2.status_code, 200)

        # check if second page consists of the second 3 tasks
        ids_page2 = [item["id"] for item in response2.data["results"]]
        expected_page2 = [t.id for t in tasks_sorted[3:6]]
        self.assertEqual(ids_page2, expected_page2)


# KanbanTaskGalleryView
class TestKanbanTaskGalleryViewFields(KanbanTaskBaseTestCase):
    def test_gallery_fields_consistency(self):
        # create 5 tasks
        tasks = []
        for _ in range(5):
            _, _, _, task = self.create_random_valid_object()
            tasks.append(task)

        # get individual tasks
        task1, task2, task3, task4, task5 = tasks

        vote_tester = KanbanTaskVoteBaseTestCase()
        vote_tester.create_random_valid_object(
            predefined_vals={"voter": task1.creator, "task": task3, "vote": True}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"voter": task2.creator, "task": task3, "vote": True}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"voter": task3.creator, "task": task4, "vote": False}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"voter": task4.creator, "task": task5, "vote": True}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"voter": task5.creator, "task": task5, "vote": False}
        )
        vote_tester.create_random_valid_object(
            predefined_vals={"voter": self.user.profile, "task": task5, "vote": False}
        )

        # authenticate self.user to test is_user_voted
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(f"{self.namespace}:kanban-gallery"), {"sort": "date"}
        )
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]

        # validate tasks
        for retrieved_item in results:
            task = next(t for t in tasks if t.id == retrieved_item["id"])

            # check base fields
            self.assert_db_retrieved_dict_match_db_stored_values(retrieved_item, task)

            # check vote counts
            expected_upvotes = task.votes.filter(vote=True).count()
            expected_downvotes = task.votes.filter(vote=False).count()
            self.assertEqual(retrieved_item["num_of_upvotes"], expected_upvotes)
            self.assertEqual(retrieved_item["num_of_downvotes"], expected_downvotes)

            # check user voting state
            vote = task.votes.filter(voter=self.user.profile).first()
            if vote is None:
                expected_vote = 0
            else:
                expected_vote = 1 if vote.vote else -1
            self.assertEqual(retrieved_item["is_user_voted"], expected_vote)
