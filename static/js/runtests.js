/*jslint    browser:    true,
            indent:     4 */
/*global    ich, jQuery, VALID_ENVIRONMENTS */

var MT = (function (MT, $) {

    'use strict';

    // hide empty run-tests environments form on initial load
    MT.hideEmptyRuntestsEnv = function () {
        $('.runenvselect.empty').hide();
    };

    // Add focus to ``invalid``, ``fail``, ``block`` and ``skip`` textboxes when expanded
    MT.autoFocus = function (trigger, context) {
        $(context).on('click', trigger, function () {
            if ($(this).parent().hasClass('open')) {
                $(this).parent().find('textarea').focus();
            }
        });
    };

    // Open hierarchical navigation directly to clicked breadcrumb link
    MT.breadcrumb = function (context) {
        var finder = $(context);
        finder.find('.runsdrill .colcontent').each(function () {
            $(this).data('originalHTML', $(this).html());
        });
        $('.runtests-nav .secondary .breadcrumb').click(function (e) {
            if (!finder.hasClass('open')) {
                finder.children('.summary').click();
            }
            finder.find('.runsdrill .colcontent').each(function () {
                $(this).html($(this).data('originalHTML'));
            });
            finder.find('#' + $(this).data('id')).click();
            e.preventDefault();
        });
    };

    // Expand all tests on bulk-open
    MT.expandAllTests = function (container) {
        var context = $(container),
            trigger = context.find('.itemlist .listordering .bybulk-open > a'),
            target,
            updateTrigger = function () {
                if (context.find('.itemlist .listitem .itembody.details').length === context.find('.itemlist .listitem .itembody.details.open').length) {
                    trigger.addClass('open');
                } else {
                    trigger.removeClass('open');
                }
            };

        trigger.click(function (e) {
            target = context.find('.itemlist .listitem .itembody.details');
            trigger.toggleClass('open');
            if (trigger.hasClass('open')) {
                target.each(function () {
                    if (!($(this).hasClass('open'))) {
                        $(this).children('.item-summary').click();
                    }
                });
            } else {
                target.each(function () {
                    if ($(this).hasClass('open')) {
                        $(this).children('.item-summary').click();
                    }
                });
            }
            e.preventDefault();
        });

        context.on('click', '.itemlist .listitem .itembody.details > .item-summary.summary', function () {
            updateTrigger();
        });

        updateTrigger();
    };

    // Ajax submit runtest forms
    MT.runTests = function (container) {
        var context = $(container),
            tests = context.find('.listitem'),
            ajaxFormsInit = function (test) {
                var forms = test.find('form');

                forms.ajaxForm({
                    beforeSubmit: function (arr, form, options) {
                        test.loadingOverlay();
                    },
                    success: function (response) {
                        var newTest = $(response.html);
                        test.loadingOverlay('remove');
                        if ($(response.html).is("article")) {
                            test.replaceWith(newTest);
                            ajaxFormsInit(newTest);
                            newTest.find('.details').html5accordion();
                        }
                        else {
                            $(ich.message({
                                  message: "This test or test run is no longer available.  Please see your test manager.",
                                  tags: "error"
                              })).appendTo($('#messages ul'));
                            $('#messages ul').messages();
                        }
                    }
                });
            },
            ajaxifyTests = function () {
                tests.each(function () {
                    var thisTest = $(this);
                    ajaxFormsInit(thisTest);
                });
            };

        ajaxifyTests();

        // Re-attach ajax-form handlers after list is ajax-replaced (sorting/filtering called in listpages.js)
        context.on('after-replace', '.itemlist.action-ajax-replace', function (event, replacement) {
            tests = context.find('.listitem');
            ajaxifyTests();
        });
    };

    // Enable/disable failed test bug URL input on-select
    MT.failedTestBug = function (container) {
        var context = $(container);

        context.on('change', '.listitem .stepfail input[type="radio"][name="bug"]', function () {
            var thisList = $(this).closest('.stepfail'),
                newBug = thisList.find('input[type="radio"].newbug-radio'),
                newBugInput = thisList.find('input[type="url"].newbug-input');

            if (newBug.is(':checked')) {
                newBugInput.removeClass('disabled').attr('name', 'bug').focus();
            } else {
                newBugInput.addClass('disabled').attr('name', 'disabled-bug');
            }
        });

        context.on('click', '.listitem .stepfail input[type="url"].newbug-input.disabled', function () {
            var newBugRadio = $(this).siblings('.newbug-radio');
            newBugRadio.click();
        });
    };

    // Clicking anywhere on test header expands test
    MT.expandTestDetails = function (container) {
        var context = $(container);

        context.on('click', '.itemlist .listitem .itemhead', function (e) {
            if (!($(e.target).is('button') || $(e.target).is('.filter-link'))) {
                $(this).closest('.listitem').find('.itembody .item-summary').click();
            }
        });
    };

    // Filter environment form options
    MT.filterEnvironments = function (container) {
        var context = $(container),
            triggers = context.find('select'),
            doFilter;

        if (context.length) {
            triggers.each(function () {
                var allopts = $(this).find('option').clone().removeAttr('selected');
                $(this).data('allopts', allopts);
            });

            doFilter = function () {
                var i,
                    key = triggers.map(function () {
                        if ($(this).find('option:selected').val()) {
                            return parseInt($(this).find('option:selected').val(), 10);
                        } else {
                            return '';
                        }
                    }),
                    filterCombos = function (elementOfArray, indexInArray) {
                        if (elementOfArray[i] === null) {
                            return true;
                        } else {
                            return elementOfArray[i] === key[i];
                        }
                    };

                for (i = 0; i < key.length; i = i + 1) {
                    if (key[i] === '') {
                        key[i] = null;
                    }
                }

                if (VALID_ENVIRONMENTS) {
                    triggers.each(function () {
                        var thisIndex = triggers.index($(this)),
                            validOpts = [],
                            acceptAll = false,
                            allopts = $(this).data('allopts'),
                            filteredValidCombos = VALID_ENVIRONMENTS,
                            filteredOpts,
                            selectedVal;

                        for (i = 0; i < key.length; i = i + 1) {
                            if (key[i] !== null && i !== thisIndex) {
                                filteredValidCombos = $.grep(filteredValidCombos, filterCombos);
                            }
                        }

                        validOpts = $.map(filteredValidCombos, function (elementOfArray, indexInArray) {
                            if (elementOfArray[thisIndex] === null) {
                                acceptAll = true;
                            }
                            return elementOfArray[thisIndex];
                        });

                        if ($(this).find('option:selected').val()) {
                            selectedVal = $(this).find('option:selected').val();
                        }

                        if (acceptAll) {
                            $(this).html(allopts);
                        } else {
                            filteredOpts = allopts.filter(function (index) {
                                if ($(this).val() === '') {
                                    return true;
                                } else {
                                    return $.inArray(parseInt($(this).val(), 10), validOpts) !== -1;
                                }
                            });
                            $(this).html(filteredOpts);
                        }

                        if (selectedVal) {
                            $(this).find('option').filter(function () {
                                return $(this).val() === selectedVal;
                            }).prop('selected', true);
                        } else {
                            $(this).find('option').first().prop('selected', true);
                        }
                    });
                }
            };

            triggers.change(doFilter);
        }
    };

    // Refetch list items according to filters to update existing list items
    MT.refreshRuntests = function (container) {
        var context = $(container),
            filterForm = context.find('#filterform');
        if (context.length) {
            var replaceList = context.find('.action-ajax-replace')
            console.log(replaceList.data("ajax-update-url"))
            var pagenum = replaceList.find(".listnav").find(".current").html();
            $.ajax({
                url: replaceList.data("ajax-update-url"),
                cache: false,
                data: {
                    pagesize: replaceList.find('.listnav').data('pagesize'),
                    pagenumber: replaceList.find(".listnav").find(".current").html()
                },
                success: function (response) {
                    var newList = $(response.html);

                    if (response.html) {
                        // here we want to walk each existing item in the list,
                        // and replace its other-result with what we have in this response

                        // loop through all the articles.
                        $('article').each(function(idx, item) {
                            // find the matching one in the response.html
                            var match = newList.find("#" + item.id);
                            if (match.length) {
                                var other = $(item).find(".other-result");
                                other.html(match.find(".other-result").html());
                            }

                        });
                    }
                },
                complete: function() {
                    setTimeout("MT.refreshRuntests('#runtests')", 30000);
                }
            });
        }
    };

    MT.startRefreshTimer = function (container) {
        var context = $(container),
            filterForm = context.find('#filterform');
        if (context.length) {
            setTimeout("MT.refreshRuntests('#runtests')", 30000);
        }
    };

    return MT;

}(MT || {}, jQuery));