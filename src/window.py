# window.py
#
# Copyright 2026 Adryan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import threading

from gi.repository import Adw
from gi.repository import Gtk, GLib
from .generator import generate

from gettext import gettext as _

@Gtk.Template(resource_path='/io/github/nasc1mento/Replica/window.ui')
class ReplicaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ReplicaWindow'

    label = Gtk.Template.Child()
    generator_type = Gtk.Template.Child()
    create_button = Gtk.Template.Child()
    toast = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_create(self):
        self.create_button.set_sensitive(False)

        generator_type = self.generator_type.get_selected_item().get_string()

        def run():
            content, extension = generate(generator_type)
            GLib.idle_add(self._on_generate_done, content, extension)

        threading.Thread(target=run, daemon=True).start()

    def _on_generate_done(self, content, extension):
        self.create_button.set_sensitive(True)

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Save artefact"))
        dialog.set_initial_name(f"replica{extension}")
        dialog.save(self, None, lambda d, r: self._on_file_selected(d, r, content, extension))

        return GLib.SOURCE_REMOVE

    def _on_file_selected(self, dialog, result, content, extension):
        try:
            file = dialog.save_finish(result)
            if file is None:
                return

            path = file.get_path()
            if not path.endswith(extension):
                path += extension

            with open(path, 'w') as f:
                f.write(content)

            toast = Adw.Toast(title=_("Artefact saved successfully!"))
            self.toast.add_toast(toast)

        except GLib.Error:
            pass
