"""Testing the database in a general sense and the models specifically."""

from sqlalchemy.exc import IntegrityError, ProgrammingError

from . import KaosTestCase
from .context import kaos
from kaos.models import DB, ResponseHistory

class TestResponseHistory(KaosTestCase):
    """Ensures that the response history table behaves as expected."""

    def test_history_empty(self):
        """Test that an empty response cannot be commited to history."""
        response_history = ResponseHistory("")
        response_history.save()

        with self.assertRaises(ProgrammingError):
            DB.session.commit()

    def test_history_non_string(self):
        """Test that a non string response cannot be commited to history."""
        response_history = ResponseHistory(420)
        response_history.save()

        with self.assertRaises(ProgrammingError):
            DB.session.commit()

    def test_history_uid_non_int(self):
        """Test that a non int uid response cannot be commited to history."""
        response_history = ResponseHistory("WOW")
        response_history.uid = "Test"
        response_history.save()

        with self.assertRaises(ProgrammingError):
            DB.session.commit()

    def test_history_save_no_commit(self):
        """Test that non commited data is not saved to the database."""
        response_history = ResponseHistory("RESPONSE")
        response_history.save()

        DB.session.rollback()
        self.assertFalse(ResponseHistory.query.all())

    def test_history_save_commit(self):
        """Test that data is commited and saved to the database."""
        response_history = ResponseHistory("RESPONSE")
        response_history.save()
        DB.session.commit()

        DB.session.rollback()
        self.assertTrue(len(ResponseHistory.query.all()) == 1)
        self.assertTrue(ResponseHistory.query.all()[0].response == "RESPONSE")

    def test_history_save_arb_id(self):
        """Test that data is commited and saved to the database even if uid is assigned manually."""
        response_history = ResponseHistory("RESPONSE")
        response_history.uid = 420
        response_history.save()
        DB.session.commit()

        DB.session.rollback()
        self.assertTrue(len(ResponseHistory.query.all()) == 1)
        self.assertTrue(ResponseHistory.query.all()[0].response == "RESPONSE")
        self.assertTrue(ResponseHistory.query.all()[0].uid == 420)

    def test_history_save_same_id(self):
        """Test that we can't have two records with the same pk."""
        response_history_1 = ResponseHistory("RESPONSE_1")
        response_history_1.save()
        DB.session.commit()

        DB.session.rollback()
        self.assertTrue(len(ResponseHistory.query.all()) == 1)
        self.assertTrue(ResponseHistory.query.all()[0].response == "RESPONSE_1")

        response_history_2 = ResponseHistory("RESPONSE_2")
        response_history_2.uid = response_history_1.uid
        del response_history_1
        response_history_2.save()
        with self.assertRaises(IntegrityError):
            DB.session.commit()