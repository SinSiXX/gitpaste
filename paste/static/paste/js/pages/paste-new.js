$(document).ready(function () {
    var ace_pos = 0;

    // Load the ACE editor and cache the binding between the
    // element and the mode for later reference.
    var editors = {};
    var ace = require(['ace/ace'], function (ace) {
        $('ul.pastes > li').each(function () {
            (function (e) {
                var $pre = $('pre', e);
                console.log($pre);
                var $textarea = $('textarea', e);
                var editor = ace.edit($pre[0]);
                editor.setTheme('ace/theme/textmate');
                editor.getSession().setMode('ace/mode/javascript');
                editor.getSession().on('change', function() {
                      $textarea.val(editor.getSession().getValue());
                });
                editors[$pre[0]] = editor;
            })(this);
        });
    });

    // Logic for building an entry in the paste
    var build_row = function (li) {
        var $li = $(li);
        var $pre = $('div.paste > pre', $li);
        var $delete_row = $('a.delete-row', $li);

        $('div.close', $li).click(function () {
            $delete_row.click();
        });

        $('div.title', $li).each(function () {
            var $this = $(this);
            var $select = $('select', $this);
            var $input = $('input', $this);
            var split = [];
            var $chosen = $select.attr('data-placeholder', 'Choose a language').chosen();

            $('option', $this).each(function () {
                var value = $(this).val().split('|');
                var regexp = new RegExp(value[1]);
                split.push({'regex': regexp,
                            'value': $(this).val(),
                            'editor': value[0]});
            });

            var active_timer = null;
            $input.keyup(function () {
                clearTimeout(active_timer);
                var input_text = $(this).val();
                active_timer = setTimeout(function () {
                    for (var i = 0; i < split.length; i++) {
                        var data = split[i];
                        if (data.regex.test(input_text)) {
                            console.log(data);
                            var mode = 'ace/mode/' + data.editor;
                            $chosen.val(data.value).trigger("liszt:updated");
                            editors[$pre[0]].getSession().setMode(mode);
                            return;
                        }
                    }
                }, 250);
            }).blur(function () {
                $(this).keyup();
            });

            $chosen.val('text|\\.txt$').trigger('liszt:updated');
        });
    };

    // jquery.formset for integration with Django
    $('ul.pastes > li').formset({
        prefix: 'formset',
        addText: '',
        deleteText: '',
        added: function (e) {
            build_row(e);
        }
    });

    // Rebind the click-event handling
    $('#add-paste').click(function () {
        $('ul.pastes .add-row').click();
    });

    // Initial construction of the pages.
    $('ul.pastes > li').each(function (e) {
        build_row(this);
    });
});