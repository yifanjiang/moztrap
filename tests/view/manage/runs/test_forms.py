"""
Tests for run-management forms.

"""
from datetime import date
from django.core.exceptions import ValidationError

from tests import case



class EditRunFormTest(case.DBTestCase):
    """Tests for EditRunForm."""
    @property
    def form(self):
        """The form class under test."""
        from moztrap.view.manage.runs.forms import EditRunForm
        return EditRunForm


    def test_edit_run(self):
        """Can edit run, including productversion, with modified-by."""
        pv = self.F.ProductVersionFactory.create()
        r = self.F.RunFactory.create(productversion__product=pv.product)
        u = self.F.UserFactory.create()

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": "new name",
                "description": "new desc",
                "start": "1/3/2012",
                "end": "1/10/2012",
                "cc_version": str(r.cc_version),
                },
            instance=r,
            user=u)

        run = f.save()

        self.assertEqual(run.productversion, pv)
        self.assertEqual(run.name, "new name")
        self.assertEqual(run.description, "new desc")
        self.assertEqual(run.start, date(2012, 1, 3))
        self.assertEqual(run.end, date(2012, 1, 10))
        self.assertEqual(run.modified_by, u)


    def test_add_suites(self):
        """Can add suites to a run."""
        pv = self.F.ProductVersionFactory.create()
        r = self.F.RunFactory.create(productversion__product=pv.product)
        s = self.F.SuiteFactory.create(product=pv.product)

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": r.name,
                "description": r.description,
                "start": r.start.strftime("%m/%d/%Y"),
                "end": "",
                "suites": [str(s.id)],
                "cc_version": str(r.cc_version),
                },
            instance=r,
            )

        run = f.save()

        self.assertEqual(set(run.suites.all()), set([s]))


    def test_add_bad_suite(self):
        """Attempt to add non-existent suite to a run."""
        pv = self.F.ProductVersionFactory.create()
        r = self.F.RunFactory.create(productversion__product=pv.product)
        s = self.F.SuiteFactory.create(product=pv.product)

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": r.name,
                "description": r.description,
                "start": r.start.strftime("%m/%d/%Y"),
                "end": "",
                "suites": [str(s.id + 1)],
                "cc_version": str(r.cc_version),
                },
            instance=r,
            )

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors["suites"],
            [u"Not a valid suite for this run."]
        )


    def test_edit_suites(self):
        """Can edit suites in a run."""
        pv = self.F.ProductVersionFactory.create()
        r = self.F.RunFactory.create(productversion__product=pv.product)
        self.F.RunSuiteFactory.create(run=r)
        s = self.F.SuiteFactory.create(product=pv.product)

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": r.name,
                "description": r.description,
                "start": r.start.strftime("%m/%d/%Y"),
                "end": "",
                "suites": [str(s.id)],
                "cc_version": str(r.cc_version),
                },
            instance=r,
            )

        run = f.save()

        self.assertEqual(set(run.suites.all()), set([s]))


    def test_no_change_product_option(self):
        """No option to change to a version of a different product."""
        self.F.ProductVersionFactory.create()
        r = self.F.RunFactory()

        f = self.form(instance=r)
        self.assertEqual(
            [c[0] for c in f.fields["productversion"].choices],
            ['', r.productversion.id]
            )


    def test_no_edit_product(self):
        """Can't change product"""
        pv = self.F.ProductVersionFactory()
        r = self.F.RunFactory()

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": "new name",
                "description": "new desc",
                "start": "1/3/2012",
                "end": "1/10/2012",
                "cc_version": str(r.cc_version),
                },
            instance=r,
            )

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors["productversion"],
            [u"Select a valid choice. "
             "That choice is not one of the available choices."]
            )


    def test_active_run_no_product_version_options(self):
        """If editing active run, current product version is only option."""
        pv = self.F.ProductVersionFactory.create()
        r = self.F.RunFactory(
            status=self.model.Run.STATUS.active,
            productversion__product=pv.product)

        f = self.form(instance=r)
        self.assertEqual(
            [c[0] for c in f.fields["productversion"].choices],
            ['', r.productversion.id]
            )


    def test_active_run_product_version_readonly(self):
        """If editing active run, product version field is marked readonly."""
        pv = self.F.ProductVersionFactory.create()
        r = self.F.RunFactory(
            status=self.model.Run.STATUS.active,
            productversion__product=pv.product)

        f = self.form(instance=r)
        self.assertTrue(f.fields["productversion"].readonly)


    def test_active_run_no_edit_product_version(self):
        """Can't change product version of active run"""
        pv = self.F.ProductVersionFactory()
        r = self.F.RunFactory(status=self.model.Run.STATUS.active)

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": "new name",
                "description": "new desc",
                "start": "1/3/2012",
                "end": "1/10/2012",
                "cc_version": str(r.cc_version),
                },
            instance=r,
            )

        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors["productversion"],
            [u"Select a valid choice. "
             "That choice is not one of the available choices."]
            )


    def test_active_run_suites_preserved(self):
        """
        Can save run with suite list as names and not disturb suites.

        This happens when you try to save an active run.  The suites
        are names rather than ids, and are read-only.  So there should
        be no change.
        """
        pv = self.F.ProductVersionFactory.create()
        s = self.F.SuiteFactory.create(product=pv.product)
        r = self.F.RunFactory.create(productversion__product=pv.product)
        self.F.RunSuiteFactory.create(run=r, suite=s)

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": r.name,
                "description": r.description,
                "start": r.start.strftime("%m/%d/%Y"),
                "end": "",
                "suites": [str(s.name)],
                "cc_version": str(r.cc_version),
                },
            instance=r,
            )

        run = f.save()

        self.assertEqual(set(run.suites.all()), set([s]))



class AddRunFormTest(case.DBTestCase):
    """Tests for AddRunForm."""
    @property
    def form(self):
        """The form class under test."""
        from moztrap.view.manage.runs.forms import AddRunForm
        return AddRunForm


    def test_add_run(self):
        """Can add run, has created-by user."""
        pv = self.F.ProductVersionFactory()
        u = self.F.UserFactory()

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": "Foo",
                "description": "foo desc",
                "start": "1/3/2012",
                "end": "1/10/2012",
                "cc_version": "0",
                },
            user=u
            )

        run = f.save()

        self.assertEqual(run.productversion, pv)
        self.assertEqual(run.name, "Foo")
        self.assertEqual(run.description, "foo desc")
        self.assertEqual(run.start, date(2012, 1, 3))
        self.assertEqual(run.end, date(2012, 1, 10))
        self.assertEqual(run.created_by, u)


    def test_add_run_series_clears_build(self):
        """Can add run as a series, and clears the build field if set."""
        pv = self.F.ProductVersionFactory()
        u = self.F.UserFactory()

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": "Foo",
                "description": "foo desc",
                "start": "1/3/2012",
                "end": "1/10/2012",
                "cc_version": "0",
                "is_series": True,
                "build": "rah",
                },
            user=u
        )

        run = f.save()

        self.assertEqual(run.build, None)


    def test_add_run_withsuites(self):
        """Can add suites to a new run."""
        pv = self.F.ProductVersionFactory.create()
        s = self.F.SuiteFactory.create(product=pv.product)

        f = self.form(
            {
                "productversion": str(pv.id),
                "name": "some name",
                "description": "some desc",
                "start": "1/3/2012",
                "end": "",
                "suites": [str(s.id)],
                "cc_version": "0",
                },
            )

        run = f.save()

        self.assertEqual(set(run.suites.all()), set([s]))
