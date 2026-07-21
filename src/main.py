# main.py
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

import sys
import gi
import os

from gettext import gettext as _

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import ReplicaWindow

class ReplicaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.nasc1mento.Replica',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/io/github/nasc1mento/Replica')
        self.create_action('quit', lambda *_: self.quit(), ['<control>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('create', self.on_create_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = ReplicaWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Replica',
                                application_icon='io.github.nasc1mento.Replica',
                                developer_name='Adryan Reis',
                                version='0.1.0',
                                # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
                                translator_credits = _('translator-credits'),
                                developers=['Adryan Reis'],
                                copyright='© 2026 Adryan')
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _action):
        preferences = Adw.PreferencesDialog()

        page = Adw.PreferencesPage(
            title=_("General")
        )

        behavior_group = Adw.PreferencesGroup(
            title=_("Behavior")
        )

        pin_versions_row = Adw.SwitchRow(
            title=_("Pin versions"),
            subtitle=_("Use exact installed version instead of stable")
        )

        include_overrides_row = Adw.SwitchRow(
            title=_("Include overrides"),
            subtitle=_("Include permission overrides in generated artifacts")
        )

        behavior_group.add(pin_versions_row)
        behavior_group.add(include_overrides_row)

        page.add(behavior_group)
        preferences.add(page)
        preferences.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_create_action(self, action, param):
        self.props.active_window.on_create()

def main(version):
    """The application's entry point."""
    app = ReplicaApplication()
    return app.run(sys.argv)
