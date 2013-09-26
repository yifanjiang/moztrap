"""Template tags/filters for running tests."""
from django import template

from classytags.core import Tag, Options
from classytags.arguments import Argument

from .... import model



register = template.Library()


class ResultFor(Tag):
    """
    Places Result for this runcaseversion/user/env in context.

    If no relevant Result exists, returns *unsaved* default Result for use in
    template (result will be saved when case is started.)

    """
    name = "result_for"
    options = Options(
        Argument("runcaseversion"),
        Argument("user"),
        Argument("environment"),
        "as",
        Argument("varname", resolve=False),
        )


    def render_tag(self, context, runcaseversion, user, environment, varname):
        """Get/construct Result and place it in context under ``varname``"""
        result_kwargs = dict(
            environment=environment,
            tester=user,
            runcaseversion=runcaseversion,
            is_latest=True,
            )
        try:
            result = model.Result.objects.get(**result_kwargs)
        except model.Result.DoesNotExist:
            result = model.Result(**result_kwargs)
        except model.Result.MultipleObjectsReturned:
            # find the latest one and set it to latest, which will set all
            # others to is_latest=False
            result = model.Result.objects.filter(**result_kwargs).order_by(
                "-modified_on")[0]
            result.set_latest()
            result.save()

        context[varname] = result
        return u""


register.tag(ResultFor)



class OtherResultFor(Tag):
    """
    Places Result for this runcaseversion/env in context for other users.

    """
    name = "other_result_for"
    options = Options(
        Argument("runcaseversion"),
        Argument("user"),
        Argument("environment"),
        "as",
        Argument("varname", resolve=False)
        )


    def render_tag(self, context, runcaseversion, user, environment, varname):
        """Get/construct Result and place it in context under ``varname``"""

        # check for any completed result states from other users for this
        # same case/env combo.
        include_kwargs = dict(
            environment=environment,
            runcaseversion=runcaseversion,
            is_latest=True,
            status__in=(model.Result.COMPLETED_STATES +
                [model.Result.STATUS.skipped]),
            )
        exclude_kwargs = dict(
            tester=user,
            )

        try:
            result = model.Result.objects.only(
                "id",
                "status",
                "tester",
                "comment",
                ).filter(
                    **include_kwargs).exclude(**exclude_kwargs).order_by(
                    "-modified_on")[0]
        except IndexError:
            result = None


        context[varname] = result
        return u""


register.tag(OtherResultFor)



class StepResultFor(Tag):
    """
    Places StepResult for this result/casestep in context.

    If no relevant StepResult exists, returns *unsaved* default StepResult for
    use in template.

    """
    name = "stepresult_for"
    options = Options(
        Argument("result"),
        Argument("casestep"),
        "as",
        Argument("varname", resolve=False),
        )


    def render_tag(self, context, result, casestep, varname):
        """Get/construct StepResult and place it in context under ``varname``"""
        stepresult_kwargs = dict(
            result=result,
            step=casestep,
            )
        try:
            stepresult = model.StepResult.objects.get(**stepresult_kwargs)
        except model.StepResult.DoesNotExist:
            stepresult = model.StepResult(**stepresult_kwargs)

        context[varname] = stepresult
        return u""


register.tag(StepResultFor)



class CompletionFor(Tag):
    """
    Places completion percentage in context.

    """
    name = "completion_for"
    options = Options(
        Argument("run"),
        Argument("environment"),
        "as",
        Argument("varname", resolve=False),
        )


    def render_tag(self, context, run, environment, varname):
        """
        Get/construct completion percentage
        and place it in context under ``varname``
        """
        completion = run.completion_single_env(environment)
        context[varname] = completion
        # context[varname] = "{0}and{1}".format(run, environment)
        # context[varname] = "foo"
        return u""


register.tag(CompletionFor)


class SuitesFor(Tag):
    """Return suite intersection of case and run."""

    name = "suites_for"
    options = Options(
        Argument("run"),
        Argument("runcaseversion"),
        "as",
        Argument("varname", resolve=False),
        )


    def render_tag(self, context, run, runcaseversion, varname):
        """Get/construct Suite list and place it in context under ``varname``"""
        result = model.Suite.objects.filter(cases=runcaseversion.caseversion.case, runs=run)

        context[varname] = result
        return u""


register.tag(SuitesFor)
